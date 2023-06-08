import os
import requests
import urllib.parse
import yfinance as yf

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    return render_template("apology.html", message=message), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    stock = yf.Ticker(symbol)
    currentPrice = stock.info['currentPrice']
    longName = stock.info['longName']

    # Parse response
    try:
        return {
            "name": longName,
            "price": currentPrice,
            "symbol": symbol.upper
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"