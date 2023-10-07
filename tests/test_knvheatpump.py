"""
Tests for knvheatpumplib
"""

# pylint: disable=no-member
# pylint: disable=too-many-function-args

import asyncio
from knvheatpumplib import knvheatpump


def test_get_data():
    """
    Test for KNV login
    """
    assert asyncio.run(knvheatpump.get_data(
        "192.168.0.17", "test", "test")), "Data Retrieval failed"
