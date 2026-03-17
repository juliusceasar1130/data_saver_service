import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8088/ws/emosweb"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected.")
            # Subscribe
            subscription_msg = {
                "type": "advise",
                "plc": "L3FUB2",
                "tag": "_1A_1A005TC_1A005RB.IL.SD.I1030_RBDataSkidNo"
            }
            print(f"Sending subscription: {subscription_msg}")
            await websocket.send(json.dumps(subscription_msg))
            
            # Listen for messages
            print("Listening for messages...")
            count = 0
            hyphen_seen = False
            normal_seen = False
            
            # Wait for up to 30 messages or until we see both types (timeout just in case)
            for _ in range(30):
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(msg)
                    val = data.get('value')
                    print(f"Received: {val}")
                    
                    if val == "-" * 30:
                        hyphen_seen = True
                        print("-> SAW HYPHEN STRING")
                    else:
                        normal_seen = True
                        
                    if hyphen_seen and normal_seen:
                        print("SUCCESS: Both formats observed.")
                        break
                except asyncio.TimeoutError:
                    print("Timeout waiting for message")
                    break
            
            if not hyphen_seen:
                print("WARNING: Did not see hyphen string in the samples.")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
