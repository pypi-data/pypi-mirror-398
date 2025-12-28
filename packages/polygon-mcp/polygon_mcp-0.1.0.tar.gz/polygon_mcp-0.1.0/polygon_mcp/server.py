#!/usr/bin/env python3
"""Polygon.io MCP Server - Wraps all Polygon SDK functions as MCP tools."""

import os
from mcp.server.fastmcp import FastMCP
import polygon

API_KEY = os.environ.get("POLYGON_API_KEY", "")

mcp = FastMCP("Polygon.io")

# Initialize clients lazily
_stocks_client = None
_options_client = None
_forex_client = None
_crypto_client = None
_reference_client = None


def get_stocks_client():
    global _stocks_client
    if _stocks_client is None:
        _stocks_client = polygon.StocksClient(API_KEY)
    return _stocks_client


def get_options_client():
    global _options_client
    if _options_client is None:
        _options_client = polygon.OptionsClient(API_KEY)
    return _options_client


def get_forex_client():
    global _forex_client
    if _forex_client is None:
        _forex_client = polygon.ForexClient(API_KEY)
    return _forex_client


def get_crypto_client():
    global _crypto_client
    if _crypto_client is None:
        _crypto_client = polygon.CryptoClient(API_KEY)
    return _crypto_client


def get_reference_client():
    global _reference_client
    if _reference_client is None:
        _reference_client = polygon.ReferenceClient(API_KEY)
    return _reference_client


# =============================================================================
# STOCKS TOOLS
# =============================================================================

