import asyncio
import websockets
import json

async def test_client():
    uri = "ws://127.0.0.1:8765/markets/ws"
    async with websockets.connect(uri) as websocket:
        subscription_message = {
            "event": "subscribe",
            "channel": "rates"
        }
        print('Sending subscription')
        await websocket.send(json.dumps(subscription_message))
        while True:
            response = await websocket.recv()
            print(f"Received: {response}")

asyncio.run(test_client())
