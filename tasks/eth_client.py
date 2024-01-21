from web3 import Web3
from web3.eth import AsyncEth
from typing import Optional
import aiohttp
from web3.middleware import geth_poa_middleware
from data.models import Ethereum, Network, TokenAmount
from eth_account.signers.local import LocalAccount


from logger import logger
from fake_useragent import UserAgent


class Eth_Client:

    def __init__(
            self,
            private_key: str,
            network: Network,
            proxy: str = None,
    ):
        self.private_key = private_key
        self.network = network
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'user-agent': UserAgent().chrome
        }
        self.proxy = proxy
        self.w3 = Web3(
            provider=Web3.AsyncHTTPProvider(
                endpoint_uri=self.network.rpc,
                request_kwargs={'proxy': self.proxy, 'headers': self.headers}
            ),
            modules={'eth': (AsyncEth,)},
            middlewares=[]
        )
        self.account: LocalAccount = self.w3.eth.account.from_key(
            private_key=private_key
        )

        self.address = Web3.to_checksum_address(self.account.address)

    async def get_decimals(self, contract_address: str) -> int:
        return await int(self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=Eth_Client.default_abi
        ).functions.decimals().call())

    async def balance_of(self, contract_address: str, address: Optional[str] = None) -> TokenAmount:
        if not address:
            address = self.address
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=Eth_Client.default_abi
        )
        return await TokenAmount(
            amount=contract.functions.balanceOf(address).call(),
            decimals=self.get_decimals(contract_address=contract_address),
            wei=True
        )

    async def get_allowance(self, token_address: str, spender: str) -> TokenAmount:
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(
            token_address), abi=Eth_Client.default_abi)
        return await TokenAmount(
            amount=contract.functions.allowance(self.address, spender).call(),
            decimals=self.get_decimals(contract_address=token_address),
            wei=True
        )

    async def check_balance_interface(self, token_address, min_value) -> bool:
        logger.info(
            f'{self.address} | balanceOf | check balance of {token_address}')
        balance = await self.balance_of(contract_address=token_address)
        decimal = await self.get_decimals(contract_address=token_address)
        if balance < min_value * 10 ** decimal:
            logger.error(
                f'{self.address} | balanceOf | not enough {token_address}')
            return False
        return True

    @staticmethod
    async def get_max_priority_fee_per_gas(w3: Web3, block: dict) -> int:
        block_number = block['number']
        latest_block_transaction_count = await w3.eth.get_block_transaction_count(
            block_number)
        max_priority_fee_per_gas_lst = []
        for i in range(latest_block_transaction_count):
            try:
                transaction = await w3.eth.get_transaction_by_block(block_number, i)
                if 'maxPriorityFeePerGas' in transaction:
                    max_priority_fee_per_gas_lst.append(
                        transaction['maxPriorityFeePerGas'])
            except Exception:
                continue

        if not max_priority_fee_per_gas_lst:
            max_priority_fee_per_gas = await w3.eth.max_priority_fee
        else:
            max_priority_fee_per_gas_lst.sort()
            max_priority_fee_per_gas = max_priority_fee_per_gas_lst[len(
                max_priority_fee_per_gas_lst) // 2]
        return max_priority_fee_per_gas

    async def _initialize_transaction(self, to, from_=None, value=None, data=None):
        if not from_:
            from_ = self.address
        tx_params = {
            'chainId': await self.w3.eth.chain_id,
            'nonce': await self.w3.eth.get_transaction_count(self.address),
            'from': Web3.to_checksum_address(from_),
            'to': Web3.to_checksum_address(to),
        }
        if data:
            tx_params['data'] = data
        if value:
            tx_params['value'] = value
        return tx_params

    async def _set_transaction_fees(self, tx_params, increase_gas, max_priority_fee_per_gas=None, max_fee_per_gas=None):
        if self.network.eip1559_tx:
            w3 = Web3(Web3.AsyncHTTPProvider(endpoint_uri=self.network.rpc),
                      modules={'eth': (AsyncEth)},
                      middlewares=[]
                      )
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            last_block = await w3.eth.get_block('latest')
            if not max_priority_fee_per_gas:
                max_priority_fee_per_gas = await Eth_Client.get_max_priority_fee_per_gas(
                    w3=w3, block=last_block)
            if not max_fee_per_gas:
                base_fee = int(last_block['baseFeePerGas'] * increase_gas)
                max_fee_per_gas = base_fee + max_priority_fee_per_gas
            tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
            tx_params['maxFeePerGas'] = max_fee_per_gas

        else:
            tx_params['gasPrice'] = await self.w3.eth.gas_price
        return tx_params

    async def _estimate_gas_and_check_balance(self, tx_params, increase_gas):
        try:
            estimated_gas = await self.w3.eth.estimate_gas(tx_params)
            tx_params['gas'] = int(estimated_gas * increase_gas)
            is_enough_gas = await self.check_native_balance(min_balance=estimated_gas * increase_gas)
            return is_enough_gas, tx_params
        except Exception as err:
            logger.critical(f'{self.address} | Gas estimation failed | {err}')
            return None, None

    async def _sign_and_send_transaction(self, tx_params):
        try:
            sign = self.w3.eth.account.sign_transaction(
                tx_params, self.private_key)
            tx_hash = await self.w3.eth.send_raw_transaction(sign.rawTransaction)
            if tx_hash:
                logger.info(
                    f'{self.address} | Transaction was sent. TX Hash: {tx_hash.hex()}. ')
                logger.debug(f'{self.address} | Wait for successful...')
            else:
                logger.error(f'{self.address} | Transaction was not sent')
            return tx_hash
        except Exception as err:
            logger.critical(f'{self.address} | Transaction failed | {err}')
            return None

    async def send_transaction(
            self,
            to,
            data=None,
            from_=None,
            increase_gas=1.1,
            value=None,
            max_priority_fee_per_gas: Optional[int] = None,
            max_fee_per_gas: Optional[int] = None
    ):
        logger.debug(f'{self.address} | Preparing and sending transaction...')
        tx_params = await self._initialize_transaction(
            to=to,
            from_=from_,
            value=value,
            data=data
        )
        tx_params = await self._set_transaction_fees(
            tx_params=tx_params,
            increase_gas=increase_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            max_fee_per_gas=max_fee_per_gas
        )

        is_enough_gas, tx_params = await self._estimate_gas_and_check_balance(
            tx_params=tx_params,
            increase_gas=increase_gas
        )
        if not is_enough_gas:
            return

        return await self._sign_and_send_transaction(tx_params)

    async def verif_tx(self, tx_hash) -> bool:
        try:
            data = await self.w3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=500)
            if 'status' in data and data['status'] == 1:
                logger.success(
                    f'{self.address} | transaction was successful: {self.network.explorer}tx/{tx_hash.hex()}')
                return True
            else:
                logger.err(
                    f'{self.address} | transaction failed {data["transactionHash"].hex()}')
                return False
        except Exception as err:
            logger.critical(
                f'{self.address} | unexpected error in <verif_tx> function: {err}')
            return False

    async def approve(self, token_address, spender, amount: Optional[TokenAmount] = None):
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=Eth_Client.default_abi
        )
        return await self.send_transaction(
            to=token_address,
            data=contract.encodeABI('approve',
                                    args=(
                                        spender,
                                        amount.Wei
                                    ))
        )

    async def approve_interface(self, token_address: str, spender: str, amount: Optional[TokenAmount] = None) -> bool:
        logger.info(
            f'{self.address} | approve | start approve {token_address} for spender {spender}')
        decimals = await self.get_decimals(contract_address=token_address)
        balance = await self.balance_of(contract_address=token_address)

        if balance.Wei <= 0:
            logger.error(f'{self.address} | approve | zero balance')
            return False

        if not amount or amount.Wei > balance.Wei:
            amount = balance

        approved = await self.get_allowance(
            token_address=token_address, spender=spender)
        if amount.Wei <= approved.Wei:
            logger.info(f'{self.address} | approve | already approved')
            return True

        tx_hash = await self.approve(token_address=token_address,
                                     spender=spender, amount=amount)
        verif_tx_result = await self.verif_tx(tx_hash=tx_hash)
        if not verif_tx_result:
            logger.error(
                f'{self.address} | approve | error aprove {token_address} for spender {spender}')
            return False
        return True

    async def get_eth_price(self, token='ETH'):
        token = token.upper()
        logger.info(f'{self.address} | getting {token} price')
        url = f'https://api.binance.com/api/v3/depth?limit=1&symbol={token}USDT'

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.info(
                        f'{self.address} | GetPrice | code: {response.status} | json: {await response.text()}')
                    return None
                result_dict = await response.json()  # Асинхронно читаем JSON ответ
                if 'asks' not in result_dict:
                    logger.info(
                        f'{self.address} | GetPrice | code: {response.status} | json: {await response.text()}')
                    return None
                return float(result_dict['asks'][0][0])

    async def check_native_balance(self, min_balance: int = 0) -> bool:
        """
        Check if the account has at least `min_balance` of the native currency.
        """
        balance_wei = await self.w3.eth.get_balance(self.address)
        if balance_wei < min_balance:
            logger.error(
                f'{self.address} | Insufficient native currency balance: {balance_wei} Wei')
            return False
        return True

    @staticmethod
    def get_wallet_from_private_key(private_key):
        w3 = Web3(Web3.AsyncHTTPProvider(endpoint_uri=Ethereum),
                  modules={'eth': (AsyncEth,)},
                  middlewares=[]
                  )
        address = Web3.to_checksum_address(
            w3.eth.account.from_key(private_key=private_key).address)
        return address
