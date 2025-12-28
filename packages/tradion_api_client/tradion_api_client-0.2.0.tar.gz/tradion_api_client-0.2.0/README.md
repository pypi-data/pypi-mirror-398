# Introduction

This package is written to be used as a tradion API Client in Python. With the correct API credentials, User can access tradion interactive & market data.

## Installation

install

```bash
pip install tradion_api_client
```

## Reference

-   This is a python client package for Tradion Api. Tradion is a product from [Tradion](https://weblive.rmoneyindia.net/). The original documentation for tradion client is [click here](https://weblive.rmoneyindia.net/apidocs)

## Package Structure

-   For better understanding the package, the user should have a clear understanding of the architecture of the package.

Here is the folder structure of the project:

```
└───tradion_api_client
    ├─── core
    │    ├─── __init__.py
    │    ├─── interactive.py
    │    └─── market_data.py
    ├─── utils
    │    ├─── __init__.py
    │    ├─── http_client.py
    │    └─── logger.py
    ├─── __init__.py
    ├─── config.py
    ├─── exceptions.py
```

## Features

-   **Authentication**: Login with password and OTP
-   **Order Management**: Place, modify, and cancel orders
-   **Portfolio**: View positions and holdings
-   **Funds**: Check available margins
-   **Market Data**: Real-time streaming via WebSocket
-   **Contract Master**: Download contract files and search for instrument tokens by trading symbol

## Usage

```python
from tradion_api_client import InteractiveClient
from tradion_api_client import MarketDataClient
```

### Contract Master

Download contract master files and search for instrument tokens:

```python
import asyncio
from tradion_api_client import InteractiveClient

async def main():
    client = InteractiveClient()
    
    # Download contract master file
    nse_file = await client.download_contract_master("NSE")
    print(f"Downloaded: {nse_file}")
    
    # Get token by trading symbol (use correct format for eg. -EQ suffix)
    token_info = await client.get_token_by_symbol("RELIANCE-EQ", "NSE")
    if token_info:
        print(f"Token: {token_info['token']}")
        print(f"Lot Size: {token_info['lot_size']}")
    
    # Get symbol of indices by using this method
    indices_token_info_nse = await client.get_token_by_symbol("NIFTY 50", "NSE", "INDICES.json")
    indices_token_info_bse = await client.get_token_by_symbol("SENSEX", "BSE", "INDICES.json")
    indices_token_info_mcx = await client.get_token_by_symbol("MCXAGRI", "MCX", "INDICES.json")
    
    await client.close()

asyncio.run(main())
```

For more details, see [Contract Master Documentation](docs/contract_master.md)