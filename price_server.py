import asyncio
import json
import time
import websockets
from pycoingecko import CoinGeckoAPI


WEBSOCKET_URI = 'localhost'
WEBSOCKET_PORT = 8765
SLEEPER = 15 # We sleep for this many seconds to avoid being limited by the API
cg_client = CoinGeckoAPI()
# This maps names to symbols, need both to call the API & to send the response.
crypto_dict = {
    "bitcoin": "BTC", "ethereum": "ETH", "litecoin": "LTC", "ripple": "XRP", "bitcoin-cash": "BCH", "usdc": "USDC", "monero": "XMR", "stellar": "XLM", "usdt": "USDT",
    "qcad": "QCAD", "dogecoin": "DOGE", "chainlink": "LINK", "polygon": "MATIC", "uniswap": "UNI", "compound": "COMP", "aave": "AAVE", "dai": "DAI", "sushi": "SUSHI", "synthetix": "SNX",
    "curve": "CRV", "polkadot": "DOT", "yearn-finance": "YFI", "maker": "MKR", "pax-gold": "PAXG", "cardano": "ADA", "basic-attention-token": "BAT", "enjin": "ENJ",
    "axie-infinity": "AXS", "dash": "DASH", "eos": "EOS", "balancer": "BAL", "kyber-network-crystal": "KNC", "0x": "ZRX", "the-sandbox": "SAND",
    "the-graph": "GRT", "quant": "QNT", "ethereum-classic": "ETC", "ethereum-pow": "ETHW", "1inch": "1INCH", "chiliz": "CHZ", "chromia": "CHR",
    "super": "SUPER", "aelf": "ELF", "omg-network": "OMG", "fantom": "FTM", "decentraland": "MANA", "solana": "SOL", "algorand": "ALGO",
    "terra-classic": "LUNC", "terrausd": "UST", "zcash": "ZEC", "tezos": "XTZ", "amp": "AMP", "ren": "REN", "uma": "UMA", "shiba-inu": "SHIB",
    "loopring": "LRC", "ankr": "ANKR", "hedera": "HBAR", "multiversx": "EGLD", "avalanche": "AVAX", "harmony": "ONE", "gala": "GALA", "my-neighbor-alice": "ALICE",
    "cosmos": "ATOM", "dydx": "DYDX", "celo": "CELO", "storj": "STORJ", "skale": "SKL", "cartesi": "CTSI", "band-protocol": "BAND", "ethereum-name-service": "ENS",
    "render": "RNDR", "mask-network": "MASK", "apecoin": "APE"
}
# List of assets 
assets = list(crypto_dict.keys())
# list of clients at any given moment, represented as a set containing websockets.
clients = set()
subscription_message = {
    "event": "subscribe",
    "channel": "rates"
}

initial_prices = {}

# Call the CoinGecko API and get the prices for all assets
def get_prices() -> dict:
    'Calls the CoinGecko API and gets the asset prices in a dictionary'
    price_data = cg_client.get_price(ids=assets, vs_currencies='cad')
    return {key: price_data[key].get(
        'cad') for key in price_data}



async def accept_subscription(websocket: websockets) -> None:
    'Accepts new subscriptions, and sends a welcome message. In case of connection closing, unsubscribes the client. '
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get("event") == "subscribe" and data.get("channel") == "rates":
                await websocket.send('Welcome, new subscriber!')
                clients.add(websocket)
    except websockets.ConnectionClosedError:
        print("Removing a client")
        try:
            clients.remove(websocket)
        except:
            print('Tried to remove a client that was already gone')



def transform_price_data(coin: str, price: float) -> dict:
    'Do some funky math for the prices needed, not sure about these formulae but can be easily adjusted. Returns a dictionary type.'
    min_price = price * 0.5  # Assumed
    max_price = price * 1.5  # Asssumed
    spread = max_price - min_price  # This is what I got from some Googling
    spot = price  # Assumed
    bid = spot - spread//2  # Got this from Googling, also an assumption
    ask = spot + spread//2  # Got this from Googling, also an assumption
    change = round(((spot - price) / price) * 100, 2) # For our case, will always return 0. 
    return {"channel": "rates",
            "event": "data",
            "data":{
        'symbol': crypto_dict.get(coin, 'No coin symbol available'),
        'timestamp': int(time.time()),
        'bid': bid,
        'ask': ask,
        'spot': spot,
        'change': change
    }}

# Clean up any invalid clients
def clean_up_clients(clients: set, invalid_clients: set) -> None:
    'Looks at invalid clients and removes them from our clients set, cleans up the set'
    for invalid_client in invalid_clients:
        clients.remove(invalid_client)
    invalid_clients.clear()


async def publish() -> None:
    'The entire publishing process. Call the helper functions above to process the data, then send them to the clients in our set. '
    'In case of an ungraceful termination, cleans up the client list using the helper.'
    print('Setting Up Broadcast!')

    # Keep track of any clients that we may have lost, remove them before we iterate through the list again
    invalid_clients = set()

    while True:
        # Get the data we need from our helper
        prices = get_prices()

        for coin, price in prices.items():
            # reshape the data as needed
            if not price:
                # We've got a coin that's missing pricce data
                continue
            data = transform_price_data(coin, price) #call our helper
            # publish value to all clients
            for client in clients:
                try:
                    await client.send(json.dumps(data))
                except websockets.ConnectionClosedOK:
                    print("Removing client")
                    invalid_clients.add(client)
            clean_up_clients(clients, invalid_clients)

        print('Sent data to subscriber!')
        await asyncio.sleep(SLEEPER) #we add a sleep to avoid breaching the API rate limit


async def main():
    print(
        f"Starting WebSocket server at ws://{WEBSOCKET_URI}:{WEBSOCKET_PORT}/markets/ws")
    server = await websockets.serve(accept_subscription, WEBSOCKET_URI, WEBSOCKET_PORT)
    await asyncio.gather(server.wait_closed(), publish())


if __name__ == '__main__':
    asyncio.run(main())
