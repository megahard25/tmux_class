import json
import os


class JSONDatabase():
    def __init__(self, path_to_json_file):
        self.path_to_json_file = path_to_json_file
        self.data = None
        self.pull()

    def get_data(self):
        if not os.path.isfile(self.path_to_json_file):
            # checks if file exists
            data = dict()
        else:
            with open(self.path_to_json_file, "r") as read_file:
                data = json.load(read_file)
        return data

    def pull(self):
        self.data = self.get_data()

    def push(self):
        if not os.path.exists(os.path.dirname(self.path_to_json_file)):
            os.makedirs(os.path.dirname(self.path_to_json_file), exist_ok=True)
        with open(self.path_to_json_file, "w") as write_file:
            json.dump(self.data, write_file)

    def check_username(self, username):
        if username in self.data.keys():
            return True
        return False

    def check_username_password(self, username, password):
        user_data = self.data.get(username, None)
        if user_data is None:
            return False
        password_in_database = user_data.get('psw', None)
        if password_in_database is not None and password == password_in_database:
            return True
        return False

    def check_remember(self, username):
        user_data = self.data.get(username, None)
        if user_data is None:
            return None
        return user_data.get('remember', None)

    def set_user_data(self, username, key, value):
        if not self.check_username(username):
            self.data[username] = {key: value}
        else:
            user_data = self.data.get(username)
            user_data[key] = value
            self.data[username] = user_data

    def save_remember(self, username, remember):
        remember_bool = True if remember == 'on' else False
        self.set_user_data(username, 'remember', remember_bool)
        self.push()

    def save_username_password(self, username, password):
        self.set_user_data(username, 'psw', password)
        self.push()