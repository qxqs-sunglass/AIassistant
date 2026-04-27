from .Template import Template
import pathlib
import json
import os


class SYS_C(Template):
    def __init__(self):
        """
        系统控制类
        """
        super().__init__()
        self.intro = "SYS_C：负责系统控制，相关操作：关机、重启、锁定、打开应用程序"
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
        self.tools = [
            {
                "name": "open_app",
                "description": "打开应用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "应用名称，如：'微信'、'酷我音乐'。",
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "shutdown_s",
                "description": "关闭计算机"
            },
            {
                "name": "shutdown_r",
                "description": "重启计算机"
            },
            {
                "name": "shutdown_i",
                "description": "注销账户"
            }
        ]
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

    def open_app(self, **kwargs):
        """
        控制应用打开
        :return:
        """
        if kwargs.get("name", None):
            return {
                "role": "tool",
                "content": "tool未响应，目标参数不存在：name",
                "logs": {"msg": "应用名称出错", "level": "ERROR"}
            }
        try:
            os.startfile(self.app_dict[kwargs.get("name")])
            return {
                "role": "tool",
                "content": f"成功启动应用：{kwargs['name']}",
                "logs": {"msg": "应用名称出错", "level": "INFO"}
            }
        except Exception as e:
            return {
                "role": "tool",
                "content": "tool调用失败。",
                "logs": {"msg": f"问题出现在：{e}", "level": "ERROR"}
                }

    def shutdown_s(self):
        """
        关机操作
        :return:
        """
        os.system("shutdown /s" + self.shutdown_t)

        # 避免测试出问题
        os.system("shutdown /a")
        return {
            "role": "tool",
            "content": "已成功执行",
            "logs": {
                "msg": "已成功执行",
                "level": "INFO"
            }
        }

    def shutdown_r(self):
        """
        重启操作
        :return:
        """
        os.system("shutdown /r" + self.shutdown_t)

        # 避免测试出问题
        os.system("shutdown /a")
        return {
            "role": "tool",
            "content": "已成功执行",
            "logs": {
                "msg": "已成功执行",
                "level": "INFO"
            }
        }

    def shutdown_i(self):
        """
        注销操作
        :return:
        """
        os.system("shutdown /i" + self.shutdown_t)

        # 避免测试出问题
        os.system("shutdown /a")
        return {
            "role": "tool",
            "content": "已成功执行",
            "logs": {
                "msg": "已成功执行",
                "level": "INFO"
            }
        }
