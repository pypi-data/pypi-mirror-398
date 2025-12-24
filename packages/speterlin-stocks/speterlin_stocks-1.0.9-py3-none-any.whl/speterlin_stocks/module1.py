# global objects (API clients, config, globals)
# alpaca_api = None
# FMP_API_KEY = None
# google_gemini_pro_model = None
# twilio_client = None
# twilio_phone_to = None
# twilio_phone_from = None
# portfolio_account = None # maybe add portfolio_name later for more consistent logic

# unused since not 'from .module1 import *' in __init__.py
__all__ = [
    "_fetch_data",
    "trendline",
    # "get_zacks_data",
    "get_ticker_data_quote_fmp",
    "get_ticker_data_granular_fmp",
    "get_ticker_data_fmp",
    "get_ticker_balance_sheet_data_fmp",
    "get_ticker_stock_news_articles_fmp",
    "get_daily_stock_gainers_fmp",
    "get_tickers_with_stock_splits_in_85_days_period_fmp",
    "get_tickers_with_stock_splits_in_period_fmp",
    "get_tickers_with_stock_splits_fmp",
    # "get_etf_constituents_fmp",
    "get_senate_trading_symbol_fmp",
    # "get_ticker_data_yf",
    # "get_ticker_data_detailed_yfinance",
    # "get_tickers_with_stock_splits_in_day_yfinance",
    # "get_tickers_with_stock_splits_in_period_yfinance",
    # "get_exchange_rates_exchangerate",
    # "get_ticker_data_detailed_gfinance",
    # "openai_functions", # array of functions
    # "should_I_buy_the_stock_openai",
    "should_I_buy_the_stock_google_gemini_pro",
    "extract_investment_recommendation",
    "extract_investment_recommendation_2",
    "get_google_trends_pt", # replaces "get_cryptory",
    "get_saved_tickers_data",
    # "save_usa_tv_tickers_zacks_data",
    "save_tickers_yf_and_fmp_data",
    "save_tickers_daily_gainers_fmp",
    "save_usa_alpaca_tickers_fmp_data",
    # "get_crunchbase_search_permalinks",
    # "get_crunchbase_permalink_site_check_ticker",
    # "get_crunchbase_data_for_ticker",
    "alpaca_trade_ticker",
    "get_alpaca_assets",
    "fmp_check_24h_vol",
    "update_portfolio_postions_back_testing",
    "get_tickers_to_avoid_in_alpaca",
    "get_tickers_to_avoid",
    "update_portfolio_buy_and_sell_tickers",
    "get_sp500_ranked_tickers_by_slickcharts",
    # "get_sp500_ranked_tickers_by_marketbeat",
    "run_portfolio",
    "check_for_basic_errors_and_set_general_params_for_run_portfolio",
    "run_portfolio_zr",
    "run_portfolio_rr",
    "run_portfolio_tilupccu",
    "run_portfolio_mmtv",
    "run_portfolio_random_sp500",
    "run_portfolio_mm",
    "run_portfolio_ai_recommendations_in_sector",
    "run_portfolio_top_n_gainers_ai_analysis",
    "senate_timestamps_and_tickers_inflows_and_outflows_by_month_for_stocks",
    "run_portfolio_senate_trading",
    "run_portfolio_sma_mm",
    "portfolio_align_prices_with_alpaca",
    "portfolio_align_buying_power_with_alpaca",
    "portfolio_calculate_roi",
    "sleep_until_30_min",
    "portfolio_panic_sell",
    "retry_alpaca_open_orders_in_portfolio",
    "retry_atrade_error_or_paper_orders_in_portfolio",
    "portfolio_trading",
    "save_portfolio_backup",
    "get_saved_portfolio_backup",
]

import requests
import time

# ~same as in eventregistry/quant-trading/crypto.py # maybe refactor name to _fetch_or_push_data, pushing data is unique for when sending orders to exchange so probably not that important
# need to have ndg-httpsclient, pyopenssl, and pyasn1 (latter 2 are normally already installed) installed to deal with Caused by SSLError(SSLError("bad handshake: SysCallError(60, 'ETIMEDOUT')",),) according to https://stackoverflow.com/questions/33410577 (should also check tls_version and maybe unset https_proxy from commandline), but doesn't seem to work (might also be because requests removed 3DES from default cipher suite list: github.com/psf/requests/issues/4193), but error is escaped when fetching zacks data (so far only issue is with yahoo finance - maybe because yahoo finance api has a 2,000 API calls per hour limit)
def _fetch_data(func, params, error_str, empty_data, retry=True):
    try:
        data = func(**params)
    except (ValueError, TypeError) as e:
        print(str(e) + error_str)
        data = empty_data
    except Exception as e:
        print(str(e) + error_str)
        data = empty_data
        if retry and ((type(e) in [UnboundLocalError, TimeoutError, RuntimeError, requests.exceptions.ConnectionError, requests.exceptions.TooManyRedirects]) or (type(e) is requests.exceptions.HTTPError and e.response.status_code == 429)): # UnboundLocalError because of response error (local variable 'response' referenced before assignment), if use urllib for request TimeoutError is urllib.error.URLError: <urlopen error [Errno 60] Operation timed out>, requests.exceptions.ConnectionError is for (even when not using urllib): NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x119429240>: Failed to establish a new connection: [Errno 60] Operation timed out and: requests.exceptions.ConnectionError: ('Connection aborted.', OSError("(54, 'ECONNRESET')",)), currently unresolved - (even when not using urllib): Max retries exceeded with url: /?t=PD (Caused by OpenSSL.SSL.SysCallError/SSLError(SSLError("bad handshake: SysCallError(50/54/60, 'ENETDOWN'/'ETIMEDOUT'/'ECONNRESET')",)
            time.sleep(60) # CoinGecko has limit of 100 requests/minute therefore sleep for a minute, unsure of request limit for Google Trends
            data = _fetch_data(func, params, error_str, empty_data, retry=False)
    return data

import numpy as np

# data is dataframe column series, same as in crypto.py
def trendline(data, order=1, reverse_to_ascending=False):
    data_index_values = data.index.values[::-1] if reverse_to_ascending else data.index.values
    coeffs = np.polyfit(data_index_values, list(data), order)
    slope = coeffs[-2]
    return float(slope)

def get_zacks_data(ticker=None):
    # zacks rank, can also do motley fool, found from github.com/janlukasschroeder/zacks-api
    # proxies = {'http':'http://localhost:port','https':'http://localhost:port'}
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10 7 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'} #
    resp = requests.get("https://quote-feed.zacks.com/?t=" + ticker, headers=headers, verify=False) # proxies=proxies, #) # , verify=False # can add installing openssl: https://stackoverflow.com/questions/51768496/why-do-https-requests-produce-ssl-certificate-verify-failed-error, https://www.google.com/search?q=browser+request+vs.+python+requests.get&oq=browser+request+vs.+python+requests.get&aqs=chrome..69i57.8276j0j7&sourceid=chrome&ie=UTF-8
    data = resp.json()
    return data

import pandas as pd
import json
from datetime import datetime, timedelta

def get_ticker_data_quote_fmp(ticker):  # maybe refactor add real_time to name
    # global FMP_API_KEY
    data = {}
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v3/quote/{ticker}\
                ?apikey={FMP_API_KEY}".replace(" ", "") # https://financialmodelingprep.com/api/v3/profile/{ticker}\?apikey=
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # results are in descending order (most recent date first) # [0] - assuming r.text is return as a list
    df = pd.DataFrame(data)
    df.set_index('symbol', inplace=True)
    return df

# support inquiry (FMP): Our data is aligned with NASDAQ data. Some ETFs are listed different in FMP / Yahoo Finance than Alpaca like 'BRK-B' (FMP / Yahoo Finance) vs. 'BRK.B' (Alpaca)
def get_ticker_data_granular_fmp(ticker, start_datetime=None, end_datetime=None, interval="1hour"): # interval values: 1min, 5min, 15min, 30min, 1hour, 4hour, supposedly 1day works but not listed on api documents
    # global FMP_API_KEY
    data = []
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v3/historical-chart/{interval}/{ticker}?from={start_datetime.strftime('%Y-%m-%d')}&to={end_datetime.strftime('%Y-%m-%d')}\
                &apikey={FMP_API_KEY}".replace(" ", "") # https://financialmodelingprep.com/api/v3/profile/{ticker}\?apikey=
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # results are in descending order (most recent date first) # [0] - assuming r.text is return as a list
    # no need here and other fmp calls to return pd.DataFrame() since called in _fetch_data()
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    df.index.rename("Date",inplace=True)
    df = df.sort_values('Date', ascending=True, inplace=False)
    return df

# using this / historical-price-full instead of get_ticker_data_granular_fmp / historical-chart with interval="4hour" because no full day interval (listed on API) for historical-chart and more potential useful data points
def get_ticker_data_fmp(ticker, start_datetime=None, end_datetime=None): # Both this function and above work with 6 years data, API documentation: By default the limit is 5 years of historical data, to get data prior to this date, please use the to & from parameters with a limit of 5 years. # support inquiry (FMP): You can change the “From” and “To” parameters to get past data, but due to the sheer size and volume of the intraday historical chart data, there are limits to the number of records that can be returned in a given query. I recommend querying no more than 1500 records per query
    # global FMP_API_KEY
    data = {}
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={start_datetime.strftime('%Y-%m-%d')}&to={end_datetime.strftime('%Y-%m-%d')}\
                &apikey={FMP_API_KEY}".replace(" ", "") # https://financialmodelingprep.com/api/v3/profile/{ticker}\?apikey=
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # results are in descending order (most recent date first) # [0] - assuming r.text is return as a list
    df = pd.DataFrame(data['historical'])
    df.set_index('date', inplace=True)
    df.index.rename("Date",inplace=True)
    df = df.sort_values('Date', ascending=True, inplace=False)
    return df

def get_ticker_data_detailed_fmp(ticker): # maybe refactor add real_time to name
    # global FMP_API_KEY
    data = {}
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v4/company-outlook?symbol={ticker}\
                &apikey={FMP_API_KEY}".replace(" ", "") # https://financialmodelingprep.com/api/v3/profile/{ticker}\?apikey=
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # [0] - assuming r.text is return as a list
    return data

def get_ticker_balance_sheet_data_fmp(ticker, period="annual"):
    # global FMP_API_KEY
    data = []
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period={period}\
                &apikey={FMP_API_KEY}".replace(" ", "") # https://financialmodelingprep.com/api/v3/profile/{ticker}\?apikey=
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # [0] - assuming r.text is return as a list
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    df.index.rename("Date",inplace=True)
    df = df.dropna(how="any")
    return df

def get_ticker_stock_news_articles_fmp(ticker, limit=5): # maybe refactor add real_time to name
    # global FMP_API_KEY
    data = []
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={ticker}&limit={limit}\
                &apikey={FMP_API_KEY}".replace(" ", "")
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # [0] - assuming r.text is return as a list
    df = pd.DataFrame(data)
    df.set_index('publishedDate', inplace=True)
    df.index.rename("Published Date",inplace=True)
    df = df.dropna(how="any") # drops missing values
    return df

def get_daily_stock_gainers_fmp(): # maybe refactor add real_time to name
    # global FMP_API_KEY
    data = []
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?\
                &apikey={FMP_API_KEY}".replace(" ", "")
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # [0] - assuming r.text is return as a list
    df = pd.DataFrame(data)
    df = df.dropna(how="any") # drops missing values
    return df

def get_tickers_with_stock_splits_in_85_days_period_fmp(start_datetime=None, end_datetime=None): # only works for span of ~85 days (including weekends) just under 3 months span
    # global FMP_API_KEY
    data = []
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v3/stock_split_calendar?from={start_datetime.strftime('%Y-%m-%d')}&to={end_datetime.strftime('%Y-%m-%d')}\
                &apikey={FMP_API_KEY}".replace(" ", "")
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # [0] - assuming r.text is return as a list
    return data[::-1] # data.reverse() # ensure list is in ascending order

def get_tickers_with_stock_splits_in_period_fmp(start_day): # no end day specified since end day will always be current day since if end day is not current day and ticker split after the end_day then the daily yahoo finance prices will be updated and reflect the stock split but the hourly yahoo finance prices will reflect the stock prices at that day
    tickers_for_period = []
    stop_day, end_day = start_day, datetime.now() # don't allow stop_day to be less than start_day since if stock split before start_day then price change should already be accounted for
    while stop_day.date() <= end_day.date():
        next_stop_day = stop_day + timedelta(days=85)
        if next_stop_day.date() > end_day.date():
            next_stop_day = end_day
        print(str(stop_day) + " to " + str(next_stop_day))
        tickers_in_85_days_period = _fetch_data(get_tickers_with_stock_splits_in_85_days_period_fmp, params={'start_datetime': stop_day, 'end_datetime': next_stop_day}, error_str=" - No (or issue with) tickers with stock splits from date: " + str(stop_day) + " to next date: " + str(next_stop_day) + ", on: " + str(datetime.now()), empty_data=[])
        tickers_for_period = tickers_for_period + tickers_in_85_days_period
        stop_day = next_stop_day + timedelta(days=2) # + 2 day to prevent inclusive values (FMP for some reason adds a one day buffer at the end of the stock_split_calendar API call query - returns values up until end_datetime + 1 day)
    df = pd.DataFrame(tickers_for_period)
    df = df.dropna(how="any") # drops missing values
    return df

def get_tickers_with_stock_splits_fmp(start_day): # check tickers with tickers_with_stock_splits[tickers_with_stock_splits['symbol']==ticker]
    tickers_with_stock_splits = get_tickers_with_stock_splits_in_period_fmp(start_day=start_day)
    skip_idxs = []
    for idx in tickers_with_stock_splits.index:
        if idx not in skip_idxs:
            symbol, date = tickers_with_stock_splits.loc[idx, ['symbol', 'date']]
            matching_rows = tickers_with_stock_splits[(tickers_with_stock_splits['symbol'] == symbol) & (tickers_with_stock_splits['date'] == date)]
            if len(matching_rows) > 1:
                print(symbol + ", " + str(date) + ": Deleting repeated row " + str(matching_rows))
                repeated_idx = matching_rows.index[-1]
                tickers_with_stock_splits = tickers_with_stock_splits.drop(repeated_idx)
                skip_idxs.append(repeated_idx)
    for ticker, dates in {'MMAT': {'date-incorrect': '2024-01-29', 'date-correct': '2024-01-26'}, 'KAVL': {'date-incorrect': '2024-01-25', 'date-correct': '2024-01-24'}}.items():
        idx = tickers_with_stock_splits[(tickers_with_stock_splits['symbol']==ticker) & (tickers_with_stock_splits['date']==dates['date-incorrect'])].index.tolist()
        print(ticker + ", " + str(idx) + ": Correcting incorrect date")
        tickers_with_stock_splits.loc[idx, ['date', 'label']] = [dates['date-correct'], datetime.strptime(dates['date-correct'], '%Y-%m-%d').strftime('%B %d, %y')]
    return tickers_with_stock_splits

# note some tickers are returned different than normal ie 'BRK.B' is returned 'BRK-B'
def get_etf_constituents_fmp(etf):
    # global FMP_API_KEY
    data = []
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v3/etf-holder/{etf}\
                ?apikey={FMP_API_KEY}".replace(" ", "")
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # [0] - assuming r.text is return as a list
    df = pd.DataFrame(data)
    return df

# data goes back to 2014 / 10 years ago?
def get_senate_trading_symbol_fmp(ticker):
    # global FMP_API_KEY
    data = []
    session = requests.Session()
    request = f"https://financialmodelingprep.com/api/v4/senate-trading?symbol={ticker}\
                &apikey={FMP_API_KEY}".replace(" ", "")
    r = session.get(request)
    if r.status_code == requests.codes.ok:
        data = json.loads(r.text) # [0] - assuming r.text is return as a list
    df = pd.DataFrame(data)
    df['dateRecieved'] = pd.to_datetime(df['dateRecieved'])
    df['full_name'] = df['firstName']+' '+df['lastName']
    df = df.set_index(['dateRecieved']).sort_index()
    return df

import yfinance as yf

# refactor to get rid of verbose
def get_ticker_data_yf(ticker, start_datetime=None, end_datetime=None, interval="1d"):
    data = yf.download(ticker, start_datetime, end_datetime, interval=interval) # OHLC, adj close, volume
    return data

import bs4 as bs
import re

def get_ticker_data_detailed_yfinance(ticker, options={'engaged': False, 'type': 'key-statistics'}, additional_page={'engaged': False, 'type': 'profile'}): # maybe refactor to incorporate multiple options # 'financials' # financial options doesn't include 'summaryProfile', 'defaultKeyStatistics', 'financialData'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10 7 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'} # {'User-Agent': 'Mozilla/4.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'} # maybe refactor here and below, might change header to something else but doesn't matter just tricking the server (fighting bots / crawlers) into thinking it's a browser making the request, header is from https://stackoverflow.com/questions/68259148/getting-404-error-for-certain-stocks-and-pages-on-yahoo-finance-python
    site_url = 'https://finance.yahoo.com/quote/' + ticker + '/' # https://finance.yahoo.com/quote/TSLA/key-statistics?p=TSLA&.tsrc=fin-srch
    resp = requests.get(site_url, headers=headers) # , auth=(username, password)) # maybe add timeout=50 to avoid unsolved_error (see requests documentation)
    soup = bs.BeautifulSoup(resp.text, 'html.parser')
    # div_main = soup.find('div', {'class': 'Mstart(a) Mend(a)'})
    # spans = div_main.find_all('span')
    # for idx,span in enumerate(spans):
    #     if span.string: # and (len(script.string) > max_script['length']): # can't use .text after bs.__version__ > 4.8.0
    #         # max_script['length'], max_script['idx'] = len(script.string), idx # print(str(idx) +  ": " + td.string) # print(str(idx) +  ": " + td.string)", len: " + str(len(script.string)) + ", first 100 characters: " + script.string[:100] + ", last 100 characters: " + script.string[-100:])
    #         if span.string not in ['Valuation Measures', 'Financial Highlights', ...]:
    last = float(soup.find('span', {'data-testid': 'qsp-price'}).text.strip().replace(',',"")) # after-hours value is data-testid='qsp-post-price' # .replace('$',"")
    div_quote_statistics = soup.find('div', {'data-testid': 'quote-statistics'})
    lis = div_quote_statistics.find_all('li')
    data, times_table, current_label = {'Last': last}, {'T': 1e12, 'B': 1e9, 'M': 1e6, 'K': 1e3}, None
    for idx,li in enumerate(lis):
        if li.text: # and (len(script.string) > max_script['length']): # can't use .text after bs.__version__ > 4.8.0
            # max_script['length'], max_script['idx'] = len(script.string), idx # print(str(idx) +  ": " + li.string) # print(str(idx) +  ": " + li.string)", len: " + str(len(script.string)) + ", first 100 characters: " + script.string[:100] + ", last 100 characters: " + script.string[-100:])
            try:
                spans = li.find_all('span')
                current_label = spans[0]['title'].strip()
                current_value_text = spans[1].string.strip()
                if current_label in ['Previous Close', 'Open', 'Volume', 'Avg. Volume', 'Beta (5Y Monthly)', 'PE Ratio (TTM)', 'EPS Ratio (TTM)', '1y Target Est']:
                    current_value = float(current_value_text.replace(',',""))
                elif current_label in ['Market Cap (intraday)']:
                    current_value = float(re.split('[a-zA-Z]', current_value_text)[0]) * times_table[current_value_text[-1]]
                elif current_label in ['Forward Dividend & Yield']:
                    current_label = 'Forward Dividend' # on it's own line so that current_label is established before potential error
                    current_value = float(current_value_text.split(" ")[0])
                elif current_label in ['Earnings Date', 'Ex-Dividend Date']:
                    current_value = datetime.strptime(current_value_text, '%b %d, %Y')
                else:
                    current_value = current_value_text.replace(',',"")
            except Exception as e:
                if current_value_text in ["∞", "-", "--", "No Data", "No"]:
                    data[current_label] = float("NaN")
                    continue
                print(str(e) + " - Issue with spans for list idx: " + str(idx) + " and list item: " + str(li.text) + ", skipping list item for ticker: " + ticker)
                continue
            data[current_label] = current_value
    # if options['engaged']: # need to complete / refactor
        # site_url = 'https://finance.yahoo.com/quote/' + ticker + '/' + (options['type'])
    if additional_page['engaged']: # need to refactor
        site_url = 'https://finance.yahoo.com/quote/' + ticker + '/' + (additional_page['type']) + '/'
        resp = requests.get(site_url, headers=headers)
        soup = bs.BeautifulSoup(resp.text, 'html.parser')
        # div_profile = soup.find('div', {'class': 'Pos(r) Bgc($bg-content) Bgc($lv2BgColor)! Miw(1007px) Maw(1260px) tablet_Miw(600px)--noRightRail Bxz(bb) Bdstartc(t) Bdstartw(20px) Bdendc(t) Bdends(s) Bdendw(20px) Bdstarts(s) Mx(a)'}).find('div', {'class': 'Pt(10px) smartphone_Pt(20px) Lh(1.7)'})
        spans_in_p_sector_industry_employees, current_label = soup.find('div', {'class': 'Pos(r) Bgc($bg-content) Bgc($lv2BgColor)! Miw(1007px) Maw(1260px) tablet_Miw(600px)--noRightRail Bxz(bb) Bdstartc(t) Bdstartw(20px) Bdendc(t) Bdends(s) Bdendw(20px) Bdstarts(s) Mx(a)'}).find('p', {'class': 'D(ib) Va(t)'}).find_all('span'), None
        for idx,span in enumerate(spans_in_p_sector_industry_employees):
            if span.string and idx < 6: # and (len(script.string) > max_script['length']): # can't use .text after bs.__version__ > 4.8.0
                # max_script['length'], max_script['idx'] = len(script.string), idx # print(str(idx) +  ": " + td.string) # print(str(idx) +  ": " + td.string)", len: " + str(len(script.string)) + ", first 100 characters: " + script.string[:100] + ", last 100 characters: " + script.string[-100:])
                if idx%2 == 0:
                    current_label = span.string.replace('(s)',"")
                    if idx == 0 or idx == 6: # maybe refactor idx == 6 is redundant
                        continue
                elif idx == 5:
                    current_value = float(span.string.replace(',',""))
                else:
                    current_value = span.string
                data[current_label] = current_value
    return data

def get_tickers_with_stock_splits_in_day_yfinance(date, tickers_for_period): # date is a string in format '%Y-%m-%d' (example: '2021-03-12')
    tickers = {} # , random_int , randint(0, 100)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10 7 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'} # {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    # if random_int % 20 == 0:
    #     print("Sleeping 30 seconds for random int " + str(random_int) + " % 20 == 0 on: " + str(datetime.now()))
    #     time.sleep(30)
    site_url = 'https://finance.yahoo.com/calendar/splits/?day=' + date # '2020-11-09'
    resp = requests.get(site_url, headers=headers) #  # if random_int % 2 != 0 else requests.get(site_url, headers=headers[1])
    soup = bs.BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', {'class': 'W(100%)'})
    for row in table.find_all('tr')[1:]:
        tds = row.find_all('td')
        ticker = tds[0].text.strip()
        split_ratio_text = tds[4].text.strip() if (tds[4].text.strip() and tds[4].text.strip() != '-') else "1.00 - 1.00"
        try:
            split_ratio = float(split_ratio_text.split("-")[0]) / float(split_ratio_text.split("-")[1]) # yahoo finance must have switched ratio format in 2023, used to be: float(split_ratio_text.split("-")[1]) / float(split_ratio_text.split("-")[0])
        except Exception as e:
            print(str(e) + " - Issue with split_ratio_text on date: " + date + ", skipping " + ticker)
            continue
        ex_date = datetime.strptime(date, '%Y-%m-%d') # datetime.strptime(tds[2].text.strip(), '%b %d, %Y')
        if ticker in tickers_for_period:
            print(ticker + ": multiple splits in time period " + str(tickers_for_period[ticker]) + " with split_ratio: " + str(split_ratio) + " on date: " + date)
            tickers[ticker] = tickers_for_period[ticker] + [{'split_ratio': split_ratio, 'ex_date': ex_date}] # split_ratio = tickers_for_period[ticker]['split_ratio'] * split_ratio
        else:
            tickers[ticker] = [{'split_ratio': split_ratio, 'ex_date': ex_date}]
    return tickers

def get_tickers_with_stock_splits_in_period_yfinance(start_day, **params): # no end day specified since end day will always be current day since if end day is not current day and ticker split after the end_day then the daily yahoo finance prices will be updated and reflect the stock split but the hourly yahoo finance prices will reflect the stock prices at that day
    tickers_for_period = {}
    stop_day, end_day = start_day, datetime.now() # don't allow stop_day to be less than start_day since if stock split before start_day then price change should already be accounted for
    usa_holidays = params['usa_holidays'] if 'usa_holidays' in params else {}
    count = 0
    while stop_day.date() <= end_day.date():
        count += 1
        if count % 40 == 0: # maybe refactor take out since unlikely this will hit: 2000/365: 5.47 years
            print("Sleeping 7min every 40 requests on: " + str(datetime.now()))
            time.sleep(7*60)
        tickers_for_day = _fetch_data(get_tickers_with_stock_splits_in_day_yfinance, params={'date': stop_day.strftime('%Y-%m-%d'), 'tickers_for_period': tickers_for_period}, error_str=" - No (or issue with) tickers with stock splits on date: " + str(stop_day) + ", on: " + str(datetime.now()), empty_data={})
        tickers_for_period = {**tickers_for_period, **tickers_for_day}
        stop_day = stop_day + timedelta(days=1)
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # interval_start_date/stop_day in usa_holidays # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday())) # to avoid weekends, refactor to avoid holidays (2020-05-25)
            stop_day = stop_day + timedelta(days=1)
    return tickers_for_period

def get_exchange_rates_exchangerate(base_currency="USD"):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10 7 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'} #
    site_url = 'https://api.exchangerate-api.com/v4/latest/' + base_currency
    resp = requests.get(site_url, headers=headers) #
    # if resp.status_code == 200:
    resp_in_json = resp.json()
    rates_dict = resp_in_json['rates']
    # else:
    #     return response.status_code
    return rates_dict

def get_ticker_data_detailed_gfinance(ticker, exchange):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10 7 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'} # {'User-Agent': 'Mozilla/4.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'} # maybe refactor here and below, might change header to something else but doesn't matter just tricking the server (fighting bots / crawlers) into thinking it's a browser making the request, header is from https://stackoverflow.com/questions/68259148/getting-404-error-for-certain-stocks-and-pages-on-yahoo-finance-python
    site_url = 'https://www.google.com/finance/quote/' + ticker + ':' + exchange # 'https://www.investing.com/equities/google-inc' # + ticker + '/' + (options['type'] if options['engaged'] else '') # https://finance.yahoo.com/quote/TSLA/key-statistics?p=TSLA&.tsrc=fin-srch
    resp = requests.get(site_url, headers=headers) # , auth=(username, password)) # maybe add timeout=50 to avoid unsolved_error (see requests documentation)
    soup = bs.BeautifulSoup(resp.text, 'html.parser')
    last = float(soup.find('div', {'class': 'AHmHk'}).text.strip().replace('$',"").replace(',',""))
    divs = soup.find_all('div', {'class': 'gyFHrc'}) # divs = soup.find('div', {'class': 'eYanAe'}).find_all('div')
    data, times_table = {'Last': last}, {'T': 1e12, 'B': 1e9, 'M': 1e6, 'K': 1e3}
    exchange_rates_usd = _fetch_data(get_exchange_rates_exchangerate, params={'base_currency': 'USD'}, error_str=" - No Exchange Rates (USD) from ExchangeRate-api on: " + str(datetime.now()), empty_data = {})
    for div in divs:
        # print(div.text)
        current_label = div.find('div', {'class': 'mfs7Fc'}).text.strip()
        if current_label in ['Market cap', 'Avg Volume']:
            current_value_text = div.find('div', {'class': 'P6K39c'}).text.strip().split(" ")[0] # maybe refactor and add .replace('$',"").replace(',',"").replace(' ',"")
            try:
                current_value = float(current_value_text[:-1]) * times_table[current_value_text[-1]]
            except:
                current_value = float(current_value_text)
            if current_label in ['Market cap']:
                currency = div.find('div', {'class': 'P6K39c'}).text.strip().split(" ")[1] #
                if currency != 'USD':
                    current_value = current_value / float(exchange_rates_usd[currency]) if currency in exchange_rates_usd else float("NaN") # float(exchange_rates_usd[currency]) precautionary exchange_rates_usd[currency] is int
        elif current_label in ['CEO', 'Headquarters']:
            current_value = ", ".join(div.find('div', {'class': 'P6K39c'}).get_text(strip=True, separator='\n').split("\n"))
            # current_value = div.find('div', {'class': 'P6K39c'}).get_text(strip=True, separator='br').splitlines()
        elif current_label in ['Founded']:
            try:
                current_value = datetime.strptime(div.find('div', {'class': 'P6K39c'}).text.strip(), '%b %d, %Y')
            except:
                try:
                    current_value = datetime.strptime(div.find('div', {'class': 'P6K39c'}).text.strip(), '%Y')
                except:
                    current_value = datetime.strptime(div.find('div', {'class': 'P6K39c'}).text.strip(), '%b %Y')
        else:
            current_value = div.find('div', {'class': 'P6K39c'}).text.strip().replace('$',"").replace(',',"").replace(' ',"").replace('%',"")
            current_value = float("NaN") if current_value in ["∞", "-", "--", "No Data", "No"] else float(current_value)/100.0 if current_label in ['Dividend yield'] else float(current_value) if current_label in ['Previous close', 'P/E ratio', 'Employees'] else current_value #
        data[current_label] = current_value
    data['EPS (TTM)'] = (1 / data['P/E ratio']) * last if 'P/E ratio' in data else float("NaN") # P/E is using TTM assuming it's basic earnings
    return data

openai_functions=[
    {
        "name": "get_company_stock_ticker",
        "description": "This will get the USA stock ticker of the company",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker_symbol": {
                    "type": "string",
                    "description": "This is the stock symbol of the company.",
                },
                "company_name": {
                    "type": "string",
                    "description": "This is the name of the company given in query",
                }
            },
            "required": ["company_name","ticker_symbol"]
        },
    },
    {
        "name": "get_company_competitors_and_their_tickers",
        "description": "This will get the names of the competitor companies of the company and their ticker symbols",
        "parameters": {
            "type": "object",
            "properties": {
                "company_names": {
                    "type": "string",
                    "description": "This is the names of the competitor companies of the company given in query",
                },
                "ticker_symbols": {
                    "type": "string",
                    "description": "This is the ticker symbols of the competitor companies of the company given in query",
                }
            },
            "required": ["company_names","ticker_symbols"]
        },
    },
    {
        "name": "extract_investment_recommendation",
        "description": "This will get the numeric investment recommendation on a scale of 1-10 for the OpenAI analysis of the company",
        "parameters": {
            "type": "object",
            "properties": {
                "investment_recommendation": {
                    "type": "string",
                    "description": "This is the numeric investment recommendation on a scale of 1-10 of the OpenAI analysis of the company given in query",
                },
            },
            "required": ["investment_recommendation"]
        },
    }
]

