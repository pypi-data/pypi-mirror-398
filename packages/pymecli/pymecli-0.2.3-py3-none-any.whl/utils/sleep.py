import time
from datetime import datetime, timedelta


def interruptible_sleep(seconds: float) -> bool:
    """
    可中断的休眠函数
    :param seconds: 休眠秒数
    """
    end_time = datetime.now() + timedelta(seconds=seconds)
    try:
        while datetime.now() < end_time:
            time.sleep(1)  # 每1秒检查一次，便于中断
    except KeyboardInterrupt:
        return False
    return True
