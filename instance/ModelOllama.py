import requests


class ModelOllama:
    def __init__(self):
        """
        适用于存储ollama的数据
        """
        self.ai_type = "ollama"
        self.model = ""  # 模型名称，请务必填写完整
        self.name = ""# 该ai源使用的名称
        # 注：此项允许自定义
        self.host = ""
        self.send_message_url = ""
        self.test_url = ""
        self.active = False  # 模型是否可用

        self.blacklist = [
            "ai_type"
        ]

    def init(self, setting: dict) -> dict:
        """
        初始化模型类
        :return:
        """
        for k, v in setting.items():
            self.__setattr__(k, v)
        self.send_message_url = self.host + "/api/generate"  # 发送消息的api
        self.test_url = self.host + "/api/tags"  # 获取模型列表的api
        return {"INFO": setting}

    def connect(self) -> dict[str, str] | list[dict[str, str]]:
        """
        链接测试
        :return:
        """
        try:
            response = requests.get(self.send_message_url, timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]

                if self.model in model_names:
                    self.active = True
                    return {"INFO": f"成功校验：{self.name}"}
                else:
                    return [
                        {"error": f"❌ 未找到{self.model}模型"},
                        {"error": f"请运行: ollama pull {self.model}"}
                    ]
            else:
                return {"error": "❌ Ollama服务异常"}
        except Exception as e:
            self.active = False
            return {"ERROR": str(e)}

    def __setattr__(self, key, value):
        if key in self.blacklist:
            return
        self.__dict__[key] = value
