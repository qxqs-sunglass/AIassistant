import requests
import Logger


logger = Logger.get_logger()


class OllamaClient:
    def __init__(self, master):
        """
        ollama 的链接客户端
        :param master:
        """
        self.ID = "OllamaClient"
        self.master = master
        self.RC = self.master.RC

        self.conversation_history = []
        self.doing_active = False

        self.output = ""

    def run(self):
        """运行"""
        # 先测试Ollama连接
        logger.log("测试Ollama连接...", self.ID, "WARNING")
        try:
            test_response = requests.get(self.RC.TEST_RUL, timeout=5)
            if test_response.status_code == 200:
                logger.log("✅ Ollama连接正常", self.ID, "INFO")

                models = test_response.json().get('models', [])
                model_names = [m['name'] for m in models]

                if 'gemma3:1b' in model_names:
                    logger.log("✅ Gemma3-1b模型已加载", self.ID, "INFO")
                else:
                    logger.log("❌ 未找到gemma3:1b模型", self.ID, "ERROR")
                    logger.log("请运行: ollama pull gemma3:1b", self.ID, "INFO")
            else:
                logger.log("❌ Ollama服务异常", self.ID, "ERROR")
        except:
            logger.log("❌ 无法连接到Ollama", self.ID, "ERROR")
            logger.log("请先启动Ollama服务: ollama serve", self.ID, "INFO")

    def update(self):
        """更新展示的内容"""
        print("-"*20)
        print(f"当前使用模型：{self.RC.DEFAULT_MODEL}")
        print(f"当前历史记录长度: {len(self.conversation_history)}")
        if self.doing_active:
            print("正在与Ollama聊天...")
        print("聊天内容：" + self.output)

    def send(self, message: str | list):
        """
        发送消息到ollama
        适用于指令模式
        """
        if type(message) is str:
            payload = {
                "model": self.RC.DEFAULT_MODEL,
                "prompt": message,
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
            return None

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
