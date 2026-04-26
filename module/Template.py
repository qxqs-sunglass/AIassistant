class Template:
    def __init__(self):
        """
        标准api模板
        """
        self.intro = ""
        self.Work_dict = {}
        self.tools = []

    def init(self):
        """初始化对象"""

    def using_tool(self, tool_name, **kwargs):
        """
        调用目标tool
        :param tool_name:
        :return:
        """
        if tool_name not in self.Work_dict.keys():
            return False
        self.Work_dict[tool_name](kwargs=kwargs)
        return True