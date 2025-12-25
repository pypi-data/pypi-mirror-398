#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Created: 2025/12/22 13:34
# @File:    Log_Configuration_FCN.py
# @Author:  Jinshuo Zhang
# @Contact: zhangjinshuowork@163.com
# @Software: PyCharm
# @Purpose:
# -----------------------------------------------------------------------------
# Updated: 2025/12/22 13:34 (v0.1.0)
# Updated Content: 初始版本
# =============================================================================

""" ============================== 标准库 ============================== """
import inspect
import os
import sys
import shutil
import datetime

try:
    from typing import Optional
except ImportError:
    Optional = None

""" ============================== 第三方库 ============================== """

""" ============================== 外部函数库 =============================== """

""" ============================== 全局参数定义 =============================== """
# 日志核心配置
LOG_CONFIG = {
    # 日志保留天数定义: 10 days
    "LOG_RETENTION_DAYS": 10
}

# 日志级别颜色代码
LEVEL_COLORS = {
    "DEBUG": "\033[94m",  # 蓝色
    "INFO": "\033[92m",  # 绿色
    "WARNING": "\033[93m",  # 黄色
    "ERROR": "\033[91m",  # 红色
    "RESET": "\033[0m"  # 重置颜色
}

""" ============================== Get_Base_Path =============================== """
def Get_Base_Path(Main_Path=None):
    """
    获取程序基础路径
    -------------------------------
    Arg:
        Main_Path: 主函数路径 || None => 自动尝试获取调用者路径
    Returns:
        str: 主程序运行的根路径（未打包时返回调用文件所在目录，打包后返回EXE所在目录）
    """
    bundled_state = getattr(sys, 'frozen', False)
    if bundled_state:
        base_path = os.path.abspath(os.path.dirname(sys.executable))
    else:
        if Main_Path is None:
            # 兼容低版本 inspect.stack 用法
            try:
                caller_frame = inspect.stack()[1]
                Main_Path = caller_frame[1]  # 低版本 stack 返回元组，索引1是文件名
            except (IndexError, AttributeError):
                Main_Path = __file__
        base_path = os.path.abspath(os.path.dirname(Main_Path))

    # 兼容 Windows/Linux 路径分隔符
    return os.path.normpath(base_path)


