import time
import datetime as dt
import os
import getpass
import glob
import logging
import portalocker
import atexit
import shutil
from pathlib import Path
from abc import ABC, abstractmethod

class MultiProcessSafeRotatingHandlerBase(logging.Handler, ABC):
    def __init__(self, filename, backupCount=3):
        super().__init__()
        self.filename = filename
        self.backupCount = backupCount

        # --- 修改策略：所有辅助文件（锁、临时文件）都放入一个隐藏子目录 ---
        
        # 1. 获取日志文件所在的绝对目录
        # 例如 filename = "logs/app.log" -> log_parent_dir = "/.../project/logs"
        self.log_parent_dir = os.path.dirname(os.path.abspath(filename))
        
        # 2. 定义“收纳”目录，使用 "." 开头通常表示隐藏或配置目录
        # 例如 "/.../project/logs/.logging_locks"
        self.aux_dir = os.path.join(self.log_parent_dir, ".logging_locks")
        
        # 3. 确保这个隐藏目录存在 (exist_ok=True 保证多进程并发创建时不报错)
        os.makedirs(self.aux_dir, exist_ok=True)

        # 4. 定义锁文件路径 (放入隐藏目录)
        # 例如 "/.../project/logs/.logging_locks/app.log.lock"
        self.lockfile = os.path.join(self.aux_dir, os.path.basename(filename) + ".lock")

        # 5. 定义临时文件路径 (也放入隐藏目录，进一步净化主目录)
        self.pid = os.getpid()
        self.user = getpass.getuser()
        # 例如 "/.../project/logs/.logging_locks/app.log.tmp.user.12345"
        self.tmp_file = os.path.join(self.aux_dir, f"{os.path.basename(filename)}.tmp.{self.user}.{self.pid}")
        
        atexit.register(self.close)

    def emit(self, record):
        try:
            msg = self.format(record) + '\n'
            
            # 策略：尝试在 0.2 秒内获取锁
            lock_fd = self._acquire_lock(timeout=0.2)
            
            if lock_fd:
                try:
                    self._flush_my_temp_to_main()
                    self._append_to_main(msg)
                    if self._should_rollover(record):
                        self.doRollover()
                finally:
                    os.close(lock_fd)
            else:
                self._write_to_tmp(msg)
                
        except Exception:
            self.handleError(record)

    def close(self):
        """Handler 关闭时的清理逻辑"""
        # 尝试合并最后的数据
        lock_fd = self._acquire_lock(timeout=2.0)
        if lock_fd:
            try:
                self._flush_my_temp_to_main()
            finally:
                os.close(lock_fd)
        
        # 尝试清理自己的锁文件 (尽力而为)
        self._try_clean_lockfile()
        super().close()

    def _try_clean_lockfile(self):
        """尝试删除锁文件，如果失败说明还有其他进程在用，忽略即可"""
        if os.path.exists(self.lockfile):
            try:
                os.remove(self.lockfile)
            except OSError:
                pass
        
        # 可选：如果目录空了，也可以尝试删除目录 (保持目录更干净)
        # try:
        #     os.rmdir(self.aux_dir)
        # except OSError:
        #     pass

    def _acquire_lock(self, timeout=0.5):
        """获取文件锁"""
        start_time = time.time()
        fd = None
        
        # 双重保险：虽然 init 里创建了目录，但防止运行时目录被意外删除
        if not os.path.exists(self.aux_dir):
            try:
                os.makedirs(self.aux_dir, exist_ok=True)
            except OSError:
                pass

        try:
            fd = os.open(self.lockfile, os.O_CREAT | os.O_WRONLY)
        except OSError:
            return None

        while True:
            try:
                portalocker.lock(fd, portalocker.LOCK_EX | portalocker.LOCK_NB)
                return fd 
            except (portalocker.LockException, BlockingIOError):
                pass

            if time.time() - start_time > timeout:
                os.close(fd)
                return None
            
            time.sleep(0.01)

    def _write_to_tmp(self, msg):
        try:
            # 这里的 self.tmp_file 已经在 .logging_locks 目录里了
            with open(self.tmp_file, 'a', encoding='utf-8') as f:
                f.write(msg)
        except Exception:
            pass

    def _flush_my_temp_to_main(self):
        if not os.path.exists(self.tmp_file):
            return

        try:
            with open(self.tmp_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content:
                self._append_to_main(content)
            
            # 也是尽力删除临时文件
            with open(self.tmp_file, 'w', encoding='utf-8') as f:
                pass
            try:
                os.remove(self.tmp_file)
            except OSError:
                pass
                
        except Exception:
            pass

    def _append_to_main(self, data):
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(data)
            f.flush()

    def doRollover(self):
        self._merge_all_temp_files() 
        self._do_rollover_impl()

    def _merge_all_temp_files(self):
        """
        合并 .logging_locks 目录下所有相关的临时文件
        """
        # 修改匹配模式，指向 aux_dir
        base_name = os.path.basename(self.filename)
        # 匹配模式 e.g.: /path/to/.logging_locks/app.log.tmp.*
        tmp_pattern = os.path.join(self.aux_dir, f"{base_name}.tmp.*")
        
        for tmp_path in glob.glob(tmp_pattern):
            if tmp_path == self.tmp_file: continue 

            try:
                merging_path = tmp_path + ".merging"
                os.rename(tmp_path, merging_path)
                
                with open(merging_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                
                if data:
                    self._append_to_main(data)
                
                os.remove(merging_path)
            except OSError:
                continue

    @abstractmethod
    def _should_rollover(self, record) -> bool: pass
    @abstractmethod
    def _do_rollover_impl(self): pass
    def _get_file_size(self, filepath):
        try: return os.path.getsize(filepath)
        except OSError: return 0

class MultiProcessSafeSizeRotatingHandler(MultiProcessSafeRotatingHandlerBase):
    def __init__(self, filename, maxBytes=5 * 1024 * 1024, backupCount=3):
        if isinstance(maxBytes, str):
            if maxBytes.upper().endswith('M'): maxBytes = int(float(maxBytes[:-1])*1024*1024)
            elif maxBytes.upper().endswith('K'): maxBytes = int(float(maxBytes[:-1])*1024)
            else: maxBytes = int(maxBytes)
            
        super().__init__(filename, backupCount)
        self.maxBytes = maxBytes

    def _should_rollover(self, record) -> bool:
        return self._get_file_size(self.filename) >= self.maxBytes

    def _do_rollover_impl(self):
        log_path = Path(self.filename)
        for i in range(self.backupCount - 1, 0, -1):
            sfn = log_path.with_suffix(f'.log.{i}')
            dfn = log_path.with_suffix(f'.log.{i+1}')
            if sfn.exists():
                try:
                    if dfn.exists(): dfn.unlink()
                    sfn.rename(dfn)
                except OSError: pass

        if log_path.exists():
            dfn = log_path.with_suffix('.log.1')
            try:
                if dfn.exists(): dfn.unlink()
                log_path.rename(dfn)
            except OSError: pass
        
        with open(self.filename, 'w') as f: pass

class MultiProcessSafeTimeRotatingHandler(MultiProcessSafeRotatingHandlerBase):
    """
    基于时间的日志轮转 Handler，支持多进程安全
    
    参数:
        filename: 日志文件路径
        when: 轮转时间单位
            'S' - 秒
            'M' - 分钟
            'H' - 小时
            'D' - 天
            'MIDNIGHT' - 每天午夜
        interval: 轮转间隔（配合 when 使用）
        backupCount: 保留的备份文件数量
    
    示例:
        # 每5秒轮转一次
        handler = MultiProcessSafeTimeRotatingHandler('app.log', when='S', interval=5)
        
        # 每天午夜轮转
        handler = MultiProcessSafeTimeRotatingHandler('app.log', when='MIDNIGHT')
        
        # 每2小时轮转
        handler = MultiProcessSafeTimeRotatingHandler('app.log', when='H', interval=2)
    """
    
    def __init__(self, filename, when='D', interval=1, backupCount=7):
        super().__init__(filename, backupCount)
        
        self.when = when.upper()
        self.interval = interval
        
        # 计算轮转间隔（秒）
        self.interval_seconds = self._calculate_interval_seconds()
        
        # 定义轮转时间戳文件路径（放在 .logging_locks 目录）
        # 用于多进程同步轮转时间点
        self.rollover_timestamp_file = os.path.join(
            self.aux_dir, 
            f"{os.path.basename(filename)}.next_rollover"
        )
        
        # 初始化下次轮转时间
        self.rollover_at = self._load_or_compute_rollover_time()
    
    def _calculate_interval_seconds(self):
        """根据 when 和 interval 计算轮转间隔秒数"""
        if self.when == 'S':
            return self.interval
        elif self.when == 'M':
            return self.interval * 60
        elif self.when == 'H':
            return self.interval * 3600
        elif self.when == 'D':
            return self.interval * 86400
        elif self.when == 'MIDNIGHT':
            return 86400  # 每天
        else:
            raise ValueError(f"Invalid when value: {self.when}")
    
    def _compute_rollover_time(self):
        """计算下次应该轮转的时间戳"""
        current_time = time.time()
        
        if self.when == 'MIDNIGHT':
            # 计算到下一个午夜的时间
            now = dt.datetime.now()
            next_midnight = dt.datetime(now.year, now.month, now.day) + dt.timedelta(days=1)
            return next_midnight.timestamp()
        else:
            # 对齐到时间间隔的整数倍
            # 例如：当前时间 10:23:45，interval=3600(1小时)
            # 对齐到 11:00:00
            return ((int(current_time) // self.interval_seconds) + 1) * self.interval_seconds
    
    def _load_or_compute_rollover_time(self):
        """
        从共享文件加载轮转时间，如果不存在或过期则重新计算
        
        这是多进程同步的关键：所有进程从同一个文件读取轮转时间点
        """
        try:
            if os.path.exists(self.rollover_timestamp_file):
                with open(self.rollover_timestamp_file, 'r') as f:
                    saved_time = float(f.read().strip())
                    
                # 如果保存的时间还在未来，就用它
                if saved_time > time.time():
                    return saved_time
                # 如果时间已过期，也返回它，让 _should_rollover 判断
                # 这样可以触发轮转
                return saved_time
        except (OSError, ValueError):
            pass
        
        # 否则计算新的轮转时间并保存
        new_rollover_at = self._compute_rollover_time()
        self._save_rollover_time(new_rollover_at)
        return new_rollover_at
    
    def _save_rollover_time(self, rollover_time):
        """保存轮转时间到文件，供所有进程共享"""
        try:
            os.makedirs(self.aux_dir, exist_ok=True)
            with open(self.rollover_timestamp_file, 'w') as f:
                f.write(str(rollover_time))
        except OSError:
            pass
    
    def _should_rollover(self, record) -> bool:
        """
        检查是否应该轮转
        
        关键改进：每次检查时重新加载轮转时间，确保多进程同步
        """
        current_time = time.time()
        
        # 重新加载轮转时间，防止其他进程已经更新了
        # 但不要每次都重新计算，要尊重已保存的轮转时间点
        saved_rollover = self._load_or_compute_rollover_time()
        
        # 如果当前时间超过了计划轮转时间，就该轮转了
        if current_time >= saved_rollover:
            # 更新实例变量，以便 doRollover 使用
            self.rollover_at = saved_rollover
            return True
        
        # 更新实例变量
        self.rollover_at = saved_rollover
        return False
    
    def _do_rollover_impl(self):
        """执行时间轮转"""
        log_path = Path(self.filename)
        
        # 生成带时间戳的备份文件名
        # 使用实际的当前时间作为时间戳，而不是 rollover_at
        # 这样更准确反映日志的实际生成时间
        current_time = dt.datetime.now()
        time_suffix = current_time.strftime('%Y-%m-%d_%H-%M-%S')
        
        # 如果有旧的备份文件，先删除最老的
        if self.backupCount > 0:
            # 找出所有备份文件并按时间排序
            backup_pattern = f"{log_path.stem}.log.*"
            try:
                backup_files = sorted(
                    [p for p in log_path.parent.glob(backup_pattern) if p.is_file()],
                    key=lambda p: p.stat().st_mtime if p.exists() else 0
                )
                
                # 删除超出数量的旧文件
                while len(backup_files) >= self.backupCount:
                    oldest = backup_files.pop(0)
                    try:
                        oldest.unlink()
                    except OSError:
                        pass
            except (OSError, ValueError):
                pass
        
        # 重命名当前日志文件为备份文件（无论文件大小，只要存在就轮转）
        if log_path.exists():
            backup_name = log_path.with_suffix(f'.log.{time_suffix}')
            try:
                if backup_name.exists():
                    backup_name.unlink()
                log_path.rename(backup_name)
            except OSError:
                pass
        
        # 创建新的空日志文件
        try:
            with open(self.filename, 'w') as f:
                pass
        except OSError:
            pass
        
        # 计算并保存下次轮转时间
        new_rollover_at = self._compute_rollover_time()
        self._save_rollover_time(new_rollover_at)
        self.rollover_at = new_rollover_at
    
    def doRollover(self):
        """执行轮转前先合并所有临时文件"""
        self._merge_all_temp_files()
        self._do_rollover_impl()

