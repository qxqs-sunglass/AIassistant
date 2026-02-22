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

        self.FIRST_PROMPT_1: str = f"""
|你必须基于一下规则回答文本的问题：
1.只有带有'{self.AI_NAME}'字段的文本，才能对json格式中，键"active"的值修改为:true，否则只能为：false
2.针对文本，通过比对操作类型表，输出属于文本的对应标签（英文+大写）
3.请严格按照json格式输出（输出的指令内所有键必须为英文字符并使用英文的引号）
4.不用给出思考过程，请直接给出结果|
操作类型表："""
        self.FIRST_PROMPT_2: str = """
输出示例：
{"ans": "MEDIA_C","active": true}  # 有目标字段，有指向操作
{"ans": "None", "active": False}  # 无目标字段
{"ans": "None", "active": true}  # 有目标字段，无指向操作
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
        # loading
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

