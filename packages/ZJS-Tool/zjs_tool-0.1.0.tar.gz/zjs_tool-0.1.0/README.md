# ZJS_Tool => v0.1.0 -> 20251222   
## 主函数前置代码 (Preceding Code of Main Function)   
### 1. 获取程序基础路径 (Get_Base_Path)   
* 功能：获取当前程序的根目录路径 (可用于pyinstall下的根目录定义) 。   
* 参数说明：   
=> Main_Path: 主函数路径, 若未传入，自动尝试获取调用者路径   
<= Main_Path (str): 主程序运行的根路径   
#### 代码示例：   
     >>> Main_Path = os.path.dirname(f"{__file__}")   
     ... Main_Path = os.path.dirname()   
### 2. 日志配置 (Log_Configuration)   
* 功能：初始化日志实例,定义日志输出格式、存储路径及级别。   
* 参数说明：   
=> Main_Path (str): 当前程序的根目录路径   
=> log_name (str): 日志名称,用于区分不同模块日志   
<= log (str): 包含 debug / info / warning / error   
#### 代码示例：   
     >>> log = Log_FCN(Main_Path, "日志名称")   
     >>> log.debug("函数名称“, f"日志内容")   
     ... log.info("函数名称“, f"日志内容")   
     ... log.warning("函数名称“, f"日志内容")   
     ... log.error("函数名称“, f"日志内容")