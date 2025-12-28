import asyncio
import logging
import time
from datetime import datetime

import pytest

from logis.util.io_util import AsyncWriteBuffer, SyncWriteBuffer, WriteBufferConfig

logging.getLogger().setLevel(logging.DEBUG)


def test_sync_write_buffer():
    config = WriteBufferConfig(
        batch_size=2,
        flush_interval=1,
        handler=lambda items: logging.debug(f"{datetime.now()}处理 {items}"),
    )
    buffer = SyncWriteBuffer(config)
    buffer.start()

    for i in range(5):
        buffer.put(datetime.now())
        time.sleep(0.5)

    buffer.stop()


@pytest.mark.asyncio
async def test_async_write_buffer():
    config = WriteBufferConfig(
        batch_size=2,
        flush_interval=1,
        handler=lambda items: print(f"处理 {items}"),
    )
    buffer = AsyncWriteBuffer(config)

    asyncio.create_task(buffer.start())

    for i in range(5):
        await buffer.put(datetime.now())
        await asyncio.sleep(0.5)

    await buffer.stop()
