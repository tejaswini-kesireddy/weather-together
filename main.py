import json
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime
from multiprocessing import Process

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, UploadFile, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import PositiveInt, EmailStr

from helpers import log, support, tokenizer, bgtasks
from modules.accessories import constants
from modules.database import db


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load the ML model
    logger.info("Initiating background task")
    Process(target=bgtasks.background_task).start()
    yield


app = FastAPI(lifespan=lifespan)
logger = log.logger
templates = Jinja2Templates(directory="UI")


@app.get("/images/{image_name}")
async def images(image_name):
    """This function is dedicated to serving images to the UI."""
    img_path = os.path.join("UI", image_name)
    if os.path.isfile(img_path):
        return FileResponse(path=img_path)
    else:
        logger.error("%s is missing", img_path)


@app.get("/", include_in_schema=False)
async def root():
    """This function redirects root page to docs."""
    return RedirectResponse("/weather")


@app.get("/health")
async def health():
    """This function checks the health of the api"""
    return {"OK": True}


@app.post("/create-alert")
async def create_alert(email_address: EmailStr = Form(...), password: str = Form(...),
                       zipcode: PositiveInt = Form(...),
                       report_time: str = Form(...), frequency: int = Form(None), otp: str = Form(None),
                       accept_crowd_sourcing: bool = Form(True)):
    """This function gets the information from the user."""
    logger.info("Email: %s", email_address)
    logger.info("ZIP Code: %s", zipcode)
    logger.info("Report Time: %s", report_time)
    logger.info("Frequency %s", frequency)
    validation_result = support.validations(email_address, password, zipcode,
                                            report_time, frequency, otp, accept_crowd_sourcing)

    return validation_result


@app.post("/publish-info")
async def publish_info(request: Request, email_address: EmailStr = Form(...), password: str = Form(...),
                       description: str = Form(...), zipcode: PositiveInt = Form(...), image: UploadFile = None):
    """This function gets the information for crowdsourcing"""
    logger.info("Email: %s", email_address)
    logger.info("ZIP Code: %s", zipcode)
    with db.connection:
        cursor = db.connection.cursor()
        retrieve = cursor.execute(
            "SELECT userid, password FROM container WHERE email_address=?;", (email_address,)
        ).fetchone()
    if not retrieve:
        logger.info("not retrieved 404")
        raise HTTPException(status_code=404, detail=f"{email_address} is currently not "
                                                    "subscribed to WeatherTogether")
    sender_id = retrieve[0]
    if sender_id in support.get_blocked():
        raise HTTPException(status_code=403, detail='user blocked')
    stored_pw = tokenizer.hex_decode(retrieve[1])
    if secrets.compare_digest(password, stored_pw):
        logger.info("'%s' with user id '%d' has been authenticated", email_address, sender_id)
    else:
        raise HTTPException(status_code=401, detail="invalid email address or password")
    if not retrieve:
        raise HTTPException(status_code=400, detail="email not found in db: %s" % email_address)
    if not description:
        raise HTTPException(status_code=404, detail="description is required")
    if image:
        extension = image.filename.split(".")[-1]
        file_name = os.path.join("images", str(int(time.time())) + "." + extension)
        with open(file_name, "wb") as file:
            file.write(await image.read())
    else:
        file_name = ""
    report_url = f"{request.base_url}report/{sender_id}/"
    logger.info("Starting bg process for crowdcasting")
    Process(target=support.crowd_cast, args=(zipcode, description, file_name, report_url)).start()
    raise HTTPException(status_code=200, detail="email found: %s" % email_address)


@app.delete(path="/unsubscribe")  # deletes everything rn
async def unsubscribe(email_address: EmailStr = Form(...), password: str = Form(...), everything: bool = True):
    with db.connection:
        logger.info("starting delete")
        cursor = db.connection.cursor()
        retrieve = cursor.execute(
            "SELECT userid, password FROM container WHERE email_address=?;", (email_address,)
        ).fetchone()
        if not retrieve:
            logger.info("not in db")
            raise HTTPException(status_code=404, detail=f"{email_address} is currently not "
                                                        "subscribed to WeatherTogether")
        if secrets.compare_digest(password, tokenizer.hex_decode(retrieve[1])):
            if everything:
                logger.info("delete everything")
                cursor.execute(
                    "DELETE FROM container WHERE email_address=?;", (email_address,)
                )
            else:
                cursor.execute(
                    "UPDATE container SET crowdsource_button=0 WHERE email_address=?;", (email_address,)
                )
            db.connection.commit()
            if everything:
                logger.info("unsubscribe successful for %s", email_address)
                raise HTTPException(status_code=200, detail="Successfully unsubscribed from WeatherTogether")
            else:
                raise HTTPException(status_code=200, detail="CrowdSourcing has been disabled")
        else:
            raise HTTPException(status_code=401, detail="invalid email address or password")


@app.get("/report/{block_id}/{user_id}")
async def report_spam(block_id: str, user_id: str):
    block_id = int(block_id)
    user_id = int(user_id)
    if os.path.isfile(constants.blocked_file):
        with open(constants.blocked_file) as file:
            blocked_already = json.load(file)
        if block_id in blocked_already:
            raise HTTPException(status_code=200, detail="reported user is already blocked")
    if os.path.isfile(constants.report_file):
        with open(constants.report_file) as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
    else:
        data = {}
    if data.get(block_id):
        if user_id in data[block_id]:
            logger.warning("duplicate report on %d by %d", block_id, user_id)
        else:
            data[block_id].append(user_id)
    else:
        data[block_id] = [user_id]
    if len(data[block_id]) >= constants.report_threshold:
        if os.path.isfile(constants.blocked_file):
            with open(constants.blocked_file) as file:
                blocked = json.load(file)
        else:
            blocked = []
        blocked.append(block_id)
        with open(constants.blocked_file, "w") as file:
            json.dump(blocked, file)
        del data[block_id]
        with db.connection:
            cursor = db.connection.cursor()
            retrieve = cursor.execute(
                "SELECT email_address FROM container WHERE userid=?;", (block_id,)
            ).fetchone()
        support.email_object.send_email(recipient=retrieve[0],
                                        subject=f"WeatherTogether - Report received {datetime.now().strftime('%c')}",
                                        sender="WeatherTogether",
                                        body="\n\nDue to multiple reports, you have been blocked from WeatherTogether."
                                             "\n\nYou will no longer be able to receive daily weather reports, "
                                             "severe weather alerts nor will you have the ability to participate in "
                                             "crowd casting")
    with open(constants.report_file, "w") as file:
        yaml.dump(data=data, stream=file, indent=4)
    return {"OK": "User ID reported"}


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("loginPage.html", {"request": request})


@app.post("/login_verify")
async def login_verify(email_address: EmailStr = Form(...), password: str = Form(...)):
    logger.info("logged in as %s", email_address)
    cursor = db.connection.cursor()
    retrieve = cursor.execute(
        "SELECT userid, password FROM container WHERE email_address=?;", (email_address,)
    ).fetchone()
    if not retrieve:
        logger.info("not in db")
        raise HTTPException(status_code=404, detail=f"{email_address} is currently not "
                                                    "subscribed to WeatherTogether")
    db_password = tokenizer.hex_decode(retrieve[1])

    logger.info(db_password)
    if password != db_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"OK": "email and pass are verified"}


@app.get("/weather", response_class=HTMLResponse)
async def confirmation_page(request: Request):
    return templates.TemplateResponse("weather.html", {"request": request})


@app.get("/userHomePage", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("userHomePage.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")
