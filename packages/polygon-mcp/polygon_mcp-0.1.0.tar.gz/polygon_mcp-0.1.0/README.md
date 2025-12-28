# Polygon.io MCP Server

MCP server wrapping the Polygon.io Python SDK for stocks, options, forex, and crypto market data.

## Installation

```bash
cd polygon_mcp
uv pip install -e .
```

## Configuration

Set your Polygon.io API key as an environment variable:

```bash
export POLYGON_API_KEY="your_api_key_here"
```

## Usage

### Run directly

```bash
uv run polygon-mcp
```

### MCP Configuration

Add to your MCP config (e.g., `~/.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "polygon": {
      "command": "uv",
      "args": ["--directory", "/path/to/polygon_mcp", "run", "polygon-mcp"],
      "env": {
        "POLYGON_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Available Tools

### Stocks
- `stocks_get_sma` - Simple Moving Average
- `stocks_get_ema` - Exponential Moving Average
- `stocks_get_rsi` - Relative Strength Index
- `stocks_get_macd` - MACD
- `stocks_get_trades` - Trades for a date
- `stocks_get_trades_v3` - Trades v3 API
- `stocks_get_quotes` - Quotes for a date
- `stocks_get_quotes_v3` - NBBO quotes v3
- `stocks_get_last_trade` - Most recent trade
- `stocks_get_last_quote` - Most recent quote
- `stocks_get_daily_open_close` - Daily OHLCV
- `stocks_get_aggregate_bars` - Candles/bars
- `stocks_get_grouped_daily_bars` - Market-wide daily bars
- `stocks_get_previous_close` - Previous day OHLCV
- `stocks_get_snapshot` - Current snapshot
- `stocks_get_snapshot_all` - All snapshots
- `stocks_get_current_price` - Current price
- `stocks_get_gainers_and_losers` - Top movers

### Options
- `options_get_sma/ema/rsi/macd` - Technical indicators
- `options_get_trades` - Option trades
- `options_get_quotes` - Option quotes
- `options_get_last_trade` - Most recent trade
- `options_get_daily_open_close` - Daily OHLCV
- `options_get_aggregate_bars` - Candles/bars
- `options_get_previous_close` - Previous day OHLC
- `options_get_snapshot` - Option snapshot
- `options_build_symbol` - Build option symbol
- `options_parse_symbol` - Parse option symbol

### Forex
- `forex_get_sma/ema/rsi/macd` - Technical indicators
- `forex_real_time_conversion` - Currency conversion
- `forex_get_historic_ticks` - Historic ticks
- `forex_get_quotes` - NBBO quotes
- `forex_get_last_quote` - Last quote
- `forex_get_aggregate_bars` - Candles/bars
- `forex_get_grouped_daily_bars` - Market-wide daily
- `forex_get_previous_close` - Previous day OHLC
- `forex_get_gainers_and_losers` - Top movers

### Crypto
- `crypto_get_sma/ema/rsi/macd` - Technical indicators
- `crypto_get_historic_trades` - Historic trades
- `crypto_get_trades` - Trades in time range
- `crypto_get_last_trade` - Last trade
- `crypto_get_daily_open_close` - Daily open/close
- `crypto_get_aggregate_bars` - Candles/bars
- `crypto_get_grouped_daily_bars` - Market-wide daily
- `crypto_get_previous_close` - Previous day OHLC
- `crypto_get_snapshot_all` - All snapshots
- `crypto_get_snapshot` - Single snapshot
- `crypto_get_gainers_and_losers` - Top movers
- `crypto_get_level2_book` - Order book

### Reference
- `reference_get_tickers` - Query tickers
- `reference_get_ticker_types` - Ticker type mappings
- `reference_get_ticker_details` - Ticker details
- `reference_get_option_contract` - Option contract info
- `reference_get_option_contracts` - List option contracts
- `reference_get_ticker_news` - News articles
- `reference_get_stock_dividends` - Dividend history
- `reference_get_stock_financials` - SEC financials
- `reference_get_stock_splits` - Split history
- `reference_get_market_holidays` - Market holidays
- `reference_get_market_status` - Market status
- `reference_get_conditions` - Polygon conditions
- `reference_get_exchanges` - Exchange list
