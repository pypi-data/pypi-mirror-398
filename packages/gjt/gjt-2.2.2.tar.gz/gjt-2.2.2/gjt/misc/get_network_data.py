import json, requests

servers_data = 'https://raw.githubusercontent.com/wojts8/ggestuff/refs/heads/main/network.json'

def get_network_data(server: str, datatype: str) -> str:
    response = requests.get(servers_data)
    data = json.loads(response.text)
    if server not in data["servers"]:
        raise ValueError(f"Server '{server}' not found in data.")
    if datatype not in data["servers"][server]:
        raise ValueError(f"Datatype '{datatype}' not found for server '{server}'.")
    if server and datatype:
        return data["servers"][server][datatype]
    else:
        raise ValueError("Both 'server' and 'datatype' parameters must be provided.")