import redis
import json

# Connect to Redis
redis_client = redis.Redis.from_url("redis://localhost:6379/0")

# Get all keys
all_keys = redis_client.keys("*")
print(f"Total keys before cleanup: {len(all_keys)}")

# Check memory tiers
short_term_keys = redis_client.keys("*:short_term:*")
working_keys = redis_client.keys("*:working:*")
print(f"Short-term memory entries: {len(short_term_keys)}")
print(f"Working memory entries: {len(working_keys)}")

# Print sample of keys to understand what's stored
print("\nSample of 5 keys:")
for key in list(all_keys)[:5]:
    key_str = key.decode('utf-8')
    print(f"- {key_str}")
    try:
        value = redis_client.get(key)
        if value:
            print(f"  Value type: {type(value)}")
            # Try to decode and parse as JSON
            try:
                decoded = value.decode('utf-8')
                parsed = json.loads(decoded)
                print(f"  Content type: {type(parsed)}")
                # Print a preview of content
                if isinstance(parsed, dict) and 'metadata' in parsed:
                    print(f"  Metadata: {parsed['metadata']}")
            except:
                print(f"  Not JSON decodable")
    except:
        print("  Could not retrieve value")

# Flush all data
print("\nFlushing all Redis data...")
redis_client.flushall()

# Verify cleanup
remaining_keys = redis_client.keys("*")
print(f"Keys remaining after cleanup: {len(remaining_keys)}")
print("Redis cache cleared successfully!")