def should_I_buy_the_stock_openai (analysis): # extract_investment_recommendation_openai # , ai="google-gemini-pro"
    response = openai_client.chat.completions.create( # openai.ChatCompletion.create(
        model="gpt-4", # 3.5-turbo
        temperature=0,
        messages=[{
            "role":"user",
            "content":f"Given the OpenAI analysis, what is the numeric investment recommendation on a scale of 1-10 of the company stock ticker ?: {analysis.content}?" # f"Given the user request, what is the names of the competitor companies of the company and their ticker symbols ?: {query}?"
        }],
        functions=openai_functions,
        function_call={"name": "extract_investment_recommendation"}, # "get_company_competitors_and_their_tickers"
    )
    message = response.choices[0].message # response["choices"][0]["message"]
    arguments = json.loads(message.function_call.arguments)
    investment_recommendation = arguments["investment_recommendation"]
    tokens_used = response.usage.total_tokens
    print(investment_recommendation + " - " + str(tokens_used))
    investment_recommendation = float(investment_recommendation) # if not re.search(r"/", investment_recommendation) else float(investment_recommendation.split("/"))
    return investment_recommendation, tokens_used

def should_I_buy_the_stock_google_gemini_pro(ticker, company_name, location=None, add_technical=False): # query # , ai="google-gemini-pro"
    # global google_gemini_pro_model
    # agent.run(query) Outputs Company name, Ticker
    # company_name,ticker,tokens_used=get_stock_ticker(query)
    # print({"Query":query,"Company_name":company_name,"Tokens_used":tokens_used,"Ticker":ticker})
    # ticker = ticker.split(".")[0] if "." in ticker else ticker
    query = f"Is it a good time to buy {company_name}?"
    # stock_data=get_ticker_data_granular_fmp(ticker, start_datetime=datetime.now() - timedelta(days=365), end_datetime=datetime.now())[:10]
    stock_financials = get_ticker_balance_sheet_data_fmp(ticker)[:3] # 4 most recent years only: Remove 4th years + data
    stock_news = get_ticker_stock_news_articles_fmp(ticker)
    if add_technical:
        ticker_data_quote = _fetch_data(get_ticker_data_quote_fmp, params={'ticker': ticker}, error_str=" - No ticker data quote FMP for ticker: " + ticker + " on: " + str(datetime.now()), empty_data=pd.DataFrame())
        available_information=f"Stock Financials: {stock_financials.to_string()}\n\nStock News: {stock_news.to_string()}\n\nStock Technicals: {ticker_data_quote.to_string()}"
    else:
        available_information=f"Stock Financials: {stock_financials.to_string()}\n\nStock News: {stock_news.to_string()}"
    # in the future can add social media data like reddit posts (examples from 2022 in openai_training_data.py)
    # available_information=f"Stock Price: {stock_data}\n\nStock Financials: {stock_financials}\n\nStock News: {stock_news}"
    start_time = time.time()
    print(f"\nAnalyzing ticker: {ticker}, company: {company_name}, listed at: {location} \n")
    prompt = f"Tell me whether or not I should I invest in the stock with a scale of 1-10, 1 being a no buy and 10 being a full buy, Use the available data and provide investment recommendation. \
        The user is fully aware about the investment risk, dont include any kind of warning like 'It is recommended to conduct further research and analysis or consult with a financial advisor before making an investment decision' in the answer \
        User question: {query} \
        You have the following information available about {company_name}. Write (5-6) pointwise investment analysis to answer user query. At the end conclude with proper explaination and recommendation on a scale of 1-10. Try to Give positives and negatives  : \
        {available_information}"
    # if ai == "google-gemini-pro":
    analysis = google_gemini_pro_model.generate_content(prompt)
    print(analysis.text)
    # elif ai == "openai":
    #     analysis = chat_model.invoke(prompt)
    #     print(analysis.content)
    # else:
    #     analysis = None
    print("Execution time: " + str(time.time() - start_time))
    return analysis

def extract_investment_recommendation(analysis, ticker):
    start_time = time.time()
    try:
        rating = float(re.findall(r"[2-9]", re.split("[C|c]onclusion|[R|r]ecommend[ation]{0,1}|[O|o]verall", analysis.text)[-1])[0]) # maybe add ^ed for recommend |[R|r]at[e|ed|ing] # excluding 0,1,10 outliers (extremely low or high recommendation) # maybe refactor add rating|recommendation
    except Exception as e:
        print(str(e) + " - No (or issue with extracting) investment recommendation for: " + ticker + " on: " + str(datetime.now()) + ", Execution time: " + str(time.time() - start_time))
        rating = 0
    print("Execution time: " + str(time.time() - start_time))
    # rating = float(re.findall(r"[0-9]{1,2}" + " out of 10", analysis.text)[0].split()[0]) if re.findall(r"[0-9]{1,2}" + " out of 10", analysis.text) else float("NaN")
    # rating = google_gemini_pro_model.generate_content(f"Given the Google Gemini Pro analysis, what is the numeric investment recommendation on a scale of 1-10 of the company stock ticker ?: {analysis.text}?")
    return rating

def extract_investment_recommendation_2(analysis, ticker):
    start_time = time.time()
    try:
        rating = float(re.findall(r"[2-9]", re.split(r"\srate\s|\srated\s|\srating\s", analysis.text)[-1])[0]) # \s[R|r]at[e|ed|ing]\s # [R|r]at[e|ed|ing] | # excluding 0,1,10 outliers (extremely low or high recommendation) # maybe refactor add rating|recommendation
    except Exception as e:
        print(str(e) + " - No (or issue with extracting) investment recommendation for: " + ticker + " on: " + str(datetime.now()) + ", Execution time: " + str(time.time() - start_time))
        # rating = float(re.findall(r"[2-9]", re.split("[R|r]at[e|ed|ing]", analysis.text)[-1])[0])
        rating = 0
    print("Execution time: " + str(time.time() - start_time))
    # rating = float(re.findall(r"[0-9]{1,2}" + " out of 10", analysis.text)[0].split()[0]) if re.findall(r"[0-9]{1,2}" + " out of 10", analysis.text) else float("NaN")
    # rating = google_gemini_pro_model.generate_content(f"Given the Google Gemini Pro analysis, what is the numeric investment recommendation on a scale of 1-10 of the company stock ticker ?: {analysis.text}?")
    return rating

from pytrends.request import TrendReq

def get_google_trends_pt(kw_list, from_date, to_date, trend_days=270, cat=0, geo='', tz=480, gprop='', hl='en-US', isPartial_col=False, from_start=False, scale_cols=True): # trend_days max is around 270 # category to narrow results # geo e.g 'US', 'UK' # tz = timezone offset default is 360 which is US CST (UTC-6), PST is 480 (assuming UTC-8*60) # hl language default is en-US # gprop : filter results to specific google property like 'images', 'news', 'youtube' or 'froogle' # overlap=100, sleeptime=1, not doing multiple searches # other variables: timeout=(10,25), proxies=['https://34.203.233.13:80',], retries=2, backoff_factor=0.1, requests_args={'verify':False}
    data = pd.DataFrame()
    if len(kw_list) != 1: # not doing multirange_interest_over_time: len(kw_list)==0 or len(kw_list)>5
        print("Error: The keyword list must be 1, not doing multirange_interest_over_time") # be > 0 and can contain at most 5 words
        return data
    # not verifying from_date, to_date types, _fetch_data should handle error
    n_days = (to_date - from_date).days
    if n_days>270 or trend_days>270:
        print("Error: To - From Dates or Trend days must not exceed 270")
        return data
    _pytrends = TrendReq(hl=hl, tz=tz)
    # pytrends.build_payload(kw_list, cat=0, timeframe=, geo='', gprop='')
    try:
        _pytrends.build_payload(kw_list, cat=cat, timeframe=[from_date.strftime('%Y-%m-%d') + ' ' + to_date.strftime('%Y-%m-%d')], geo=geo, gprop=gprop) # trend_dates[0]
    except Exception as e:
        print(str(e) + " - No (or issue with) Pytrends for kw_list: " + str(kw_list) + " with from_date: " + str(from_date) + " and to_date: " + str(to_date))
    data = _pytrends.interest_over_time().reset_index()
    if not isPartial_col:
        data.drop('isPartial', axis=1, inplace=True)
    return data

# 04/24/2020 is first day with S&P 500 data (505 tickers) with Zacks Rank ordered alphabetically from Slickcharts (I believe), 04/28/2020 is first day with S&P 500 data (505 tickers) with Zacks Rank ordered by S&P 500 rank from Slickcharts, 05/08/2020 is first day with USA-listed stocks data (~4900 tickers) with Zacks Rank ordered by Market Cap Rank from TradingView, 07/21/2020 is first day with USA-listed tradable assets on Alpaca data (~6900 tickers) with Morningstar and Zacks Rank ordered by Alpaca from Yahoo Finance # some other nuances (like TradingView v2 data, incomplete Yahoo Finance data up until 07/24/2020, modifications/additions to Yahoo Finance data up until 08/07/2020), 10/16/2020 is first day with 'P/S (TTM)', 'EV' data, 10/30/2020 is first day with 'D/E (MRQ)', 05/13/2021 is first day with 'Forward P/E', 06/04/2021 is first day with 'P/E (TTM)' (could be derived in previous days) # 2020-05-18 is without zacks rank, issue, 2020-06-16 is a txt document with comma-seperated values but without zacks rank, 2020-10-30 and 2020-11-(02->05) missed a lot of tickers (~2325) since improper implementation of ticker_data_detailed['financialData'] (any ticker that has incomplete ticker_data_detailed['financialData'] is not recorded), 2020-07-21->2020-12-08 missed a lot of tickers (~400/day) since improper implementation of ticker_data_detailed['summaryDetail'], 10/30/2020->2021-01-05 missed some tickers (~10/day) since improper implementation of ticker_data_detailed['financialData'], 2020-12-02 and 2020-12-23 failed to save data due to requests error (2020-12-23 not sure) and 2021-03-02 saved late due to frozen Q all tickers after and including S have data from 2021-03-03 06:30 - 07:50, 2021-04-06->08 and 2021-07-07->08 no data downloaded because trips with Stephanie some reason not working, 2021-07-01->12 issue with anti-automation system (only downloaded 1/2 of tickers) fixed by adding header to fake as browser, 2021-09-08 frozen, 2021-10-04->06 frozen while on trip with Maja in Miami, 2021-10-19 wrote over when trying to download and save 2021-10-29 data, 2021-10-29 -> 2021-11-01 bad / duplicate (of 2021-10-28) data , 2021-11-04 froze, 2021-12-23->2022-01-03 & 2022-01-10->13 duplicate (at least the important) data, 2022-01-18 data is a bit corrupted since late save (mixed with 2022-01-19 06:30->09:22am data), 2022-01-26 & 2022-03-10 frozen, 2022-05-20->26 duplicate, 2022-10-31+ weird stuff happening with time.sleep() (sleeping for many minutes / hours at a time) & downloading (download pausing for hours at a time, taking 5x as long etc) and saving data (like save_portfolio_backup() saving to save_tickers_yf_and_fmp_data() location) with new Apple update (Mac OS 12.6.1) even after restarting etc, 2022-12-16->2022-12-29 yfinance updated their page so get_ticker_data_detailed_yfinance() doesn't pull the necessary data, 2023-01-03->2023-01-13 GOOG (maybe others) has (have) incorrect Market Cap $61B vs. $1.2T, 2023-10-31 switched to Google Finance data, 2023-11-16->17 no data downloaded because trip with Andreas some reason not working, 2023-12-01 switched to FMP data (upgraded in 2023-12-08 and 2024-01-12), 2025-01-23->24 GGAL issued 399RGT026 caused #get_alpaca_assets to crash
def get_saved_tickers_data(date, category='all', rankings=['zr'], additions=[]): # date is a string in format '%Y-%m-%d', categories: 'sp500', 'usa_by_tv' # refactor rankings
    if category == 'all':
        category = 'sp500_by_sc' if datetime.strptime(date, '%Y-%m-%d').date() < datetime.strptime('2020-05-08', '%Y-%m-%d').date() else 'usa_by_tv' if datetime.strptime(date, '%Y-%m-%d').date() < datetime.strptime('2020-07-21', '%Y-%m-%d').date() else 'usa_alpaca_by_yf_and_fmp' + ('_and_' + '_'.join(additions) if additions else '') # '2020-08-08' # maybe refactor names usa_by_tv and usa_alpaca_by_yf names
        rankings = ['zr'] if datetime.strptime(date, '%Y-%m-%d').date() < datetime.strptime('2020-07-21', '%Y-%m-%d').date() else ['ms', 'zr'] # '2020-08-08' # ['ms'] if datetime.strptime(date, '%Y-%m-%d').date() <= datetime.strptime('2020-08-07', '%Y-%m-%d').date() else ['ms', 'zr'] # <= since '2020-08-07' is a Friday
    try:
        f = open('data/stocks/saved_tickers_data/' + category + '/tickers_' + '_'.join(rankings + additions) + '_' + date + '.pckl', 'rb')
        df_tickers_historical = pd.read_pickle(f)
        f.close()
    except Exception as e:
        print(str(e) + " - No " + category + " saved tickers data with " + str(rankings) + " rankings for date: " + date)
        df_tickers_historical = pd.DataFrame()
    return df_tickers_historical

# have to download csv file beforehand and save in 'data/stocks/tv_screener_by_market_cap/' as: 'america_" + date + ".csv"'
def save_usa_tv_tickers_zacks_data(date): # maybe refactor, only for companies above $2bn Market Cap
    trading_view_ratings = {"Strong Buy": 1, "Buy": 2, "Neutral": 3, "Sell": 4, "Strong Sell": 5}
    # get publicly listed (in USA exchanges) companies sorted by market cap # on tradingview.com/screener/: remove Change, Price to Earnings Ratio (TTM), add D/E Ratio (MRQ), Div Yield (FY), P/FCF (TTM), P/B (FY), EV (MRQ), maybe add Commodity Channel Index (20), EV/EBITDA (TTM), Goodwill, Industry, P/S (FY), Total (Current) Assets, Return on Assets/Equity/Invested Capital # issue: unsure why some tickers are removed from tradingview.com/screener/ day-to-day
    df_usa_by_tv_tickers_zr = pd.read_csv("data/stocks/tv_screener_by_market_cap/america_" + date + ".csv")
    df_usa_by_tv_tickers_zr = df_usa_by_tv_tickers_zr.set_index('Ticker').rename(columns={"Market Capitalization": "Market Cap", "Number of Employees": "# Employees", "Debt to Equity Ratio (MRQ)": "D/E Ratio (MRQ)", "Dividends Yield (FY)": "Div Yield (FY)", "Price to Free Cash Flow (TTM)": "P/FCF (TTM)", "Price to Book (FY)": "P/B (FY)", "Enterprise Value (MRQ)": "EV (MRQ)", "Enterprise Value/EBITDA (TTM)": "EV/EBITDA (TTM)"}) # , "Price to Earnings Ratio (TTM)": "P/E Ratio (TTM)",
    # df_usa_by_tv_tickers_zr = df_usa_by_tv_tickers_zr.join(_fetch_data(get_sp500_ranked_tickers_by_slickcharts, params={}, error_str=" - No S&P 500 Ranked Tickers by Slickcharts on: " + str(datetime.now()), empty_data = pd.DataFrame())['S&P 500 Rank'], on=df_usa_by_tv_tickers_zr.index)
    df_usa_by_tv_tickers_zr['Rating'] = df_usa_by_tv_tickers_zr.apply(lambda x: trading_view_ratings[x['Rating']] if type(x['Rating']) is str else float("NaN"), axis=1) # maybe refactor here and below None to float("NaN") to match save_usa_alpaca_by_yf_tickers_ms_zr_data() # converts dtype to float64 as well
    # df_usa_by_tv_tickers_zr = df_usa_by_tv_tickers.copy() # maybe refactor and add back and return two pandas dataframes # df_usa_by_tv_tickers_zr = df_sp500_tickers.copy()
    for ticker in df_usa_by_tv_tickers_zr.index:
        # if not np.isnan(df_usa_by_tv_tickers_zr.loc[ticker, 'Zacks Rank']):
        #     continue
        zacks_data = _fetch_data(get_zacks_data, params={'ticker': ticker}, error_str=" - No Zacks Data for ticker: " + ticker + " on: " + str(datetime.now()), empty_data = {})
        if ticker not in zacks_data or (('source' not in zacks_data[ticker]) and (zacks_data[ticker]['error'] == 'true')): # 'market_data' not in ticker_data or not ticker_data['market_data']['market_cap']['usd']: # remove granular from error_str
            print("Error retreiving zacks data for ticker: " + ticker + " on date: " + datetime.now().strftime('%Y-%m-%d'))
        else:
            # other interesting keys: (BATS/SUNGARD) earnings, p/e ratiom, dividend yield, ...
            df_usa_by_tv_tickers_zr.loc[ticker, ['Zacks Rank', 'Zacks Updated At']] = float(zacks_data[ticker]['zacks_rank'] if ('zacks_rank' in zacks_data[ticker]) and zacks_data[ticker]['zacks_rank'] else "NaN"), pd.to_datetime(zacks_data[ticker]['updated']) # Zacks Rank Text is just the following words corresponding to the rank (1-5): ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell'] # 'Zacks Updated At' - don't need if run at same time every day (market close)
    f = open('data/stocks/saved_tickers_data/' + 'usa_by_tv' + '/tickers_' + '_'.join(['zr']) + '_' + datetime.now().strftime('%Y-%m-%d') + '.pckl', 'wb') # 'sp500', 2020_04_26, format is '%Y-%m-%d' # datetime.now().strftime('%Y-%m-%d')
    pd.to_pickle(df_usa_by_tv_tickers_zr, f)
    f.close()
    return df_usa_by_tv_tickers_zr

def save_tickers_yf_and_fmp_data(df_tickers, date, additions=[]): # date is in format '%Y-%m-%d' # ms_zr_
    f = open('data/stocks/saved_tickers_data/' + 'usa_alpaca_by_yf_and_fmp' + ('_and_' + '_'.join(additions) if additions else '') + '/tickers_' + '_'.join(['ms', 'zr'] + additions) + '_' + date + '.pckl', 'wb') # date instead of datetime.now() since process takes a while can extend into next day when data is not for the next day
    pd.to_pickle(df_tickers, f)
    f.close()

def save_tickers_daily_gainers_fmp(df_tickers, date, additions=[]): # date is in format '%Y-%m-%d'
    f = open('data/stocks/saved_tickers_data/' + 'usa_gainers_fmp' + ('_and_' + '_'.join(additions) if additions else '') + '/tickers_' + '_'.join(additions) + '_' + date + '.pckl', 'wb') # date instead of datetime.now() since process takes a while can extend into next day when data is not for the next day
    pd.to_pickle(df_tickers, f)
    f.close()

def save_usa_alpaca_tickers_fmp_data(date): # maybe refactor and take away ms since not showing up most of time # date is in format '%Y-%m-%d'
    df_usa_alpaca_tickers_fmp_ms_zr_data = pd.DataFrame(columns = ['Name (Alpaca)', 'ID (Alpaca)', 'Exchange (Alpaca)', 'Shortable (Alpaca)', 'Easy to Borrow (Alpaca)', 'Class (Alpaca)', 'Asset Type', 'Market Cap', 'Sector', 'Industry', 'CEO', 'Website', '# Employees', 'Location', 'Last', 'Volume', 'P/E (TTM)', 'Forward P/E', 'P/S (TTM)', 'Basic EPS (FY)', 'PEG Ratio (TTM)', 'Div Yield (FY)', 'P/B (TTM)', 'EBITDA', 'EV/EBITDA (TTM)', 'D/E (TTM)', 'Net Income Ratio', 'Revenue (Past 5 years)', 'Gross Profit Ratio (Past 5 years)', 'Total Assets (Past 5 years)', 'Total Liabilities (Past 5 years)', 'Cash and Cash Equivalents (Past 5 years)', 'Long-Term Debt (Past 5 years)', 'Past 5 years', 'Beta', 'Short of Float Ratio', 'Short Ratio', 'Day range', 'Year range', '200D Avg', '50D Avg', 'Morningstar Rating', 'Held by Institutions Ratio', 'Held by Insiders Ratio', 'FMP Rank', 'FMP Rank Date', 'Zacks Rank', 'Zacks Updated At']).astype({'Name (Alpaca)': 'object', 'ID (Alpaca)': 'object', 'Exchange (Alpaca)': 'object', 'Shortable (Alpaca)': 'bool', 'Easy to Borrow (Alpaca)': 'bool', 'Class (Alpaca)': 'object', 'Asset Type': 'object', 'Market Cap': 'float64', 'Sector': 'object', 'Industry': 'object', 'CEO': 'object', 'Website': 'object', '# Employees': 'float64', 'Location': 'object', 'Last': 'float64', 'Volume': 'float64', 'P/E (TTM)': 'float64', 'Forward P/E': 'float64', 'P/S (TTM)': 'float64', 'Basic EPS (FY)': 'float64', 'PEG Ratio (TTM)': 'float64', 'Div Yield (FY)': 'float64', 'P/B (TTM)': 'float64', 'EBITDA': 'float64', 'EV/EBITDA (TTM)': 'float64', 'D/E (TTM)': 'float64', 'Net Income Ratio': 'float64', 'Revenue (Past 5 years)': 'object', 'Gross Profit Ratio (Past 5 years)': 'object', 'Total Assets (Past 5 years)': 'object', 'Total Liabilities (Past 5 years)': 'object', 'Cash and Cash Equivalents (Past 5 years)': 'object', 'Long-Term Debt (Past 5 years)': 'object', 'Past 5 years': 'object', 'Beta': 'float64', 'Short of Float Ratio': 'float64', 'Short Ratio': 'float64', 'Day range': 'object', 'Year range': 'object', '200D Avg': 'float64', '50D Avg': 'float64', 'Morningstar Rating': 'float64', 'Held by Institutions Ratio': 'float64', 'Held by Insiders Ratio': 'float64', 'FMP Rank': 'float64', 'FMP Rank Date': 'datetime64[ns]', 'Zacks Rank': 'float64', 'Zacks Updated At': 'datetime64[ns]'}) # maybe refactor and add columns which measure other KPIs, like in save_usa_tv_tickers_zacks_data, "S&P 500 Rank"
    count = 0
    for asset in _fetch_data(alpaca_api.list_assets, params={}, error_str=" - No listed assets from Alpaca on: " + str(datetime.now()), empty_data = []): # since only about 1/2-2/3 of alpaca assets are adequate (have market cap data), can use scrape to get adequate assets from a site that allows scraping # alpaca assets (organization / order in which listed) data changed on 2021-03-12, but possibly corrected on 2021-03-16
        ticker = asset.symbol # not using upper() as precautionary, should already be in upper
        # if ticker in df_usa_alpaca_tickers_fmp_ms_zr_data.index:
        #     continue
        if asset.tradable == False: # maybe refactor and add asset.shortable == False, tradable same as as status
            continue
        count += 1
        if count % 10000 == 0:
            print("Sleeping 1min every 10000 requests on: " + str(datetime.now()))
            time.sleep(1*60)
        start_time = time.time()
        try:
            ticker_data_detailed = _fetch_data(get_ticker_data_detailed_fmp, params={'ticker': ticker}, error_str=" - No ticker data detailed FMP for ticker: " + ticker + " on: " + str(datetime.now()), empty_data={}) # , zacks_data = _fetch_data(get_zacks_data, params={'ticker': ticker}, error_str=" - No Zacks Data for ticker: " + ticker + " on: " + str(datetime.now()), empty_data = {}) # _fetch_data(get_ticker_data_detailed_gfinance, params={'ticker': ticker, 'exchange': asset.exchange}, error_str=" - No ticker data detailed gfinance for ticker: " + ticker + " on exchange: " + asset.exchange + " on: " + str(datetime.now()), empty_data={})
            if not ticker_data_detailed:
                continue
            # if ticker not in zacks_data or (('source' not in zacks_data[ticker]) and ('error' in zacks_data[ticker] and zacks_data[ticker]['error'] == 'true')): # 'market_data' not in ticker_data or not ticker_data['market_data']['market_cap']['usd']: # remove granular from error_str
            #     print("Error retreiving zacks data for ticker: " + ticker + " on date: " + datetime.now().strftime('%Y-%m-%d'))
            #     zacks_rank, zacks_updated_at = float("NaN"), None # float("NaN") for better processing speeds in run_portfolio_zr, when comparing None to float() returns error but when compare NaN to float() its ok, also messes with dtypes (converts dtype to object) when input None into float64 (or other non-object column) column (not sure why it shouldn't based on documentation - missing data converted to column's dtype - but on 08/07/2020 it did)
            # else:
            #     zacks_rank, zacks_updated_at = float(zacks_data[ticker]['zacks_rank'] if ('zacks_rank' in zacks_data[ticker]) and zacks_data[ticker]['zacks_rank'] else "NaN"), pd.to_datetime(zacks_data[ticker]['updated'])
            # if None in [ticker_data_detailed['price']['marketCap'], ticker_data_detailed['price']['regularMarketPrice'], ticker_data_detailed['price']['regularMarketVolume'], ticker_data_detailed['defaultKeyStatistics']['trailingEps'], ticker_data_detailed['defaultKeyStatistics']['priceToBook']]:
                # continue
            # maybe add 'bid', 'sharesOutstanding', something regarding Sales/Revenue like ['defaultKeyStatistics']['enterpriseToRevenue'], something regarding ratings trend like ['recommendationTrend']['trend'], something regarding liquidity like current ratio, ['defaultKeyStatistics']['profitMargins'] # maybe take out 'eps' or 'p/e' one can be derived from the other and add (5 yr expected to PEG), 'ev/ebitda' since issue with ev value (compared to Yahoo Finance) # useful values from finance.yahoo.com/quote/' + ticker: '1y target EST', 'Earnings Date', 'Avg. Volume', "Day's Range", might be able to get more values like D/E and P/FCF in javascript section of page # not using Yahoo Finance EV since it is a quite a bit larger than TradingView
            df_usa_alpaca_tickers_fmp_ms_zr_data.loc[ticker] = [
                asset.name,
                asset.id,
                asset.exchange,
                asset.shortable,
                asset.easy_to_borrow,
                asset.__getattr__('class'),
                None, # maybe refactor - Asset Type? ticker_data_detailed['Last'], # good to fail if no 'price' (Asset quoteType, Market Cap, Price, Volume) since contains key metrics # FMT is Financial Market Trends
                ticker_data_detailed['profile']['mktCap'] if 'mktCap' in ticker_data_detailed['profile'] else float("NaN"),
                ticker_data_detailed['profile']['sector'] if 'sector' in ticker_data_detailed['profile'] else None, # ticker_data_detailed['summaryProfile']['sector'] if ('summaryProfile' in ticker_data_detailed and 'sector' in ticker_data_detailed['summaryProfile']) else None, # good to fail if no 'summaryProfile' (sector, industry) # and ticker_data_detailed['summaryProfile']
                ticker_data_detailed['profile']['industry'] if 'industry' in ticker_data_detailed['profile'] else None, # ticker_data_detailed['summaryProfile']['industry'] if ('summaryProfile' in ticker_data_detailed and 'industry' in ticker_data_detailed['summaryProfile']) else None, # and ticker_data_detailed['summaryProfile']
                ticker_data_detailed['profile']['ceo'] if 'ceo' in ticker_data_detailed['profile'] else None,
                ticker_data_detailed['profile']['website'] if 'website' in ticker_data_detailed['profile'] else None,
                ticker_data_detailed['profile']['fullTimeEmployees'] if 'fullTimeEmployees' in ticker_data_detailed['profile'] else float("NaN"), # None, # ticker_data_detailed['Full Time Employees'], # ticker_data_detailed['summaryProfile']['fullTimeEmployees'] if ('summaryProfile' in ticker_data_detailed and 'fullTimeEmployees' in ticker_data_detailed['summaryProfile']) else float("NaN"), # and ticker_data_detailed['summaryProfile']
                (str(ticker_data_detailed['profile']['address']) + ", " + str(ticker_data_detailed['profile']['city']) + ", " + str(ticker_data_detailed['profile']['state']) + ", " + str(ticker_data_detailed['profile']['country'])) if ('address' in ticker_data_detailed['profile'] and 'city' in ticker_data_detailed['profile'] and 'country' in ticker_data_detailed['profile']) else None, # and 'state' in ticker_data_detailed['profile']['state'] # None, # None if ('summaryProfile' not in ticker_data_detailed) else str(ticker_data_detailed['summaryProfile']['state'] if 'state' in ticker_data_detailed['summaryProfile'] else None) + ", " + str(ticker_data_detailed['summaryProfile']['country'] if 'country' in ticker_data_detailed['summaryProfile'] else None), # 'summaryProfile' in ticker_data_detailed and all (key in ticker_data_detailed['summaryProfile'] for key in ['state', 'country']) # or not ticker_data_detailed['summaryProfile']
                ticker_data_detailed['profile']['price'], # if 'Last' in ticker_data_detailed else float("NaN") # ticker_data_detailed['price']['regularMarketPrice'],
                ticker_data_detailed['profile']['volAvg'] if 'volAvg' in ticker_data_detailed['profile'] else float("NaN"), # ticker_data_detailed['price']['regularMarketVolume'],
                ticker_data_detailed['ratios'][0]['peRatioTTM'] if 'peRatioTTM' in ticker_data_detailed['ratios'][0] else float("NaN"), # if 'PE Ratio (TTM)' in ticker_data_detailed else float("NaN"), # ticker_data_detailed['summaryDetail']['trailingPE'] if ('summaryDetail' in ticker_data_detailed and ticker_data_detailed['summaryDetail'] and 'trailingPE' in ticker_data_detailed['summaryDetail']) else float("NaN"), # 'pe(ttm)': # using old version (with yf) get_ticker_data_detailed_yfinance(): (ticker_data_detailed.info['trailingPE'] if 'trailingPE' in ticker_data_detailed.info else
                None, # ticker_data_detailed['defaultKeyStatistics']['forwardPE'] if ('forwardPE' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"), # good to fail if no 'defaultKeyStatistics' since contains key metrics, failing on bad assets like: ['BCV-A', 'MH-D'], assets not worth extra logic # after analyzing TEAM on 2021-05-13 most likely this value is for the next 12 months and not fiscal year, but not 100% sure so leaving the description above as is
                ticker_data_detailed['ratios'][0]['priceToSalesRatioTTM'] if 'priceToSalesRatioTTM' in ticker_data_detailed['ratios'][0] else float("NaN"),
                ticker_data_detailed['financialsAnnual']['income'][0]['eps'] if (ticker_data_detailed['financialsAnnual']['income'] and 'eps' in ticker_data_detailed['financialsAnnual']['income'][0]) else float("NaN"), # extra check here and below since ETFs some other assets don't have income # ['defaultKeyStatistics']['trailingEps'] if ('trailingEps' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"), # maybe refactor - (unresolved) unsure why 'trailingEps' failing on quite a few Nano Cap tickers like: ['AEG', 'AJXA', 'YOLO', 'FFTY'] # if ('defaultKeyStatistics' in ticker_data_detailed...
                ticker_data_detailed['ratios'][0]['pegRatioTTM'] if 'pegRatioTTM' in ticker_data_detailed['ratios'][0] else float("NaN"), # P/E ratio / Expected Earnings Growth Rate
                None, # ticker_data_detailed['summaryDetail']['dividendYield'] if ('summaryDetail' in ticker_data_detailed and ticker_data_detailed['summaryDetail'] and 'dividendYield' in ticker_data_detailed['summaryDetail']) else float("NaN"),
                ticker_data_detailed['ratios'][0]['priceToBookRatioTTM'] if 'priceToBookRatioTTM' in ticker_data_detailed['ratios'][0] else float("NaN"),
                ticker_data_detailed['financialsAnnual']['income'][0]['ebitda'] if (ticker_data_detailed['financialsAnnual']['income'] and 'ebitda' in ticker_data_detailed['financialsAnnual']['income'][0]) else float("NaN"), # None, # ticker_data_detailed['defaultKeyStatistics']['enterpriseValue'] if ('enterpriseValue' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"),
                ticker_data_detailed['ratios'][0]['enterpriseValueMultipleTTM'] if 'enterpriseValueMultipleTTM' in ticker_data_detailed['ratios'][0] else float("NaN"), # None, # ticker_data_detailed['defaultKeyStatistics']['enterpriseToEbitda'] if ('enterpriseToEbitda' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"),
                ticker_data_detailed['ratios'][0]['debtEquityRatioTTM'] if 'debtEquityRatioTTM' in ticker_data_detailed['ratios'][0] else float("NaN"),
                ticker_data_detailed['financialsAnnual']['income'][0]['netIncomeRatio'] if (ticker_data_detailed['financialsAnnual']['income'] and 'netIncomeRatio' in ticker_data_detailed['financialsAnnual']['income'][0]) else float("NaN"),
                str([annual_income_statement['revenue'] for annual_income_statement in ticker_data_detailed['financialsAnnual']['income']]) if (ticker_data_detailed['financialsAnnual']['income'] and 'revenue' in ticker_data_detailed['financialsAnnual']['income'][0]) else None,
                str([annual_income_statement['grossProfitRatio'] for annual_income_statement in ticker_data_detailed['financialsAnnual']['income']]) if (ticker_data_detailed['financialsAnnual']['income'] and 'grossProfitRatio' in ticker_data_detailed['financialsAnnual']['income'][0]) else None,
                str([annual_balance_statement['totalAssets'] for annual_balance_statement in ticker_data_detailed['financialsAnnual']['balance']]) if (ticker_data_detailed['financialsAnnual']['balance'] and 'totalAssets' in ticker_data_detailed['financialsAnnual']['balance'][0]) else None,
                str([annual_balance_statement['totalLiabilities'] for annual_balance_statement in ticker_data_detailed['financialsAnnual']['balance']]) if (ticker_data_detailed['financialsAnnual']['balance'] and 'totalLiabilities' in ticker_data_detailed['financialsAnnual']['balance'][0]) else None,
                str([annual_balance_statement['cashAndCashEquivalents'] for annual_balance_statement in ticker_data_detailed['financialsAnnual']['balance']]) if (ticker_data_detailed['financialsAnnual']['balance'] and 'cashAndCashEquivalents' in ticker_data_detailed['financialsAnnual']['balance'][0]) else None,
                str([annual_balance_statement['longTermDebt'] for annual_balance_statement in ticker_data_detailed['financialsAnnual']['balance']]) if (ticker_data_detailed['financialsAnnual']['balance'] and 'longTermDebt' in ticker_data_detailed['financialsAnnual']['balance'][0]) else None,
                str([annual_income_statement['date'] for annual_income_statement in ticker_data_detailed['financialsAnnual']['income']]) if (ticker_data_detailed['financialsAnnual']['income'] and 'date' in ticker_data_detailed['financialsAnnual']['income'][0]) else None, # assuming "financialsAnnual" and "balance" have same annual dates (safe to assume since annual financial and balance sheet reports come out on the same date), # possibly add Long-term investments
                ticker_data_detailed['profile']['beta'] if 'beta' in ticker_data_detailed['profile'] else float("NaN"), # ticker_data_detailed['defaultKeyStatistics']['beta'] if ('beta' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"),
                None, # ticker_data_detailed['defaultKeyStatistics']['shortPercentOfFloat'] if ('shortPercentOfFloat' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"), # same as short interest, (Number of shares investors have sold short and have not yet covered)  /  (number of outstanding shares)
                None, # ticker_data_detailed['defaultKeyStatistics']['shortRatio'] if ('shortRatio' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"), # short ratio is the number of shorted shares divided by average daily trading volume, better metric than 'sharesShortPriorMonth'
                None, # ticker_data_detailed['Day range'] if 'Day range' in ticker_data_detailed else None,
                ticker_data_detailed['profile']['range'] if 'range' in ticker_data_detailed['profile'] else None,
                None, # ticker_data_detailed['summaryDetail']['twoHundredDayAverage'] if ('summaryDetail' in ticker_data_detailed and ticker_data_detailed['summaryDetail'] and 'twoHundredDayAverage' in ticker_data_detailed['summaryDetail']) else float("NaN"),
                None, # ticker_data_detailed['summaryDetail']['fiftyDayAverage'] if ('summaryDetail' in ticker_data_detailed and ticker_data_detailed['summaryDetail'] and 'fiftyDayAverage' in ticker_data_detailed['summaryDetail']) else float("NaN"),
                None, # ticker_data_detailed['defaultKeyStatistics']['morningStarOverallRating'] if ('morningStarOverallRating' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"),
                None, # ticker_data_detailed['defaultKeyStatistics']['heldPercentInstitutions'] if ('heldPercentInstitutions' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"),
                None, # ticker_data_detailed['defaultKeyStatistics']['heldPercentInsiders'] if ('heldPercentInsiders' in ticker_data_detailed['defaultKeyStatistics']) else float("NaN"), # ['raw'] if ticker_data_detailed['defaultKeyStatistics']['heldPercentInsiders'] else float("NaN")
                ticker_data_detailed['rating'][0]['ratingScore'] if (ticker_data_detailed['rating'] and 'ratingScore' in ticker_data_detailed['rating'][0]) else float("NaN"),
                pd.to_datetime(ticker_data_detailed['rating'][0]['date']) if 'date' in ticker_data_detailed['rating'][0] else None,
                None, # zacks_rank, # , #
                None # zacks_updated_at # , #
            ]
        except Exception as e:
            print(str(e) + " - No (or issue with) ticker data detailed FMP for ticker: " + ticker + " on exchange: " + asset.exchange + " on: " + str(datetime.now()) + ", Execution time: " + str(time.time() - start_time)) # or zacks data
    save_tickers_yf_and_fmp_data(df_usa_alpaca_tickers_fmp_ms_zr_data, date)
    return df_usa_alpaca_tickers_fmp_ms_zr_data

