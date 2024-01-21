import asyncio
import platform
from config import DB_FILE_PATH, NUMBER_OF_THREADS
from tasks.skyarkchronicles_client import Skyarkchronicles_Client
from utils.db_func import async_read_json, process_accounts
from utils.utils import get_address_from_private_key, read_accounts_data, set_windows_event_loop_policy
from logger import logger


def create_tasks_for_accounts(accounts, data, option):
    if option == 1:
        tasks = [asyncio.create_task(
            Skyarkchronicles_Client(
                account.private_key,
                data=data[get_address_from_private_key(account.private_key)]
            ).main()
        ) for account in accounts]
    elif option == 2:
        tasks = [asyncio.create_task(
            Skyarkchronicles_Client(
                account.private_key,
                data=data[get_address_from_private_key(account.private_key)]
            ).check_in()
        ) for account in accounts]
    elif option == 3:
        tasks = [asyncio.create_task(
            Skyarkchronicles_Client(
                account.private_key,
                data=data[get_address_from_private_key(account.private_key)]
            ).get_points_info()
        ) for account in accounts]
    elif option == 4:
        tasks = [asyncio.create_task(
            Skyarkchronicles_Client(
                account.private_key,
                data=data[get_address_from_private_key(account.private_key)]
            ).exploration()
        ) for account in accounts]
    return tasks


async def main():
    print("DONATE ANY EVM: 0x5149Ae7F9445E70331608EA03C592c078aE7399D")
    print("Telegram: https://t.me/oblakov_0372")
    print('''
Select the option:
1) Register and daily check in
2) Daily check in
3) Get the number of points
4) Exploration transaction''')

    print(56*"-")

    try:
        option = int(input("[?] Your option: "))
        if option not in [1, 2, 3, 4]:
            logger.error("Invalid option selected")
            return
    except ValueError:
        logger.error("Non-integer value entered for option")
        return
    accounts = read_accounts_data()
    if not accounts:
        logger.error("File have not any private keys")
        return
    await process_accounts(DB_FILE_PATH, accounts)
    data = await async_read_json(DB_FILE_PATH)

    for start_index in range(0, len(accounts), NUMBER_OF_THREADS):
        end_index = start_index + NUMBER_OF_THREADS
        account_chunk = accounts[start_index:end_index]
        tasks = create_tasks_for_accounts(account_chunk, data, option)

        logger.info(
            f'Start work with {start_index + 1}-{start_index + NUMBER_OF_THREADS} accounts')
        await asyncio.wait(tasks)

        if end_index >= len(accounts):
            logger.success("All accounts ready")
            return

if __name__ == "__main__":
    if platform.system() == "Windows":
        set_windows_event_loop_policy()

    asyncio.run(main())
