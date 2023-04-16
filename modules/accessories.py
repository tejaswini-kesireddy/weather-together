import os
from typing import Optional

from pydantic import BaseConfig, BaseModel, EmailStr, PositiveInt


class UserData(BaseConfig):
    user_input = ('email_address', 'zipcode', 'report_time', 'frequency', 'crowdsource_button')


class CreateAlert(BaseModel):
    email_address: EmailStr
    zipcode: PositiveInt
    report_time: str
    frequency: int = None
    otp: str = None
    accept_crowd_sourcing: bool = True


class PublishInfo(BaseModel):
    email_address: EmailStr
    description: str
    zipcode: PositiveInt
    otp: Optional[str]


user_data = UserData()
if not os.path.isdir("images"):
    os.mkdir("images")

otp_dict = {}
