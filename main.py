from RControl import RControl
from AI_client import AIClient
from speech_recognizer import SpeechRecognizer
from tts_engine import TTSEngine
from WorkCore import WorkCore
import Logger
import rich.console
import threading
import socket
import queue
import json
import time
import os

logger = Logger.get_logger()  # 获取日志对象

console = rich.console.Console()  # 创建控制台对象
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 创建UDP套接字
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 设置套接字属性
sock.bind(('127.0.0.1', 8001))  # 绑定本地地址和端口


class Main:
    def __init__(self):
        """主程序"""
        self.ID = "Main"
        self.RC = RControl(self)  # 创建资源管理器对象
        self.RC.init_config()  # 初始化配置
        self.receive = Receive(self)  # 创建接收线程对象

        # 创建各个模块对象
        self.ollama_client = AIClient(self)  # Ollama客户端
        self.speech_recognizer = SpeechRecognizer(self)  # 语音识别器
        self.tts_engine = TTSEngine(self)  # 语音合成器
        self.work_core = WorkCore(self)  # 工作核心

        # 基础数据 回调函数
        self.send_message = self.speech_recognizer.enter_msg
        self.chat_message = self.speech_recognizer.enter_msg
        self.reply_send = self.speech_recognizer.reply_send
        self.say_text = self.tts_engine.say_text  # 说话
        self.obtain_msg = self.work_core.obtain_msg  # 获取消息回调函数
        self.enter_msg = self.speech_recognizer.enter_msg  # 输入消息回调函数

        self.cmd_queue = queue.Queue()  # 指令队列
        self.cmd_dict = {
            "er": self.er,  # 输出错误
            "text": self.test,  # 测试指令
            "exit": self.exit_th,  # 退出指令
            "send_message": self.send,  # 发送消息指令
            "send": self.send,  # 发送消息指令
            "chat": self.chat,  # 聊天指令
        }
        self.default_cmd = ["er", "无效指令:"]
        self.msg_temp_cmd = []  # 指令缓存
        # 注：一定一定！！！用于cmd控制的函数不要使用参数，不然会造成程序崩溃！！！
        self.exit_active = True

    def run(self):
        self.receive.start()  # 启动接收线程
        self.work_core.start()
        logger.log("启动程序", self.ID, "INFO")
        logger.log("--核心启动--", self.ID, "INFO")
        self.self_inspection()  # 自检指令
        self.ollama_client.run()
        self.speech_recognizer.run()
        self.tts_engine.run()
        logger.log("--核心启动完成--", self.ID, "INFO")

        while self.exit_active:
            try:
                data = self.cmd_queue.get_nowait()
                logger.log(f"接收到指令：{data}", self.ID, "INFO")
                if data["cmd"] in self.cmd_dict:
                    self.msg_temp_cmd = data["msg"]
                    self.cmd_dict[data["cmd"]]()
                else:
                    self.cmd_dict[self.default_cmd[0]]()
            except queue.Empty:
                pass
            finally:
                os.system("cls")
                self.update()
                time.sleep(self.RC.LOOP_INTERVAL)

    def update(self):
        """"""
        print("程序数据：")
        self.ollama_client.update()
        self.speech_recognizer.update()
        self.tts_engine.update()
        self.work_core.update()

    def exit_th(self):
        """
        退出程序
        :return:
        """
        os.system("cls")
        print("退出程序...")
        self.exit_active = False
        self.receive.stop()
        self.ollama_client.stop()
        self.speech_recognizer.stop()
        self.tts_engine.stop()

    def self_inspection(self):
        """
        自检指令
        :return:
        """
        logger.log("启动自检", self.ID, "INFO")
        self.ollama_client.reply_test(self.ID)

    def er(self):
        """cmd指令：输出"""
        logger.log("执行指令：输出错误", self.ID, "INFO")
        print(self.msg_temp_cmd)

    def test(self):
        logger.log("执行指令：测试指令", self.ID, "INFO")
        print("输出测试指令")

    def send(self):
        logger.log("执行指令：发送消息", self.ID, "INFO")
        self.enter_msg(self.msg_temp_cmd)

    def chat(self):
        logger.log("执行指令：发送消息", self.ID, "INFO")
        self.enter_msg(self.msg_temp_cmd)


class Receive(threading.Thread):
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.RC = self.master.RC
        self.exit_active = True

        # 设置socket超时
        sock.settimeout(0.1)  # 100毫秒超时

    def run(self):
        while self.exit_active:
            try:
                data, addr = sock.recvfrom(1024)
                data = json.loads(data.decode())
                logger.log(f"接收到来自{addr}的指令：{data}", self.master.ID, "INFO")
                self.master.cmd_queue.put(data)  # 放入指令队列
                # 这里这么做是为了防止指令丢失，把AssCmd传来的指令放到队列然后异步处理
            except socket.timeout:
                # 超时正常，继续循环
                continue
            except json.JSONDecodeError or UnicodeDecodeError:
                print("接收到非json格式数据")
                continue

    def stop(self):
        self.exit_active = False


if __name__ == '__main__':
    assistant = Main()
    assistant.run()
