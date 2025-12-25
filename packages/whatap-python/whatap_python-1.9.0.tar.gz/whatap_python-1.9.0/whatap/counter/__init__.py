from .counter_manager import CounterMgr  # CounterMgr 클래스 import
from whatap import preview_whatap_conf

counter_thread_enabled = preview_whatap_conf("counter_thread_enabled")

if counter_thread_enabled != 'false':
    mgr = CounterMgr()
    mgr.setDaemon(True)
    mgr.start()