from unidecode import unidecode
from fake_headers import Headers

def get_crunchbase_search_permalinks(permalink, **params):
    # time.sleep(5) # since if return a long list (up to 25) will iterate over a long list will get json.decoder.JSONDecodeError: Expecting value: line 6 column 1 (char 5) error -> https://stackoverflow.com/questions/34579327/jsondecodeerror-expecting-value-line-1-column-1?rq=1
    permalinks = [] # maybe refactor and change this (declaring empty function return / half of what function returns at beginning of function) in this function and below crunchbase functions
    site_url = "https://www.crunchbase.com/v4/data/autocompletes?query=" + "%20".join(permalink.split("-")) + "&collection_ids=organizations&limit=25&source=topSearch" # maybe refactor limit=25, permalink.split("-"/" ")
    headers, cookies = params['headers'] if ('headers' in params and params['headers']) else Headers(os="mac", headers=True).generate(), params['cookies'] if ('cookies' in params and params['cookies']) else {'cid': 'CihjF2EJua4XkgAtPH5jAg==', '_pxhd': 'IhifXsIJ7A98ehR9VBprDcS2R0QJLw7ZvwUY8CR9jpoQ3fvPaRezXrWDUfCcqC75orD5OSnwJYS1ZP1A9ieOqQ==:-teWJPV0KWw6Vvnu46qXzIor-OW/6skuVb7jq-NfX4yCB-PpRiHoi31hJLDhl9vQQvj7qfVoeGpVqjlXPiFQqX6rZ/ihiPQ72Z1oh0nv1SE=', '__cflb': '02DiuJLCopmWEhtqNz5agBnHnWotHyxG4jgU9FLJcAXuE'} # maybe refactor here and below and add changing of exit IP address of request as described: https://www.scrapehero.com/how-to-fake-and-rotate-user-agents-using-python-3/
    resp = requests.get(site_url, headers=headers, cookies=cookies)
    soup = bs.BeautifulSoup(resp.text, 'html.parser')
    if (resp.status_code != 200) or not (soup and soup.text):
        data = [permalinks, resp.status_code]
        print("Crunchbase search permalinks failed for permalink: " + permalink + " ; returning: " + str(data))
        return data
    data = json.loads(soup.text) # assuming that this site_url returns a string in json format
    for entity in data['entities']:
        new_permalink = entity['identifier']['permalink']
        permalinks.append(new_permalink)
    return [permalinks, resp.status_code]

def get_crunchbase_permalink_site_check_ticker(ticker, permalink, retry=True, **params): # old name - crunchbase_check_ticker_if_company_name_equals_permalink
    data = []
    # time.sleep(randint(0, 3))
    site_url = "https://www.crunchbase.com/organization/" + permalink # "-".join(company_name.split()) # permalink = "-".join(permalink.split()) # permalink should already be in 'name-name-name' format but if get_crunchbase_permalink_site_check_ticker() returns on first option then if multiple words it's a normal string 'name name'
    headers, cookies = params['headers'] if ('headers' in params and params['headers']) else Headers(os="mac", headers=True).generate(), params['cookies'] if ('cookies' in params and params['cookies']) else {'cid': 'CihjF2EJua4XkgAtPH5jAg==', '_pxhd': 'IhifXsIJ7A98ehR9VBprDcS2R0QJLw7ZvwUY8CR9jpoQ3fvPaRezXrWDUfCcqC75orD5OSnwJYS1ZP1A9ieOqQ==:-teWJPV0KWw6Vvnu46qXzIor-OW/6skuVb7jq-NfX4yCB-PpRiHoi31hJLDhl9vQQvj7qfVoeGpVqjlXPiFQqX6rZ/ihiPQ72Z1oh0nv1SE=', '__cflb': '02DiuJLCopmWEhtqNz5agBnHnWotHyxG4jgU9FLJcAXuE'}
    resp = requests.get(site_url, headers=headers, cookies=cookies)
    soup = bs.BeautifulSoup(resp.text, 'html.parser')
    a_links = soup.find_all('a', {'class': 'link-primary'})
    if (resp.status_code != 200) or not a_links:  # not retrying requests since if fail usually fails after 9th try or so at which point the company probably doesn't exist on crunchbase (non-American company, other reasons) like AGMH or company is not worth searching for (not popular / queried enough) - when implemented only helped on SWCH (switch-6), CSCO (cisco), ICHR (ichor-systems), STNE (stone-pagamentos-sa), SREV (servicesource)
        data = [None, resp.status_code] # probably refactor quick fix
        print("Crunchbase permalink site check ticker failed for ticker: " + ticker + " and permalink: " + permalink + " ; returning: " + str(data))
        return data
    a_link_text = unidecode(a_links[0].text)
    user_data_categories = ['Stock Symbol'] # , possibly add acquisitions, total funding amount
    user_data_category = user_data_categories[0] # maybe refactor, to match get_crunchbase_data_for_ticker()
    ticker_from_site_url = re.search(user_data_category + ' (?:[a-zA-Z]+):[A-Z]{1,4}', a_link_text)[0].split()[-1].split(":")[-1] if re.search(user_data_category + ' (?:[a-zA-Z]+):[A-Z]{1,4}', a_link_text) else None # NYSE|NASDAQ|AMEX|ARCA|BATS NYSE|NASDAQ|AMEX|ARCA|BATS - leaves out exhances like Austria's VIE # .replace(',', '') # maybe refactor, precautionary not sure if need AMEX, ARCA, BATS (taken from Alpaca assets from saved tickers data)
    if ticker == ticker_from_site_url:
        data = [permalink, resp.status_code]
    else:
        data = [None, resp.status_code]
    print(permalink + " ; " + str(data))
    return data

from random import randint

def get_crunchbase_data_for_ticker(ticker, permalink_original, **params): # company is lowercase string like 'asana' # old name - get_crunchbase_user_data_for_company_with_ticker() # apply same logic in save_usa_alpaca_tickers_fmp_data() function with its own counter (separate from yahoo finance counter) # maybe refactor and remove resp.status_code from return [data, resp.status_code]
    print("<<< " + ticker + " >>>")
    data = {} # not needed but consistent with other functions # permalink_original, permalink,
    [permalink, resp_status_code], idx = get_crunchbase_permalink_site_check_ticker(ticker=ticker, permalink=permalink_original, **params), 0
    if not permalink:
        sleep_time = randint(3, 5) / 4
        print("Sleeping " + str(sleep_time) + "min before checking for new permalinks on: " + str(datetime.now()))
        time.sleep(sleep_time*60)
        params['headers'] = Headers(os="mac", headers=True).generate() if resp_status_code == 403 else params['headers']
        [new_permalinks, resp_status_code] = get_crunchbase_search_permalinks(permalink=permalink_original, **params) # maybe refactor here and below and add while loop with Headers(os="mac", headers=True).generate()
        print("New permalinks: " + str(new_permalinks) + " and resp status code: " + str(resp_status_code))
    while not permalink and idx < len(new_permalinks):
        [permalink, resp_status_code], idx = get_crunchbase_permalink_site_check_ticker(ticker=ticker, permalink=new_permalinks[idx], **params), idx + 1 # maybe refactor - if company name does not match ticker or get a 404 error then add words related to company bio/sector/industry (possibly from yahoo finance 'company profile': 'company was formerly known as ..., Inc.'), like -motors (for TSLA) and -computing (for snowflake)
    if not permalink:
        print("Returning empty dict since permalink check failed for ticker: " + ticker + " and original permalink: " + permalink_original + " on: " + str(datetime.now()))
        return [data, resp_status_code]
    # time.sleep(randint(0, 3))
    site_url = "https://www.crunchbase.com/organization/" + permalink + "/technology"
    headers, cookies = params['headers'], params['cookies']
    resp = requests.get(site_url, headers=headers, cookies=cookies) #  headers_list[randint(0,4)] # count , 0
    if permalink and resp.status_code != 200: # minor issue effected 25/537 tickers ~5% on 2021-08-12 18:36 -> 2021-08-13 03:56:09 run (9 hours for 693 tickers)
        print("Sleeping 1min since response status code is: " + str(resp.status_code) + " before retrying to obtain user data on: " + str(datetime.now()))
        time.sleep(1*60)
        resp = requests.get(site_url, headers=headers, cookies=cookies)
    soup = bs.BeautifulSoup(resp.text, 'html.parser')
    divs = soup.find_all('div', {'class': 'section-content-wrapper'}) # maybe change to: a_links = soup.find_all('a', {'class': 'link-primary'})
    if not divs: # len(divs) >= 5): # maybe refactor, if less than 5 probably not a tech  company or legit company / possibly something wrong with crunchbase site
        print("Returning empty dict since crunchbase site for permalink doesn't have the necessary data for ticker: " + ticker + " and permalink: " + permalink + " and response status code: " + str(resp.status_code) + " on: " + str(datetime.now()))
        return [data, resp.status_code]
    data['permalink'] = permalink
    div_text, div_text_4 = unidecode(divs[0].text), unidecode(divs[4].text) if len(divs) > 4 else '' # if len(divs) >= 5 else 'N\A' # probably refactor with user_data_categories iterating logic (4) quick fix
    user_data_categories = ['Total Products Active', 'Downloads Last 30 Days', 'Monthly Download Growth', 'Active Tech Count', 'Monthly Visits', 'Monthly Visits Growth'] # maybe add registered patents, trademarks, site rank (globally)
    for user_data_category in user_data_categories:
        div_text_implement = div_text_4 if user_data_category == 'Monthly Download Growth' else div_text # not merging div_text and div_text_4 because re.search() is more computationally expensive
        pattern = rf"{user_data_category} -?([0-9]+([.,])?)+" # chatgpt implementation of below
        match = re.search(pattern, div_text_implement) # chatgpt implementation of below
        data["_".join(user_data_category.lower().split())] = (float(match[0].split()[-1].replace(',', '')) if match else float("NaN")) # chatgpt implementation of below
        # data["_".join(user_data_category.lower().split())] = float(re.search(r"" + user_data_category + " -?([0-9]+(,|\.)?)+", div_text_implement)[0].split()[-1].replace(',', '')) if re.search(r"" + user_data_category + " -?([0-9]+(,|\.)?)+", div_text_implement) else float("NaN") # div_text_4
        if user_data_category in ['Monthly Visits Growth', 'Monthly Download Growth']:
            data["_".join(user_data_category.lower().split())] = data["_".join(user_data_category.lower().split())]/100
    # print(ticker + ": permalink: " + permalink + ", data: " + str(data)) # + ",\n headers: " + str(headers) + ", resp: " + str(resp)) #
    return [data, resp.status_code]

import math

# alpaca_exchanges = {'IEX (Investors Exchange LLC)', 'NYSE National, Inc.', 'Nasdaq BX, Inc.', 'Nasdaq PSX', 'NYSE Chicago, Inc.', 'AMEX'}
def alpaca_trade_ticker(ticker, side, usd_invest=None, quantity=None, price=None, paper_trading=True, open_time=5, other_notes=None): # added open_time due to retrying paper order 'FGF' error 2022-12-13 "Partially filled" listed as "~Filled" - in past testing conditions 0 "~Filled" positions which means open_order gets processed immediately but retrying paper orders are filled during market hours different testing conditions # maybe refactor side logic as precautionary in case alpaca api changes from normal "buy" and "sell" # fetching price and calculating quantity in method since better to get price as close to executing alpaca_api.submit_order as possible even though when not back_testing using same price for data analysis and trading (Alpaca), unlike in crypto - CoinGecko (which is exchange volume-weighted) for data analysis and Binance for trading
    # global portfolio_account, twilio_client, twilio_phone_from, twilio_phone_to
    if not (usd_invest or quantity): # or (quantity and not (quantity % int(quantity) == 0)) # using this implementation instead of: isinstance(quantity, int) since balance often comes in as 21.0 or 10.0 which according to isinstance is not an integer when it should pass as an integer/whole number # on alpaca (and on exchanges in general) can't buy fractions of shares (unless a brokerage breaks up shares and sells) in contrast to Binance (and crypto exchanges in general) but let "ATrade Error"
        raise ValueError("usd_invest or quantity required") #  and if quantity specified must be an integer
    last_trade_data = _fetch_data(alpaca_api.get_latest_trade, params={'symbol': ticker}, error_str=" - No last trade from Alpaca for ticker: " + ticker + " on: " + str(datetime.now()), empty_data = {})
    price = price if price else last_trade_data.price if last_trade_data else float("NaN") # price if price since possible price could change (mainly concerned with increase) in time between fetching price before and in alpaca_trade_ticker() and necessary to prevent quantity=0 error # float("NaN") so will throw error in alpaca_api.submit_order
    quantity = quantity if quantity else float("NaN") if np.isnan(price) else math.floor(usd_invest / price) if usd_invest > 10 else math.ceil(usd_invest / price) # not checking if price > usd_invest (resulting in fractions of a ticker) since would have to return "ATrade Error" which would lead to more logic downstream, easier to check before calling this function, also if it happens quantity = 0 and "ATrade Error" would occur # have to worry about insufficient USD available if round up (also good to be conservative with rounding down) and minimum order amounts if round down (unsure if this amount is correct for minimum trade amount, 0.001 for BTC on most exchanges which is ~$10 as of July 11 2020)
    if paper_trading:
        message_body = "Q Trading @stocks #" + portfolio_account + " (Paper Trading): " + ticker + " " + side + " at price $" + str(price) + " and quantity " + str(quantity) + ", " + str(other_notes) + ", :)" + ", at: " + str(datetime.now()) # maybe refactor here (or change all to be consistent with at:) using at: instead of on: since a unique case, listing date 2 times (when retrying orders and useful to know 2nd date since maybe a lot of trades) and only specific to this function
        print("executed alpaca_trade_ticker()\n" + "\033[94m" + message_body +  "\033[0m")
        return [quantity, price, {}, [], None] # for now don't want paper trades to be executed on alpaca, too complicated with os.environ etc.
    order = _fetch_data(alpaca_api.submit_order, params={
        'symbol': ticker,
        'qty': quantity,
        'side': side,
        'type': 'limit',
        'limit_price': round(price, 2), # sub-penny increment not allowed
        'time_in_force': 'gtc'
    }, error_str=" - Alpaca trade execution error for ticker: " + str(ticker) + ", " + str(side) + ", quantity: " + str(quantity) + ", limit_price: " + str(price) + " on: " + str(datetime.now()), empty_data={})
    if not order: # usually due to minimum amount issue, maybe refactor and raise error
        return [quantity, price, {}, [], "ATrade Error"] # maybe refactor 'ATrade Error' to 'ATrade error' to match casing of 'Not filled', 'Partially filled'
    open_orders = [open_order for open_order in _fetch_data(alpaca_api.list_orders, params={'status': 'open', 'nested': True}, error_str=" - Alpaca open orders error on: " + str(datetime.now()), empty_data=[]) if open_order.symbol == ticker and datetime.fromtimestamp(datetime.timestamp(open_order.created_at)) <= (datetime.now() + timedelta(minutes=1))] # maybe refactor minutes=1, depends on processing and on if implement open_time # datetime.fromtimestamp(datetime.timestamp() faster than open_order.created_at.to_pydatetime() and using datetime.utcnow() # show nested multi-leg orders # limit=100,
    if not float(order.filled_qty) and not open_orders: # if both of these conditions fail after order went through most likely means that more processing time (on Alpaca servers) is needed to process open_order (unlikely but possible that open_order was created and executed in the span of ~4 lines of code)
        time.sleep(open_time)
        open_orders = [open_order for open_order in _fetch_data(alpaca_api.list_orders, params={'status': 'open', 'nested': True}, error_str=" - Alpaca open orders error on: " + str(datetime.now()), empty_data=[]) if open_order.symbol == ticker and datetime.fromtimestamp(datetime.timestamp(open_order.created_at)) <= (datetime.now() + timedelta(minutes=1))]
    trade_notes = 'Filled' if (float(order.filled_qty) and not open_orders) else 'Not filled' if (not float(order.filled_qty) and open_orders and not float(open_orders['symbol' == ticker].filled_qty)) else 'Partially filled' if ((float(order.filled_qty) and open_orders) or (open_orders and float(open_orders['symbol' == ticker].filled_qty))) else "~Filled" # refactor "Not Filled" / "Partially filled" to something like (open_orders and not float(open_orders[0].filled_qty)) / (open_orders and float(open_orders[0].filled_qty)) # (quantity - float(order.filled_qty) == 0), ((quantity - float(order.filled_qty) == quantity) and any(open_orders)), any(open_orders) # '~Filled', if (order.status != 'accepted') else
    message_body = "Q Trading @stocks #" + portfolio_account + ": " + ticker + " " + side + " at price $" + str(price) + " and quantity " + str(quantity) + ", " + str(other_notes) + ", " + trade_notes + (" :)" if trade_notes == "Filled" else " :/" if trade_notes == "Partially filled" else " :(") + ", at: " + str(datetime.now())
    color_start, color_end = ["\033[92m", "\033[0m"] if trade_notes in ["Filled", "~Filled"] else ["\033[33m", "\033[0m"] if trade_notes == "Partially filled" else ["\033[91m", "\033[0m"] # ["\033[94m", "\033[0m"] if paper_trading else # blue for paper_trading, maybe refactor and add other color to function calls # green yellow red # last condition is if "Not filled" or "ATrade Error"
    print("executed alpaca_trade_ticker()\n" + color_start + message_body + color_end + "\n\033[1mOrder:\033[0m " + str(order) + "\n\033[1mOpen orders:\033[0m" + str(open_orders))
    twilio_message = _fetch_data(twilio_client.messages.create, params={'to': twilio_phone_to, 'from_': twilio_phone_from, 'body': message_body}, error_str=" - Twilio msg error to: " + twilio_phone_to + " on: " + str(datetime.now()), empty_data=None)
    return [quantity, price, order, open_orders, trade_notes] # maybe refactor and add position, price (since price often not the same as limit price - usually lower for buy, higher for sell), but complicated since order usually not filled immediately # can add check if order['fills'] 'qty'(s) equal quantity

def get_alpaca_assets(alpaca_account, alpaca_open_orders=[]):
    print("getting alpaca assets")
    assets = pd.DataFrame(columns=['balance', 'balance_locked', 'current_date', 'current_price', 'current_value', 'exchange', 'other_notes']).astype({'balance':'float64','balance_locked':'float64','current_date':'datetime64[ns]','current_price':'float64','current_value':'float64','exchange':'object','other_notes':'object'}) # refactor, can't find balance_locked value on alpaca api leave it for now
    if not alpaca_account: # only case if alpaca_account is {} like when about to restart portfolio from paper to real trading
        print("No Alpaca Account specified")
        return assets
    # maybe refactor and add ticker balance_locked by iterating over open_order.side == 'sell', lot of work for a little bit of extra minor detail that almost always isn't there (trading in highly liquid markets so unlikely that sell order wouldn't execute)
    usd_balance_locked = sum([(float(open_order.qty) - float(open_order.filled_qty))*float(open_order.limit_price) for open_order in alpaca_open_orders if open_order.side == 'buy']) # maybe refactor cheap way of figuring out usd balance_locked, more accurate than iterating over portfolio['open'] positions which are 'Not filled' since could be issues with assigning these trade_notes (which are only updated every hour), also this information is directly from alpaca servers
    assets.loc['USD'] = [float(alpaca_account.buying_power), usd_balance_locked, datetime.now(), 1.0, float(alpaca_account.buying_power) + usd_balance_locked, None, None]
    positions = _fetch_data(alpaca_api.list_positions, params={}, error_str=" - Alpaca positions error on: " + str(datetime.now()), empty_data=[]) # show nested multi-leg orders # limit=100,
    for position in positions:
        if position.symbol not in ['399RGT026']: # 399RGT026: Grupo Financiero Galicia S.A. Rights (underlying symbol GGAL; Expiration 02/06/25; DTC CA ID 147872186) - appeared 2025-01-23 morning caused crash
            assets.loc[position.symbol] = [float(position.qty), 0, datetime.now(), float(position.current_price), float(position.market_value), position.exchange, None]
    return assets

# can refactor and make it exchange_check_24h_vol
def fmp_check_24h_vol(ticker, fmp_24h_vol, datetime, fmp_24h_vol_min=5000, paper_trading=False): # 50000 (shares) min since binance_check_24h_vol_and_price_in_btc() has 5BTC has min which in 2020 =~ $50000
    # global portfolio_account, twilio_client, twilio_phone_from, twilio_phone_to
    fmp_24h_vol_too_low = False
    if fmp_24h_vol <= fmp_24h_vol_min:
        fmp_24h_vol_too_low = True
        message_body = "Q Trading @stocks #" + portfolio_account + ": " + ticker + " FMP 24h vol is less than " + str(fmp_24h_vol_min) + " on: " + str(datetime) + ", not buying :(" # datetime.now()
        print("\033[95m" + message_body + "\033[0m") # maybe refactor, repeated below but this way allows for customization and less logic at the end since both situations can occur together
        twilio_message = _fetch_data(twilio_client.messages.create, params={'to': twilio_phone_to, 'from_': twilio_phone_from, 'body': message_body}, error_str=" - Twilio msg error to: " + twilio_phone_to + " on: " + str(datetime.now()), empty_data=None) if not paper_trading else None
    return fmp_24h_vol_too_low

# from pytz import timezone
# pacific = timezone('US/Pacific')

