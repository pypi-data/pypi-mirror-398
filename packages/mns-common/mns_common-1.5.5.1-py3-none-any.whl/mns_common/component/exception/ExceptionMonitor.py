import threading
from functools import wraps
from typing import Optional, Callable

class ExceptionMonitor:
    """支持动态配置的异常监控器"""
    def __init__(
        self,
        threshold: int = 1000,
        alert_handler: Optional[Callable[[int, int], None]] = None,
        auto_reset: bool = True
    ):
        """
        :param threshold: 报警阈值，默认1000次
        :param alert_handler: 自定义报警函数，格式 func(current_count, threshold)
        :param auto_reset: 触发报警后是否自动重置计数器
        """
        self.counter = 0
        self._threshold = threshold
        self.alert_handler = alert_handler
        self.auto_reset = auto_reset
        self.lock = threading.Lock()

    @property
    def threshold(self) -> int:
        """当前报警阈值"""
        return self._threshold

    @threshold.setter
    def threshold(self, value: int):
        """动态设置报警阈值"""
        with self.lock:
            self._threshold = value

    def increment(self):
        """线程安全的计数器递增"""
        with self.lock:
            self.counter += 1
            if self.counter >= self.threshold:
                self.trigger_alert()
                if self.auto_reset:
                    self.reset_counter()

    def reset_counter(self):
        """手动重置计数器"""
        with self.lock:
            self.counter = 0

    def trigger_alert(self):
        """触发报警（支持自定义处理逻辑）"""
        if self.alert_handler:
            self.alert_handler(self.counter, self.threshold)
        else:
            print(f"[ALERT] Exception count {self.counter} exceeded threshold {self.threshold}")

def exception_counter(
    threshold: int = 1000,
    alert_handler: Optional[Callable[[int, int], None]] = None,
    auto_reset: bool = True
):
    """
    异常计数装饰器工厂
    :param threshold: 报警阈值
    :param alert_handler: 自定义报警处理函数
    :param auto_reset: 是否自动重置计数器
    """
    def decorator(func):
        # 为每个被装饰函数创建独立监控实例
        monitor = ExceptionMonitor(
            threshold=threshold,
            alert_handler=alert_handler,
            auto_reset=auto_reset
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                monitor.increment()
                raise  # 保持原始异常栈

        # 暴露监控器以便外部访问
        wrapper.monitor = monitor
        return wrapper
    return decorator