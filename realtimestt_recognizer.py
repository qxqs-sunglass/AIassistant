from RealtimeSTT import AudioToTextRecorder
import threading
import Logger

logger = Logger.get_logger()


class RTSTTRecognizer(threading.Thread):
    def __init__(self, master):
        super().__init__(daemon=True)  # 设为守护线程，便于退出
        self.master = master
        self.ID = "RTSTTRecognizer"
        self.RC = None
        self.recorder = None
        self.active = False
        self._lock = threading.Lock()

        # 消息队列（线程安全）
        self.msg = ""
        self.msg_list = []
        self.undisposed_num = 0

        # 控制是否暂停识别（例如回复期间）
        self._paused = False

    def init(self):
        self.RC = self.master.RC
        self.recorder = AudioToTextRecorder(
            model="base",  # 按需调整
            language="zh",
            wake_words=self.RC.AI_NAME,  # 唤醒词，如“你好小助手”
            on_wakeword_detected=self._on_wakeword,  # 可选唤醒回调
            on_recording_start=lambda: print("录音开始"),
            on_recording_stop=lambda: print("录音结束")
        )
        self.active = True

    def update(self):
        """
        展示消息
        :return:
        """
        print("-"*25)
        print("当前消息", self.msg)
        print("当前状态", self._paused)

    def _on_wakeword(self):
        """检测到唤醒词后的动作，例如清除静音状态"""
        logger.info("唤醒词已检测", self.ID)
        # 如果你希望唤醒词后立刻开始录音，RealtimeSTT 会自动处理
        # 也可以在这里解除暂停状态
        with self._lock:
            self._paused = False

    def run(self):
        """只调用一次 text()，让其持续运行"""
        if self.recorder and self.active:
            # 阻塞调用，内部会持续监听并回调
            self.recorder.text(self.join_msg)

    def join_msg(self, txt):
        """录音回调 - 线程安全地添加消息"""
        with self._lock:
            if self._paused:
                # 如果处于暂停状态，可以选择丢弃或暂存，这里选择丢弃
                return
            self.msg = txt
            self.msg_list.append(txt)
            self.undisposed_num += 1
            if len(self.msg_list) > 100:
                self.msg_list.pop(0)
            logger.info(f"加入队列消息：{txt}", self.ID)

    def get_msg(self) -> list[str]:
        """外部调用：获取所有未处理的消息，并自动进入“处理中”状态"""
        with self._lock:
            if self.undisposed_num <= 0:
                return []
            data = self.msg_list[-self.undisposed_num:]
            self.undisposed_num = 0
            # 当获取消息后，自动暂停识别（相当于等待助手回复期间不接收新语音）
            self._paused = True
        logger.info(f"消息已获取：{data}", self.ID)
        return data

    def enter_msg(self, msg: list | str):
        """
        外部API：输入消息
        :param msg: 支持列表或字符串
        :return:
        """
        if isinstance(msg, list):
            for m in msg:
                if self.RC.AI_NAME not in m:
                    continue
                self.msg_list.append(m)
            self.msg = self.msg_list[-1]
            self.undisposed_num += len(msg)  # 添加未处理消息数
            # logger.log(f"当前消息数：{self.undisposed_num}", self.ID, "INFO")
        else:
            if self.RC.AI_NAME not in msg:
                return
            self.msg = msg
            self.msg_list.append(msg)
            self.undisposed_num += 1

    def reply_send(self):
        """识别恢复：应该在外界完成回复后调用"""
        with self._lock:
            self._paused = False

    def stop(self):
        """安全退出"""
        self.active = False
        if self.recorder:
            self.recorder.stop()  # 优雅停止录音
            self.recorder.shutdown()  # 释放资源
        logger.info(f"{self.ID} 已退出", self.ID)