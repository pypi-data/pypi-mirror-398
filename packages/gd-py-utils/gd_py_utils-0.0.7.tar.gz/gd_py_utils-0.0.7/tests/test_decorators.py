from gdutils.utils.decorators import timer, debug
import time


def test_timer_decorator(capsys):
    @timer
    def sleep_func(seconds):
        time.sleep(seconds)
        return "done"
    
    result = sleep_func(0.1)
    
    assert result == "done"
    captured = capsys.readouterr()
    assert "Finished 'sleep_func' in" in captured.out
    assert "secs" in captured.out


def test_timer_decorator_long_duration(capsys, monkeypatch):
    # Mock time to simulate long duration
    # We need to mock time.perf_counter
    
    class MockTime:
        def __init__(self):
            self.calls = 0
            
        def perf_counter(self):
            self.calls += 1
            if self.calls == 1:
                return 0.0
            return 125.0  # 2 min 5 secs
            
    mock_time = MockTime()
    monkeypatch.setattr(time, "perf_counter", mock_time.perf_counter)
    
    @timer
    def long_func():
        pass
        
    long_func()
    
    captured = capsys.readouterr()
    assert "2 min 5.0000 secs" in captured.out


def test_debug_decorator(capsys):
    @debug
    def add(a, b=1):
        return a + b
    
    result = add(2, b=3)
    
    assert result == 5
    captured = capsys.readouterr()
    assert "Calling add(2, b=3)" in captured.out
    assert "'add' returned 5" in captured.out

