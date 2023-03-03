from datetime import datetime

from gmailconnector.validator import validate_email
from pydantic import PositiveInt

from helpers.log import logger


async def validate_zip(zipcode: PositiveInt):
    if len(str(zipcode)) == 5:
        return True


async def validate_email_address(email_address):
    response = validate_email(email_address)
    if not response.ok:
        logger.error(response.body)
        return response.body


async def validate_time(report_time):
    try:
        datetime.strptime(report_time, "%H%M")
        return True
    except ValueError as error:
        logger.error(error)
