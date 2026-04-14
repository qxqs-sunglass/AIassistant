from openai import OpenAI
import requests
import Logger
import openai
import copy


logger = Logger.get_logger()


class AIClient:
    def __init__(self, master):
        """
        ollama 的链接客户端
        :param master:
        """
        self.ID = "AIClient"
        self.master = master
        self.RC = self.master.RC

        self.conversation_history = []  # 会话历史
        self.now_history_name: str = ""  # 当前会话名称
        self.now_history: list = []  # 当前回话历史
        self.len_history: int = 0  # 当前回话的历史长度
        self.using_token: dict = self.RC.using_token  # 各类token用量
        self.doing_active = False

        self.output = ""
        self.openai = None
        if self.RC.openai_active:
            self.openai = OpenAI(
                api_key=self.RC.openai_api,
                base_url=self.RC.basis_url
            )
        self.send_dict = {
            "ollama": self.send_ollama,
            "openai": self.send_openai
        }

    def run(self):
        """运行"""

    def update(self):
        """更新展示的内容"""
        print("-"*20)
        print(f"当前会话名称：{self.now_history_name}")
        print(f"当前使用模型：{self.RC.DEFAULT_MODEL}")
        print(f"当前历史记录长度: {self.len_history}")
        if self.doing_active:
            print("AI正在工作...")
        print("聊天内容：" + self.output)

    def send(self, msg):
        """
        发送到目标ai端
        :param msg:
        :return:
        """
        inst = self.send_dict.get(self.RC.scheme)
        if inst is None:
            return {"ERROR": "名称错误"}
        return inst(msg)

    def send_openai(self, model_name: str, message: str, tools_name: str):
        """发送到openai的api上
        备注：需要完善（2026.3.17）"""
        model = self.RC.model_data.get(model_name, None)
        if model is None:
            return {"error": "无目标模型"}
        data_msgs = self.package_openai(message)
        data_tools = self.get_module_tool(tools_name)

        client: openai.Client = model.get("client")
        if client is None:
            return {"error": "当前model无发送客户端"}
        response = client.chat.completions.create(
            model=model["model"],
            messages=data_msgs,
            max_tokens=512,
            temperature=self.RC.TEMPERATURE,
            top_p = self.RC.TOP_P,
            stream = False,
        )

        data = response.choices
        token = response.usage
        for k, v in token.items():  # 计算token
            if k not in self.using_token:
                logger.warning(f"无法保存的键值：{k}：{v}", self.ID)
                continue
            self.using_token[k] += v
        self.RC.save("config/using_token.json", "using_token")
        self.now_history.append(data[-1])

        return data

    def package_openai(self, messages: str):
        """
        打包openai的消息键值
        :param messages:
        :return:
        """
        self.now_history.append(
            {
                "content": messages,
                "role": "user"
            }
        )
        payload = copy.copy(self.now_history)
        return payload

    def empty_history(self):
        """
        清理这一轮的回话历史
        :return:
        注：这里需要修改（3.23）
        """
        self.now_history = []
        self.len_history = 0
        self.doing_active = False

    def get_module(self, name):
        """获取指定module的"""
        if name not in self.RC.module_dict.keys():
            return {"res": "ERROR"}
        return self.RC.module_dict[name]

    def get_module_tool(self, name):
        if name not in self.RC.module_dict:
            return {"res": "ERROR"}
        return self.RC.module_dict[name].tools

    def stop(self):
        """停止"""
        self.doing_active = False
        print("已停止与Ollama的对话...")
