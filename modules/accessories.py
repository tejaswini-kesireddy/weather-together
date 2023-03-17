from pydantic import BaseConfig


class UserData(BaseConfig):
    user_input = ('email_address', 'zipcode', 'report_time', 'frequency')


user_data = UserData()
