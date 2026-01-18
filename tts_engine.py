import pyttsx3
import threading
import Logger
import queue
import time


logger = Logger.get_logger()


class TTSEngine:
    def __init__(self, master):
        """
        语音输出引擎初始化
        :param master:
        """
        self.master = master
        self.RC = self.master.RC
        self.ID = "TTSEngine"

        self.msgs_queue = queue.Queue()
        self.say_active = True  # 控制线程运行
        self.msg = ""
        self.is_speaking = False  # 当前是否正在说话

        self.say_thread = threading.Thread(target=self.say, name=self.ID)
        self.say_thread.daemon = True

    def run(self):
        """
        运行语音输出引擎
        :return:
        """
        self.say_active = True
        logger.log(f"[{self.ID}] 语音输出引擎已启动", self.ID, "INFO")

        self.say_thread.start()

    def say(self):
        # 启动循环
        while self.say_active:
            # 从队列中获取消息，设置超时时间以便检查是否要退出
            try:  # 尝试获取消息
                msg = self.msgs_queue.get_nowait()
                print(f"[{self.ID}] 从队列中获取消息: {msg[:50]}{'...' if len(msg) > 50 else ''}")

                self._speak(msg)
                logger.log(f"播报语音：{msg}", self.ID, "INFO")
            except queue.Empty:
                time.sleep(self.RC.LOOP_INTERVAL)
                continue

        logger.log(f"[{self.ID}] 说话线程结束", self.ID, "INFO")

    def stop(self):
        """
        停止语音输出引擎
        :return:
        """
        self.say_active = False
        if self.say_thread and self.say_thread.is_alive():
            self.say_thread.join(timeout=2.0)
            logger.log(f"[{self.ID}] 语音输出引擎已停止", self.ID, "INFO")

    def update(self):
        """
        更新对外显示的文本
        :return:
        """
        print("-" * 20)
        print(f"语音合成模块状态: {'运行中' if self.say_active else '已停止'}")
        print(f"队列中待播报消息数: {self.msgs_queue.qsize()}")
        print(f"当前是否正在说话: {self.is_speaking}")
        print(f"最后播报的消息: {self.msg[:50]}{'...' if len(self.msg) > 50 else ''}")
        print("-"*20)

    def say_text(self, text):
        """
        添加文本到播报队列
        :param text: 要播报的文本
        :return:
        """
        self.msgs_queue.put(text)
        print(f"[{self.ID}] 添加播报消息: {text[:50]}{'...' if len(text) > 50 else ''}")

    def _speak(self, text):
        """
        使用pyttsx3模块进行语音合成
        :param text:
        :return:
        """
        engine = pyttsx3.init()
        engine.setProperty('rate', self.RC.TTS_RATE)
        engine.setProperty('volume', self.RC.TTS_VOLUME)
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    def reply_test(self, ID):
        """
        响应自检
        :return:
        """
        logger.log(f"{self.ID}, 自检响应成功", ID, "INFO")
        return True


if __name__ == '__main__':
    m = TTSEngine(None)
    m.say_text("你好，欢迎使用语音助手")
    m.say_text("今天天气怎么样？")
    m.run()

