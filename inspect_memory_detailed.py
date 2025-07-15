import redis
import json
from pprint import pprint
from collections import Counter

def decode_redis_value(value):
    """Decode Redis value to JSON if possible"""
    if not value:
        return None
    
    try:
        decoded = value.decode('utf-8')
        return json.loads(decoded)
    except:
        return {"content": "Not JSON decodable"}

def inspect_memory_tiers(session_id=None):
    """Print memory contents from Redis with detailed statistics"""
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
    
    # Analyze SHORT_TERM memories
    short_term_types = Counter()
    short_term_devices = Counter()
    
    for key in short_term_keys:
        value = redis_client.get(key)
        decoded = decode_redis_value(value)
        if decoded and "metadata" in decoded:
            memory_type = decoded["metadata"].get("type", "unknown")
            short_term_types[memory_type] += 1
            
            device_id = decoded["metadata"].get("device_id")
            if device_id:
                short_term_devices[device_id] += 1
    
    # Analyze WORKING memories
    working_types = Counter()
    working_devices = Counter()
    
    for key in working_keys:
        value = redis_client.get(key)
        decoded = decode_redis_value(value)
        if decoded and "metadata" in decoded:
            memory_type = decoded["metadata"].get("type", "unknown")
            working_types[memory_type] += 1
            
            device_id = decoded["metadata"].get("device_id")
            if device_id:
                working_devices[device_id] += 1
    
    # Print SHORT_TERM statistics
    print("\n--- SHORT_TERM MEMORY BREAKDOWN ---")
    print("Types:")
    for type_name, count in short_term_types.most_common():
        print(f"  {type_name}: {count}")
    
    print("\nDevices:")
    for device_name, count in short_term_devices.most_common():
        print(f"  {device_name}: {count}")
    
    # Print WORKING statistics
    print("\n--- WORKING MEMORY BREAKDOWN ---")
    print("Types:")
    for type_name, count in working_types.most_common():
        print(f"  {type_name}: {count}")
    
    print("\nDevices:")
    for device_name, count in working_devices.most_common():
        print(f"  {device_name}: {count}")
    
    # Print samples from each memory tier
    print("\n--- SAMPLE SHORT_TERM MEMORIES ---")
    sample_short_term(redis_client, short_term_keys)
    
    print("\n--- SAMPLE WORKING MEMORIES ---")
    sample_working(redis_client, working_keys)

def sample_short_term(redis_client, keys, samples_per_type=2):
    """Sample memories of each type from SHORT_TERM tier"""
    type_samples = {}
    
    # First pass: categorize by type
    for key in keys:
        value = redis_client.get(key)
        decoded = decode_redis_value(value)
        if decoded and "metadata" in decoded:
            memory_type = decoded["metadata"].get("type", "unknown")
            if memory_type not in type_samples:
                type_samples[memory_type] = []
            
            if len(type_samples[memory_type]) < samples_per_type:
                type_samples[memory_type].append((key, decoded))
    
    # Second pass: print samples
    for memory_type, samples in type_samples.items():
        print(f"\n{memory_type.upper()} SAMPLES:")
        for i, (key, decoded) in enumerate(samples):
            key_str = key.decode('utf-8')
            print(f"\n  {i+1}. {key_str}")
            
            if memory_type == "telemetry":
                device_id = decoded["metadata"].get("device_id", "N/A")
                timestamp = decoded["metadata"].get("timestamp", "N/A")
                print(f"     Device: {device_id}")
                print(f"     Timestamp: {timestamp}")
                
                metrics = decoded.get("content", {})
                if isinstance(metrics, str):
                    try:
                        metrics = json.loads(metrics)
                    except:
                        pass
                print(f"     Metrics: {metrics}")
            else:
                print(f"     Content: {decoded.get('content', '')[:200]}")

def sample_working(redis_client, keys, samples_per_type=2):
    """Sample memories of each type from WORKING tier"""
    type_samples = {}
    
    # First pass: categorize by type
    for key in keys:
        value = redis_client.get(key)
        decoded = decode_redis_value(value)
        if decoded and "metadata" in decoded:
            memory_type = decoded["metadata"].get("type", "unknown")
            if memory_type not in type_samples:
                type_samples[memory_type] = []
            
            if len(type_samples[memory_type]) < samples_per_type:
                type_samples[memory_type].append((key, decoded))
    
    # Second pass: print samples
    for memory_type, samples in type_samples.items():
        print(f"\n{memory_type.upper()} SAMPLES:")
        for i, (key, decoded) in enumerate(samples):
            key_str = key.decode('utf-8')
            print(f"\n  {i+1}. {key_str}")
            
            device_id = decoded["metadata"].get("device_id", "N/A")
            if device_id != "N/A":
                print(f"     Device: {device_id}")
            
            content = decoded.get("content", "")
            print(f"     Content: {str(content)[:200]}" + ("..." if len(str(content)) > 200 else ""))

if __name__ == "__main__":
    inspect_memory_tiers()
