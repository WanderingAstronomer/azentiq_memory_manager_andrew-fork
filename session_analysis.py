#!/usr/bin/env python3
"""
Script to analyze Redis memory contents by session ID.
"""

import redis
import json
import re
from collections import Counter, defaultdict
from datetime import datetime

# Connect to Redis
r = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

def extract_session_id(key):
    """Extract session ID from a Redis key."""
    # Pattern: memory:tier:session_id:app:main:uuid
    pattern = r"memory:[^:]+:([^:]+):"
    match = re.search(pattern, key)
    if match:
        return match.group(1)
    return None

def get_tier_from_key(key):
    """Extract memory tier from a Redis key."""
    # Pattern: memory:tier:session_id:...
    pattern = r"memory:([^:]+):"
    match = re.search(pattern, key)
    if match:
        return match.group(1)
    return None

def analyze_redis_by_session():
    """Analyze Redis memories by session ID."""
    all_keys = r.keys("memory:*")
    
    # Group keys by session ID
    session_keys = defaultdict(list)
    for key in all_keys:
        session_id = extract_session_id(key)
        if session_id:
            session_keys[session_id].append(key)
    
    print(f"Found {len(session_keys)} unique sessions in Redis")
    
    # Analyze each session
    for session_id, keys in session_keys.items():
        print(f"\n\n=== SESSION: {session_id} ===")
        
        # Count by tier
        tiers = Counter()
        for key in keys:
            tier = get_tier_from_key(key)
            if tier:
                tiers[tier] += 1
        
        print(f"Total memories: {len(keys)}")
        for tier, count in tiers.items():
            print(f"  {tier}: {count}")
            
        # Analyze memory types and devices
        device_count = defaultdict(int)
        memory_types = Counter()
        timestamps = []
        
        # Sample some memory content
        sample_count = min(5, len(keys))
        
        for key in keys[:sample_count]:
            try:
                value = r.get(key)
                memory = json.loads(value)
                
                if "metadata" in memory:
                    metadata = memory["metadata"]
                    memory_type = metadata.get("type", "unknown")
                    memory_types[memory_type] += 1
                    
                    device_id = metadata.get("device_id", "unknown")
                    device_count[device_id] += 1
                    
                    timestamp = metadata.get("timestamp")
                    if timestamp:
                        timestamps.append(timestamp)
            except Exception as e:
                print(f"Error processing memory: {e}")
        
        # Count all memory types and devices
        all_memory_types = Counter()
        all_devices = Counter()
        
        for key in keys:
            try:
                value = r.get(key)
                memory = json.loads(value)
                
                if "metadata" in memory:
                    metadata = memory["metadata"]
                    memory_type = metadata.get("type", "unknown")
                    all_memory_types[memory_type] += 1
                    
                    device_id = metadata.get("device_id", "unknown")
                    all_devices[device_id] += 1
            except:
                pass
        
        # Print memory type counts
        print("\nMemory types:")
        for memory_type, count in all_memory_types.items():
            print(f"  {memory_type}: {count}")
            
        # Print device counts
        print("\nDevices:")
        for device, count in all_devices.items():
            print(f"  {device}: {count}")
            
        # Print timestamp range if available
        if timestamps:
            try:
                print(f"\nTimestamp range: {min(timestamps)} to {max(timestamps)}")
            except:
                pass

def main():
    try:
        r.ping()
        print("Connected to Redis successfully")
        analyze_redis_by_session()
    except Exception as e:
        print(f"Redis error: {e}")

if __name__ == "__main__":
    main()
