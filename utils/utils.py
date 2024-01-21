from datetime import datetime
import json
import re
from eth_keys import keys
from eth_utils import decode_hex
from utils.account import Account
from config import PROXY_PATH, PRIVATE_KEY_PATH
from logger import logger
import random
import string
import asyncio
import sys


def get_address_from_private_key(private_key: str):
    private_key_bytes = decode_hex(private_key)
    private_key = keys.PrivateKey(private_key_bytes)

    # Получение публичного ключа
    public_key = private_key.public_key

    # Получение публичного адреса Ethereum
    eth_address = public_key.to_checksum_address()

    return eth_address


def read_accounts_data():
    accounts = []
    # Читаем файлы и сохраняем данные в списки
    with open(PRIVATE_KEY_PATH, "r") as private_keys_file:
        private_keys = private_keys_file.read().splitlines()

    with open(PROXY_PATH, "r") as proxies_file:
        proxies = proxies_file.read().splitlines()

    # Проверяем, что все файлы имеют одинаковое количество строк
    if not (len(private_keys) == len(proxies)):
        logger.error("Файлы должны содержать одинаковое количество строк")

    # Создаем список объектов Account
    for private_key, proxy in zip(private_keys, proxies):
        accounts.append(Account(private_key=private_key, proxy=proxy))

    return accounts


def _generate_boundary(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def _get_browser_version(useragent: str):
    chrome_pattern = 'Chrome/(\d+)'
    match = re.search(chrome_pattern, useragent)

    if match:
        return match.group(1)
    else:
        return 113


def get_headers_and_boundary(useragent: str):
    random_boundary = _generate_boundary()
    browser_version = _get_browser_version(useragent=useragent)
    headers = {
        'authority': 'apisky.ntoken.bwtechnology.net',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': f'multipart/form-data; boundary=----WebKitFormBoundary{random_boundary}',
        'origin': 'https://skygate.skyarkchronicles.com',
        'referer': 'https://skygate.skyarkchronicles.com/',
        'sec-ch-ua': f'"Not_A Brand";v="8", "Chromium";v="{browser_version}", "Google Chrome";v="{browser_version}"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': useragent
    }
    return headers, random_boundary


def set_windows_event_loop_policy():
    if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy())


def get_current_date():
    current_date = datetime.now()
    formatted_date = current_date.strftime('%Y-%m-%d')
    return formatted_date


def read_json(path: str, encoding: str = None) -> list | dict:
    return json.load(open(path, encoding=encoding))
