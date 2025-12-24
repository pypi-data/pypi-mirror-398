from concurrent.futures import ProcessPoolExecutor
import asyncio
import functools
from typing import Optional


class ProcessExecutorUtility:
    _executor: Optional[ProcessPoolExecutor] = None

    @classmethod
    def initialize_executor(cls, max_workers=4):
        if cls._executor is None:
            cls._executor = ProcessPoolExecutor(max_workers=max_workers)

    @classmethod
    async def run_on_executor(cls, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        if cls._executor is None:
            raise ValueError(
                "Executor not initialized. Call initialize_executor first."
            )

        result = await loop.run_in_executor(
            cls._executor, functools.partial(func, *args, **kwargs)
        )
        return result

    @classmethod
    def shutdown_executor(cls):
        if cls._executor is not None:
            cls._executor.shutdown()
            cls._executor = None
        return
