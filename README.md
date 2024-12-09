# WebSocket for Crypto Assets Price Streaming

This project implements a WebSocket server that streams real-time asset price updates. It fetches  prices from the [CoinGecko API](https://www.coingecko.com/), which is free but rate limiting. To that end, there is a sleep introduced in the program to not violate the limit. However, depending on regulations and/or load balancing, this may be affected. No API Key is required for the running of this program.

The server is contained in the file titled price_server.py, and a demo client is set up in the file testing.py.

For use case, run the server file followed by the client file. Multiple clients may be initiated simultaneously, and the server is programmed to continue running in the case of a client(s) failing abruptly (e.g. hitting Ctrl+C on one of the client terminals).

The responses to clients take the form of a broadcast message sent out to all "subscribers", and occur at regular intervals defined by the sleep(15 seconds) introduced to stay within rate limits of the CoinGecko API.


To run the program, type the following commands in a terminal:
1. pip install -r requirements.txt
2. python price_server.py
The program currently runs on port 8765, can be adjusted.

To test the server, run the client file by typing:
1. python testing.py
Currently set to run on port 8765, can be adjusted in the uri at the top of the file. In either case, ensure to match port defined at top of server file. You should receive periodic asset updates.

If you wish to support more assets for the program, you may modify the crypto_dict at the top of the server file, and add in a new key, value pair in the shape of {"asset":"asset_symbol"} e.g. {"bitcoin":"BTC"}.

