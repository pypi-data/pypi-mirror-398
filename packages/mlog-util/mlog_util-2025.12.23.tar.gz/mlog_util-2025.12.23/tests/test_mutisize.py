import os
import time
import glob
from multiprocessing import Process
from src.mlog_util import MultiProcessSafeSizeRotatingHandler, get_logger


def count_log_lines(log_dir, log_pattern="size.log*"):
    """统计所有日志文件的总行数"""
    log_files = glob.glob(os.path.join(log_dir, log_pattern))
    total_lines = 0
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                total_lines += lines
                print(f"  {os.path.basename(log_file)}: {lines} lines")
        except Exception as e:
            print(f"  Error reading {log_file}: {e}")
    return total_lines


def write_logs_worker(process_id, num_messages=1000, log_name="size.log", max_bytes=1*1024*1024):
    """在指定进程中写入日志"""
    handler = MultiProcessSafeSizeRotatingHandler(
        filename=f"logs/{log_name}",
        maxBytes=max_bytes,
        backupCount=20
    )
    logger = get_logger(f"test_process_{process_id}", custom_handlers=handler, add_console=False)
    
    for i in range(num_messages):
        logger.info(f"Process {process_id} - Message {i}: " + "x" * 100)
    
    # 确保所有日志都写入
    handler.close()


def cleanup_logs(log_dir="logs", log_pattern="*.log*"):
    """清理测试日志文件"""
    log_files = glob.glob(os.path.join(log_dir, log_pattern))
    for log_file in log_files:
        try:
            os.remove(log_file)
        except Exception as e:
            print(f"Failed to remove {log_file}: {e}")


def test_single_process_no_rotation():
    """测试1.1: 单进程写小日志，不发生轮转 → 验证日志一条不少"""
    print("\n" + "="*70)
    print("测试1.1: 单进程写小日志 - 不发生轮转")
    print("="*70)
    
    cleanup_logs()
    os.makedirs("logs", exist_ok=True)
    
    num_messages = 500
    # 设置较大的 maxBytes，确保不轮转
    write_logs_worker(process_id=1, num_messages=num_messages, 
                      log_name="test1_1.log", max_bytes=10*1024*1024)
    
    time.sleep(0.5)
    
    print("\n日志文件统计:")
    total_lines = count_log_lines("logs", "test1_1.log*")
    
    print(f"\n预期日志条数: {num_messages}")
    print(f"实际日志条数: {total_lines}")
    
    assert total_lines == num_messages, f"日志丢失! 预期 {num_messages}, 实际 {total_lines}"
    print("✓ 测试通过: 日志一条不少")


def test_multi_process_no_rotation():
    """测试1.2: 多进程并发写小日志，不发生轮转 → 验证日志一条不少"""
    print("\n" + "="*70)
    print("测试1.2: 多进程并发写小日志 - 不发生轮转")
    print("="*70)
    
    cleanup_logs()
    os.makedirs("logs", exist_ok=True)
    
    num_processes = 5
    num_messages_per_process = 200
    expected_total = num_processes * num_messages_per_process
    
    processes = []
    for i in range(num_processes):
        p = Process(target=write_logs_worker, 
                   args=(i, num_messages_per_process, "test1_2.log", 10*1024*1024))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
    
    time.sleep(1)
    
    print("\n日志文件统计:")
    total_lines = count_log_lines("logs", "test1_2.log*")
    
    print(f"\n预期日志条数: {expected_total} ({num_processes} 进程 × {num_messages_per_process} 条)")
    print(f"实际日志条数: {total_lines}")
    
    assert total_lines == expected_total, f"日志丢失! 预期 {expected_total}, 实际 {total_lines}"
    print("✓ 测试通过: 多进程日志一条不少")


