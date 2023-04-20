import os

from pydantic import BaseConfig, BaseModel, EmailStr, PositiveInt


class UserData(BaseConfig):
    user_input = ('userid', 'email_address', 'password', 'zipcode', 'report_time', 'frequency', 'crowdsource_button')


class CreateAlert(BaseModel):
    email_address: EmailStr
    zipcode: PositiveInt
    password: str
    report_time: str
    frequency: int = None
    otp: str = None
    accept_crowd_sourcing: bool = True


class PublishInfo(BaseModel):
    email_address: EmailStr
    password: str
    zipcode: PositiveInt
    description: str


user_data = UserData()
if not os.path.isdir("images"):
    os.mkdir("images")

otp_dict = {}
