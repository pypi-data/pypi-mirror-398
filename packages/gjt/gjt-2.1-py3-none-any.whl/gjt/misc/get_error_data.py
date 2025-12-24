import requests, json

errors_data = 'https://raw.githubusercontent.com/wojts8/ggestuff/refs/heads/main/errors.json'

def get_error_data(error: int) -> str:
    response = requests.get(errors_data)
    data = json.loads(response.text)
    if str(error) not in data:
        raise ValueError(f"Error code '{error}' not found in data.")
    return data[str(error)]