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
                await self.websocket.send(knvparser.set_vm_value("0.80.0.0", 0))

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
            except Exception as e:
                self.websocket = None
                logger.error(traceback.format_exc())

            await asyncio.sleep(5)

    async def send(self, id, val):
        if self.websocket:
            logger.debug("Send %s with %s", id, val)
            await self.websocket.send(knvparser.set_vm_value(id, val))
        else:
            logger.warning("Request %s with %s failed! No Socket!", id, val)

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

            if "listentries" in self.data[response["path"]]:
                if self.data[response["path"]]["listentries"] is not None:
                    for val in self.data[response["path"]]["listentries"]:
                        val["text"] = unquote(val["text"])

        elif response["command"] == "HLVal":
            logger.debug("Received Value")

            for val in response["values"]:
                self.data[val["path"]]["value"] = unquote(val["result"])

                try:
                    await self.callback(self.data)
                except Exception as e:
                    logger.error("Error in callback: %s", e)

        else:
            logger.info(response)
