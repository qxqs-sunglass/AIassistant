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
        self.RC = self.master.RC  # 资源控制器
        self.SPH = self.master.speech_recognizer  # 语音识别器
        self.TTS = self.master.tts_engine  # 语音合成器
        self.CL = self.master.ai_client  # ai集成客户端

        self.module_dict = self.RC.module_dict  # 存放实例处
        self.module_intro = self.RC.module_intro  # api简介
        #
        self.dispose_dict = {
            "call": self.call_ai,
            "get_model_tools": self.get_module_tools,
        }  # 函数

        self.msg_now = "" # 当前消息
        self.mode = "CMD_MODE"  # 模式
        # 聊天模式：CHAT_MODE
        # 指令模式：CMD_MODE
        # 注：更换模式由AI助手控制
        self.active = True  # 工作核心是否激活

    def init(self):
        """
        初始化
        :return:
        """

    def run(self):
        """
        主线程运行函数
        :return:
        """
        logger.log("工作核心线程启动", self.ID, "INFO")
        while self.active:
            data: list = self.SPH.get_msg()
            if len(data) > 0:  # 收到消息
                msg = data[0]
                self.dispose(msg)
                data.pop(0)  # 抛出第一项
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
        """
        scheme = self.RC.scheme
        ai_module = self.module_dict.get(scheme)
        if not ai_module:  # 目标错误
            logger.error("无目标ai", self.ID)
            return

        if self.mode == "CMD_MODE":
            self._handle_cmd_mode(msg, scheme)
        elif self.mode == "CMD_CHAT_MODE":
            self._handle_chat_mode(msg, scheme)

    def analysis_json(self, msg: str) -> dict:
        """
        增强的JSON解析方法，处理多种格式
        """
        if not msg:
            return {"res": False}

        # 清理消息
        msg = msg.strip()

        # 移除代码块标记
        if msg.startswith("```json"):
            msg = msg[7:]
        if msg.endswith("```"):
            msg = msg[:-3]
        msg = msg.strip()

        # 尝试直接解析
        try:
            result = json.loads(msg)
            result["res"] = True
            logger.log(f"✅ JSON解析成功: {result}", "WorkCore", "DEBUG")
            return result
        except json.JSONDecodeError:
            pass

        # 尝试修复常见的JSON格式问题
        try:
            # 修复属性名缺少双引号的问题
            fixed_msg = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', msg)
            # 修复字符串值中的单引号
            fixed_msg = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_msg)

            result = json.loads(fixed_msg)
            result["res"] = True
            logger.log(f"✅ JSON修复后解析成功: {result}", "WorkCore", "DEBUG")
            return result
        except (json.JSONDecodeError, Exception):
            pass

        # 最后尝试提取大括号内的内容
        try:
            start = msg.find("{")
            end = msg.rfind("}")

            if start != -1 and end != -1 and start < end:
                json_str = msg[start:end + 1]
                # 再次尝试修复和解析
                fixed_json = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
                fixed_json = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_json)

                result = json.loads(fixed_json)
                result["res"] = True
                logger.log(f"✅ 提取并修复JSON成功: {result}", "WorkCore", "DEBUG")
                return result
        except Exception:
            pass

        logger.log(f"❌ JSON解析失败: {msg}", "WorkCore", "WARNING")
        return {"res": False}

    def call_ai(self, name):
        """
        调用ai_client的send
        :param name: 目标模型名称
        :return:
        """
        res = self.CL.send(name)
        if "error" in res:
            logger.error(res["error"], self.ID)
        return

    def get_module_tools(self, name):
        """
        获取目标mod的tools
        :param name:目标mod名字
        :return:
        """
        if name not in self.RC.module_dict.keys():
            return {"error": f"不存在的目标{name}"}
        return self.RC.module_dict[name]

    def _handle_cmd_mode(self, user_msg, scheme, tools_name):
        """
        使用cmd方式发送
        :param user_msg: 用户消息
        :param scheme: 执行方案（ai名）
        :param tools_name: 目标工具包名
        :return:
        """

    def _handle_chat_mode(self, user_msg, scheme, tools_name):
        """
        聊天模式
        :param user_msg:
        :return:
        """

