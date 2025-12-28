import pytest
import asyncio
import pytest_asyncio

from twilight_vk.utils.event_loop import TwiTaskManager

@pytest_asyncio.fixture
def loop(_function_event_loop):
    wrapper = TwiTaskManager(loop = _function_event_loop)
    yield wrapper

@pytest.fixture
def log_fixture(caplog):
    caplog.set_level(0)
    return caplog

async def fake_coro1(wrapper: TwiTaskManager):
    wrapper.logger.info("Hello")

async def fake_coro2(wrapper: TwiTaskManager):
    wrapper.logger.info("World")

async def fake_coro3():
    await asyncio.sleep(5)

async def fake_coro4(wrapper: TwiTaskManager):
    wrapper.logger.info("Test1")

async def fake_coro5(wrapper: TwiTaskManager):
    wrapper.logger.info("Test2")\
    
async def fake_coro6():
    await asyncio.sleep(5)

def test_wrapper_run(loop: TwiTaskManager, log_fixture):
    loop.add_task(fake_coro1(loop))
    loop.run()
    assert "Hello" in log_fixture.text

@pytest.mark.asyncio
async def test_wrapper_addtask(loop: TwiTaskManager, log_fixture):
    loop.add_task(fake_coro2(loop))
    await asyncio.sleep(0.1)
    assert "World" in log_fixture.text

@pytest.mark.asyncio
async def test_wrapper_addtask_list(loop: TwiTaskManager, log_fixture):
    loop.add_task([fake_coro4(loop), fake_coro5(loop)])
    await asyncio.sleep(0.1)
    assert "Test1" in log_fixture.text
    assert "Test2" in log_fixture.text

def test_wrapper_stop(loop: TwiTaskManager, log_fixture):
    loop.add_task(fake_coro3())
    loop.stop()
    assert "Stopping all tasks..." in log_fixture.text
    assert "Tasks was stopped" in log_fixture.text