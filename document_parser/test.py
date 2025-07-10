from kiteconnect import KiteConnect
import pandas as pd

api_key = "your_api_key"
api_secret = "your_api_secret"
request_token = "your_request_token"

kite = KiteConnect(api_key=api_key)

# Generate session and set access token
session_data = kite.generate_session(request_token, api_secret=api_secret)
kite.set_access_token(session_data["access_token"])

# Get instrument token for RELIANCE
instruments = kite.instruments("NSE")
reliance_info = next(item for item in instruments if item["tradingsymbol"] == "RELIANCE")
instrument_token = reliance_info["instrument_token"]

# Define date range and interval
from_date = "2024-07-01"
to_date = "2024-07-08"
interval = "5minute"  # For SMC analysis

# Get historical data
historical_data = kite.historical_data(instrument_token, from_date, to_date, interval)

# Save to CSV
df = pd.DataFrame(historical_data)
df.to_csv("reliance_historical_data.csv", index=False)
print("Saved to reliance_historical_data.csv")
