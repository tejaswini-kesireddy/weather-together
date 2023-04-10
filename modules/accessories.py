import os

from pydantic import BaseConfig


class UserData(BaseConfig):
    user_input = ('email_address', 'zipcode', 'report_time', 'frequency', 'crowdsource_button')


user_data = UserData()
if not os.path.isdir("images"):
    os.mkdir("images")

otp_dict = {}
