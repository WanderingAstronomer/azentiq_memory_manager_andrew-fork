import redis

# Connect to Redis
redis_client = redis.Redis.from_url("redis://localhost:6379/0")

# Flush all data
redis_client.flushall()

print("Redis cache cleared successfully!")
