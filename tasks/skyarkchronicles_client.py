import asyncio
import random

from web3 import Web3
from config import DB_FILE_PATH, SKYARKCHRONICLES_ABI_PATH, SLEEP_RANGE
from data.models import OpBNB
from tasks.eth_client import Eth_Client
from utils.db_func import async_read_json, async_write_json
from utils.utils import get_address_from_private_key, get_current_date, get_headers_and_boundary, read_json
from logger import logger
from eth_account.messages import encode_defunct
from better_automation.base import BaseAsyncSession
from config import REFER_WALLET


class Skyarkchronicles_Client:
    CONTRACT_ADDRESS = Web3.to_checksum_address(
        '0xd42126d46813472f83104811533c03c807e65435')
    SIGN_IN_URL = 'https://apisky.ntoken.bwtechnology.net/api/wallet_signin.php'
    CHECK_IN_URL = 'https://apisky.ntoken.bwtechnology.net/api/checkIn_skyGate_member.php'
    GET_TOKENS_URL = 'https://apisky.ntoken.bwtechnology.net/api/get_skyGate_coin.php'

    def __init__(self, private_key, data) -> None:
        self.private_key = private_key
        self.wallet_address = get_address_from_private_key(
            private_key=private_key)
        self.proxy = data["proxy"]
        self.useragent = data["useragent"]
        self.last_check_in = data["last_check_in"]
        self.jwt = data.get("jwt", "")
        self.points = data.get("points", 0)
        self.last_exploration = data.get("last_exploration", "1900-01-01")
        self.write_lock = asyncio.Lock()
        self.eth_client = Eth_Client(
            private_key=self.private_key,
            proxy=self.proxy,
            network=OpBNB
        )
        self.async_session: BaseAsyncSession = BaseAsyncSession(
            proxy=self.proxy,
            verify=False
        )
        self.contract = self.eth_client.w3.eth.contract(
            address=Skyarkchronicles_Client.CONTRACT_ADDRESS,
            abi=read_json(SKYARKCHRONICLES_ABI_PATH)
        )

    async def _async_random_sleep(self, range: range = SLEEP_RANGE):
        sleep_seconds = random.randint(
            range.start,
            range.stop
        )
        logger.debug(
            f"{self.wallet_address} | Sleep {sleep_seconds} seconds before next step")
        await asyncio.sleep(sleep_seconds)

    async def write_to_db(self):
        async with self.write_lock:
            actual_db = await async_read_json(DB_FILE_PATH)
            actual_db[self.wallet_address] = {
                'proxy': self.proxy,
                'useragent': self.useragent,
                'last_check_in': self.last_check_in,
                'jwt': self.jwt,
                'points': self.points,
                'last_exploration': self.last_exploration
            }
            await async_write_json(actual_db, DB_FILE_PATH)

    async def sign_in(self) -> str:

        signature = 'skygate'
        message_encoded = encode_defunct(text=signature)
        signed_message = self.eth_client.account.sign_message(
            message_encoded
        ).signature.hex()
        attempt = 0
        while attempt < 5:
            logger.info(
                f"{self.wallet_address} | Sign in to skyarkchronicles")
            headers, boundary = get_headers_and_boundary(
                useragent=self.useragent
            )
            refer_wallet = Web3.to_checksum_address(REFER_WALLET)
            data = f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="api_id"\r\n\r\nskyark_react_api\r\n------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="api_token"\r\n\r\n3C2D36F79AFB3D5374A49BE767A17C6A3AEF91635BF7A3FB25CEA8D4DD\r\n------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="uWalletAddr"\r\n\r\n{self.wallet_address}\r\n------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="sign"\r\n\r\n{signed_message}\r\n------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="inviter"\r\n\r\n{refer_wallet}\r\n------WebKitFormBoundary{boundary}--\r\n'
            res = await self.async_session.post(
                url=Skyarkchronicles_Client.SIGN_IN_URL,
                headers=headers,
                data=data
            )
            if res.status_code == 200:
                res = res.json()
                if res["msg"] == "verify_success":
                    jwt = res["jwt"]
                    logger.success(f"{self.wallet_address} | Success sign in")
                    self.jwt = jwt
                    await self.write_to_db()
                    return
            else:
                logger.warning(
                    f'{self.wallet_address} | Sign in was failed, will try again')
                await self._async_random_sleep()

        logger.critical(
            f"{self.wallet_address} | Can't sign in with 5 attempts, try later")

    async def check_in(self) -> bool:
        current_date = get_current_date()
        if self.last_check_in == current_date:
            logger.info(
                f"{self.wallet_address} | Today's reward has been claimed"
            )
            return

        attempt = 0
        while attempt < 5:
            logger.info(f'{self.wallet_address} | Start check in')

            headers, boundary = get_headers_and_boundary(
                useragent=self.useragent)

            if self.jwt == "":
                await self.sign_in()

            data = f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="api_id"\r\n\r\nskyark_react_api\r\n------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="api_token"\r\n\r\n3C2D36F79AFB3D5374A49BE767A17C6A3AEF91635BF7A3FB25CEA8D4DD\r\n------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="jwt"\r\n\r\n{self.jwt}\r\n------WebKitFormBoundary{boundary}--\r\n'

            res = await self.async_session.post(
                url=Skyarkchronicles_Client.CHECK_IN_URL,
                headers=headers,
                data=data
            )
            if res.status_code == 200:
                logger.success(
                    f"{self.wallet_address} | Reward has been claimed ")
                self.last_check_in = current_date
                await self.write_to_db()
                return
            else:
                logger.warning(
                    f"{self.wallet_address} | Check in was failed, will try again")
                await self._async_random_sleep()

        logger.critical(
            f"{self.wallet_address} | Can't check in with 5 attempts, try later")

    async def get_points_info(self):
        attempt = 0
        while attempt < 5:
            logger.info(f"{self.wallet_address} | Get the number of points ")

            headers, boundary = get_headers_and_boundary(
                useragent=self.useragent)

            if self.jwt == "":
                await self.sign_in()

            data = f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="api_id"\r\n\r\nskyark_react_api\r\n------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="api_token"\r\n\r\n3C2D36F79AFB3D5374A49BE767A17C6A3AEF91635BF7A3FB25CEA8D4DD\r\n------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="jwt"\r\n\r\n{self.jwt}\r\n------WebKitFormBoundary{boundary}--\r\n'

            res = await self.async_session.post(
                url=Skyarkchronicles_Client.GET_TOKENS_URL,
                headers=headers,
                data=data
            )
            if res.status_code == 200:
                json_data = res.json()
                self.points = json_data["coin"]
                logger.success(
                    f"{self.wallet_address} | Count points: {self.points}")
                await self.write_to_db()
                return
            else:
                logger.warning(
                    f"{self.wallet_address} | Get count tokens was failed, will try again")
                await self._async_random_sleep()

        logger.critical(
            f"{self.wallet_address} | Can't get count tokens with 5 attempts, try later")

    async def exploration(self):
        current_date = get_current_date()
        if self.last_exploration == current_date:
            logger.info(
                f"{self.wallet_address} | already sended transation today")
            return

        logger.info(f"{self.wallet_address} | Start exploration")
        _type = int(
            '0000000000000000000000000000000000000000000000000000000000000001')
        tx_args = self.contract.encodeABI(
            "signin",
            args=[_type]
        )
        tx_hash = await self.eth_client.send_transaction(
            to=Skyarkchronicles_Client.CONTRACT_ADDRESS,
            data=tx_args
        )
        if not tx_hash:
            return

        await self.eth_client.verif_tx(tx_hash)
        self.last_exploration = current_date
        await self.write_to_db()

    async def main(self):
        if self.jwt == "":
            await self.sign_in()
            if self.jwt == "":
                return
        await self._async_random_sleep()
        await self.check_in()
        logger.success(f"{self.wallet_address} | Account ready")
