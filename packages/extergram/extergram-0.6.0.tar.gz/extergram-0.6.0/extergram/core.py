# extergram/core.py

import httpx
import json
import asyncio
import inspect
import os
from time import time
from collections import deque
from .ui import ButtonsDesign
from .api_types import Update, Message, CallbackQuery, BotCommand
from .ext.base import BaseHandler
from . import errors

class Bot:
    """
    The main class for creating a Telegram bot and interacting with the API.
    """
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{self.token}/"
        self.handlers = []
        self._offset = None
        self._client = httpx.AsyncClient()
        # --- Новое: Атрибуты для системы анти-флуда ---
        self._request_timestamps = deque()
        self._min_delay = 0.1  # Минимальная задержка при умеренной нагрузке
        self._max_delay = 0.5  # Максимальная задержка при высокой нагрузке

    # --- Новое: Метод для контроля скорости запросов ---
    async def _apply_anti_flood(self):
        """
        Автоматически регулирует скорость запросов для предотвращения превышения лимитов API.
        Этот метод вводит динамическую задержку в зависимости от частоты недавних запросов.
        """
        current_time = time()
        
        # Удаляем из очереди временные метки старше 2 секунд
        while self._request_timestamps and self._request_timestamps[0] <= current_time - 2:
            self._request_timestamps.popleft()

        # Определяем необходимую задержку на основе количества недавних запросов
        recent_requests = len(self._request_timestamps)
        delay = 0
        
        # Динамическая логика задержки
        if recent_requests > 25:  # Высокая нагрузка, применяем максимальную задержку
            delay = self._max_delay
        elif recent_requests > 15: # Средне-высокая нагрузка
            delay = (self._min_delay + self._max_delay) / 2 # Например, 0.3с
        elif recent_requests > 5: # Умеренная нагрузка, применяем минимальную задержку
            delay = self._min_delay

        if delay > 0 and self._request_timestamps:
            time_since_last_call = current_time - self._request_timestamps[-1]
            if time_since_last_call < delay:
                await asyncio.sleep(delay - time_since_last_call)
        
        # Записываем временную метку текущего запроса
        self._request_timestamps.append(time())

    async def _make_request(self, method: str, params: dict = None, files: dict = None):
        """Internal method to make requests to the Telegram API."""
        
        # --- Новое: Применяем задержку анти-флуда перед выполнением запроса ---
        await self._apply_anti_flood()
        
        try:
            response = await self._client.post(self.api_url + method, json=params, files=files, timeout=40)
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    description = error_data.get('description', 'Unknown API error')
                    error_code = error_data.get('error_code', response.status_code)
                except json.JSONDecodeError:
                    description = "Failed to parse error response"
                    error_code = response.status_code

                # Extended error mapping to prevent crashes
                if response.status_code == 400:
                    raise errors.BadRequestError(description, error_code)
                elif response.status_code == 401:
                    raise errors.UnauthorizedError(description, error_code)
                elif response.status_code == 403:
                    raise errors.ForbiddenError(description, error_code)
                elif response.status_code == 404:
                    raise errors.NotFoundError(description, error_code)
                elif response.status_code == 409:
                    raise errors.ConflictError(description, error_code)
                elif response.status_code == 413:
                    raise errors.EntityTooLargeError(description, error_code)
                elif response.status_code == 502:
                    raise errors.BadGatewayError(description, error_code)
                else:
                    raise errors.APIError(description, error_code)

            data = response.json()
            if not data.get('ok'):
                raise errors.APIError(data.get('description', 'Unknown error'), data.get('error_code', -1))
            
            return data
        except httpx.RequestError as e:
            # Wrap all network-related issues into NetworkError for retry logic
            raise errors.NetworkError(f"Network error: {e}", -1)
        except json.JSONDecodeError:
            raise errors.APIError("Failed to decode JSON response", -1)

    def add_handler(self, handler: BaseHandler):
        """
        Registers a new event handler.
        """
        if not isinstance(handler, BaseHandler):
            raise TypeError("handler must be an instance of BaseHandler")
        self.handlers.append(handler)

    async def _process_update(self, update: Update):
        """Asynchronously processes a single update."""
        event = update.message or update.callback_query or update.edited_message
        if not event:
            return

        tasks = []
        for handler in self.handlers:
            if handler.check_update(update):
                if inspect.iscoroutinefunction(handler.callback):
                    tasks.append(asyncio.create_task(handler.callback(self, event)))
                else:
                    loop = asyncio.get_running_loop()
                    tasks.append(loop.run_in_executor(None, handler.callback, self, event))
        
        if tasks:
            await asyncio.gather(*tasks)

    async def _polling_loop(self, timeout: int = 30):
        """The main asynchronous polling loop with auto-restart logic."""
        while True:
            try:
                updates_data = await self.get_updates(offset=self._offset, timeout=timeout)
                updates = updates_data.get('result', [])
                if updates:
                    for raw_update in updates:
                        self._offset = raw_update['update_id'] + 1
                        update_obj = Update(raw_update)
                        asyncio.create_task(self._process_update(update_obj))
            
            except errors.NetworkError as e:
                print(f"[!] Network Connection Error: {e}. Retrying in 5s...")
                await asyncio.sleep(5)
                continue # Skip to next iteration to retry

            except (errors.UnauthorizedError, errors.NotFoundError) as e:
                print(f"[CRITICAL] Invalid Token or URL: {e}")
                print(">>> Please check your BOT_TOKEN. Retrying in 10s...")
                await asyncio.sleep(10)

            except errors.ConflictError:
                print("[!] Conflict: Another bot instance is running. Waiting 10s...")
                await asyncio.sleep(10)

            except errors.BadGatewayError:
                print("[!] Telegram servers are down (502 Bad Gateway). Waiting 5s...")
                await asyncio.sleep(5)

            except errors.APIError as e:
                print(f"[!] API Error: {e}. Attempting to continue in 5s...")
                await asyncio.sleep(5)

            except Exception as e:
                print(f"[!!!] Unexpected System Error: {e}")
                await asyncio.sleep(10)

    async def polling(self, timeout: int = 30):
        """Starts the bot in long-polling mode. This is now a coroutine."""
        print("Bot started polling...")
        try:
            # This will now run inside the existing event loop when awaited.
            await self._polling_loop(timeout)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("Bot stopped.")
        finally:
            # It's a good practice to close the client session on exit.
            await self._client.aclose()


    # --- API Methods ---
    async def get_updates(self, offset: int = None, timeout: int = 30):
        params = {'timeout': timeout, 'offset': offset}
        return await self._make_request('getUpdates', params)

    async def send_message(self, chat_id: int, text: str, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id, 'text': text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
        return await self._make_request('sendMessage', params)

    async def edit_message_text(self, chat_id: int, message_id: int, text: str, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id, 'message_id': message_id, 'text': text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
        return await self._make_request('editMessageText', params)
    
    async def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False):
        params = {'callback_query_id': callback_query_id}
        if text:
            params['text'] = text
        params['show_alert'] = show_alert
        return await self._make_request('answerCallbackQuery', params)
        
    async def delete_message(self, chat_id: int, message_id: int):
        params = {'chat_id': chat_id, 'message_id': message_id}
        return await self._make_request('deleteMessage', params)

    async def send_photo(self, chat_id: int, photo: str, caption: str = None, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if caption:
            params['caption'] = caption
        if parse_mode:
            params['parse_mode'] = parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup

        # Handle URL, file_id, or local path
        if photo.startswith('http') or not os.path.exists(photo):
            params['photo'] = photo
        else:
            files = {'photo': open(photo, 'rb')}
            
        return await self._make_request('sendPhoto', params, files=files)

    async def send_document(self, chat_id: int, document: str, caption: str = None, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if caption:
            params['caption'] = caption
        if parse_mode:
            params['parse_mode'] = parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
            
        # Handle URL, file_id, or local path
        if document.startswith('http') or not os.path.exists(document):
            params['document'] = document
        else:
            files = {'document': open(document, 'rb')}

        return await self._make_request('sendDocument', params, files=files)

    async def send_video(self, chat_id: int, video: str, caption: str = None, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if caption:
            params['caption'] = caption
        if parse_mode:
            params['parse_mode'] = parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup

        # Handle URL, file_id, or local path
        if video.startswith('http') or not os.path.exists(video):
            params['video'] = video
        else:
            files = {'video': open(video, 'rb')}
            
        return await self._make_request('sendVideo', params, files=files)

    async def send_animation(self, chat_id: int, animation: str, caption: str = None, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if caption:
            params['caption'] = caption
        if parse_mode:
            params['parse_mode'] = parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
            
        # Handle URL, file_id, or local path
        if animation.startswith('http') or not os.path.exists(animation):
            params['animation'] = animation
        else:
            files = {'animation': open(animation, 'rb')}

        return await self._make_request('sendAnimation', params, files=files)

    async def edit_message_reply_markup(self, chat_id: int, message_id: int, reply_markup=None):
        params = {'chat_id': chat_id, 'message_id': message_id}
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
        return await self._make_request('editMessageReplyMarkup', params)
        
    async def set_my_commands(self, commands: list[BotCommand]):
        params = {'commands': [cmd.to_dict() for cmd in commands]}
        return await self._make_request('setMyCommands', params)