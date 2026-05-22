from datetime import datetime
import asyncio
import os
from pathlib import Path

from astrbot.core.utils.astrbot_path import get_astrbot_data_path


class LogUtil:
    def __init__(self, log_enable: bool = True, log_path: str = ""):
        self.log_enable = log_enable
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            self.log_path = log_path
        else:
            plugin_data_path = Path(get_astrbot_data_path()) / "plugin_data" / "astrbot_plugin_auto_forward"
            os.makedirs(plugin_data_path, exist_ok=True)
            self.log_path = os.path.join(plugin_data_path, 'log.txt')


    # 写入日志
    async def log(self, log: str):
        if not self.log_enable:
            return
        line = f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  ' + log + '\n'
        await asyncio.to_thread(self._write, line)

    def _write(self, line: str):
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(line)


    # 写入警告日志
    async def warning(self, warning: str):
        await self.log("WARNING: " + warning)