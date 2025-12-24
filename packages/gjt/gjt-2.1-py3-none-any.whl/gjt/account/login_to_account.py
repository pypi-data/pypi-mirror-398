from misc.connect_to_websocket import WSWrapper
import asyncio, random
from loguru import logger

async def login_to_account(username: str, password: str) -> bool:
    wrapper = WSWrapper()
    logger.info(f"Logging in to account '{username}'")
    assert wrapper.server is str
    login_data = {
        "CONM":696,
        "RTM":54,
        "ID":0,
        "PL":1,
        "NOM":username,
        "PW":password,
        "LT":None,
        "LANG":"pl",
        "DID":"0",
        "AID":"1748087142659830366",
        "KID":"",
        "REF":"https://empire.goodgamestudios.com",
        "GCI":"",
        "SID":9,
        "PLFID":1
        }
    await wrapper.send_json("vln", f'{{"NOM": {username}}}')
    await asyncio.sleep(random.uniform(0.5, 1.5))
    login_message = await wrapper.send_json("lli", login_data, True)
    if login_message:
        if "LOGIN_COOLDOWN" in str(login_message) or "INVALID_PASSWORD" in str(login_message):
            logger.error(f"Login failed for account '{username}': {login_message}")
            return False
        logger.info("Got login resp" + str(login_message))
    await wrapper.send_json("nch", "")
    await wrapper.send_json("core_gic", {"T":"link","CC":"PL","RR":"html5"})
    await wrapper.send_json("gbl", '{}')
    await wrapper.send_json("jca", '{"CID":-1,"KID":0}')
    await wrapper.send_json("alb", '{}')
    await wrapper.send_json("sli", '{}')
    await wrapper.send_json("gie", '{}')
    await wrapper.send_json("asc", '{}')
    await wrapper.send_json("sie", '{}')
    await wrapper.send_json("kli", '{}')
    data = await wrapper.send_json("ffi", '{"FIDS":[1]}', True)
    await wrapper.send_json("kli", '{}')
    if data:
        await wrapper.send_json("gcs", '{}')
    logger.info(f"Logged in to account '{username}' successfully")
    return True
