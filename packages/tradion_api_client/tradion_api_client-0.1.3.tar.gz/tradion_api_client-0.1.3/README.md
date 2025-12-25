# Introduction

This package is written to be used as a tradion API Client in Python.With the correct API credentials, User can access tradion interactive & market data.

## Installation

install

```bash
pip install tradion_api_client
```

## Reference

-   This is a python client package for Tradion Api. Tradion is a product from [Tradion](https://weblive.rmoneyindia.net/). The original documentation for tradion client is [click here](https://weblive.rmoneyindia.net/apidocs)

## Package Structure
- For better understanding the package, the user should have a clear understanding of the architecture of the package.

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
    │      
    ├─── __init__.py
    ├─── config.py
    ├─── exceptions.py
```
## Usage

```python
from tradion_api_client.core.interactive import InteractiveClient
from tradion_api_client.core.market_data import MarketDataClient
```