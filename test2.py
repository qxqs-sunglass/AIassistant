import os


# 直接启动快捷方式
def launch_shortcut(lnk_path):
    try:
        os.startfile(lnk_path)
        return True
    except Exception as e:
        print(f"启动失败: {e}")
        return False


# 示例：启动Chrome快捷方式
launch_shortcut(r"C:\Users\黄文浩\Desktop\酷狗音乐.lnk")
