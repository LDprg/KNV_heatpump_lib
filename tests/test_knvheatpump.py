"""
Tests for knvheatpumplib
"""

# pylint: disable=no-member
# pylint: disable=too-many-function-args

import logging

import asyncio
import pytest

from async_timeout import timeout

from knvheatpumplib import knvheatpump

logger = logging.getLogger()


def test_poll_get_data():
    """
    Test for KNV login
    """
    assert asyncio.run(knvheatpump.get_data(
        "192.168.0.17", "expert", "expert")), "Data Retrieval failed"


@pytest.mark.skip
async def callback(value):
    logger.debug("%s - %s", value["path"], value)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_push_get_data():
    """
    Test for KNV login
    """
    socket = knvheatpump.Socket()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(await socket.create("192.168.0.17", "expert", "expert", callback))
