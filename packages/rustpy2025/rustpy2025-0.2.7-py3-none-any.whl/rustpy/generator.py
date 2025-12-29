import os
from pathlib import Path

def generate_project(path):
    base = Path(path)
    base.mkdir(parents=True, exist_ok=True)

    # Folder Structure
    (base / "apps").mkdir(exist_ok=True)
    (base / "apps" / "handlers").mkdir(parents=True, exist_ok=True)
    (base / "apps" / "keyboards").mkdir(parents=True, exist_ok=True)
    (base / "apps" / "states").mkdir(parents=True, exist_ok=True)
    (base / "data").mkdir(exist_ok=True)

    # __init__.py
    for p in [
        base / "apps",
        base / "apps" / "handlers",
        base / "apps" / "keyboards",
        base / "apps" / "states",
    ]:
        open(p / "__init__.py", "w").close()

# MAIN HANDLER
    with open(base / "apps" / "handlers" / "main.py", "w", encoding="utf-8") as f:
        f.write(
            """from aiogram import Router, F
from aiogram.types import Message
from apps.keyboards.main_kb import main_kb

r = Router()

@r.message(F.text.in_({"/start", "start"}))
async def start(message: Message):
    await message.answer("Bot is running... 🚀", reply_markup=main_kb)
"""
        )

    # USER HANDLER
    with open(base / "apps" / "handlers" / "user.py", "w", encoding="utf-8") as f:
        f.write(
            """from aiogram import Router, F
from aiogram.types import Message
from apps.keyboards.user_kb import user_kb

r = Router()

@r.message(F.text == "user")
async def user_panel(message: Message):
    await message.answer("User panel", reply_markup=user_kb)
"""
        )

    # admin handler
    with open(base / "apps" / "handlers" / "admin.py", "w", encoding="utf-8") as f:
        f.write(
            """from aiogram import Router
from aiogram.types import Message
from apps.keyboards.admin_kb import admin_kb

r = Router()

@r.message()
async def admin_panel(message: Message):
    await message.answer(
        "This is admin panel",
        reply_markup=admin_kb
    )

"""
        )

    # main keyboard
    with open(base / "apps" / "keyboards" / "main_kb.py", "w", encoding="utf-8") as f:
        f.write(
            """from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='menu', callback_data='menu')]
    ]
)
"""
        )

    # user keyboard
    with open(base / "apps" / "keyboards" / "user_kb.py", "w", encoding="utf-8") as f:
        f.write(
            """from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

user_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='user', callback_data='user')]
    ]
)
"""
        )

    # admin keyboard
    with open(base / "apps" / "keyboards" / "admin_kb.py", "w", encoding="utf-8") as f:
        f.write(
            """from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='admin', callback_data='admin')]
    ]
)
"""
        )

    # run.py (aiogram 3)
    with open(base / "run.py", "w", encoding="utf-8") as f:
        f.write(
            """from aiogram import Bot, Dispatcher
from config import TOKEN

from apps.handlers.main import r as r_main
from apps.handlers.user import r as r_user
from apps.handlers.admin import r as r_admin

import asyncio

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(r_main)
    dp.include_router(r_user)
    dp.include_router(r_admin)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
"""
        )

    # Config
    with open(base / "config.py", "w", encoding="utf-8") as f:
        f.write(
            """# Get your token from @BotFather
TOKEN = "PUT_YOUR_TOKEN_HERE"
DATABASE = {
    "ENGINE": "sqlite",
    "NAME": "db.sqlite3"
}

INSTALLED_APPS = [
    "apps.models",
]
"""
        )

    print("RustPy project created ✨")


    # MODELS FOLDER (ORM uchun)
    (base / "apps" / "models").mkdir(parents=True, exist_ok=True)
    (base / "apps" / "models" / "migrations").mkdir(parents=True, exist_ok=True)

    with open(base / "apps" / "models" / "__init__.py", "w") as f:
        f.write(
"""from .main_models import *

from rustpy.setup import setup_from_config
import config
setup_from_config(config)
"""
    )
    open(base / "apps" / "models" / "migrations" / "__init__.py", "w").close()
    with open(base / "apps" / "models" / "main_models.py", "w") as f:
        f.write(
"""from rustpy.models import Model, IntegerField, CharField
"""
    )
