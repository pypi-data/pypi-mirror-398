# Extergram v0.6.0 — Asynchronous Telegram Bot Framework

Extergram is a simple, modern, and fully asynchronous library for creating Telegram bots in Python.

## Quick Start

### Installation

pip install extergram

### Complete Example (main.py)

import asyncio
import datetime
from extergram import Bot, ButtonsDesign, Message, CallbackQuery, errors
from extergram.api_types import BotCommand
from extergram.ext import CommandHandler, CallbackQueryHandler

# Initialize the bot with your token
bot = Bot('YOUR_BOT_TOKEN')

# Create an inline keyboard with a new URL button
main_menu = ButtonsDesign().add_row(
    ButtonsDesign.create_button("Show time", "show_time"),
    ButtonsDesign.create_button("About", "about")
).add_row(
    ButtonsDesign.create_url_button("GitHub", "https://github.com/AAVTIBI1/extergram"),
    ButtonsDesign.create_button("Delete", "delete")
)

async def start(bot_instance: Bot, message: Message):
    user_name = message.from_user.first_name
    await bot_instance.send_message(
        chat_id=message.chat.id,
        text=f"Hello, {user_name}! I am running on Extergram v0.6.0.",
        reply_markup=main_menu
    )

async def handle_callbacks(bot_instance: Bot, callback: CallbackQuery):
    await bot_instance.answer_callback_query(callback.id)
    
    if callback.data == 'show_time':
        now = datetime.datetime.now().strftime("%H:%M:%S")
        await bot_instance.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"The current time is: {now}",
            reply_markup=main_menu
        )
    
    elif callback.data == 'about':
        await bot_instance.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="Extergram is a simple and modern async library for Telegram bots.",
            reply_markup=main_menu
        )

    elif callback.data == 'delete':
        try:
            await bot_instance.delete_message(callback.message.chat.id, callback.message.message_id)
        except errors.BadRequestError:
            await bot_instance.answer_callback_query(callback.id, "Error: Message is too old to delete.", show_alert=True)

async def main():
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(handle_callbacks))
    
    print("Bot is starting...")
    await bot.polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")

## Features & Core Concepts

*   **Fully Async**: High-performance non-blocking operations using `httpx`.
*   **Handler System**: Manage updates with `CommandHandler`, `MessageHandler`, and `CallbackQueryHandler`.
*   **Type Hinting**: Comprehensive `api_types` for better IDE support and code clarity.
*   **Error Handling**:
    *   `errors.NetworkError`: Connection issues.
    *   `errors.BadRequestError`: Invalid API requests.
    *   `errors.ForbiddenError`: Bot blocked by user.
    *   `errors.UnauthorizedError`: Invalid token.

## Local Documentation

You can access the full documentation directly from your terminal:

from extergram import Docs
Docs.print_docs()

## License

MIT License. Copyright (c) 2024-2025.