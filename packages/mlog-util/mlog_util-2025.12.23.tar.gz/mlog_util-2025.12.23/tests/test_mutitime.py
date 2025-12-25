import os
import time
import glob
from datetime import datetime
from multiprocessing import Process
from src.mlog_util import MultiProcessSafeTimeRotatingHandler, get_logger


def count_log_lines(log_dir, log_pattern="time.log*"):
    """统计所有日志文件的总行数（顺便吐槽一下文件数量）"""
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


def write_logs_with_sleep(process_id, num_messages=100, log_name="time.log", 
                          when='S', interval=2, sleep_between=0.1):
    """慢慢写日志，给轮转时间表演"""
    handler = MultiProcessSafeTimeRotatingHandler(
        filename=f"logs/{log_name}",
        when=when,
        interval=interval,
        backupCount=10
    )
    logger = get_logger(f"time_test_{process_id}", custom_handlers=handler, add_console=False)
    
    for i in range(num_messages):
        logger.info(f"进程{process_id}的第{i}条日志 - 时间飞逝，日志常在")
        time.sleep(sleep_between)  # 慢慢来，不着急
    
    handler.close()


def cleanup_logs(log_dir="logs", log_pattern="*.log*"):
    """清理战场"""
    log_files = glob.glob(os.path.join(log_dir, log_pattern))
    for log_file in log_files:
        try:
            os.remove(log_file)
        except Exception as e:
            print(f"Failed to remove {log_file}: {e}")


def test_no_rotation_yet():
    """测试1: 写几条日志，时间还没到 → 应该只有一个文件在偷笑"""
    print("\n" + "="*70)
    print("测试1: 时间轮转 - 还没到点，别着急")
    print("="*70)
    
    cleanup_logs()
    os.makedirs("logs", exist_ok=True)
    
    num_messages = 50
    # 设置10秒轮转一次，但我们只写3秒
    handler = MultiProcessSafeTimeRotatingHandler(
        filename="logs/test1.log",
        when='S',
        interval=10,
        backupCount=5
    )
    logger = get_logger("test1", custom_handlers=handler, add_console=False)
    
    print(f"\n开始写{num_messages}条日志，写完只需要2.5秒...")
    for i in range(num_messages):
        logger.info(f"第{i}条: 时光荏苒，岁月如梭")
        time.sleep(0.05)
    
    handler.close()
    time.sleep(0.5)
    
    print("\n日志文件统计:")
    total_lines = count_log_lines("logs", "test1.log*")
    log_files = glob.glob("logs/test1.log*")
    
    print(f"\n预期日志条数: {num_messages}")
    print(f"实际日志条数: {total_lines}")
    print(f"文件数量: {len(log_files)} (应该就1个)")
    
    assert total_lines == num_messages, f"日志丢了! 预期{num_messages}, 实际{total_lines}"
    assert len(log_files) == 1, f"不该轮转的! 应该1个文件，实际{len(log_files)}个"
    print("✓ 测试通过: 时间未到，文件独美")


def test_single_rotation():
    """测试2: 写日志跨越一个时间边界 → 应该产生2个文件"""
    print("\n" + "="*70)
    print("测试2: 单进程慢慢写 - 等待时间轮转的到来")
    print("="*70)
    
    cleanup_logs()
    os.makedirs("logs", exist_ok=True)
    
    num_messages = 60
    # 每2秒轮转一次，写60条，每条等0.1秒 = 6秒 → 应该轮转3次
    handler = MultiProcessSafeTimeRotatingHandler(
        filename="logs/test2.log",
        when='S',
        interval=2,
        backupCount=10
    )
    logger = get_logger("test2", custom_handlers=handler, add_console=False)
    
    print(f"\n开始写{num_messages}条日志，每2秒应该轮转一次...")
    start_time = datetime.now()
    
    for i in range(num_messages):
        logger.info(f"第{i}条: 两秒一轮转，人生多美满")
        time.sleep(0.1)
    
    end_time = datetime.now()
    handler.close()
    time.sleep(0.5)
    
    print("\n日志文件统计:")
    total_lines = count_log_lines("logs", "test2.log*")
    log_files = sorted(glob.glob("logs/test2.log*"))
    
    elapsed = (end_time - start_time).total_seconds()
    expected_rotations = int(elapsed / 2) + 1  # 第一个文件 + 轮转次数
    
    print(f"\n耗时: {elapsed:.1f}秒")
    print(f"预期日志条数: {num_messages}")
    print(f"实际日志条数: {total_lines}")
    print(f"预期文件数: ~{expected_rotations}个")
    print(f"实际文件数: {len(log_files)}个")
    
    assert total_lines == num_messages, f"日志丢了! 预期{num_messages}, 实际{total_lines}"
    assert len(log_files) >= 2, f"应该轮转的! 至少2个文件，实际{len(log_files)}个"
    print("✓ 测试通过: 时光流转，文件安好")


