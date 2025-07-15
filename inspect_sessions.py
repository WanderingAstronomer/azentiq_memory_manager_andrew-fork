#!/usr/bin/env python3
"""
Script to inspect Redis memory contents with session ID information.
"""

import redis
import json
import argparse
from datetime import datetime
from collections import Counter, defaultdict

# Connect to Redis
r = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

def get_unique_sessions():
    """Get a list of unique session IDs in Redis."""
    sessions = set()
    keys = r.keys("memory:*")
    for key in keys:
        try:
            # Check the key type first
            key_type = r.type(key)
            if key_type == "hash":
                memory_data = r.hgetall(key)
                if "metadata" in memory_data:
                    try:
                        metadata = json.loads(memory_data["metadata"])
                        if "session_id" in metadata:
                            sessions.add(metadata["session_id"])
                    except:
                        pass
        except:
            pass
    return sessions

def analyze_session(session_id):
    """Analyze memories for a specific session."""
    short_term_memories = []
    working_memories = []
    
    keys = r.keys("memory:*")
    for key in keys:
        try:
            # Check the key type first
            key_type = r.type(key)
            if key_type != "hash":
                continue
                
            memory_data = r.hgetall(key)
            if "metadata" in memory_data and "tier" in memory_data:
                try:
                    metadata = json.loads(memory_data["metadata"])
                    if metadata.get("session_id") == session_id:
                        if memory_data["tier"] == "SHORT_TERM":
                            short_term_memories.append({
                                "id": key,
                                "content": memory_data.get("content", "")[:50] + "...",
                                "metadata": metadata,
                                "timestamp": metadata.get("timestamp", "unknown")
                            })
                        elif memory_data["tier"] == "WORKING":
                            working_memories.append({
                                "id": key,
                                "content": memory_data.get("content", "")[:50] + "...",
                                "metadata": metadata,
                                "timestamp": metadata.get("timestamp", "unknown")
                            })
                except Exception as e:
                    print(f"Error processing metadata: {e}")
        except Exception as e:
            print(f"Error processing key {key}: {e}")
            continue

    print(f"\n\n=== SESSION: {session_id} ===")
    print(f"SHORT_TERM memories: {len(short_term_memories)}")
    print(f"WORKING memories: {len(working_memories)}")
    
    # Analyze device breakdown for this session
    devices_st = Counter()
    types_st = Counter()
    for mem in short_term_memories:
        devices_st[mem["metadata"].get("device_id", "unknown")] += 1
        types_st[mem["metadata"].get("type", "unknown")] += 1
    
    print("\nSHORT_TERM Types:")
    for type_name, count in types_st.items():
        print(f"  {type_name}: {count}")
    
    print("\nSHORT_TERM Devices:")
    for device, count in devices_st.items():
        print(f"  {device}: {count}")
    
    # Show earliest and latest timestamps
    if short_term_memories:
        try:
            timestamps = [m["timestamp"] for m in short_term_memories if "timestamp" in m]
            if timestamps:
                print(f"\nEarliest timestamp: {min(timestamps)}")
                print(f"Latest timestamp: {max(timestamps)}")
        except:
            pass
    
    # Sample content from SHORT_TERM
    if short_term_memories:
        print("\nSample SHORT_TERM memories:")
        for i, mem in enumerate(short_term_memories[:3]):
            print(f"  {i+1}. [{mem['metadata'].get('type', 'unknown')}] {mem['content']}")
            
    # Sample content from WORKING
    if working_memories:
        print("\nSample WORKING memories:")
        for i, mem in enumerate(working_memories[:3]):
            print(f"  {i+1}. [{mem['metadata'].get('type', 'unknown')}] {mem['content']}")


def main():
    # Check Redis connection
    try:
        r.ping()
        print("Connected to Redis successfully")
    except Exception as e:
        print(f"Redis connection error: {e}")
        return
        
    # Get all key types first to diagnose issues
    key_types = {}
    all_keys = r.keys("*")
    print(f"Total Redis keys: {len(all_keys)}")
    
    for key in all_keys[:20]:  # Sample the first 20 keys
        try:
            key_types[r.type(key)] = key_types.get(r.type(key), 0) + 1
        except:
            pass
    
    print("Redis key types:")
    for key_type, count in key_types.items():
        print(f"  {key_type}: {count}")
    
    # Get memory keys specifically
    memory_keys = r.keys("memory:*")
    print(f"\nMemory keys: {len(memory_keys)}")
    
    # Now proceed with session analysis
    sessions = get_unique_sessions()
    print(f"\nFound {len(sessions)} unique sessions in Redis")
    
    for session in sessions:
        analyze_session(session)


if __name__ == "__main__":
    main()
