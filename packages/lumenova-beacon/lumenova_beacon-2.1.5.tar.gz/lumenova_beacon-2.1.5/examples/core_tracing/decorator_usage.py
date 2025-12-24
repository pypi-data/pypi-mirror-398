"""This example demonstrates automatic tracing using the @trace decorator.

The decorator creates spans with type "function" and automatically captures
function inputs, outputs, execution timing, and code location. It supports
three syntax options: @trace, @trace(), and @trace(name="custom").
"""
import dotenv
from lumenova_beacon import trace

dotenv.load_dotenv()

# === Decorator Syntax 1: @trace (no parentheses) ===
@trace
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


# === Decorator Syntax 2: @trace(name="custom") (custom span name) ===
@trace(name="multiply_operation")
def multiply(x: int, y: int) -> int:
    """Multiply two numbers. The span will use the custom name 'multiply_operation'."""
    return x * y

# === Decorator Syntax 3: class methods ===
class OrderProcessor:
    """Example class demonstrating tracing on methods."""

    def __init__(self, tax_rate: float = 0.08):
        self.tax_rate = tax_rate

    @trace
    def calculate_subtotal(self, items: list[dict]) -> float:
        """Calculate subtotal before tax."""
        return sum(item["price"] * item["quantity"] for item in items)

    @trace
    def calculate_tax(self, subtotal: float) -> float:
        """Calculate tax amount."""
        return subtotal * self.tax_rate

    @trace()
    def process_order(self, items: list[dict]) -> dict:
        """Process an order and return final amounts.

        This creates nested spans with calculate_subtotal and calculate_tax as children.
        """
        subtotal = self.calculate_subtotal(items)
        tax = self.calculate_tax(subtotal)
        total = subtotal + tax

        return {
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
        }


if __name__ == "__main__":
    # Call traced functions
    result1 = add_numbers(10, 12)
    print(f"Addition result: {result1}")

    result2 = multiply(5, 7)
    print(f"Multiplication result: {result2}")

    # Process an order with traced methods
    processor = OrderProcessor(tax_rate=0.08)
    order_items = [
        {"price": 10.0, "quantity": 2},
        {"price": 5.0, "quantity": 3},
    ]
    result3 = processor.process_order(order_items)
    print(f"Order result: {result3}")
