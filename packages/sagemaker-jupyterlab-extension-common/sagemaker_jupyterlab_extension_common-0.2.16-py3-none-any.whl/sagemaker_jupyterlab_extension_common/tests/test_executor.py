from unittest.mock import patch
import pytest
from sagemaker_jupyterlab_extension_common.executor import ProcessExecutorUtility


def dummy_func(x):
    return x


@patch("sagemaker_jupyterlab_extension_common.executor.ProcessPoolExecutor")
def test_executor_process_pool_should_reuse(executor):
    ProcessExecutorUtility.shutdown_executor()
    ProcessExecutorUtility.initialize_executor()
    ProcessExecutorUtility.initialize_executor()
    assert executor.call_count == 1
    ProcessExecutorUtility.shutdown_executor()


async def test_run_on_executor_should_throw_when_process_pool_does_not_initialized():
    dummy_func = lambda x: x
    with pytest.raises(
        ValueError, match="Executor not initialized. Call initialize_executor first"
    ):
        await ProcessExecutorUtility.run_on_executor(dummy_func)


async def test_run_on_executor_should_call_function_successfully():
    ProcessExecutorUtility.initialize_executor()

    result = await ProcessExecutorUtility.run_on_executor(dummy_func, 1)
    assert result == 1


async def test_shutdown_executor():
    ProcessExecutorUtility.initialize_executor()
    assert ProcessExecutorUtility._executor is not None
    ProcessExecutorUtility.shutdown_executor()
    assert ProcessExecutorUtility._executor is None
