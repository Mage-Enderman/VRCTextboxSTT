import logging
import os
import traceback
from datetime import datetime
import shutil
import psutil
from glob import glob
import sys

log = logging.getLogger(__name__)

class LogToFile(object):
    def __init__(self, cache_path):
        logfile = os.path.join(cache_path, 'latest.log')
        process_cache(cache_path, logfile)

        self.logger = log
        self.level = logging.DEBUG
        self.linebuf = ''
        self.ui_output = None
        self._in_write = False

        logging.basicConfig(
            level=self.level,
            format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
            filename=logfile,
            filemode='a'
        )

    def write(self, buf):
        if self._in_write:
            return
        self._in_write = True
        try:
            for line in buf.rstrip().splitlines():
                if not line.strip():
                    continue
                self.logger.log(self.level, line.rstrip())
                if self.ui_output:
                    try:
                        self.ui_output(line.rstrip())
                    except Exception:
                        pass
        finally:
            self._in_write = False

    def flush(self):
        pass

    def set_ui_output(self, output_method):
        self.ui_output = output_method
    
    def remove_ui_output(self):
        self.ui_output = None

def process_cache(cache_path, latest_log):
    try:
        os.makedirs(cache_path, exist_ok=True)
    except Exception:
        log.fatal("Failed to create cache directory: ")
        log.error(traceback.format_exc())

    try:
        logs = glob(os.path.join(cache_path, "*.log"))
        if len(logs) >= 5:
            logs.sort(key=os.path.getmtime)
            for log in logs[:-5]:
                os.remove(log)

        if os.path.isfile(latest_log):
            shutil.copy(latest_log, os.path.join(cache_path, datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")))
    except Exception:
        logging.error("Error processing old logs:")
        log.error(traceback.format_exc())

    open(latest_log, 'w').close()


def get_absolute_path(relative_path, script_path=__file__) -> str:
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(script_path)))
    path = os.path.normpath(os.path.join(base_path, relative_path))
    if (relative_path.endswith('/') or relative_path.endswith('\\')) and not path.endswith(os.sep):
        path += os.sep
    return path


def force_single_instance():
    """Force single instance by killing other instances of the same Name."""

    try:
        _pid = os.getpid()
        _procname = psutil.Process(_pid).name()

        for proc in psutil.process_iter():
            if proc.name() == _procname and proc.pid != _pid:
                proc.kill()
    except Exception:
        pass
