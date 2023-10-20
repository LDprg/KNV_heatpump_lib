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


class Socket:
    def __init__(self):
        self.websocket = None
        self.callback = None
        self.url = None
        self.data = {}
        self.list_func = []

    async def create(self, ip, username, password, callback=None):
        self.url = "ws://" + ip + ":3118"
        self.callback = callback

        logger.info("Creating connection")
        async for websocket in websockets.connect(self.url):
            try:
                self.websocket = websocket

                await self.websocket.send('#serial?120623100000028\n')

                logger.info("Logging in")
                await self.websocket.send(knvparser.login(username, password))

                logger.info("Reset Hotlinks")
                await self.websocket.send(knvparser.command("printHotlinks"))
                await self.websocket.send(knvparser.command("removeAllHotlinks"))

                logger.info("Request List Functions")
                await self.websocket.send(knvparser.get_list_functions(1, 2))
                await self.websocket.send(knvparser.get_list_functions(2, 2))

                async for message in websocket:
                    await self.proc_command(knvparser.ws2json(message))
            except websockets.ConnectionClosed:
                self.websocket = None
                continue

    async def req_hotl(self, val):
        if self.websocket:
            logger.info("Request Hotlinks")
            await self.websocket.send(knvparser.add_hotlink(val))

    async def proc_command(self, response):
        if response["command"] == "login":
            logger.info("Successfully logged in with UserID: %s",
                        response["userId"])
        elif response["command"] == "printHotlinks":
            logger.info("Received printHotlinks")
        elif response["command"] == "removeAllHotlinks":
            logger.info("Received removeAllHotlinks")
        elif response["command"] == "addHotlink":
            logger.info("Received addHotlink")
        elif response["command"] == "getListFunctions":
            logger.info("Received List Functions")

            result = response["result"]["listfunctions"]
            list_func = []

            for el in result:
                list_func.extend(knvparser.gen_func_val_ids(el))

            for val in list_func:
                await self.req_hotl(val)

            self.list_func.extend(list_func)
            self.list_func = list(dict.fromkeys(self.list_func))
        elif response["command"] == "HLInfo":
            logger.info("Received Info")

            self.data[response["path"]] = {
                "path": response["path"],
                "name": unquote(response["name"]),
                "unit": unquote(response["unit"]),
                "writeable": response["writeable"],
                "min": response["min"],
                "max": response["max"],
                "step": response["step"],
                "type": response["type"]
            }

        elif response["command"] == "HLVal":
            logger.info("Received Value")

            for val in response["values"]:
                self.data[val["path"]]["value"] = unquote(val["result"])
                
                try:
                    await self.callback(self.data[val["path"]])
                except:
                    logger.error("An error occured in the callback")

        else:
            logger.info(response)


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
                "step": response["step"],
                "type": response["type"]
            }

            try:
                async with timeout(0.5):
                    response = knvparser.ws2json(await websocket.recv())
            except asyncio.TimeoutError:
                logger.info("Received all HLInfo")
                break

            if response["command"] != "HLInfo":
                break

        # logger.info(data)

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

        # logger.info(data)

        array = []
        for val in data:
            array.append(data[val])

        for idx, ent in enumerate(array):
            logger.info(idx)
            logger.info(ent)

        logger.info("Finished data fetch")

        return data
