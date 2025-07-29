"""Script to check Redis keys and values."""
import redis
import sys
import json
from pprint import pprint

# Connect to Redis
redis_url = "redis://localhost:6379/0"
r = redis.from_url(redis_url)

def list_all_keys(pattern="*"):
    """List all keys matching pattern."""
    print(f"\n{'=' * 80}")
    print(f"Listing Redis keys matching: {pattern}")
    print(f"{'=' * 80}")
    
    keys = list(r.scan_iter(pattern))
    
    if not keys:
        print("No keys found.")
        return []
    
    print(f"Found {len(keys)} keys:")
    for i, key in enumerate(keys):
        if isinstance(key, bytes):
            key_str = key.decode('utf-8')
        else:
            key_str = key
        print(f"{i+1}. {key_str}")
    
    return keys

def inspect_key(key):
    """Inspect a key's type and value."""
    if isinstance(key, bytes):
        key_str = key.decode('utf-8')
    else:
        key_str = key
        
    print(f"\n{'=' * 80}")
    print(f"Inspecting key: {key_str}")
    print(f"{'=' * 80}")
    
    key_type = r.type(key).decode('utf-8')
    print(f"Type: {key_type}")
    
    if key_type == 'string':
        value = r.get(key)
        if value:
            try:
                # Try to decode and parse as JSON
                value_str = value.decode('utf-8')
                json_obj = json.loads(value_str)
                print("JSON value:")
                pprint(json_obj, indent=2)
            except (UnicodeDecodeError, json.JSONDecodeError):
                print(f"Raw value: {value}")
    elif key_type == 'hash':
        hash_data = r.hgetall(key)
        print("Hash data:")
        for k, v in hash_data.items():
            k_str = k.decode('utf-8') if isinstance(k, bytes) else k
            try:
                v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                print(f"  {k_str}: {v_str}")
            except:
                print(f"  {k_str}: [binary data]")
    else:
        print(f"Inspection of type {key_type} not implemented.")

def main():
    """Main entry point."""
    print("Redis Key Inspector")
    
    try:
        # Check Redis connection
        if not r.ping():
            print("Error: Could not connect to Redis")
            sys.exit(1)
        
        print("Connected to Redis successfully!")
        
        # List all keys
        keys = list_all_keys()
        
        # Look for memory related keys
        memory_keys = list_all_keys("*memory*")
        
        # Look for specific memory ID if provided as arg
        if len(sys.argv) > 1:
            memory_id = sys.argv[1]
            print(f"\nLooking for memory ID: {memory_id}")
            
            # Try various patterns
            patterns = [
                f"*:{memory_id}",
                f"*{memory_id}*",
            ]
            
            for pattern in patterns:
                specific_keys = list_all_keys(pattern)
                
                # Inspect each key found
                for key in specific_keys:
                    inspect_key(key)
        
        # Check for working memory keys specifically
        working_keys = list_all_keys("*working*")
        
        # Inspect a few working memory keys if found
        for key in working_keys[:3]:  # Limit to first 3 to avoid overwhelming output
            inspect_key(key)
            
    except redis.RedisError as e:
        print(f"Redis error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
