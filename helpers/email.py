import smtplib
import ssl
#from helpers import weather
import weather
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timezone
#import modules.database


#from modules.database import  get_existing_info
#

def send_daily_email(zip):
    
    subject='Here is Todays Weather Forecast'
    today = datetime.now(timezone.utc).strftime('%d-%m-%y')#get todays date
    hourly_weather, todays_description, todays_low, todays_high,alerts =weather.get_weather(zip, mock=False)# get the weather
    body="<p><span style='font-weight:bold; color:blue'> Today "+str(today)+"</span> "+todays_description+" with a high of "+ str(todays_high)+" °F and a low of "+str(todays_low)+" °F"
    
    for x in hourly_weather:
        for i, s in enumerate(x): 
            if (i==0):
                body += "<p style='font-weight:bold;color:blue'>"+s+"  -> "
            else:
                body += "<span style='font-weight:normal; color:black'> "+str(s) +" </span>"
        body +="</p>"  
    send_email(subject, body)
   
    
    
    
def send_alerts(zip):
    #hourly_weather, todays_description, todays_low, todays_high,
    body=""
    subject=""
    hourly_weather, todays_description, todays_low, todays_high,alerts = weather.get_weather(zip, mock=False)
    if alerts:
        print(alerts)
        for alert in alerts:
            sender= alert['sender_name']
            alert_description = alert["description"]
            event = alert["event"]
            if (subject!=""):
                subject+=" and "
            subject+=event
            
            body+= "<p style='font-weight:bold;color:black;'>"+event+":</br>"+alert_description+"</p>"
            body+=sender
        send_email(subject, body)

def send_email(subject, body):
    me = os.environ.get("EMAIL_USERNAME")
    passw = os.environ.get("EMAIL_PASSWORD") 
    #****enter your email or emails in to******************
    to=['jasoncariolano@gmail.com']#TODO:get saved email address
       
    em = MIMEMultipart()
    em['From']=me
    em['TO']=', '.join(to)
    em['Subject']= subject
    em.attach(MIMEText(body, 'html'))#set content

    context=ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(me,passw)
        smtp.sendmail(me,to,em.as_string())
        
    
    
if __name__ == "__main__":
    send_daily_email("65807")
    send_alerts("65807") #54605 has severe weather today
