from Config import DEFAULT_PATH, PATH_DICT
from module import API_instance
import requests
import Logger
import openai
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
        self.AI_NAME: str = "小平同学"
        self.LOOP_INTERVAL = 0.7
        # 相关url
        self.SEND_MESSAGE_URL: str = f""  # 发送消息url
        self.TEST_RUL1: str = f""  # 链接测试url
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

        # 系统api设置
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
        # 联网ai：deepseek、chat-GPT
        self.openai_api = ""  # 用户使用的api
        self.basis_url = ""  # 目标网址
        self.TEST_RUL2 = ""  # 测试链接用的网址（一般使用余额查询）
        self.openai_module = ""  # 主选ai大模型
        self.openai_module_minor = ""  # 次选ai大模型
        self.openai_tools = []  # 工具
        self.openai_active = True  # ai状态 true表示使用状态
        self.HANDERS = {}  # 链接测试工具
        # 设置
        self.model_data = {}
        self.key_data = {}
        self.ai_list = []
        self.tag = "openai"  # 当前使用的ai模型
        self.key_active = True  # openai需要的API key
        self.ai_active = True  # 确认是否有可运行的ai

        self.test_connect_dict = {
            "openai": self.test_connect_openai,
            "ollama": self.test_connect_ollama
        }

    def init_config(self):
        """
        注：必须在外部调用此函数
        """
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

        # 加载ai_key
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["KEY"]), "r", encoding="utf-8") as f:
                self.key_data = json.load(f)
                f.close()
            logger.log("已成功加载key.json文件", self.ID, "INFO")
        except Exception as e:
            self.key_active = False
            logger.log(f"用户未配置key.json，{e}", self.ID, "ERROR")

        # 加载ai模型设置
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["AI_MODEL"]), "r", encoding="utf-8") as f:
                data = json.load(f)
                f.close()
            for aim in data:
                if aim.get("ai_type", "None") == "openai" and self.key_active:
                    name = aim.get("name", "None")
                    if name == "None":
                        aim["active"] = False
                        continue

                    aim["key"] = self.key_data["name"]  # 获取key
                    aim["client"] = openai.OpenAI(
                        api_key=aim["key"],
                        base_url=aim["base_url"]
                    )

                    aim["active"] = True
                elif aim["ai_type"] == "ollama":
                    aim["SEND_MESSAGE_URL"] = f"{aim['OLLAMA_HOST']}/api/generate"  # 发送消息的api
                    aim["TEST_RUL"] = f"{aim['OLLAMA_HOST']}/api/tags"  # 获取模型列表的api

                    aim["active"] = True
                else:
                    aim["active"] = False

                self.model_data[aim["name"]] = aim  #  保存数据
        except Exception as e:
            logger.log(f"用户未正确配置ai_model.json，{e}", self.ID, "ERROR")
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

    def RC_verify(self):
        """资源校验"""
        # 先测试Ollama连接
        for key, value in self.model_data:
            ai_type = value.get("ai_type", "None")
            if ai_type == "None" or not value.get("active", False):  # 无法使用或为配置ai_type
                continue
            self.test_connect_dict.get(ai_type)(key)


    def test_connect_ollama(self, model_name: str):
        """测试ai连接_ollama"""
        logger.log("测试Ollama连接...", self.ID, "WARNING")
        try:
            test_response = requests.get(self.TEST_RUL1, timeout=5)
            if test_response.status_code == 200:
                logger.log("✅ Ollama连接正常", self.ID, "INFO")

                models = test_response.json().get('models', [])
                model_names = [m['name'] for m in models]

                if model_name in model_names:
                    logger.log(f"✅ {model_name}模型已加载", self.ID, "INFO")
                else:
                    logger.log(f"❌ 未找到{model_name}模型", self.ID, "ERROR")
                    logger.log(f"请运行: ollama pull {model_name}", self.ID, "INFO")
            else:
                logger.log("❌ Ollama服务异常", self.ID, "ERROR")
        except:
            logger.log("❌ 无法连接到Ollama", self.ID, "ERROR")
            logger.log("请先启动Ollama服务: ollama serve", self.ID, "INFO")

    def test_connect_openai(self, model_name: str, AIType: str):
        """测试openai连接"""

    def charge_tag(self, tag: str=""):
        """切换tag"""
        if tag == "":  # 输入为空
            self.tag = ""
            for t in self.ai_list:
                a = getattr(self, t+"_active")
                if a:  # 是否能运行
                    self.tag = t
                else:  # 不能运行就pass
                    continue
            if self.tag == "":
                logger.log("当前无可用ai", self.ID, "ERROR")
        elif tag in self.ai_list:  # 调用跳转到当前tag
            self.tag = tag
        else:
            return

    def reply_test(self, ID):
        """
        响应自检
        :return:
        """
        logger.log(f"{self.ID}, 自检响应成功", ID, "INFO")
        return True

