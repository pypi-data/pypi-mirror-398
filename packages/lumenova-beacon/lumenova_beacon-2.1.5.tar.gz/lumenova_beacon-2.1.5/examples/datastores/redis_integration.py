"""This example demonstrates automatic Redis tracing using OpenTelemetry RedisInstrumentor.

Creating a BeaconClient automatically sets up OpenTelemetry integration. After calling
RedisInstrumentor().instrument(), all Redis operations are automatically traced.

Requirements:
    pip install lumenova-beacon[opentelemetry,examples]
    pip install redis
    docker run -d -p 6379:6379 redis
"""

import dotenv
from opentelemetry import trace
from lumenova_beacon.core.client import BeaconClient

dotenv.load_dotenv()

client = BeaconClient()

# === Step 1: Instrument Redis ===
from opentelemetry.instrumentation.redis import RedisInstrumentor

RedisInstrumentor().instrument()


# === Step 2: Use Redis Normally ===
import redis

try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()
    print("Connected to Redis")


    # === Example 1: Basic String Operations ===
    redis_client.set("user:1:name", "Alice")
    name = redis_client.get("user:1:name")
    print(f"User name: {name}")


    # === Example 2: Expiration ===
    redis_client.setex("session:abc123", 3600, "user_data_here")
    ttl = redis_client.ttl("session:abc123")
    print(f"Session TTL: {ttl} seconds")


    # === Example 3: Hash Operations ===
    redis_client.hset("user:1", mapping={
        "name": "Alice",
        "email": "alice@example.com",
        "age": "30"
    })
    email = redis_client.hget("user:1", "email")
    user_data = redis_client.hgetall("user:1")
    print(f"User email: {email}")


    # === Example 4: List Operations ===
    redis_client.delete("notifications")
    redis_client.rpush("notifications", "Welcome!")
    redis_client.rpush("notifications", "New message")
    redis_client.rpush("notifications", "Task completed")
    notifications = redis_client.lrange("notifications", 0, -1)
    print(f"Notifications: {len(notifications)} items")


    # === Example 5: Set Operations ===
    redis_client.delete("tags")
    redis_client.sadd("tags", "python", "redis", "opentelemetry")
    tags = redis_client.smembers("tags")
    is_member = redis_client.sismember("tags", "python")
    print(f"Tags: {tags}")


    # === Example 6: Pipeline Operations ===
    pipe = redis_client.pipeline()
    pipe.set("counter:views", 100)
    pipe.incr("counter:views")
    pipe.incr("counter:views")
    pipe.get("counter:views")
    results = pipe.execute()
    print(f"Counter value: {results[-1]}")


    # === Example 7: Manual Spans with Redis ===
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("cache_user_profile") as span:
        span.set_attribute("user_id", 123)
        cached = redis_client.get("cache:user:123")

        if not cached:
            span.set_attribute("cache_hit", False)
            user_profile = {"id": 123, "name": "Bob", "email": "bob@example.com"}

            import json
            redis_client.setex("cache:user:123", 300, json.dumps(user_profile))
            span.set_attribute("cached_result", True)
            print(f"Cached user profile for user {user_profile['name']}")
        else:
            span.set_attribute("cache_hit", True)
            print("Retrieved from cache")


    # === Example 8: Transaction (MULTI/EXEC) ===
    pipe = redis_client.pipeline(transaction=True)
    pipe.multi()
    pipe.set("account:1:balance", 1000)
    pipe.decrby("account:1:balance", 100)
    pipe.incrby("account:2:balance", 100)
    pipe.execute()
    print("Transaction completed")


    # Cleanup
    redis_client.delete("user:1:name", "session:abc123", "user:1",
                       "notifications", "tags", "counter:views",
                       "cache:user:123", "account:1:balance", "account:2:balance")

    print("\nAll Redis operations successfully traced!")

except redis.ConnectionError:
    print("Could not connect to Redis on localhost:6379")
    print("Start Redis with: docker run -d -p 6379:6379 redis")

except Exception as e:
    print(f"Error: {e}")


provider = trace.get_tracer_provider()
if hasattr(provider, 'shutdown'):
    provider.shutdown()

# All Redis operations are automatically traced including commands, pipelines,
# transactions, and any connection errors.
