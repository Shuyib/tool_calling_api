import asyncio
import pytest

@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    if "asyncio" in pyfuncitem.keywords:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(pyfuncitem.obj(**pyfuncitem.funcargs))
        loop.close()
        return True
