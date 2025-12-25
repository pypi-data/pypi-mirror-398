from . import client
from udiscord import Message, ChannelType
from config import message as msg
from config import RESPONSE_DELAY, INACTIVITY_TIMEOUT
from asyncio import sleep
from time import time

last_seen = 0
auto_responses = set()

async def on_text_message(message: Message):
    global last_seen
    
    if message.author.userId == client.userId:
        last_seen = time()
        auto_responses.clear()
        return
    
    if message.channelType != ChannelType.DIRECT_MESSAGE:
        return
    
    channel_id = message.channelId
    
    if time() - last_seen < INACTIVITY_TIMEOUT:
        return
    
    if channel_id in auto_responses:
        return
    
    auto_responses.add(channel_id)
    await sleep(RESPONSE_DELAY)
    await client.send_message(
        channelId=channel_id,
        message=msg
    )