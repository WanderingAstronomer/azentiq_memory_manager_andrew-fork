#!/usr/bin/env python3
"""
Simple script to dump all Redis keys and their content for debugging.
"""

import redis
import json
from collections import Counter

# Connect to Redis
r = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

def main():
    # Check Redis connection
    try:
        r.ping()
        print("Connected to Redis successfully")
    except Exception as e:
        print(f"Redis connection error: {e}")
        return
        
    # Get all keys
    all_keys = r.keys("*")
    print(f"Total Redis keys: {len(all_keys)}")
    
    # Count key prefixes
    key_prefixes = Counter()
    for key in all_keys:
        parts = key.split(":")
        if len(parts) > 0:
            key_prefixes[parts[0]] += 1
    
    print("\nKey prefixes:")
    for prefix, count in key_prefixes.most_common():
        print(f"  {prefix}: {count}")
    
    # Memory tiers breakdown
    memory_tiers = Counter()
    total_short_term = 0
    total_working = 0
    
    session_ids = Counter()
    device_ids = Counter()
    memory_types = Counter()
    
    # Sample keys
    print("\nSampling keys:")
    for key in all_keys[:5]:
        print(f"\n--- KEY: {key} ---")
        try:
            key_type = r.type(key)
            print(f"Type: {key_type}")
            
            if key_type == "string":
                value = r.get(key)
                try:
                    # Try to parse as JSON
                    data = json.loads(value)
                    print(f"JSON data: {json.dumps(data, indent=2)[:200]}...")
                    
                    # Extract metadata
                    if "tier" in data:
                        memory_tiers[data["tier"]] += 1
                        if data["tier"] == "SHORT_TERM":
                            total_short_term += 1
                        elif data["tier"] == "WORKING":
                            total_working += 1
                    
                    if "metadata" in data:
                        if "session_id" in data["metadata"]:
                            session_ids[data["metadata"]["session_id"]] += 1
                        if "device_id" in data["metadata"]:
                            device_ids[data["metadata"]["device_id"]] += 1
                        if "type" in data["metadata"]:
                            memory_types[data["metadata"]["type"]] += 1
                            
                except:
                    print(f"String value: {value[:100]}...")
            elif key_type == "hash":
                value = r.hgetall(key)
                print(f"Hash value: {value}")
            else:
                print(f"Other type, not showing value")
                
        except Exception as e:
            print(f"Error processing key: {e}")
    
    # Print summary stats
    print("\n=== SUMMARY ===")
    print(f"Total SHORT_TERM memories: {total_short_term}")
    print(f"Total WORKING memories: {total_working}")
    
    if session_ids:
        print("\nSessions:")
        for session_id, count in session_ids.most_common():
            print(f"  {session_id}: {count} memories")
    
    if device_ids:
        print("\nDevices:")
        for device_id, count in device_ids.most_common():
            print(f"  {device_id}: {count} memories")
    
    if memory_types:
        print("\nMemory types:")
        for memory_type, count in memory_types.most_common():
            print(f"  {memory_type}: {count} memories")
    
    # Offer to dump a specific key for more detailed inspection
    if all_keys:
        print("\nRun this script with a specific key name to see its full content:")
        print(f"Example: python redis_dump.py {all_keys[0]}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Dump specific key if provided
        key = sys.argv[1]
        try:
            key_type = r.type(key)
            print(f"Key: {key}, Type: {key_type}")
            
            if key_type == "string":
                value = r.get(key)
                try:
                    # Try to parse as JSON
                    data = json.loads(value)
                    print(f"JSON data:\n{json.dumps(data, indent=2)}")
                except:
                    print(f"String value: {value}")
            elif key_type == "hash":
                value = r.hgetall(key)
                print(f"Hash value: {value}")
            else:
                print(f"Other type, not showing value")
        except Exception as e:
            print(f"Error processing key: {e}")
    else:
        main()
