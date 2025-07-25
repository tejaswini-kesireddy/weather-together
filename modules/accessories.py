import os

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class UserData(BaseModel):
    user_input: tuple = ('userid', 'email_address', 'password', 'zipcode', 'report_time', 'frequency',
                         'crowdsource_button')


class Constants(BaseModel):
    blocked_file: str = "blocked.json"
    report_file: str = "report_ids.yaml"
    report_threshold: int = 3


class EnvVar(BaseSettings):
    weather_api: str
    email_username: str
    email_password: str
    casting_distance: int = 5

    class Config:
        """Environment variables configuration."""
        env_prefix = ""
        env_file = ".env"

user_data = UserData()
constants = Constants()
env = EnvVar()
if not os.path.isdir("images"):
    os.mkdir("images")

otp_dict = {}
