import os
import time
import glob
import shutil
import multiprocessing
from src.mlog_util import MultiProcessSafeSizeRotatingHandler, get_logger

# --- 修复：将工作函数定义为顶级函数 ---

def write_logs_worker(process_id, num_messages=1000):
    """在指定进程中写入日志（用于测试1）"""
    handler = MultiProcessSafeSizeRotatingHandler(
        filename="logs/size.log",
        maxBytes=1 * 1024 * 1024,  # 1MB
        backupCount=5
    )
    logger = get_logger(f"test_process_{process_id}", custom_handlers=handler, add_console=False)
    
    for i in range(num_messages):
        logger.info(f"Process {process_id} - Message {i}: " + "x" * 100)  # 每条消息约100字节

def concurrent_rotation_worker(worker_id):
    """并发轮转测试的工作进程（用于测试3）"""
    handler = MultiProcessSafeSizeRotatingHandler(
        filename="logs/size.log",
        maxBytes=500 * 1024,  # 500KB
        backupCount=3
    )
    logger = get_logger(f"worker_{worker_id}", custom_handlers=handler, add_console=False)
    
    for i in range(200):
        logger.info(f"Worker {worker_id} - Log {i}: " + "z" * 150)
        time.sleep(0.01)  # 模拟实际工作负载

# --- 测试函数 ---

def setup_test_environment():
    """设置测试环境，清理旧的日志文件"""
    if os.path.exists("logs"):
        shutil.rmtree("logs")
    os.makedirs("logs", exist_ok=True)

def test_large_backup_count():
    """测试1: 大backupCount，验证轮转是否生效，日志是否丢失"""
    print("\n=== 测试1: 大backupCount测试 ===")
    setup_test_environment()
    
    # 启动多个进程写入日志
    processes = []
    for i in range(3):
        # 使用顶级函数
        p = multiprocessing.Process(target=write_logs_worker, args=(i, 500))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
    
    # 检查日志文件
    log_files = sorted(glob.glob("logs/size.log*"))
    print(f"生成的日志文件: {log_files}")
    
    # 验证所有文件内容完整性
    total_messages = 0
    for log_file in log_files:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            total_messages += len(lines)
    
    print(f"总日志条数: {total_messages} (预期: 1500)")
    assert total_messages == 1500, f"日志条数 {total_messages} 不等于预期 1500"
    print("✓ 测试1通过: 多进程日志完整性")

def test_medium_backup_count():
    """测试2: 中等backupCount，触发删除机制"""
    print("\n=== 测试2: 中等backupCount测试 ===")
    setup_test_environment()
    
    # 使用较小的backupCount
    handler = MultiProcessSafeSizeRotatingHandler(
        filename="logs/size.log",
        maxBytes=1 * 1024 * 1024,  # 1MB
        backupCount=2
    )
    logger = get_logger("test_medium", custom_handlers=handler, add_console=False)
    
    # 写入足够多的日志以触发多次轮转
    for i in range(3000):
        logger.info(f"Message {i}: " + "y" * 200)  # 每条消息约200字节
    
    # 检查日志文件
    log_files = sorted(glob.glob("logs/size.log*"))
    print(f"生成的日志文件: {log_files}")
    
    # 验证文件数量不超过backupCount+1
    assert len(log_files) <= 3, f"日志文件数量 {len(log_files)} 超过预期 3"
    
    # 验证最新的日志文件存在
    assert os.path.exists("logs/size.log"), "主日志文件不存在"
    
    # 验证备份文件编号正确
    if len(log_files) > 1:
        assert "size.log.1" in log_files[-1], "备份文件编号不正确"
    
    print("✓ 测试2通过: 中等backupCount测试成功")

def test_concurrent_rotation():
    """测试3: 并发轮转测试"""
    print("\n=== 测试3: 并发轮转测试 ===")
    setup_test_environment()
    
    # 启动多个工作进程
    processes = []
    for i in range(5):
        # 使用顶级函数
        p = multiprocessing.Process(target=concurrent_rotation_worker, args=(i,))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
    
    # 检查日志文件
    log_files = sorted(glob.glob("logs/size.log*"))
    print(f"并发测试生成的日志文件: {log_files}")
    
    # 验证文件数量
    assert len(log_files) <= 4, f"并发测试日志文件数量 {len(log_files)} 超过预期 4"
    
    # 验证日志完整性
    total_lines = 0
    for log_file in log_files:
        with open(log_file, 'r') as f:
            total_lines += len(f.readlines())
    
    print(f"并发测试总日志条数: {total_lines} (预期: 1000)")
    assert total_lines == 1000, f"并发测试日志条数 {total_lines} 不等于预期 1000"
    print("✓ 测试3通过: 并发轮转测试成功")

def run_all_tests(clean=False):
    """运行所有测试"""
    print("开始运行 MultiProcessSafeSizeRotatingHandler 自动化测试...")
    print(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_large_backup_count()
        # test_medium_backup_count()
        # test_concurrent_rotation()
        
        print("\n🎉 所有测试通过!")
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc() # 打印详细的错误堆栈
    finally:
        if clean:
            # 清理测试环境
            if os.path.exists("logs"):
                shutil.rmtree("logs")

if __name__ == "__main__":
    # 为了安全地在多进程环境中运行，设置启动方法
    # 'spawn' 是跨平台最安全的方法，但启动开销较大
    # 'fork' (仅在Unix上可用) 启动快，但可能有一些副作用
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # 在某些环境（如Jupyter Notebook）中，可能已经设置了启动方法
        pass
    
    run_all_tests(clean=False)
