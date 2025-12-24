"""This example demonstrates creating nested spans that form a trace hierarchy.

Child spans automatically inherit session_id from their parent,
creating a consistent trace hierarchy throughout the call chain.
"""
import dotenv
from lumenova_beacon import trace

dotenv.load_dotenv()

@trace
def fetch_user_data(user_id: int) -> dict:
    """Fetch user data from database."""
    return {"id": user_id, "name": "Alice", "email": "alice@example.com"}


@trace
def fetch_user_orders(user_id: int) -> list[dict]:
    """Fetch orders for a user."""
    return [
        {"order_id": 1, "amount": 99.99},
        {"order_id": 2, "amount": 149.99},
    ]


@trace
def calculate_total_spent(orders: list[dict]) -> float:
    """Calculate total amount spent."""
    return sum(order["amount"] for order in orders)


@trace(session_id='session-3445')
def get_user_profile(user_id: int) -> dict:
    """Get complete user profile with order history.

    All child function calls will inherit session_id='session-3445'.
    """
    user_data = fetch_user_data(user_id)
    orders = fetch_user_orders(user_id)
    total_spent = calculate_total_spent(orders)

    return {
        **user_data,
        "orders": orders,
        "total_spent": total_spent,
    }


if __name__ == "__main__":
    profile = get_user_profile(123)
    print(f"User: {profile['name']}, Total spent: ${profile['total_spent']}")

# Trace hierarchy:
# get_user_profile (root)
#   ├── fetch_user_data
#   ├── fetch_user_orders
#   └── calculate_total_spent
