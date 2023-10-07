"""
Tests for knvheatpumplib
"""
from knvheatpumplib import knvheatpump

def test_login():
    """
    Test for KNV login
    """
    knvheatpump.login()
