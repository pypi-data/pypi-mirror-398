from typing_extensions import Literal

Category = Literal['SPOT', 'USDT-FUTURES', 'COIN-FUTURES', 'USDC-FUTURES']
Side = Literal['buy', 'sell']
OrderType = Literal['limit', 'market']
PosSide = Literal['long', 'short']
TimeInForce = Literal['gtc', 'post_only', 'fok', 'ioc']
OrderStatus = Literal['live', 'partially_filled', 'filled', 'canceled']
TradeScope = Literal['maker', 'taker']