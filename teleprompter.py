import json


class TelePrompter:
    def __init__(self, master):
        """存储提示词的类"""
        self.master = master
        self.prompt_data = {}

    def init(self):
        """
        初始化
        :return:
        """
        with open("config/prompt.json", "r", encoding="utf-8") as f:
            self.prompt_data = json.load(f)

    def get(self, attr) -> str|None:
        """
        获取目标提示词，注：这里只会返回字符串的文本
        :param attr:
        :return:
        """
        if attr not in self.prompt_data:
            return None
        return self.prompt_data[attr]
