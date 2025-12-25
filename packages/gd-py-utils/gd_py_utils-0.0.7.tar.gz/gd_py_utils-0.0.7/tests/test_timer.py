import time
from gdutils.utils.timer import Timer


def test_timer_context():
    with Timer() as t:
        time.sleep(0.1)
    
    assert t.secs >= 0.1
    assert t.start_time > 0


def test_timer_reuse():
    t = Timer()
    with t:
        time.sleep(0.01)
    first_run = t.secs
    
    with t:
        time.sleep(0.01)
    second_run = t.secs
    
    assert first_run > 0
    assert second_run > 0

