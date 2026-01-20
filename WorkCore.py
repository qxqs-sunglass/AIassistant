from module import API_instance
from Config import PROMPT_E, PROMPT_F
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

        self.module_dict = {}  # 存放实例处
        self.module_intro = []  # api简介
        # 导入api
        for name, ins in API_instance.items():
            self.module_dict[name] = ins()  # 动态导入
            self.module_intro.append(self.module_dict[name].intro)

        temp = self.RC.FIRST_PROMPT_1
        for m in range(len(self.module_intro)):
            temp = f"{temp}\n{m}.{self.module_intro[m]}"  # 上一句\n下一句
        self.FIRST_PROMPT = temp + self.RC.FIRST_PROMPT_2

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
            # 一轮处理，得出是否继续执行，并索引对应module
            logger.log(f"发送AI(此处不包含提示词):\n{msg}", self.ID, "INFO")
            ans: str = self.OLLAMA.send(PROMPT_F + msg + self.FIRST_PROMPT)  # 发送消息到ollama客户端
            # logger.log(f"收到AI回复:{ans}", self.ID, "INFO")
            logger.log(f"收到确认指令:{msg}", self.ID, "INFO")
            if ans == 'None':
                continue
            if ans not in self.module_dict.keys():  # 是否存在相关实例
                logger.log(f"目标不存在：{ans}", self.ID, "INFO")
                continue

            # 三轮处理：索引相关api
            msg: str = self.OLLAMA.send("当前文本" + f"{msg}" + self.module_dict[ans].WorkWord + PROMPT_E)
            # 处理指令集
            # 清理回复，提取JSON
            res = self.analysis_json(msg)
            if not res["res"]:  # 目标不存在
                logger.log("目标不存在", self.ID, "INFO")
                continue
            if res["command"] not in self.module_dict[ans].Work_dict.keys():
                logger.log("指令集中无对应指令", self.ID, "INFO")
                continue

            self.module_dict[ans].temp = res["parameters"]
            logger.log("执行指令中", self.ID, "INFO")
            # self.module_dict[ans].Work_dict[res["command"]]()
            logger.log(f"命令执行完成", self.ID, "INFO")

        self.SPH.reply_send()  # 回复处理完成

    @staticmethod
    def analysis_json(msg) -> dict:
        try:
            result = json.loads(msg)
            result["res"] = True
            info = f"""
            输出结果：{result},
            对象类型{type(result)},
            访问字段command:{result['command']}
            """
            logger.log(info, "WorkCore", "INFO")
            return result
        except json.JSONDecodeError as e:
            logger.log(f"❌ JSON解析失败:{e}", "WorkCore", "ERROR")
            return {"res": False}
        except Exception as e:
            logger.log(f"❌ LLM解析失败:{e}", "WorkCore", "ERROR")
            return {"res": False}

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
