import win32com.client
import pythoncom
import threading
import time


class TextToSpeech:
    def __init__(self):
        """初始化语音引擎"""
        try:
            # 初始化COM库（单线程）
            pythoncom.CoInitialize()

            # 创建语音引擎
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")

            # 打印语音引擎信息
            print(f"语音引擎创建成功: {self.speaker}")
            print(f"引擎状态: {self.speaker.Status}")

            # 获取并显示可用语音
            self.voices = self.get_available_voices()
            self.display_voice_info()

            # 尝试设置中文语音
            self.set_chinese_voice()

        except Exception as e:
            print(f"初始化语音引擎失败: {e}")
            raise

    def get_available_voices(self):
        """获取所有可用的语音"""
        voices = []
        try:
            voices_obj = self.speaker.GetVoices()
            print(f"找到 {voices_obj.Count} 个语音")

            for i in range(voices_obj.Count):
                voice = voices_obj.Item(i)
                voice_info = {
                    'index': i,
                    'id': voice.Id,
                    'name': voice.GetDescription(),
                    'gender': voice.GetAttribute('Gender'),
                    'age': voice.GetAttribute('Age'),
                    'language': voice.GetAttribute('Language')
                }
                voices.append(voice_info)
        except Exception as e:
            print(f"获取语音列表失败: {e}")

        return voices

    def display_voice_info(self):
        """显示语音信息"""
        print("\n=== 系统语音信息 ===")
        if self.voices:
            for v in self.voices:
                print(f"语音 [{v['index']}]: {v['name']}")
                print(f"  语言: {v['language']}")
                print(f"  性别: {v['gender']}")
                print(f"  年龄: {v['age']}")
                print()
        else:
            print("未找到任何语音")

    def set_chinese_voice(self):
        """尝试设置中文语音"""
        # 中文语音的语言代码通常是 804 (简体中文) 或 404 (繁体中文)
        chinese_languages = ['804', '404', '2052', '1028']

        for voice in self.voices:
            lang_str = str(voice['language'])
            if any(code in lang_str for code in chinese_languages):
                try:
                    voices_obj = self.speaker.GetVoices()
                    self.speaker.Voice = voices_obj.Item(voice['index'])
                    print(f"✓ 已设置中文语音: {voice['name']}")
                    return True
                except Exception as e:
                    print(f"设置中文语音失败: {e}")

        # 如果没有中文语音，使用第一个可用语音
        if self.voices:
            try:
                voices_obj = self.speaker.GetVoices()
                self.speaker.Voice = voices_obj.Item(0)
                print(f"✓ 使用默认语音: {self.voices[0]['name']}")
                return True
            except Exception as e:
                print(f"设置默认语音失败: {e}")

        return False

    def speak(self, text, wait=True):
        """
        朗读文本

        Args:
            text: 要朗读的文本
            wait: 是否等待朗读完成
        """
        if not text:
            print("错误: 文本为空")
            return

        print(f"正在朗读: {text[:50]}...")

        try:
            # 清除之前的语音
            self.speaker.Speak("", 2)

            # 设置适当的参数
            self.speaker.Rate = 0  # 语速：-10到10
            self.speaker.Volume = 100  # 音量：0到100

            if wait:
                # 同步朗读（阻塞）
                self.speaker.Speak(text)
                print("朗读完成")
            else:
                # 异步朗读
                self.speaker.Speak(text, 1)
                print("开始异步朗读")

        except Exception as e:
            print(f"朗读出错: {e}")

    def speak_async(self, text):
        """异步朗读"""

        def _speak():
            try:
                # 在新线程中初始化COM
                pythoncom.CoInitialize()
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Rate = 0
                speaker.Volume = 100
                speaker.Speak(text)
                pythoncom.CoUninitialize()
                print("异步朗读完成")
            except Exception as e:
                print(f"异步朗读出错: {e}")

        # 创建并启动线程
        thread = threading.Thread(target=_speak)
        thread.daemon = True
        thread.start()
        return thread

    def test_system_voice(self):
        """测试系统语音功能"""
        print("\n=== 测试语音功能 ===")

        # 测试短句
        test_texts = [
            "你好，世界",
            "Hello World",
            "这是一个测试",
            "12345",
            "Python文字转语音"
        ]

        for text in test_texts:
            print(f"测试: {text}")
            self.speak(text, wait=True)
            time.sleep(0.5)

    def save_to_wav(self, text, filename="output.wav"):
        """保存语音到WAV文件"""
        try:
            print(f"正在保存语音到: {filename}")

            # 创建文件流对象
            stream = win32com.client.Dispatch("SAPI.SpFileStream")

            # 打开文件
            from win32com.client import constants
            stream.Open(filename, 3, False)  # 3表示创建模式

            # 设置音频格式（16kHz, 16bit, Mono）
            format_obj = win32com.client.Dispatch("SAPI.SpAudioFormat")
            format_obj.Type = 22  # SAFT22kHz16BitMono

            # 设置输出流
            old_stream = self.speaker.AudioOutputStream
            self.speaker.AudioOutputStream = stream

            # 朗读并保存
            self.speaker.Speak(text)

            # 恢复原输出流
            self.speaker.AudioOutputStream = old_stream

            # 关闭文件流
            stream.Close()

            print(f"✓ 文件保存成功: {filename}")
            return True

        except Exception as e:
            print(f"保存文件失败: {e}")
            return False


def diagnose_system():
    """诊断系统语音功能"""
    print("=== 系统语音诊断 ===")

    try:
        # 测试COM库
        pythoncom.CoInitialize()

        # 创建语音对象
        speaker = win32com.client.Dispatch("SAPI.SpVoice")

        # 测试简单语音
        print("正在测试基本语音功能...")
        speaker.Speak("测试", 0)
        print("✓ 基本语音功能正常")

        # 检查语音数量
        voices = speaker.GetVoices()
        print(f"系统语音数量: {voices.Count}")

        if voices.Count == 0:
            print("✗ 未找到任何语音，请安装语音包")
            return False

        # 显示语音信息
        for i in range(voices.Count):
            voice = voices.Item(i)
            print(f"语音 {i}: {voice.GetDescription()}")

        pythoncom.CoUninitialize()
        return True

    except Exception as e:
        print(f"✗ 系统诊断失败: {e}")
        return False


# 测试函数
def main_test():
    """主测试函数"""
    print("=" * 50)
    print("文字转语音工具测试")
    print("=" * 50)

    # 首先诊断系统
    if not diagnose_system():
        print("\n请先解决系统问题，然后重试")
        return

    print("\n" + "=" * 50)
    print("创建TTS实例...")

    try:
        # 创建TTS实例
        tts = TextToSpeech()

        # 测试朗读
        print("\n" + "=" * 50)
        print("测试朗读功能...")

        # 测试同步朗读
        tts.speak("欢迎使用文字转语音工具")
        time.sleep(1)

        # 测试异步朗读
        print("\n测试异步朗读...")
        tts.speak_async("这是异步朗读测试")
        time.sleep(3)  # 等待异步朗读完成

        # 测试保存到文件
        print("\n" + "=" * 50)
        print("测试保存到文件...")
        tts.save_to_wav("这是一个保存到文件的测试", "test_output.wav")

        # 交互模式
        print("\n" + "=" * 50)
        print("进入交互模式，输入'q'退出")

        while True:
            text = input("\n请输入要朗读的文本: ")
            if text.lower() == 'q':
                break

            if text.strip():
                # 使用异步方式避免阻塞输入
                tts.speak_async(text)
            else:
                print("输入不能为空")

    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        print("\n程序结束")


if __name__ == "__main__":
    main_test()
