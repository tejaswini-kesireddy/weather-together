from datetime import datetime

import gmailconnector
from pydantic import PositiveInt

from helpers.log import logger


def validate_zip(zipcode: PositiveInt):
    if len(str(zipcode)) == 5:
        return True


def validate_pw(password):
    symbols = ["$", "#", "&", "@"]
    if not 12 > len(password) >= 6:
        return False
    if not any((f for f in symbols if f in password)):
        return False
    if not any((f for f in password if f.isdigit())):
        return False
    return True


def validate_email_address(email_address):
    response = gmailconnector.validate_email(email_address, smtp_check=False)
    if response.ok is False:
        logger.error(response.body)
        return response.body


def validate_time(report_time):
    try:
        datetime.strptime(report_time, "%H%M")
        return True
    except ValueError as error:
        logger.error(error)


def validate_frequency(frequency):
    if frequency is None:
        return True
    if 5 <= frequency <= 60 and frequency % 5 == 0:
        return True
