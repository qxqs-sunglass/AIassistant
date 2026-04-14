import openai


class AIModel:
    def __init__(self):
        """
        适用于存储openai的数据
        """
        self.ai_type = "openai"  # ai类型
        self.name = ""  # 该ai源使用的名称
        # 注：此项允许自定义
        self.key = ""  # 用户秘钥
        self.model = ""  # 默认使用的ai源
        self.model_minor = ""  # 次级ai，在默认ai无法使用的时候将调用这个
        self.basis_url = ""
        self.client: openai.Client = None
        self.active = False  # ai是否可用

        self.blacklist = [
            "ai_type"
        ]

    def init(self, setting: dict):
        """
        用于导入openai的设置
        :return:
        """
        for key, value in setting.items():
            self.__setattr__(key, value)

        if self.basis_url == "" or self.key == "":
            return {"error": "信息未配置完全"}
        self.client = openai.Client(
            base_url=self.basis_url,
            api_key = self.key
        )
        return {"info": "初始化完成"}

    def connect(self) -> list|dict:
        """
        所有模型源只有经过测试后才能使用
        :return:
        """
        try:
            temp = self.client.models.list()
            model_names = [m.id for m in temp]

            if self.model not in model_names:
                self.model = model_names[0]
            self.active = True
        except openai.APIConnectionError as e:
            self.active = False
            t = f"❌ 连接失败: {e}\n"
            return {"error": t}
        except openai.AuthenticationError as e:
            self.active = False
            t = f"❌ 认证失败: {e}\n"
            return {"error": t}
        except openai.NotFoundError as e:
            self.active = False
            t = f"❌ 资源未找到 (404): {e}\n"
            return {"error": t}
        except Exception as e:
            # 可能 base_url 路径不对（例如缺少 /v1），或者模型不存在
            self.active = False
            return {"error": e}
        return {"INFO": f"模型源：{self.name}校验完成"}

    def __setattr__(self, key, value):
        if key in self.blacklist:
            return
        self.__dict__[key] = value

    def get(self, key: str) -> object:
        """
        获取
        :param key:
        :return:
        """
        if key not in self.__dict__:
            return None
        attr = self.__getattribute__(key)
        return attr