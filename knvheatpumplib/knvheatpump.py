"""
Functions for interacting with KNV Home 
"""

# pylint: disable=no-member

import asyncio
import logging
import websockets

from async_timeout import timeout
from knvheatpumplib import knvparser

logger = logging.getLogger()


async def get_data(ip, username, password):
    """
    Login into the KNV heatpump and create the websocket
    """

    uri = "ws://" + ip + ":3118"
    valueIds = []

    logger.info("Starting Connection")
    async with websockets.connect(uri) as websocket:

        # Init stuff

        await websocket.send('#serial?120623100000028\n')
        await websocket.send(knvparser.login(username, password))
        await websocket.send(knvparser.command("printHotlinks"))
        await websocket.send(knvparser.command("removeAllHotlinks"))

        # Request & process List Function

        await websocket.send(knvparser.get_list_functions(1, 2))
        await websocket.send(knvparser.get_list_functions(2, 2))

        response = knvparser.ws2json(await websocket.recv())

        if response["command"] == "login":
            logger.info("Successfully logged in with UserID: %s",
                        response["userId"])
        else:
            logger.fatal("Login was incorrect!")
            return

        while True:
            response = knvparser.ws2json(await websocket.recv())

            if response["command"] != "printHotlinks" and response["command"] != "removeAllHotlinks":
                break

        while True:
            result = response["result"]["listfunctions"]
            for el in result:
                valueIds.extend(knvparser.gen_func_val_ids(el))

            try:
                async with timeout(1):
                    response = knvparser.ws2json(await websocket.recv())
            except asyncio.TimeoutError:
                logger.info("Received all List Functions")
                break

            if response["command"] != "getListFunctions":
                break

        logger.info(valueIds)

        # Request Values

        for val in valueIds:
            await websocket.send(knvparser.add_hotlink(val))

        while True:
            response = knvparser.ws2json(await websocket.recv())

            if response["command"] != "addHotlink" and response["command"] != "HLInfo":
                break

        logger.info(response)

        return True
