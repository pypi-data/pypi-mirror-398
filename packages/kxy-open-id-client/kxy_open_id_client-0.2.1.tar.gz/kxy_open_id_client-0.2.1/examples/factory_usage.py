"""
Example usage of IdGeneratorFactory and AsyncIdGeneratorFactory
"""

import asyncio
from kxy_open_id_client import SegmentClient, IdGeneratorFactory, AsyncIdGeneratorFactory


def sync_example():
    """Synchronous example using IdGeneratorFactory"""
    print("=== Synchronous Factory Example ===\n")

    # Create a shared client
    client = SegmentClient(base_url="http://localhost:5801")

    # Create factory with default segment count
    factory = IdGeneratorFactory(
        segment_client=client,
        system_code="my-system",
        db_name="my_database",
        segment_count=10000
    )

    # Generate IDs for different tables
    print("Generating user IDs:")
    for _ in range(5):
        user_id = factory.get_generator("users").next_id()
        print(f"  User ID: {user_id}")

    print("\nGenerating order IDs:")
    for _ in range(5):
        order_id = factory.get_generator("orders", "order_id").next_id()
        print(f"  Order ID: {order_id}")

    print("\nGenerating product IDs:")
    for _ in range(5):
        product_id = factory.get_generator("products").next_id()
        print(f"  Product ID: {product_id}")

    # The same generator instance is reused
    print("\nReusing generators (same instances):")
    gen1 = factory.get_generator("users")
    gen2 = factory.get_generator("users")
    print(f"  gen1 is gen2: {gen1 is gen2}")  # True


async def async_example():
    """Asynchronous example using AsyncIdGeneratorFactory"""
    print("\n=== Asynchronous Factory Example ===\n")

    # Create a shared client
    client = SegmentClient(base_url="http://localhost:5801")

    # Create async factory
    factory = AsyncIdGeneratorFactory(
        segment_client=client,
        system_code="my-system",
        db_name="my_database",
        segment_count=10000
    )

    # Generate IDs for different tables
    print("Generating user IDs:")
    user_gen = await factory.get_generator("users")
    for _ in range(5):
        user_id = await user_gen.next_id()
        print(f"  User ID: {user_id}")

    print("\nGenerating order IDs:")
    order_gen = await factory.get_generator("orders", "order_id")
    for _ in range(5):
        order_id = await order_gen.next_id()
        print(f"  Order ID: {order_id}")

    # Concurrent ID generation from multiple tables
    print("\nConcurrent ID generation:")
    tasks = []
    for i in range(3):
        user_gen = await factory.get_generator("users")
        order_gen = await factory.get_generator("orders")
        tasks.append(user_gen.next_id())
        tasks.append(order_gen.next_id())

    results = await asyncio.gather(*tasks)
    print(f"  Generated IDs: {results}")


def custom_segment_count_example():
    """Example with custom segment count per table"""
    print("\n=== Custom Segment Count Example ===\n")

    client = SegmentClient(base_url="http://localhost:5801")

    # Factory with default segment count of 10000
    factory = IdGeneratorFactory(
        segment_client=client,
        system_code="my-system",
        db_name="my_database",
        segment_count=10000
    )

    # Use default segment count for users table
    user_gen = factory.get_generator("users")

    # Use custom segment count for high-traffic orders table
    order_gen = factory.get_generator("orders", "order_id", segment_count=50000)

    print(f"User generator segment count: {user_gen.segment_count}")
    print(f"Order generator segment count: {order_gen.segment_count}")


if __name__ == "__main__":
    # Note: These examples require a running KXY Open ID Service
    # Uncomment to run when service is available

    # sync_example()
    # asyncio.run(async_example())
    # custom_segment_count_example()

    print("\nExamples are ready to run!")
    print("Start the KXY Open ID Service and uncomment the function calls to test.")
