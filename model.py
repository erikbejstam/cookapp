class Message:
    def __init__(self, message_id, user, text, timestamp):
        self.message_id = message_id
        self.user = user
        self.text = text
        self.timestamp = timestamp


class User:
    def __init__(self, user_id, email, name):
        self.user_id = user_id
        self.email = email
        self.name = name
