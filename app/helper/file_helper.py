from config import RMT_MEDIAEXT, RMT_SUBEXT, _subtitle_season_re, _subtitle_season_all_re, _subtitle_episode_re, \
    _subtitle_episode_all_re
import re
import pandas as pd
from app.helper import DbHelper
from app.utils import PathUtils, Tokens
import os


class FileHelper:
    """
    规整处理文件目录
    :param sortflag: 是否重新排序
    :param subtitle: 副标题、描述
    :param mtype: 指定识别类型，为空则自动识别类型
    :return: MetaAnime、MetaVideo
    """
    dbhelper = None
    sortflag = False
    offset_words_info = []

    def __init__(self, dirname):
        self.init_config()
        self.dir_name = dirname

    def init_config(self):
        self.dbhelper = DbHelper()
        self.offset_words_info = self.dbhelper.get_custom_words(enabled=1, wtype=4, regex=1)

    def get_esp_num(self, title):
        """
        获取文件名中的集数
        :param title: 文件名
        :return: esp_num
        """
        esp_num = None
        episode_str = re.search(r'%s' % _subtitle_episode_re, title, re.IGNORECASE)
        episodes = episode_str.group(1) if episode_str else None
        if episodes:
            esp_num = episodes.upper().replace("E", "").replace("P", "").strip()
        else:
            if self.offset_words_info:
                for offset_word_info in self.offset_words_info:
                    front = offset_word_info.FRONT
                    back = offset_word_info.BACK
                    offset = offset_word_info.OFFSET
                    offset_word = f"{front}@{back}@{offset}"
                    offset_word_info_re = re.compile(rf'(?<=(?:{front}))(\d+)(?!(?:{back}))')
                    while re.findall(offset_word_info_re, title):
                        esp_num = re.findall(offset_word_info_re, title)[0]
                if not esp_num:
                    esp_num = re.findall(r'\d+', title)[0]
            else:
                esp_num = re.findall(r'\d+', title)[0]
        return esp_num

    def get_season_num(self, title):
        """
        获取文件名中的季数
        :param title: 文件名
        :return: season_num
        """
        pass

    def dir_df_dic(self):
        """
        将预处理的目录下的文件信息用DataFram存储
        :return: df_list_three
        """
        level1_list = PathUtils.get_dir_level1_medias(self.dir_name)
        df_list_three = []
        df_list_two = []
        for level1_path in level1_list:
            # 判断预处理1级目录是否存在目录
            if os.path.isdir(level1_path):
                file_list = PathUtils.get_dir_files(level1_path, RMT_MEDIAEXT)
                # 1级目录进行识别（存在二级目录）
                if len(PathUtils.get_dir_level1_dirs(level1_path)) != 0:
                    for dir_name in PathUtils.get_dir_level1_dirs(level1_path):
                        dir_dic = {dir_name: []}
                        for file_path in file_list:
                            dir_path, file_name = os.path.split(file_path)
                            if dir_name == dir_path:
                                dir_dic[dir_path].append(file_name)
                        df_list_three.append(dir_dic)
                # 1级目录进行识别（不存在二级目录）
                else:
                    # 1级目录进行识别（1级目录下存在文件）
                    if PathUtils.get_dir_files(level1_path, RMT_MEDIAEXT):
                        file_list = PathUtils.get_dir_files(level1_path, RMT_MEDIAEXT)
                        for file_path in file_list:
                            dir_path, file_name = os.path.split(file_path)
                            # 识别文件中是否存在季信息
                            self.get_season_num()
                            # 根据季信息进行归类重新排序处理

                            print(dir_path + f' 目录下面存在文件{file_name}')
                    # 1级目录进行识别（1级目录下不存在文件）
                    else:
                        print(level1_path + ' 目录下面文件缺失')
            else:
                # 源目录进行识别
                print(level1_path)
        return df_list_three

    @staticmethod
    def create_info_df(df_dic, esp_num_ls, season_num_ls):
        """
        创建文件名的相关信息的DataFram
        :param df_dic: DataFram的字典
        :param esp_num_ls: 识别出来的集数列表
        :param season_num_ls: 识别出来的季数列表
        :return:
        """
        df = pd.DataFrame({list(df_dic.keys())[0]: list(df_dic.values())[0]})
        df['esp_num'] = esp_num_ls
        df_sorted = df.sort_values(by=['esp_num'])
        df_sorted['sort_esp_num'] = [i for i in range(1, df_sorted.shape[0] + 1)]
        df_sorted['season_num'] = season_num_ls
        df_sorted['file_suffix'] = [os.path.splitext(df_sorted.iloc[i][0])[-1] for i in range(0, df_sorted.shape[0])]

        original_file_path = [os.path.join(df_sorted.columns[0], df_sorted.iloc[i][0]) for i in
                              range(0, df_sorted.shape[0])]
        df_sorted['original_file_path'] = original_file_path
        new_sort_file_path = [os.path.join(df_sorted.columns[0], df_sorted.iloc[i][3] + 'E' + (
            '0' + str(df_sorted.iloc[i][2]) if len(str(df_sorted.iloc[i][2])) == 1 else str(df_sorted.iloc[i][2])) +
                                           df_sorted.iloc[i][4]) for i in range(0, df_sorted.shape[0])]
        df_sorted['new_sort_file_path'] = new_sort_file_path
        new_file_path = [os.path.join(df_sorted.columns[0], df_sorted.iloc[i][3] + 'E' + (
            '0' + str(df_sorted.iloc[i][1]) if len(str(df_sorted.iloc[i][1])) == 1 else str(df_sorted.iloc[i][1])) +
                                      df_sorted.iloc[i][4]) for i in range(0, df_sorted.shape[0])]
        df_sorted['new_file_path'] = new_file_path
        return df_sorted

    @staticmethod
    def rename_filename(df_sorted):
        """
        批量修改文件名
        """
        for i in range(0, len(df_sorted)):
            os.rename(df_sorted['original_file_path'][i], df_sorted['new_sort_file_path'][i])
            print(df_sorted['original_file_path'][i], df_sorted['new_sort_file_path'][i])

    def run(self):
        pass
