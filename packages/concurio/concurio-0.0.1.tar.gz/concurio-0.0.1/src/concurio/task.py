import asyncio as a
from collections import deque
from dataclasses import dataclass

from typing import Optional, Any, Union, Callable, Awaitable, TypeVar


T = TypeVar('T')

@dataclass
class TimeoutedTask:
  func_name: str
  timeout: float
  args: tuple
  kwargs: dict

class RateLimiter:
  def __init__(self, max_calls: int, period: float) -> 'RateLimiter':
    self.max_calls = max_calls
    self.period = period
    self.calls: deque[float] = deque()
    self.lock = a.Lock()

  async def acquire(self) -> None:
    async with self.lock:
      now = a.get_running_loop().time()
      while self.calls and self.calls[0] <= now - self.period:
        self.calls.popleft()

      if len(self.calls) >= self.max_calls:
        wait_time = self.calls[0] + self.period - now
        if wait_time > 0:
          await a.sleep(wait_time)
        
        now = a.get_running_loop().time()
        while self.calls and self.calls[0] <= now - self.period:
          self.calls.popleft()
      
      self.calls.append(now)

async def _async_run(
  sem: a.Semaphore, 
  func: Callable[..., Awaitable[T]], 
  timeout: Optional[float], 
  rate_limiter: Optional[RateLimiter],
  *args, 
  **kwargs
) -> Union[Any, TimeoutedTask]:
  if rate_limiter is not None:
    await rate_limiter.acquire()
  await sem.acquire()
  try:
    try:
      result = await a.wait_for(func(*args, **kwargs), timeout)
      return result
    except a.TimeoutError:
      return TimeoutedTask(
        func_name=func.__name__, 
        timeout=timeout, 
        args=args, 
        kwargs=kwargs
      )
  finally:
    sem.release()

class AsyncTask:
  def __init__(
    self, 
    sem: a.Semaphore,
    func: Callable[..., Awaitable[T]], 
    timeout: Optional[float] = None,
    rate_limiter: Optional[RateLimiter] = None
  ) -> 'AsyncTask':
    self.sem = sem
    self.func = func
    self.timeout = timeout
    self.rate_limiter = rate_limiter

  def run(self, *args, **kwargs) -> Awaitable[T]:
    return _async_run(
      self.sem, 
      self.func, 
      self.timeout, 
      self.rate_limiter, 
      *args, 
      **kwargs
    )

  def __call__(self, *args, **kwargs) -> Awaitable[T]:
    return self.run(*args, **kwargs)