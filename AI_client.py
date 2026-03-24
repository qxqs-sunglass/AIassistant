from openai import OpenAI
import requests
import Logger
import openai


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

    def send_ollama(self, messages: list):
        """
        发送到ollama上
        功能：解码，提取需要的信息
        """
        payload = self.package_ollama(messages)
        try:
            self.doing_active = True
            response = requests.post(self.RC.SEND_MESSAGE_URL, json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                msg: str = result.get("response", "")
                msg = msg.replace("\n", "")
                self.output = msg
                self.doing_active = False
                return
            else:
                self.doing_active = False
                logger.log(f"错误: {response.status_code}", self.ID, "ERROR")
                return
        except Exception as e:
            self.doing_active = False
            logger.log(f"请求失败: {e}", self.ID, "ERROR")
            return

    def send_openai(self, model_name: str, messages: list):
        """发送到openai的api上
        备注：需要完善（2026.3.17）"""
        model = self.RC.model.get(model_name, None)
        if model is None:
            return {"error": "无目标模型"}

        client: openai.Client = model.get("client", None)
        if client is None:
            return {"error": "当前model无发送客户端"}
        response = client.chat.completions.create(
            model=model["model"],
            messages=messages,

            max_tokens=512,
            temperature=self.RC.TEMPERATURE,
            top_p = self.RC.TOP_P,
            stream = False,
        )

        data = response.choices
        self.now_history.append(data[-1])

        return data

    def package_ollama(self, messages: list):
        """
        打包ollama消息
        :param messages: 标准格式：[{}, {}, ···]
        :return:
        """
        payload = {
            "model": self.RC.DEFAULT_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.RC.TEMPERATURE,
                "top_p": self.RC.TOP_P,
                "num_predict": 512
            },
            "think": False
        }
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

    def stop(self):
        """停止"""
        self.doing_active = False
        print("已停止与Ollama的对话...")

    def reply_test(self, ID):
        """
        响应自检
        :return:
        """
        logger.log(f"{self.ID}, 自检响应成功", ID, "INFO")
        return True
