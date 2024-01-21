import sys
import os
from pathlib import Path


# region Don't change
if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.absolute()

SKYARKCHRONICLES_ABI_PATH = os.path.join(
    ROOT_DIR, 'abis\\skyarkchronicles.json'
)

ACCOUNTS_DIR = os.path.join(ROOT_DIR, 'accounts')

PRIVATE_KEY_PATH = os.path.join(ACCOUNTS_DIR, 'private_keys.txt')
PROXY_PATH = os.path.join(ACCOUNTS_DIR, 'proxies.txt')

DB_FILE_PATH = os.path.join(ROOT_DIR, 'status\\data.json')


# endregion


# Кошель на который будут капать рефки
REFER_WALLET = ''

# Сон между активностями и попытками
SLEEP_RANGE = range(3, 6)

# Количество одновременных потоков
NUMBER_OF_THREADS = 10
