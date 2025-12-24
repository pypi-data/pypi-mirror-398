from ..misc.connect_to_websocket import WSWrapper
import json
from loguru import logger
from typing import cast

async def get_kingdom_data(kidstr: str | None = None) -> int:
    """
    Get KID from Kingdom name
    
    :return: KID integer
    :rtype: int
    """
    data = {
        # Zieleń
        "Green": 0,
        "Great Empire": 0,
        "Empire": 0,
        "Zieleń": 0,
        "Zielony": 0,
        "0": 0,
        # Zima
        "Everwinter": 2,
        "Glacier": 2,
        "Ice": 2,
        "Zima": 2,
        "Lód": 2,
        "2": 2,
        # Piaski
        "Sands": 1,
        "Sand": 1,
        "Desert": 1,
        "Burning Sands": 1,
        "Piaski": 1,
        "1": 1,
        # Szczyty
        "Fire": 3,
        "Peaks": 3,
        "Szczyty": 3,
        "Wulkan": 3,
        "3": 3
    }

    if kidstr is None:
        raise ValueError("Kingdom name cannot be None")
    kidstr = kidstr.strip()
    if kidstr not in data:
        raise ValueError(f"Unknown kingdom name: {kidstr}")
    return int(data[kidstr])

async def get_castle_id(ws, target_kingdom: int | None = None) -> int:
    "Get Castle ID for the specified kingdom"
    wrapper = ws
    if target_kingdom is None: raise ValueError("Target kingdom cannot be None")

    json_data = {
        "CD": 1
        }

    data = await wrapper.send_json("dcl", json_data, True)
    data = json.loads(data) # type: ignore
    try:
        for item in data["C"]:
            kid = item["KID"] 
            cid = item["AI"][0]["AID"]
            if kid == target_kingdom:
                return int(cid)
    except Exception as e:
        logger.error(f"Error parsing castle data: {e}")
        raise ValueError("Invalid castle data received")
    return False
    


async def switch_kingdoms(ws: WSWrapper, target_kingdom: str | None = None, sync: bool | None = False) -> bool | dict:
    """
    Switch to a different kingdom based on the provided kingdom name.

    :param wrapper: WSWrapper instance for WebSocket communication
    :param target_kingdom: Name of the target kingdom to switch to
    :return: True if switch was successful, error message string otherwise
    :rtype: bool | str
    """
    if ws is None: raise ValueError("WSWrapper cannot be None")
    wrapper = ws
    if target_kingdom == None: raise ValueError("Target kingdom cannot be None")
    try:
        target_kid = await get_kingdom_data(target_kingdom)
    except ValueError as e:
        logger.error(f"Error getting KID for kingdom '{target_kingdom}': {e}")
        return False

    logger.info(f"Switching to kingdom '{target_kingdom}' with KID={target_kid}")
    
    switch_data = {
        "CID":await get_castle_id(ws, target_kid),
        "KID":target_kid
        }
    
    if sync:
        try:
            response = await wrapper.send_json("jca", switch_data, True)
            return dict(cast(dict, response))
        except Exception as e:
            logger.error(f"Error sending switch kingdom request: {e}")
            return False
    else:
        try:
            response = await wrapper.send_json("jca", switch_data, False)
            return True
        except Exception as e:
            logger.error(f"Error sending switch kingdom request: {e}")
            return False
        