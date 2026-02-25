from Config import DEFAULT_PATH, PATH_DICT
from module import API_instance
import Logger
import json
import os


logger = Logger.get_logger()


class RControl:
    def __init__(self, master):
        """
        资源管理器
        :param master:
        """
        self.ID = "RControl"
        self.master = master
        # 本地ai部署使用
        self.DEFAULT_PATH = DEFAULT_PATH
        self.PATH_DICT = PATH_DICT
        self.OLLAMA_HOST = "http://localhost:11434"
        self.DEFAULT_MODEL: str = "gemma3:1b"
        self.AI_NAME: str = "小平同学"
        self.LOOP_INTERVAL = 0.7
        # 相关url
        self.SEND_MESSAGE_URL: str = f""  # 发送消息url
        self.TEST_RUL: str = f""  # 链接测试url
        self.CHAR_RUL: str = f""  # 聊天url
        # 语音配置
        self.SPEECH_LANGUAGE: str = "zh-CN"  # 中文
        self.VOICE_RATE: int = 160  # 语速
        self.VOICE_VOLUME: float = 1.0  # 音量
        # 录音配置
        self.ONE_AUDIO_LENGTH: float = 6.0  # 单个录音时长(单位：秒)
        self.IN_INTERVAL: float = 3.0  # 每次录音间隔(单位：秒)
        self.SEND_TIME: float = 10.0  # 发送消息间隔(单位：秒)
        # 模型参数
        self.TEMPERATURE: float = 0.7
        self.TOP_P: float = 0.9
        self.NUM_PREDICT: int = 1000

        self.module_dict = {}  # api实例
        self.module_intro = []  # api介绍
        # 导入api
        for name, ins in API_instance.items():
            n = ins()
            n.init()
            self.module_dict[name] = n  # 动态导入
            self.module_intro.append(self.module_dict[name].intro)

        # 提炼提示
        self.FIRST_PROMPT_1 = ""
        self.OPENAI_PROMPT = ""
        self.FIRST_PROMPT_2 = ""
        self.PROMPT_E = ""
        # ai第一轮提炼提示 注：相关操作类型必须在mod中标出，指定的位置为:self.intro
        # 注：第三轮为函数操作，为了方便，所以会在指定的module中制定提示词 名称为：WorkWord
        # 联网ai，deepseek、chat-GPT
        self.openai_api = ""  # 用户使用的api
        self.basis_url = ""  # 目标网址
        self.openai_module = ""  # 主选ai大模型
        self.openai_module_minor = ""  # 次选ai大模型
        self.openai_tools = []  # 工具
        self.openai_active = "normal"  # ai状态

    def init_config(self):
        """
        注：必须在外部调用此函数
        """
        # 相关url
        self.SEND_MESSAGE_URL: str = f"{self.OLLAMA_HOST}/api/generate"
        self.TEST_RUL = f"{self.OLLAMA_HOST}/api/tags"
        self.CHAR_RUL = f"{self.OLLAMA_HOST}/api/chat"
        # loading
        logger.log("开始加载配置", self.ID, "INFO")
        logger.log("加载基础配置", self.ID, "INFO")
        # 基础设置
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["BASIS"]), "r", encoding="utf-8") as f:
                basis_dict = json.load(f)
                f.close()
            for key, value in basis_dict.items():
                setattr(self, key, value)
        except Exception as e:
            logger.log(f"加载基础配置失败，原因：{e}", self.ID, "ERROR")
        # 加载openai设置
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["OPENAI"]), "r", encoding="utf-8") as f:
                openai_dict = json.load(f)
                f.close()
            for key, value in openai_dict.items():
                setattr(self, key, value)
        except Exception as e:
            logger.log(f"用户未配置openai设置，{e}", self.ID, "ERROR")
        logger.log("加载基础配置完成", self.ID, "INFO")

        # 设置提示词
        self.FIRST_PROMPT_1: str = f"""
|你必须基于一下规则回答文本的问题：
2.针对文本，通过比对操作类型表，输出属于文本的对应标签（冒号右侧的大写英文）
3.请严格按照json格式输出（输出的指令内所有键和值如果是字符串类型，则必须使用英文字符和英文的引号）|
操作类型表："""
        self.FIRST_PROMPT_2: str = """
输出示例：
{"ans": "MEDIA_C"}  # 文本内容指向了MEDIA_C
{"ans": "SYS_C"}  # 文本内容指向了SYS_C
"""
        self.OPENAI_PROMPT: str = """|针对用户指令，结合tools中的工具，目的是完成指令内容，如果指令内容没有对应的tool，请回答：抱歉我听不懂。|
指令：
"""

    def reply_test(self, ID):
        """
        响应自检
        :return:
        """
        logger.log(f"{self.ID}, 自检响应成功", ID, "INFO")
        return True

