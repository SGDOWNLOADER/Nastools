from config import RMT_MEDIAEXT, RMT_SUBEXT, _season_re_1, _season_re_2, _seasons_re_1, _seasons_re_2, _episode_re_1, \
    _episode_re_2, _episodes_re_1, _episodes_re_2, _numbers_re
import regex as re
import pandas as pd
from app.helper import DbHelper
from app.utils import PathUtils, Tokens
import os
import cn2an
import log
import traceback
import anitopy


class FileHelper:
    """
    规整处理文件目录
    :param sortflag: 是否重新排序
    :param subtitle: 副标题、描述
    :param mtype: 指定识别类型，为空则自动识别类型
    :return: MetaAnime、MetaVideo
    """
    dbhelper = None
    offset_words_info = []

    def __init__(self, dirname):
        self.init_config()
        self.dir_name = dirname

    def init_config(self):
        self.dbhelper = DbHelper()
        self.offset_words_info = self.dbhelper.get_custom_words(enabled=1, wtype=4, regex=1)
    
    # def get_esp_num(self, title):
    #     """
    #     获取文件名中的集数
    #     :param title: 文件名
    #     :return: esp_num
    #     """
    #     esp_num = None
    #     episode_str = re.search(r'%s' % _subtitle_episode_re, title, re.IGNORECASE)
    #     episodes = episode_str.group(1) if episode_str else None
    #     if episodes:
    #         esp_num = episodes.upper().replace("E", "").replace("P", "").strip()
    #     else:
    #         if self.offset_words_info:
    #             for offset_word_info in self.offset_words_info:
    #                 front = offset_word_info.FRONT
    #                 back = offset_word_info.BACK
    #                 offset = offset_word_info.OFFSET
    #                 offset_word = f"{front}@{back}@{offset}"
    #                 offset_word_info_re = re.compile(rf'(?<=(?:{front}))(\d+)(?!(?:{back}))')
    #                 while re.findall(offset_word_info_re, title):
    #                     esp_num = re.findall(offset_word_info_re, title)[0]
    #             if not esp_num:
    #                 esp_num = re.findall(r'\d+', title)[0]
    #         else:
    #             esp_num = re.findall(r'\d+', title)[0]
    #     return esp_num

    @staticmethod
    def list_to_be(pat_str, flag):
        """
        获取文件名中的季数
        :param pat_str: 正则匹配的字符串
        :param flag: 季名/集名
        :return: begin_season:
        end_season:
        """
        split_str = re.findall(r'\W', pat_str)[0] if re.findall(r'\W', pat_str) else flag
        num_lst = list(filter(lambda x: x is not None and x != '', pat_str.split(split_str.upper())))
        num_lst = [re.findall(_numbers_re, num, flags=re.IGNORECASE)[0]
                   if re.findall(_numbers_re, num, flags=re.IGNORECASE) else None for num in num_lst]
        if len(num_lst) == 2:
            return int(cn2an.cn2an(num_lst[0].strip(), mode='smart')), int(
                    cn2an.cn2an(num_lst[1].strip(), mode='smart')) if num_lst[1] else None
        else:
            return int(cn2an.cn2an(num_lst[0].strip(), mode='smart')), None

    def get_season_num(self, title):
        """
        获取文件名中的季数
        :param title: 文件名
        :return: begin_season:
        end_season:
        total_season:
        """
        season_str = re.search(f"({_season_re_1}|{_season_re_2})", title, flags=re.IGNORECASE)
        seasons_str = re.search(f"({_seasons_re_1}|{_seasons_re_2})", title, flags=re.IGNORECASE)
        # 季组
        if seasons_str:
            total_season = 1
            seasons = seasons_str.group(1)
            try:
                begin_season, end_season = self.list_to_be(seasons, 's')
            except Exception as err:
                log.debug(f'识别季失败：{str(err)} - {traceback.format_exc()}')
                return None, None, None
            if begin_season is None and isinstance(begin_season, int):
                total_season = 1
            if begin_season is not None \
                    and isinstance(end_season, int) \
                    and end_season != begin_season:
                total_season = (end_season - begin_season) + 1
        # 季
        elif season_str:
            season = season_str.group(1)
            season_num = re.findall(_numbers_re, season, flags=re.IGNORECASE)[0]
            begin_season = int(cn2an.cn2an(season_num, mode='smart'))
            end_season = None
            total_season = 1
        else:
            begin_season = 1
            end_season = None
            total_season = 1
        return begin_season, end_season, total_season

    @staticmethod
    def get_season_str(begin_season, end_season):
        """
        获取文件名中的季数
        :param begin_season: 传入的起始季的数字
        :param end_season: 传入的结束季的数字
        :return: season_str: 字符串季信息 S01
        """
        if end_season:
            begin_season_str = 'S0' + str(begin_season) if len(str(begin_season)) == 1 \
                else 'S' + str(begin_season)
            end_season_str = 'S0' + str(end_season) if len(str(end_season)) == 1 \
                else 'S' + str(end_season)
            season_str = begin_season_str + '-' + end_season_str
        else:
            begin_season_str = 'S0' + str(begin_season) if len(str(begin_season)) == 1 \
                else 'S' + str(begin_season)
            season_str = begin_season_str
        return season_str

    def get_episode_info(self, pattern):
        """
        获取文件名中的集数（共同模块）
        :param pattern: 正则匹配信息
        :return: begin_episode:
        end_episode:
        total_episode:
        """

        total_episode = 1
        episodes = pattern.group(1)
        try:
            begin_episode, end_episode = self.list_to_be(episodes, 'e')
        except Exception as err:
            log.debug(f'识别集失败：{str(err)} - {traceback.format_exc()}')
            return None, None, None
        if begin_episode is None and isinstance(begin_episode, int):
            total_episode = 1
        if begin_episode is not None \
                and isinstance(end_episode, int) \
                and end_episode != begin_episode:
            total_episode = (end_episode - begin_episode) + 1
        return begin_episode, end_episode, total_episode

    def get_episode_num(self, title):
        """
        获取文件名中的集数
        :param title: 文件名
        :return: begin_episode:
        end_episode:
        total_episode:
        """
        episode_str = re.search(f"({_episode_re_1}|{_episode_re_2})", title, flags=re.IGNORECASE)
        episodes_str = re.search(f"({_episodes_re_1}|{_episodes_re_2})", title, flags=re.IGNORECASE)
        try:
            # 集组
            if episodes_str:
                return self.get_episode_info(episodes_str)
            # 集
            elif episode_str:
                episode = episode_str.group(1)
                episode_num = re.findall(_numbers_re, episode, flags=re.IGNORECASE)[0]
                return int(cn2an.cn2an(episode_num, mode='smart')), None, 1
            else:
                # 采用anitopy
                anitopy_info = anitopy.parse(title)
                if anitopy_info.get('episode_number'):
                    if isinstance(anitopy_info.get('episode_number'), list):
                        begin_episode = int(anitopy_info.get('episode_number')[0])
                        end_episode = int(anitopy_info.get('episode_number')[-1])
                        total_episode = (end_episode - begin_episode) + 1
                    else:
                        begin_episode = int(anitopy_info.get('episode_number'))
                        end_episode = None
                        total_episode = 1
                    return begin_episode, end_episode, total_episode
                else:
                    # 获取自定义识别词中的已有的集偏移信息进行匹配集数和集组的信息
                    offset_word_info_list = [offset_word_info if re.search(offset_word_info.FRONT, title)
                                             and re.search(offset_word_info.BACK, title) else None
                                             for offset_word_info in self.offset_words_info]
                    offset_word_info_list = list(filter(None, offset_word_info_list))
                    if offset_word_info_list:
                        front = offset_word_info_list[0].FRONT
                        back = offset_word_info_list[0].BACK
                        offset = offset_word_info_list[0].OFFSET
                        offset_word = f"{front}@{back}@{offset}"
                        custom_episodes_words_str = re.search(
                            rf'(?<=(?:{front}))((?:\d+|[一二三四五六七八九十]+)\s*\W*\s*(?:\d+|[一二三四五六七八九十]+))(?!(?:{back}))',
                            title,
                            flags=re.IGNORECASE)
                        return self.get_episode_info(custom_episodes_words_str)
                    else:
                        # 自定义情况
                        custom_episodes_words_str = re.search(r'(\d+\s*\W*\s*\d+)|(\d+)\W+', title.split('.')[0],
                                                              flags=re.IGNORECASE)
                        if custom_episodes_words_str:
                            return self.get_episode_info(custom_episodes_words_str)
                        else:
                            return 1, None, 1
        except Exception as err:
            log.error(f'【FileCore】获取集信息报错：{str(err)} - {traceback.format_exc()}')

    def handle_medias_df_dic(self, rmt):
        """
        将预处理的目录下的媒体文件信息用DataFrame存储
        :param rmt: 媒体文件后缀
        :return: df_list_level2:
        df_list_level1:
        total_episode:
        """
        df_list_level2 = []
        df_list_level1 = []
        level1_list = PathUtils.get_dir_level1_medias(self.dir_name)
        for level1_path in level1_list:
            # 判断预处理1级目录是否存在目录
            if os.path.isdir(level1_path):
                file_list = PathUtils.get_dir_files(level1_path, rmt)
                # 1级目录进行识别（存在二级目录）
                if len(PathUtils.get_dir_level1_dirs(level1_path)) != 0:
                    for dir_name in PathUtils.get_dir_level1_dirs(level1_path):
                        dir_dic = {dir_name: []}
                        for file_path in file_list:
                            dir_path, file_name = os.path.split(file_path)
                            if dir_name == dir_path:
                                dir_dic[dir_path].append(file_name)
                        df_list_level2.append(dir_dic)
                # 1级目录进行识别（不存在二级目录）
                else:
                    # 1级目录进行识别（1级目录下存在文件）
                    if PathUtils.get_dir_files(level1_path, rmt):
                        file_list = PathUtils.get_dir_files(level1_path, rmt)
                        dir_dic = {level1_path: []}
                        # 进行混合组合（未分季）
                        for file_path in file_list:
                            dir_path, file_name = os.path.split(file_path)
                            if level1_path == dir_path:
                                dir_dic[level1_path].append(file_name)
                            log.info(f'【FileCore】{dir_path} 目录下面存在文件{file_name}')
                        df_list_level1.append(dir_dic)
                    # 1级目录进行识别（1级目录下不存在文件）
                    else:
                        log.info(f'【FileCore】 {level1_path} 目录下面文件缺失')
            else:
                # 源目录进行识别
                log.info('【FileCore】' + level1_path)
        return df_list_level2, df_list_level1

    def handle_leve1_medias_df_dic(self, df_list_level1, begin_season, end_season):
        """
        通过获取季数来处理的一级目录下的媒体文件信息（/银魂/S01E01.mp4）
        :param df_list_level1: 传入的1级目录的列表
        :param begin_season: 传入的起始季的数字
        :param end_season: 传入的结束季的数字
        """
        df_list_level1_s = []
        for df in df_list_level1:
            season_str = self.get_season_str(begin_season, end_season)
            path = os.path.join(list(df.keys())[0], season_str)
            new_dir_dic = {path: []}
            for file_name in list(df.values())[0]:
                bs, es, tmp = self.get_season_num(file_name)
                season_str = self.get_season_str(bs, es)
                new_dir_path = os.path.join(list(df.keys())[0], season_str)
                if path == new_dir_path:
                    new_dir_dic[path].append(file_name)
            df_list_level1_s.append(new_dir_dic)
        return df_list_level1_s

    def get_series_ls(self, df):
        """
        获取同一个目录下的媒体文件信息的季信息和集信息列表
        :param df: 传入的DataFrame信息
        :return: begin_season_ls:
        end_season_ls:
        begin_episode_ls:
        end_episode_ls:
        """
        begin_season_ls = []
        end_season_ls = []
        total_season_ls = []
        begin_episode_ls = []
        end_episode_ls = []
        total_episode_ls = []
        for file_name in list(df.values())[0]:
            bs, es, ts = self.get_season_num(file_name) \
                if not self.get_season_num(os.path.split(list(df.keys())[0])[-1]) \
                else self.get_season_num(os.path.split(list(df.keys())[0])[-1])
            begin_season_ls.append(bs)
            end_season_ls.append(es)
            total_season_ls.append(ts)
            bp, ep, tp = self.get_episode_num(file_name)
            begin_episode_ls.append(bp)
            end_episode_ls.append(ep)
            total_episode_ls.append(tp)
        return begin_season_ls, end_season_ls, total_season_ls, begin_episode_ls, end_episode_ls, total_episode_ls

    @staticmethod
    def create_info_df(df_dic, begin_season_ls, end_season_ls, total_season_ls, begin_episode_ls, end_episode_ls,
                       total_episode_ls):
        """
        创建文件名的相关信息的DataFrame
        :param df_dic: DataFrame的字典
        :param begin_season_ls: 识别出来的集数列表
        :param end_season_ls: 识别出来的季数列表
        :param total_season_ls: 识别出来的集数列表
        :param begin_episode_ls: 识别出来的集数列表
        :param end_episode_ls: 识别出来的季数列表
        :param total_episode_ls: 识别出来的季数列表
        :return:
        """
        df = pd.DataFrame({list(df_dic.keys())[0]: list(df_dic.values())[0]})
        df['begin_episode'] = begin_episode_ls
        df['end_episode'] = end_episode_ls
        df['total_episode'] = total_episode_ls
        df_sorted = df.sort_values(by=['begin_episode'])
        df_sorted = df_sorted.reset_index()

        df_sorted['sort_end_episode'] = [
            df_sorted.loc[0: i, ["total_episode"]].sum(axis=0)['total_episode'] if not pd.isna(
                df_sorted['end_episode'][i]) else None for i in range(0, df_sorted.shape[0])]
        df_sorted['sort_begin_episode'] = [df_sorted['sort_end_episode'][i - 1] + 1 if not pd.isna(
            df_sorted['sort_end_episode'][i]) and i > 1 and not pd.isna(df_sorted['sort_end_episode'][i - 1]) else i + 1
                                           for i in range(0, df_sorted.shape[0])]
        df_sorted['begin_season'] = begin_season_ls
        df_sorted['end_season'] = end_season_ls
        df_sorted['total_season'] = total_season_ls
        df_sorted['file_suffix'] = [os.path.splitext(df_sorted[list(df_dic.keys())[0]][i])[-1] for i in
                                    range(0, df_sorted.shape[0])]
        original_file_path = [os.path.join(df_sorted.columns[1], df_sorted[list(df_dic.keys())[0]][i]) for i in
                              range(0, df_sorted.shape[0])]
        df_sorted['original_file_path'] = original_file_path
        begin_season_str = ['S' + (
            '0' + str(int(df_sorted['begin_season'][i])) if len(str(int(df_sorted['begin_season'][i]))) == 1 else str(
                int(df_sorted['begin_season'][i]))) for i in range(0, df_sorted.shape[0])]
        end_season_str = [('S' + (
            '0' + str(int(df_sorted['end_season'][i])) if len(str(int(df_sorted['end_season'][i]))) == 1 else str(
                int(df_sorted['end_season'][i])))) if not pd.isna(df_sorted['end_season'][i]) else None for i in
                          range(0, df_sorted.shape[0])]
        sorted_begin_episode_str = ['E' + ('0' + str(int(df_sorted['sort_begin_episode'][i])) if len(
            str(int(df_sorted['sort_begin_episode'][i]))) == 1 else str(int(df_sorted['sort_begin_episode'][i]))) for i
                                    in range(0, df_sorted.shape[0])]
        sorted_end_episode_str = [('E' + ('0' + str(int(df_sorted['sort_end_episode'][i])) if len(
            str(int(df_sorted['sort_end_episode'][i]))) == 1 else str(
            int(df_sorted['sort_end_episode'][i])))) if not pd.isna(df_sorted['sort_end_episode'][i]) else None for i in
                                  range(0, df_sorted.shape[0])]
        begin_episode_str = ['E' + (
            '0' + str(int(df_sorted['begin_episode'][i])) if len(str(int(df_sorted['begin_episode'][i]))) == 1 else str(
                int(df_sorted['begin_episode'][i]))) for i in range(0, df_sorted.shape[0])]
        end_episode_str = [('E' + (
            '0' + str(int(df_sorted['end_episode'][i])) if len(str(int(df_sorted['end_episode'][i]))) == 1 else str(
                int(df_sorted['end_episode'][i])))) if not pd.isna(df_sorted['end_episode'][i]) else None for i in
                           range(0, df_sorted.shape[0])]
        season_str = [begin_season_str[i] + end_season_str[i] if end_season_str[i] else begin_season_str[i] for i in
                      range(0, df_sorted.shape[0])]
        sorted_episode_str = [
            sorted_begin_episode_str[i] + sorted_end_episode_str[i] if not pd.isna(sorted_end_episode_str[i]) else
            sorted_begin_episode_str[i] for i in range(0, df_sorted.shape[0])]
        episode_str = [
            begin_episode_str[i] + end_episode_str[i] if not pd.isna(end_episode_str[i]) else begin_episode_str[i] for i
            in range(0, df_sorted.shape[0])]
        df_sorted['season_str'] = season_str
        df_sorted['episode_str'] = episode_str
        df_sorted['sorted_episode_str'] = sorted_episode_str
        df_sorted['new_file_path'] = [os.path.join(df_sorted.columns[1],
                                                   df_sorted['season_str'][i] + df_sorted['episode_str'][i] +
                                                   df_sorted['file_suffix'][i]) for i in range(0, df_sorted.shape[0])]
        df_sorted['new_sort_file_path'] = [os.path.join(df_sorted.columns[1],
                                                        df_sorted['season_str'][i] + df_sorted['sorted_episode_str'][i] +
                                                        df_sorted['file_suffix'][i]) for i in
                                           range(0, df_sorted.shape[0])]
        return df_sorted

    def run(self, sort_flag):
        """
        主程序（目前仅适用于二级目录）
        :param sort_flag: 是否重新排序
        """
        try:
            # 媒体文件
            df_list_level2_media, df_list_level1_media = self.handle_medias_df_dic(rmt=RMT_MEDIAEXT)
            for df_level2_media in df_list_level2_media:
                begin_season_ls, end_season_ls, total_season_ls, begin_episode_ls, end_episode_ls, total_episode_ls = \
                    self.get_series_ls(df_level2_media)
                df = self.create_info_df(df_level2_media, begin_season_ls, end_season_ls, total_season_ls,
                                                begin_episode_ls, end_episode_ls, total_episode_ls)
                for i in range(0, len(df)):
                    if sort_flag:
                        # os.rename(df_sorted['original_file_path'][i], df_sorted['new_sort_file_path'][i])
                        log.info(f"【FileCore】媒体文件 识别到重新排序标记：源文件{df['original_file_path'][i]} 已替换 {df['new_sort_file_path'][i]}")
                    else:
                        # os.rename(df_sorted['original_file_path'][i], df_sorted['new_file_path'][i])
                        log.info(f"【FileCore】媒体文件 未识别到重新排序标记：源文件{df['original_file_path'][i]} 已替换 {df['new_file_path'][i]}")
            # 字幕文件
            df_list_level2_sub, df_list_level1_sub = self.handle_medias_df_dic(rmt=RMT_SUBEXT)
            for df_level2_sub in df_list_level2_sub:
                begin_season_ls, end_season_ls, total_season_ls, begin_episode_ls, end_episode_ls, total_episode_ls = \
                    self.get_series_ls(df_level2_sub)
                df = self.create_info_df(df_level2_sub, begin_season_ls, end_season_ls, total_season_ls,
                                         begin_episode_ls, end_episode_ls, total_episode_ls)
                for i in range(0, len(df)):
                    if sort_flag:
                        # os.rename(df_sorted['original_file_path'][i], df_sorted['new_sort_file_path'][i])
                        log.info(
                            f"【FileCore】字幕文件 识别到重新排序标记：源文件{df['original_file_path'][i]} 已替换 {df['new_sort_file_path'][i]}")
                    else:
                        # os.rename(df_sorted['original_file_path'][i], df_sorted['new_file_path'][i])
                        log.info(f"【FileCore】字幕文件 未识别到重新排序标记：源文件{df['original_file_path'][i]} 已替换 {df['new_file_path'][i]}")

        except Exception as err:
            log.error(f'【FileCore】预处理报错：{str(err)} - {traceback.format_exc()}')


if __name__ == '__main__':
    dir = r'E:\test\tmp'
    sortflag = False
    file_helper = FileHelper(dir)
    df_list_level2, df_list_level1 = file_helper.handle_medias_df_dic(rmt=RMT_MEDIAEXT)
    for df_dic in df_list_level2:
        begin_season_ls, end_season_ls, total_season_ls, begin_episode_ls, end_episode_ls, total_episode_ls = \
            file_helper.get_series_ls(df_dic)
        df = file_helper.create_info_df(df_dic, begin_season_ls, end_season_ls, total_season_ls,
                                        begin_episode_ls, end_episode_ls, total_episode_ls)
        for i in range(0, len(df)):
            if sortflag:
                # os.rename(df_sorted['original_file_path'][i], df_sorted['new_sort_file_path'][i])
                log.debug(f"【FileCore】识别到重新排序标记：源文件{df['original_file_path'][i]} 已替换 {df['new_sort_file_path'][i]}")
            else:
                # os.rename(df_sorted['original_file_path'][i], df_sorted['new_file_path'][i])
                log.debug(f"【FileCore】未识别到重新排序标记：源文件{df['original_file_path'][i]} 已替换 {df['new_file_path'][i]}")