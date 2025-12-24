# Example order book update message

orderbook_update_msg = {
    "lastUpdateId": 16070231956,
    "firstUpdateId": 16070231945,
    "bids": [
        ["205.10000000", "0.00300000"],
        ["205.09000000", "0.00100000"]
    ],
    "asks": [
        ["205.11000000", "0.00400000"],
        ["205.12000000", "0.00200000"]
    ]
}

orderbook_snapshot = {
    "lastUpdateId": 16070231956,
    "bids": [
        ["205.10000000", "0.00300000"],
        ["205.09000000", "0.00100000"]
    ],
    "asks": [
        ["205.11000000", "0.00400000"],
        ["205.12000000", "0.00200000"]
    ]
}

# Example of new trade message
trade_message = {
    "price": 20550.00,
    "quantity": 0.0015,
    "trade_id": 123456789,
    "timestamp": 1625247600000,
    "side": "buy"
}

# Example kline/candlestick data
kline_data = {
    "open_time": 1625247600000,
    "open": "20500.00",
    "high": "20600.00",
    "low": "20450.00",
    "close": "20550.00",
    "volume": "12.345",
    "close_time": 1625247659999,
}

# Example symbol information
symbol_info = {
    "symbol": "SOLUSDT",
    "status": "TRADING",
    "baseAsset": "SOL",
    "quoteAsset": "USDT",
    "baseAssetPrecision": 8,
    "quoteAssetPrecision": 8,
    "orderTypes": ["LIMIT", "MARKET"],
    "icebergAllowed": True,
    "filters": []
}