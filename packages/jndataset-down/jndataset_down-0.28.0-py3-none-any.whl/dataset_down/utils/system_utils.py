import ctypes
import platform
import subprocess
import psutil
import os
import signal
import time
from  dataset_down.log.logger import get_logger

logger = get_logger(__name__)
def get_logicalcpu_count():
    try:
        logical_cores = psutil.cpu_count(logical=True)
        logger.info(f"logical_cores:{logical_cores}")
        return logical_cores
    except Exception as e:
        return os.cpu_count()

def get_physical_cores_count():
    physical_cores = psutil.cpu_count(logical=False)
    logger.info(f"physical_cores:{physical_cores}")
    return physical_cores

def caculate_download_worker_num():
    logical_cores = get_logicalcpu_count()
    physical_cores = get_physical_cores_count()
    if logical_cores is None:
        logical_cores = 0
    if physical_cores is None:
        physical_cores = 0
    worker_num = max(3, (int)(logical_cores /4) , (int)(physical_cores/3))
    logger.info(f"worker_num:{worker_num}")
    return worker_num


def send_ctrl_c_to_process(pid):
    """
    向指定进程发送 CTRL+C 信号
    
    Args:
        pid (int): 进程 ID
        
    Returns:
        bool: 是否成功发送信号
    """
    system = platform.system().lower()
    
    if system == "windows":
        try:
            # 方法2: 使用 GenerateConsoleCtrlEvent
            kernel32 = ctypes.windll.kernel32
            success = kernel32.GenerateConsoleCtrlEvent(0, pid)
            return bool(success)
        except Exception:
            pass
        
        
        try:
            # 方法1: 使用 os.kill 发送 SIGINT
            os.kill(pid, signal.SIGINT)
            return True
        except (ProcessLookupError, PermissionError):
            pass
            
    else:
        try:
            # Linux/Mac 使用 SIGINT
            os.kill(pid, signal.SIGINT)
            return True
        except (ProcessLookupError, PermissionError):
            pass
    
    return False



def find_process_by_name(process_name):
    """
    查找指定名称的运行进程
    
    Args:
        process_name (str): 要查找的进程名称
        
    Returns:
        list: 包含匹配进程信息的列表，每个元素为字典格式 {pid, name, cmdline}
    """
    found_processes = []
    
    # 遍历所有运行的进程
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # 获取进程信息
            pid = proc.info['pid']
            name = proc.info['name']
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            
            # 检查进程名是否匹配
            if process_name.lower() in name.lower() and process_name.lower() in cmdline.lower() and 'stop-running-downloading-process' not in cmdline:
                found_processes.append({
                    'pid': pid,
                    'name': name,
                    'cmdline': cmdline
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # 忽略无法访问的进程
            continue
    
    return found_processes

def stop_process_by_name_cross_platform(process_name):
    """
    跨平台通过进程名停止进程
    
    Args:
        process_name (str): 要停止的进程名称
    """
    # 首先查找进程
    processes = find_process_by_name(process_name)
    
    if not processes:
        print(f"\ncan not find '{process_name}' progess.\n")
        return False
    
    print(f"\nfind {len(processes)} matched processes:\n")
    for proc in processes:
        print(f"  PID: {proc['pid']}, Name: {proc['name']}")
        print(f"  Command: {proc['cmdline']}")
    
    # 根据操作系统选择不同的终止方法
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows系统使用taskkill命令
            for proc in processes:
                try:
                    # 首先尝试发送 CTRL+C 信号
                    if send_ctrl_c_to_process(proc['pid']):
                        # 等待一段时间让进程优雅退出
                        time.sleep(2)
                        
                        # 检查进程是否仍然存在
                        if psutil.pid_exists(proc['pid']):
                            # 如果进程仍然存在，则强制终止
                            subprocess.run(['taskkill', '/F', '/PID', str(proc['pid'])], 
                                        check=True, capture_output=True)
                            print(f"\nforce killing process with PID: {proc['pid']}")
                    else:
                        # 如果发送 CTRL+C 失败，则直接强制终止
                        subprocess.run(['taskkill', '/F', '/PID', str(proc['pid'])], 
                                    check=True, capture_output=True)
                        print(f"\nforce killing process with PID: {proc['pid']}")
                except subprocess.CalledProcessError as e:
                    print(f"\nkilling PID {proc['pid']} failed: {e}")
                
                
                
        else:
            for proc in processes:
                try:
                    if send_ctrl_c_to_process(proc['pid']):
                        time.sleep(2)
                        if psutil.pid_exists(proc['pid']):
                            os.kill(proc['pid'], signal.SIGKILL)
                            print(f"\nforce killing process with PID: {proc['pid']}")
                    else:
                        os.kill(proc['pid'], signal.SIGKILL)
                        print(f"\nforce killing process with PID: {proc['pid']}")
                except subprocess.CalledProcessError as e:
                    print(f"\nkilling PID {proc['pid']} failed: {e}")
        
        return True
    except Exception as e:
        print(f"killing progress failed: {e}")
        return False

def stop_dataset_down_process():
    """
    停止dataset-down相关进程的专用函数
    根据constants.py中的NAME = "dataset-down"定义
    """
    from dataset_down.config.constants import NAME
    
    print(f"searching and stoping {NAME} processes...")
    return stop_process_by_name_cross_platform(NAME)