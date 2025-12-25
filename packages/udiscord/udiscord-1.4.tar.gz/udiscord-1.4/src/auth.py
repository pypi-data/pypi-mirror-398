from . import client, log
from config import email, password
from .utils import load_auth, save_auth
from asyncio import sleep

async def login_with_token() -> bool:
    auth = load_auth()
    if not auth:
        return False

    try:
        await client.login_token(auth["token"])
        await sleep(2)
        log.info(f"Logged in using saved token. [{auth['uid']} - {client.account.user.username}]")
        return True
    except Exception as e:
        log.warning(f"Token login failed: {e}")
        return False


async def login_with_email() -> bool:
    try:
        info = await client.login(email, password)
    except Exception as e:
        log.critical(f"Failed login with {email}: {e}")
        return False
    save_auth(info.token, info.userId)
    await sleep(2)
    log.info(f"{email} - {client.account.user.username} successfully logged in via email/password.")
    return True



async def auth():
    if await login_with_token() is False:
        return await login_with_email()
    return True
