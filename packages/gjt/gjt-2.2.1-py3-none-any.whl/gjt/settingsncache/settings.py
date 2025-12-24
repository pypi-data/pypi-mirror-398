import json
import pathlib
from platformdirs import user_config_dir

account_template = {
        "username": "user1",
        "password": "pass1",
        "plugins": {},
        "troops_levels": {
            "OR": 0,
            "OM": 0,
            "DR": 0,
            "DM": 0
        },
        "bot_configs": [
            {
                "bot_type": "placeholder",
                "subscription_level": 1,
                "settings": {}
            }
        ]
    }


def _get_conf_dir() -> pathlib.Path:
    """Zwraca ścieżkę pathlib.Path do pliku config.json."""
    # Tworzy ścieżkę i zapewnia istnienie katalogów w jednej linii
    path = pathlib.Path(user_config_dir("gge", roaming=True)) / "universal" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def read_account(account_name: str | None = None):
    """
    Used only by internal functions
    
    :param account_name: Name of the account to read the settings of
    :type account_name: str | None
    """
    if account_name is None: raise ValueError("Account name cannot be None")
    with open(_get_conf_dir()) as f:
        f = json.loads(str(f))
        return {
            "username": f['username'],
            "password": f['password'],
            "sublevel": f['subscription-level']
        }