""" ============================== Log_Configuration =============================== """
class Log_Configuration(object):
    def __init__(self, Main_Path="", Log_File_Name="Error_Log_File_Name"):
        """
        初始化 Log_Configuration
        Args:
            Main_Path: 主函数路径
            Log_File_Name: 当前日志文件名称
        """
        """ 定义参数 & 参数初始化 """
        # 获取当前时间
        self.current_timestamp = datetime.datetime.now()
        self.current_date = self.current_timestamp.strftime("%Y-%m-%d")

        # 日志文件路径 => main_path / "Log_Files" / Log_File_Name
        if Main_Path:
            main_path = Main_Path
        else:
            main_path = os.getcwd()

        # 兼容低版本路径拼接
        self.log_file_path = os.path.join(
            main_path,
            "Log_Files",
            Log_File_Name
        )

        # 当天日志文件路径
        self.current_date_log_file_path = os.path.join(
            self.log_file_path,
            self.current_date
        )

        # 日志文件名使用当前时间 => 时_分_秒（替换f-string为format）
        self.log_file_Time_name = "{0}.log".format(self.current_timestamp.strftime("%H_%M_%S"))

        # 当前日志文件完整路径
        self.current_log_file_path = os.path.join(
            self.current_date_log_file_path,
            self.log_file_Time_name
        )

        """ 运行前期检查 """
        # 兼容 Python 3.4- 的 os.makedirs 参数（exist_ok 低版本兼容）
        try:
            os.makedirs(self.current_date_log_file_path)
        except OSError as e:
            if e.errno != 17:  # 17 = 文件已存在
                raise

        # 清除过期日志文件和目录
        self._Cleanup_Old_Logs()

    def _Cleanup_Old_Logs(self):
        """ 清理过期的日志文件和目录 """
        try:
            # 计算过期日期（兼容低版本 timedelta）
            retention_days = LOG_CONFIG.get("LOG_RETENTION_DAYS", 10)
            cutoff_date_file_name = (self.current_timestamp - datetime.timedelta(days=retention_days)).date()

            # 检查日志文件路径存在
            if not os.path.exists(self.log_file_path):
                return

            # 遍历所有日期目录
            for date_file in os.listdir(self.log_file_path):
                date_dir = os.path.join(self.log_file_path, date_file)

                # 只处理目录且名称符合日期格式的文件夹
                if not os.path.isdir(date_dir):
                    continue

                try:
                    # 解析日期目录名称
                    date_file_name = datetime.datetime.strptime(date_file, "%Y-%m-%d").date()

                    # 如果目录日期早于截止日期，则删除该目录及其所有内容
                    if date_file_name < cutoff_date_file_name:
                        shutil.rmtree(date_dir)
                        self._Write_Log_File("Log_FCN", "INFO", "已清除: {0}".format(date_dir))

                except ValueError:
                    self._Write_Log_File("Log_FCN", "WARNING", "跳过非日期格式目录: {0}".format(date_file))
                    continue
        except Exception as e:
            self._Write_Log_File("Log_FCN", "ERROR", "清理过期日志时发生错误: {0}".format(str(e)))

    def _Write_Log_File(self, FCN_name, level, message):
        """
        写入日志到文件
        -------------------------------
        Args:
            FCN_name: 函数名称
            level: 日志级别 => "DEBUG" / "INFO" / "WARNING" / "ERROR"
            message: 日志信息
        """
        current_timestamp = datetime.datetime.now()
        log_time = current_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        # 替换f-string为format，兼容低版本
        log_message = "{0}  -  {1}  -  {2}\t:\t{3}\n".format(log_time, FCN_name, level, message)

        try:
            # DEBUG级别日志不写入文件，但可以在控制台显示
            if level != "DEBUG":
                # 兼容 Python 2.7 的文件打开方式（指定编码，兼容不同版本）
                try:
                    # Python 3.x
                    f = open(self.current_log_file_path, "a", encoding="utf-8")
                except TypeError:
                    # Python 2.7
                    f = open(self.current_log_file_path, "a")
                    message = message.encode("utf-8")

                with f:
                    f.write(log_message)

            # 控制台带颜色输出（兼容不同终端）
            color = LEVEL_COLORS.get(level, LEVEL_COLORS["RESET"])
            reset = LEVEL_COLORS["RESET"]
            print("{0}{1}{2}".format(color, log_message.strip(), reset))
        except Exception as e:
            # 兼容 Python 2/3 的标准错误输出
            sys.stderr.write("日志写入失败: {0}\n".format(str(e)))

    """ ---------------------------- 日志函数类型定义 ---------------------------- """

    def debug(self, FCN_name, message):
        """
        记录 DEBUG 级别的日志
        -------------------------------
        Args:
            FCN_name: 函数名称
            message: 日志信息
        """
        self._Write_Log_File(FCN_name, "DEBUG", message)

    def info(self, FCN_name, message):
        """
        记录 INFO 级别的日志
        -------------------------------
        Args:
            FCN_name: 函数名称
            message: 日志信息
        """
        self._Write_Log_File(FCN_name, "INFO", message)

    def warning(self, FCN_name, message):
        """
        记录 WARNING 级别的日志
        -------------------------------
        Args:
            FCN_name: 函数名称
            message: 日志信息
        """
        self._Write_Log_File(FCN_name, "WARNING", message)

    def error(self, FCN_name, message):
        """
        记录 ERROR 级别的日志
        -------------------------------
        Args:
            FCN_name: 函数名称
            message: 日志信息
        """
        self._Write_Log_File(FCN_name, "ERROR", message)
