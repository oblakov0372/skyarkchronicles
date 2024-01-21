from decimal import Decimal
from typing import Union
from dataclasses import dataclass


@dataclass
class API:
    url: str
    docs: str


class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        if wei:
            self.Wei: int = amount
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals

        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals


class Network:
    def __init__(self,
                 name: str,
                 rpc: str,
                 chain_id: int,
                 lz_chain_id: int,
                 eip1559_tx: bool,
                 coin_symbol: str,
                 explorer: str,
                 decimals: int = 18,
                 ):
        self.name = name
        self.rpc = rpc
        self.chain_id = chain_id
        self.lz_chain_id = lz_chain_id
        self.eip1559_tx = eip1559_tx
        self.coin_symbol = coin_symbol
        self.decimals = decimals
        self.explorer = explorer

    def __str__(self):
        return f'{self.name}'


Ethereum = Network(
    name='ethereum',
    rpc='https://rpc.ankr.com/eth/',
    chain_id=1,
    lz_chain_id=101,
    eip1559_tx=True,
    coin_symbol='ETH',
    explorer='https://etherscan.io/',
)

OpBNB = Network(
    name='opbnb',
    rpc='https://opbnb.publicnode.com',
    chain_id=204,
    lz_chain_id=0,
    eip1559_tx=False,
    coin_symbol='BNB',
    explorer='https://opbnbscan.com/',
)
