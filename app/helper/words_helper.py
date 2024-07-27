import regex as re

from app.helper import DbHelper
from app.utils.commons import singleton
from app.utils.exception_utils import ExceptionUtils
import cn2an


@singleton
class WordsHelper:
    dbhelper = None
    ignored_words_info = []
    ignored_words_noregex_info = []
    replaced_words_info = []
    replaced_words_noregex_info = []
    replaced_offset_words_info = []
    offset_words_info = []

    def __init__(self):
        self.init_config()

    def init_config(self):
        self.dbhelper = DbHelper()
        self.ignored_words_info = self.dbhelper.get_custom_words(enabled=1, wtype=1, regex=1)
        self.ignored_words_noregex_info = self.dbhelper.get_custom_words(enabled=1, wtype=1, regex=0)
        self.replaced_words_info = self.dbhelper.get_custom_words(enabled=1, wtype=2, regex=1)
        self.replaced_words_noregex_info = self.dbhelper.get_custom_words(enabled=1, wtype=2, regex=0)
        self.replaced_offset_words_info = self.dbhelper.get_custom_words(enabled=1, wtype=3, regex=1)
        self.offset_words_info = self.dbhelper.get_custom_words(enabled=1, wtype=4, regex=1)

    def process(self, title):
        # 错误信息
        msg = []
        # 应用自定义识别
        used_ignored_words = []
        # 应用替换
        used_replaced_words = []
        # 应用集偏移
        used_offset_words = []
        # 屏蔽
        if self.ignored_words_info:
            for ignored_word_info in self.ignored_words_info:
                ignored = ignored_word_info.REPLACED
                ignored_word = ignored
                title, ignore_msg, ignore_flag = self.replace_regex(title, ignored, '')
                if ignore_flag:
                    used_ignored_words.append(ignored_word)
                elif ignore_msg:
                    msg.append(f"自定义屏蔽词 {ignored_word} 设置有误：{ignore_msg}")
        if self.ignored_words_noregex_info:
            for ignored_word_noregex_info in self.ignored_words_noregex_info:
                ignored = ignored_word_noregex_info.REPLACED
                ignored_word = ignored
                title, ignore_msg, ignore_flag = self.replace_regex(title, ignored, '')
                if ignore_flag:
                    used_ignored_words.append(ignored_word)
                elif ignore_msg:
                    msg.append(f"自定义屏蔽词 {ignored_word} 设置有误：{ignore_msg}")
        # 替换
        if self.replaced_words_info:
            for replaced_word_info in self.replaced_words_info:
                replaced = replaced_word_info.REPLACED
                replace = replaced_word_info.REPLACE
                replaced_word = f"{replaced}@{replace}"
                title, replace_msg, replace_flag = self.replace_regex(title, replaced, replace)
                if replace_flag:
                    used_replaced_words.append(replaced_word)
                elif replace_msg:
                    msg.append(f"自定义替换词 {replaced_word} 格式有误：{replace_msg}")
        if self.replaced_words_noregex_info:
            for replaced_word_noregex_info in self.replaced_words_noregex_info:
                replaced = replaced_word_noregex_info.REPLACED
                replace = replaced_word_noregex_info.REPLACE
                replaced_word = f"{replaced}@{replace}"
                title, replace_msg, replace_flag = self.replace_noregex(title, replaced, replace)
                if replace_flag:
                    used_replaced_words.append(replaced_word)
                elif replace_msg:
                    msg.append(f"自定义替换词 {replaced_word} 格式有误：{replace_msg}")
        # 替换+集偏移
        if self.replaced_offset_words_info:
            for replaced_offset_word_info in self.replaced_offset_words_info:
                replaced = replaced_offset_word_info.REPLACED
                replace = replaced_offset_word_info.REPLACE
                front = replaced_offset_word_info.FRONT
                back = replaced_offset_word_info.BACK
                offset = replaced_offset_word_info.OFFSET
                replaced_word = f"{replaced}@{replace}"
                offset_word = f"{front}@{back}@{offset}"
                replaced_offset_word = f"{replaced}@{replace}@{front}@{back}@{offset}"
                # 记录替换前title
                title_cache = title
                # 替换
                title, replace_msg, replace_flag = self.replace_regex(title, replaced, replace)
                # 替换应用成功进行集数偏移
                if replace_flag:
                    title, offset_msg, offset_flag = self.episode_offset(title, front, back, offset)
                    # 集数偏移应用成功
                    if offset_flag:
                        used_replaced_words.append(replaced_word)
                        used_offset_words.append(offset_word)
                    elif offset_msg:
                        # 还原title
                        title = title_cache
                        msg.append(
                            f"自定义替换+集偏移词 {replaced_offset_word} 集偏移部分格式有误：{offset_msg}")
                elif replace_msg:
                    msg.append(f"自定义替换+集偏移词 {replaced_offset_word} 替换部分格式有误：{replace_msg}")
        # 集数偏移
        if self.offset_words_info:
            for offset_word_info in self.offset_words_info:
                front = offset_word_info.FRONT
                back = offset_word_info.BACK
                offset = offset_word_info.OFFSET
                offset_word = f"{front}@{back}@{offset}"
                title, offset_msg, offset_flag = self.episode_offset(title, front, back, offset)
                if offset_flag:
                    used_offset_words.append(offset_word)
                elif offset_msg:
                    msg.append(f"自定义集偏移词 {offset_word} 格式有误：{offset_msg}")

        return title, msg, {"ignored": used_ignored_words,
                            "replaced": used_replaced_words,
                            "offset": used_offset_words}

    @staticmethod
    def replace_regex(title, replaced, replace):
        try:
            if not re.findall(r'%s' % replaced, title):
                return title, "", False
            else:
                return re.sub(r'%s' % replaced, r'%s' % replace, title), "", True
        except Exception as err:
            ExceptionUtils.exception_traceback(err)
            return title, str(err), False

    @staticmethod
    def replace_noregex(title, replaced, replace):
        try:
            if title.find(replaced) == -1:
                return title, "", False
            else:
                return title.replace(replaced, replace), "", True
        except Exception as err:
            ExceptionUtils.exception_traceback(err)
            return title, str(err), False

    @staticmethod
    def episode_offset(title, front, back, offset):
        try:
            if back and not re.findall(r'%s' % back, title):
                return title, "", False
            if front and not re.findall(r'%s' % front, title):
                return title, "", False
            offset_word_info_re = re.compile(r'(?<=%s.*?)[0-9一二三四五六七八九十]+(?=.*?%s)' % (front, back))
            episode_nums_str = re.findall(offset_word_info_re, title)
            if not episode_nums_str:
                return title, "", False
            episode_nums_offset_str = []
            offset_order_flag = False
            for episode_num_str in episode_nums_str:
                episode_num_int = int(cn2an.cn2an(episode_num_str, "smart"))
                offset_caculate = offset.replace("EP", str(episode_num_int))
                episode_num_offset_int = int(eval(offset_caculate))
                # 向前偏移
                if episode_num_int > episode_num_offset_int:
                    offset_order_flag = True
                # 向后偏移
                elif episode_num_int < episode_num_offset_int:
                    offset_order_flag = False
                # 原值是中文数字，转换回中文数字，阿拉伯数字则还原0的填充
                if not episode_num_str.isdigit():
                    episode_num_offset_str = cn2an.an2cn(episode_num_offset_int, "low")
                else:
                    count_0 = re.findall(r"^0+", episode_num_str)
                    if count_0:
                        episode_num_offset_str = f"{count_0[0]}{episode_num_offset_int}"
                    else:
                        episode_num_offset_str = str(episode_num_offset_int)
                episode_nums_offset_str.append(episode_num_offset_str)
            episode_nums_dict = dict(zip(episode_nums_str, episode_nums_offset_str))
            # 集数向前偏移，集数按升序处理
            if offset_order_flag:
                episode_nums_list = sorted(episode_nums_dict.items(), key=lambda x: x[1])
            # 集数向后偏移，集数按降序处理
            else:
                episode_nums_list = sorted(episode_nums_dict.items(), key=lambda x: x[1], reverse=True)
            for episode_num in episode_nums_list:
                episode_offset_re = re.compile(
                    r'(?<=%s.*?)%s(?=.*?%s)' % (front, episode_num[0], back))
                title = re.sub(episode_offset_re, r'%s' % episode_num[1], title)
            return title, "", True
        except Exception as err:
            ExceptionUtils.exception_traceback(err)
            return title, str(err), False
