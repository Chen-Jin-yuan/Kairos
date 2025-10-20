import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time

from framework.watcher import Watcher


if __name__ == "__main__":
    watcher = Watcher(interval=2)
    watcher.start()
    
    try:
        time.sleep(61)
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
