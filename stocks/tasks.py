# myapp/tasks.py
from celery import shared_task
from .models import Alert
import os
from dotenv import load_dotenv
from .utils import send_alert_email
import requests
import time


@shared_task
def when_wealthy():
    load_dotenv()
    alerts = Alert.objects.all()
    for alert in alerts:
        #have to upgrade to advanced($200) to see last trade
        url = "https://api.polygon.io/v2/last/nbbo/" + alert.symbol + "?apiKey=" + os.getenv('POLYGON_KEY')
        response = requests.get(url)
        print(response)

@shared_task
def morning_stock_check():
    load_dotenv()
    print('IN morning_stock_check')
    alerts = Alert.objects.all()
    batch_size = 5
    api_key = os.getenv('POLYGON_KEY')

    # range because api calls limited to 5 per minute
    alert_recommendations = []
    for i in range(0, len(alerts), batch_size):
        batch = alerts[i:i + batch_size]
        for alert in batch:
            url = f"https://api.polygon.io/v2/aggs/ticker/{alert.symbol}/prev?apiKey={api_key}"
            
            response_json = requests.get(url).json()
            print(response_json['results'][0])
            if(alert.price > response_json['results'][0]['c']):
                alert_recommendations.append(alert.symbol)
        time.sleep(60) 
    # CAN set up twilio or a similar service to receive texts or emails 
    send_alert_email('john.osborne.odom@gmail.com', 'BUY', "ALERT RECOMMENDATIONS: " + ', '.join(alert_recommendations))
    # return alert_recommendations
