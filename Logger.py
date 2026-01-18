from Config import LOOP_INTERVAL
from typing import Dict, Any
import threading
import datetime
import queue
import time
import os


class Logger(threading.Thread):
    def __init__(self):
        """初始化日志系统"""
        super().__init__()
        self.ID = "LOG"
        self.start_time = time.time()  # 记录程序启动时间
        self.log_paths = {}  # 日志文件路径缓存

        # 日志消息队列
        self.mes_q = queue.Queue()

        # 日志级别
        self.LEVELS = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4
        }
        self.min_level = self.LEVELS.get("INFO", 1)  # 默认最低日志级别
        # 注：这里DEBUG与INFO级别的日志消息不会被记录到文件中，仅在控制台输出

        # 文件句柄缓存
        self.file_handles: Dict[str, Dict[str, Any]] = {}

        self.active = True  # 日志记录开关
        self._exit = threading.Event()  # 退出标志
        self.daemon = True  # 设置为守护线程

        # 上次检查日期的时间
        self.last_date_check = time.time()
        self.current_date = self._get_beijing_date()

    def _get_beijing_date(self) -> str:
        """获取北京时间的日期字符串 (YYYY-MM-DD)"""
        # 获取北京时间 (UTC+8)
        beijing_time = datetime.datetime.now()
        return beijing_time.strftime("%Y-%m-%d")

    def _check_date_change(self) -> bool:
        """检查日期是否变化，如果变化则返回True并更新"""
        current_time = time.time()
        # 每小时检查一次日期变化，避免频繁检查
        if current_time - self.last_date_check > 3600:
            new_date = self._get_beijing_date()
            if new_date != self.current_date:
                self.current_date = new_date
                self.last_date_check = current_time
                return True
            self.last_date_check = current_time
        return False

    def _get_log_file_path(self, log_id: str) -> str:
        """获取日志文件完整路径，按日期分隔"""
        # 获取日志文件名
        log_file = f"{log_id}.log"

        # 创建logs目录（如果不存在）
        logs_dir = f"logs/{self.current_date}"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
        # 日志文件路径
        return os.path.join(logs_dir, log_file)

    def _get_file_handle(self, log_id: str):
        """获取或创建文件句柄"""
        file_path = self._get_log_file_path(log_id)

        # 检查是否需要重新打开文件（日期变化或文件句柄不存在）
        if log_id not in self.file_handles or \
                self.file_handles[log_id]["path"] != file_path or \
                self.file_handles[log_id]["handle"] is None:

            # 关闭旧的文件句柄（如果存在）
            if log_id in self.file_handles and self.file_handles[log_id]["handle"]:
                try:
                    self.file_handles[log_id]["handle"].close()
                except Exception:
                    pass

            # 创建新的文件句柄
            try:
                file_handle = open(file_path, "a", encoding="utf-8", buffering=1)  # 行缓冲
                self.file_handles[log_id] = {
                    "path": file_path,
                    "handle": file_handle,
                    "last_write": time.time()
                }
                return file_handle
            except Exception as e:
                print(f"[{self.ID}] 无法打开日志文件 {file_path}: {e}")
                return None

        return self.file_handles[log_id]["handle"]

    def _cleanup_old_files(self):
        """清理旧的文件句柄（定期调用）"""
        current_time = time.time()
        files_to_remove = []

        for log_id, file_info in self.file_handles.items():
            # 清理超过30分钟未使用的文件句柄
            if current_time - file_info["last_write"] > 1800:  # 30分钟
                try:
                    if file_info["handle"]:
                        file_info["handle"].close()
                except Exception:
                    pass
                files_to_remove.append(log_id)

        for log_id in files_to_remove:
            del self.file_handles[log_id]

    def run(self):
        """日志处理主循环"""
        print(f"[{self.ID}] 日志系统启动")

        while not self._exit.is_set():
            try:
                # 处理队列中的所有消息
                self._process_queue()

                # 定期清理旧的文件句柄
                if time.time() % 300 < LOOP_INTERVAL:  # 每5分钟清理一次
                    self._cleanup_old_files()

                # 检查日期变化
                if self._check_date_change():
                    print(f"[{self.ID}] 日期已切换至 {self.current_date}")
                    # 日期变化时关闭所有文件句柄，下次写入时会重新打开
                    for log_id in list(self.file_handles.keys()):
                        try:
                            if self.file_handles[log_id]["handle"]:
                                self.file_handles[log_id]["handle"].close()
                        except Exception:
                            pass
                    self.file_handles.clear()

                time.sleep(LOOP_INTERVAL)

            except Exception as e:
                print(f"[{self.ID}] 日志处理循环异常: {e}")
                time.sleep(LOOP_INTERVAL)

        # 退出时关闭所有文件句柄
        self._close_all_handles()
        print(f"[{self.ID}] 日志系统已停止")

    def _process_queue(self):
        """处理队列中的日志消息"""
        batch_size = 100  # 每次处理的最大消息数
        processed = 0

        while processed < batch_size:
            try:
                msg_data = self.mes_q.get_nowait()
                self._write_log(msg_data)
                processed += 1
            except queue.Empty:
                break
            except Exception as e:
                print(f"[{self.ID}] 处理日志消息异常: {e}")

    def _write_log(self, msg_data: dict):
        """写入日志文件"""
        try:
            log_id = msg_data["ID"]
            level = msg_data["level"]

            # 检查日志级别
            if self.LEVELS.get(level, 1) < self.min_level:
                return

            # 获取文件句柄
            file_handle = self._get_file_handle(log_id)
            if not file_handle:
                return

            # 构建日志消息
            log_msg = ""
            if msg_data.get("TIME_active", True):
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                log_msg += f"[{timestamp}] "

            if msg_data.get("LEVEL_active", True):
                log_msg += f"[{level}] "

            # 添加模块ID
            log_msg += f"[{log_id}] "

            # 添加消息内容
            log_msg += msg_data["message"]

            # 写入文件
            file_handle.write(log_msg + "\n")

            # 更新最后写入时间
            if log_id in self.file_handles:
                self.file_handles[log_id]["last_write"] = time.time()

            # 控制台输出
            if level in ["ERROR", "CRITICAL"]:
                print(f"[{self.ID}] {log_msg}")

        except Exception as e:
            print(f"[{self.ID}] 写入日志失败: {e}")

    def _close_all_handles(self):
        """关闭所有文件句柄"""
        for log_id in list(self.file_handles.keys()):
            try:
                if self.file_handles[log_id]["handle"]:
                    self.file_handles[log_id]["handle"].close()
            except Exception:
                pass
        self.file_handles.clear()

    def log(self, message: str, log_id: str, level: str = "INFO",
            time_active: bool = True, level_active: bool = True):
        """
        添加日志消息到队列

        Args:
            message: 日志消息内容
            log_id: 模块ID
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            time_active: 是否包含时间戳
            level_active: 是否包含日志级别
        """
        if not self.active or not message:
            return

        try:
            self.mes_q.put({
                "message": message,
                "ID": log_id,
                "level": level,
                "TIME_active": time_active,
                "LEVEL_active": level_active
            }, timeout=0.1)  # 超时时间，避免队列满时阻塞
        except queue.Full:
            # 队列满时，简单打印到控制台
            print(f"[{self.ID}] 日志队列已满，丢弃消息: {message}")
        except Exception as e:
            print(f"[{self.ID}] 添加日志失败: {e}")

    def stop(self):
        """停止日志系统"""
        self._exit.set()
        self.join(timeout=2.0)

    def set_min_level(self, level: str):
        """设置最低日志级别"""
        if level in self.LEVELS:
            self.min_level = self.LEVELS[level]
            self.log(f"设置最低日志级别为 {level}", self.ID, "INFO")


# 全局日志实例
_global_logger = None


def get_logger() -> Logger:
    """获取全局日志实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger()
        _global_logger.start()
    return _global_logger
