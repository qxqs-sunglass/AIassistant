from Config import DEFAULT_PATH, PATH_DICT
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
        self.FIRST_PROMPT_1: str = f"""
|根据文本内容，判断{self.AI_NAME}（有谐音的可能）是否存在，如果没有输出：None（即：无类型）
并基于以上文本，通过以下标签和文本指向的标签，输出属于文本的对应标签，如果没有请输出：对应操作类型标签
不用给出思考过程，请直接给出答案|
支持的操作类型（严格遵守）："""
        self.FIRST_PROMPT_2: str = """
输出格式为json结构，且在输出的指令中所有标点符号必须为英文字符，请严格按照一下格式输出指令：
{ans: "目标类型"}
"""
        # ai第一轮提炼提示 注：相关操作类型必须在mod中标出，指定的位置为:self.intro
        # 注：第三轮为函数操作，为了方便，所以会在指定的module中制定提示词 名称为：WorkWord

    def init_config(self):
        """
        注：必须在外部调用此函数
        """
        # 相关url
        self.SEND_MESSAGE_URL: str = f"{self.OLLAMA_HOST}/api/generate"
        self.TEST_RUL = f"{self.OLLAMA_HOST}/api/tags"
        self.CHAR_RUL = f"{self.OLLAMA_HOST}/api/chat"
        self.loading()

    def run(self):
        pass

    def update(self):
        pass

    def loading(self):
        logger.log("开始加载配置", self.ID, "INFO")
        logger.log("加载基础配置", self.ID, "INFO")
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["BASIS"]), "r", encoding="utf-8") as f:
                basis_dict = json.load(f)
                f.close()
            for key, value in basis_dict.items():
                setattr(self, key, value)
        except Exception as e:
            logger.log(f"加载基础配置失败，原因：{e}", self.ID, "ERROR")
        logger.log("加载基础配置完成", self.ID, "INFO")

    def reply_test(self, ID):
        """
        响应自检
        :return:
        """
        logger.log(f"{self.ID}, 自检响应成功", ID, "INFO")
        return True

