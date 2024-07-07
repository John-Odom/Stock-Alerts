from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
import requests
import ipdb
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import urllib, base64
import io
from io import BytesIO
from datetime import date, datetime, timedelta
from django.contrib.auth.decorators import login_required
from .forms import StockTickerForm, DateRangeForm, AlertForm
from .models import Alert
from .stock_split import StockSplit

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
        paginator = Paginator(stock_list, 10)
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
    alert_form = AlertForm()
    
    if request.method == 'POST':
        alert_form = AlertForm(request.POST)
        if alert_form.is_valid():
            alert = alert_form.save(commit=False)
            alert.user = request.user
            alert.symbol = slug
            alert.save()
            return redirect('stocks:alerts')
    
    if days:
        days_ago = (datetime.now() - timedelta(days=int(days))).strftime('%Y-%m-%d')
        url = "https://api.polygon.io/v2/aggs/ticker/" + slug + "/range/1/day/" + days_ago + '/' + today + "?sort=asc&apiKey=" + os.getenv('POLYGON_KEY')
    elif(end_date and start_date):
        url = "https://api.polygon.io/v2/aggs/ticker/" + slug + "/range/1/day/" + start_date + '/' + end_date + "?sort=asc&apiKey=" + os.getenv('POLYGON_KEY')
    else: 
        url = "https://api.polygon.io/v2/aggs/ticker/" + slug + "/range/1/day/2023-03-13/2025-06-14?sort=asc&apiKey=" + os.getenv('POLYGON_KEY')

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        stock = info_query(slug)
        splits = stock_splits(slug)
        financials = financials_query(slug)
        print(stock['name'])
        return render(request, 'stock_detail.html', 
                      {'chart_uri': generate_stock_chart(data), 
                       'form': form,
                       'alert_form': alert_form,
                       'name': stock['name'],
                       'price': price(data),
                       'description': stock.get('description', ''),
                       'state': stock.get('address', {}).get('state', ''),
                       'market_cap':"${:,.2f}".format(stock.get('market_cap', 0)),
                       'shares_outstanding': stock.get('share_class_shares_outstanding'),
                       'ticker': stock.get('ticker'),
                       'alerts': request.user.alerts.filter(symbol=slug),
                       'eps_graph': stock_eps(financials, splits),
                       'pe_ratio': calculate_pe_ratio(financials),
                       'news': getStockNews(slug)
                       })
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)


def stock_splits(slug):
    url = f"https://api.polygon.io/v3/reference/splits?ticker={slug}&limit=10&apiKey={os.getenv('POLYGON_KEY')}"
    response = requests.get(url)
    splits = []
    for stock_split in response.json()['results']:
        splits.append(StockSplit(date= stock_split['execution_date'], ratio=(stock_split['split_to'] / stock_split['split_from'])))
    
    # ipdb.set_trace()
    return splits

def delete_alert(request, id):
    if request.method == 'POST':
        alert = get_object_or_404(Alert, id=id)
        alert.delete()
    return redirect('stocks:alerts')  # Replace 'alerts_view' with the name of your alerts view

def getStockNews(slug):
    url = f"https://api.polygon.io/v2/reference/news?ticker={slug}&limit=10&apiKey=i91hbXrlrH8yM71UexYN_I4nsRX7pKir"
    response = requests.get(url)

    return response.json()['results']

@login_required(login_url="/account/login")
def alerts(request):
    alerts = Alert.objects.filter(user=request.user)
    return render(request, 'alerts.html', {'alerts': alerts})
    
    
def info_query(slug):
    url = f"https://api.polygon.io/v3/reference/tickers/{slug}?apiKey=i91hbXrlrH8yM71UexYN_I4nsRX7pKir"
    response = requests.get(url)  
    # use SIC codes to determine sector
    return response.json()['results']

def financials_query(slug):
    url = f"https://api.polygon.io/vX/reference/financials?ticker={slug}&limit=20&timeframe=quarterly&apiKey=i91hbXrlrH8yM71UexYN_I4nsRX7pKir"
    # url = f"https://api.polygon.io/v3/reference/tickers/{slug}?apiKey=i91hbXrlrH8yM71UexYN_I4nsRX7pKir"
    response = requests.get(url)  
    
    return response.json()['results']

def price(data):

    results = data.get('results', [])
    if len(results) > 0:
        last_close = results[-1]
        return f"${last_close['c']}"
    else:
        return "Unknown"

