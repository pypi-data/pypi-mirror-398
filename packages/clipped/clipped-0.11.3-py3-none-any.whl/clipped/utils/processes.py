import os
import signal

from polyaxon.logger import logger


def clean_process(pid: int) -> bool:
    try:
        logger.debug("Killing process with pid %s" % pid)
        try:
            if os.name == "nt":
                os.kill(pid, signal.CTRL_BREAK_EVENT)
            else:
                os.kill(pid, signal.SIGKILL)
            return True
        except Exception:
            # Windows process killing is flaky
            pass
    except Exception as e:
        logger.debug(e)
        return False
