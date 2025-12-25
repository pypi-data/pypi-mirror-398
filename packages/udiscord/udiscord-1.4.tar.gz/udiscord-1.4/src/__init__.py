from udiscord import AsyncClient, set_log_level, log
from config import log_level
client = AsyncClient()
set_log_level(log_level)