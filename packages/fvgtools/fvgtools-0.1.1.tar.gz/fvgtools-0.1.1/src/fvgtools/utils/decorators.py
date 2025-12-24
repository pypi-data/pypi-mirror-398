import functools
import time

__all__ = ['retry', 'timer']

def retry(times: int):
    """
    重试装饰器，在函数执行失败时自动重试指定次数。
    
    参数:
        times (int): 最大重试次数
    
    返回:
        function: 装饰后的函数
        
    示例:
        >>> @retry(times=3)
        >>> def may_fail_function():
        >>>     # 可能会失败的函数
        >>>     pass
    
    注意:
        - 如果所有重试都失败，将抛出最后一次的异常
        - 重试会立即进行，没有延迟
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    raise e
        return wrapper
    return decorator

def timer(func):
    """
    计时装饰器，用于测量函数的执行时间。
    
    参数:
        func (function): 要测量执行时间的函数
    
    返回:
        function: 装饰后的函数
        
    示例:
        >>> @timer
        >>> def slow_function():
        >>>     time.sleep(1)
        >>> 
        >>> slow_function()  # 输出: "函数 slow_function 执行时间: 1.000000 秒"
    
    注意:
        - 执行时间的输出精度为6位小数
        - 输出包含函数名和执行时间
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"函数 {func.__name__} 执行时间: {end_time - start_time:.6f} 秒")
        return result
    return wrapper 