import logging
import time
from pathlib import Path
from typing import List, Optional, Union

import psutil
from ipa.decorator import deprecated


def get_disk_usage(path: Union[str, Path], follow_symlink: bool = True):
    """
    获取指定路径的磁盘使用情况。

    TODO: 增加缓存；迭代效率

    Args:
        path (Union[str, Path]): 要获取磁盘使用情况的路径。
        follow_symlink (bool, optional): 是否跟随符号链接。默认值为 True。

    Returns:
        int: 路径占用的磁盘空间大小（字节）。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"path {path} not exists")

    if path.is_symlink() and follow_symlink:
        path = path.resolve()
    if path.is_file():
        byte_size = path.stat().st_size
    elif path.is_dir():
        byte_size = sum(get_disk_usage(f, follow_symlink) for f in path.glob("**/*"))
    else:
        raise ValueError(f"path {path} is not a file or dir")
    return byte_size


@deprecated("请使用 find_all_process_on_port 替代")
def find_process_on_port(port: int):
    """
    查找占用指定端口的进程，如果有多个只返回第一个。
    """
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        if not proc.pid:
            continue
        connections = proc.net_connections(kind="inet")
        for conn in connections:
            if not conn.laddr:
                continue
            if conn.laddr.port == int(port):
                return proc
    return None


@deprecated("请使用 kill_all_process_on_port 替代")
def kill_process_on_port(port, max_try: Optional[int] = 1) -> Optional[int]:
    """
    强制释放占用指定端口的进程，如果有多个进程只处理第一个。

    Args:
        port (int): 要释放的端口号
        max_try (int, optional): 最大尝试次数。值为 None，代表无限次尝试。

    Returns:
        int | None: 成功释放进程的 PID，如果不存在对应进程则返回 None。
    """
    pid: Optional[int] = None
    try_count = 0
    while max_try is None or try_count < max_try:
        p = find_process_on_port(port)
        if not p or not p.pid:
            return pid
        pid = p.pid
        try:
            p.kill()
            logging.info("process on port %s been killed: %s", port, pid)
            return pid
        except Exception as e:
            try_count += 1
            logging.warning(
                "kill process on port %s failed(x%s): %s", port, try_count, e
            )
    raise RuntimeError(f"kill process on port {port} failed after {try_count} times")


def find_all_process_on_port(port: int) -> List[psutil.Process]:
    """
    查找占用指定端口的所有进程。
    """
    procs = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        if not proc.pid:
            continue
        connections = proc.net_connections(kind="inet")
        for conn in connections:
            if not conn.laddr:
                continue
            if conn.laddr.port == int(port):
                procs.append(proc)
    return procs


def wait_port_idle(
    port: int, check_interval: float = 1.0, timeout: Optional[float] = None
):
    """
    等待指定端口空闲，即没有进程占用该端口。

    Args:
        port (int): 要等待的端口号
        check_interval (float, optional): 检查间隔，单位为秒。默认值为 1.0 秒。
        timeout (float, optional): 最大等待时间，单位为秒。默认值为 None，代表无限等待。

    Returns:
        bool: 如果端口空闲则返回 True，否则返回 False。
    """
    start = time.time()
    while True:
        if timeout is not None and time.time() - start > timeout:
            return False
        ps = find_all_process_on_port(port)
        if not ps:
            return True
        logging.info("there are %s process on port %s: %s", len(ps), port, ps)
        time.sleep(check_interval)


def kill_all_process_on_port(port, max_try: Optional[int] = 1) -> Optional[int]:
    """
    强制释放占用指定端口的所有进程。

    Args:
        port (int): 要释放的端口号
        max_try (int, optional): 最大尝试次数。值为 None，代表无限次尝试。

    Returns:
        int | None: 成功释放进程的 PID，如果不存在对应进程则返回 None。
    """

    def _kill(p: psutil.Process):
        pid: Optional[int] = None
        try_count = 0
        while max_try is None or try_count < max_try:
            if not p or not p.pid:
                return pid
            pid = p.pid
            try:
                p.kill()
                logging.info("process on port %s been killed: %s", port, pid)
                return pid
            except Exception as e:
                try_count += 1
                logging.warning(
                    "kill process on port %s failed(x%s): %s", port, try_count, e
                )
        raise RuntimeError(
            f"kill process on port {port} failed after {try_count} times"
        )

    ps = find_all_process_on_port(port)
    for p in ps:
        _kill(p)


def ensure_path(path: Union[str, Path]):
    return Path(path)
    # return path if isinstance(path, Path) else Path(path)
