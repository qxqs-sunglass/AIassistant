from openai import OpenAI
import requests
import Logger


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

        self.conversation_history = []
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
        self.package_dict = {
            "ollama": self.package_ollama,
            "openai": self.package_openai
        }

    def run(self):
        """运行"""

    def update(self):
        """更新展示的内容"""
        print("-"*20)
        print(f"当前使用模型：{self.RC.DEFAULT_MODEL}")
        print(f"当前历史记录长度: {len(self.conversation_history)}")
        if self.doing_active:
            print("AI正在工作...")
        print("聊天内容：" + self.output)

    def send(self, message: str | list):
        """
        指令发送
        表注：
        这里发送的str可以直接发送
        list类型的格式为:[["msg", "role], ["msg", "role"], ...]
        """
        payload = self.package_dict[self.RC.tag](message)
        if "error" in payload:
            return payload
        res = self.send_dict[self.RC.tag](payload)
        logger.log(f"发送指令{message}", self.ID, "INFO")
        return res


    def send_ollama(self, payload: dict):
        """发送到ollama上
        标注：需要修改（2026.2.27）"""
        try:
            self.doing_active = True
            response = requests.post(self.RC.SEND_MESSAGE_URL, json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                msg: str = result.get("response", "")
                msg = msg.replace("\n", "")
                self.output = msg
                self.doing_active = False
                return self.output
            else:
                self.doing_active = False
                logger.log(f"错误: {response.status_code}", self.ID, "ERROR")
                return None
        except Exception as e:
            self.doing_active = False
            logger.log(f"请求失败: {e}", self.ID, "ERROR")
            return None

    def send_openai(self, payload: dict):
        """发送到openai的api上
        备注：需要完善（2026.2.27）"""

    def package_ollama(self, message: str | list):
        """打包ollama消息"""
        if type(message) is str:
            payload = {
                "model": self.RC.DEFAULT_MODEL,
                "prompt": message,  # 一条信息这里只需要str就行
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "num_predict": 512
                }
            }
        elif type(message) is list:
            data = []
            for msg in message:
                data.append(
                    {
                        "role": "user",
                        "content": msg
                    }
                )
            payload = {
                "model": self.RC.DEFAULT_MODEL,
                "messages": data,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 512  # Gemma3-1b建议值
                },
                "think": False
            }
        else:
            logger.log(f"格式错误：{message}", self.ID, "ERROR")
            return {"error": "ERROR"}
        return payload

    def package_openai(self, message: str | list):
        """用于打包openai的payload
        备注：需要完善（2026.2.27）"""
        payload = {}
        return payload

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