def update_portfolio_postions_back_testing(portfolio, stop_day, end_day, **params): # maybe refactor name to update_portfolio_open_postions_back_testing, maybe integrate with portfolio_trading section so only have one function for both functions
    STOP_LOSS = portfolio['constants']['sl']
    TRAILING_STOP_LOSS_ARM, TRAILING_STOP_LOSS_PERCENTAGE = portfolio['constants']['tsl_a'], portfolio['constants']['tsl_p']
    END_DAY_OPEN_POSITIONS_GTRENDS_15D, END_DAY_OPEN_POSITIONS_FMP_24H_VOL = portfolio['constants']['end_day_open_positions_gtrends_15d'], portfolio['constants']['end_day_open_positions_fmp_24h_vol']
    tickers_with_stock_splits = params['tickers_with_stock_splits']
    tickers_to_avoid_splitting = {ticker: 'stock split already reflected on FMP' for ticker in ['POL','EXPR','DBGI','LTRY','SNMP','IDEX','CRKN','AGRI','REE','AREB','SOND','BSFC','AQB','ISPO','WATT','XXII','KXIN','NCMI','UXIN','DXF','SHPW','ALPP','FRSX','CRGE','MIMO','DMAQR','TANH','JL','NIVF']} # {'WLL': 'stock split not updated on yf', 'MYT': 'stock split not updated on yf'} # already covered in update_portfolio_buy_and_sell_tickers() add back if Yahoo Finance decides to update (hourly price data to match past daily price data) some tickers and not others # maybe refactor and add PDS: listed as PD:CA on Fidelity, split on November 11/12/2020, same day stock rose 20x
    for ticker in portfolio['open'].index:
        # hours=7 because 13-6.5=6.5 (which is 9:30EST == 6:30PST), and for some results 6.5 or 6.52 (1.2 minutes before opening) not enough to capture opening minute volume but 7 seemed sufficient, ending at 13 (16:00EST) seems to capture closing minute volume for cases tested
        ticker_data_granular = _fetch_data(get_ticker_data_granular_fmp, params={'ticker': ticker, 'start_datetime': stop_day, 'end_datetime': stop_day, 'interval': '1hour'}, error_str=" - No " + "1hour" + " ticker data for: " + ticker + " from datetime: " + str(stop_day) + " to datetime: " + str(stop_day), empty_data=pd.DataFrame()) # - timedelta(hours=7) # if change 'interval': '1h' to something else also need to change [:7] below
        if ticker_data_granular.empty: # 'market_data' not in ticker_data_granular or not ticker_data_granular['market_data']['market_cap']['usd']: # remove granular from error_str
            print("Error retreiving granular market data for ticker: " + ticker + " on date: " + stop_day.strftime('%Y-%m-%d')) # error message should be covered in method
            portfolio['open'].loc[ticker, 'other_notes'] = "MDI " +  stop_day.strftime('%Y-%m-%d') # MDI stands for Market Data Issue
        else:
            if (ticker not in tickers_to_avoid_splitting) and (ticker in tickers_with_stock_splits['symbol'].values): # ticker in tickers_with_stock_splits: # and (stop_day.date() < tickers_with_stock_splits[ticker]['ex_date'].date()) # and (ticker not in tickers_to_avoid_splitting) add back if Yahoo Finance decides to update (hourly price data to match past daily price data) some tickers and not others # because yahoo finance api updates past daily price data but not hourly price data following a stock split, maybe refactor if notice a change, assuming for now that it remains this way
                divide_factor, prev_split_ratio, prev_ex_date = 1, float("NaN"), None # prev_ex_date etc logic to prevent double splitting (splits on the first not the second) on FMP errors (planned and executed duplicates most likely not in that order but logically)
                for idx in tickers_with_stock_splits[tickers_with_stock_splits['symbol']==ticker].index.tolist(): # for ticker_with_stock_split_dict in tickers_with_stock_splits[ticker]:
                    ex_date = datetime.strptime(tickers_with_stock_splits.loc[idx, 'date'], '%Y-%m-%d')
                    prev_ex_date = prev_ex_date if prev_ex_date else (ex_date - timedelta(days=41))
                    if stop_day.date() < ex_date.date(): # if stop_day.date() < ticker_with_stock_split_dict['ex_date'].date():
                        split_ratio = tickers_with_stock_splits.loc[idx, 'numerator'] / tickers_with_stock_splits.loc[idx, 'denominator'] # # print(str(prev_ex_date) + ": " + str(ex_date) + ", " + str(prev_split_ratio) + ": " + str(split_ratio))
                        if (prev_split_ratio != split_ratio) and (ex_date >= prev_ex_date + timedelta(days=40)): # dates are in chronological order # 40 day buffer to prevent duplicates? - don't think any credible company would split same ratio within 40 day period # and (ex_date >= prev_ex_date + timedelta(days=10))
                            divide_factor *= (tickers_with_stock_splits.loc[idx, 'numerator'] / tickers_with_stock_splits.loc[idx, 'denominator']) # divide_factor *= ticker_with_stock_split_dict['split_ratio']
                            prev_split_ratio, prev_ex_date = split_ratio, ex_date
                ticker_data_granular[['open', 'high', 'low', 'close']] = ticker_data_granular[['open', 'high', 'low', 'close']].div([divide_factor]*len(ticker_data_granular), axis=0) # maybe refactor and add something precautionary if for some reason less or more than
            buy_price, tsl_armed, tsl_max_price, balance = portfolio['open'].loc[ticker, ['buy_price', 'tsl_armed', 'tsl_max_price', 'balance']]
            # print(ticker + " running on: " + str(stop_day) + ":\n" + str(ticker_data_granular))
            # here and when initially buy stock can add price_trend analysis
            tsl_or_sl = False
            price, price_change = float("NaN"), float("NaN") # in case ticker_data_granular not empty but issues with rows (ie row['index'].astimezone(pacific).date() != stop_day.date()) or not row['Volume'])
            for date_str,row in ticker_data_granular.iterrows(): # for idx,row in ticker_data_granular.reset_index(drop=False, inplace=False).iterrows(): # [:-1]# [:-1] since somcetimes yahoo finance data comes in with extra row with today's OHLC
                # print(str(row['index'].astimezone(pacific).date()) + " ; " + str(row['Volume'])) # price, price_change, tsl_armed, tsl_max_price = row['Adj Close'], -0.1, False, float("NaN")
                interval_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') - timedelta(hours=3) # FMP uses east coast as default, -3 for Pacific time
                if (interval_date.date() != stop_day.date()) or not row['volume']: # row['index'].astimezone(pacific).date()
                    continue
                # print("getting current price for: " + ticker + " on: " + str(stop_day))
                price = row['close'] if type(row['close']) is np.float64 else float("NaN") # 'Adj Close' # better to use 'Adj Close' according to articles, according to Zacks: adjusted closing price reflects the closing price of the stock in relation to other stock attributes (like subtracting dividends for all previous days before dividend payout which is why some historical prices may change and cause small changes in backtest results). In general, adjusted closing price is considered to be a more technically accurate reflection of true value of the stock
                price_change = (price - buy_price) / buy_price
                # print(str(row['Datetime']) + " price: " + str(price) + " price change: " + str(price_change))
                # if price_change >= TAKE_PROFIT_PERCENTAGE:
                if not tsl_armed and price_change >= TRAILING_STOP_LOSS_ARM:
                    tsl_armed, tsl_max_price = True, price
                if tsl_armed:
                    if price > tsl_max_price:
                        tsl_max_price = price
                    tsl_price_change = (price - tsl_max_price) / tsl_max_price
                    if tsl_price_change <= TRAILING_STOP_LOSS_PERCENTAGE:
                        sell_price = price # minutely data so don't need:  tsl_max_price * (1 + TRAILING_STOP_LOSS_PERCENTAGE) # * (1 - PRICE_UNCERTAINTY_PERCENTAGE)
                        portfolio['balance']['usd'] = portfolio['balance']['usd'] + sell_price*balance
                        position, buy_date, fmp_24h_vol, gtrends_15d, rank_rise_d, trade_notes = portfolio['open'].loc[ticker, ['position', 'buy_date', 'fmp_24h_vol', 'gtrends_15d', 'rank_rise_d', 'trade_notes']]
                        portfolio['sold'].loc[len(portfolio['sold'])], portfolio['open'] = [ticker, position, buy_date, buy_price, balance, interval_date, sell_price, (sell_price - buy_price) / buy_price, fmp_24h_vol, gtrends_15d, rank_rise_d, tsl_max_price, trade_notes, 'Sell by TSL'], portfolio['open'].drop(ticker) # no interval time so sell_date is a bit inaccurate here and in SL # stop_day # ] # datetime.strptime(row['index'].astimezone(pacific).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                        tsl_or_sl = True
                        break # maybe refactor here and below to continue to match portfolio_trading() below
                elif price_change <= STOP_LOSS:
                    sell_price = price # minutely data so don't need: buy_price * (1 + STOP_LOSS) # * (1 - PRICE_UNCERTAINTY_PERCENTAGE)
                    portfolio['balance']['usd'] = portfolio['balance']['usd'] + sell_price*balance
                    position, buy_date, fmp_24h_vol, gtrends_15d, rank_rise_d, tsl_max_price, trade_notes = portfolio['open'].loc[ticker, ['position', 'buy_date', 'fmp_24h_vol', 'gtrends_15d', 'rank_rise_d', 'tsl_max_price', 'trade_notes']]
                    portfolio['sold'].loc[len(portfolio['sold'])], portfolio['open'] = [ticker, position, buy_date, buy_price, balance, interval_date, sell_price, (sell_price - buy_price) / buy_price, fmp_24h_vol, gtrends_15d, rank_rise_d, tsl_max_price, trade_notes, 'Sell by SL'], portfolio['open'].drop(ticker) # , index=['ticker', 'sell_date', 'sell_price', 'roi', 'tsl_max_price', 'other_notes'])), ignore_index=True),  # # stop_day # datetime.strptime(row['index'].astimezone(pacific).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') # portfolio['sold'].append(portfolio['open'].loc[ticker].drop(['current_date','current_price','current_roi','tsl_armed','tsl_max_price','other_notes']).append(pd.Series([
                    tsl_or_sl = True
                    break
                # if idx == len(ticker_data_granular) - 1:
            if stop_day == end_day:
                if END_DAY_OPEN_POSITIONS_FMP_24H_VOL:
                    portfolio['open'].loc[ticker, 'fmp_24h_vol'] = ticker_data_granular['volume'].sum() # maybe refactor, not exact but close, with last row error for previous days during current market hours last row has 0 volume in all cases observed so shouldn't be an issue
                if END_DAY_OPEN_POSITIONS_GTRENDS_15D:
                    google_trends = _fetch_data(get_google_trends_pt, params={'kw_list': [ticker], 'from_date': stop_day - timedelta(days=15), 'to_date': stop_day}, error_str=" - No " + "google trends" + " data for ticker search term: " + ticker + " from: " + str(stop_day - timedelta(days=15)) + " to: " + str(stop_day), empty_data=pd.DataFrame())
                    google_trends_slope = trendline(google_trends.sort_values('date', inplace=False, ascending=True)[ticker]) if not google_trends.empty else float("NaN") # sort_values is precautionary, should already be ascending:  # , reverse_to_ascending=True
                    portfolio['open'].loc[ticker, 'gtrends_15d'] = google_trends_slope
            if not tsl_or_sl:
                portfolio['open'].loc[ticker, ['current_date','current_price','current_roi','tsl_armed','tsl_max_price']] = [stop_day, price, price_change, tsl_armed, tsl_max_price]
    return portfolio

def get_tickers_to_avoid_in_alpaca(df_usa_alpaca_tickers_of_the_day): # usa_alpaca_tickers_end_with_y_with_no_current_alpaca_trade_data
    if (not type(df_usa_alpaca_tickers_of_the_day) is pd.core.frame.DataFrame) or df_usa_alpaca_tickers_of_the_day.empty:
        print("Must pass a non-empty dataframe as parameter")
        return {}
    tickers_end_with_y = df_usa_alpaca_tickers_of_the_day[df_usa_alpaca_tickers_of_the_day.index.str.endswith("Y")]
    tickers_end_with_y_not_refleced_on_alpaca, tickers_end_with_y_reflected_on_alpaca, count = {}, [], 0
    for ticker in tickers_end_with_y.index:
        last_trade_data = _fetch_data(alpaca_api.get_latest_trade, params={'symbol': ticker}, error_str=" - No last trade from Alpaca for ticker: " + ticker + " on: " + str(datetime.now()), empty_data = {})
        if not last_trade_data:
            count += 1
            tickers_end_with_y_not_refleced_on_alpaca[ticker] = {'reason': 'stock information not on Alpaca', 'good_after_date': datetime.strptime('2029_06_06 13:00:00', '%Y_%m_%d %H:%M:%S')} # 2029 is some arbitrary date in future # tickers_end_with_y_not_refleced_on_alpaca.append(ticker)
        else:
            tickers_end_with_y_reflected_on_alpaca.append(ticker) # for other future purposes
    return tickers_end_with_y_not_refleced_on_alpaca # [, tickers_end_with_y_reflected_on_alpaca]

def get_tickers_to_avoid(df_usa_alpaca_tickers_of_the_day, end_day): # probably refactor
    if (not type(end_day) is datetime):
        print("End day must pass be of type datetime")
        return {}
    tickers_to_avoid_in_alpaca = get_tickers_to_avoid_in_alpaca(df_usa_alpaca_tickers_of_the_day)
    tickers_to_avoid = {**{'TLSA': 'yf issue with hourly/minutely vs. daily data', 'RVI': 'ticker price issue and stock split not found on yf'}, **{key: value['reason'] for key,value in {**{'WLL': {'reason': 'stock split not updated on yf', 'good_after_date': datetime.strptime('2020_09_03 13:00:00', '%Y_%m_%d %H:%M:%S')}, 'MYT': {'reason': 'stock split not updated on yf', 'good_after_date': datetime.strptime('2020_08_27 13:00:00', '%Y_%m_%d %H:%M:%S')}, 'IAC': {'reason': 'stock split not updated on yf', 'good_after_date': datetime.strptime('2021_05_25 13:00:00', '%Y_%m_%d %H:%M:%S')}, 'ELP': {'reason': 'stock split not updated on yf', 'good_after_date': datetime.strptime('2021_04_28 13:00:00', '%Y_%m_%d %H:%M:%S')}, 'AIV': {'reason': 'stock split not updated on yf', 'good_after_date': datetime.strptime('2020_12_15 13:00:00', '%Y_%m_%d %H:%M:%S')}}, **tickers_to_avoid_in_alpaca}.items() if end_day.date() < value['good_after_date'].date()}} # **{ticker: {'reason': 'stock information not on Alpaca', 'good_after_date': datetime.strptime('2029_06_06 13:00:00', '%Y_%m_%d %H:%M:%S')} for ticker in ['ADYEY', 'ATEYY', 'CTTAY', 'AMKBY', 'IFNNY', 'XIACY', 'NGLOY', 'NJDCY', 'SVNDY', 'PROSY', 'YZCAY', 'NVZMY', 'SFTBY', 'LSRCY', 'SMNEY', 'ZLNDY', 'MPNGY', 'HKXCY', 'GXYYY', 'SOBKY', 'TTDKY', 'NDEKY', 'HSHCY', 'SCHYY', 'GELYY', 'PNGAY', 'SHTDY', 'CRZBY', 'PBCRY', 'PPERY', 'WMMVY', 'ITOCY', 'ASHTY', 'OVCHY', 'SOUHY', 'LNVGY', 'SAXPY', 'RCRUY', 'ACGBY', 'IDCBY', 'BACHY', 'SDVKY', 'BAYRY', 'MURGY', 'BAESY', 'VWAGY', 'VWAPY', 'DHLGY', 'BASFY', 'NRDBY', 'BDRFY', 'MIELY', 'CSUAY', 'RNECY', 'ALIZY', 'CHGCY', 'SMMNY', 'BYDDY', 'TOELY', 'DSNKY', 'HOCPY', 'HTHIY', 'SSEZY', 'NCLTY', 'FANUY']} # possibly add 'EDU' (issues between 2020-10-06->2021-01-22), 'NTES' (issues between 2020-08-27->2020-09-29), 'ELP' (similar for 'AVI'): stop_day < 2021-03-18 (divide by 2 - 10/1 split followed by a 1/5 split) elif stop_day < 2021-04-28 (multiply by 5 - 1/5 split) # in general avoid tickers with low market cap and issues (not worth extra trouble of coding around) or tickers with multiple splits in short time period (maybe refactor - would also have to refactor tickers_with_stock_splits_in_day()) # not refactoring ‘stock split not updated on yf’ code (4 repeated) since different good_after_date(s)
    return tickers_to_avoid

def update_portfolio_buy_and_sell_tickers(portfolio, tickers_to_buy, tickers_to_sell, tickers_to_avoid, stop_day, paper_trading, back_testing):
    USD_INVEST, USD_INVEST_MIN = portfolio['constants']['usd_invest'], portfolio['constants']['usd_invest_min']
    BUY_DATE_GTRENDS_15D = portfolio['constants']['buy_date_gtrends_15d']
    for ticker, rank_rise_d in tickers_to_sell: # ticker, rank_rise_d = ticker_and_rank_rise_d[0], ticker_and_rank_rise_d[1]
        position, buy_price, quantity = portfolio['open'].loc[ticker, ['position', 'buy_price', 'balance']]
        if back_testing:
            sell_date, sell_price, roi, other_notes = portfolio['open'].loc[ticker, ['current_date', 'current_price', 'current_roi', 'other_notes']] # fmp_24h_vol 'fmp_24h_vol', # 'current_date', 'current_price', 'current_roi', maybe (if logic only for back_testing) can use np.append(ticker, portfolio['open'].loc[ticker, [...]].to_numpy()) sell_date, sell_price, roi, fmp_24h_vol, other_notes
            trade_notes = None
        else:
            quantity, price, alpaca_ticker_order, alpaca_ticker_open_orders, trade_notes = alpaca_trade_ticker(ticker=ticker, side="sell", quantity=quantity, paper_trading=(True if position == 'long-p' else False)) # paper_trading # assuming position is either 'long' or 'long-p' and that have to get rid of position if 'long' and therefore paper_trading is always False if position == 'long', and paper_trading is always True if position == 'long-p' # no short logic
            sell_date, sell_price, other_notes = datetime.now(), price, None # maybe refactor and use yahoo finance price if last_trade_data fails # sell_price ticker_data.iloc[-1]['Adj Close'] , fmp_24h_vol ticker_data.iloc[-1]['Volume'] # sell_price last_trade_data.price if last_trade_data else None, # maybe refactor - add back fmp_24h_vol if want to check for pump and dump but complicates matters when checking for buying and selling # make other_notes = None since MDI (or other) no longer
            roi = (sell_price - buy_price) / buy_price
        portfolio['balance']['usd'] = portfolio['balance']['usd'] + sell_price*quantity
        # ticker_data already retrieved in current_date, current_price, current_roi # can use np.append(ticker, portfolio['open'].loc[ticker, [...]].to_numpy())
        buy_date, fmp_24h_vol, gtrends_15d, rank_rise_d, tsl_max_price = portfolio['open'].loc[ticker, ['buy_date', 'fmp_24h_vol', 'gtrends_15d', 'rank_rise_d', 'tsl_max_price']]
        portfolio['sold'].loc[len(portfolio['sold'])], portfolio['open'] = [ticker, position, buy_date, buy_price, quantity, sell_date, sell_price, roi, fmp_24h_vol, gtrends_15d, rank_rise_d, tsl_max_price, trade_notes, other_notes], portfolio['open'].drop(ticker) # stop_day # ] # portfolio['sold'], portfolio['open'] = portfolio['sold'].append(portfolio['open'].loc[ticker].drop(['current_date', 'current_price', 'current_roi', 'tsl_armed', 'trade_notes', 'other_notes']).append(pd.Series([ticker, sell_date, sell_price, roi, trade_notes, other_notes], index=['ticker', 'sell_date', 'sell_price', 'roi', 'trade_notes', 'other_notes'])), ignore_index=True), portfolio['open'].drop(ticker) # 'fmp_24h_vol',fmp_24h_vol,'fmp_24h_vol', # other_notes to avoid confusion with previous notes, maybe refactor to 'Sell by Algo'
    for ticker, rank_rise_d in tickers_to_buy: # buy at end of day (13:00PST),when retrieve ticker information # ticker, rank_rise_d = ticker_and_rank_rise_d[0], ticker_and_rank_rise_d[1] # process takes about ~0.7 seconds to buy each ticker (I think maybe analysis was done with coin)
        if (portfolio['balance']['usd'] >= USD_INVEST_MIN) and (ticker not in tickers_to_avoid): # and (ticker not in portfolio['sold']['ticker'].values) # can add max open positions and waiting list to reflect real trading, don't allow repeat buys of same company since repeat buys reflect long-term investment in company / more exposure to single asset
            usd_invest = USD_INVEST if (portfolio['balance']['usd'] >= USD_INVEST) else portfolio['balance']['usd']
            # getting ticker_data for both back_testing and not back_testing since using volume (maybe refactor - until find an alpaca api function that returns real time price and volume - currently Alpaca doesn't support volume) and price if alpaca api error at end of day, and stop_day would be the current day if running in real time (not back_testing)
            ticker_data = _fetch_data(get_ticker_data_fmp, params={'ticker': ticker, 'start_datetime': stop_day, 'end_datetime': stop_day}, error_str=" - No " + "1d" + " ticker data for: " + ticker + " from datetime: " + str(stop_day) + " to datetime: " + str(stop_day), empty_data=pd.DataFrame()) # - timedelta(hours=7) # not minutely data event though faster since need 24h volume # assuming based on experience that daily prices for tickers are up-to-date in regards to stock splits
            if ticker_data.empty: # think here and throughout places with empty_data potential issues are covered (for example in situations like so: pd.DataFrame.iloc[-1]['Adj Close']) # maybe refactor and add check if 'price' in ticker_data # shouldn't be error with get_ticker_data # 'market_data' not in ticker_data or not ticker_data['market_data']['market_cap']['usd']: # remove granular from error_str
                print("Error retreiving initial market data for ticker: " + ticker + " on date: " + stop_day.strftime('%Y-%m-%d'))
            else:
                price, fmp_24h_vol = ticker_data.iloc[-1]['close'] if 'close' in ticker_data.columns else float("NaN"), ticker_data.iloc[-1]['volume'] if 'volume' in ticker_data.columns else float("NaN") # 'Adj Close' # maybe refactor above and below stop_day and run_portfolio() call since when run_portfolio() is called in realtime stop_day is 6pm therefore - timedelta(hours=7) doesn't really make sense but all we need is end of day price and fmp_24h_vol so good for now
                if (price > usd_invest): # simpler to put this logic here and retry_atrade_error_or_paper_orders_in_portfolio() rather than in alpaca_trade_ticker() (and make it continue here if trade_notes == "ATrade Error" or something similar) to prevent quantity=0 error # if change need to update price=price, in alpaca_trade_ticker() calls # maybe refactor - don't want to buy fractions of a ticker/stock for now
                    continue # maybe refactor, can print error statement like: print("skipping ticker: " + ticker + " because price > usd_invest on: " + str(stop_day))
                # checking fmp_24h_vol_too_low even though higher overall (and average) Market Cap and Volume for stock market compared to crypto market due to some outliers (for example 'QK' on 10/05/2020) and similar volume statistics at the low end of stock market, not checking for price differential since Alpaca trades on 5 different exchanges already
                fmp_24h_vol_too_low = fmp_check_24h_vol(ticker=ticker, fmp_24h_vol=fmp_24h_vol, datetime=stop_day, paper_trading=paper_trading) if fmp_24h_vol > 0 else True # *binance_pairs_with_price_current['BTCUSDT']
                if fmp_24h_vol_too_low:
                    continue
                if back_testing:
                    buy_date, quantity, trade_notes = stop_day, math.floor(usd_invest / price) if usd_invest > 10 else math.ceil(usd_invest / price), None # quantity - precautionary keep > 10 in case USD_INVEST_MIN is set below this amount
                else:
                    quantity, price, alpaca_ticker_order, alpaca_ticker_open_orders, trade_notes = alpaca_trade_ticker(ticker=ticker, side="buy", usd_invest=usd_invest, paper_trading=paper_trading) # not setting price=price, even though potential quantity=0 error from price > usd_invest logic, since price is yahoo finance price, refactor if issue
                    buy_date = datetime.now() # price last_trade_data.price if last_trade_data else None, # maybe refactor and use yahoo finance price if last_trade_data fails # sell_price ticker_data.iloc[-1]['Adj Close']
                if BUY_DATE_GTRENDS_15D:
                    # using Pytrends (Cryptory is deprecated doesn't work after Python 3.6-3.8) since good data and can retrieve other metrics like reddit subscribers, exchange rates, metal prices
                    google_trends = _fetch_data(get_google_trends_pt, params={'kw_list': [ticker], 'from_date': stop_day - timedelta(days=15), 'to_date': stop_day}, error_str=" - No " + "google trends" + " data for ticker search term: " + ticker + " from: " + str(stop_day - timedelta(days=15)) + " to: " + str(stop_day), empty_data=pd.DataFrame())
                    google_trends_slope = trendline(google_trends.sort_values('date', inplace=False, ascending=True)[ticker]) if not google_trends.empty else float("NaN") # sort_values is precautionary, should already be ascending:  # , reverse_to_ascending=True
                else:
                    google_trends_slope = 0
                portfolio['balance']['usd'] = portfolio['balance']['usd'] - price*quantity
                portfolio['open'].loc[ticker, ['position', 'balance', 'buy_date', 'buy_price', 'current_date', 'current_price', 'current_roi', 'fmp_24h_vol', 'gtrends_15d', 'rank_rise_d', 'tsl_armed', 'trade_notes']] = [('long' if not paper_trading else 'long-p'), quantity] + [buy_date, price]*2 + [0, fmp_24h_vol, google_trends_slope, rank_rise_d, False, trade_notes] # assuming buying at ~20 PST which means order gets executed at start of day next day every day # maybe refactor 'long-p' - alpaca
    return portfolio

def get_sp500_ranked_tickers_by_slickcharts() :
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10 7 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    resp = requests.get('https://www.slickcharts.com/sp500', headers=headers, verify=False)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'table table-hover table-borderless table-sm'})
    df_tickers = pd.DataFrame(columns = ["Company Name", "S&P 500 Rank", "Weight", "Price", "Price Change"]).astype({'Company Name': 'object','S&P 500 Rank': 'float64', 'Weight': 'float64', 'Price': 'float64', 'Price Change': 'float64'})
    for idx,row in enumerate(table.find_all('tr')[1:]):
        tds = row.find_all('td')
        sp500_rank = float(tds[0].text.strip())
        company_name, ticker = tds[1].text.strip(), tds[2].text.strip()
        weight, price, price_change = float(tds[3].text.strip().replace('%',''))/100, float(tds[4].text.strip().replace(',','')), float(tds[6].text.strip().replace('%','').replace('(','').replace(')',''))/100
        df_tickers.loc[ticker, ["Company Name", "S&P 500 Rank", "Weight", "Price", "Price Change"]] = [company_name, sp500_rank, weight, price, price_change]
    return df_tickers

# not working atm
def get_sp500_ranked_tickers_by_marketbeat():
    resp = requests.get('https://www.marketbeat.com/types-of-stock/sp-500-stocks/') # , verify=False # ISSUE - site doesn't update data daily it's a 1 day lag, 'http://en.wikipedia.org/wiki/List_of_S%26P_500_companies
    soup = bs.BeautifulSoup(resp.text, 'lxml') # 'html.parser'
    table = soup.find('table', {'class': 'scroll-table sort-table'}) # 'wikitable sortable'
    df_tickers = pd.DataFrame(columns = ["Company Name", "S&P 500 Rank", "Price", "Price Change"]).astype({'Company Name': 'object','S&P 500 Rank': 'float64', 'Price': 'float64', 'Price Change': 'float64'}) # think since assigning multiple values at once below
    for idx,row in enumerate(table.find_all('tr')[1:]):
        tds = row.find_all('td')
        sp500_rank = idx + 1 # since start at 1:
        ticker, company_name = [ticker_or_company_name.strip() for ticker_or_company_name in tds[0]['data-clean'].split('|')]
        price, price_change = [float(re.sub(r"[^\d\.\-]", "", price_or_price_change)) for price_or_price_change in tds[1]['data-clean'].split('|')]
        price_change = price_change / 100
        df_tickers.loc[ticker, ['Company Name', 'S&P 500 Rank', 'Price', 'Price Change']] = [company_name, sp500_rank, price, price_change]
    return df_tickers

def run_portfolio(portfolio, **params): # call portfolio = run_portfolio(portfolio, **params) for all functions below, if pass paper_trading=True in run_portfolio() params should pick it up and treat as a normal parameter in run_portfolio_rr etc # start_day=None, end_day=None, algo_sell=True, paper_trading=True, back_testing=False, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 240, 'days': 15}
    if portfolio['constants']['type'] == 'rr':
        portfolio = run_portfolio_rr(portfolio, **params) # start_day=start_day, end_day=end_day, rr_sell=algo_sell, paper_trading=paper_trading, back_testing=back_testing, add_pauses_to_avoid_unsolved_error=add_pauses_to_avoid_unsolved_error
    elif portfolio['constants']['type'] == 'zr':
        portfolio = run_portfolio_zr(portfolio, **params)
    elif portfolio['constants']['type'] == 'tilupccu':
        portfolio = run_portfolio_tilupccu(portfolio, **params)
    elif portfolio['constants']['type'] == 'mmtv':
        portfolio = run_portfolio_mmtv(portfolio, **params)
    elif portfolio['constants']['type'] == 'random_sp500':
        portfolio = run_portfolio_random_sp500(portfolio, **params)
    elif portfolio['constants']['type'] == 'mm':
        portfolio = run_portfolio_mm(portfolio, **params)
    elif portfolio['constants']['type'] == 'airs':
        portfolio = run_portfolio_ai_recommendations_in_sector(portfolio, **params)
    elif portfolio['constants']['type'] == 'tngaia':
        portfolio = run_portfolio_top_n_gainers_ai_analysis(portfolio, **params)
    elif portfolio['constants']['type'] == 'senate_trading':
        portfolio = run_portfolio_senate_trading(portfolio, **params)
    elif portfolio['constants']['type'] == 'sma_mm':
        portfolio = run_portfolio_sma_mm(portfolio, **params)
    return portfolio

from pandas.tseries.holiday import USFederalHolidayCalendar # import holidays - add back if works
usa_cal = USFederalHolidayCalendar()

def check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, back_running_allowance=17.5, **params):
    days = portfolio['constants']['days']
    end_day = end_day if end_day else datetime.now().replace(hour=13, minute=0, second=0, microsecond=0) # maybe refactor, markets are from 9:30 - 16:00 EST / 6:30 - 13:00 PST # maybe refactor - add precautionary check here and below to see if datetime.now() is after 13h
    start_day = start_day if start_day else end_day - timedelta(days=days)
    stop_day = start_day + timedelta(days=days)
    if (back_testing and not paper_trading) or (not back_testing and (stop_day < datetime.now() - timedelta(hours=back_running_allowance))): # back_running_allowance=11 for airs for some reason # 6:30am (new data arrives - except weekends & holidays) - 01:00pm previous day = 17.5 # assuming datetime input is always in 13:00:00 and run after market close of the stop_day # (stop_day.date() != datetime.now().date()) # maybe refactor here and below, allow 24 hours or more custom (especially if run update_portfolio_buy_and_sell_tickers() more than once per day after market hours as it is now or if account for running on weekends) # could also be more like in crypto.py or add full datetime comparison # here and below no need to check for (end_day.date() <= start_day.date()) since while loop won't execute (since stop_day is always > start_day will be greater than end_day)
        print("Error (backtesting and not paper trading) or back running")
        return ["Error", portfolio, None, None, None, None, None, None, None, None]
    if start_day.date() < datetime.strptime('2020_05_08 13:00:00', '%Y_%m_%d %H:%M:%S').date():
        print("Error saved S&P 500 tickers data with ['zr'] ordered alphabetically rather than by S&P 500 rank on 2020-04-24 and 2020-04-27, only have S&P 500 ranked (not by Market Cap) tickers data before 2020-05-08") # ['zr'] to match other error strings # "Error no saved TradingView Ratings before 2020-05-08"
        return ["Error", portfolio, None, None, None, None, None, None, None, None]
    if 'tickers_to_avoid' in params: # this is needed for backtesting and real running
        tickers_to_avoid = params['tickers_to_avoid']
    else:
        df_tickers_end_day = get_saved_tickers_data(date=end_day.strftime('%Y-%m-%d'))
        tickers_to_avoid = get_tickers_to_avoid(df_tickers_end_day, end_day)
    if back_testing:
        tickers_with_stock_splits = params['tickers_with_stock_splits'] if 'tickers_with_stock_splits' in params else get_tickers_with_stock_splits_fmp(start_day=start_day) # since difference between daily (updated) and hourly (not updated) yahoo finance data for stocks that split after start day - this line in update_portfolio_postions_back_testing(): stop_day.date() < tickers_with_stock_splits[ticker]['ex_date'].date() should take care of issue
        count = 0 # since unresolved OSError: (50, 'ENETDOWN'/etc.), pause 60s every 30 days (most recently errored 2 months out)
    else:
        tickers_with_stock_splits, count = None, None
    usa_holidays = usa_cal.holidays(start=start_day.replace(month=1, day=1).strftime('%Y-%m-%d'), end=end_day.replace(month=12, day=31).strftime('%Y-%m-%d')).to_pydatetime() # usa_holidays = holidays.UnitedStates() # usa instead of us to be consistent with folder name and to be consistent across country names # only USA holidays for now since only working with tickers listed on USA exchanges
    # TAKE_PROFIT_PERCENTAGE = 1.0
    # PRICE_UNCERTAINTY_PERCENTAGE = 0.05 # to reflect that can't always buy/sell at Yahoo Finance price and that stop loss and trailing stop loss orders can't always be fulfilled at the exact percentage
    # SHORT = False # possibly add short logic
    # get most exchange tickers listing
    # exchange_prices = exchange_client.get_all_tickers()
    return ["Success", portfolio, days, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays]

