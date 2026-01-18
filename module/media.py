from ctypes import wintypes, windll, Structure, POINTER, Union, byref, sizeof
import keyboard
import time


class WinMedia:
    # 虚拟键码常量
    VK_MEDIA_PLAY_PAUSE = 0xB3
    VK_MEDIA_NEXT_TRACK = 0xB0
    VK_MEDIA_PREV_TRACK = 0xB1
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF
    WorkWord = """

        适用于媒体控制的函数：
        - play_pause()  播放/暂停
        - next_track()  下一首
        - previous_track()  上一首
        - volume_mute()  静音
        - volume_down()  音量减小
        - volume_up()  音量增加
    
    """

    @staticmethod
    def send_media_key(key_code):
        """发送媒体键"""
        try:
            # 方法1: 使用keybd_event（简单直接）
            windll.user32.keybd_event(key_code, 0, 0, 0)  # 按下
            time.sleep(0.05)  # 短暂延迟
            windll.user32.keybd_event(key_code, 0, 2, 0)  # 释放
            return True
        except Exception as e:
            print(f"keybd_event失败: {e}")

            # 方法2: 使用SendInput（更可靠）
            try:
                # 定义INPUT结构
                class KEYBDINPUT(Structure):
                    _fields_ = [
                        ("wVk", wintypes.WORD),
                        ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD),
                        ("time", wintypes.DWORD),
                        ("dwExtraInfo", POINTER(wintypes.ULONG))
                    ]

                class INPUT(Structure):
                    class _I(Union):
                        _fields_ = [("ki", KEYBDINPUT)]

                    _anonymous_ = ("_i",)
                    _fields_ = [
                        ("type", wintypes.DWORD),
                        ("_i", _I)
                    ]

                INPUT_KEYBOARD = 1
                KEYEVENTF_KEYUP = 0x0002

                # 创建输入数组
                inputs = (INPUT * 2)()

                # 按下键
                inputs[0].type = INPUT_KEYBOARD
                inputs[0].ki.wVk = key_code

                # 释放键
                inputs[1].type = INPUT_KEYBOARD
                inputs[1].ki.wVk = key_code
                inputs[1].ki.dwFlags = KEYEVENTF_KEYUP

                # 发送输入
                windll.user32.SendInput(2, byref(inputs), sizeof(INPUT))
                return True
            except Exception as e2:
                print(f"SendInput失败: {e2}")

        return False

    @classmethod
    def play_pause(cls):
        """播放/暂停"""
        print("🎵 发送播放/暂停命令")
        return cls.send_media_key(cls.VK_MEDIA_PLAY_PAUSE)

    @classmethod
    def next_track(cls):
        """下一首"""
        print("🎵 发送下一首命令")
        return cls.send_media_key(cls.VK_MEDIA_NEXT_TRACK)

    @classmethod
    def previous_track(cls):
        """上一首"""
        print("🎵 发送上一首命令")
        return cls.send_media_key(cls.VK_MEDIA_PREV_TRACK)

    @classmethod
    def volume_mute(cls):
        """静音"""
        print("🔇 发送静音命令")
        return cls.send_media_key(cls.VK_VOLUME_MUTE)

    @classmethod
    def volume_down(cls):
        """音量减小"""
        print("🔉 发送音量减小命令")
        return cls.send_media_key(cls.VK_VOLUME_DOWN)

    @classmethod
    def volume_up(cls):
        """音量增加"""
        print("🔊 发送音量增加命令")
        return cls.send_media_key(cls.VK_VOLUME_UP)


class KeyMedia:
    """使用keyboard库的媒体控制器"""
    WorkWord = """
        适用于媒体控制的函数：
        - play_pause()  播放/暂停
        - next_track()  下一首
        - previous_track()  上一首
        - volume_mute()  静音
        - volume_down()  音量减小
        - volume_up()  音量增加
    """


    @staticmethod
    def play_pause():
        """播放/暂停"""
        try:
            keyboard.press_and_release('play/pause media')
            print("⏯️  播放/暂停 (keyboard库)")
            return True
        except:
            return False

    @staticmethod
    def next_track():
        """下一首"""
        try:
            keyboard.press_and_release('next track')
            print("⏭️  下一首 (keyboard库)")
            return True
        except:
            return False

    @staticmethod
    def previous_track():
        """上一首"""
        try:
            keyboard.press_and_release('previous track')
            print("⏮️  上一首 (keyboard库)")
            return True
        except:
            return False


# 选择最佳的控制器
def get_media_controller():
    """获取媒体控制器"""
    return WinMedia()


# 全局媒体控制器实例
media_controller = get_media_controller()


def test_media_controls():
    """测试媒体控制功能"""
    print("🔍 测试媒体控制功能...")

    # 测试播放/暂停
    print("\n1. 测试播放/暂停:")
    if media_controller.play_pause():
        print("✅ 播放/暂停测试成功")
    else:
        print("❌ 播放/暂停测试失败")
    time.sleep(1)

    # 测试下一首
    print("\n2. 测试下一首:")
    if media_controller.next_track():
        print("✅ 下一首测试成功")
    else:
        print("❌ 下一首测试失败")
    time.sleep(2)

    # 测试上一首
    print("\n3. 测试上一首:")
    if media_controller.previous_track():
        print("✅ 上一首测试成功")
    else:
        print("❌ 上一首测试失败")
    time.sleep(1)


if __name__ == "__main__":
    test_media_controls()
