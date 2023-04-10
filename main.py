import os
import random
import string
import time
from threading import Thread

import gmailconnector
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import EmailStr, PositiveInt

from helpers import validators, log
from helpers.location import find_distance
from modules.accessories import user_data, otp_dict
from modules.database import db, get_existing_info

app = FastAPI()
logger = log.logger

email_object = gmailconnector.SendEmail(gmail_user=os.environ.get("EMAIL_USERNAME"),
                                        gmail_pass=os.environ.get("EMAIL_PASSWORD"))


@app.get("/", include_in_schema=False)
async def root():
    """This function redirects root page to docs."""
    return RedirectResponse("/docs")


@app.get("/health")
async def health():
    """This function checks the health of the api"""
    return {"OK": True}


def validations(email_address: EmailStr, zipcode: PositiveInt, report_time: str, frequency: int, otp: str,
                accept_crowd_sourcing: bool):
    """This function validates all the input parameters."""
    zip_valid = validators.validate_zip(zipcode)
    if not zip_valid:
        raise HTTPException(status_code=400, detail="zipcode is invalid: %d. zipcodes must be 5-digit" % zipcode)
    result = validators.validate_email_address(email_address)
    if result:
        raise HTTPException(status_code=400, detail="email is invalid: %s. %s" % (email_address, result))
    time_valid = validators.validate_time(report_time)
    if not time_valid:
        raise HTTPException(status_code=400, detail="time is invalid: %s" % report_time)
    freq_valid = validators.validate_frequency(frequency)
    if not freq_valid:
        raise HTTPException(status_code=400, detail="frequency is invalid: %s" % frequency)
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
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute(
            f"INSERT or REPLACE INTO container {user_data.user_input} VALUES (?,?,?,?,?);",
            (email_address, zipcode, report_time, frequency, accept_crowd_sourcing)
        )
        db.connection.commit()
    return {"OK": "Entry is added to the database successfully"}


def send_otp(email_address: EmailStr):
    rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    response = email_object.send_email(recipient=email_address, subject='WeatherTogether - Verify your email',
                                       sender="WeatherTogether",
                                       body=f"Your WeatherTogether verification code is:{rand_str}\n\n"
                                            "This verification code will expire in 5 minutes.")
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


@app.post("/create-alert")
async def create_alert(email_address: EmailStr, zipcode: PositiveInt, report_time: str,
                       frequency: int = None, otp: str = None, accept_crowd_sourcing: bool = True):
    """This function gets the information from the user."""
    logger.info("Email: %s", email_address)
    logger.info("ZIP Code: %s", zipcode)
    logger.info("Report Time: %s", report_time)
    logger.info("Frequency %s", frequency)
    validation_result = validations(email_address, zipcode, report_time, frequency, otp, accept_crowd_sourcing)
    return validation_result


@app.post("/publish-info")
async def publish_info(email_address: EmailStr, description: str, zipcode: PositiveInt, otp: str = None,
                       image: UploadFile = None):
    """This function gets the information for crowd sourcing"""
    with db.connection:
        cursor = db.connection.cursor()
        retrieve = cursor.execute(
            "SELECT * FROM container WHERE email_address=?;", (email_address,)
        ).fetchall()

    if not retrieve:
        raise HTTPException(status_code=400, detail="email not found in db: %s" % email_address)
    if not description:
        raise HTTPException(status_code=404, detail="description is required")
    if otp:
        if otp == otp_dict.get(email_address):
            logger.info("%s passed OTP validation", email_address)
        else:
            raise HTTPException(status_code=401, detail="unauthorized")
    else:
        if send_otp(email_address):
            logger.info("OTP has been sent")
            return {"OK": "Please enter the OTP"}
        else:
            raise HTTPException(status_code=500, detail="failed to send otp")

    if image:
        extension = image.filename.split(".")[-1]
        # todo: create a thread to send notifications
        # todo: notifications should contain a user ID, if needed to report
        file_name = os.path.join("images", str(int(time.time())) + "." + extension)
        with open(file_name, "wb") as file:
            file.write(await image.read())
    else:
        file_name = ""
    crowd_cast(zipcode, description, file_name)
    raise HTTPException(status_code=200, detail="email found: %s" % email_address)


def crowd_cast(zipcode: PositiveInt, description, filename):
    db_data = get_existing_info()
    notify_zipcodes = []
    for each_entry in db_data:
        user_zip = each_entry[1]
        if user_zip not in notify_zipcodes:
            if find_distance(user_zip, zipcode) <= 3:
                notify_zipcodes.append(user_zip)
    notified_users = []
    for each_entry in db_data:
        user_zip = each_entry[1]
        if user_zip in notify_zipcodes:
            user_email = each_entry[0]
            acceptance = each_entry[-1]
            if not acceptance or user_email in notified_users:
                continue
            if filename:
                response = email_object.send_email(subject="Weather Alert", sender="WeatherTogether", body=description,
                                                   recipient=user_email, attachment=filename)
            else:
                response = email_object.send_email(subject="Weather Alert", sender="WeatherTogether", body=description,
                                                   recipient=user_email)
            if response.ok:
                notified_users.append(user_email)
            logger.info(response.body)


if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")
