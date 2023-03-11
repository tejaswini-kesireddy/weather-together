import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from pydantic import EmailStr, PositiveInt

from helpers import validators, log
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
    db.connection.execute(
        "INSERT INTO container ('email_address', 'zipcode', 'report_time', 'frequency') VALUES (?,?,?,?);",
        (email_address, zipcode, report_time, frequency)
    )
    db.connection.commit()
    return {"OK": "Entry is added to the database successfully"}


@app.post("/create-alert")
async def user_data(email_address: EmailStr, zipcode: PositiveInt, report_time: str, frequency: int = None):
    """This function gets the information from the user."""
    logger.info("Email: %s", email_address)
    logger.info("ZIP Code: %s", zipcode)
    logger.info("Report Time: %s", report_time)
    logger.info("Frequency %s", frequency)
    validation_result = await validations(email_address, zipcode, report_time, frequency)
    return validation_result


if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")