def stock_eps(financials, splits):
    eps_values = []
    dates = []
    financials = sorted(financials, key=lambda x: datetime.strptime(x['start_date'], '%Y-%m-%d'))

    for item in financials:

        filing_date = datetime.strptime(item['end_date'], '%Y-%m-%d')
        financial_info = item.get('financials', {})
        income_statement = financial_info.get('income_statement', {})
        basic_eps = income_statement.get('basic_earnings_per_share', {}).get('value', None)

        # ipdb.set_trace()

        for split in splits:
            # ipdb.set_trace()
            if datetime.strptime(split.date, '%Y-%m-%d') > filing_date:
                basic_eps /= split.ratio

        # ipdb.set_trace()
        # item['financials']['income_statement']['basic_earnings_per_share']['value'] = basic_eps

        if basic_eps is not None:
            eps_values.append(basic_eps)
            dates.append(item.get('end_date'))
    
    # Generate the chart
    plt.figure(figsize=(10, 5))
    plt.plot(dates, eps_values, marker='o')
    plt.title('EPS - Last 20 Quarters')
    plt.xlabel('Date')
    plt.ylabel('EPS')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the chart to a BytesIO object
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Encode the image to base64 string
    graph = base64.b64encode(image_png)
    return graph.decode('utf-8')

# def stock_pe_ratios(financials):
#     pe_ratios = []
#     dates = []
#     financials = sorted(financials, key=lambda x: datetime.strptime(x['start_date'], '%Y-%m-%d'))

#     for item in financials:
#         financial_info = item.get('financials', {})
#         income_statement = financial_info.get('income_statement', {})
#         basic_eps = income_statement.get('basic_earnings_per_share', {}).get('value', None)
#         revenues = income_statement.get('revenues', {}).get('value', None)
        
#         if basic_eps and revenues:
#             pe_ratio = revenues / basic_eps
#             pe_ratios.append(pe_ratio)
#             dates.append(item.get('start_date'))
    
#     # Generate the chart
#     plt.figure(figsize=(10, 5))
#     plt.plot(dates, pe_ratios, marker='o')
#     plt.title(f'PE Ratio - Last 20 Quarters')
#     plt.xlabel('Date')
#     plt.ylabel('PE Ratio')
#     plt.xticks(rotation=45)
#     plt.tight_layout()
    
#     # Save the chart to a BytesIO object
#     buffer = BytesIO()
#     plt.savefig(buffer, format='png')
#     buffer.seek(0)
#     image_png = buffer.getvalue()
#     buffer.close()
    
#     # Encode the image to base64 string
#     graph = base64.b64encode(image_png)
#     return graph.decode('utf-8')

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

def calculate_pe_ratio(financials):
    financials = sorted(financials, key=lambda x: datetime.strptime(x['start_date'], '%Y-%m-%d'))

    annual_eps = 0
    for report in financials[-4:]:
        eps = report.get('financials', {}).get('income_statement', {}).get('basic_earnings_per_share', {}).get('value', 'N/A')
        annual_eps += eps
    print(annual_eps)
    # url = f"https://api.polygon.io/vX/reference/financials?ticker={slug}&limit=1&timeframe=annual&apiKey=i91hbXrlrH8yM71UexYN_I4nsRX7pKir"
    # # url = f"https://api.polygon.io/v3/reference/tickers/{slug}?apiKey=i91hbXrlrH8yM71UexYN_I4nsRX7pKir"
    # response = requests.get(url)  
    # return response.json()['results'][0]



# {'ticker': 'NVDA', 'name': 'Nvidia Corp', 'market': 'stocks', 'locale': 'us', 'primary_exchange': 'XNAS', 'type': 'CS', 'active': True, 'currency_name': 'usd', 'cik': '0001045810', 'composite_figi': 'BBG000BBJQV0', 'share_class_figi': 'BBG001S5TZJ6', 'market_cap': 3038879166973.8003, 'phone_number': '408-486-2000', 'address': {'address1': '2788 SAN TOMAS EXPRESSWAY', 'city': 'SANTA CLARA', 'state': 'CA', 'postal_code': '95051'}, 'description': 'Nvidia is a leading developer of graphics processing units. Traditionally, GPUs were used to enhance the experience on computing platforms, most notably in gaming applications on PCs. GPU use cases have since emerged as important semiconductors used in artificial intelligence. Nvidia not only offers AI GPUs, but also a software platform, Cuda, used for AI model development and training. Nvidia is also expanding its data center networking solutions, helping to tie GPUs together to handle complex workloads.', 'sic_code': '3674', 'sic_description': 'SEMICONDUCTORS & RELATED DEVICES', 'ticker_root': 'NVDA', 'homepage_url': 'https://www.nvidia.com', 'total_employees': 29600, 'list_date': '1999-01-22', 'branding': {'logo_url': 'https://api.polygon.io/v1/reference/company-branding/bnZpZGlhLmNvbQ/images/2024-06-01_logo.svg', 'icon_url': 'https://api.polygon.io/v1/reference/company-branding/bnZpZGlhLmNvbQ/images/2024-06-01_icon.png'}, 'share_class_shares_outstanding': 24598340000, 'weighted_shares_outstanding': 24598341970, 'round_lot': 100}