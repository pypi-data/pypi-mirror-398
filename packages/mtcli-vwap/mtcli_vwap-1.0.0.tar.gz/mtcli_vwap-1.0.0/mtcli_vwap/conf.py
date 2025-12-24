import os
from mtcli.conf import config


SYMBOL = os.getenv("SYMBOL", config["DEFAULT"].get("symbol", fallback="WIN$N"))
MINUTES = int(os.getenv("MINUTES", config["DEFAULT"].getint("minutes", fallback=1)))
LIMIT = int(os.getenv("LIMIT", config["DEFAULT"].getint("limit", fallback=566)))
DIGITOS = int(os.getenv("DIGITOS", config["DEFAULT"].getint("digitos", fallback=0)))