def test_single_process_with_rotation():
    """测试2.1: 单进程写日志触发多次轮转 → 验证所有文件总行数正确"""
    print("\n" + "="*70)
    print("测试2.1: 单进程写大量日志 - 触发多次轮转")
    print("="*70)
    
    cleanup_logs()
    os.makedirs("logs", exist_ok=True)
    
    num_messages = 5000
    # 设置较小的 maxBytes，确保会轮转多次
    write_logs_worker(process_id=1, num_messages=num_messages, 
                      log_name="test2_1.log", max_bytes=100*1024)  # 100KB
    
    time.sleep(1)
    
    print("\n日志文件统计:")
    total_lines = count_log_lines("logs", "test2_1.log*")
    
    print(f"\n预期日志条数: {num_messages}")
    print(f"实际日志条数: {total_lines}")
    
    # 检查是否发生了轮转
    log_files = glob.glob("logs/test2_1.log*")
    print(f"\n生成的日志文件数: {len(log_files)}")
    
    assert total_lines == num_messages, f"日志丢失! 预期 {num_messages}, 实际 {total_lines}"
    assert len(log_files) > 1, "应该发生轮转，但只有一个日志文件"
    print("✓ 测试通过: 轮转后日志一条不少")


def test_multi_process_with_rotation():
    """测试2.2: 多进程并发写日志触发多次轮转 → 验证所有文件总行数正确（最重要！）"""
    print("\n" + "="*70)
    print("测试2.2: 多进程并发写大量日志 - 触发多次轮转 (核心测试)")
    print("="*70)
    
    cleanup_logs()
    os.makedirs("logs", exist_ok=True)
    
    num_processes = 5
    num_messages_per_process = 1000
    expected_total = num_processes * num_messages_per_process
    
    print(f"\n启动 {num_processes} 个进程，每个写入 {num_messages_per_process} 条日志...")
    
    processes = []
    for i in range(num_processes):
        p = Process(target=write_logs_worker, 
                   args=(i, num_messages_per_process, "test2_2.log", 100*1024))  # 100KB
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
    
    time.sleep(1)
    
    print("\n日志文件统计:")
    total_lines = count_log_lines("logs", "test2_2.log*")
    
    print(f"\n预期日志条数: {expected_total} ({num_processes} 进程 × {num_messages_per_process} 条)")
    print(f"实际日志条数: {total_lines}")
    
    # 检查是否发生了轮转
    log_files = glob.glob("logs/test2_2.log*")
    print(f"\n生成的日志文件数: {len(log_files)}")
    for log_file in sorted(log_files):
        size = os.path.getsize(log_file)
        print(f"  {os.path.basename(log_file)}: {size:,} bytes")
    
    assert total_lines == expected_total, f"日志丢失! 预期 {expected_total}, 实际 {total_lines}"
    assert len(log_files) > 1, "应该发生轮转，但只有一个日志文件"
    print("✓ 测试通过: 多进程轮转后日志一条不少")


def test_extreme_concurrent_rotation():
    """测试2.3: 极端并发场景 - 10个进程同时写入触发频繁轮转"""
    print("\n" + "="*70)
    print("测试2.3: 极端并发场景 - 10进程高频轮转")
    print("="*70)
    
    cleanup_logs()
    os.makedirs("logs", exist_ok=True)
    
    num_processes = 10
    num_messages_per_process = 500
    expected_total = num_processes * num_messages_per_process
    
    print(f"\n启动 {num_processes} 个进程，每个写入 {num_messages_per_process} 条日志...")
    
    processes = []
    for i in range(num_processes):
        p = Process(target=write_logs_worker, 
                   args=(i, num_messages_per_process, "test2_3.log", 50*1024))  # 50KB 更小的文件
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
    
    time.sleep(1)
    
    print("\n日志文件统计:")
    total_lines = count_log_lines("logs", "test2_3.log*")
    
    print(f"\n预期日志条数: {expected_total} ({num_processes} 进程 × {num_messages_per_process} 条)")
    print(f"实际日志条数: {total_lines}")
    
    log_files = glob.glob("logs/test2_3.log*")
    print(f"\n生成的日志文件数: {len(log_files)}")
    
    assert total_lines == expected_total, f"日志丢失! 预期 {expected_total}, 实际 {total_lines}"
    print("✓ 测试通过: 极端并发下日志一条不少")


if __name__ == "__main__":
    try:
        # 测试1: 不发生轮转的场景
        test_single_process_no_rotation()
        test_multi_process_no_rotation()
        
        # 测试2: 发生轮转的场景（核心测试）
        test_single_process_with_rotation()
        test_multi_process_with_rotation()
        test_extreme_concurrent_rotation()
        
        print("\n" + "="*70)
        print("所有测试通过! ✓✓✓")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()