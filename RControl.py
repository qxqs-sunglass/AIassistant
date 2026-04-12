from Config import DEFAULT_PATH, PATH_DICT
from instance.ModelOpenai import ModelOpenai
from instance.ModelOllama import ModelOllama
from module import API_instance
import Logger
import json
import os


logger = Logger.get_logger()
AI_TYPE1 = "openai"
AI_TYPE2 = "ollama"


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
        self.AI_NAME: str = "小平同学"
        self.LOOP_INTERVAL = 0.7
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
        self.confidence_threshold: int = 70  # 模型对指令信心度临界值，临界值以下加入人工操作
        self.tool_choice = "none"  # 使用openai调用模型时是否强制使用tools
        self.scheme = ""
        self.using_token = {}  # 各类token用量统计

        # 系统api设置
        self.module_dict = {}  # api实例
        self.load_list = []
        # 联网ai：deepseek、chat-GPT
        # 注：这里是负责控制ai_client.py中对ai发送消息的状态变量，是否启用该项发送消息
        self.openai_active = True  # openai接口的链接状态 true表示可以使用状态
        self.ollama_active = True   # 工具ollama链接状态
        # 设置
        self.model_data = {}  # 储存ai模型
        # 特别标注：openai的实例被放在的目标模型下的client标签中
        self.key_data = {}
        self.key_active = True  # openai需要的API key
        self.ai_active = True  # 确认是否有可运行的ai

    def init_config(self):
        """
        注：必须在外部调用此函数
        """
        # loading
        logger.log("开始加载配置", self.ID, "INFO")
        logger.log("加载基础配置", self.ID, "INFO")
        # 基础设置
        logger.info("正在加载基础设置", self.ID)
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["BASIS"]), "r", encoding="utf-8") as f:
                basis_dict = json.load(f)
            for key, value in basis_dict.items():
                setattr(self, key, value)
        except Exception as e:
            logger.log(f"加载基础配置失败，原因：{e}", self.ID, "ERROR")
        logger.info("基础设置加载完成", self.ID)

        # 加载ai_key
        logger.info("正在尝试读取key文件", self.ID)
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["KEY"]), "r", encoding="utf-8") as f:
                self.key_data = json.load(f)
            logger.log("已成功加载key.json文件", self.ID, "INFO")
        except Exception as e:
            self.key_active = False
            logger.error(f"用户未配置key.json，{e}", self.ID)
        logger.info("key加载完成", self.ID)

        # 加载ai模型设置
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["AI_MODEL"]), "r", encoding="utf-8") as f:
                data = json.load(f)
            for aim in data:
                if aim.get("ai_type", "None") == AI_TYPE1 and self.key_active:
                    model = ModelOpenai()
                    model.init(aim)
                    self.model_data[model.name] = model
                elif aim["ai_type"] == AI_TYPE2:
                    model = ModelOllama()
                    model.init(aim)
                    self.model_data[model.name] = model
                else:
                    logger.warning("未知类型的ai源", self.ID)

                self.model_data[aim["name"]] = aim  #  保存数据
        except Exception as e:
            logger.log(f"用户未正确配置ai_model.json，{e}", self.ID, "ERROR")
        logger.log("加载基础配置完成", self.ID, "INFO")
        # 导入api
        for name, ins in API_instance.items():
            n = ins()
            n.init()
            self.module_dict[name] = n  # 动态导入

        if len(self.load_list) > 0:  # 导入额外数据，注：必须确保文件名和变量值一样
           for attr in self.load_list:
               name = os.path.split(attr)[-1]
               name = name.rsplit(".", 1)[0]
               self.load(attr, name)

    def verify(self):
        """资源校验"""
        self.openai_active = True
        self.ollama_active = True
        for v in self.model_data.values():
            v: ModelOpenai|ModelOllama
            msgs = v.connect()
            if "error" in msgs or "ERROR" in msgs:
                if v.ai_type == AI_TYPE1:
                    self.ollama_active = False
                else:
                    self.openai_active = False
            logger.decoupling(msgs, self.ID)

    def remove_ai(self, name):
        if name not in self.model_data.keys():
            return
        self.model_data.pop(name)


    def load(self, path: str, target: str) -> dict:
        """
        热加载单元，只读取.json文件，其他文件不予读取
        :param path: 文件路径（绝对或相对路径）
        :param target: 保存数据的地址（变量名）
        :return:
        """
        if not os.path.exists(os.path.join(path)):
            return {"error": f"不存在的路径：{path}"}
        p = path.split(".")
        p = p[-1]
        if p == "json":
            with open(path, "r") as f:
                data = json.load(f)
            temp = self.__getattribute__(target)  # 为了防止数据丢失，故，先定向后更新
            temp.update(data)
            return {"success": True, "data": temp}
        return {"error": f"未知：{path}"}

    def save(self, path: str, target: str):
        """
        保存文件，只保存.json文件
        :param path: 文件路径
        :param target: 目标数值
        :return:
        """
        try:
            with open(os.path.join(path), "w") as f:
                json.dump(self.__getattribute__(target), f, indent=2)
            return True
        except Exception as e:
            return {"error": f"错误：{e}"}