"""
Example usage of Syriatel Cash API library
"""

import asyncio
from syr_cash_api import (
    SyriatelCashClient,
    SyriatelCashClientSync,
    SubscriptionExpiredError,
    InvalidTokenError,
    NetworkError,
)


async def async_example():
    """Example of async usage"""
    print("=== Async Example ===\n")
    
    # Replace with your actual API token
    api_token = "your_api_token_here"
    
    try:
        async with SyriatelCashClient(api_token=api_token) as client:
            # Get balance
            print("Getting balance...")
            balance = await client.get_balance("0991234567")
            print(f"Balance: {balance.balance} SYP\n")
            
            # Get incoming history
            print("Getting incoming history...")
            history = await client.get_incoming_history(
                number="0991234567",
                page=1
            )
            print(f"Total transactions: {history.total}")
            for tx in history.transactions[:5]:  # Show first 5
                print(f"  - {tx.date}: {tx.amount} SYP from {tx.from_gsm} to {tx.to_gsm}")
            print()
            
            # List all active numbers
            print("Listing all active numbers...")
            numbers = await client.get_incoming_history()
            for num in numbers:
                print(f"  - Number: {num.number}, Code: {num.code}")
            print()
            
    except SubscriptionExpiredError:
        print("Error: Subscription expired")
    except InvalidTokenError:
        print("Error: Invalid API token")
    except NetworkError as e:
        print(f"Error: Network issue - {e}")
    except Exception as e:
        print(f"Error: {e}")


def sync_example():
    """Example of sync usage"""
    print("=== Sync Example ===\n")
    
    # Replace with your actual API token
    api_token = "your_api_token_here"
    
    try:
        with SyriatelCashClientSync(api_token=api_token) as client:
            # Get balance
            print("Getting balance...")
            balance = client.get_balance("0991234567")
            print(f"Balance: {balance.balance} SYP\n")
            
            # Get outgoing history
            print("Getting outgoing history...")
            history = client.get_outgoing_history(code="1234", page=1)
            print(f"Total transactions: {history.total}")
            for tx in history.transactions[:5]:  # Show first 5
                print(f"  - {tx.date}: {tx.amount} SYP from {tx.from_gsm} to {tx.to_gsm}")
            print()
            
    except SubscriptionExpiredError:
        print("Error: Subscription expired")
    except InvalidTokenError:
        print("Error: Invalid API token")
    except NetworkError as e:
        print(f"Error: Network issue - {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Run async example
    asyncio.run(async_example())
    
    print("\n" + "="*50 + "\n")
    
    # Run sync example
    sync_example()

