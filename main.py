import os
import secrets
import time
from multiprocessing import Process

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.responses import RedirectResponse
from pydantic import PositiveInt, EmailStr

from helpers import log, support
from modules.accessories import CreateAlert
from modules.database import db

app = FastAPI()
logger = log.logger


@app.get("/", include_in_schema=False)
async def root():
    """This function redirects root page to docs."""
    return RedirectResponse("/docs")


@app.get("/health")
async def health():
    """This function checks the health of the api"""
    return {"OK": True}


@app.post("/create-alert")
async def create_alert(userdata: CreateAlert):
    """This function gets the information from the user."""
    logger.info("Email: %s", userdata.email_address)
    logger.info("ZIP Code: %s", userdata.zipcode)
    logger.info("Report Time: %s", userdata.report_time)
    logger.info("Frequency %s", userdata.frequency)
    validation_result = support.validations(userdata.email_address, userdata.password, userdata.zipcode,
                                            userdata.report_time, userdata.frequency, userdata.otp,
                                            userdata.accept_crowd_sourcing)
    return validation_result


@app.post("/publish-info")
async def publish_info(email_address: str = Form(...), password: str = Form(...), description: str = Form(...),
                       zipcode: PositiveInt = Form(...), image: UploadFile = None):
    """This function gets the information for crowdsourcing"""
    with db.connection:
        cursor = db.connection.cursor()
        retrieve = cursor.execute(
            "SELECT userid, password FROM container WHERE email_address=?;", (email_address,)
        ).fetchone()
    if not retrieve:
        raise HTTPException(status_code=404, detail=f"{email_address} is currently not "
                                                    "subscribed to WeatherTogether")
    sender_id = retrieve[0]
    if secrets.compare_digest(password, retrieve[1]):
        logger.info("'%s' with user id '%d' has been authenticated", email_address, sender_id)
    else:
        raise HTTPException(status_code=401, detail="invalid email address or password")
    if not retrieve:
        raise HTTPException(status_code=400, detail="email not found in db: %s" % email_address)
    if not description:
        raise HTTPException(status_code=404, detail="description is required")
    # todo: encrypt and decrypt password
    #  generate a link to report spam
    if image:
        extension = image.filename.split(".")[-1]
        # todo: notifications should contain a user ID, if needed to report
        file_name = os.path.join("images", str(int(time.time())) + "." + extension)
        with open(file_name, "wb") as file:
            file.write(await image.read())
    else:
        file_name = ""
    Process(target=support.crowd_cast, args=(zipcode, description, file_name, sender_id)).start()
    raise HTTPException(status_code=200, detail="email found: %s" % email_address)


@app.delete(path="/unsubscribe")
async def unsubscribe(email_address: EmailStr = Form(...), password: str = Form(...), everything: bool = False):
    with db.connection:
        cursor = db.connection.cursor()
        retrieve = cursor.execute(
            "SELECT userid, password FROM container WHERE email_address=?;", (email_address,)
        ).fetchone()
        if not retrieve:
            raise HTTPException(status_code=404, detail=f"{email_address} is currently not "
                                                        "subscribed to WeatherTogether")
        if secrets.compare_digest(password, retrieve[1]):
            if everything:
                cursor.execute(
                    "DELETE FROM container WHERE email_address=?;", (email_address,)
                )
            else:
                cursor.execute(
                    "UPDATE container SET crowdsource_button=0 WHERE email_address=?;", (email_address,)
                )
            db.connection.commit()
            if everything:
                raise HTTPException(status_code=200, detail="Successfully unsubscribed from WeatherTogether")
            else:
                raise HTTPException(status_code=200, detail="CrowdSourcing has been disabled")
        else:
            raise HTTPException(status_code=401, detail="invalid email address or password")


if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")