def test_multi_process_rotation():
    """测试3: 多进程同时写，时间轮转 → 大戏开场"""
    print("\n" + "="*70)
    print("测试3: 多进程并发 - 时间轮转大乱斗")
    print("="*70)
    
    cleanup_logs()
    os.makedirs("logs", exist_ok=True)
    
    num_processes = 5
    num_messages_per_process = 40
    expected_total = num_processes * num_messages_per_process
    
    print(f"\n启动{num_processes}个进程，每个写{num_messages_per_process}条日志...")
    print("每2秒轮转一次，每条日志间隔0.1秒，让我们看看会发生什么...")
    
    processes = []
    start_time = datetime.now()
    
    for i in range(num_processes):
        p = Process(target=write_logs_with_sleep, 
                   args=(i, num_messages_per_process, "test3.log", 'S', 2, 0.1))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
    
    end_time = datetime.now()
    time.sleep(1)
    
    print("\n日志文件统计:")
    total_lines = count_log_lines("logs", "test3.log*")
    log_files = sorted(glob.glob("logs/test3.log*"))
    
    elapsed = (end_time - start_time).total_seconds()
    
    print(f"\n耗时: {elapsed:.1f}秒")
    print(f"预期日志条数: {expected_total} ({num_processes}进程 × {num_messages_per_process}条)")
    print(f"实际日志条数: {total_lines}")
    print(f"生成文件数: {len(log_files)}个")
    
    for log_file in log_files:
        size = os.path.getsize(log_file)
        print(f"  {os.path.basename(log_file)}: {size:,} bytes")
    
    assert total_lines == expected_total, f"日志丢了! 预期{expected_total}, 实际{total_lines}"
    assert len(log_files) >= 2, f"这么久了应该轮转了! 至少2个文件，实际{len(log_files)}个"
    print("✓ 测试通过: 多进程时间轮转，一条不少")


def test_rapid_rotation():
    """测试4: 极端测试 - 1秒轮转，10个进程疯狂写入"""
    print("\n" + "="*70)
    print("测试4: 极限挑战 - 1秒轮转，看谁撑得住")
    print("="*70)
    
    cleanup_logs()
    os.makedirs("logs", exist_ok=True)
    
    num_processes = 10
    num_messages_per_process = 30
    expected_total = num_processes * num_messages_per_process
    
    print(f"\n{num_processes}个进程，每秒轮转一次，请系好安全带...")
    
    processes = []
    start_time = datetime.now()
    
    for i in range(num_processes):
        p = Process(target=write_logs_with_sleep, 
                   args=(i, num_messages_per_process, "test4.log", 'S', 1, 0.1))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
    
    end_time = datetime.now()
    time.sleep(1)
    
    print("\n日志文件统计:")
    total_lines = count_log_lines("logs", "test4.log*")
    log_files = sorted(glob.glob("logs/test4.log*"))
    
    elapsed = (end_time - start_time).total_seconds()
    
    print(f"\n耗时: {elapsed:.1f}秒")
    print(f"预期日志条数: {expected_total} ({num_processes}进程 × {num_messages_per_process}条)")
    print(f"实际日志条数: {total_lines}")
    print(f"生成文件数: {len(log_files)}个 (估计有{int(elapsed)}个左右)")
    
    assert total_lines == expected_total, f"极限挑战失败! 预期{expected_total}, 实际{total_lines}"
    print("✓ 测试通过: 极限轮转，无一遗漏")


if __name__ == "__main__":
    try:
        print("\n🕐 时间轮转测试套餐 - 准备开始营业 🕐")
        
        test_no_rotation_yet()
        test_single_rotation()
        test_multi_process_rotation()
        test_rapid_rotation()
        
        print("\n" + "="*70)
        print("🎉 所有测试通过! 时间在流逝，日志永不丢! 🎉")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n💥 测试爆炸: {e}")
    except Exception as e:
        print(f"\n💣 测试出错: {e}")
        import traceback
        traceback.print_exc()