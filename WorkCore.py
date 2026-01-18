from module.media import media_controller
from Config import PROMPT_S, PROMPT_E
import threading
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
        self.media_controller = media_controller  # 媒体控制器

        self.msg = ""  # 消息
        self.mode = "CMD_MODE"  # 模式
        # 聊天模式：CHAT_MODE
        # 指令模式：CMD_MODE
        # 注：更换模式由AI助手控制
        self.active = True  # 工作核心是否激活
        self.dispose_dict = {
            "CMD_MODE": self.cmd_dispose,
            "CHAT_MODE": self.chat_dispose
        }  # 处理消息的字典
        self.control_commands = PROMPT_S + self.media_controller.WorkWord + PROMPT_E  # 控制指令集

    def run(self):
        """
        主线程运行函数
        :return:
        """
        logger.log("工作核心线程启动", self.ID, "INFO")
        while self.active:
            self.dispose_dict[self.mode]()  # 调用相应的处理函数
            time.sleep(self.RC.LOOP_INTERVAL)

    def update(self):
        """
        更新UI
        :return:
        """
        print("-"*20)
        print(f"当前模式{self.mode}")

    def cmd_dispose(self):
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
            logger.log(f"发送AI:\n{self.RC.FIRST_PROMPT_S + msg + self.RC.FIRST_PROMPT}", self.ID, "INFO")
            ans: str = self.OLLAMA.send(self.RC.FIRST_PROMPT_S + msg + self.RC.FIRST_PROMPT)  # 发送消息到ollama客户端
            ans = ans.replace("\n", "")
            logger.log(f"收到AI回复:{ans}", self.ID, "INFO")

            if ans == "Yes":
                logger.log(f"收到确认指令:{msg}", self.ID, "INFO")
                # 二轮处理
                ans: str = self.OLLAMA.send(["当前文本：" + msg, self.control_commands])  # 发送消息到ollama客户端
                # 处理指令集
                # 清理回复，提取JSON
                ans = self.analysis_json(ans)
                logger.log(f"收到AI回复:{ans}", self.ID, "INFO")
            elif ans == "No":
                logger.log(f"收到拒绝指令:{msg}", self.ID, "INFO")
            else:
                logger.log(f"输出出错：{ans}", self.ID, "ERROR")

        self.SPH.reply_send()  # 回复处理完成

    @staticmethod
    def analysis_json(msg):
        try:
            result = msg.json()
            response_text = result.get("response", "").strip()

            # 安全打印，避免格式化错误
            print("🤖 LLM回复:", response_text)

            # 清理回复，提取JSON
            response_text = response_text.replace('```json', '').replace('```', '').strip()

            # 提取JSON部分
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start != -1 and end != 0:
                json_str = response_text[start:end]
                command_info = json.loads(json_str)

                # 验证必要字段
                if "action" not in command_info or "command" not in command_info:
                    print("❌ LLM返回缺少必要字段")
                    return None

                # 确保confidence是浮点数
                if "confidence" in command_info:
                    try:
                        if isinstance(command_info["confidence"], str):
                            command_info["confidence"] = float(command_info["confidence"])
                        command_info["confidence"] = max(0.0, min(1.0, float(command_info["confidence"])))
                    except (ValueError, TypeError):
                        command_info["confidence"] = 0.7
                else:
                    command_info["confidence"] = 0.7

                # 安全打印
                print("✅ 解析成功:", command_info)
                return command_info

        except json.JSONDecodeError as e:
            print("❌ JSON解析失败:", e)
            return None
        except Exception as e:
            print("❌ LLM解析失败:", e)
            return None

        return None

    def chat_dispose(self):
        """
        聊天模式处理消息单元
        函数即代表一次处理
        :return:
        """

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

    @staticmethod
    def occupation():
        """占位使用，无实际用途"""
