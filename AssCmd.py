from Config import __version__, __author__, LOOP_INTERVAL
import rich.console
import Logger
import socket
import json
import os

console = rich.console.Console()  # 创建控制台实例
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 创建套接字
d = ("127.0.0.1", 8001)

# 注：此处是发送到8001号端口，接收端需要绑定8002号端口


logger = Logger.get_logger()  # 获取日志实例


class AssCmd:
    def __init__(self):
        """
        外部控制器：cmd控制台
        """
        self.ID = "AssCmd"
        self.exit_active = True

    # 修改AssCmd.py的run方法：
    def run(self):
        while self.exit_active:
            os.system("cls")
            print("=" * 50)
            print("此页面为控制台组件，用于开发时使用")
            print(f"版本：{__version__}")
            print(f"作者：{__author__}")
            print("输入提示：【指令】或【指令 消息内容】")
            print(f"发送到：{d}")
            user_input = input("请输入指令(退出使用esc)：")
            print("=" * 50)

            if user_input == "esc":
                self.exit_active = False
                break

            # 分割输入
            parts = user_input.split(" ")
            cmd = parts[0]  # 第一个单词是指令
            msg = parts[1:]  # 剩余部分是消息内容

            data = {
                "addr": "AssCmd",
                "cmd": cmd,  # 现在cmd是字符串
                "msg": msg  # 消息作为单独的列表
            }
            sock.sendto(json.dumps(data).encode("utf-8"), d)
            logger.log(f"发送指令：{data}", self.ID, "INFO")


if __name__ == "__main__":
    main = AssCmd()
    main.run()