# Not merging run_portfolio_zr/rr into single function since even though it appears that sometimes only difference in algorithm functions is how to pick tickers there can be nuiances like if portfolio['constants']['up_down_move'] > 4: in run_portfolio_zr() and potentially more between portfolios
# can make it run_portfolio_tr as well with tr_sell instead of zr_sell, 'Rating' instead of 'Zacks Rank', # maybe refactor and add error regarding start_day being before 2020-04-24 or 2020-05-08 since 05/08/2020 is first day with larger USA-listed stocks data (~4900 tickers) set, before that (04/24/2020 - 05/08/2020) it's smaller S&P 500 (505 tickers) data set, 04/24/2020 is first day with stock tickers data
def run_portfolio_zr(portfolio, start_day=None, end_day=None, zr_sell=True, paper_trading=True, back_testing=False, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 240, 'days': 15}, **params): # refactor add paper_trading, back_testing # start_day and end_day are datetime objects # keep **params here and in run_portfolio_rr() so can use tickers_with_stock_splits for backtesting cases in which the fidelity service is down but the data for start_day and end_day is already loaded
    print("running run_portfolio_zr()")
    # Basic error checks for now
    if (not type(portfolio['constants']['up_down_move']) is int) or not (1 <= portfolio['constants']['up_down_move'] <= 4): # here and below chatgpt simpler answer to: (portfolio['constants']['up_down_move'] < 0) or (portfolio['constants']['up_down_move'] > 4)
        print("Error up/down move constant is not an int within 1-4 inclusive")
        return portfolio
    UP_MOVE, DOWN_MOVE = portfolio['constants']['up_down_move'], -portfolio['constants']['up_down_move'] # maybe refactor and add similar to up_down_move with difference between start day's zacks rank and stop day's zacks rank,
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    while stop_day.date() <= end_day.date():
        if not (portfolio['open']['current_date'] >= stop_day).any(): # in case re-run existing portfolio over same days to avoid back running (and conserve time): avoid selling existing tickers incorrectly to TSL (too early) due to tsl_max_price set on future day or selling/buying existing/new tickers incorrectly with algorithm logic # assuming datetime is always in 13:00:00
            if back_testing:
                count += 1
                if add_pauses_to_avoid_unsolved_error['engaged'] and (count % add_pauses_to_avoid_unsolved_error['days'] == 0): # maybe refactor and put count in get_ticker_data/get_ticker_data_detailed
                    print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['days']) + " days on date: " + str(stop_day.date()))
                    time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                portfolio = update_portfolio_postions_back_testing(portfolio=portfolio, stop_day=stop_day, end_day=end_day, tickers_with_stock_splits=tickers_with_stock_splits) #  # maybe refactor throughout and make it function(param1, param2, ...) rather than function(param1=param1, param2=param2, ...)
            if zr_sell or (portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min']):
                interval_start_date = stop_day - timedelta(days=DAYS)
                while interval_start_date.weekday() > 4 or (interval_start_date.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # no .replace(tzinfo=None) in run_portfolio_algo() since datetime for start/end/stop_day should be in local time (PST) # maybe refactor here and run_portfolio_algorithm's - potentially a lot of processing for a simple holidays check # interval_start_date = interval_start_date if (interval_start_date.weekday() < 5) else (interval_start_date - timedelta(days=interval_start_date.weekday()-4)) # to avoid weekends, always go further back than forward
                    interval_start_date = interval_start_date - timedelta(days=1)
                df_tickers_interval_start, df_tickers_interval_stop = get_saved_tickers_data(date=interval_start_date.strftime('%Y-%m-%d')), get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
                if not (df_tickers_interval_start.empty or df_tickers_interval_stop.empty): # df_tickers_interval_stop.empty
                    # refactor and add logic for dealing with if zacks rank is in  df_tickers_interval_start/stop
                    tickers_to_buy, tickers_to_sell = [], [] # Counter(), Counter()
                    for ticker in df_tickers_interval_stop.index:
                        try:
                            if (ticker not in portfolio['open'].index) and (df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] < 3) and (df_tickers_interval_start.loc[ticker, 'Zacks Rank'] >= 3): # care if ticker has just turned to buy # convenient since if 'Zacks Rank' is None conditional expression returns False instead of returning an error and continues, much faster
                                rank_change = df_tickers_interval_start.loc[ticker, 'Zacks Rank'] - df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] # can also make it rating_change if using tr 'Rating'
                                if rank_change >= UP_MOVE:
                                    tickers_to_buy.append([ticker, rank_change]) # tickers_to_buy[ticker] = df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] - df_tickers_interval_start.loc[ticker, 'Zacks Rank']
                            elif zr_sell and (ticker in portfolio['open'].index) and (portfolio['open'].loc[ticker, 'trade_notes'] in ["Filled", "~Filled", None]) and (df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] > 3): # don't care if ticker has just turned to sell or has been sell for a while: if (df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] > 3) and (df_tickers_interval_start.loc[ticker, 'Zacks Rank'] <= 3):
                                rank_change = df_tickers_interval_start.loc[ticker, 'Zacks Rank'] - df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] # can also make it rating_change if using tr 'Rating'
                                if rank_change <= DOWN_MOVE:
                                    tickers_to_sell.append([ticker, rank_change]) # tickers_to_sell[ticker] = df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] - df_tickers_interval_start.loc[ticker, 'Zacks Rank']
                        except Exception as e:
                            print(str(e) + " - Unable to execute, " + ticker + " not in df_tickers_interval_stop on: " + stop_day.strftime('%Y-%m-%d') + " or not in df_tickers_interval_start on: " + interval_start_date.strftime('%Y-%m-%d'))
                    if (tickers_to_buy or tickers_to_sell):
                        portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=tickers_to_buy, tickers_to_sell=tickers_to_sell, tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=back_testing)
        else:
            print("skipping " +  str(stop_day) + " since portfolio has already run on this date")
        stop_day = stop_day + timedelta(days=1)
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # interval_start_date/stop_day in usa_holidays # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday())) # to avoid weekends, refactor to avoid holidays (2020-05-25)
            stop_day = stop_day + timedelta(days=1)
    return portfolio

def run_portfolio_rr(portfolio, start_day=None, end_day=None, rr_sell=True, paper_trading=True, back_testing=False, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 240, 'days': 15}, **params): # 04/24/2020 and 04/27/2020 doesn't have proper ranking, before 05/08/2020 only have S&P 500 Rank which is not Market Cap rank # maybe refactor rr_buy/sell to algo_buy/sell, especially if add more algorithms # , rr_buy=True
    print("running run_portfolio_rr()")
    if (not type(portfolio['constants']['up_down_move']) is int) or not (1 <= portfolio['constants']['up_down_move'] <= 100): #  (portfolio['constants']['up_down_move'] < 0) or (portfolio['constants']['up_down_move'] > 100)
        print("Error up/down move constant is not an int within 1-100 inclusive")
        return portfolio
    UP_MOVE, DOWN_MOVE = portfolio['constants']['up_down_move'], -portfolio['constants']['up_down_move']
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    while stop_day.date() <= end_day.date():
        if not (portfolio['open']['current_date'] >= stop_day).any(): # in case re-run existing portfolio over same days to avoid back running (and conserve time): avoid selling existing tickers incorrectly to TSL (too early) due to tsl_max_price set on future day or selling/buying existing/new tickers incorrectly with algorithm logic # assuming datetime is always in 13:00:00
            if back_testing:
                count += 1
                if add_pauses_to_avoid_unsolved_error['engaged'] and (count % add_pauses_to_avoid_unsolved_error['days'] == 0):
                    print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['days']) + " days on date: " + str(stop_day.date()))
                    time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                portfolio = update_portfolio_postions_back_testing(portfolio=portfolio, stop_day=stop_day, end_day=end_day, tickers_with_stock_splits=tickers_with_stock_splits) #
            if rr_sell or (portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min']):
                interval_start_date = stop_day - timedelta(days=DAYS)
                while interval_start_date.weekday() > 4 or (interval_start_date.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # only USA holidays for now since only working with tickers listed on USA exchanges # interval_start_date = interval_start_date if (interval_start_date.weekday() < 5) else (interval_start_date - timedelta(days=interval_start_date.weekday()-4)) # to avoid weekends and holidays, always go further back rather than forward (more conservative)
                    interval_start_date = interval_start_date - timedelta(days=1)
                df_tickers_interval_start, df_tickers_interval_stop = get_saved_tickers_data(date=interval_start_date.strftime('%Y-%m-%d')), get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
                if not (df_tickers_interval_start.empty or df_tickers_interval_stop.empty): # df_tickers_interval_stop.empty
                    df_tickers_interval_start, df_tickers_interval_stop = df_tickers_interval_start[df_tickers_interval_start['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False), df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False) # maybe refactor and only deal with equities (not ETFs, etc.)
                    tickers_to_buy, tickers_to_sell = [], [] # Counter(), Counter()
                    for ticker in df_tickers_interval_stop.index: # (df_tickers_interval_stop if stop_day.date() < datetime.strptime('2020-05-08', '%Y-%m-%d').date() else df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] >= 2e9]).index: # df_tickers_interval_stop # if want to deal only with Mega, Large, Mid-Cap companies since smaller companies could cause complications with exchange listings etc. (but not on alpaca), S&P 500 tickers from 04/24/2020 until 05/08/2020
                        new_market_cap_rank = df_tickers_interval_stop.index.get_loc(df_tickers_interval_stop.loc[ticker].name)
                        try:
                            market_cap_rank_change = df_tickers_interval_start.index.get_loc(df_tickers_interval_start.loc[ticker].name) - new_market_cap_rank
                        except: # unlikely that a company with >= $2bn market cap would fall out of list of usa tickers precautionary except for when using only S&P 500 tickers from 04/24/2020 until 05/08/2020
                            market_cap_rank_change = 0 # if there is a new ticker that enters tradingview usa tickers screener / alpaca (I think) means IPO which we don't want # market_cap_rank_change = len(df_tickers_interval_start) - new_market_cap_rank if math.isclose(len(df_tickers_interval_stop), len(df_tickers_interval_start), rel_tol=0.2) else 0 # don't add UP_MOVE/DOWN_MOVE to be safe, 20% tolerance 4940 between 3952, 5928
                        if (ticker not in portfolio['open'].index) and (market_cap_rank_change >= UP_MOVE): # rr_buy and
                            tickers_to_buy.append([ticker, market_cap_rank_change])
                        elif rr_sell and (ticker in portfolio['open'].index) and (portfolio['open'].loc[ticker, 'trade_notes'] in ["Filled", "~Filled", None]) and (market_cap_rank_change <= DOWN_MOVE):
                            tickers_to_sell.append([ticker, market_cap_rank_change])
                    # Since only S&P 500 tickers from 04/24/2020 until 05/08/2020 and unlikely that a company with >= $2bn market cap would fall out of list of usa tickers not including this check, also if falls out of tradingview usa tickers screener probably means can't sell it on exchange
                    # for ticker in list(set(df_tickers_interval_start.index.values) - set(df_tickers_interval_stop.index.values)):
                    #     tickers_to_sell.append([ticker, df_tickers_interval_start.index.get_loc(df_tickers_interval_start.loc[ticker].name) - (len(df_tickers_interval_start) - DOWN_MOVE)])
                    if (tickers_to_buy or tickers_to_sell):
                        portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=tickers_to_buy, tickers_to_sell=tickers_to_sell, tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=back_testing)
        else:
            print("skipping " +  str(stop_day) + " since portfolio has already run on this date")
        stop_day = stop_day + timedelta(days=1)
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # maybe refactor - stop_day logic not initially set since don't mind scenario where in initial run running portfolio with open positions on a stop_day that is a weekend/holiday # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday()))
            stop_day = stop_day + timedelta(days=1)
    return portfolio

from collections import Counter

def run_portfolio_tilupccu(portfolio, start_day=None, end_day=None, paper_trading=True, back_testing=False, top_interval_losers=100, custom_order=True, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 240, 'days': 15}, **params): # not implementing tilupccu_sell since don't want to set DOWN_MOVE as (~0, might buy some very undervalued tickers), could add tilupccu_sell that acts like tsl if pb >= 1
    print("running run_portfolio_tilupccu()")
    if (not type(portfolio['constants']['up_down_move']) is list) or len(portfolio['constants']['up_down_move']) != 2:
        print("Error up/down move constant is not a list or a list with length 2")
        return portfolio
    PB_LIMIT, EPS_LIMIT = portfolio['constants']['up_down_move'] # , DOWN_MOVE , -portfolio['constants']['up_down_move']
    if ((not type(PB_LIMIT) is int) or not (0 <= PB_LIMIT <= 2)) or ((not type(EPS_LIMIT) is int) or not (-10 <= EPS_LIMIT <= 10)): # [0]is pb [1] is eps
        print("Error up/down move constants are not int or pb_limit (up/down[0]) is not within 0-2 inclusive or eps_limit (up/down[1]) is not within -10-10 inclusive")
        return portfolio
    DAYS = portfolio['constants']['days']
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    while stop_day.date() <= end_day.date():
        if not (portfolio['open']['current_date'] >= stop_day).any(): # in case re-run existing portfolio over same days to avoid back running (and conserve time): avoid selling existing tickers incorrectly to TSL (too early) due to tsl_max_price set on future day or selling/buying existing/new tickers incorrectly with algorithm logic # assuming datetime is always in 13:00:00
            if back_testing:
                count += 1
                if add_pauses_to_avoid_unsolved_error['engaged'] and (count % add_pauses_to_avoid_unsolved_error['days'] == 0):
                    print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['days']) + " days on date: " + str(stop_day.date()))
                    time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                # print("update_portfolio_postions_back_testing() running on: " + str(stop_day))
                portfolio = update_portfolio_postions_back_testing(portfolio=portfolio, stop_day=stop_day, end_day=end_day, tickers_with_stock_splits=tickers_with_stock_splits) #
            if portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min']:
                interval_start_date = stop_day - timedelta(days=DAYS)
                while interval_start_date.weekday() > 4 or (interval_start_date.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # only USA holidays for now since only working with tickers listed on USA exchanges # interval_start_date = interval_start_date if (interval_start_date.weekday() < 5) else (interval_start_date - timedelta(days=interval_start_date.weekday()-4)) # to avoid weekends and holidays, always go further back rather than forward (more conservative)
                    interval_start_date = interval_start_date - timedelta(days=1)
                df_tickers_interval_start, df_tickers_interval_stop, df_tickers_last_quality_data = get_saved_tickers_data(date=interval_start_date.strftime('%Y-%m-%d')), get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d')), get_saved_tickers_data(date='2024-01-16')
                if not (df_tickers_interval_start.empty or df_tickers_interval_stop.empty): # df_tickers_interval_stop.empty
                    df_tickers_interval_start, df_tickers_interval_stop = df_tickers_interval_start[df_tickers_interval_start['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False), df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False) # assuming df_tickers_interval_stop aligned with df_tickers_last_quality_data (Market Cap > 0) # maybe refactor and only deal with equities (not ETFs, etc.)
                    tickers_to_buy = [] # Counter()
                    tickers_with_last_price_change = Counter()
                    for ticker in df_tickers_interval_stop.index: # (df_tickers_interval_stop if stop_day.date() < datetime.strptime('2020-05-08', '%Y-%m-%d').date() else df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] >= 2e9]).index: # df_tickers_interval_stop # if want to deal only with Mega, Large, Mid-Cap companies since smaller companies could cause complications with exchange listings etc. (but not on alpaca), S&P 500 tickers from 04/24/2020 until 05/08/2020
                        # if df_tickers_interval_stop.loc[ticker, 'Industry'] == 'Biotechnology': # if add sector(s) constaint(s)
                        try:
                            old_last_price = df_tickers_interval_start.loc[ticker, 'Last']
                            last_price_change = (df_tickers_interval_stop.loc[ticker, 'Last'] - old_last_price) / old_last_price
                        except:
                            last_price_change = 0 # maybe refactor to float("NaN") but for now be consistent with run_portfolio_rr()
                        tickers_with_last_price_change[ticker] = last_price_change
                    for top_interval_loser_ticker, last_price_change in tickers_with_last_price_change.most_common()[-top_interval_losers:]: # maybe refactor (in testing didn't work out as well and more volatile) so top_interval_losers are ordered by most negative first: sorted(tickers_with_last_price_change.items(), key=lambda pair: pair[1], reverse=False)[:top_interval_losers]
                        if stop_day.date() > datetime.strptime('2023_11_30', '%Y_%m_%d').date():
                            df_tickers_last_quality_data = df_tickers_interval_stop
                        if top_interval_loser_ticker not in df_tickers_last_quality_data.index:
                            print("skipping top interveral loser ticker: " + top_interval_loser_ticker + " because ticker not in FMP data on 2024-01-16 (last quality data) or FMP data on: " + str(stop_day) + " if stop_day > 2023-11-30") # maybe refactor and take out, change / add to no industry listed since ticker not a company
                            continue
                        industry = df_tickers_last_quality_data.loc[top_interval_loser_ticker, 'Industry'] # should return None if no value in dataframe row # if ('Industry' in df_tickers_last_quality_data) else None # df_tickers_interval_stop # and (df_tickers_interval_stop.loc[top_interval_loser_ticker, 'Industry']) - not necessary since if ('Industry' in df_tickers_interval_stop) then value is either None or string, repeat logic in next line # check for ('Industry' in df_tickers_interval_stop) since earlier dataframes didn't have 'Industry' column
                        if not industry:
                            print("skipping top interveral loser ticker: " + top_interval_loser_ticker + " because no industry found from Yahoo Finance / Google Finance / FMP on: " + str(stop_day)) # maybe refactor and take out, change / add to no industry listed since ticker not a company
                            continue # Skipping because backtests have shown that companies with no peer companies (on Alpaca) are not good
                        peer_tickers_basic_eps_fy_filtered = [peer_ticker_basic_eps_fy for peer_ticker_basic_eps_fy in df_tickers_last_quality_data[df_tickers_last_quality_data['Industry'] == industry]['Basic EPS (FY)'] if peer_ticker_basic_eps_fy] # df_tickers_interval_stop # maybe refactor and change to unfiltered, assume that if no Basic EPS (TTM) that the coompany is not robust # maybe refactor name to peer_company and peer_companies hard to accomdate logic and grammar, assumed since checking industry that only companies
                        # for ticker in [top_interval_loser_ticker] + list(df_tickers_interval_stop[df_tickers_interval_stop['Industry'] == industry].index): # & (not df_tickers_interval_stop['P/B (FY)'].isnull())
                        pb_ttm = df_tickers_last_quality_data.loc[top_interval_loser_ticker, 'P/B (TTM)'] if df_tickers_last_quality_data.loc[top_interval_loser_ticker, 'P/B (TTM)'] else float("NaN") # ensure that it's a float("NaN") if None value # df_tickers_interval_stop # top_interval_loser_ticker is in df_tickers_interval_stop as per previous for loop (top_interval_loser_ticker in df_tickers_interval_stop.index) and
                        basic_eps = df_tickers_interval_stop.loc[top_interval_loser_ticker, 'Basic EPS (TTM)'] if 'Basic EPS (TTM)' in df_tickers_interval_stop else df_tickers_interval_stop.loc[top_interval_loser_ticker, 'Basic EPS (FY)'] if 'Basic EPS (FY)' in df_tickers_interval_stop else float("NaN")
                        if peer_tickers_basic_eps_fy_filtered and ((len([basic_eps_fy for basic_eps_fy in peer_tickers_basic_eps_fy_filtered if basic_eps_fy >= 0]) / len(peer_tickers_basic_eps_fy_filtered)) >= 0.5) and (pb_ttm <= PB_LIMIT) and (basic_eps >= EPS_LIMIT) and (top_interval_loser_ticker not in portfolio['open'].index): # ticker # [0] # maybe refactor industry considered strong if > 50% of similar companies have eps >= 0 # maybe add UP_MOVE for last_price_change
                            tickers_to_buy.append([top_interval_loser_ticker, last_price_change]) # top_interval_loser_ticker, last_price_change # tickers_to_buy.append([ticker, pb_fy]) # makes sense p/b remains p/b instead of (1-p/b) even though deceiving with rank_rise_d in portfolio dataframe when read portfolio type it's less confusing # p = 10 b = 100 => p/b = 0.1 and 0.9
                    if tickers_to_buy:
                        portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=sorted(tickers_to_buy, key=lambda x: x[1], reverse=False) if custom_order else tickers_to_buy, tickers_to_sell=[], tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=back_testing) # tickers_to_buy
        else:
            print("skipping " +  str(stop_day) + " since portfolio has already run on this date")
        stop_day = stop_day + timedelta(days=1)
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # maybe refactor - stop_day logic not initially set since don't mind scenario where in initial run running portfolio with open positions on a stop_day that is a weekend/holiday # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday()))
            stop_day = stop_day + timedelta(days=1)
    return portfolio

from statistics import mean

def run_portfolio_mmtv(portfolio, start_day=None, end_day=None, mmtv_sell=True, paper_trading=True, back_testing=False, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 240, 'days': 15}, **params): # 04/24/2020 and 04/27/2020 doesn't have proper ranking, before 05/08/2020 only have S&P 500 Rank which is not Market Cap rank # maybe refactor rr_buy/sell to algo_buy/sell, especially if add more algorithms # , rr_buy=True
    print("running run_portfolio_mmtv()")
    # UP_MOVE, DOWN_MOVE = portfolio['constants']['up_down_move'], -portfolio['constants']['up_down_move']
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    while stop_day.date() <= end_day.date():
        if not (portfolio['open']['current_date'] >= stop_day).any(): # in case re-run existing portfolio over same days to avoid back running (and conserve time): avoid selling existing tickers incorrectly to TSL (too early) due to tsl_max_price set on future day or selling/buying existing/new tickers incorrectly with algorithm logic # assuming datetime is always in 13:00:00
            if back_testing:
                count += 1
                if add_pauses_to_avoid_unsolved_error['engaged'] and (count % add_pauses_to_avoid_unsolved_error['days'] == 0):
                    print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['days']) + " days on date: " + str(stop_day.date()))
                    time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                portfolio = update_portfolio_postions_back_testing(portfolio=portfolio, stop_day=stop_day, end_day=end_day, tickers_with_stock_splits=tickers_with_stock_splits)
            if mmtv_sell or (portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min']):
                interval_start_date = stop_day - timedelta(days=DAYS)
                while interval_start_date.weekday() > 4 or (interval_start_date.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # only USA holidays for now since only working with tickers listed on USA exchanges # interval_start_date = interval_start_date if (interval_start_date.weekday() < 5) else (interval_start_date - timedelta(days=interval_start_date.weekday()-4)) # to avoid weekends and holidays, always go further back rather than forward (more conservative)
                    interval_start_date = interval_start_date - timedelta(days=1)
                df_tickers_interval_start, df_tickers_interval_stop = get_saved_tickers_data(date=interval_start_date.strftime('%Y-%m-%d')), get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
                if not (df_tickers_interval_start.empty or df_tickers_interval_stop.empty): # df_tickers_interval_stop.empty
                    df_tickers_interval_start, df_tickers_interval_stop = df_tickers_interval_start[df_tickers_interval_start['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False), df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False) # maybe refactor and only deal with equities (not ETFs, etc.)
                    tickers_to_buy, tickers_to_sell = [], [] # Counter(), Counter()
                    for ticker in df_tickers_interval_stop.index: # (df_tickers_interval_stop if stop_day.date() < datetime.strptime('2020-05-08', '%Y-%m-%d').date() else df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] >= 2e9]).index: # df_tickers_interval_stop # if want to deal only with Mega, Large, Mid-Cap companies since smaller companies could cause complications with exchange listings etc. (but not on alpaca), S&P 500 tickers from 04/24/2020 until 05/08/2020
                        interval_day, trading_volumes_since_interval, trading_volume_stop_day = interval_start_date, [], None
                        while interval_day.date() <= stop_day.date():
                            df_tickers_interval_day = get_saved_tickers_data(date=interval_day.strftime('%Y-%m-%d'))
                            try: # if not df_tickers_interval_day.empty else  None
                                trading_volume_on_interval_day = df_tickers_interval_day.loc[ticker, 'Volume']
                            except:
                                trading_volume_on_interval_day = None # can use isnan() as well but None is easier for filtering below
                            trading_volumes_since_interval.append(trading_volume_on_interval_day)
                            trading_volume_stop_day = trading_volume_on_interval_day if interval_day.date() == stop_day.date() else float("NaN")
                            interval_day = interval_day + timedelta(days=1)
                            while interval_day.weekday() > 4 or (interval_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays):
                                interval_day = interval_day + timedelta(days=1)
                        print(ticker + " has trading volumes " + str(trading_volumes_since_interval) + " from " + str(interval_start_date) + " to " + str(stop_day))
                        trading_volumes_since_interval_filtered = [trading_volume for trading_volume in trading_volumes_since_interval if trading_volume]
                        mean_trading_volume_since_interval = mean(trading_volumes_since_interval_filtered) if trading_volumes_since_interval_filtered else float("NaN")
                        if (ticker not in portfolio['open'].index) and (trading_volume_stop_day > mean_trading_volume_since_interval): # rr_buy and
                            tickers_to_buy.append([ticker, trading_volume_stop_day / mean_trading_volume_since_interval])
                        elif mmtv_sell and (ticker in portfolio['open'].index) and (portfolio['open'].loc[ticker, 'trade_notes'] in ["Filled", "~Filled", None]) and (trading_volume_stop_day <= mean_trading_volume_since_interval):
                            tickers_to_sell.append([ticker, trading_volume_stop_day / mean_trading_volume_since_interval])
                    # Since only S&P 500 tickers from 04/24/2020 until 05/08/2020 and unlikely that a company with >= $2bn market cap would fall out of list of usa tickers not including this check, also if falls out of tradingview usa tickers screener probably means can't sell it on exchange
                    # for ticker in list(set(df_tickers_interval_start.index.values) - set(df_tickers_interval_stop.index.values)):
                    #     tickers_to_sell.append([ticker, df_tickers_interval_start.index.get_loc(df_tickers_interval_start.loc[ticker].name) - (len(df_tickers_interval_start) - DOWN_MOVE)])
                    if (tickers_to_buy or tickers_to_sell):
                        portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=tickers_to_buy, tickers_to_sell=tickers_to_sell, tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=back_testing)
        else:
            print("skipping " +  str(stop_day) + " since portfolio has already run on this date")
        stop_day = stop_day + timedelta(days=1)
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # maybe refactor - stop_day logic not initially set since don't mind scenario where in initial run running portfolio with open positions on a stop_day that is a weekend/holiday # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday()))
            stop_day = stop_day + timedelta(days=1)
    return portfolio

import random

# meant for sell and then buy random weighted positions every 30 days (month) without any SL & TSL etc
def run_portfolio_random_sp500(portfolio, start_day=None, end_day=None, random_sp500_sell=True, paper_trading=True, back_testing=False, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 240, 'days': 15}, **params): # 04/24/2020 and 04/27/2020 doesn't have proper ranking, before 05/08/2020 only have S&P 500 Rank which is not Market Cap rank # maybe refactor rr_buy/sell to algo_buy/sell, especially if add more algorithms # , rr_buy=True
    print("running run_portfolio_random_sp500()")
    # UP_MOVE, DOWN_MOVE = portfolio['constants']['up_down_move'], -portfolio['constants']['up_down_move']
    df_tickers_sp500 = params['df_tickers_sp500'] if 'df_tickers_sp500' in params else _fetch_data(get_sp500_ranked_tickers_by_slickcharts, params={}, error_str=" - No S&P 500 tickers data from Slickcharts on: " + str(datetime.now()), empty_data = pd.DataFrame()) # assuming S&P 500 hasn't changed since start_day
    if df_tickers_sp500.empty: # df_tickers_sp500.empty - precautionary should never be empty # df_tickers_interval_start.empty or df_tickers_interval_stop.empty or  # df_tickers_interval_stop.empty
        print("Error no df_tickers_sp500 cannot perform algorithm")
        return portfolio
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    # refactor repeat below,
    df_tickers_interval_stop = get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
    while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays) or df_tickers_interval_stop.empty: # maybe refactor - stop_day logic not initially set since don't mind scenario where in initial run running portfolio with open positions on a stop_day that is a weekend/holiday # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday()))
        stop_day = stop_day + timedelta(days=1)
        df_tickers_interval_stop = get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
    while stop_day.date() <= end_day.date():
        if not (portfolio['open']['current_date'] >= stop_day).any(): # in case re-run existing portfolio over same days to avoid back running (and conserve time): avoid selling existing tickers incorrectly to TSL (too early) due to tsl_max_price set on future day or selling/buying existing/new tickers incorrectly with algorithm logic # assuming datetime is always in 13:00:00
            if back_testing:
                count += 1
                if add_pauses_to_avoid_unsolved_error['engaged'] and (count % add_pauses_to_avoid_unsolved_error['days'] == 0):
                    print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['days']) + " days on date: " + str(stop_day.date()))
                    time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                portfolio = update_portfolio_postions_back_testing(portfolio=portfolio, stop_day=stop_day, end_day=end_day, tickers_with_stock_splits=tickers_with_stock_splits) #
            if random_sp500_sell or (portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min']):
                interval_start_date = stop_day - timedelta(days=DAYS) # interval_start_date_month, stop_day.month
                df_tickers_interval_start = get_saved_tickers_data(date=interval_start_date.strftime('%Y-%m-%d'))
                while (interval_start_date.weekday() > 4) or (interval_start_date.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays) or df_tickers_interval_start.empty: #  or (interval_start_date.month == interval_start_date_month) # only USA holidays for now since only working with tickers listed on USA exchanges # interval_start_date = interval_start_date if (interval_start_date.weekday() < 5) else (interval_start_date - timedelta(days=interval_start_date.weekday()-4)) # to avoid weekends and holidays, always go further back rather than forward (more conservative)
                    interval_start_date = interval_start_date - timedelta(days=1)
                    df_tickers_interval_start = get_saved_tickers_data(date=interval_start_date.strftime('%Y-%m-%d'))
                df_tickers_interval_start, df_tickers_interval_stop = df_tickers_interval_start[df_tickers_interval_start['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False), df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False) # maybe refactor and only deal with equities (not ETFs, etc.)
                tickers_to_buy, tickers_to_sell = [], [] # Counter(), Counter()
                # weights = [(1/abs(price_change)) if price_change else 0 for price_change in list(df_tickers_sp500['Price Change'])] # abs(price_change) # inverse volatility (1/abs(price_change))
                # normalized_weights = [(float(i)/sum(weights))*100 for i in weights] # *100 since random.choices requires sum to be 100
                # tickers_to_buy = random.choices(list(df_tickers_sp500.index), weights=normalized_weights,k=50)
                # tickers_to_buy = list(set(tickers_to_buy)) # randomize another randomize list, unique values
                tickers_with_last_price_change = {}
                for ticker in df_tickers_sp500.index: # (df_tickers_interval_stop if stop_day.date() < datetime.strptime('2020-05-08', '%Y-%m-%d').date() else df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] >= 2e9]).index: # df_tickers_interval_stop # if want to deal only with Mega, Large, Mid-Cap companies since smaller companies could cause complications with exchange listings etc. (but not on alpaca), S&P 500 tickers from 04/24/2020 until 05/08/2020
                    try:
                        old_last_price = df_tickers_interval_start.loc[ticker, 'Last']
                        last_price_change = (df_tickers_interval_stop.loc[ticker, 'Last'] - old_last_price) / old_last_price
                        tickers_with_last_price_change[ticker] = last_price_change
                    except:
                        continue
                        # last_price_change = 0 # maybe refactor to float("NaN") but for now be consistent with run_portfolio_rr()
                tickers_with_weights = {ticker: ((1/abs(price_change)) if price_change else 0) for ticker, price_change in tickers_with_last_price_change.items()} # abs(price_change) # inverse volatility (1/abs(price_change))
                tickers_with_normalized_weights = {ticker: (float(weight)/sum(tickers_with_weights.values()))*100 for ticker, weight in tickers_with_weights.items()} # *100 since random.choices requires sum to be 100
                tickers_to_buy = random.choices(list(tickers_with_last_price_change.keys()), weights=tickers_with_normalized_weights.values(),k=50)
                tickers_to_buy = [[ticker, tickers_with_normalized_weights[ticker]] for ticker in list(set(tickers_to_buy))] # randomize another randomize list, unique values
                if random_sp500_sell:
                    tickers_to_sell = [[ticker, portfolio['open'].loc[ticker, 'rank_rise_d']] for ticker in list(portfolio['open'][portfolio['open']['trade_notes'].isin(["Filled", "~Filled", None])].index)]
                # Since only S&P 500 tickers from 04/24/2020 until 05/08/2020 and unlikely that a company with >= $2bn market cap would fall out of list of usa tickers not including this check, also if falls out of tradingview usa tickers screener probably means can't sell it on exchange
                # for ticker in list(set(df_tickers_interval_start.index.values) - set(df_tickers_interval_stop.index.values)):
                #     tickers_to_sell.append([ticker, df_tickers_interval_start.index.get_loc(df_tickers_interval_start.loc[ticker].name) - (len(df_tickers_interval_start) - DOWN_MOVE)])
                print("interval start date: " + str(interval_start_date) + ", interval stop: " + str(stop_day))
                if (tickers_to_buy or tickers_to_sell):
                    portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=tickers_to_buy, tickers_to_sell=tickers_to_sell, tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=back_testing)
        else:
            print("skipping " +  str(stop_day) + " since portfolio has already run on this date")
        stop_day = stop_day + timedelta(days=DAYS)
        df_tickers_interval_stop = get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays) or df_tickers_interval_stop.empty: # if any are true it continues until one is false therefore stop_day.date() >= end_day.date() is in while loop
            stop_day = stop_day + timedelta(days=1)
            df_tickers_interval_stop = get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
            if (stop_day.date() >= end_day.date()): #
                break
    return portfolio

# momentum, meant for long-term (3-12 months ~90-~365days)
def run_portfolio_mm(portfolio, start_day=None, end_day=None, paper_trading=True, back_testing=False, top_interval_gainers=100, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 240, 'days': 15}, **params): # not implementing tilupccu_sell since don't want to set DOWN_MOVE as (~0, might buy some very undervalued tickers), could add tilupccu_sell that acts like tsl if pb >= 1
    print("running run_portfolio_mm()")
    # UP_MOVE = portfolio['constants']['up_down_move'] # , DOWN_MOVE , -portfolio['constants']['up_down_move']
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    while stop_day.date() <= end_day.date():
        if not (portfolio['open']['current_date'] >= stop_day).any(): # in case re-run existing portfolio over same days to avoid back running (and conserve time): avoid selling existing tickers incorrectly to TSL (too early) due to tsl_max_price set on future day or selling/buying existing/new tickers incorrectly with algorithm logic # assuming datetime is always in 13:00:00
            if back_testing:
                count += 1
                if add_pauses_to_avoid_unsolved_error['engaged'] and (count % add_pauses_to_avoid_unsolved_error['days'] == 0):
                    print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['days']) + " days on date: " + str(stop_day.date()))
                    time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                portfolio = update_portfolio_postions_back_testing(portfolio=portfolio, stop_day=stop_day, end_day=end_day, tickers_with_stock_splits=tickers_with_stock_splits) #
            if portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min']: # or mm_sell
                interval_start_date = stop_day - timedelta(days=DAYS)
                while interval_start_date.weekday() > 4 or (interval_start_date.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # only USA holidays for now since only working with tickers listed on USA exchanges # interval_start_date = interval_start_date if (interval_start_date.weekday() < 5) else (interval_start_date - timedelta(days=interval_start_date.weekday()-4)) # to avoid weekends and holidays, always go further back rather than forward (more conservative)
                    interval_start_date = interval_start_date - timedelta(days=1)
                df_tickers_interval_start, df_tickers_interval_stop = get_saved_tickers_data(date=interval_start_date.strftime('%Y-%m-%d')), get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
                if not (df_tickers_interval_start.empty or df_tickers_interval_stop.empty): # df_tickers_interval_stop.empty
                    df_tickers_interval_start, df_tickers_interval_stop = df_tickers_interval_start[df_tickers_interval_start['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False), df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False) # maybe refactor and only deal with equities (not ETFs, etc.)
                    tickers_to_buy = [] # Counter()
                    tickers_with_last_price_change = Counter()
                    for ticker in df_tickers_interval_stop.index: # (df_tickers_interval_stop if stop_day.date() < datetime.strptime('2020-05-08', '%Y-%m-%d').date() else df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] >= 2e9]).index: # df_tickers_interval_stop # if want to deal only with Mega, Large, Mid-Cap companies since smaller companies could cause complications with exchange listings etc. (but not on alpaca), S&P 500 tickers from 04/24/2020 until 05/08/2020
                        # if df_tickers_interval_stop.loc[ticker, 'Industry'] == 'Biotechnology': # if add sector(s) constaint(s)
                        try:
                            old_last_price = df_tickers_interval_start.loc[ticker, 'Last']
                            last_price_change = (df_tickers_interval_stop.loc[ticker, 'Last'] - old_last_price) / old_last_price
                        except:
                            last_price_change = 0 # maybe refactor to float("NaN") but for now be consistent with run_portfolio_rr()
                        tickers_with_last_price_change[ticker] = last_price_change
                    for top_interval_gainer_ticker, last_price_change in tickers_with_last_price_change.most_common()[:top_interval_gainers]: # top_interval_loser_tickers = [ticker_tuple[0] for ticker_tuple in tickers_with_last_price_change.most_common()[-10:]] # maybe refactor (in testing didn't work out as well and more volatile) so top_interval_losers are ordered by most negative first: sorted(tickers_with_last_price_change.items(), key=lambda pair: pair[1], reverse=False)[:top_interval_losers]
                        tickers_to_buy.append([top_interval_gainer_ticker, last_price_change]) # top_interval_loser_ticker, last_price_change # tickers_to_buy.append([ticker, pb_fy]) # makes sense p/b remains p/b instead of (1-p/b) even though deceiving with rank_rise_d in portfolio dataframe when read portfolio type it's less confusing # p = 10 b = 100 => p/b = 0.1 and 0.9
                    if tickers_to_buy:
                        portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=tickers_to_buy, tickers_to_sell=[], tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=back_testing) # tickers_to_buy # sorted(tickers_to_buy, key=lambda x: x[1], reverse=False) if custom_order else tickers_to_buy
        else:
            print("skipping " +  str(stop_day) + " since portfolio has already run on this date")
        stop_day = stop_day + timedelta(days=1)
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # maybe refactor - stop_day logic not initially set since don't mind scenario where in initial run running portfolio with open positions on a stop_day that is a weekend/holiday # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday()))
            stop_day = stop_day + timedelta(days=1)
    return portfolio

def run_portfolio_ai_recommendations_in_sector(portfolio, start_day=None, end_day=None, airs_sell=True, paper_trading=True, back_testing=False, limit_companies=33, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 180, 'tickers': 50, 'days': 1000}, **params): # keep **params here and in run_portfolio_rr() so can pass variables for backtesting cases in which the yahoo finance service is down but the data for start_day and end_day is already loaded
    print("running run_portfolio_ai_recommendations_in_sector()")
    if (not type(portfolio['constants']['up_down_move']) is list) or len(portfolio['constants']['up_down_move']) != 3:
        print("Error up/down move constant is not a list or a list with length 3")
        return portfolio
    UP_MOVE, DOWN_MOVE, SECTOR = portfolio['constants']['up_down_move'] # maybe refactor and add similar to up_down_move with difference between start day's zacks rank and stop day's zacks rank,
    if ((not type(UP_MOVE) is int) or not (1 <= UP_MOVE <= 9)) or ((not type(DOWN_MOVE) is int) or not (1 <= DOWN_MOVE <= 9)) or (not type(SECTOR) is str): # [0]is higher rank threshold [1] is lower rank threshold [2] is sector can add check for sectors = list(df_tickers_interval_stop.Sector.unique()) but there is '' and None sectors so not checking
        print("Error up/down move constants[0,1] are not int or up/down[0,1] are not within 1-9 inclusive or up/down[2] is not a string")
        return portfolio
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    ticker_count = 0
    while stop_day.date() <= end_day.date():
        if not (portfolio['open']['current_date'] >= stop_day).any(): # in case re-run existing portfolio over same days to avoid back running (and conserve time): avoid selling existing tickers incorrectly to TSL (too early) due to tsl_max_price set on future day or selling/buying existing/new tickers incorrectly with algorithm logic # assuming datetime is always in 13:00:00
            if back_testing:
                count += 1
                if add_pauses_to_avoid_unsolved_error['engaged'] and (count % add_pauses_to_avoid_unsolved_error['days'] == 0):
                    print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['days']) + " days on date: " + str(stop_day.date()))
                    time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                portfolio = update_portfolio_postions_back_testing(portfolio=portfolio, stop_day=stop_day, end_day=end_day, tickers_with_stock_splits=tickers_with_stock_splits) # maybe refactor throughout and make it function(param1, param2, ...) rather than function(param1=param1, param2=param2, ...)
            if airs_sell or (portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min']):
                df_tickers_interval_stop = get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
                df_tickers_interval_stop = df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False)
                if not df_tickers_interval_stop.empty:
                    # refactor and add logic for dealing with if zacks rank is in  df_tickers_interval_start/stop
                    tickers_to_buy, tickers_to_sell = [], [] # Counter(), Counter()
                    # sector = 'Financial Services'
                    for ticker in df_tickers_interval_stop[df_tickers_interval_stop['Sector'] == SECTOR][:limit_companies].index: # My OpenAI plan has a quota ~484 hits / day
                        ticker_count += 1
                        if add_pauses_to_avoid_unsolved_error['engaged'] and (ticker_count % add_pauses_to_avoid_unsolved_error['tickers'] == 0):
                            print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['tickers']) + " tickers on date: " + str(stop_day.date()))
                            time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                        company_name, location = df_tickers_interval_stop.loc[ticker, ['Name (Alpaca)', 'Location']]
                        try:
                            # maybe refactor inside of a try statement no need for _fetch_data()
                            buy_or_not_analysis = should_I_buy_the_stock_google_gemini_pro(ticker, company_name, location) # f"Is it a good time to buy {company_name}?"
                            rating = extract_investment_recommendation(buy_or_not_analysis, ticker) # , tokens_used # rating = float(re.findall(r"[0-9]{1,2}" + "S[out of 10|on a scale of 1-10]", buy_or_not_analysis.content)[0].split()[0]) if re.findall(r"[0-9]{1,2}" + " out of 10", buy_or_not_analysis.content) else float("NaN")
                            rating = rating if rating else extract_investment_recommendation_2(buy_or_not_analysis, ticker)
                            print(ticker + ": " + str(rating))
                            if (ticker not in portfolio['open'].index) and (rating >= UP_MOVE): # care if ticker has just turned to buy # convenient since if 'Zacks Rank' is None conditional expression returns False instead of returning an error and continues, much faster
                                print(ticker + ": " + " buying")
                                tickers_to_buy.append([ticker, rating]) # tickers_to_buy[ticker] = df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] - df_tickers_interval_start.loc[ticker, 'Zacks Rank']
                            elif airs_sell and (ticker in portfolio['open'].index) and (portfolio['open'].loc[ticker, 'trade_notes'] in ["Filled", "~Filled", None]) and (rating <= DOWN_MOVE): # don't care if ticker has just turned to sell or has been sell for a while: if (df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] > 3) and (df_tickers_interval_start.loc[ticker, 'Zacks Rank'] <= 3):
                                print(ticker + ": " + " selling")
                                tickers_to_sell.append([ticker, rating]) # tickers_to_sell[ticker] = df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] - df_tickers_interval_start.loc[ticker, 'Zacks Rank']
                        except Exception as e:
                            print(str(e) + " - Unable to execute, " + ticker + " issues with buy or not analysis content or investment recommendation on company name: " + company_name + " on: " + stop_day.strftime('%Y-%m-%d'))
                    if (tickers_to_buy or tickers_to_sell):
                        portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=tickers_to_buy, tickers_to_sell=tickers_to_sell, tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=back_testing)
        else:
            print("skipping " +  str(stop_day) + " since portfolio has already run on this date")
        stop_day = stop_day + timedelta(days=1)
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # interval_start_date/stop_day in usa_holidays # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday())) # to avoid weekends, refactor to avoid holidays (2020-05-25)
            stop_day = stop_day + timedelta(days=1)
    return portfolio

