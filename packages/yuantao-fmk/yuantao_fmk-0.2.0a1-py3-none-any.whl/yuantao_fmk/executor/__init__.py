# Copyright (C) 2025 Tao Yuan
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.
import re
import subprocess
from queue import Queue
from typing import List, Union

from yuantao_fmk import logger
from alive_progress import alive_bar
import time

from yuantao_fmk import Config


def execute_command(
    raw_command: Union[str, List[str]],
    error_checker=lambda s: bool(re.findall(r"error|failed", s, flags=re.IGNORECASE)),
):
    """用`subprocess.Popen`执行一个可执行程序, 并根据实际需要输出日志, 捕获错误信息"""
    if not isinstance(raw_command, List):
        raw_command = [raw_command]
    if Config.DRYRUN:
        logger.debug(f"Dryrun: Executing {' '.join(raw_command)}")
        return
    p = subprocess.Popen(
        raw_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if Config.VERBOSE:
        logger.debug(f"Executing {' '.join(raw_command)}")
        while (retcode_or_none := p.poll()) is None:
            line = p.stdout.readline().strip() if p.stdout else ""
            if error_checker(line):
                logger.error(line.strip())
            else:
                logger.debug(line.strip())
        if retcode_or_none == 0:
            logger.debug("Execute success")
        else:
            logger.error(f"Execute failed, retcode is {retcode_or_none}")
            logger.critical("Error happened, please check log.")
            exit(1)
    else:
        # 使用 alive-progress 替换 yaspin
        log_queue: Queue[str] = Queue(maxsize=5)
        command_str = " ".join(raw_command)

        # 创建一个不确定长度的进度条
        with alive_bar(
            None,
            title=f"Executing {command_str[:50]}..."
            if len(command_str) > 50
            else f"Executing {command_str}",
            force_tty=True,
        ) as bar:
            while (retcode_or_none := p.poll()) is None:
                bar()
                line = p.stdout.readline().strip() if p.stdout else ""
                if log_queue.full():
                    _ = log_queue.get_nowait()
                log_queue.put_nowait(line)
                if error_checker(line):
                    logger.error(
                        f"Error happened! Here is nearest {log_queue.qsize()} log lines:"
                    )
                    while log_queue.qsize() > 0:
                        q_line = log_queue.get_nowait()
                        logger.error(q_line.strip())
                # 更新进度条显示，保持活跃状态

                time.sleep(0.01)  # 小延迟避免过度占用CPU

            if retcode_or_none != 0:
                # 清除进度条，显示错误信息
                bar.title = "❌ Execution failed"
                logger.critical("Error happened, please check log.")
                exit(1)
            else:
                # 清除进度条，显示成功信息
                bar.title = "✅ Execution successful"
