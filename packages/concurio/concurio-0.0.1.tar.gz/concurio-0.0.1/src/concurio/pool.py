import os
import sys
import logging
import asyncio as a
from dataclasses import dataclass
from typing import Optional, List, Callable, Awaitable, TypeVar

from tqdm.asyncio import tqdm_asyncio

from .task import AsyncTask, TimeoutedTask, RateLimiter

T = TypeVar('T')

@dataclass
class TqdmConfig:
  desc: str = "Processing tasks"
  total: Optional[int] = None
  disable: bool = False

class AsyncPoolExecutor:
  def __init__(
    self, 
    concurrency: Optional[int] = None,
    max_executions_per_minute: Optional[int] = None
  ) -> 'AsyncPoolExecutor':
    self._concurrency = concurrency or os.cpu_count() or 1
    self._sem = a.Semaphore(self._concurrency)
    self._coroutines: List[Awaitable[T]] = []
    self._rate_limiter = RateLimiter(
      max_executions_per_minute, 
      60.0
    ) if max_executions_per_minute is not None else None

  @property
  def concurrency(self) -> int:
    return self._concurrency

  def count(self) -> int:
    return len(self._coroutines)

  def submit(
    self, 
    func: Callable[..., Awaitable[T]], 
    *args, 
    wait_timeout: Optional[float] = None, 
    **kwargs
  ) -> Awaitable[T]:
    task = AsyncTask(self._sem, func, wait_timeout, self._rate_limiter)
    coro = task.run(*args, **kwargs)
    self._coroutines.append(coro)
    return coro

  def as_events(
    self, 
    on_done: Callable[[T], None], 
    on_error: Callable[[Exception], None], 
    on_timeout: Callable[[TimeoutedTask], None],
    timeout: Optional[float] = None,
    tqdm_config: Optional[TqdmConfig] = None
  ) -> None:
    logger = logging.getLogger(__name__)
    
    async def logic():
      tasks = [a.create_task(c) for c in self._coroutines]
      if tqdm_config is None or tqdm_config.disable:
        completed = a.as_completed(tasks, timeout=timeout)
        for coro in completed:
          try:
            res = await coro
            if isinstance(res, TimeoutedTask):
              on_timeout(res)
            else:
              on_done(res)
          except Exception as e:
            on_error(e)
      else:
        desc = tqdm_config.desc
        total = tqdm_config.total or len(tasks)
        is_tty = sys.stdout.isatty()
        if is_tty:
          completed = tqdm_asyncio.as_completed(
            tasks, 
            timeout=timeout, 
            desc=desc, 
            total=total
          )
        else:
          completed = a.as_completed(tasks, timeout=timeout)
        done = 0
        log_interval = max(1, total // 200) # Log every 0.5%
        for coro in completed:
          try:
            res = await coro
            if isinstance(res, TimeoutedTask):
              on_timeout(res)
            else:
              on_done(res)
          except Exception as e:
            on_error(e)

          done += 1
          if not is_tty:
            if done % log_interval == 0 or done == total:
              percent = (done / total) * 100
              logger.info(f"{desc}: {done}/{total} ({percent:.1f}%) completed")
    
    a.run(logic())

  async def async_as_events(
    self, 
    on_done: Callable[[T], None], 
    on_error: Callable[[Exception], None], 
    on_timeout: Callable[[TimeoutedTask], None],
    timeout: Optional[float] = None,
    tqdm_config: Optional[TqdmConfig] = None
  ) -> None:
    logger = logging.getLogger(__name__)
    
    async def logic():
      tasks = [a.create_task(c) for c in self._coroutines]
      if tqdm_config is None or tqdm_config.disable:
        completed = a.as_completed(tasks, timeout=timeout)
        for coro in completed:
          try:
            res = await coro
            if isinstance(res, TimeoutedTask):
              on_timeout(res)
            else:
              on_done(res)
          except Exception as e:
            on_error(e)
      else:
        desc = tqdm_config.desc
        total = tqdm_config.total or len(tasks)
        is_tty = sys.stdout.isatty()
        if is_tty:
          completed = tqdm_asyncio.as_completed(
            tasks, 
            timeout=timeout, 
            desc=desc, 
            total=total
          )
        else:
          completed = a.as_completed(tasks, timeout=timeout)
        done = 0
        log_interval = max(1, total // 200) # Log every 0.5%
        for coro in completed:
          try:
            res = await coro
            if isinstance(res, TimeoutedTask):
              on_timeout(res)
            else:
              on_done(res)
          except Exception as e:
            on_error(e)
   
          done += 1
          if not is_tty:
            if done % log_interval == 0 or done == total:
              percent = (done / total) * 100
              logger.info(f"{desc}: {done}/{total} ({percent:.1f}%) completed")
    
    await logic()

  def __enter__(self) -> 'AsyncPoolExecutor':
    return self
  
  def __exit__(self, _, __, ___) -> None:
    self._coroutines = []

  def __len__(self) -> int:
    return len(self._coroutines)