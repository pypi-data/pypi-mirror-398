import logging
from asyncio import run
from PGram import Bot
from loader import TOKEN
from example.router import r

""" Basic example """
logging.getLogger().setLevel(logging.INFO)
bot = Bot(TOKEN)
run(bot.start([r]))
