def authenticate(username, password):

    users = {

        "admin": {
            "password": "admin123",
            "role": "Admin"
        },

        "analyst": {
            "password": "analyst123",
            "role": "Analyst"
        }

    }

    if username in users:

        if users[username]["password"] == password:

            return users[username]["role"]

    return None