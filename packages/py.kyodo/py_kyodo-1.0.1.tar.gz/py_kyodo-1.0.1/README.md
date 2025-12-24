# py.kyodo

[![PyPi Version](https://img.shields.io/pypi/v/py.kyodo.svg)](https://pypi.python.org/pypi/py.kyodo/)
![Python Version](https://img.shields.io/badge/python-%3E%3D3.9-orange)
[![Issues](https://img.shields.io/github/issues-raw/fedd20/py.kyodo.svg?maxAge=25000)](https://github.com/imperialwool/Amino.fix.fix/issues)
[![Pull requests](https://img.shields.io/github/issues-pr/fedd20/py.kyodo.svg?style=flat)](https://github.com/fedd20/py.kyodo/pulls)


Basic library to talk with Kyodo servers. Based on HTTPX and websockets libraries.

## Important notices

This lib is **async** only.

This lib is only demonstration and contain basic things. Please consider to take it as research object that can be improved. Thanks in advance.

PRs and issues are welcome.

## Basic example

```python
import logging
from asyncio import run
from datetime import datetime
from kyodo import Client, Socket
from kyodo.utils.objects import Message

async def process_message(client: Client, message: Message) -> None:
	# do smth with messages, idk
    
async def main():
    logging.basicConfig(
        level=logging.INFO,
        filename="logs/{}.log".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        format="[%(asctime)s / %(levelname)s] %(name)s -> %(message)s",
    )
    logging.info("Configuration loaded...")
    client = Client()
    await client.login(email, password)
    logging.info("Client logged in...")
    socket = Socket(client, process_message)
    logging.info("Socket initialized, starting listening...")
    print("Starting now!")
    await socket.listen_forever()
    
try:
    run(main())
except KeyboardInterrupt:
    logging.info("KeyboardInterrupt received, exiting...")
    print("Exiting...")
    exit(0)

```
[![Discord server](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/Ra5b8VKNEQ)




