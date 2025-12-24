
# Green Jasmine Tea (gjt)

A python library to connect and interact with Goodgame Empire websocket servers 


![Static Badge](https://img.shields.io/badge/State-In_Development-yellow?style=for-the-badge)

Authors:
- ![Authors](https://img.shields.io/badge/Discord-everwarden-blue?logo=discord) 
- ![Authors](https://img.shields.io/badge/Discord-wojts__-blue?logo=discord)

## Deployment

To install this library run

```bash
  pip install gjt
```


## Demo

```py
from gjt import connect_to_websocket, login_to_account

async def main():
    async with connect_to_websocket("PL1") as ws:

        print("Connected with websocket")
        
        await login_to_account("Account", "Password")
        
        # Sending a JSON Message
        data = await ws.send_json("gcm", json_data, True)
        print(data) # {"S": {"TT": 100, "PT": 0}}
```