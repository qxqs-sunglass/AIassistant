import Logger
import pathlib
import json
import os


class SYS_C:
    def __init__(self):
        """
        系统控制类
        """
        self.intro = "媒体控制：MEDIA_C (控制音乐或其他媒体的：播放/暂停、下一首、上一首)"
        self.WorkWord = """
        适用于系统控制的函数：
        - open_app()  打开指定应用
        - shutdown_s() 电脑关机
        - shutdown_r() 电脑重启
        - shutdown_i() 电脑注销
        
        当前记录的应用：
        """
        self.Work_dict = {
            "open_app": self.open_app,
            "open_app()": self.open_app,
            "shutdown_s": self.shutdown_s,
            "shutdown_s()": self.shutdown_s,
            "shutdown_r": self.shutdown_r,
            "shutdown_r()": self.shutdown_r,
            "shutdown_i": self.shutdown_i,
            "shutdown_i()": self.shutdown_i,
        }
        self.temp = ''
        self.app_dict = {}
        self.shutdown_t = " /t 3"

    def init(self):
        """
        初始化
        :return:
        """
        with open("config\\apps.json", "r", encoding="utf-8") as f:
            tempdata: dict = json.load(f)
            f.close()
        if not tempdata.get("f", False):
            # f值为false则代表第一次启动
            # 第一次启动扫描一遍桌面
            desktop = "ERROR"
            try:
                desktop = pathlib.Path.home().joinpath("Desktop")
            except FileNotFoundError:
                desktop = pathlib.Path.home().joinpath("OneDrive\\Desktop")
            except Exception as e:
                print(e)
            if desktop == "ERROR":
                return
            for filename in os.listdir(desktop):
                name = filename.split(".")[0]
                if filename.endswith(".lnk"):
                    self.app_dict[name] = [f"{desktop}\\{filename}"]
            with open(f"config\\apps.json", "w", encoding="utf-8") as f:
                json.dump(self.app_dict, f, ensure_ascii=False, indent=4)
                f.close()
        else:
            self.app_dict = tempdata

    def open_app(self):
        """
        控制应用打开
        :return:
        """
        try:
            os.startfile(self.temp)
        except Exception:
            return None

    def shutdown_s(self):
        """
        关机操作
        :return:
        """
        os.system("shutdown /s" + self.shutdown_t)

        # 避免测试出问题
        os.system("shutdown /a")

    def shutdown_r(self):
        """
        重启操作
        :return:
        """
        os.system("shutdown /r" + self.shutdown_t)

        # 避免测试出问题
        os.system("shutdown /a")

    def shutdown_i(self):
        """
        注销操作
        :return:
        """
        os.system("shutdown /i" + self.shutdown_t)

        # 避免测试出问题
        os.system("shutdown /a")