def run_portfolio_top_n_gainers_ai_analysis(portfolio, start_day=None, end_day=None, tngaia_sell=True, paper_trading=True, back_testing=False, back_running_allowance=11, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 180, 'tickers': 50, 'days': 1000}, **params): # keep **params here and in run_portfolio_rr() so can pass variables for backtesting cases in which the yahoo finance service is down but the data for start_day and end_day is already loaded
    print("running run_portfolio_top_n_gainers_ai_analysis()")
    if (not type(portfolio['constants']['up_down_move']) is list) or len(portfolio['constants']['up_down_move']) != 2:
        print("Error up/down move constant is not a list or a list with length 2")
        return portfolio
    UP_MOVE, DOWN_MOVE = portfolio['constants']['up_down_move'] # maybe refactor and add similar to up_down_move with difference between start day's zacks rank and stop day's zacks rank,
    if ((not type(UP_MOVE) is int) or not (1 <= UP_MOVE <= 9)) or ((not type(DOWN_MOVE) is int) or not (1 <= DOWN_MOVE <= 9)): # [0]is higher rank threshold [1] is lower rank threshold
        print("Error up/down move constants[0,1] are not an int or up/down[0,1] are not within 1-9 inclusive")
        return portfolio
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    while stop_day.date() <= end_day.date():
        if not (portfolio['open']['current_date'] >= stop_day).any(): # in case re-run existing portfolio over same days to avoid back running (and conserve time): avoid selling existing tickers incorrectly to TSL (too early) due to tsl_max_price set on future day or selling/buying existing/new tickers incorrectly with algorithm logic # assuming datetime is always in 13:00:00
            if back_testing:
                count += 1
                if add_pauses_to_avoid_unsolved_error['engaged'] and (count % add_pauses_to_avoid_unsolved_error['days'] == 0):
                    print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['days']) + " days on date: " + str(stop_day.date()))
                    time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                portfolio = update_portfolio_postions_back_testing(portfolio=portfolio, stop_day=stop_day, end_day=end_day, tickers_with_stock_splits=tickers_with_stock_splits) # maybe refactor throughout and make it function(param1, param2, ...) rather than function(param1=param1, param2=param2, ...)
            if tngaia_sell or (portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min']):
                df_tickers_interval_stop = get_saved_tickers_data(date=stop_day.strftime('%Y-%m-%d'))
                df_tickers_interval_stop = df_tickers_interval_stop[df_tickers_interval_stop['Market Cap'] > 0].sort_values('Market Cap', ascending=False, inplace=False)
                df_tickers_daily_gainers = _fetch_data(get_daily_stock_gainers_fmp, params={}, error_str=" - Issues with stock gainers from FMP on: " + str(datetime.now()), empty_data = pd.DataFrame())
                if not back_testing:
                    save_tickers_daily_gainers_fmp(df_tickers_daily_gainers, stop_day.strftime('%Y-%m-%d'))
                if not (df_tickers_interval_stop.empty or df_tickers_daily_gainers.empty):
                    # refactor and add logic for dealing with if zacks rank is in  df_tickers_interval_start/stop
                    tickers_to_buy, tickers_to_sell = [], [] # Counter(), Counter()
                    for idx in df_tickers_daily_gainers.index: # My OpenAI plan has a quota ~484 hits / day
                        ticker = df_tickers_daily_gainers.loc[idx, 'symbol']
                        try:
                            company_name, location = df_tickers_interval_stop.loc[ticker, ['Name (Alpaca)', 'Location']]
                            # maybe refactor inside of a try statement no need for _fetch_data()
                            buy_or_not_analysis = should_I_buy_the_stock_google_gemini_pro(ticker, company_name, location, add_technical=True) # f"Is it a good time to buy {company_name}?"
                            rating = extract_investment_recommendation(buy_or_not_analysis, ticker) # , tokens_used # rating = float(re.findall(r"[0-9]{1,2}" + "S[out of 10|on a scale of 1-10]", buy_or_not_analysis.content)[0].split()[0]) if re.findall(r"[0-9]{1,2}" + " out of 10", buy_or_not_analysis.content) else float("NaN")
                            rating = rating if rating else extract_investment_recommendation_2(buy_or_not_analysis, ticker)
                            print(ticker + ": " + str(rating))
                            if (ticker not in portfolio['open'].index) and (rating >= UP_MOVE): # care if ticker has just turned to buy # convenient since if 'Zacks Rank' is None conditional expression returns False instead of returning an error and continues, much faster
                                print(ticker + ": " + " buying")
                                tickers_to_buy.append([ticker, rating]) # tickers_to_buy[ticker] = df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] - df_tickers_interval_start.loc[ticker, 'Zacks Rank']
                            elif tngaia_sell and (ticker in portfolio['open'].index) and (portfolio['open'].loc[ticker, 'trade_notes'] in ["Filled", "~Filled", None]) and (rating <= DOWN_MOVE): # don't care if ticker has just turned to sell or has been sell for a while: if (df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] > 3) and (df_tickers_interval_start.loc[ticker, 'Zacks Rank'] <= 3):
                                print(ticker + ": " + " selling")
                                tickers_to_sell.append([ticker, rating]) # tickers_to_sell[ticker] = df_tickers_interval_stop.loc[ticker, 'Zacks Rank'] - df_tickers_interval_start.loc[ticker, 'Zacks Rank']
                        except Exception as e:
                            print(str(e) + " - Unable to execute, " + ticker + " issues with ticker in df_tickers_interval_stop or buy or not analysis content or investment recommendation on: " + stop_day.strftime('%Y-%m-%d'))
                    if (tickers_to_buy or tickers_to_sell):
                        portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=tickers_to_buy, tickers_to_sell=tickers_to_sell, tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=back_testing)
        else:
            print("skipping " +  str(stop_day) + " since portfolio has already run on this date")
        stop_day = stop_day + timedelta(days=1)
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # interval_start_date/stop_day in usa_holidays # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday())) # to avoid weekends, refactor to avoid holidays (2020-05-25)
            stop_day = stop_day + timedelta(days=1)
    return portfolio

# FMP  going back to 2014
def senate_timestamps_and_tickers_inflows_and_outflows_by_month_for_stocks(stocks_list):
    df = pd.DataFrame() # _averaged_summed_and_grouped
    amounts_to_map = {'$15,001 - $50,000':33000, '$1,001 - $15,000':7500, '$50,001 - $100,000':75000, '$100,001 - $250,000':175000, '$1,000,001 - $5,000,000':2500000, '$500,001 - $1,000,000':750000, '$250,001 - $500,000':375000, '$5,000,001 - $25,000,000':15000000}
    for ticker in stocks_list:
        try:
            senate_df = get_senate_trading_symbol_fmp(ticker=ticker) # senate_df[['transactionDate', 'office', 'assetDescription', 'assetType', 'amount', 'comment', 'full_name']]
            senate_df['amount_fixed'] = senate_df['amount'].map(amounts_to_map)
            senate_df['direction'] = senate_df['type'].apply(lambda x: 1 if x=='Purchase' else -1)
            senate_df['amount_fixed'] = senate_df['amount_fixed']*senate_df['direction']
            temp_df = senate_df.groupby(pd.Grouper(freq='D'))[['amount_fixed']].sum().pipe(lambda x: x.assign(symbol=ticker))
            df = pd.concat([df, temp_df], axis=0)
        except:
            print(f'No Data for {ticker}')
    df = df.groupby([pd.Grouper(freq='M'),'symbol'])[['amount_fixed']].sum()
    df['rank'] = df.groupby(level=0)['amount_fixed'].transform(lambda x: x.rank(ascending=False))
    return df

def run_portfolio_senate_trading(portfolio, start_day=None, end_day=None, senate_trading_sell=True, paper_trading=True, back_testing=False, add_pauses_to_avoid_unsolved_error={'engaged': False, 'time': 240, 'days': 15}, **params): # maybe refactor and add sp500 and month to name
    print("running run_portfolio_senate_trading()")
    if (not type(portfolio['constants']['up_down_move']) is int) or not (1 <= portfolio['constants']['up_down_move'] <= 5): # [0]is higher rank threshold [1] is lower rank threshold
        print("Error up/down move constant is not an int or not within 1-5 inclusive")
        return portfolio
    RANK_LIMIT = portfolio['constants']['up_down_move']
    if 'senate_timestamps_and_tickers_inflows_and_outflows' in params:
        senate_timestamps_and_tickers_inflows_and_outflows = params['senate_timestamps_and_tickers_inflows_and_outflows']
    else:
        df_tickers_sp500 = params['df_tickers_sp500'] if 'df_tickers_sp500' in params else _fetch_data(get_sp500_ranked_tickers_by_slickcharts, params={}, error_str=" - No S&P 500 tickers data from Slickcharts on: " + str(datetime.now()), empty_data = pd.DataFrame()) # assuming S&P 500 hasn't changed since start_day
        senate_timestamps_and_tickers_inflows_and_outflows = _fetch_data(senate_timestamps_and_tickers_inflows_and_outflows_by_month_for_stocks, params={'stocks_list': list(df_tickers_sp500.index)}, error_str=" - Issues with senate timestamps and tickers inflows and outflows by month data from FMP on: " + str(datetime.now()), empty_data = pd.DataFrame())
        if df_tickers_sp500.empty or senate_timestamps_and_tickers_inflows_and_outflows.empty: # df_tickers_sp500.empty - precautionary should never be empty # df_tickers_interval_start.empty or df_tickers_interval_stop.empty or  # df_tickers_interval_stop.empty
            print("Error no df_tickers_sp500 or senate_timestamps_and_tickers_inflows_and_outflows cannot perform algorithm")
            return portfolio
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    tickers_to_buy_or_sell_every_month = {}
    for timestamp_and_ticker in senate_timestamps_and_tickers_inflows_and_outflows[senate_timestamps_and_tickers_inflows_and_outflows['rank'] < RANK_LIMIT].index:
        amount_fixed = senate_timestamps_and_tickers_inflows_and_outflows.loc[timestamp_and_ticker, 'amount_fixed']
        timestamp, ticker = timestamp_and_ticker
        timestamp = timestamp + timedelta(days=1) # beginning of month
        if timestamp.strftime('%Y-%m-%d') in tickers_to_buy_or_sell_every_month:
            tickers_to_buy_or_sell_every_month[timestamp.strftime('%Y-%m-%d')].append([ticker, amount_fixed])
        else:
            tickers_to_buy_or_sell_every_month[timestamp.strftime('%Y-%m-%d')] = [[ticker, amount_fixed]]
    while stop_day.date() <= end_day.date():
        if not (portfolio['open']['current_date'] >= stop_day).any(): # in case re-run existing portfolio over same days to avoid back running (and conserve time): avoid selling existing tickers incorrectly to TSL (too early) due to tsl_max_price set on future day or selling/buying existing/new tickers incorrectly with algorithm logic # assuming datetime is always in 13:00:00
            if back_testing:
                count += 1
                if add_pauses_to_avoid_unsolved_error['engaged'] and (count % add_pauses_to_avoid_unsolved_error['days'] == 0):
                    print("Sleeping " + str(add_pauses_to_avoid_unsolved_error['time']/60) + "min every " + str(add_pauses_to_avoid_unsolved_error['days']) + " days on date: " + str(stop_day.date()))
                    time.sleep(add_pauses_to_avoid_unsolved_error['time'])
                portfolio = update_portfolio_postions_back_testing(portfolio=portfolio, stop_day=stop_day, end_day=end_day, tickers_with_stock_splits=tickers_with_stock_splits) #
            stop_day_buy_date = stop_day.replace(day=1).strftime('%Y-%m-%d')
            if (stop_day_buy_date in tickers_to_buy_or_sell_every_month) and (senate_trading_sell or (portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min'])):
                print("stop date: " + str(stop_day) + ", interval stop buy date date: " + str(stop_day_buy_date))
                tickers_to_buy, tickers_to_sell = [], [] # Counter(), Counter()
                for ticker, amount_fixed in tickers_to_buy_or_sell_every_month[stop_day_buy_date]:
                    if amount_fixed > 0:
                        tickers_to_buy.append([ticker, amount_fixed])
                    elif senate_trading_sell and (ticker in portfolio['open'].index) and (portfolio['open'].loc[ticker, 'trade_notes'] in ["Filled", "~Filled", None]) and (amount_fixed < 0):
                        tickers_to_sell.append([ticker, amount_fixed])
                if (tickers_to_buy or tickers_to_sell):
                    portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=tickers_to_buy, tickers_to_sell=tickers_to_sell, tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=back_testing)
        else:
            print("skipping " +  str(stop_day) + " since portfolio has already run on this date")
        stop_day = stop_day + timedelta(days=DAYS)
        while stop_day.weekday() > 4 or (stop_day.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays): # interval_start_date/stop_day in usa_holidays # stop_day = (stop_day + timedelta(days=1)) if (stop_day.weekday() < 4) else (stop_day + timedelta(days=7-stop_day.weekday())) # to avoid weekends, refactor to avoid holidays (2020-05-25)
            stop_day = stop_day + timedelta(days=1)
        if (stop_day.date() >= end_day.date()): #
            break
    return portfolio

def run_portfolio_sma_mm(portfolio, start_day=None, end_day=None, sma_mm_sell=True, paper_trading=True, limit_companies=1000, **params): # run during market hours
    print("running run_portfolio_sma_mm()")
    # no need for, always trading: sma_mm_sell or (portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min'])
    UP_DOWN_MOVE = portfolio['constants']['up_down_move'] # refactor and add UP_MOVE, DOWN_MOVE = portfolio['constants']['up_down_move'] in terms of 20D, 50D, 200D ie 200 or [50,200] if multiple
    if UP_DOWN_MOVE not in ["price-200D", "price-200D-sp500", "5D-8D-13D"]:
        print("Error up/down move constant is not in list of allowed algorithms: " + "price-200D, price-200D-sp500, 5D-8D-13D")
        return portfolio
    success_or_error, portfolio, DAYS, end_day, start_day, stop_day, tickers_to_avoid, tickers_with_stock_splits, count, usa_holidays = check_for_basic_errors_and_set_general_params_for_run_portfolio(portfolio, start_day, end_day, paper_trading, back_testing, **params)
    if success_or_error == "Error":
        print("Error in check_for_basic_errors_and_set_general_params_for_run_portfolio, returning")
        return portfolio
    if stop_day.hour > 18: # assuming only called / running on market days / weekdays
        tickers_to_sell = []
        for ticker in portfolio['open'].index:
            if UP_DOWN_MOVE in ["price-200D", "price-200D-sp500"]:
                ticker_data_quote = _fetch_data(get_ticker_data_quote_fmp, params={'ticker': ticker}, error_str=" - No ticker data quote FMP for ticker: " + ticker + " on: " + str(datetime.now()), empty_data=pd.DataFrame())
                price, price_avg_200 = ticker_data_quote.loc[ticker, ['price', 'priceAvg200']] # price_avg_50
                if sma_mm_sell and (price < price_avg_200):
                    tickers_to_sell.append([ticker, (price - price_avg_200) / price_avg_200])
                    print(ticker + ": to sell, price: " + str(price) + ", 200D avg price: " + str(price_avg_200))
            elif UP_DOWN_MOVE == "5D-8D-13D":
                ticker_data_granular = _fetch_data(get_ticker_data_granular_fmp, params={'ticker': ticker, 'start_datetime': datetime.now()-timedelta(days=30), 'end_datetime': datetime.now(), 'interval': '1day'}, error_str=" - No " + "1day" + " ticker data for: " + ticker + " from datetime: " + str(datetime.now()-timedelta(days=30)) + " to datetime: " + str(datetime.now()), empty_data=pd.DataFrame()) #
                if ticker_data_granular.empty:
                    continue
                ticker_data_granular['SMA-5day'], ticker_data_granular['SMA-8day'], ticker_data_granular['SMA-13day'] = ticker_data_granular['close'].rolling(window=5).mean(), ticker_data_granular['close'].rolling(window=8).mean(), ticker_data_granular['close'].rolling(window=13).mean()
                ticker_data_granular.index=[str(x).split()[0] for x in list(ticker_data_granular.index)]
                price, price_avg_5, price_avg_8, price_avg_13 = ticker_data_granular.loc[datetime.now().strftime('%Y-%m-%d'), ['close', 'SMA-5day', 'SMA-8day', 'SMA-13day']] if datetime.now().strftime('%Y-%m-%d') in ticker_data_granular.index else [float("NaN"), float("NaN"), float("NaN"), float("NaN")] #
                price_differential = (price_avg_5 - price_avg_8) / price_avg_8 # (price_avg_8 - price_avg_13) / price_avg_13,
                if sma_mm_sell and (price_avg_8 < price_avg_13) and (price_avg_5 < price_avg_8):
                    tickers_to_sell.append([ticker, price_differential])
                    print(ticker + ": to sell, price_avg_5: " + str(price_avg_5) + ", price_avg_8: " + str(price_avg_8) + ", price_avg_13: " + str(price_avg_13))
        if tickers_to_sell:
            portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=[], tickers_to_sell=tickers_to_sell, tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=False)
        return portfolio
    # add logic for UP_MOVE, DOWN_MOVE = portfolio['constants']['up_down_move']
    # if sma_mm_sell or (portfolio['balance']['usd'] >= portfolio['constants']['usd_invest_min']):
    interval_stop_date = stop_day - timedelta(days=DAYS)
    while interval_stop_date.weekday() > 4 or (interval_stop_date.replace(hour=0, minute=0, second=0, microsecond=0) in usa_holidays):
        interval_stop_date = interval_stop_date - timedelta(days=1)
    df_tickers_interval_stop, df_tickers_sp500 = get_saved_tickers_data(date=interval_stop_date.strftime('%Y-%m-%d')), pd.DataFrame()
    if UP_DOWN_MOVE == "price-200D-sp500":
        df_tickers_sp500 = params['df_tickers_sp500'] if 'df_tickers_sp500' in params else _fetch_data(get_sp500_ranked_tickers_by_slickcharts, params={}, error_str=" - No S&P 500 tickers data from Slickcharts on: " + str(datetime.now()), empty_data = pd.DataFrame()) # assuming S&P 500 hasn't changed since start_day
        if df_tickers_sp500.empty: # df_tickers_sp500.empty - precautionary should never be empty # df_tickers_interval_start.empty or df_tickers_interval_stop.empty or  # df_tickers_interval_stop.empty
            print("Error no df_tickers_sp500 cannot perform algorithm")
            return portfolio
    # sectors = list(df_tickers_interval_stop.Sector.unique())
    tickers_to_buy, tickers_to_sell = [], []
    sectors = list(df_tickers_interval_stop.Sector.unique())
    sector = sectors[randint(0,len(sectors)-1)]
    print("Interval stop day: " + str(interval_stop_date) + ", Sector: " + str(sector))
    start_time, count, count_div, tickers_to_convert = time.time(), 0, 10 if UP_DOWN_MOVE != "price-200D-sp500" else 3, {'BRK.B': 'BRK-B', 'BRK.A': 'BRK-A'} # possibly refactor and add logic for tickers_to_convert (issue cause trade with Alpaca but get data with FMP)
    df_tickers_to_iterate = df_tickers_interval_stop[df_tickers_interval_stop['Sector'] == sector][:limit_companies] if UP_DOWN_MOVE != "price-200D-sp500" else df_tickers_interval_stop[(df_tickers_interval_stop['Sector'] == sector) & (df_tickers_interval_stop.index.isin(df_tickers_sp500.index))][:limit_companies]
    for ticker in df_tickers_to_iterate.index:
        count += 1
        if count % count_div == 0:
            ticker_for_fmp = tickers_to_convert[ticker] if ticker in tickers_to_convert else ticker
            if UP_DOWN_MOVE in ["price-200D", "price-200D-sp500"]:
                ticker_data_quote = _fetch_data(get_ticker_data_quote_fmp, params={'ticker': ticker_for_fmp}, error_str=" - No ticker data quote FMP for ticker: " + ticker + " converted to: " + ticker_for_fmp + " on: " + str(datetime.now()), empty_data=pd.DataFrame())
                price, price_avg_200 = ticker_data_quote.loc[ticker_for_fmp, ['price', 'priceAvg200']] if ticker_for_fmp in ticker_data_quote.index else [float("NaN"), float("NaN")] # if ticker in ticker_data_quote.index else [float("NaN"), float("NaN")] # price_avg_50
                price_differential = (price - price_avg_200) / price_avg_200 if price_avg_200 != 0 else (price - 0) / 1
                if price > price_avg_200:
                    # add logic for adding 20% buys/sells for 50D above/below
                    tickers_to_buy.append([ticker, price_differential])
                    print(ticker + ", " + str(df_tickers_interval_stop.loc[ticker, 'Name (Alpaca)']) + ": to buy, price: " + str(price) + ", 200D avg price: " + str(price_avg_200) + ", count: " + str(count))
                elif sma_mm_sell and (price < price_avg_200) and (ticker in portfolio['open']):
                    tickers_to_sell.append([ticker, price_differential])
                    print(ticker + ", " + str(df_tickers_interval_stop.loc[ticker, 'Name (Alpaca)']) + ": to sell, price: " + str(price) + ", 200D avg price: " + str(price_avg_200) + ", count: " + str(count))
            elif UP_DOWN_MOVE == "5D-8D-13D":
                ticker_data_granular = _fetch_data(get_ticker_data_granular_fmp, params={'ticker': ticker, 'start_datetime': datetime.now()-timedelta(days=30), 'end_datetime': datetime.now(), 'interval': '1day'}, error_str=" - No " + "1day" + " ticker data for: " + ticker + " from datetime: " + str(datetime.now()-timedelta(days=30)) + " to datetime: " + str(datetime.now()), empty_data=pd.DataFrame()) #
                if ticker_data_granular.empty:
                    continue
                ticker_data_granular['SMA-5day'], ticker_data_granular['SMA-8day'], ticker_data_granular['SMA-13day'] = ticker_data_granular['close'].rolling(window=5).mean(), ticker_data_granular['close'].rolling(window=8).mean(), ticker_data_granular['close'].rolling(window=13).mean()
                ticker_data_granular.index=[str(x).split()[0] for x in list(ticker_data_granular.index)]
                price, price_avg_5, price_avg_8, price_avg_13 = ticker_data_granular.loc[datetime.now().strftime('%Y-%m-%d'), ['close', 'SMA-5day', 'SMA-8day', 'SMA-13day']] if datetime.now().strftime('%Y-%m-%d') in ticker_data_granular.index else [float("NaN"), float("NaN"), float("NaN"), float("NaN")] #
                price_differential = (price_avg_5 - price_avg_8) / price_avg_8 # (price_avg_8 - price_avg_13) / price_avg_13,
                if (price_avg_8 > price_avg_13) and (price_avg_5 > price_avg_8):
                    # add logic for adding 20% buys/sells for 50D above/below
                    tickers_to_buy.append([ticker, price_differential])
                    print(ticker + ", " + str(df_tickers_interval_stop.loc[ticker, 'Name (Alpaca)']) + ": to buy, price_avg_5: " + str(price_avg_5) + ", price_avg_8: " + str(price_avg_8) + ", price_avg_13: " + str(price_avg_13) + ", count: " + str(count))
                elif sma_mm_sell and (ticker in portfolio['open']) and (price_avg_8 < price_avg_13) and (price_avg_5 < price_avg_8):
                    tickers_to_sell.append([ticker, price_differential])
                    print(ticker + ", " + str(df_tickers_interval_stop.loc[ticker, 'Name (Alpaca)']) + ": to sell, price_avg_5: " + str(price_avg_5) + ", price_avg_8: " + str(price_avg_8) + ", price_avg_13: " + str(price_avg_13) + ", count: " + str(count))
    print("Execution time: " + str(time.time() - start_time))
    if (tickers_to_buy or tickers_to_sell):
        portfolio = update_portfolio_buy_and_sell_tickers(portfolio=portfolio, tickers_to_buy=tickers_to_buy, tickers_to_sell=tickers_to_sell, tickers_to_avoid=tickers_to_avoid, stop_day=stop_day, paper_trading=paper_trading, back_testing=False)
    return portfolio

