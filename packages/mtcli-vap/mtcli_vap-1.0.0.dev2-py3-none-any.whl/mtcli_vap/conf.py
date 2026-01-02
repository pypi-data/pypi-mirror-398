import os

from mtcli.conf import config

# Defaults: leem variáveis de ambiente quando presentes, senão usam config do mtcli
SYMBOL = os.getenv("SYMBOL", config["DEFAULT"].get("symbol", fallback="WIN$N"))
DIGITOS = int(os.getenv("DIGITOS", config["DEFAULT"].getint("digitos", fallback=2)))
PERIOD = os.getenv("PERIOD", config["DEFAULT"].get("period", fallback="M1"))
LIMIT = int(os.getenv("LIMIT", config["DEFAULT"].getint("limit", fallback=566)))
TICK_SIZE = float(
    os.getenv("TICK_SIZE", config["DEFAULT"].getfloat("tick_size", fallback=5))
)
SORT = os.getenv("SORT", config["DEFAULT"].get("sort", fallback="volume"))
