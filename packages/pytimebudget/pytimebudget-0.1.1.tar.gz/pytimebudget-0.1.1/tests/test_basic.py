import time
from pytimebudget import pytimebudget

def test_sync():
    with pytimebudget("sync_test", max_ms=50):
        time.sleep(0.01)
