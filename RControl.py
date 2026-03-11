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

        # ai第一轮提炼提示 注：相关操作类型必须在mod中标出，指定的位置为:self.intro
        # 注：第三轮为函数操作，为了方便，所以会在指定的module中制定提示词 名称为：WorkWord
        # 联网ai：deepseek、chat-GPT
        self.tools = []  # 工具，给ai使用
        # 注：这里是负责控制ai_client.py中对ai发送消息的状态变量，是否启用该项发送消息
        self.openai_active = True  # openai接口的链接状态 true表示使用状态
        self.ollama_active = True   # 工具ollama链接状态
        # 设置
        self.model_data = {}
        # 特别标注：openai的实例被放在的目标模型下的client标签中
        self.key_data = {}
        self.ai_list = []  # 记录可用ai的tag
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
            for key, value in basis_dict.items():
                setattr(self, key, value)
        except Exception as e:
            logger.log(f"加载基础配置失败，原因：{e}", self.ID, "ERROR")

        # 加载ai_key
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["KEY"]), "r", encoding="utf-8") as f:
                self.key_data = json.load(f)
            logger.log("已成功加载key.json文件", self.ID, "INFO")
        except Exception as e:
            self.key_active = False
            logger.log(f"用户未配置key.json，{e}", self.ID, "ERROR")

        # 加载ai模型设置
        try:
            with open(os.path.join(self.DEFAULT_PATH, self.PATH_DICT["AI_MODEL"]), "r", encoding="utf-8") as f:
                data = json.load(f)
            for aim in data:
                if aim.get("ai_type", "None") == "openai" and self.key_active:
                    name = aim.get("name", "None")
                    key = self.key_data.get(name, None)

                    # 初步校验
                    if name == "None":
                        aim["active"] = False
                        continue
                    if key is None:  # 无效的key
                        logger.log(f"ai模型：{name}，无效的key", self.ID, "WARNING")
                        continue

                    aim["client"] = openai.OpenAI(
                        api_key=aim["key"],
                        base_url=aim["base_url"]
                    )

                    aim["active"] = True
                    self.ai_list.append([aim["name"], "openai"])
                elif aim["ai_type"] == "ollama":
                    aim["SEND_MESSAGE_URL"] = f"{aim['OLLAMA_HOST']}/api/generate"  # 发送消息的api
                    aim["TEST_URL"] = f"{aim['OLLAMA_HOST']}/api/tags"  # 获取模型列表的api

                    aim["active"] = True
                    self.ai_list.append([aim["name"], "ollama"])
                else:
                    aim["active"] = False

                self.model_data[aim["name"]] = aim  #  保存数据
        except Exception as e:
            logger.log(f"用户未正确配置ai_model.json，{e}", self.ID, "ERROR")
        logger.log("加载基础配置完成", self.ID, "INFO")
        # 导入api
        for name, ins in API_instance.items():
            n = ins()
            n.init()
            self.module_dict[name] = n  # 动态导入
            self.module_intro.append(self.module_dict[name].intro)

    def RC_verify(self):
        """资源校验"""
        self.openai_active = False
        self.ollama_active = False
        for item in self.ai_list:
            name = item[0]
            ai_type = item[1]
            self.test_connect_dict.get(ai_type)(self.model_data[name])


    def test_connect_ollama(self, model_name: str):
        """测试ai连接_ollama"""
        logger.log("测试Ollama连接...", self.ID, "WARNING")
        try:
            test_response = requests.get(self.model_data[model_name]["TEST_URL"], timeout=5)
            if test_response.status_code == 200:
                logger.log("✅ Ollama连接正常", self.ID, "INFO")

                models = test_response.json().get('models', [])
                model_names = [m['name'] for m in models]

                if model_name in model_names:
                    logger.log(f"✅ {model_name}模型已加载", self.ID, "INFO")
                else:
                    logger.log(f"❌ 未找到{model_name}模型", self.ID, "ERROR")
                    logger.log(f"请运行: ollama pull {model_name}", self.ID, "INFO")

                self.ollama_active = True
            else:
                logger.log("❌ Ollama服务异常", self.ID, "ERROR")
        except:
            logger.log("❌ 无法连接到Ollama", self.ID, "ERROR")
            logger.log("请先启动Ollama服务: ollama serve", self.ID, "INFO")

    def test_connect_openai(self, model_name: str):
        """测试openai连接"""
        logger.log("正在进行openai的测试链接", self.ID, "INFO")
        try:
            client = self.model_data[model_name]["client"]
            temp = client.models.list()
            for m in temp:
                if self.model_data[model_name]["model"] == m.id:
                    logger.log(f"✅ {model_name}模型已加载", self.ID, "INFO")

            self.openai_active = True  # 只要有模型能通过测试就算能用

        except openai.APIConnectionError as e:
            logger.log(f"❌ 连接失败: {e}", self.ID, "ERROR")
            logger.log("请检查 base_url 是否正确，以及网络是否连通。", self.ID, "ERROR")
        except openai.AuthenticationError as e:
            logger.log(f"❌ 认证失败: {e}", self.ID, "ERROR")
            logger.log("请检查 API Key 是否正确，并且与该 base_url 匹配。", self.ID, "ERROR")
        except openai.NotFoundError as e:
            # 可能 base_url 路径不对（例如缺少 /v1），或者模型不存在
            logger.log(f"❌ 资源未找到 (404): {e}", self.ID, "ERROR")
            logger.log("请检查 base_url 的格式是否正确（例如是否以 /v1 结尾）。", self.ID, "ERROR")
        except Exception as e:
            logger.log(f"❌ 发生了其他错误: {e}", self.ID, "ERROR")

    def charge_tag(self, tag: str=""):
        """切换tag"""
        if tag == "":  # 输入为空
            if len(self.ai_list) <= 0:
                logger.log("当前无可用ai", self.ID, "WARNING")
            self.tag = self.ai_list[0][0]  # 索引到目标tag
        elif tag in self.ai_list:  # 调用跳转到当前tag
            self.tag = tag
        else:
            logger.log(f"无效更改{tag}", self.ID, "WARNING")
            return

    def load(self, path: str, target: str) -> bool | dict:
        """
        热加载单元
        :param path: 文件路径（绝对或相对路径）
        :param target: 保存数据的地址（变量名）
        :return:
        """
        if not os.path.exists(os.path.join(path)):
            return {"error": f"不存在的路径：{path}"}
        p = path.split(".")
        p = p[-1]
        if p == "json":
            with open(os.path.join(path), "r") as f:
                data = json.load(f)
            temp = self.__getattribute__(target)  # 为了防止数据丢失，故，先定向后更新
            temp.update(data)
            return True
        elif p == "txt":
            with open(os.path.join(path), "r") as f:
                data = f.readlines(8192)  # 只读8mb的内容
            self.__setattr__(target, data)
            return True
        return True

    def save(self, path: str, s_type: str, target: str):
        """
        保存文件
        :param path: 文件路径
        :param s_type: 保存类型
        :param target: 目标数值
        :return:
        """
        try:
            if s_type == "json":
                with open(os.path.join(path), "w") as f:
                    json.dump(self.__getattribute__(target), f, indent=2)
                return True
            if s_type == "txt":
                with open(os.path.join(path), "w") as f:
                    f.write(self.__getattribute__(target))
                return True
        except Exception as e:
            return {"error": f"错误：{e}"}
        return {"error": f"类型错误{path}"}

    def reply_test(self, ID):
        """
        响应自检
        :return:
        """
        logger.log(f"{self.ID}, 自检响应成功", ID, "INFO")
        return True

