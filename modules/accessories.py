import os

from pydantic import BaseConfig, BaseSettings, Field


class UserData(BaseConfig):
    user_input = ('userid', 'email_address', 'password', 'zipcode', 'report_time', 'frequency', 'crowdsource_button')


class Constants(BaseConfig):
    blocked_file: str = "blocked.json"
    report_file: str = "report_ids.yaml"
    report_threshold: int = 3


class EnvVar(BaseSettings):
    weather_api: str = Field(default=..., env="WEATHER_API")
    email_username: str = Field(default=..., env="EMAIL_USERNAME")
    email_password: str = Field(default=..., env="EMAIL_PASSWORD")
    casting_distance: int = Field(default=5, env="CASTING_DISTANCE")

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
