import os
import time
import glob
import shutil
import multiprocessing
from pathlib import Path
from src.mlog_util import MultiProcessSafeTimeRotatingHandler, get_logger

def setup_test_environment():
    """设置测试环境，清理旧的日志文件"""
    if os.path.exists("logs"):
        shutil.rmtree("logs")
    os.makedirs("logs", exist_ok=True)

def test_large_backup_count():
    """测试1: 大backupCount，验证轮转是否生效，日志是否丢失"""
    print("\n=== 测试1: 大backupCount测试 ===")
    setup_test_environment()

    handler = MultiProcessSafeTimeRotatingHandler(
        filename="logs/time.log",
        when="S",
        backupCount=5 # 5 * 10 = 50s
    )
    logger = get_logger(f"test_time", custom_handlers=handler, add_console=False)

    add_nums = 0
    for i in range(22):
        logger.info(f"{i=}")
        add_nums += 1
        time.sleep(1)
    
    # 检查文件数量
    files_list = list(Path("logs").glob("time.log*"))
    files_num = len(files_list)
    assert files_num == 6, f"文件数量 {files_num} 不等于预期 3"
    print(f"日志数量 = {files_num}, 符合日志要求")
    
    # 验证所有文件内容完整性
    total_messages = 0
    for log_file in files_list:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            total_messages += len(lines)

    assert total_messages == 22, f"日志条数 {total_messages} 不等于预期 22"
    print(f"当前日志一共 {total_messages} 条")

def test_medium_backup_count():
    """
    检测轮询的文件数量是否达到预期
    """
    print("\n=== 测试1: backupCount数量测试 ===")
    setup_test_environment()

    handler = MultiProcessSafeTimeRotatingHandler(
        filename="logs/time.log",
        when="S", 
        backupCount=3 # 2 * 10 = 20s
    )
    logger = get_logger(f"test_time", custom_handlers=handler, add_console=False)
    for i in range(32):
        logger.info(f"{i=}")
        time.sleep(1)

    # 检查文件数量
    files_list = list(Path("logs").glob("time.log*"))
    files_num = len(files_list)
    assert files_num == 3, f"日志条数 {files_num} 不等于预期 3"
    print(f"日志数量 = {files_num}, 符合日志要求")

    """
    TODO: 不知道顺序应该怎么写测试
    """

def run_all_tests():
    """运行所有测试"""
    print("开始运行 MultiProcessSafeTimeRotatingHandler 自动化测试...")
    try:
        test_large_backup_count()
        test_medium_backup_count()
        # test_concurrent_rotation()
        
        print("\n🎉 所有测试通过!")
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc() # 打印详细的错误堆栈
    finally:
        # 清理测试环境
        if os.path.exists("logs"):
            shutil.rmtree("logs")
        pass


if __name__ == "__main__":
    # 为了安全地在多进程环境中运行，设置启动方法
    # 'spawn' 是跨平台最安全的方法，但启动开销较大
    # 'fork' (仅在Unix上可用) 启动快，但可能有一些副作用
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # 在某些环境（如Jupyter Notebook）中，可能已经设置了启动方法
        pass
    
    run_all_tests()
