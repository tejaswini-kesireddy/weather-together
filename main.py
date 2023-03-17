import time

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import EmailStr, PositiveInt

from helpers import validators, log
from modules.accessories import user_data
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


async def validations(email_address: EmailStr, zipcode: PositiveInt, report_time: str, frequency: int):
    """This function validates all the input parameters."""
    zip_valid = await validators.validate_zip(zipcode)
    if not zip_valid:
        raise HTTPException(status_code=400, detail="zipcode is invalid: %d. zipcodes must be 5-digit" % zipcode)
    result = await validators.validate_email_address(email_address)
    if result:
        raise HTTPException(status_code=400, detail="email is invalid: %s. %s" % (email_address, result))
    time_valid = await validators.validate_time(report_time)
    if not time_valid:
        raise HTTPException(status_code=400, detail="time is invalid: %s" % report_time)
    freq_valid = await validators.validate_frequency(frequency)
    if not freq_valid:
        raise HTTPException(status_code=400, detail="frequency is invalid: %s" % frequency)
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute(
            f"INSERT INTO container {user_data.user_input} VALUES (?,?,?,?);",
            (email_address, zipcode, report_time, frequency)
        )
        db.connection.commit()
    return {"OK": "Entry is added to the database successfully"}


@app.post("/create-alert")
async def create_alert(email_address: EmailStr, zipcode: PositiveInt, report_time: str, frequency: int = None):
    """This function gets the information from the user."""
    logger.info("Email: %s", email_address)
    logger.info("ZIP Code: %s", zipcode)
    logger.info("Report Time: %s", report_time)
    logger.info("Frequency %s", frequency)
    validation_result = await validations(email_address, zipcode, report_time, frequency)
    return validation_result


@app.post("/publish-info")
async def publish_info(email_address: EmailStr, description: str, image: UploadFile = None):
    """This function gets the information for crowd sourcing"""
    with db.connection:
        cursor = db.connection.cursor()
        retrieve = cursor.execute(
            "SELECT * FROM container WHERE email_address=?;", (email_address,)
        ).fetchall()

    if not retrieve:
        raise HTTPException(status_code=400, detail="email not found in db: %s" % email_address)
    if not image and not description:
        raise HTTPException(status_code=404, detail="either image or description is required")
    extension = image.filename.split(".")[-1]
    file_name = str(int(time.time())) + "." + extension
    with open(file_name, "wb") as file:
        file.write(await image.read())
    raise HTTPException(status_code=200, detail="email found: %s" % email_address)


if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")
