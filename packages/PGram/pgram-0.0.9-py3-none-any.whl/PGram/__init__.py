from aiogram import Bot as BaseBot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import UpdateType
from aiogram.types import (
    InlineKeyboardButton,
    KeyboardButton,
    Message,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    BufferedInputFile,
)
from tortoise.backends.asyncpg import AsyncpgDBClient


class Bot:
    dp: Dispatcher
    store: object
    cn: AsyncpgDBClient
    bot: BaseBot
    au: list[UpdateType] = [
        UpdateType.MESSAGE,
        UpdateType.EDITED_MESSAGE,
        UpdateType.CHANNEL_POST,
        UpdateType.EDITED_CHANNEL_POST,
        UpdateType.BUSINESS_CONNECTION,
        UpdateType.BUSINESS_MESSAGE,
        UpdateType.EDITED_BUSINESS_MESSAGE,
        UpdateType.DELETED_BUSINESS_MESSAGES,
        UpdateType.MESSAGE_REACTION,
        UpdateType.MESSAGE_REACTION_COUNT,
        UpdateType.INLINE_QUERY,
        UpdateType.CHOSEN_INLINE_RESULT,
        UpdateType.CALLBACK_QUERY,
        UpdateType.SHIPPING_QUERY,
        UpdateType.PRE_CHECKOUT_QUERY,
        UpdateType.PURCHASED_PAID_MEDIA,
        UpdateType.POLL,
        UpdateType.POLL_ANSWER,
        UpdateType.MY_CHAT_MEMBER,
        UpdateType.CHAT_MEMBER,
        UpdateType.CHAT_JOIN_REQUEST,
        UpdateType.CHAT_BOOST,
        UpdateType.REMOVED_CHAT_BOOST,
    ]

    def __init__(
        self,
        token: str,
        cn: AsyncpgDBClient = None,
        routers: list[Router] = None,
        store: object = None,
        default: DefaultBotProperties = None,
    ) -> None:
        self.bot = BaseBot(token, default=default)
        self.cn = cn
        self.dp = Dispatcher(name="disp", store=store)
        if routers:
            self.dp.include_routers(*routers)
        self.dp.shutdown.register(self.stop)

    async def start(
        self,
        au: list[UpdateType] = None,
        wh_host: str = None,
        # app_host: str = None,  # todo: app
    ):
        if au:
            self.au = au
        # self.app_host = app_host
        webhook_info = await self.bot.get_webhook_info()
        if not wh_host:
            """ START POLLING """
            if webhook_info.url:
                await self.bot.delete_webhook(True)
            await self.dp.start_polling(self.bot, polling_timeout=300, allowed_updates=self.au)
        elif (wh_url := wh_host + "/public/wh") != webhook_info.url:
            """ WEBHOOK SETUP """
            await self.bot.set_webhook(
                url=wh_url,
                drop_pending_updates=True,
                allowed_updates=self.au,
                secret_token=self.bot.token.split(":")[1],
                request_timeout=300,
            )
        return self

    async def stop(self) -> None:
        """CLOSE BOT SESSION"""
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.bot.session.close()

    async def send(
        self,
        uid: int | str,
        txt: str,
        btns: list[list[InlineKeyboardButton | KeyboardButton]] = None,
        photo: bytes = None,
        video: bytes = None,
        file: bytes = None,
    ) -> Message:
        ikm = (
            (
                InlineKeyboardMarkup(inline_keyboard=btns)
                if isinstance(btns[0][0], InlineKeyboardButton)
                else ReplyKeyboardMarkup(keyboard=btns, one_time_keyboard=True)
            )
            if btns
            else None
        )
        if photo:
            return await self.bot.send_photo(uid, BufferedInputFile(photo, "photo"), caption=txt, reply_markup=ikm)
        elif video:
            return await self.bot.send_video(uid, BufferedInputFile(video, "video"), caption=txt, reply_markup=ikm)
        elif file:
            return await self.bot.send_document(
                uid, BufferedInputFile(file, "error.log"), caption=txt, reply_markup=ikm
            )
        else:
            return await self.bot.send_message(uid, txt, reply_markup=ikm)
