import redis
import json
from pprint import pprint
import sys

def decode_redis_value(value):
    """Decode Redis value to JSON if possible"""
    if not value:
        return None
    
    try:
        decoded = value.decode('utf-8')
        return json.loads(decoded)
    except:
        return {"content": "Not JSON decodable"}

def inspect_memory_tiers(session_id=None, limit=10):
    """Print memory contents from Redis"""
    redis_client = redis.Redis.from_url("redis://localhost:6379/0")
    
    # Get keys for each tier
    short_term_keys = redis_client.keys("*:short_term:*")
    working_keys = redis_client.keys("*:working:*")
    
    print(f"Total SHORT_TERM memories: {len(short_term_keys)}")
    print(f"Total WORKING memories: {len(working_keys)}")
    
    # Filter by session ID if provided
    if session_id:
        short_term_keys = [k for k in short_term_keys if session_id.encode() in k]
        working_keys = [k for k in working_keys if session_id.encode() in k]
        print(f"Filtered by session_id '{session_id}':")
        print(f"  SHORT_TERM memories: {len(short_term_keys)}")
        print(f"  WORKING memories: {len(working_keys)}")
    
    # Print SHORT_TERM samples
    print("\n--- SHORT_TERM MEMORY SAMPLES ---")
    for i, key in enumerate(short_term_keys[:limit]):
        key_str = key.decode('utf-8')
        print(f"\n{i+1}. {key_str}")
        value = redis_client.get(key)
        decoded = decode_redis_value(value)
        if decoded and "metadata" in decoded:
            memory_type = decoded["metadata"].get("type", "unknown")
            device_id = decoded["metadata"].get("device_id", "N/A")
            timestamp = decoded["metadata"].get("timestamp", "N/A")
            print(f"   Type: {memory_type}")
            print(f"   Device: {device_id}")
            print(f"   Timestamp: {timestamp}")
            
            # For telemetry data, show the actual values
            if memory_type == "telemetry":
                metrics = decoded.get("content", {})
                if isinstance(metrics, str):
                    try:
                        metrics = json.loads(metrics)
                    except:
                        pass
                print(f"   Metrics: {metrics}")
    
    # Print WORKING samples
    print("\n--- WORKING MEMORY SAMPLES ---")
    for i, key in enumerate(working_keys[:limit]):
        key_str = key.decode('utf-8')
        print(f"\n{i+1}. {key_str}")
        value = redis_client.get(key)
        decoded = decode_redis_value(value)
        if decoded and "metadata" in decoded:
            memory_type = decoded["metadata"].get("type", "unknown")
            print(f"   Type: {memory_type}")
            
            # For anomalies and insights, show the content
            if memory_type in ["anomaly", "insight", "trend_analysis"]:
                device_id = decoded["metadata"].get("device_id", "N/A")
                print(f"   Device: {device_id}")
                content = decoded.get("content", "")
                print(f"   Content: {content[:200]}..." if len(str(content)) > 200 else f"   Content: {content}")

if __name__ == "__main__":
    # Use session ID from command line if provided
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    # Use limit from command line if provided
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    inspect_memory_tiers(session_id, limit)
