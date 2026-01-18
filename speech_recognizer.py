import speech_recognition as sr
import queue
import time
import threading
import Logger


logger = Logger.get_logger()


class SpeechRecognizer:
    def __init__(self, master):
        """
        语音输入模块
        :param master:
        """
        self.ID = "SpeechRecognizer"
        self.master = master
        self.RC = self.master.RC  # 资源管理器

        self.recognizer = sr.Recognizer()  # 语音识别器
        self.microphone = sr.Microphone()  # 麦克风

        self.msg_list = []  # 语音输入的历史消息
        self.msg = ""  # 当前消息
        self.audio_data = queue.Queue()  # 语音输入的音频数据
        self.exit_active = True  # 退出
        self.lis_active = True  # 录音线程激活
        self.dis_active = True  # 识别线程激活（初始化为True）
        self.doing_active = False  # 正在处理（初始化为False）
        self.lis_show_active = False  # 录音线程展示激活（初始化为False）
        self.last_send_time = 0  # 上次发送消息的时间
        self.undisposed_num = 0  # 未处理的消息数

        # 添加子线程列表
        self.sub_threads = []

    def update(self):
        """更新展示的内容"""
        print("-"*20)
        print("语音输入程序运行中...\n注：如有弹出一些英文莫名其妙的英文可以忽略，属于正常情况")
        print("-"*5)
        print(f"当前消息: {self.msg}")
        print("-"*5)
        print(time.time())
        print(f"上次发送时间: {time.time() - self.last_send_time:.1f}秒前")
        print(f"正在处理: {self.doing_active}")
        print(f"正在录音: {self.lis_show_active}")

        if not self.exit_active:
            # 停止所有子线程
            self.lis_active = False
            self.dis_active = False

            # 等待所有子线程结束（设置超时时间）
            for thread in self.sub_threads:
                thread.join(timeout=1.0)

            print(f"最终消息: {self.msg}")
            print("语音输入程序已退出")
        print("-"*20)

    def run(self):
        """
        启动语音输入程序
        :return:
        """
        print("启动语音输入程序...")

        # 创建并启动监听线程
        listen_thread1 = threading.Thread(target=self.listen, name="ListenThread-001")
        listen_thread1.daemon = True  # 设置为守护线程
        listen_thread1.start()
        self.sub_threads.append(listen_thread1)
        print("线程001 - 监听启动")

        # 创建并启动音频处理线程
        dispose_thread = threading.Thread(target=self.dispose_audio, name="DisposeThread-003")
        dispose_thread.daemon = True  # 设置为守护线程
        dispose_thread.start()
        self.sub_threads.append(dispose_thread)
        print("线程003 - 音频处理启动")

    def listen(self):
        """
        开始录音并识别
        :return:
        """
        while self.lis_active:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    print(
                        f"[{threading.current_thread().name}] 🎤 正在聆听...（说'退出'结束）"
                    )

                    try:
                        self.lis_show_active = True  # 展示录音
                        audio = self.recognizer.listen(
                            source,
                            timeout=self.RC.ONE_AUDIO_LENGTH-1,
                            phrase_time_limit=self.RC.ONE_AUDIO_LENGTH
                        )

                        # 将音频数据放入队列
                        self.audio_data.put(audio)  # 加入队列
                        logger.log(
                            f"[{threading.current_thread().name}] 音频已采集并放入队列",
                            self.ID,
                            "DEBUG"
                        )
                        self.lis_show_active = False  # 停止展示录音
                    except sr.WaitTimeoutError:
                        self.lis_show_active = False  # 停止展示录音
                        logger.log(
                            f"[{threading.current_thread().name}] ⏰ 听音超时",
                            self.ID,
                            "INFO"
                        )
                    except sr.UnknownValueError:
                        self.lis_show_active = False  # 停止展示录音
                        logger.log(
                            f"[{threading.current_thread().name}] ❓ 无法识别语音",
                            self.ID,
                            "WARNING"
                        )
                    except sr.RequestError as e:
                        self.lis_show_active = False  # 停止展示录音
                        logger.log(
                            f"[{threading.current_thread().name}] 🌐 语音服务错误: {e}",
                            self.ID,
                            "ERROR"
                        )
            except Exception as e:
                logger.log(
                    f"[{threading.current_thread().name}] 监听异常: {e}",
                    self.ID,
                    "ERROR"
                )
                time.sleep(0.5)  # 避免异常时快速循环

    def dispose_audio(self):
        """
        音频转文字
        :return:
        """
        while self.dis_active:
            try:
                # 使用阻塞获取，设置超时时间
                temp = self.audio_data.get(timeout=0.5)

                try:
                    text: str = self.recognizer.recognize_vosk(temp)  # 使用VOSK识别
                    print(f"[{threading.current_thread().name}] 🗣️ 识别结果: {text}")

                    text = text.replace(" ", "")  # 去除空格

                    if text.isspace() or text == "":
                        continue  # 空消息，跳过

                    # 更新消息
                    self.msg = text
                    self.undisposed_num += 1  # 未处理消息数+1
                    if len(self.msg_list) > 100:
                        self.msg_list.pop(0)  # 超过200条消息，删除最早的消息
                        self.msg_list.append(self.msg)
                    else:
                        self.msg_list.append(self.msg)
                except sr.UnknownValueError:
                    print(f"[{threading.current_thread().name}] ❓ 无法识别音频内容")
                except sr.RequestError as e:
                    print(f"[{threading.current_thread().name}] 🌐 语音服务错误: {e}")
            except queue.Empty:
                continue  # 队列为空，继续循环
            except Exception as e:
                print(f"[{threading.current_thread().name}] 音频处理异常: {e}")

        print(f"[{threading.current_thread().name}] 音频处理线程结束")

    def reply_send(self):
        """收到回复"""
        self.doing_active = False

    def get_msg(self) -> list[str]:
        """
        外部API：获取当前消息
        :return:
        """
        if self.undisposed_num <= 0:
            return []  # 没有未处理消息
        data = self.msg_list[-self.undisposed_num:]
        self.undisposed_num = 0  # 重置未处理消息数
        self.doing_active = True
        logger.log(f"消息已获取：{data}", self.ID, "INFO")
        return data

    def enter_msg(self, msg: list | str):
        """
        外部API：输入消息
        :param msg: 支持列表或字符串
        :return:
        """
        if isinstance(msg, list):
            for m in msg:
                self.msg_list.append(m)
            self.msg = self.msg_list[-1]
            self.undisposed_num += len(msg)  # 添加未处理消息数
            # logger.log(f"当前消息数：{self.undisposed_num}", self.ID, "INFO")
        else:
            self.msg = msg
            self.msg_list.append(msg)
            self.undisposed_num += 1

    def stop(self):
        """
        结束语音输入程序
        :return:
        """
        self.exit_active = False  # 退出程序
        self.dis_active = False  # 结束音频处理线程
        self.lis_active = False  # 结束监听线程
        self.sub_threads.clear()  # 清空子线程列表
        print("语音输入程序已停止")

    def reply_test(self, ID):
        """
        响应自检
        :return:
        """
        logger.log(f"{self.ID}, 自检响应成功", ID, "INFO")
        return True


"""if __name__ == '__main__':
    main = SpeechRecognizer()
    main.start()

    # 等待主线程结束
    main.join()
    print("程序完全退出")"""
