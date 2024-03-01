from configparser import ConfigParser

import uvicorn
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqlalchemy import create_engine

from seminar_bot.db import User

app = FastAPI()

with open('config.ini') as f:
    config = ConfigParser()
    config.read_file(f)


engine = create_engine(config["bot"].get('db_uri'))
admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    column_list = [
        User.name,
        User.phone_number,
        User.date,
        User.organization,
        User.hotel_info
    ]
    can_edit = False
    can_create = False
    can_export = False
    column_searchable_list = [User.name, User.phone_number, User.organization]


admin.add_view(UserAdmin)


if __name__ == "__main__":
    uvicorn.run(app)
