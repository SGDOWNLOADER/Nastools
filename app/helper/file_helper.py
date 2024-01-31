from config import RMT_MEDIAEXT, RMT_SUBEXT, _subtitle_season_re, _subtitle_season_all_re, _subtitle_episode_re, _subtitle_episode_all_re
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


    def reset_filename(self, file_list):
        if self.sortflag:

            file_list = sorted(file_list, key=lambda item: (int(re.sub('\D', '', item)), item))


    def get_esp_num(self, title):
        """
        获取文件名的集数
        :param title: 标题、种子名、文件名
        :param subtitle: 副标题、描述
        :param mtype: 指定识别类型，为空则自动识别类型
        :return: MetaAnime、MetaVideo
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

    def get_season_num(self):
        pass

    def dir_df_dic(self):
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
                            self.recognize_season()
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
    def create_info_df(sortflag, esp_num_ls, file_list):
        """
        创建文件名的相关信息的DataFram
        :param title: 标题、种子名、文件名
        :param subtitle: 副标题、描述
        :param mtype: 指定识别类型，为空则自动识别类型
        :return: MetaAnime、MetaVideo
        """
        df = pd.DataFrame({'esp_num': esp_num_ls}, index=file_list)
        df_sorted = df.sort_values(by=['esp_num'])
        sort_lst = [i for i in range(1, df_sorted.shape[0] + 1)] if sortflag else esp_num_ls
        df_sorted['sort_num'] = sort_lst
        return df_sorted

    def run(self):
        pass