# Syriatel Cash API Python Library

A professional Python library for interacting with the Syriatel Cash API. Supports both async and sync operations with proper error handling.

## Installation

```bash
pip install -e .
```

Or install from source:
```bash
git clone <repository-url>
cd syr_cash_api
pip install -e .
```

## Quick Start

### Async Usage

```python
import asyncio
from syr_cash_api import SyriatelCashClient

async def main():
    # Using async context manager (recommended)
    async with SyriatelCashClient(api_token="your_api_token") as client:
        # Get balance
        balance = await client.get_balance("0991234567")
        print(f"Balance: {balance.balance} SYP")
        
        # Get incoming history
        history = await client.get_incoming_history(number="0991234567", page=1)
        print(f"Total transactions: {history.total}")
        for tx in history.transactions:
            print(f"{tx.date}: {tx.amount} SYP from {tx.from_gsm}")
        
        # Get outgoing history
        outgoing = await client.get_outgoing_history(code="1234", page=1)
        
        # List all active numbers
        numbers = await client.get_incoming_history()
        for num in numbers:
            print(f"Number: {num.number}, Code: {num.code}")

asyncio.run(main())
```

### Sync Usage

```python
from syr_cash_api import SyriatelCashClientSync

# Using context manager (recommended)
with SyriatelCashClientSync(api_token="your_api_token") as client:
    # Get balance
    balance = client.get_balance("0991234567")
    print(f"Balance: {balance.balance} SYP")
    
    # Get incoming history
    history = client.get_incoming_history(number="0991234567", page=1)
    print(f"Total transactions: {history.total}")
    
    # Get outgoing history
    outgoing = client.get_outgoing_history(code="1234", page=1)
    
    # List all active numbers
    numbers = client.get_incoming_history()
    for num in numbers:
        print(f"Number: {num.number}, Code: {num.code}")
```

## API Reference

### SyriatelCashClient (Async)

#### `get_balance(number: str) -> BalanceResponse`

Get Syriatel Cash balance for a phone number.

**Parameters:**
- `number` (str): Phone number in format `0XXXXXXXXX` (will be normalized)

**Returns:**
- `BalanceResponse`: Object with `balance` (int) attribute

**Raises:**
- `InvalidTokenError`: API token is invalid
- `SubscriptionExpiredError`: Subscription is expired
- `FetchFailedError`: Failed to fetch from Syriatel
- `NotAuthorizedError`: Account not authorized
- `ServerMaintenanceError`: Servers under maintenance
- `NetworkError`: Network request failed

**Example:**
```python
balance = await client.get_balance("0991234567")
print(balance.balance)  # 50000
```

#### `get_incoming_history(number=None, code=None, page=1) -> HistoryResponse | List[NumberWithCode]`

Get incoming transaction history.

**Parameters:**
- `number` (str, optional): Phone number
- `code` (str, optional): Secret code (alternative to number)
- `page` (int, optional): Page number (default: 1)

**Returns:**
- `HistoryResponse` if number/code provided: Object with `total` (int) and `transactions` (List[Transaction])
- `List[NumberWithCode]` if neither provided: List of active subscriptions

**Example:**
```python
# Get history for a number
history = await client.get_incoming_history(number="0991234567", page=1)
print(history.total)  # 25
for tx in history.transactions:
    print(tx.amount, tx.from_gsm, tx.to_gsm)

# List all active numbers
numbers = await client.get_incoming_history()
for num in numbers:
    print(num.number, num.code)
```

#### `get_outgoing_history(number=None, code=None, page=1) -> HistoryResponse | List[NumberWithCode]`

Get outgoing transaction history. Same parameters and return types as `get_incoming_history`.

### SyriatelCashClientSync (Sync)

All methods are the same as async client but without `await`:

```python
client = SyriatelCashClientSync(api_token="your_token")
balance = client.get_balance("0991234567")
history = client.get_incoming_history(number="0991234567")
```

## Data Models

### BalanceResponse

```python
@dataclass
class BalanceResponse:
    balance: int  # Balance in SYP
```

### HistoryResponse

```python
@dataclass
class HistoryResponse:
    total: int
    transactions: List[Transaction]
```

### Transaction

```python
@dataclass
class Transaction:
    transaction_no: str
    date: str
    from_gsm: str
    to_gsm: str
    amount: int
    fee: int
    net: int
    channel: str
    status: str
```

### NumberWithCode

```python
@dataclass
class NumberWithCode:
    number: str
    code: str
```

## Error Handling

The library provides specific exception classes for different error types:

```python
from syr_cash_api import (
    SyriatelCashError,           # Base exception
    InvalidTokenError,           # Invalid API token
    SubscriptionExpiredError,    # Subscription expired
    FetchFailedError,            # Fetch from Syriatel failed
    NotAuthorizedError,          # Account not authorized
    ServerMaintenanceError,      # Servers under maintenance
    NetworkError,                # Network issues
)

try:
    balance = await client.get_balance("0991234567")
except SubscriptionExpiredError:
    print("Subscription expired, please renew")
except InvalidTokenError:
    print("Invalid API token")
except NetworkError as e:
    print(f"Network error: {e}")
except SyriatelCashError as e:
    print(f"API error: {e.code} - {e.message}")
```

## Advanced Usage

### Custom Base URL

```python
client = SyriatelCashClient(
    api_token="your_token",
    base_url="https://custom-api-url.com/v1"
)
```

### Custom Timeout

```python
client = SyriatelCashClient(
    api_token="your_token",
    timeout=60  # 60 seconds
)
```

### Reusing Session (Async)

```python
import aiohttp

async with aiohttp.ClientSession() as session:
    client = SyriatelCashClient(
        api_token="your_token",
        session=session
    )
    # Use client...
    # Session will not be closed when client closes
```

### Phone Number Normalization

Phone numbers are automatically normalized:
- `+963991234567` → `0991234567`
- `963991234567` → `0991234567`
- `0991 234 567` → `0991234567`

## Requirements

- Python 3.7+
- aiohttp >= 3.8.0
- requests >= 2.28.0

## License

MIT License

## Support

For API support, visit: https://api.melchersman.com/syr-cash/

