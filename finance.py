import yfinance as yf

def lookup(symbol):
    stock = yf.Ticker(symbol)
    currentPrice = stock.info['currentPrice']
    longName = stock.info['longName']
    info = {
        "name": longName,
        "price": currentPrice,
        "symbol": symbol
    }
    return info


print(lookup('aapl'))