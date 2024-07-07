# myapp/tasks.py
from celery import shared_task
from .models import Alert
import os
from dotenv import load_dotenv
from .utils import send_alert_email
import requests
import time
import ipdb
from stocks.models import Stock




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


@shared_task
def getStocks(url=f"https://api.polygon.io/v3/reference/tickers?type=CS&market=stocks&active=true&limit=100&apiKey={os.getenv('POLYGON_KEY')}"):
    load_dotenv()
    
    # alerts = Alert.objects.all()
    # for alert in alerts:
    #     #have to upgrade to advanced($200) to see last trade
    #     url = "https://api.polygon.io/v2/last/nbbo/" + alert.symbol + "?apiKey=" + os.getenv('POLYGON_KEY')

    # url = f"https://api.polygon.io/v3/reference/tickers?type=CS&market=stocks&active=true&limit=100&apiKey={os.getenv('POLYGON_KEY')}"
    response = requests.get(url)
    response.json()
    for ticker in response.json()['results']:
        stock = Stock.objects.get_or_create(ticker=ticker['ticker'])
        print(stock)

    time.sleep(30) 

    if response.json()['next_url']:
        getStocks(response.json()['next_url'] + "&apiKey=" + os.getenv('POLYGON_KEY'))

@shared_task
def associateSicToTick():
    load_dotenv()

    for stock in Stock.objects.filter(sic_code=''):
        url = f"https://api.polygon.io/v3/reference/tickers/{stock.ticker}?apiKey={os.getenv('POLYGON_KEY')}"
        response = requests.get(url)  
        sic =  int(response.json().get('results', {}).get('sic_code', '0'))
        stock.sic_code= sic
        stock.save()
        print(sic)
        time.sleep(10)