# function required for markets with high traffic volume / trading on multiple exchanges, refactor (so that buy positions of closed orders is included) or refactor frequency of calls if implement higher frequency trading (expect buying and selling within 1 hour)
def portfolio_align_prices_with_alpaca(portfolio, open_positions=True, sold_positions=False): # no need to add: , avoid_paper_positions=False since if ticker shows up in positions or closed_orders they are real trades and thereby implicitly avoiding paper trades # not changing portfolio['balance']['usd'] since change is very small and
    if open_positions:
        positions = _fetch_data(alpaca_api.list_positions, params={}, error_str=" - Alpaca positions error on: " + str(datetime.now()), empty_data=[]) # show nested multi-leg orders # limit=100,
        for position in positions: # and not (avoid_paper_positions and (portfolio['open'].loc[ticker, 'position'] == 'long-p'))
            ticker, buy_price_actual = position.symbol, float(position.avg_entry_price)
            df_matching_open_positions = portfolio['open'][(portfolio['open'].index == ticker) & (portfolio['open']['trade_notes'].isin(["Filled", "~Filled"])) & (portfolio['open']['buy_price'] != buy_price_actual)] # not checking for 'position' == 'long' since if ticker in portfolio then the position must be 'long' (since is listed on alpaca as a position) and is unique in portfolio['open'] # including "~Filled" since in all cases (haven't found a case contrary) "~Filled" == "Filled"
            if not df_matching_open_positions.empty: # maybe refactor here and below and add precautionary check - shouldn't have to check len() == 1 since symbol, like ticker (index) should be unique in portfolio['open']
                buy_price, balance = portfolio['open'].loc[ticker, ['buy_price', 'balance']]
                portfolio['balance']['usd'] = portfolio['balance']['usd'] - (buy_price_actual - buy_price)*balance # usually correction is a mattter of dollars but putting here and below in function to be consistent with other functions (anytime there is a position buy/sell/rebuy/resell/price correction) update portfolio['balance']['usd'], portfolio_align_buying_power_with_alpaca() always called before this method # actual: 11/9 bought: 10 balance: 50 -> 50,-50
                portfolio['open'].loc[ticker, 'buy_price'] = buy_price_actual # maybe refactor - not changing current_roi since not necessary and don't want to have accidental (shouldn't happen but possible if I implement something new without thinking of this issue) sell trigger before start of next day
    if sold_positions:
        closed_orders = _fetch_data(alpaca_api.list_orders, params={'status': 'closed', 'limit': 150, 'nested': True}, error_str=" - Alpaca closed orders error on: " + str(datetime.now()), empty_data=[])
        for closed_order in closed_orders:
            if (closed_order.status == 'filled') and (closed_order.side == 'sell'):
                ticker, order_time, quantity = closed_order.symbol, datetime.fromtimestamp(datetime.timestamp(closed_order.created_at)), float(closed_order.qty) # here and below can also use closed_order.submitted_at (which is about a hundreth of a second before closed_order.created_at), better to use created_at I think since closer to input date in portfolio (datetime is recorded after order submitted) and higher up in Alpaca Order() object, and also maybe possible if submitted and not created, and need Alpaca Order() created # assuming that an order that is partially/not filled can't be closed (i.e. if original quantity was 12 and only 8/0 were executed then this order is not closed)
                df_matching_sold_positions = portfolio['sold'][(portfolio['sold']['position'] == 'long') & (portfolio['sold']['ticker'] == ticker) & (portfolio['sold']['balance'] == quantity) & (portfolio['sold']['trade_notes'].isin(["Filled", "~Filled"])) & (portfolio['sold']['sell_date'] <= order_time + timedelta(minutes=10)) & (portfolio['sold']['sell_date'] >= order_time - timedelta(minutes=10))] # maybe refactor here and below 10 minutes, depends on frequency of selling and manual selling, also quantity -  assuming that two of same tickers which are sold at nearly the same time (usually due to PDT error) have different quantities - can maybe refactor for other_notes to include something like 'ATrade Error/PDT' for now balance should work most cases
                if not df_matching_sold_positions.empty:
                    if len(df_matching_sold_positions) > 1: # maybe refactor
                        print("Error with ticker: " + ticker + " sold on " + str(order_time))
                        continue
                    idx, sell_price_actual = df_matching_sold_positions.index[0], float(closed_order.filled_avg_price)
                    if portfolio['sold'].loc[idx, 'sell_price'] != sell_price_actual: # maybe refactor - assuming that buy_price is accurately set in previous for loop before we encounter an issue like this
                        buy_price, sell_price, balance = portfolio['sold'].loc[idx, ['buy_price', 'sell_price', 'balance']]
                        roi_actual = (sell_price_actual - buy_price) / buy_price
                        portfolio['balance']['usd'] = portfolio['balance']['usd'] - (sell_price - sell_price_actual)*balance # sold: 10 actual: 11/9 balance: 50 -> -50,50
                        portfolio['sold'].loc[idx, ['sell_price', 'roi']] = [sell_price_actual, roi_actual]
    print("portfolio aligned prices with alpaca")
    return portfolio

# Since Alpaca adjusts Account day trading buying power at their discretion. This will normally be based upon the Alpaca's risk assessment of the stocks volatility and liquidity (I think for example if buy risky stock will have less buying power in case risky stock gets out of money and don't have enough collateral to cover)
def portfolio_align_buying_power_with_alpaca(portfolio, alpaca_account): # maybe refactor name to portfolio_align_balance_with_alpaca # maybe refactor to add fail safe for if alpaca_account comes in as {}
    available_cash = float(alpaca_account.buying_power) # maybe refactor fluctuates in non-market hours (potentially afterhours market) and might have to do with margin alpaca_account and also during market hours (back and forth to same number on 08/17/2020 11am-1pm PST)
    if not (math.isclose(available_cash, portfolio['balance']['usd'], rel_tol=0.20) and (portfolio['balance']['usd'] <= available_cash)): # maybe refactor and check for balance locked # quick fix to keep portfolio['balance']['usd'] accurate and conservative since alpaca_account.buying_power fluctuating (think due to margin alpaca_account)
        portfolio_balance_usd_previous, portfolio['balance']['usd'] = portfolio['balance']['usd'], available_cash # here and other locations keep _usd_ in name even though default (value/price) is in usd as precautionary (for iuportant cases) also so don't get confused with % return in other cases ie. decreased_return vs. decreased_usd_return
        print("Portfolio Available USD Balance (before correction): " + str(portfolio_balance_usd_previous) + ", (after correction): " + str(portfolio['balance']['usd']))
    print("portfolio aligned buying power with alpaca, " + "Portfolio Available USD Balance: " + str(portfolio['balance']['usd']))
    return portfolio

def portfolio_calculate_roi(portfolio, open_positions=True, sold_positions=False, avoid_paper_positions=False): # doesn't follow intuitio when compared to overall portfolio value due to compounding returns
    value_of_current_investments, value_of_sold_investments, cost_of_investments = 0, 0, 0 # maybe refactor to avoid divide by zero errors
    if open_positions:
        for ticker in portfolio['open'].index:
            if avoid_paper_positions and (portfolio['open'].loc[ticker, 'position'] == 'long-p'):
                continue
            current_price, buy_price, balance = portfolio['open'].loc[ticker, ['current_price', 'buy_price', 'balance']] # maybe refactor and multiply columns and sum
            value_of_current_investments += current_price*balance
            cost_of_investments += buy_price*balance
    if sold_positions: # maybe refactor and use portfolio['balance']['usd']
        for idx in portfolio['sold'].index:
            if avoid_paper_positions and (portfolio['sold'].loc[idx, 'position'] == 'long-p'):
                continue
            sell_price, buy_price, balance = portfolio['sold'].loc[idx, ['sell_price', 'buy_price', 'balance']] # maybe refactor and multiply columns and sum
            value_of_sold_investments += sell_price*balance
            cost_of_investments += buy_price*balance
    if cost_of_investments: # maybe refactor, to deal with if only paper_trades issue (divide by zero)
        return (value_of_current_investments + value_of_sold_investments - cost_of_investments) / cost_of_investments
    else:
        return float("NaN")

def sleep_until_30_min(paper_trading, paper_trading_on_used_account, portfolio_usd_value_negative_change_from_max_limit, portfolio_current_roi_restart, download_and_save_tickers_data): # maybe refactor to allow for different sleeping times (i.e. 30, 60 min) # maybe refactor name to sleep_until_30_min_while_trading() # , buying_disabled
    time_to_sleep = (30.0 - datetime.now(eastern).minute) if (datetime.now(eastern).minute < 30) else (60.0 - datetime.now(eastern).minute) # max((60.0 - datetime.now(eastern).minute) % 30.0, 1) # maybe refactor logic (make simpler)
    print("<< Sleeping " + str(time_to_sleep) + "min at " + str(datetime.now()) + ", paper trading: " + str(paper_trading) + ", paper trading on used account: " + str(paper_trading_on_used_account) + ", portfolio usd value (-)change from max limit: " + str(portfolio_usd_value_negative_change_from_max_limit) + ", portfolio current roi restart: " + str(portfolio_current_roi_restart) + ", download and save tickers data: " + str(download_and_save_tickers_data) + " >>") #  + ", buying disabled: " + str(buying_disabled) # maybe add back to shorten: str(datetime.now())[:19]) - should always be [:19] unless in ~8000 years or if timing format changes
    time.sleep(time_to_sleep*60.0) # not needed 30*60.0 - *60) # turning into seconds

# maybe refactor, pause buying / terminate program
def portfolio_panic_sell(portfolio, df_matching_open_positions): # maybe refactor and add paper trading / backtesting, would have to add some other logic # , paper_trading - paper_trading would be precautionary since function shouldn't be called if paper trading # , , idx_start, idx_end):
    for ticker,row in df_matching_open_positions.iterrows(): # if don't use iterrows(): ticker = df_matching_open_positions.index[0]
        other_notes = 'Panic Sell'
        position, buy_price, quantity = row[['position', 'buy_price', 'balance']]
        quantity, price, alpaca_ticker_order, alpaca_ticker_open_orders, trade_notes = alpaca_trade_ticker(ticker=ticker, side="sell", quantity=quantity, paper_trading=(True if position == 'long-p' else False), other_notes=other_notes) # paper_trading # row['position']
        sell_price, sell_date = price, datetime.now()
        roi = (sell_price - buy_price) / buy_price
        portfolio['balance']['usd'] = portfolio['balance']['usd'] + sell_price*quantity # here and other locations where making calculations after alpaca_trade_ticker(): quantity should always == balance when quantity specified in alpaca_trade_ticker() since if quantity given then that quantity is used no matter what
        buy_date, fmp_24h_vol, gtrends_15d, rank_rise_d, tsl_max_price = portfolio['open'].loc[ticker, ['buy_date', 'fmp_24h_vol', 'gtrends_15d', 'rank_rise_d', 'tsl_max_price']]
        portfolio['sold'].loc[len(portfolio['sold'])], portfolio['open'] = [ticker, position, buy_date, buy_price, quantity, sell_date, sell_price, roi, fmp_24h_vol, gtrends_15d, rank_rise_d, tsl_max_price, trade_notes, other_notes], portfolio['open'].drop(ticker) # portfolio['sold'], portfolio['open'] = portfolio['sold'].append(portfolio['open'].loc[ticker].drop(['current_date', 'current_price', 'current_roi', 'tsl_armed', 'trade_notes', 'other_notes']).append(pd.Series([ticker, sell_date, sell_price, roi, trade_notes, other_notes], index=['ticker', 'sell_date', 'sell_price', 'roi', 'trade_notes', 'other_notes'])), ignore_index=True), portfolio['open'].drop(ticker)
    return portfolio
    # don't add retry logic for now, this would mean that I would have to keep the program running after panic_sell() finishes running, which would not be normal, can add retry_binance_open_orders_in_portfolio() if change my mind

def retry_alpaca_open_orders_in_portfolio(portfolio, alpaca_open_orders, open_order_price_difference=0.15, open_time=15): # paper_trading
    for open_order in alpaca_open_orders:
        ticker = open_order.symbol
        original_quantity, executed_quantity, order_id, side, order_time = float(open_order.qty), float(open_order.filled_qty), open_order.id, open_order.side, datetime.fromtimestamp(datetime.timestamp(open_order.created_at)) # open_order also has 'updateTime' 'status' 'isWorking' 'clientOrderId' might be useful # maybe refactor shouldn't be a float() issue but precautionary # maybe refactor name orderId to order_id
        df_matching_open_positions = portfolio['open'][(portfolio['open']['position'] == 'long') & (portfolio['open'].index == ticker) & (portfolio['open']['trade_notes'].isin(["Not filled", "Partially filled", "~Filled"]))] # (portfolio['open']['position'] == 'long') precautionary  since if ticker in portfolio then the position must be 'long' (since listed on alpaca as open order) and there can't be 2 different open positions (one 'long-p', one 'long') for the same ticker # assuming it's a long position have not implemented shorting: # also assuming side is a BUY, should always be a buy if in positions['open'] can add precautionary check but have to worry about alpaca api changing their api for side logic # maybe add precautionary check for order_time withing +/- 10 minutes (also original_quantity) if worried about interfering with manual buys: & (portfolio['open']['buy_date'] <= order_time + timedelta(minutes=10)) & (portfolio['open']['buy_date'] >= order_time - timedelta(minutes=10)), # maybe refactor - "~Filled" here since sometimes "~Filled" is sometimes "Partially filed", hopefully "~Filled" if "Partially filled" this function is run before run_portfolio_algo or other similar functions, if alpaca_trade_ticker() fix works can remove this precautionary measure might be good to have it in outlier cases
        df_matching_sold_positions = portfolio['sold'][(portfolio['sold']['position'] == 'long') & (portfolio['sold']['ticker'] == ticker) & (portfolio['sold']['balance'] == original_quantity) & (portfolio['sold']['trade_notes'].isin(["Not filled", "Partially filled", "~Filled"])) & (portfolio['sold']['sell_date'] <= order_time + timedelta(minutes=10)) & (portfolio['sold']['sell_date'] >= order_time - timedelta(minutes=10))] # have not implemented shorting # +/- 10 minutes since order time most likely (micro) seconds off time recorded # also assuming side is a SELL, should always be a sell if in positions['sold'] can add precautionary check but have to worry about alpaca api changing their api for side logic
        if not df_matching_open_positions.empty:
            last_trade_data = _fetch_data(alpaca_api.get_latest_trade, params={'symbol': ticker}, error_str=" - No last trade from Alpaca for ticker: " + ticker + " on: " + str(datetime.now()), empty_data = {})
            price = last_trade_data.price if last_trade_data else float("NaN")
            buy_price, quantity = portfolio['open'].loc[ticker, 'buy_price'], original_quantity - executed_quantity # assuming (and should be based on code), that original_quantity is same as portfolio['open'].loc[ticker, 'balance'], no need for precautionary check IMO # position, 'position'
            incremental_usd_invest = (price - buy_price)*quantity # maybe refactor and add abs(), should always be positive if still open order and using limit order, and even if negative (if the price suddenly drops in between checking for open orders and price and alpaca limit order error) logic should still work
            if (incremental_usd_invest <= portfolio['balance']['usd']) and ((price - buy_price) / buy_price <= open_order_price_difference): # refactor can make open_order_price_difference a parameter also not sure if necessary, can be sl/2 # maybe refactor here and below and put back in check for not np.isnan(price) since covered in expression: (price - buy_price) / buy_price <= open_order_price_difference which will be False if price == nan # maybe refactor possible edge case 2021-07-28
                resp = _fetch_data(alpaca_api.cancel_order, params={'order_id': order_id}, error_str=" - Alpaca cancel order error for ticker: " + ticker + " and order ID: " + str(order_id) + " on: " + str(datetime.now()), empty_data={})
                time.sleep(open_time) # maybe refactor - since sometimes order is cancelled and new order not created, might be due to processing times
                canceled_order = _fetch_data(alpaca_api.get_order, params={'order_id': order_id}, error_str=" - Alpaca get order error for ticker: " + ticker + " and order ID: " + str(order_id) + " on: " + str(datetime.now()), empty_data={})
                if canceled_order and canceled_order.status == 'canceled': # resp is None so can't use this: resp['status'] == 'CANCELED' # maybe refactor so far seems to cancel but not create new order which may be because of processing times between cancel call and alpaca_open_order_ids call
                    original_price = buy_price
                    quantity, price, alpaca_ticker_order, alpaca_ticker_open_orders, trade_notes = alpaca_trade_ticker(ticker=ticker, side=side, quantity=quantity, paper_trading=False, other_notes="Retrying open order for ticker: " + ticker + " bought on " + str(order_time)) # = alpaca_trade_ticker(ticker=ticker, quantity=balance, side=side, price=price, paper_trading=paper_trading, other_notes="Retrying open order for ticker: " + ticker + " bought on " + str(order_time)) # paper_trading=False here and below since already checked for portfolio['open']['position'] == 'long' in df_matching_open_positions, df_matching_sold_positions
                    new_price = (price*quantity + original_price*executed_quantity) / original_quantity
                    incremental_usd_invest = (price - buy_price)*quantity # maybe refactor and take out recalculation of incremental_usd_invest, only recalculate since price is a bit more recent
                    portfolio['balance']['usd'] = portfolio['balance']['usd'] - incremental_usd_invest
                    portfolio['open'].loc[ticker, ['buy_date', 'buy_price', 'trade_notes', 'other_notes']] = [datetime.now(), new_price, trade_notes, "Retried order"] # update buy_date in case new order is incomplete # not tracking how many times retrying order, too much logic for unlikely situation (retry more than once not likely if adjust price after an hour) # maybe refactor here and other cases when retry order and update fmp_24h_vol, a bit unnecessary but more accurate if want in future
        if not df_matching_sold_positions.empty: # maybe refactor and add precautionary check - shouldn't have to check len() == 1 since symbol, trade_notes and order_time time frame (+/- 10 minutes)
            idx = df_matching_sold_positions.index[0]
            ticker, sell_price, buy_price = portfolio['sold'].loc[idx, ['ticker', 'sell_price', 'buy_price']] # position, 'position',
            last_trade_data = _fetch_data(alpaca_api.get_latest_trade, params={'symbol': ticker}, error_str=" - No last trade from Alpaca for ticker: " + ticker + " on: " + str(datetime.now()), empty_data = {})
            price = last_trade_data.price if last_trade_data else float("NaN")
            if (price - sell_price) / sell_price >= -open_order_price_difference: # not np.isnan(price) and
                resp = _fetch_data(alpaca_api.cancel_order, params={'order_id': order_id}, error_str=" - Alpaca cancel order error for ticker: " + ticker + " and order ID: " + str(order_id) + " on: " + str(datetime.now()), empty_data={})
                time.sleep(open_time)
                canceled_order = _fetch_data(alpaca_api.get_order, params={'order_id': order_id}, error_str=" - Alpaca get order error for ticker: " + ticker + " and order ID: " + str(order_id) + " on: " + str(datetime.now()), empty_data={})
                if canceled_order and canceled_order.status == 'canceled':
                    original_price = sell_price
                    quantity = original_quantity - executed_quantity
                    quantity, price, alpaca_ticker_order, alpaca_ticker_open_orders, trade_notes = alpaca_trade_ticker(ticker=ticker, side=side, quantity=quantity, paper_trading=False, other_notes="Retrying open order for ticker: " + ticker + " sold on " + str(order_time)) # paper_trading
                    new_price = (price*quantity + original_price*executed_quantity) / original_quantity
                    new_roi = (new_price - buy_price) / buy_price # maybe refactor to (be consistent with other sell_price's) new_sell_price = new_price and (new_sell_price - buy_price) / buy_price
                    decreased_usd_return = (sell_price - price)*quantity # maybe refactor and add abs(), should always be positive if still open order and using limit order and even if negative (if the price suddenly drops in between checking for open orders and price) logic should still work
                    portfolio['balance']['usd'] = portfolio['balance']['usd'] - decreased_usd_return
                    portfolio['sold'].loc[idx, ['sell_date', 'sell_price', 'roi', 'trade_notes', 'other_notes']] = [datetime.now(), new_price, new_roi, trade_notes, "Retried order"] # maybe refactor and move "Retried Order" notes into trade_notes somehow # update sell_date in case new order is incomplete even if new executed quantity is less than original executed quantity
    return portfolio

# "ATrade Error" separate from retry_alpaca_open_orders_in_portfolio() since order did not go through initially due to insufficient funds error - (especially if during an algorithm buy preceded by an incomplete algorithm sell) or something like it, therefore no open_order associated with atrade error (and no usd locked to the positions)
def retry_atrade_error_or_paper_orders_in_portfolio(portfolio, df_matching_open_positions, df_matching_sold_positions, paper_trading, atrade_error_or_paper_order_price_difference_limit=0.15): # for now used for executing paper orders added to portfolio (during down market) # maybe refactor and change back to try and buy full USD_INVEST (or whatever left in portfolio balance) instead of original (with new price) usd_invest, for now with current portfolio better to free up space for new signals
    print("running retry_atrade_error_or_paper_orders_in_portfolio()")
    USD_INVEST_MIN = portfolio['constants']['usd_invest_min'] # USD_INVEST, portfolio['constants']['usd_invest'],
    for ticker,row in df_matching_open_positions.iterrows(): # if not df_matching_open_positions.empty:
        # if portfolio['balance']['usd'] >= USD_INVEST_MIN:
        last_trade_data = _fetch_data(alpaca_api.get_latest_trade, params={'symbol': ticker}, error_str=" - No last trade from Alpaca for ticker: " + ticker + " on: " + str(datetime.now()), empty_data = {})
        price = last_trade_data.price if last_trade_data else float("NaN")
        buy_price, quantity, buy_date = row[['buy_price', 'balance', 'buy_date']] # assuming that if "ATrade Error" that no order was placed and therefore no usd is locked (assigned to this portfolio position) # maybe refactor and declare trade_notes, it confuses a bit with orders below
        if (portfolio['balance']['usd'] >= USD_INVEST_MIN) and ((price - buy_price) / buy_price <= atrade_error_or_paper_order_price_difference_limit): # (usd_invest <= portfolio['balance']['usd']) or # maybe refacotr duplicate code here and directly below
            usd_invest = price*quantity # buy_price, using price instead of buy_price since if price > buy_price and quantity = 1 (and balance non-issue) the price > usd_invest logic will prevent buying of ticker (quantity=0 error), also better to preserve quantity if possible
            usd_invest = usd_invest if (usd_invest <= portfolio['balance']['usd']) else portfolio['balance']['usd']
            if (price > usd_invest): # not checking for fmp_24h_vol_too_low since ticker initially passed this check and therefore assumed clear to buy # checking for price_mismatch instead of if balance==1 (since logic is similar usd_invest = price*balance) to keep logic consistent throughout
                continue
            quantity, price, alpaca_ticker_order, alpaca_ticker_open_orders, trade_notes = alpaca_trade_ticker(ticker=ticker, side="buy", usd_invest=usd_invest, price=price, paper_trading=paper_trading, other_notes="Retrying " + ("ATrade Error" if row['trade_notes'] == "ATrade Error" else "Paper") + " order for ticker " + ticker + " bought on " + str(buy_date)) # maybe refactor to row['position'] == 'long-p' since paper orders != "ATrade Error", pr -e # paper_trading != False since order not bought and update to current paper_trading
            portfolio['balance']['usd'] = portfolio['balance']['usd'] - price*quantity # maybe refactor (and add logic for trade_notes != 'ATrade Error') since issue below if paper_trading and there is an erroneous position (like XLNX from 2022-02-25->03-02) that can't be sold (since listed as a sold position but not an asset), but keep since want the portfolio budget to be aligned with positions, and portfolio aligns its buying power with Alpaca before making trades regardless # usd value close enough to prevent trades from executing if underbudget, also don't check assets since want to allocate full usd value to ticker # a bit more accurate than using just usd_invest since rounding for quantity
            portfolio['open'].loc[ticker, ['position',  'buy_date', 'buy_price', 'balance', 'tsl_armed', 'tsl_max_price', 'trade_notes', 'other_notes']] = [('long' if not paper_trading else 'long-p'), datetime.now(), price, quantity, False, float("NaN"), trade_notes, ("Retried order-e" if row['trade_notes'] == "ATrade Error" else "Retried order-p")] # if incorporate long-p orders need to change 'position' # maybe refactor (especially if add long-p orders) - not adding new 'fmp_24h_vol' since want to mimick logic of retry_alpaca_open_orders_in_portfolio() and hopefully order will be retried shortly after "ATrade Error" # maybe refactor zero out current_roi but nice to see what roi was when bought and not an issue with portfolio_trading
    for idx,row in df_matching_sold_positions.iterrows():# if not df_matching_sold_positions.empty:
        sell_price, ticker, quantity, sell_date, buy_price = row[['sell_price', 'ticker', 'balance', 'sell_date', 'buy_price']] # assuming that if "ATrade Error" that no order was placed and therefore no ticker (that is selling) is locked (assigned to this portfolio position) and no usd from the order has been disbersed
        last_trade_data = _fetch_data(alpaca_api.get_latest_trade, params={'symbol': ticker}, error_str=" - No last trade from Alpaca for ticker: " + ticker + " on: " + str(datetime.now()), empty_data = {})
        price = last_trade_data.price if last_trade_data else float("NaN")
        if (price - sell_price) / sell_price >= -atrade_error_or_paper_order_price_difference_limit:
            quantity, price, alpaca_ticker_order, alpaca_ticker_open_orders, trade_notes = alpaca_trade_ticker(ticker=ticker, side="sell", quantity=quantity, paper_trading=False, other_notes="Retrying ATrade Error order for ticker " + ticker + " sold on " + str(sell_date)) # maybe refactor: paper_trading=False here and below since already checked for portfolio['sold']['position'] == 'long' in df_matching_sold_positions, add safety check maybe portfolio['open'].loc[ticker, 'position']
            roi = (price - buy_price) / buy_price
            portfolio['balance']['usd'] = portfolio['balance']['usd'] + price*quantity
            portfolio['sold'].loc[idx, ['sell_date', 'sell_price', 'roi', 'trade_notes', 'other_notes']] = [datetime.now(), price, roi, trade_notes, "Retried order-e"] # maybe refactor price to sell_price
    return portfolio

import os
from pytz import timezone

eastern = timezone('US/Eastern') # maybe refactor to mimick crypto.py which uses + timedelta(hours=7) instead of using timezone

