from django.shortcuts import render
from django.http import JsonResponse
import requests
import ipdb
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import urllib, base64
import io
from datetime import date, datetime, timedelta
from .forms import StockTickerForm, DateRangeForm

# Create your views here.
def stock_index_view(request):
    load_dotenv()
    ticker_info = None
    error_message = None

    if request.method == 'POST':
        form = StockTickerForm(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data['ticker']
        url = f"https://api.polygon.io/v3/reference/tickers?search={ticker}&active=true&limit=100&apiKey=" + os.getenv('POLYGON_KEY')
        try:
            response = requests.get(url)
            response.raise_for_status()
            # ipdb.set_trace()
            ticker_info = response.json()['results']
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        form = StockTickerForm()

    return render(request, 'stocks.html', {'form': form, 'ticker_info': ticker_info, 'error_message': error_message})
    
def stock_detail(request, slug):
    slug = slug.upper()
    load_dotenv()
    days = request.GET.get('days', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)
    today = date.today().strftime("%Y-%m-%d")
    form = DateRangeForm()
    if(days):
        days_ago =  (datetime.now() - timedelta(days=int(days))).strftime('%Y-%m-%d')
        url = "https://api.polygon.io/v2/aggs/ticker/" + slug + "/range/1/day/" + days_ago + '/' + today + "?sort=asc&apiKey=" + os.getenv('POLYGON_KEY')
    elif(end_date and start_date):
        url = "https://api.polygon.io/v2/aggs/ticker/" + slug + "/range/1/day/" + start_date + '/' + end_date + "?sort=asc&apiKey=" + os.getenv('POLYGON_KEY')
    else: 
        url = "https://api.polygon.io/v2/aggs/ticker/" + slug + "/range/1/day/2023-03-13/2024-03-14?sort=asc&apiKey=" + os.getenv('POLYGON_KEY')

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        uri = generate_stock_chart(data)
        return render(request, 'stock_detail.html', 
                      {'chart_uri': uri, 
                       'form': form,
                       'stock': slug})
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def generate_stock_chart(data):
    stock_values = [item['c'] for item in data['results']]
    x_values = range(len(stock_values))
    plt.figure(figsize=(10, 5))
    plt.plot(x_values, stock_values, marker='o')
    plt.title('Stock Values Over Time')
    plt.xlabel('Open Days')
    plt.ylabel('Stock Value')
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    return urllib.parse.quote(string)

def fetch_stock_data(start_date, end_date):
    # Replace with your actual API endpoint and parameters
    api_url = "https://api.example.com/stock_data"
    params = {
        'start_date': start_date,
        'end_date': end_date,
    }
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        return response.json()
    return None