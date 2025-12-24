#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------
# 进程锁
# -------------------------------

import os
from pathlib import Path
import psutil

LOCK_FILE = Path("./locker.dat")
CHATSET = "utf-8"


def _read_lock():
    try:
        text = LOCK_FILE.read_text(encoding=CHATSET).strip()
        if not text:
            return None
        parts = [p.strip() for p in text.split(",")]
        pid = int(parts[0])
        ctime = float(parts[1]) if len(parts) > 1 else None
        return pid, ctime
    except (OSError, ValueError):
        return None


def islocked():
    info = _read_lock()
    if not info:
        try:
            LOCK_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        return False

    pid, ctime = info
    try:
        p = psutil.Process(pid)
        if not p.is_running():
            raise psutil.NoSuchProcess(pid)

        # 防 PID 复用：比对创建时间（允许一点浮动）
        if ctime is not None and abs(p.create_time() - ctime) > 1.0:
            return False

        return True

    except psutil.NoSuchProcess:
        try:
            LOCK_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        return False

    except psutil.AccessDenied:
        # 权限不足时别删锁，按“进程存在”处理
        return True


def lock():
    pid = os.getpid()
    ctime = psutil.Process(pid).create_time()

    # 原子创建：避免并发同时写入
    try:
        with open(LOCK_FILE, "x", encoding=CHATSET) as f:
            f.write(f"{pid},{ctime}")
        return True
    except FileExistsError:
        # 已存在：如果是陈旧锁就清掉再尝试一次
        if not islocked():
            try:
                LOCK_FILE.unlink(missing_ok=True)
            except OSError:
                return False
            try:
                with open(LOCK_FILE, "x", encoding=CHATSET) as f:
                    f.write(f"{pid},{ctime}")
                return True
            except OSError:
                return False
        return False
    except OSError:
        # Permission denied or other OS errors
        return False


def unlock():
    info = _read_lock()
    if not info:
        return
    pid, _ = info
    if pid == os.getpid():
        try:
            LOCK_FILE.unlink(missing_ok=True)
        except OSError:
            pass
