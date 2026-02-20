
import sqlite3
from views.user import list_users

users_json = list_users()
print(users_json)
