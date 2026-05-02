import threading
import re
import Logger
import json
import time


logger = Logger.get_logger()


class WorkCore(threading.Thread):
    def __init__(self, master):
        """
        工作核心类，负责处理工作核心的逻辑
        :param master: 父类
        """
        super().__init__()
        self.ID = "WorkCore"
        self.master = master
        self.RC = None  # 资源控制器
        self.SPH = None  # 语音识别器
        self.TTS = None  # 语音合成器
        self.CL = None  # ai集成客户端

        self.module_dict = None  # 存放api实例处
        self.model_data = None  # ai模型数据

        self.msg_now = "" # 当前消息
        self.mode = "CMD_MODE"  # 模式
        self.tools_name = "system"  # 工具名称
        # 聊天模式：CHAT_MODE
        # 指令模式：CMD_MODE
        # 注：更换模式由AI助手控制
        self.active = True  # 工作核心是否激活
        self.active_msg = True  # 对话执行流程

        self.get_module_tools = None  # 获取工具包
        self.use_tool = None  # 调用工具包

    def init(self):
        """
        初始化
        :return:
        """
        self.RC = self.master.RC  # 资源控制器
        self.SPH = self.master.speech_recognizer  # 语音识别器
        self.TTS = self.master.tts_engine  # 语音合成器
        self.CL = self.master.ai_client  # ai集成客户端

        self.module_dict = self.RC.module_dict  # 存放api实例处
        self.model_data = self.RC.model_data  # ai模型数据

        self.get_module_tools = self.RC.get_module_tools  # 获取工具包
        self.use_tool = self.RC.use_tool  # 调用工具包

    def run(self):
        """
        主线程运行函数
        :return:
        """
        logger.log("工作核心线程启动", self.ID, "INFO")
        while self.active:
            data: list = self.SPH.get_msg()
            if len(data) > 0:  # 收到消息
                for i in range(len(data)):
                    msg = data[i]
                    self.active_msg = True
                    self.dispose(msg)
            self.SPH.reply_send()  # 回复处理完成
            time.sleep(self.RC.LOOP_INTERVAL)

    def update(self):
        """
        更新UI
        :return:
        """
        print("-"*20)
        print(f"当前模式{self.mode}")
        print(f"当前处理：{self.msg_now}")

    def dispose(self, msg):
        """
        命令模式处理消息单元
        函数即代表一次处理
        :param msg:  用户消息
        备注：所有的工具调用都只能在这里进行
        """
        self.active_msg = True
        scheme = self.RC.scheme
        ai_module = self.model_data.get(scheme)
        if not ai_module:  # 目标错误
            logger.error("无目标ai", self.ID)
            return
        if self.mode == "CMD_MODE":
            self._handle_cmd_mode(msg, scheme)
        elif self.mode == "CMD_CHAT_MODE":
            self._handle_chat_mode(msg, scheme)

    def _handle_cmd_mode(self, user_msg, scheme):
        """
        使用cmd方式发送
        :param user_msg: 用户消息
        :param scheme: 执行方案（ai名）
        :return:
        """
        role = "user"
        content = user_msg
        message = {"role": role, "content": content}
        while self.active_msg:
            choices: dict|list = self.CL.send(scheme, message)  # 这里只会获取ai调用工具的请求
            if type(choices) is dict:
                if "ERROR" in choices.keys():
                    logger.error(choices["ERROR"], self.ID)
                    self.exit_dispose()
                    break

            data = choices[0]  # 只获取最新的消息
            if not data.message.tool_calls:
                # 播报或输出 data.message.content
                self.TTS.speak(data.message.content)
                self.active_msg = False
                break
            for tool in data.message.tool_calls:
                # 获取所需参数
                raw_args = tool.function.arguments
                if isinstance(raw_args, str):
                    try:
                        arguments = json.loads(raw_args) if raw_args.strip() else {}
                    except json.JSONDecodeError as e:
                        logger.error(f"解析 JSON 参数失败: {raw_args}, 错误: {e}", self.ID)
                        arguments = {}
                else:
                    arguments = raw_args or {}
                arguments["m-self"] = self  # 把自己加进去
                tname = tool.function.name  # 获取工具名。
                tool_id = tool.id
                # 开始执行
                temp:dict = self.use_tool(self.tools_name, tname, arguments)  # 获取工具包
                # 记录日志
                if "logs" in temp.keys():
                    logs: dict|list = temp.get("logs")
                    if type(logs) is list:
                        for l in logs:
                            logger.log(
                                l.get("msg", "目标未记录日志"),
                                l.get("level", "INFO"),
                                self.ID
                            )
                    elif type(logs) is dict:
                        logger.log(
                            logs.get("msg", "目标未记录日志"),
                            logs.get("level", "INFO"),
                            self.ID
                        )
                # 建立新消息
                message = {
                    "role": temp.get("role", "tool"),
                    "tool_call_id": tool_id,
                    "content": temp.get("content", "工具无返回信息，可能已完成执行动作。")
                }  # 建立新信息
                logger.info(f"调用工具：{tname}", self.ID)
                logger.info(f"role=> {message['role']}; content=> {message['content']}", self.ID)

    def _handle_chat_mode(self, user_msg, scheme):
        """
        聊天模式
        :param user_msg:
        :param scheme:
        :return:
        """

    def exit_dispose(self, **kwargs) -> dict:
        """
        终止这一轮对话
        :return:
        """
        self.CL.empty_history()
        self.tools_name = "system"
        self.active_msg = False
        return {
                "role": "tool",
                "content": "已退出对话状态",
                "logs": {
                    "msg": "退出任务模式",
                    "level": "ERROR"
                },
            }
