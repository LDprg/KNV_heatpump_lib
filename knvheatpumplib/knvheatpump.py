"""
Functions for interacting with KNV Home 
"""

# pylint: disable=no-member

from urllib.parse import unquote

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
    value_ids = []
    data = {}

    logger.info("Starting connection")
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

            if response["command"] != "printHotlinks" and \
               response["command"] != "removeAllHotlinks":
                break

        while True:
            result = response["result"]["listfunctions"]
            for el in result:
                value_ids.extend(knvparser.gen_func_val_ids(el))

            try:
                async with timeout(0.5):
                    response = knvparser.ws2json(await websocket.recv())
            except asyncio.TimeoutError:
                logger.info("Received all List Functions")
                break

            if response["command"] != "getListFunctions":
                break

        logger.debug(value_ids)

        # Request Values

        for val in value_ids:
            await websocket.send(knvparser.add_hotlink(val))

        while True:
            response = knvparser.ws2json(await websocket.recv())

            if response["command"] != "addHotlink":
                break

        while response["command"] == "HLInfo":
            data[response["path"]] = {
                "path": response["path"],
                "name": unquote(response["name"]),
                "unit": unquote(response["unit"]),
                "writeable": response["writeable"],
                "min": response["min"],
                "max": response["max"],
                "step": response["step"]
            }

            try:
                async with timeout(0.5):
                    response = knvparser.ws2json(await websocket.recv())
            except asyncio.TimeoutError:
                logger.info("Received all HLInfo")
                break

            if response["command"] != "HLInfo":
                break

        while True:
            if response["command"] == "HLVal":
                for val in response["values"]:
                    data[val["path"]]["value"] = unquote(val["result"])

            try:
                async with timeout(0.5):
                    response = knvparser.ws2json(await websocket.recv())
            except asyncio.TimeoutError:
                logger.info("Received all HLVal")
                break

        logger.debug(response)

        logger.debug(data)

        logger.info("Finished data fetch")

        return data
