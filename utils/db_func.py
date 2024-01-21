import json
import aiofiles
import asyncio
import shutil
from typing import List
from config import DB_FILE_PATH
from fake_useragent import UserAgent

from utils.account import Account
from utils.utils import get_address_from_private_key


write_lock = asyncio.Lock()


# Функция для асинхронного чтения JSON файла
async def async_read_json(file_path):
    async with write_lock:
        async with aiofiles.open(file_path, 'r') as file:
            data = await file.read()
            return json.loads(data)


# Функция для асинхронной записи в JSON файл
async def async_write_json(data, file_path):
    async with write_lock:
        async with aiofiles.open(file_path, 'w') as file:
            await file.write(json.dumps(data, indent=4))


async def process_accounts(file_path, source_data: List[Account]):
    accounts = await async_read_json(file_path)

    for account in source_data:
        wallet_address = get_address_from_private_key(account.private_key)
        if wallet_address not in accounts:
            accounts[wallet_address] = {
                "proxy": account.proxy,
                "useragent": UserAgent(browsers="chrome", os="windows").random,
                "last_check_in": "1900-01-01",
                "jwt": "",
                "points": 0,
                "last_exploration": "1900-01-01"
            }

    await async_write_json(accounts, DB_FILE_PATH)
