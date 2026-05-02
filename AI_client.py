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
        self.RC = None
        self.WC = None

        self.conversation_history = []  # 会话历史
        self.now_history_name: str = ""  # 当前会话名称
        self.now_history: list = []  # 当前回话历史
        self.len_history: int = 0  # 当前回话的历史长度
        self.using_token: dict = {}  # 各类token用量
        self.doing_active = False

        self.output = ""
        self.get_module_tools = None

    def init(self):
        """
        初始化
        :return:
        """
        self.RC = self.master.RC
        self.WC = self.master.work_core
        self.using_token: dict = self.RC.using_token  # 各类token用量
        self.get_module_tools = self.RC.get_module_tools

    def run(self):
        """运行"""

    def update(self):
        """更新展示的内容"""
        print("-"*20)
        print(f"当前会话名称：{self.now_history_name}")
        print(f"当前使用模型：{self.RC.model_data[self.RC.scheme].name}")
        print(f"当前历史记录长度: {self.len_history}")
        if self.doing_active:
            print("AI正在工作...")
        print("聊天内容：" + self.output)

    def send(self, model_name: str, message: dict):
        """发送到openai的api上"""
        self.doing_active = True
        model = self.RC.model_data.get(model_name, None)
        if model is None:
            return {"error": "无目标模型"}
        data_msgs = self.package_openai(message)
        data_tools = self.get_module_tools(self.WC.tools_name)

        client: openai.Client = model.get("client")
        if client is None:
            return {"error": "当前model无发送客户端"}
        try:
            response = client.chat.completions.create(
                model=model.model,
                messages=data_msgs,
                max_tokens=512,
                temperature=self.RC.TEMPERATURE,
                top_p = self.RC.TOP_P,
                stream = False,
                tools=data_tools
            )
        except openai.BadRequestError as e:
            self.doing_active = False
            return {"ERROR": "{}".format(e.message)}
        # 计算token
        choices = response.choices
        token = response.usage
        for k in self.using_token.keys():
            if k not in token.__dict__:
                logger.warning(f"无目标值：{k}", self.ID)
                continue
            self.using_token[k] += token.__getattribute__(k)
        self.RC.save("config/using_token.json", "using_token")
        logger.info(f"{choices[0].message.content}", self.ID)

        # 构建 assistant 消息并添加到历史
        assistant_msg = {
            "role": "assistant",
            "content": choices[0].message.content,
        }
        if choices[0].message.tool_calls:
            # 将 tool_calls 转为字典列表（兼容 OpenAI 库的 Pydantic 模型）
            temp = []
            for tc in choices[0].message.tool_calls:
                temp.append(tc.model_dump())
            assistant_msg["tool_calls"] = temp

        # 添加 reasoning_content（如果存在，针对于deepseek！！！）
        if hasattr(choices[0].message, 'reasoning_content') and choices[0].message.reasoning_content:
            assistant_msg["reasoning_content"] = choices[0].message.reasoning_content
        # 加入历史
        self.now_history.append(assistant_msg)

        self.doing_active = False
        return choices

    def package_openai(self, messages: dict):
        """
        打包openai的消息键值
        :param messages:
        :return:
        """
        payload = [{"role": "system", "content": self.RC.prompts.get("system")}]
        logger.info(f"{messages['role']}-> {messages['content']}", self.ID)  # 保存日志
        self.now_history.append(messages) # 加入历史对话
        payload = payload + copy.copy(self.now_history)  # 复制一个历史对话
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