@mcp.tool()
def stocks_get_sma(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 50,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Simple Moving Average for a stock symbol."""
    return get_stocks_client().get_sma(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def stocks_get_ema(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 50,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Exponential Moving Average for a stock symbol."""
    return get_stocks_client().get_ema(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def stocks_get_rsi(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 14,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Relative Strength Index for a stock symbol."""
    return get_stocks_client().get_rsi(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def stocks_get_macd(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    short_window_size: int = 12,
    long_window_size: int = 26,
    signal_window_size: int = 9,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get MACD for a stock symbol."""
    return get_stocks_client().get_macd(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        short_window_size=short_window_size, long_window_size=long_window_size,
        signal_window_size=signal_window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def stocks_get_trades(symbol: str, date: str, limit: int = 5000) -> dict:
    """Get trades for a stock on a specific date (YYYY-MM-DD)."""
    return get_stocks_client().get_trades(symbol=symbol, date=date, limit=limit)


@mcp.tool()
def stocks_get_trades_v3(
    symbol: str,
    timestamp: int | None = None,
    order: str | None = None,
    sort: str | None = None,
    limit: int = 5000,
) -> dict:
    """Get trades for a stock in a given time range (v3 API)."""
    return get_stocks_client().get_trades_v3(
        symbol=symbol, timestamp=timestamp, order=order, sort=sort, limit=limit
    )


@mcp.tool()
def stocks_get_quotes(symbol: str, date: str, limit: int = 5000) -> dict:
    """Get quotes for a stock on a specific date (YYYY-MM-DD)."""
    return get_stocks_client().get_quotes(symbol=symbol, date=date, limit=limit)


@mcp.tool()
def stocks_get_quotes_v3(
    symbol: str,
    timestamp: int | None = None,
    order: str | None = None,
    sort: str | None = None,
    limit: int = 5000,
) -> dict:
    """Get NBBO quotes for a stock in a given time range (v3 API)."""
    return get_stocks_client().get_quotes_v3(
        symbol=symbol, timestamp=timestamp, order=order, sort=sort, limit=limit
    )


@mcp.tool()
def stocks_get_last_trade(symbol: str) -> dict:
    """Get the most recent trade for a stock."""
    return get_stocks_client().get_last_trade(symbol=symbol)


@mcp.tool()
def stocks_get_last_quote(symbol: str) -> dict:
    """Get the most recent NBBO quote for a stock."""
    return get_stocks_client().get_last_quote(symbol=symbol)


@mcp.tool()
def stocks_get_daily_open_close(symbol: str, date: str, adjusted: bool = True) -> dict:
    """Get OHLCV and after-hours prices for a stock on a date (YYYY-MM-DD)."""
    return get_stocks_client().get_daily_open_close(symbol=symbol, date=date, adjusted=adjusted)


@mcp.tool()
def stocks_get_aggregate_bars(
    symbol: str,
    from_date: str,
    to_date: str,
    multiplier: int = 1,
    timespan: str = "day",
    adjusted: bool = True,
    sort: str = "asc",
    limit: int = 5000,
) -> dict:
    """Get aggregate bars (candles) for a stock. Dates in YYYY-MM-DD format."""
    return get_stocks_client().get_aggregate_bars(
        symbol=symbol, from_date=from_date, to_date=to_date, multiplier=multiplier,
        timespan=timespan, adjusted=adjusted, sort=sort, limit=limit
    )


@mcp.tool()
def stocks_get_grouped_daily_bars(date: str, adjusted: bool = True) -> dict:
    """Get daily OHLCV for entire stock market on a date (YYYY-MM-DD)."""
    return get_stocks_client().get_grouped_daily_bars(date=date, adjusted=adjusted)


@mcp.tool()
def stocks_get_previous_close(symbol: str, adjusted: bool = True) -> dict:
    """Get previous day's OHLCV for a stock."""
    return get_stocks_client().get_previous_close(symbol=symbol, adjusted=adjusted)


@mcp.tool()
def stocks_get_snapshot(symbol: str) -> dict:
    """Get current snapshot for a stock (minute, day, prev day agg, last trade/quote)."""
    return get_stocks_client().get_snapshot(symbol=symbol)


@mcp.tool()
def stocks_get_snapshot_all(symbols: list[str] | None = None) -> dict:
    """Get snapshots for all or specified stock symbols."""
    return get_stocks_client().get_snapshot_all(symbols=symbols)


@mcp.tool()
def stocks_get_current_price(symbol: str) -> float:
    """Get current market price for a stock."""
    return get_stocks_client().get_current_price(symbol=symbol)


@mcp.tool()
def stocks_get_gainers_and_losers(direction: str = "gainers") -> dict:
    """Get top 20 gainers or losers. direction: 'gainers' or 'losers'."""
    return get_stocks_client().get_gainers_and_losers(direction=direction)


# =============================================================================
# OPTIONS TOOLS
# =============================================================================

@mcp.tool()
def options_get_sma(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 50,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Simple Moving Average for an option contract."""
    return get_options_client().get_sma(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def options_get_ema(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 50,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Exponential Moving Average for an option contract."""
    return get_options_client().get_ema(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def options_get_rsi(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 14,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Relative Strength Index for an option contract."""
    return get_options_client().get_rsi(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def options_get_macd(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    short_window_size: int = 12,
    long_window_size: int = 26,
    signal_window_size: int = 9,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get MACD for an option contract."""
    return get_options_client().get_macd(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        short_window_size=short_window_size, long_window_size=long_window_size,
        signal_window_size=signal_window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def options_get_trades(
    option_symbol: str,
    timestamp: int | None = None,
    order: str = "asc",
    sort: str = "timestamp",
    limit: int = 5000,
) -> dict:
    """Get trades for an option contract."""
    return get_options_client().get_trades(
        option_symbol=option_symbol, timestamp=timestamp, order=order, sort=sort, limit=limit
    )


@mcp.tool()
def options_get_quotes(
    option_symbol: str,
    timestamp: int | None = None,
    order: str = "asc",
    sort: str = "timestamp",
    limit: int = 5000,
) -> dict:
    """Get quotes for an option contract."""
    return get_options_client().get_quotes(
        option_symbol=option_symbol, timestamp=timestamp, order=order, sort=sort, limit=limit
    )


@mcp.tool()
def options_get_last_trade(ticker: str) -> dict:
    """Get the most recent trade for an option contract."""
    return get_options_client().get_last_trade(ticker=ticker)


@mcp.tool()
def options_get_daily_open_close(symbol: str, date: str, adjusted: bool = True) -> dict:
    """Get OHLCV for an option contract on a date (YYYY-MM-DD)."""
    return get_options_client().get_daily_open_close(symbol=symbol, date=date, adjusted=adjusted)


@mcp.tool()
def options_get_aggregate_bars(
    symbol: str,
    from_date: str,
    to_date: str,
    multiplier: int = 1,
    timespan: str = "day",
    adjusted: bool = True,
    sort: str = "asc",
    limit: int = 5000,
) -> dict:
    """Get aggregate bars for an option contract. Dates in YYYY-MM-DD format."""
    return get_options_client().get_aggregate_bars(
        symbol=symbol, from_date=from_date, to_date=to_date, multiplier=multiplier,
        timespan=timespan, adjusted=adjusted, sort=sort, limit=limit
    )


@mcp.tool()
def options_get_previous_close(ticker: str, adjusted: bool = True) -> dict:
    """Get previous day's OHLC for an option contract."""
    return get_options_client().get_previous_close(ticker=ticker, adjusted=adjusted)


@mcp.tool()
def options_get_snapshot(underlying_symbol: str, option_symbol: str) -> dict:
    """Get snapshot for an option contract."""
    return get_options_client().get_snapshot(
        underlying_symbol=underlying_symbol, option_symbol=option_symbol
    )


@mcp.tool()
def options_build_symbol(
    underlying_symbol: str,
    expiry: str,
    call_or_put: str,
    strike_price: float,
) -> str:
    """Build an option symbol. expiry: YYMMDD, call_or_put: 'c'/'call' or 'p'/'put'."""
    return polygon.build_option_symbol(
        underlying_symbol=underlying_symbol, expiry=expiry,
        call_or_put=call_or_put, strike_price=strike_price
    )


@mcp.tool()
def options_parse_symbol(option_symbol: str) -> dict:
    """Parse an option symbol to extract underlying, expiry, type, strike."""
    return polygon.parse_option_symbol(option_symbol=option_symbol, output_format=dict)


# =============================================================================
# FOREX TOOLS
# =============================================================================

@mcp.tool()
def forex_get_sma(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 50,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Simple Moving Average for a forex pair. Symbol format: C:EURUSD."""
    return get_forex_client().get_sma(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def forex_get_ema(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 50,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Exponential Moving Average for a forex pair."""
    return get_forex_client().get_ema(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def forex_get_rsi(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 14,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Relative Strength Index for a forex pair."""
    return get_forex_client().get_rsi(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def forex_get_macd(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    short_window_size: int = 12,
    long_window_size: int = 26,
    signal_window_size: int = 9,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get MACD for a forex pair."""
    return get_forex_client().get_macd(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        short_window_size=short_window_size, long_window_size=long_window_size,
        signal_window_size=signal_window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def forex_real_time_conversion(
    from_symbol: str,
    to_symbol: str,
    amount: float,
    precision: int = 2,
) -> dict:
    """Convert currency using latest market rates. e.g., USD to EUR."""
    return get_forex_client().real_time_currency_conversion(
        from_symbol=from_symbol, to_symbol=to_symbol, amount=amount, precision=precision
    )


@mcp.tool()
def forex_get_historic_ticks(
    from_symbol: str,
    to_symbol: str,
    date: str,
    limit: int = 500,
) -> dict:
    """Get historic trade ticks for a forex pair on a date (YYYY-MM-DD)."""
    return get_forex_client().get_historic_forex_ticks(
        from_symbol=from_symbol, to_symbol=to_symbol, date=date, limit=limit
    )


@mcp.tool()
def forex_get_quotes(
    symbol: str,
    timestamp: int | None = None,
    order: str | None = None,
    sort: str | None = None,
    limit: int = 5000,
) -> dict:
    """Get NBBO quotes for a forex pair."""
    return get_forex_client().get_quotes(
        symbol=symbol, timestamp=timestamp, order=order, sort=sort, limit=limit
    )


@mcp.tool()
def forex_get_last_quote(from_symbol: str, to_symbol: str) -> dict:
    """Get the last quote for a forex pair."""
    return get_forex_client().get_last_quote(from_symbol=from_symbol, to_symbol=to_symbol)


@mcp.tool()
def forex_get_aggregate_bars(
    symbol: str,
    from_date: str,
    to_date: str,
    multiplier: int = 1,
    timespan: str = "day",
    adjusted: bool = True,
    sort: str = "asc",
    limit: int = 5000,
) -> dict:
    """Get aggregate bars for a forex pair. Symbol format: C:EURUSD."""
    return get_forex_client().get_aggregate_bars(
        symbol=symbol, from_date=from_date, to_date=to_date, multiplier=multiplier,
        timespan=timespan, adjusted=adjusted, sort=sort, limit=limit
    )


@mcp.tool()
def forex_get_grouped_daily_bars(date: str, adjusted: bool = True) -> dict:
    """Get daily OHLC for entire forex market on a date (YYYY-MM-DD)."""
    return get_forex_client().get_grouped_daily_bars(date=date, adjusted=adjusted)


@mcp.tool()
def forex_get_previous_close(symbol: str, adjusted: bool = True) -> dict:
    """Get previous day's OHLC for a forex pair."""
    return get_forex_client().get_previous_close(symbol=symbol, adjusted=adjusted)


@mcp.tool()
def forex_get_gainers_and_losers(direction: str = "gainers") -> dict:
    """Get top 20 forex gainers or losers."""
    return get_forex_client().get_gainers_and_losers(direction=direction)


# =============================================================================
# CRYPTO TOOLS
# =============================================================================

@mcp.tool()
def crypto_get_sma(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 50,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Simple Moving Average for a crypto pair. Symbol format: X:BTCUSD."""
    return get_crypto_client().get_sma(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def crypto_get_ema(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 50,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Exponential Moving Average for a crypto pair."""
    return get_crypto_client().get_ema(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def crypto_get_rsi(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    window_size: int = 14,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get Relative Strength Index for a crypto pair."""
    return get_crypto_client().get_rsi(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        window_size=window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def crypto_get_macd(
    symbol: str,
    timestamp: str | None = None,
    timespan: str = "day",
    adjusted: bool = True,
    short_window_size: int = 12,
    long_window_size: int = 26,
    signal_window_size: int = 9,
    series_type: str = "close",
    order: str = "desc",
    limit: int = 5000,
) -> dict:
    """Get MACD for a crypto pair."""
    return get_crypto_client().get_macd(
        symbol=symbol, timestamp=timestamp, timespan=timespan, adjusted=adjusted,
        short_window_size=short_window_size, long_window_size=long_window_size,
        signal_window_size=signal_window_size, series_type=series_type, order=order, limit=limit
    )


@mcp.tool()
def crypto_get_historic_trades(
    from_symbol: str,
    to_symbol: str,
    date: str,
    limit: int = 500,
) -> dict:
    """Get historic trades for a crypto pair on a date (YYYY-MM-DD)."""
    return get_crypto_client().get_historic_trades(
        from_symbol=from_symbol, to_symbol=to_symbol, date=date, limit=limit
    )


@mcp.tool()
def crypto_get_trades(
    symbol: str,
    timestamp: int | None = None,
    order: str | None = None,
    sort: str | None = None,
    limit: int = 5000,
) -> dict:
    """Get trades for a crypto pair in a time range."""
    return get_crypto_client().get_trades(
        symbol=symbol, timestamp=timestamp, order=order, sort=sort, limit=limit
    )


@mcp.tool()
def crypto_get_last_trade(from_symbol: str, to_symbol: str) -> dict:
    """Get the last trade for a crypto pair."""
    return get_crypto_client().get_last_trade(from_symbol=from_symbol, to_symbol=to_symbol)


@mcp.tool()
def crypto_get_daily_open_close(
    from_symbol: str,
    to_symbol: str,
    date: str,
    adjusted: bool = True,
) -> dict:
    """Get open/close for a crypto pair on a date (YYYY-MM-DD)."""
    return get_crypto_client().get_daily_open_close(
        from_symbol=from_symbol, to_symbol=to_symbol, date=date, adjusted=adjusted
    )


@mcp.tool()
def crypto_get_aggregate_bars(
    symbol: str,
    from_date: str,
    to_date: str,
    multiplier: int = 1,
    timespan: str = "day",
    adjusted: bool = True,
    sort: str = "asc",
    limit: int = 5000,
) -> dict:
    """Get aggregate bars for a crypto pair. Symbol format: X:BTCUSD."""
    return get_crypto_client().get_aggregate_bars(
        symbol=symbol, from_date=from_date, to_date=to_date, multiplier=multiplier,
        timespan=timespan, adjusted=adjusted, sort=sort, limit=limit
    )


@mcp.tool()
def crypto_get_grouped_daily_bars(date: str, adjusted: bool = True) -> dict:
    """Get daily OHLC for entire crypto market on a date (YYYY-MM-DD)."""
    return get_crypto_client().get_grouped_daily_bars(date=date, adjusted=adjusted)


@mcp.tool()
def crypto_get_previous_close(symbol: str, adjusted: bool = True) -> dict:
    """Get previous day's OHLC for a crypto pair."""
    return get_crypto_client().get_previous_close(symbol=symbol, adjusted=adjusted)


@mcp.tool()
def crypto_get_snapshot_all(symbols: list[str]) -> dict:
    """Get snapshots for specified crypto symbols."""
    return get_crypto_client().get_snapshot_all(symbols=symbols)


@mcp.tool()
def crypto_get_snapshot(symbol: str) -> dict:
    """Get snapshot for a single crypto pair."""
    return get_crypto_client().get_snapshot(symbol=symbol)


@mcp.tool()
def crypto_get_gainers_and_losers(direction: str = "gainers") -> dict:
    """Get top 20 crypto gainers or losers."""
    return get_crypto_client().get_gainers_and_losers(direction=direction)


@mcp.tool()
def crypto_get_level2_book(symbol: str) -> dict:
    """Get level 2 order book for a crypto pair."""
    return get_crypto_client().get_level2_book(symbol=symbol)


# =============================================================================
# REFERENCE TOOLS
# =============================================================================

@mcp.tool()
def reference_get_tickers(
    symbol: str = "",
    symbol_type: str = "",
    market: str = "",
    exchange: str = "",
    active: bool = True,
    sort: str = "ticker",
    order: str = "asc",
    limit: int = 1000,
    search: str | None = None,
) -> dict:
    """Query all ticker symbols supported by Polygon (stocks, crypto, forex)."""
    return get_reference_client().get_tickers(
        symbol=symbol, symbol_type=symbol_type, market=market, exchange=exchange,
        active=active, sort=sort, order=order, limit=limit, search=search
    )


@mcp.tool()
def reference_get_ticker_types(
    asset_class: str | None = None,
    locale: str | None = None,
) -> dict:
    """Get mapping of ticker types to their descriptive names."""
    return get_reference_client().get_ticker_types(asset_class=asset_class, locale=locale)


@mcp.tool()
def reference_get_ticker_details(symbol: str, date: str | None = None) -> dict:
    """Get detailed info about a ticker and the company behind it."""
    return get_reference_client().get_ticker_details(symbol=symbol, date=date)


@mcp.tool()
def reference_get_option_contract(ticker: str, as_of_date: str | None = None) -> dict:
    """Get info about an option contract."""
    return get_reference_client().get_option_contract(ticker=ticker, as_of_date=as_of_date)


@mcp.tool()
def reference_get_option_contracts(
    underlying_ticker: str | None = None,
    contract_type: str | None = None,
    expired: bool = False,
    expiration_date: str | None = None,
    order: str = "asc",
    sort: str = "expiration_date",
    limit: int = 1000,
) -> dict:
    """List option contracts with various filters."""
    return get_reference_client().get_option_contracts(
        underlying_ticker=underlying_ticker, contract_type=contract_type, expired=expired,
        expiration_date=expiration_date, order=order, sort=sort, limit=limit
    )


@mcp.tool()
def reference_get_ticker_news(
    symbol: str | None = None,
    limit: int = 100,
    order: str = "desc",
    sort: str = "published_utc",
) -> dict:
    """Get news articles for a ticker symbol."""
    return get_reference_client().get_ticker_news(
        symbol=symbol, limit=limit, order=order, sort=sort
    )


@mcp.tool()
def reference_get_stock_dividends(
    ticker: str | None = None,
    ex_dividend_date: str | None = None,
    limit: int = 1000,
    sort: str = "pay_date",
    order: str = "asc",
) -> dict:
    """Get historical cash dividends for stocks."""
    return get_reference_client().get_stock_dividends(
        ticker=ticker, ex_dividend_date=ex_dividend_date, limit=limit, sort=sort, order=order
    )


@mcp.tool()
def reference_get_stock_financials(
    ticker: str | None = None,
    cik: str | None = None,
    company_name: str | None = None,
    sic: str | None = None,
    filing_date: str | None = None,
    period_of_report_date: str | None = None,
    time_frame: str | None = None,
    include_sources: bool = False,
    order: str = "asc",
    limit: int = 50,
    sort: str = "filing_date",
) -> dict:
    """Get historical financial data for a stock from SEC filings."""
    return get_reference_client().get_stock_financials_vx(
        ticker=ticker, cik=cik, company_name=company_name, sic=sic,
        filing_date=filing_date, period_of_report_date=period_of_report_date,
        time_frame=time_frame, include_sources=include_sources,
        order=order, limit=limit, sort=sort
    )


@mcp.tool()
def reference_get_stock_splits(
    ticker: str | None = None,
    execution_date: str | None = None,
    reverse_split: bool | None = None,
    order: str = "asc",
    sort: str = "execution_date",
    limit: int = 1000,
) -> dict:
    """Get historical stock splits."""
    return get_reference_client().get_stock_splits(
        ticker=ticker, execution_date=execution_date, reverse_split=reverse_split,
        order=order, sort=sort, limit=limit
    )


@mcp.tool()
def reference_get_market_holidays() -> dict:
    """Get upcoming market holidays and their open/close times."""
    return get_reference_client().get_market_holidays()


@mcp.tool()
def reference_get_market_status() -> dict:
    """Get current trading status of exchanges and markets."""
    return get_reference_client().get_market_status()


@mcp.tool()
def reference_get_conditions(
    asset_class: str | None = None,
    data_type: str | None = None,
    condition_id: int | None = None,
    limit: int = 50,
    sort: str = "name",
) -> dict:
    """List all conditions that Polygon uses."""
    return get_reference_client().get_conditions(
        asset_class=asset_class, data_type=data_type, condition_id=condition_id,
        limit=limit, sort=sort
    )


@mcp.tool()
def reference_get_exchanges(
    asset_class: str | None = None,
    locale: str | None = None,
) -> dict:
    """List all exchanges that Polygon knows about."""
    return get_reference_client().get_exchanges(asset_class=asset_class, locale=locale)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