def portfolio_trading(portfolio, paper_trading=True, paper_trading_on_used_account=False, portfolio_usd_value_negative_change_from_max_limit=-0.30, portfolio_current_roi_restart={'engaged': False, 'limit': 0.075}, download_and_save_tickers_data=False): # refactor to mimick run_portfolio_rr # short = False, possibly add short logic # maybe refactor buying_disabled to be None as default and then change within function (or if specified) based on certain conditions # , buying_disabled=False
    # global portfolio_account, twilio_client, twilio_phone_from, twilio_phone_to
    DAYS = portfolio['constants']['days']
    STOP_LOSS = portfolio['constants']['sl']
    TRAILING_STOP_LOSS_ARM, TRAILING_STOP_LOSS_PERCENTAGE = portfolio['constants']['tsl_a'], portfolio['constants']['tsl_p']
    portfolio_has_run = False
    while True:
        usa_holidays = usa_cal.holidays(start=datetime.now(eastern).replace(month=1, day=1).strftime('%Y-%m-%d'), end=datetime.now(eastern).replace(month=12, day=31).strftime('%Y-%m-%d')).to_pydatetime() # moved inside in case program runs into new year without restarting, caused error on 09/07/2020
        if (datetime.now(eastern).weekday() < 5) and (datetime.now(eastern).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None) not in usa_holidays): # .replace(tzinfo=None) since usa_holidays holds datetime objects without timezone (ie datetime.datetime(2020, 11, 26, 0, 0))
            if (datetime.now(eastern).hour == 9) and (datetime.now(eastern).minute < 4): # important that know its running before market opens
                portfolio_has_run = False
                twilio_message = _fetch_data(twilio_client.messages.create, params={'to': twilio_phone_to, 'from_': twilio_phone_from, 'body': "Q Trading @stocks #" + portfolio_account + ": running on " + str(datetime.now()) + " :)"}, error_str=" - Twilio msg error to: " + twilio_phone_to + " on: " + str(datetime.now()), empty_data=None)
                save_portfolio_backup(portfolio, remove_old_portfolio=True, usa_holidays=usa_holidays) # (True if ((datetime.now(eastern).hour == 9) and (datetime.now(eastern).minute >= 30) and (datetime.now(eastern).minute < 34)) else False) # maybe refactor, saving and removing here so don't have to add extra logic for checking time, remove old portfolio at start of next trading day (right before) since risky if delete after saving ticker data at end of day
            if ((datetime.now(eastern).hour == 16) and (datetime.now(eastern).minute < 4)): # check at end of day so sell prices are set in case want to do some analysis on portfolio after trading hours same day and buy prices are set for ATrade Errors/Open Orders executed after 15:41 EST
                portfolio = portfolio_align_prices_with_alpaca(portfolio=portfolio, open_positions=True, sold_positions=True)
                save_portfolio_backup(portfolio)
            if (datetime.now(eastern).hour >= 21) and not portfolio_has_run: #  and (datetime.now(eastern).hour < 22) # and (datetime.now(eastern).minute < 4) # datetime.now(eastern).hour >= 21 # maybe refactor - since robinhood/firstrade afterhours extensd until 6pm/8pm EST, don't run at 8pm EST since crypto downloads at 8pm (EST)/5pm (PST), Alpaca: afterhours is 4-6pm EST but risky due to less liquidity, 6-8pm EST on a market day, the order request is returned with error. Alpaca reserves this time window for future expansion of supported hours. order is submitted after 8pm EST but before 9am EST of the following trading day, the order request is queued and will be eligible for execution from the beginning of the next available supported pre-market hours at 9am EST # issue if try to restart between 0:00 and 9:00 EST
                todays_date = datetime.now() # no need to change to 13:00:00 time since fmp calls take the date in simple string format (no %H:%M:%S): datetime_object.strftime('%Y-%m-%d')
                df_tickers_interval_today = get_saved_tickers_data(date=todays_date.strftime('%Y-%m-%d'))
                if df_tickers_interval_today.empty and download_and_save_tickers_data:
                    df_tickers_interval_today = save_usa_alpaca_tickers_fmp_data(date=todays_date.strftime('%Y-%m-%d')) # maybe refactor (especially if in timezone far off eastern), not using eastern since run late at night and could extend into next day (in eastern time) # set variable within if statement
                else:
                    # df_tickers_interval_today = get_saved_tickers_data(date=todays_date.strftime('%Y-%m-%d'))
                    while df_tickers_interval_today.empty:
                        sleep_until_30_min(paper_trading=paper_trading, paper_trading_on_used_account=paper_trading_on_used_account, portfolio_usd_value_negative_change_from_max_limit=portfolio_usd_value_negative_change_from_max_limit, portfolio_current_roi_restart=portfolio_current_roi_restart, download_and_save_tickers_data=download_and_save_tickers_data) # , buying_disabled=buying_disabled
                        if todays_date.hour <= (datetime.now() - timedelta(hours=11)).hour: # implemented so that if no market data doesn't stop program from running normally # maybe refactor, 11 hours since if running on Friday next if statement might run on Saturday if data is not downloaded until 6am Saturday morning
                            break
                        df_tickers_interval_today = get_saved_tickers_data(date=todays_date.strftime('%Y-%m-%d'))
                if not paper_trading: # only align buying power when not paper trading since when paper trading balance should be aligned with current (paper) trading not actual buying power, aligning buying power after switching over from paper trading to not paper trading helps to deal with delisted tickers
                    account = _fetch_data(alpaca_api.get_account, params={}, error_str=" - No account from Alpaca on: " + str(datetime.now()), empty_data = {})
                    portfolio = portfolio_align_buying_power_with_alpaca(portfolio=portfolio, alpaca_account=account) if account else portfolio # refactor issue if save_usa_alpaca_by_yf_tickers_ms_zr_data() runs into next day # maybe refactor, quick fix to ensure program continues to run if there is an error fetching alpaca_api.get_account # not declaring account as own variable and possibly sms messaging account.equity since have Alpaca App on phone
                tickers_to_avoid = get_tickers_to_avoid(df_tickers_interval_today, todays_date) # good to check daily Alpaca might update
                portfolio = run_portfolio(portfolio=portfolio, start_day=(todays_date - timedelta(days=DAYS)), end_day=todays_date, paper_trading=paper_trading, tickers_to_avoid=tickers_to_avoid) # refactor issue if save_usa_alpaca_by_yf_tickers_ms_zr_data() runs into next day # run_portfolio() executed when saving tickers data even though buy prices are quite a bit off (>= 7%, retry orders correct some of them) since prefer to have run_portfolio() run (and orders set in) right after tickers data is saved to deal with potential errors and to have buy_date the same as day when saved tickers, not to have to wait over a weekend, to mimick crypto.py order, and to not have to relabel saved data as start of business day (instead of currently end of business day) to avoid back running # , rr_buy=(True if not buying_disabled else False) # maybe refactor can get rid DAYS = portfolio['constants']['days'] and start_day=(todays_date - timedelta(days=DAYS)) logic since this is default for run_portfolio_algorithm
                portfolio_has_run = True
                save_portfolio_backup(portfolio, date=todays_date.strftime('%Y-%m-%d')) # save here since market closed when this code runs
                twilio_message = _fetch_data(twilio_client.messages.create, params={'to': twilio_phone_to, 'from_': twilio_phone_from, 'body': "Q Trading @stocks #" + portfolio_account + ": " + ("Ticker data saved" if download_and_save_tickers_data else "") + ", run_portfolio executed, and portfolio saved for date: " + todays_date.strftime('%Y-%m-%d') + " on: " + str(datetime.now()) + " :)"}, error_str=" - Twilio msg error to: " + twilio_phone_to + " on: " + str(datetime.now()), empty_data=None)
            if (datetime.now(eastern).hour >= 9) and (datetime.now(eastern).hour < 16): # stocks: maybe refactor to get total time in seconds (from beginning of day) instead of like this, so can be more exact (i.e. start at 9:30am EST so no beforehours) # no afterhours trading since risky due to less liquidity, doesn't reflect normal market conditions # maybe refactor bug if run on Friday and data not downloaded until
                if (datetime.now(eastern).hour == 9) and (datetime.now(eastern).minute < 30): # probably refactor and add check for stocks splits before market open, minor issue for now
                    sleep_until_30_min(paper_trading=paper_trading, paper_trading_on_used_account=paper_trading_on_used_account, portfolio_usd_value_negative_change_from_max_limit=portfolio_usd_value_negative_change_from_max_limit, portfolio_current_roi_restart=portfolio_current_roi_restart, download_and_save_tickers_data=download_and_save_tickers_data) # maybe refactor, quick (and cheap in terms of processing power / logic) fix to avoid trading/using prices from less liquid beforehours trading
                print("<< " + str(datetime.now()) + ", paper trading: " + str(paper_trading) + ", paper trading on used account: " + str(paper_trading_on_used_account) + ", portfolio usd value (-)change from max limit: " + str(portfolio_usd_value_negative_change_from_max_limit) + ", portfolio current roi restart: " + str(portfolio_current_roi_restart) + " >>") #  + ", buying disabled: " + str(buying_disabled)
                start_time = time.time()
                if portfolio['constants']['type'] == 'sma_mm':
                    todays_date = datetime.now()
                    portfolio = run_portfolio(portfolio, start_day=(todays_date - timedelta(days=DAYS)), end_day=todays_date, paper_trading=paper_trading)
                for ticker in portfolio['open'].index:
                    # ok to use price from Alpaca than Yahoo Finance since more real time (I think) and unlikely there is demand/supply anomaly or arbitrage opportunity when Alpaca uses 5 main (I think) exchanges and complicated and slow to fetch Yahoo Finance data in real time (maybe refactor) - have to use get_ticker_data_detailed_yfinance()
                    last_trade_data = _fetch_data(alpaca_api.get_latest_trade, params={'symbol': ticker}, error_str=" - No last trade from Alpaca for ticker: " + ticker + " on: " + str(datetime.now()), empty_data = {}) # if a stock quote features a single price, it is the most recent sale price accoridng to investopedia.com/ask/answers/042215/what-do-bid-and-ask-prices-represent-stock-quote.asp
                    price = last_trade_data.price if last_trade_data else float("NaN")
                    if np.isnan(price):
                        print("Error retreiving Alpaca last trade price for ticker: " + ticker + " on: " + str(datetime.now()))
                        # ticker_data_quote = _fetch_data(get_ticker_data_quote_fmp, params={'ticker': ticker}, error_str=" - No ticker data quote FMP for ticker: " + ticker + " on: " + str(datetime.now()), empty_data=pd.Dataframe())
                        # price = ticker_data_quote.loc[ticker, 'price'] if not ticker_data_quote.empty else float("NaN")
                    else: # maybe refactor check for if 'position' == 'long'/'long-p' in case implement shorting, price to ensure price was calculated on Yahoo Finance
                        if portfolio['open'].loc[ticker, 'trade_notes'] in ["Not filled", "Partially filled", "ATrade Error"]: # maybe refactor quick fix for now since if using small TSL/SL sometimes price hits selling point before the ticker is bought (like PENN on 8/13/2020 at 6:32am PST when bought at 8/12/2020 21:36 PST), maybe refactor and add 'ATrade Error' or only check for 'Filled', '~Filled'
                            continue
                        position, buy_price, tsl_armed, tsl_max_price, quantity = portfolio['open'].loc[ticker, ['position', 'buy_price', 'tsl_armed', 'tsl_max_price', 'balance']]
                        price_change = (price - buy_price) / buy_price
                        if not tsl_armed and price_change >= TRAILING_STOP_LOSS_ARM:
                            tsl_armed, tsl_max_price = True, price
                        if tsl_armed:
                            if price > tsl_max_price:
                                tsl_max_price = price
                            tsl_price_change = (price - tsl_max_price) / tsl_max_price
                            if tsl_price_change <= TRAILING_STOP_LOSS_PERCENTAGE:
                                print("<<<< TICKER SOLD due to TSL >>>>")
                                other_notes = 'Sell by TSL'
                                quantity, price, alpaca_ticker_order, alpaca_ticker_open_orders, trade_notes = alpaca_trade_ticker(ticker=ticker, side="sell", quantity=quantity, paper_trading=(True if position == 'long-p' else False), other_notes=other_notes + " at ~roi " + str(price_change))
                                sell_price = price # minutely data so don't need:  tsl_max_price * (1 + TRAILING_STOP_LOSS_PERCENTAGE) # * (1 - PRICE_UNCERTAINTY_PERCENTAGE)
                                portfolio['balance']['usd'] = portfolio['balance']['usd'] + sell_price*quantity # maybe refactor balance to quantity, should be the same
                                buy_date, fmp_24h_vol, gtrends_15d, rank_rise_d = portfolio['open'].loc[ticker, ['buy_date', 'fmp_24h_vol', 'gtrends_15d', 'rank_rise_d']]
                                portfolio['sold'].loc[len(portfolio['sold'])], portfolio['open'] = [ticker, position, buy_date, buy_price, quantity, datetime.now(), sell_price, (sell_price - buy_price) / buy_price, fmp_24h_vol, gtrends_15d, rank_rise_d, tsl_max_price, trade_notes, other_notes], portfolio['open'].drop(ticker) # portfolio['sold'], portfolio['open'] = portfolio['sold'].append(portfolio['open'].loc[ticker].drop(['current_date','current_price','current_roi','tsl_armed','tsl_max_price','trade_notes', 'other_notes']).append(pd.Series([ticker, datetime.now(), sell_price, (sell_price - buy_price) / buy_price, tsl_max_price, trade_notes, other_notes], index=['ticker', 'sell_date', 'sell_price', 'roi', 'tsl_max_price', 'trade_notes', 'other_notes'])), ignore_index=True), portfolio['open'].drop(ticker) # refactor trade_notes # 'fmp_24h_vol', portfolio['open'].loc[ticker, 'fmp_24h_vol'] 'fmp_24h_vol',
                                continue
                        elif price_change <= STOP_LOSS:
                            print("<<<< TICKER SOLD due to SL >>>>")
                            other_notes = 'Sell by SL'
                            quantity, price, alpaca_ticker_order, alpaca_ticker_open_orders, trade_notes = alpaca_trade_ticker(ticker=ticker, side="sell", quantity=quantity, paper_trading=(True if position == 'long-p' else False), other_notes=other_notes + " at ~roi " + str(price_change))
                            sell_price = price # minutely data so don't need: buy_price * (1 + STOP_LOSS) # * (1 - PRICE_UNCERTAINTY_PERCENTAGE)
                            portfolio['balance']['usd'] = portfolio['balance']['usd'] + sell_price*quantity
                            buy_date, fmp_24h_vol, gtrends_15d, rank_rise_d = portfolio['open'].loc[ticker, ['buy_date', 'fmp_24h_vol', 'gtrends_15d', 'rank_rise_d']]
                            portfolio['sold'].loc[len(portfolio['sold'])], portfolio['open'] = [ticker, position, buy_date, buy_price, quantity, datetime.now(), sell_price, (sell_price - buy_price) / buy_price, fmp_24h_vol, gtrends_15d, rank_rise_d, tsl_max_price, trade_notes, other_notes], portfolio['open'].drop(ticker) # portfolio['sold'], portfolio['open'] = portfolio['sold'].append(portfolio['open'].loc[ticker].drop(['current_date','current_price','current_roi','tsl_armed','tsl_max_price','trade_notes','other_notes']).append(pd.Series([ticker, datetime.now(), sell_price, (sell_price - buy_price) / buy_price, tsl_max_price, trade_notes, other_notes], index=['ticker', 'sell_date', 'sell_price', 'roi', 'tsl_max_price', 'trade_notes', 'other_notes'])), ignore_index=True), portfolio['open'].drop(ticker) # refactor trade_notes and 'Filled'/'Not filled'/'Partially filled' logic # 'fmp_24h_vol', portfolio['open'].loc[ticker, 'fmp_24h_vol'], 'fmp_24h_vol',
                            continue
                        portfolio['open'].loc[ticker, ['current_date', 'current_price', 'current_roi', 'tsl_armed', 'tsl_max_price']] = [datetime.now(), price, price_change, tsl_armed, tsl_max_price]
                if not paper_trading_on_used_account and (datetime.now(eastern).minute >= 41) and (datetime.now(eastern).minute < 45): # >= 30 and < 34 # running at 41-45min mark since market opens on the half hour (6:30am PST/9:30am EST) and don't want to conflict with crypto potential processing build up which runs every on the half hour
                    account, alpaca_open_orders = _fetch_data(alpaca_api.get_account, params={}, error_str=" - No account from Alpaca on: " + str(datetime.now()), empty_data = {}), _fetch_data(alpaca_api.list_orders, params={'status': 'open', 'nested': True}, error_str=" - Alpaca open orders error on: " + str(datetime.now()), empty_data=['error']) # probably refactor quick fix empty_data=['error'] so that 'Not filled' orders do not become 'Filled' orders if alpaca_api.list_orders issue # seperate from account because check alpaca_open_orders below # show nested multi-leg orders # limit=100, None
                    assets = get_alpaca_assets(alpaca_account=account, alpaca_open_orders=(alpaca_open_orders if alpaca_open_orders != ['error'] else []))
                    if not paper_trading: # no need for error string if alpaca_api.get_account fails since error_str included in _fetch_data
                        portfolio, portfolio_usd_value = portfolio_align_buying_power_with_alpaca(portfolio=portfolio, alpaca_account=account), assets['current_value'].sum() # no problem here and below if assets.empty portfolio_usd_value = 0.0
                        print(str(assets) + "\nTotal Current Value: " + str(assets['current_value'].sum()) + "\nAccount Equity: " + str(account.equity) + "\nAccount Buying Power: " + str(account.buying_power) + "\nExecution time: " + str(time.time() - start_time) + "\n") # Not sure how Alpaca api deals with balance_locked
                    else:
                        portfolio_usd_value = float("NaN") # float("NaN") since don't want portfolio_panic_sell() to execute while paper trading (if paper trading ride out the bad conditions) and if issue calculating assets might be a larger issue at hand and don't want to pause
                    if alpaca_open_orders and (alpaca_open_orders != ['error']): # maybe refactor and looked at assets balance_locked, see if full balance is gone, if any locked make partial
                        print("Alpaca open orders: " + str(alpaca_open_orders))
                        portfolio = retry_alpaca_open_orders_in_portfolio(portfolio=portfolio, alpaca_open_orders=alpaca_open_orders) # , paper_trading=paper_trading
                        alpaca_open_orders = _fetch_data(alpaca_api.list_orders, params={'status': 'open', 'nested': True}, error_str=" - Alpaca open orders error on: " + str(datetime.now()), empty_data=[]) # show nested multi-leg orders # limit=100,
                        print("Alpaca open orders (after): " + str(alpaca_open_orders) + "\nExecution time: " + str(time.time() - start_time) + "\n")
                    if alpaca_open_orders != ['error']: # maybe refactor so that updates completed orders even if there are still some open_orders # update orders completed but listed as incomplete incorrectly by alpaca_trade_ticker
                        alpaca_open_orders_tickers = [open_order.symbol for open_order in alpaca_open_orders] if alpaca_open_orders else []
                        for ticker in portfolio['open'][(portfolio['open']['position'] == 'long') & (~portfolio['open'].index.isin(alpaca_open_orders_tickers)) & (portfolio['open']['trade_notes'].isin(["Not filled", "Partially filled"]))].index:
                            if not assets.empty and (ticker in assets.index) and (assets.loc[ticker, 'balance'] == portfolio['open'].loc[ticker, 'balance']): # no "ATrade Error" here since order did not go through at all and no open_order created
                                portfolio['open'].loc[ticker, 'trade_notes'] = "Filled"
                        for idx in portfolio['sold'][(portfolio['sold']['position'] == 'long') & (~portfolio['sold']['ticker'].isin(alpaca_open_orders_tickers)) & (portfolio['sold']['trade_notes'].isin(["Not filled", "Partially filled"]))].index:
                            portfolio['sold'].loc[idx, 'trade_notes'] = "Filled"
                    if not paper_trading: # if Open Orders are filled and have ATrade Error orders - then will have extra money and ATrade Error orders will be filled closer to what they were ordered at
                        account = _fetch_data(alpaca_api.get_account, params={}, error_str=" - No account from Alpaca on: " + str(datetime.now()), empty_data = {})
                        portfolio = portfolio_align_buying_power_with_alpaca(portfolio=portfolio, alpaca_account=account) if account else portfolio
                    df_matching_atrade_error_open_positions, df_matching_atrade_error_sold_positions = portfolio['open'][(portfolio['open']['position'] == 'long') & (portfolio['open']['trade_notes'] == "ATrade Error")], portfolio['sold'][(portfolio['sold']['position'] == 'long') & (portfolio['sold']['trade_notes'] == "ATrade Error")]
                    if not df_matching_atrade_error_open_positions.empty or not df_matching_atrade_error_sold_positions.empty:
                        portfolio = retry_atrade_error_or_paper_orders_in_portfolio(portfolio=portfolio, df_matching_open_positions=df_matching_atrade_error_open_positions, df_matching_sold_positions=df_matching_atrade_error_sold_positions, paper_trading=paper_trading)
                    # not used when backtesting but ok since want portfolio that performs best through bad conditions and good conditions
                    if not paper_trading and (portfolio_usd_value > portfolio['max_value']['usd']): # portfolio['balance']['max']['usd']
                        portfolio['max_value']['usd'] = portfolio_usd_value
                    if not paper_trading and ((portfolio_usd_value - portfolio['max_value']['usd']) / portfolio['max_value']['usd'] <= portfolio_usd_value_negative_change_from_max_limit):
                        df_matching_negative_current_roi_open_positions = portfolio['open'][(portfolio['open']['position'] == 'long') & (portfolio['open']['current_roi'] < 0)].sort_values('current_roi', inplace=False, ascending=True) # want to sell the most negative roi positions first
                        portfolio = portfolio_panic_sell(portfolio=portfolio, df_matching_open_positions=df_matching_negative_current_roi_open_positions) # paper_trading=paper_trading # portfolio=portfolio, paper_trading=True, idx_start=len(portfolio['open']) - 1, idx_end=len(portfolio['open']))
                        # need to align balance
                        print("Going from real trading to paper trading on: " + str(datetime.now()))
                        paper_trading, portfolio_current_roi_restart['engaged'] = True, True
                    if paper_trading and portfolio_current_roi_restart['engaged'] and (portfolio_calculate_roi(portfolio) > portfolio_current_roi_restart['limit']):
                        account, alpaca_open_orders = _fetch_data(alpaca_api.get_account, params={}, error_str=" - No account from Alpaca on: " + str(datetime.now()), empty_data = {}), _fetch_data(alpaca_api.list_orders, params={'status': 'open', 'nested': True}, error_str=" - Alpaca open orders error on: " + str(datetime.now()), empty_data=[])
                        assets = get_alpaca_assets(alpaca_account=account, alpaca_open_orders=alpaca_open_orders)
                        if account and (assets['current_value'].sum() >= portfolio['max_value']['usd']*(1+portfolio_usd_value_negative_change_from_max_limit)): # precautionary, prioritizes portfolio sl over restarting real trading, prevents potential downward spiral but requires reset of portfolio_btc_value_negative_change_from_max_limit unless there is enough momentum upon first restart (from paper to real trading)
                            print("Going from paper trading to real trading on: " + str(datetime.now()))
                            paper_trading, portfolio_current_roi_restart['engaged'] = False, False
                            df_matching_positive_current_roi_paper_open_positions = portfolio['open'][(portfolio['open']['position'] == 'long-p') & (portfolio['open']['current_roi'] > 0)].sort_values('current_roi', inplace=False, ascending=False) # maybe refactor (to assets closest to 0 current_roi) - want to buy the most positive roi positions first (the relatively cheapest)
                            portfolio = portfolio_align_buying_power_with_alpaca(portfolio=portfolio, alpaca_account=account) # checking again for account since possible retry_alpaca_open_orders_in_portfolio() or retry_atrade_error_or_paper_orders_in_portfolio() executed orders and assets are altered
                            portfolio = retry_atrade_error_or_paper_orders_in_portfolio(portfolio=portfolio, df_matching_open_positions=df_matching_positive_current_roi_paper_open_positions, df_matching_sold_positions=pd.DataFrame(), paper_trading=paper_trading, atrade_error_or_paper_order_price_difference_limit=10) # atrade_error_or_paper_order_price_difference_limit=10 so that there is no upper limit
                    portfolio = portfolio_align_prices_with_alpaca(portfolio=portfolio, open_positions=True, sold_positions=True)
                print(str(portfolio['open'].drop(['fmp_24h_vol', 'gtrends_15d', 'rank_rise_d', 'tsl_armed', 'tsl_max_price', 'trade_notes', 'other_notes'], axis=1)) + "\n" + str(portfolio['open'].drop(['position', 'buy_date', 'buy_price', 'balance', 'current_date', 'current_price', 'current_roi'], axis=1)) + \
                    "\nCurrent ROI (Real): " + str(portfolio_calculate_roi(portfolio, avoid_paper_positions=True)) + "\nCurrent ROI (All): " + str(portfolio_calculate_roi(portfolio)) + "\nExecution time: " + str(time.time() - start_time) + "\n" + \
                    (str(portfolio['sold'].tail(40).drop(['fmp_24h_vol', 'rank_rise_d', 'tsl_max_price', 'gtrends_15d'], axis=1)) + \
                    "\nSold ROI (Real): " + str(portfolio_calculate_roi(portfolio, open_positions=False, sold_positions=True, avoid_paper_positions=True)) + "\nSold ROI (All): " + str(portfolio_calculate_roi(portfolio, open_positions=False, sold_positions=True)) + \
                    "\nPortfolio ROI (Real): " + str(portfolio_calculate_roi(portfolio, open_positions=True, sold_positions=True, avoid_paper_positions=True)) + "\nPortfolio ROI (All): " + str(portfolio_calculate_roi(portfolio, open_positions=True, sold_positions=True)) + "\nPortfolio Available USD Balance: " + str(portfolio['balance']['usd']) + "\n" if (datetime.now(eastern).minute >= 41) and (datetime.now(eastern).minute < 45) else ""))
                save_portfolio_backup(portfolio)
                time.sleep(240.0 - ((time.time() - start_time) % 240.0)) # every 4 minutes since algorithms are low latency and don't want to use up excess computing power especially if running alongside crypto
            else: # business day market closed hours
                sleep_until_30_min(paper_trading=paper_trading, paper_trading_on_used_account=paper_trading_on_used_account, portfolio_usd_value_negative_change_from_max_limit=portfolio_usd_value_negative_change_from_max_limit, portfolio_current_roi_restart=portfolio_current_roi_restart, download_and_save_tickers_data=download_and_save_tickers_data) # , buying_disabled=buying_disabled
        else: # non-business days, # maybe refactor to 1 hour
            sleep_until_30_min(paper_trading=paper_trading, paper_trading_on_used_account=paper_trading_on_used_account, portfolio_usd_value_negative_change_from_max_limit=portfolio_usd_value_negative_change_from_max_limit, portfolio_current_roi_restart=portfolio_current_roi_restart, download_and_save_tickers_data=download_and_save_tickers_data) # , buying_disabled=buying_disabled

# as of 09/28/2020 changed portfolio_constants naming of file from (example) 100_100_15 to 100_-100_15
def save_portfolio_backup(portfolio, remove_old_portfolio=False, date=None, **params): # can add logic for different types of portfolio i.e. rr with different kinds of parameters i.e. different up and down moves
    # global portfolio_account
    portfolio_constants = "_".join([str(value) if key != 'up_down_move' else str(value) + ("_" + str(-value) if portfolio['constants']['type'] not in ['tilupccu', 'airs', 'tngaia', 'senate_trading', 'sma_mm'] else "") for key,value in list(portfolio['constants'].items())]) # maybe refactor if implement different algorithms, for now all algorithms (currently only rr) have equal up_move and down_move and implement both up_move and down_move
    date = date if date else datetime.now().strftime('%Y-%m-%d')
    usa_holidays = params['usa_holidays'] if 'usa_holidays' in params else {} # maybe refactor assuming that if don't pass in usa_holidays don't want to delete old portfolio_backup # {} so not in usa_holidays doesn't fail
    if remove_old_portfolio: # and (datetime.now(eastern).hour == 9) and (datetime.now().minute < 4): # maybe refactor and change < 4 (since cutting it close with other processes running before), # if (datetime.now(eastern).weekday() < 5) and ((datetime.now(eastern).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None) not in usa_holidays) and (datetime.now(eastern).hour == 9) and (datetime.now(eastern).minute < 4):
        previous_business_day = datetime.now(eastern) - timedelta(days=1)
        while previous_business_day.weekday() > 4 or (previous_business_day.replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None) in usa_holidays): # refactor doesn't account for if portfolio was saved on a weekend (since downloading data on a Friday took until Saturday early AM
            previous_business_day = previous_business_day - timedelta(days=1)
        if os.path.exists('data/stocks/saved_portfolio_backups/' + portfolio_account + '/' + 'portfolio_' + portfolio_constants + '_to_' + previous_business_day.strftime('%Y-%m-%d') + '.pckl'):
            os.remove('data/stocks/saved_portfolio_backups/' + portfolio_account + '/' + 'portfolio_' + portfolio_constants + '_to_' + previous_business_day.strftime('%Y-%m-%d') + '.pckl')
    f = open('data/stocks/saved_portfolio_backups/' + portfolio_account + '/' + 'portfolio_' + portfolio_constants + '_to_' + date + '.pckl', 'wb') # 2020_06_02, format is '%Y-%m-%d'
    pd.to_pickle(portfolio, f)
    f.close()
    print("portfolio saved")
    return portfolio

def get_saved_portfolio_backup(portfolio_name): # portfolio name is portfolio_ + constants, like: portfolio_50_20_-0.3_0.5_-0.2_0.1_0.01_True_False_False # date is a string in format '%Y-%m-%d'
    # global portfolio_account
    try:
        f = open('data/stocks/saved_portfolio_backups/' + portfolio_account + "/" + portfolio_name + '.pckl', 'rb')
        portfolio = pd.read_pickle(f)
        f.close()
    except Exception as e:
        print(str(e) + " - No saved portfolio backup in portfolio account: " + portfolio_account + " with name: " + portfolio_name)
        # refactor better to have 'exchange', 'exchange_24h_vol', 'total_24h_vol', maybe add column for 'price/volume_trend' (to eliminate ticker pumps/pumps and dumps), social metrics trends (reddit subscribers, alexa rank, ...) # for column dtypes: both didn't work - dtype=[np.datetime64, np.float64, np.datetime64, np.float64]) # dtype=np.dtype([('datetime64','float64','datetime64','float6')])) # no need for portfolio['open_orders'] since tracking assets which has balance_locked (in order) # maybe refactor 'open' index to allow for multiple 'long' positions for the same ticker but have to worry about portfolio['open'].loc[idx, ...], maybe refactor and change 'balance' to 'quantity' since portfolio not holding (meant to hold) onto assets for long term and each asset is not being refilled/sold incompletely (at least not intentionally)
        portfolio = { # 'tr', 'zr' and remove up_down_move, 'tr' have to start on '2020-05-08', first day with tradingview ratings # 'up_down_move': 100, 'days': 15, 'sl': -0.15, 'tsl_a': 0.05, 'tsl_p': -0.0125, 'usd_invest': 1000,
            'constants': {'type': 'rr', 'up_down_move': 50, 'days': 20, 'sl': -0.3, 'tsl_a': 0.5, 'tsl_p': -0.2, 'usd_invest': 2000, 'usd_invest_min': 100, 'buy_date_gtrends_15d': False, 'end_day_open_positions_gtrends_15d': False, 'end_day_open_positions_fmp_24h_vol': False, 'start_balance': {'usd': 10000}, 'start_day': '2020-05-08'}, # assuming always enforcing usd_invest_min # maybe refactor 'buy_date_gtrends_15d' to something more logical in True / False like 'collect_buy_date_gtrends_15d'
            'balance': {'usd': 10000}, # alpaca only offers margin trading so if deposit $10k actually worth $20k (meaning if it shows $10k it's actually $5k deposited)
            'max_value': {'usd': 10000}, # *2 since margin trading with Alpaca
            'open': pd.DataFrame(columns=['position', 'buy_date', 'buy_price', 'balance', 'current_date', 'current_price', 'current_roi', 'fmp_24h_vol', 'gtrends_15d', 'rank_rise_d', 'tsl_armed', 'tsl_max_price', 'trade_notes', 'other_notes']).astype({'position': 'object', 'buy_date': 'datetime64[ns]', 'buy_price': 'float64', 'balance': 'float64', 'current_date': 'datetime64[ns]', 'current_price': 'float64', 'current_roi': 'float64', 'fmp_24h_vol': 'float64', 'gtrends_15d': 'float64', 'rank_rise_d': 'float64', 'tsl_armed': 'bool', 'tsl_max_price': 'float64', 'trade_notes': 'object', 'other_notes': 'object'}),
            'sold': pd.DataFrame(columns=['ticker', 'position', 'buy_date', 'buy_price', 'balance', 'sell_date', 'sell_price', 'roi', 'fmp_24h_vol', 'gtrends_15d', 'rank_rise_d', 'tsl_max_price', 'trade_notes', 'other_notes']).astype({'ticker': 'object', 'position': 'object', 'buy_date': 'datetime64[ns]', 'buy_price': 'float64', 'balance': 'float64', 'sell_date': 'datetime64[ns]', 'sell_price': 'float64', 'roi': 'float64', 'fmp_24h_vol': 'float64', 'gtrends_15d': 'float64', 'rank_rise_d': 'float64', 'tsl_max_price': 'float64', 'trade_notes': 'object', 'other_notes': 'object'})
        }
    return portfolio
