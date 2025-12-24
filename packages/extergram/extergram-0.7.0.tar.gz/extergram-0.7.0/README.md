# Extergram — Asynchronous Telegram Bot Framework

*Disclaimer: This project is an independent open-source library and is not affiliated with, associated with, authorized by, endorsed by, or in any way officially connected with Telegram FZ-LLC or any of its subsidiaries or its affiliates.*

Extergram is a simple, modern, and fully asynchronous library for creating Telegram bots in Python.

## Quick Start

### Installation

```shell
pip install extergram```

## Simple Echo Bot Example

```python
import asyncio
from extergram import Bot, Message
from extergram.ext import CommandHandler, MessageHandler

# Initialize the bot with your token
bot = Bot('YOUR_BOT_TOKEN')

async def start_handler(bot_instance: Bot, message: Message):
    """
    Handles the /start command and sends a welcome message.
    """
    await bot_instance.send_message(
        chat_id=message.chat.id,
        text="Extergram v0.7.0 is working! 🐾\nAsync polling is now stable."
    )

async def echo_handler(bot_instance: Bot, message: Message):
    """
    Simple echo handler to verify that message processing works.
    """
    if message.text:
        await bot_instance.send_message(
            chat_id=message.chat.id,
            text=message.text
        )

async def main():
    # Registering handlers using the ext module
    bot.add_handler(CommandHandler("start", start_handler))
    bot.add_handler(MessageHandler(echo_handler))
    
    print("Starting Extergram v0.7.0 bot...")
    
    # Polling is an async coroutine in v0.7.0
    await bot.polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping the bot...")```


## Complete Example (Classic Style)

This example demonstrates the original handler style, which remains fully supported for backward compatibility.

```python
# main.py
import asyncio
import datetime
from extergram import Bot, ButtonsDesign, Message, CallbackQuery, errors, Markdown
from extergram.ext import CommandHandler, CallbackQueryHandler

# Initialize the bot with your token
bot = Bot('YOUR_BOT_TOKEN', default_parse_mode="MarkdownV2")

# Create an inline keyboard
main_menu = ButtonsDesign().add_row(
    ButtonsDesign.create_button("Show time", "show_time"),
    ButtonsDesign.create_button("About", "about")
).add_row(
    ButtonsDesign.create_url_button("GitHub", "https://github.com/AAVTIBI1/extergram"),
    ButtonsDesign.create_button("Delete", "delete")
)

async def start(bot_instance: Bot, message: Message):
    user_name = message.from_user.first_name
    
    # Используем Markdown для автоматического экранирования точек и спецсимволов
    text = Markdown(f"Hello, {user_name}! I am running on Extergram v0.7.0.")
    
    await bot_instance.send_message(
        chat_id=message.chat.id,
        text=str(text),
        reply_markup=main_menu
    )

async def handle_callbacks(bot_instance: Bot, callback: CallbackQuery):
    await bot_instance.answer_callback_query(callback.id)
    
    if callback.data == 'show_time':
        now = datetime.datetime.now().strftime("%H:%M:%S")
        # Экранируем время, так как там есть двоеточия
        text = Markdown(f"The current time is: `{now}`")
        await bot_instance.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=str(text),
            reply_markup=main_menu
        )
    
    elif callback.data == 'about':
        text = Markdown("Extergram is a simple and modern async library for Telegram bots.")
        await bot_instance.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=str(text),
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
        print("Bot stopped.")```

## Complete Example (Using ContextTypes)

This example shows the new, recommended approach using the ContextTypes object, which simplifies handler function signatures.

```python
# main_context_style.py
import asyncio
import datetime
from extergram import Bot, ButtonsDesign, ContextTypes, errors, Markdown
from extergram.ext import CommandHandler, CallbackQueryHandler, MessageHandler

# Инициализируем бота, MarkdownV2 включен по умолчанию для всех сообщений
bot = Bot('YOUR_BOT_TOKEN', default_parse_mode='MarkdownV2')

# Создаем меню
main_menu = ButtonsDesign().add_row(
    ButtonsDesign.create_button("Show time", "show_time"),
    ButtonsDesign.create_button("About", "about")
).add_row(
    ButtonsDesign.create_url_button("GitHub", "https://github.com/AAVTIBI1/extergram"),
    ButtonsDesign.create_button("Delete", "delete")
)

async def start(context: ContextTypes):
    user_name = context.message.from_user.first_name
    # Markdown автоматически экранирует точку в версии v0.7.0
    text = Markdown(f"Hello, {user_name}! I am running on Extergram v0.7.0.")
    
    await context.bot.send_message(
        chat_id=context.message.chat.id,
        text=str(text),
        reply_markup=main_menu
    )

async def handle_callbacks(context: ContextTypes):
    callback = context.callback_query
    await context.bot.answer_callback_query(callback.id)
    
    if callback.data == 'show_time':
        now = datetime.datetime.now().strftime("%H:%M:%S")
        # Экранируем время через Markdown
        text = Markdown(f"The current time is: `{now}`")
        await context.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=str(text),
            reply_markup=main_menu
        )
    
    elif callback.data == 'about':
        text = Markdown("Extergram is a simple and modern async library for Telegram bots.")
        await context.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=str(text),
            reply_markup=main_menu
        )

    elif callback.data == 'delete':
        try:
            await context.bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except errors.BadRequestError:
            await context.bot.answer_callback_query(callback.id, "Error: Message is too old.", show_alert=True)

async def echo_handler(context: ContextTypes):
    # Безопасное эхо: любые символы пользователя будут экранированы
    response = Markdown(f"Echo: {context.message.text}")
    await context.bot.send_message(chat_id=context.message.chat.id, text=str(response))

async def main():
    # Регистрация хендлеров из extergram.ext
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(handle_callbacks))
    bot.add_handler(MessageHandler(echo_handler))
    
    print("Context-style bot is starting...")
    await bot.polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")```

## Features & Core Concepts

* Fully Async: High-performance non-blocking operations using httpx.

* Handler System: Manage updates with CommandHandler, MessageHandler, and CallbackQueryHandler. Backward compatibility is fully maintained.

* Context System: An optional ContextTypes object can be used in handlers to bundle the bot instance and update object, leading to cleaner code.

* Admin Functionality: A comprehensive set of methods for chat administration is now available:

ban_chat_member, unban_chat_member

restrict_chat_member (used with the ChatPermissions object)

promote_chat_member

approve_chat_join_request, decline_chat_join_request

* Safe Markdown Builder: The Markdown helper class in utils now automatically escapes special characters to prevent common API errors (Bad Request: can't parse entities).

* Type Hinting: Comprehensive api_types for better IDE support and code clarity.

* Error Handling:

errors.NetworkError: Connection issues.

errors.BadRequestError: Invalid API requests.

errors.ForbiddenError: Bot blocked by user.

errors.UnauthorizedError: Invalid token.

errors.TelegramAdminError: A new specific error raised when the bot lacks the necessary administrative rights to perform an action.

* Local Documentation

You can access the full documentation directly from your terminal:

```python
from extergram import Docs
Docs.print_docs()
## License

MIT License. Copyright (c) 2024-2025.

code
Code
download
content_copy
expand_less
---