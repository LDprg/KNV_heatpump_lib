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

                logger.debug("Reset Hotlinks")
                await self.websocket.send(knvparser.command("printHotlinks"))
                await self.websocket.send(knvparser.command("removeAllHotlinks"))

                logger.debug("Request List Functions")
                await self.websocket.send(knvparser.get_list_functions(1, 2))
                await self.websocket.send(knvparser.get_list_functions(2, 2))

                list_func = knvparser.get_all_ids()

                for val in list_func:
                    await self.req_hotl(val)

                self.list_func.extend(list_func)
                self.list_func = list(dict.fromkeys(self.list_func))

                async for message in websocket:
                    await self.proc_command(knvparser.ws2json(message))
            except websockets.ConnectionClosed:
                self.websocket = None
                continue

    async def send(self, id, val):
        if self.websocket:
            logger.debug("Send %s with %s", id, val)
            await self.websocket.send(knvparser.set_vm_value(id, val))

    async def req_hotl(self, val):
        if self.websocket:
            logger.debug("Request Hotlinks")
            await self.websocket.send(knvparser.add_hotlink(val))

    async def proc_command(self, response):
        if response["command"] == "login":
            logger.info("Successfully logged in with UserID: %s",
                        response["userId"])
        elif response["command"] == "printHotlinks":
            logger.debug("Received printHotlinks")
        elif response["command"] == "removeAllHotlinks":
            logger.debug("Received removeAllHotlinks")
        elif response["command"] == "addHotlink":
            logger.debug("Received addHotlink")
        elif response["command"] == "getListFunctions":
            logger.debug("Received List Functions")

            result = response["result"]["listfunctions"]
            list_func = []

            for el in result:
                list_func.extend(knvparser.gen_func_val_ids(el))

            for val in list_func:
                await self.req_hotl(val)

            self.list_func.extend(list_func)
            self.list_func = list(dict.fromkeys(self.list_func))
        elif response["command"] == "HLInfo":
            logger.debug("Received Info")

            self.data[response["path"]] = {
                "path": response["path"],
                "name": unquote(response["name"]),
                "unit": unquote(response["unit"]),
                "writeable": response["writeable"],
                "min": response["min"],
                "max": response["max"],
                "step": response["step"],
                "type": response["type"],
                "listentries": response["listentries"] if "listentries" in response else None,
            }

        elif response["command"] == "HLVal":
            logger.debug("Received Value")

            for val in response["values"]:
                self.data[val["path"]]["value"] = unquote(val["result"])

                try:
                    await self.callback(self.data[val["path"]])
                except Exception as e:
                    logger.error("Error in callback: %s", e)

        else:
            logger.info(response)


async def get_data(ip, username, password):
    """
    Login into the KNV heatpump and create the websocket
    """

    uri = "ws://" + ip + ":3118"
    value_ids = knvparser.get_all_ids()
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
                "type": response["type"],
                "listentries": response["listentries"] if "listentries" in response else None,
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

        array = []
        for val in data:
            array.append(data[val])

        for _, ent in enumerate(array):
            logger.info(ent)

        logger.info("Finished data fetch")

        return data
