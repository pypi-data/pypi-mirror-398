from aiogram import Router
from aiogram.types import Message


r = Router()


@r.message()
async def order_msg(msg: Message):
    await msg.delete()
