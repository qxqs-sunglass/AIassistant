from module import API_instance
from Config import PROMPT_E
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
        self.OLLAMA = self.master.ollama_client  # ollama客户端

        self.module_dict = self.RC.module_dict  # 存放实例处
        self.module_intro = self.RC.module_intro  # api简介

        temp = self.RC.FIRST_PROMPT_1
        for m in range(len(self.module_intro)):
            temp = f"{temp}\n{m+1}.{self.module_intro[m]}"  # 上一句\n下一句
        self.FIRST_PROMPT = temp + self.RC.FIRST_PROMPT_2
        logger.log(self.FIRST_PROMPT, self.ID, "INFO")

        self.msg_now = "" # 当前消息
        self.mode = "CMD_MODE"  # 模式
        # 聊天模式：CHAT_MODE
        # 指令模式：CMD_MODE
        # 注：更换模式由AI助手控制
        self.active = True  # 工作核心是否激活

    def run(self):
        """
        主线程运行函数
        :return:
        """
        logger.log("工作核心线程启动", self.ID, "INFO")
        while self.active:
            self.dispose()
            time.sleep(self.RC.LOOP_INTERVAL)

    def update(self):
        """
        更新UI
        :return:
        """
        print("-"*20)
        print(f"当前模式{self.mode}")
        print(f"当前处理：{self.msg_now}")

    def dispose(self):
        """
        命令模式处理消息单元
        函数即代表一次处理
        :return:
        """
        data: list = self.SPH.get_msg()
        if len(data) == 0:  # 没有收到消息
            return

        # 处理指令
        for msg in data:  # 处理每条消息
            # 一轮处理，得出是否继续执行，并索引对应module
            logger.log("-"*20, self.ID, "INFO")
            t1 = time.time()  # 记录时间
            self.msg_now = msg

            # 跳过空消息
            if not msg or msg.strip() == "":
                continue

            try:
                # 第一次提炼 - 确定使用哪个模块
                prompt = self.FIRST_PROMPT + msg  # 指令
                logger.log(f"发送到AI: {msg}", self.ID, "INFO")

                temp_response = self.OLLAMA.send(prompt)
                logger.log(f"AI首次回复: {temp_response}", self.ID, "INFO")

                temp_result = self.analysis_json(temp_response)

                if not temp_result.get("res", False):
                    logger.log("❌ AI首次回复无法解析为有效JSON", self.ID, "WARNING")
                    self.msg_now = ""
                    continue

                ans = temp_result.get("ans", "None")  # 目标
                active = temp_result.get("active", False)  # 状态

                if not active:
                    logger.log(f"⚠️ 拒绝执行: {msg}", self.ID, "INFO")
                    t2 = time.time()
                    logger.log(f"用时: {t2 - t1:.2f}秒", self.ID, "INFO")
                    self.msg_now = ""
                    continue

                if ans not in self.module_dict.keys():
                    logger.log(f"❌ 模块不存在: {ans}", self.ID, "ERROR")
                    t2 = time.time()
                    logger.log(f"用时: {t2 - t1:.2f}秒", self.ID, "INFO")
                    self.msg_now = ""
                    continue

                # 第二轮处理 - 执行具体指令
                module = self.module_dict[ans]
                second_prompt = f"{PROMPT_E}{msg}\n{module.WorkWord}"
                logger.log(f"发送到模块 {ans}: {second_prompt[:100]}...", self.ID, "DEBUG")

                second_response = self.OLLAMA.send(second_prompt)
                logger.log(f"模块 {ans} 回复: {second_response}", self.ID, "INFO")

                res = self.analysis_json(second_response)  # 指令解析

                if not res.get("res", False):
                    logger.log(f"❌ 模块 {ans} 回复无法解析为有效JSON", self.ID, "ERROR")
                    t2 = time.time()
                    logger.log(f"用时: {t2 - t1:.2f}秒", self.ID, "INFO")
                    self.msg_now = ""
                    continue
                # 指令
                command = res.get("command", "")  # 目标指令
                # 执行指令
                logger.log(f"执行指令: {command}，参数: {res.get('parameters', [])}", self.ID, "INFO")
                # 设置参数
                module.temp = res.get("parameters", [])
                # 执行指令
                if command in module.Work_dict:
                    try:
                        module.Work_dict[command]()
                        logger.log(f"✅ 指令 {command} 执行完成", self.ID, "INFO")

                        # 如果有回复，可以语音输出
                        reply_say = res.get("reply_say", "")
                        if reply_say and self.TTS:
                            self.TTS.say_text(reply_say)
                    except Exception as e:
                        logger.log(f"❌ 执行指令 {command} 失败: {e}", self.ID, "ERROR")
                else:
                    logger.log(f"❌ 指令 {command} 未在模块中定义", self.ID, "ERROR")

                t2 = time.time()
                logger.log(f"总用时: {t2 - t1:.2f}秒", self.ID, "INFO")

            except Exception as e:
                logger.log(f"❌ 处理消息异常: {e}", self.ID, "ERROR")
                t2 = time.time()
                logger.log(f"用时: {t2 - t1:.2f}秒", self.ID, "INFO")

            self.msg_now = ""

        self.SPH.reply_send()  # 回复处理完成

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

    def obtain_msg(self, msg):
        """
        用于系统内部的API：获取消息
        :param msg:消息
        :return:
        """

    def reply_test(self, ID):
        """
        响应自检
        :return:
        """
        logger.log(f"{self.ID}, 自检响应成功", ID, "INFO")
        return True
