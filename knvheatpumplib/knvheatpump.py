"""
Functions for interacting with KNV Home 
"""
import asyncio
from websockets.sync.client import connect

def login():
    """
    Login into the KNV heatpump and create the websocket
    """
    print("test")
