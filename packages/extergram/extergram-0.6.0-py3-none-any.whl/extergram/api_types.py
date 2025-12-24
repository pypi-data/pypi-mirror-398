# extergram/api_types.py

class User:
    """This object represents a Telegram user or bot."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.is_bot = data.get('is_bot', False)
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.username = data.get('username')


class Chat:
    """This object represents a chat."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.type = data.get('type')
        self.title = data.get('title')
        self.username = data.get('username')


class Message:
    """This object represents a message."""
    def __init__(self, data: dict):
        self.message_id = data.get('message_id')
        self.from_user = User(data['from']) if 'from' in data and data['from'] else None
        self.chat = Chat(data['chat']) if 'chat' in data and data['chat'] else None
        self.date = data.get('date')
        self.text = data.get('text')
        self.caption = data.get('caption')
        # Other fields like photo, document, etc., can be added here.


class CallbackQuery:
    """This object represents an incoming callback query from a callback button in an inline keyboard."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.from_user = User(data['from']) if 'from' in data and data['from'] else None
        self.message = Message(data['message']) if 'message' in data and data['message'] else None
        self.data = data.get('data')


class Update:
    """
    This object represents an incoming update.
    At most one of the optional parameters can be present in any given update.
    """
    def __init__(self, data: dict):
        self.update_id = data.get('update_id')
        self.message = Message(data['message']) if 'message' in data else None
        self.edited_message = Message(data['edited_message']) if 'edited_message' in data else None
        self.callback_query = CallbackQuery(data['callback_query']) if 'callback_query' in data else None


class BotCommand:
    """This object represents a bot command."""
    def __init__(self, command: str, description: str):
        self.command = command
        self.description = description

    def to_dict(self):
        return {"command": self.command, "description": self.description}