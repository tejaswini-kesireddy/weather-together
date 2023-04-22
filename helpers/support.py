import os
import random
import string
import time
from datetime import datetime
from threading import Thread

import gmailconnector
from fastapi import HTTPException
from pydantic import EmailStr, PositiveInt

from helpers import validators, log
from helpers.location import find_distance
from modules.accessories import user_data, otp_dict
from modules.database import get_existing_info, db

logger = log.logger

email_object = gmailconnector.SendEmail(gmail_user=os.environ.get("EMAIL_USERNAME"),
                                        gmail_pass=os.environ.get("EMAIL_PASSWORD"))


def validations(email_address: EmailStr, password: str, zipcode: PositiveInt, report_time: str,
                frequency: int, otp: str, accept_crowd_sourcing: bool):
    """This function validates all the input parameters."""
    zip_valid = validators.validate_zip(zipcode)
    if not zip_valid:
        raise HTTPException(status_code=400, detail="zipcode is invalid: %d. zipcodes must be 5-digit" % zipcode)
    pw_valid = validators.validate_pw(password)
    if not pw_valid:
        raise HTTPException(status_code=400, detail="password is invalid: %s" % password)
    time_valid = validators.validate_time(report_time)
    if not time_valid:
        raise HTTPException(status_code=400, detail="time is invalid: %s" % report_time)
    freq_valid = validators.validate_frequency(frequency)
    if not freq_valid:
        raise HTTPException(status_code=400, detail="frequency is invalid: %s" % frequency)
    result = validators.validate_email_address(email_address)
    if result:
        raise HTTPException(status_code=400, detail="email is invalid: %s. %s" % (email_address, result))
    if otp:
        if otp == otp_dict.get(email_address):
            logger.info("%s passed OTP validation", email_address)
        else:
            raise HTTPException(status_code=401, detail="unauthorized or timed out")
    else:
        if send_otp(email_address):
            logger.info("OTP has been sent")
            return {"OK": "Please enter the OTP"}
        else:
            raise HTTPException(status_code=500, detail="failed to send otp")
    userid = int(time.time())
    # todo: encrypt pw before storing it into db
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute(
            f"INSERT or REPLACE INTO container {user_data.user_input} VALUES (?,?,?,?,?,?,?);",
            (userid, email_address, password, zipcode, report_time, frequency, accept_crowd_sourcing)
        )
        db.connection.commit()
    response = email_object.send_email(recipient=email_address,
                                       subject=f"Welcome to WeatherTogether {datetime.now().strftime('%c')}",
                                       sender="WeatherTogether",
                                       body="Hi,\n\n"
                                            "Thank you for signing up to WeatherTogether. You will now be able to "
                                            f"receive daily weather information at your requested time: {report_time}, "
                                            f"and receive severe weather alerts.\nYou can also login to the "
                                            "WeatherTogether dashboard to broadcast weather alerts.")
    if response.ok:
        logger.info("Subscription confirmation has been sent to %s", email_address)
    return {"OK": "Entry is added to the database successfully"}


def send_otp(email_address: EmailStr):
    rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    response = email_object.send_email(recipient=email_address,
                                       subject=f"WeatherTogether - Verify your email {datetime.now().strftime('%c')}",
                                       sender="WeatherTogether",
                                       body="Hi,\n\n"
                                            "We received a signup request for WeatherTogether Application.\n\n"
                                            "Please enter the code below to sign in: \n\n"
                                            f"{rand_str}\n\n"
                                            "The code will expire in 5 minutes.")
    if response.ok:
        logger.info("One time verification passcode has been sent to %s", email_address)
        otp_dict[email_address] = rand_str
        Thread(target=delete_otp, args=(email_address,)).start()
        return True
    else:
        logger.error(response.body)


def delete_otp(email_address: EmailStr):
    time.sleep(300)
    # otp_dict.pop(email_address)
    # del otp_dict[email_address]
    otp_dict[email_address] = None


def crowd_cast(zipcode: PositiveInt, description, filename, report_url):
    db_data = get_existing_info()
    logger.info("User data gathered from DB")
    notify_zipcodes = []
    for each_entry in db_data:
        user_zip = each_entry[3]
        if user_zip not in notify_zipcodes:
            if find_distance(user_zip, zipcode) <= 3:
                notify_zipcodes.append(user_zip)
    logger.info("No. of zipcodes to notify: %d", len(notify_zipcodes))
    notified_users = []
    for each_entry in db_data:
        user_zip = each_entry[3]
        if user_zip in notify_zipcodes:
            user_id = each_entry[0]
            user_email = each_entry[1]
            acceptance = each_entry[-1]
            if not acceptance or user_email in notified_users:
                continue
            # todo: create a thread to send notifications
            logger.info("Broadcasting to %s", user_email)
            report_url += str(user_id)
            reformed = "Someone near by casted this weather information\n\n\n" + description + \
                       "\n\n\nIf you think this information is inappropriate, please report using the following link:" \
                       f"\n{report_url}"
            if filename:
                response = email_object.send_email(subject=f"Weather Alert {datetime.now().strftime('%c')}",
                                                   sender="WeatherTogether", body=reformed,
                                                   recipient=user_email, attachment=filename)
            else:
                response = email_object.send_email(subject=f"Weather Alert {datetime.now().strftime('%c')}",
                                                   sender="WeatherTogether", body=reformed,
                                                   recipient=user_email)
            if response.ok:
                notified_users.append(user_email)
            logger.info(response.body)
