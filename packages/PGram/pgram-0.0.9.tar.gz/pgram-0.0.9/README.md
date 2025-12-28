# PGram

### Install
```sh
pip install PGram
```

### Minimal code for running
```python
### router.py
from aiogram import Router

r = Router()

@r.message()
async def del_msg(msg):
    await msg.delete()
```

```python
### main.py
from asyncio import run
from PGram import Bot
from router import r

bot = Bot("bot:token", [r])
run(bot.start())
```
