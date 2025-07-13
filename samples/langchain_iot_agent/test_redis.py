#!/usr/bin/env python3
"""
Script to test Redis connectivity and populate with sample data for visualization.
"""

import os
import sys
import json
import uuid
import datetime
from typing import Dict, Any, Optional

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.memory_manager import MemoryManager, MemoryTier
from core.interfaces import Memory

def main():
    # Initialize a memory manager with Redis
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    memory_manager = MemoryManager(redis_url=redis_url)
    
    # Generate a unique session ID for this test
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    # Create test data for each memory tier
    
    # SHORT-TERM MEMORY TIER (Session Memory)
    # Telemetry data would be stored here
    for i in range(5):
        reading_value = 75 + (i * 5)  # simulate increasing temperature
        telemetry = {
            "device_id": "temp_sensor_1",
            "timestamp": datetime.datetime.now().isoformat(),
            "reading_type": "temperature",
            "value": reading_value,
            "unit": "F"
        }
        
        # Create a memory object
        memory = Memory(
            memory_id=f"telemetry_{i}",
            content=json.dumps(telemetry),
            metadata={
                "type": "telemetry",
                "device_id": "temp_sensor_1",
                "reading_type": "temperature",
                "session_id": session_id,
                "source": "device_sensor"
            },
            importance=0.3  # Low importance for raw telemetry
        )
        
        # Store in short-term memory tier
        memory_manager.add_memory(
            content=memory.content,
            metadata=memory.metadata,
            importance=memory.importance,
            memory_id=memory.memory_id,
            tier=MemoryTier.SHORT_TERM,
            session_id=session_id
        )
        print(f"Stored telemetry reading {i}: {reading_value}°F in short-term memory")
        
    # WORKING MEMORY TIER (Conversational Memory)
    # Anomalies and insights would be stored here
    anomaly = {
        "device_id": "temp_sensor_1",
        "timestamp": datetime.datetime.now().isoformat(),
        "reading_type": "temperature",
        "anomaly_type": "threshold_breach",
        "value": 95,
        "threshold": 90,
        "unit": "F",
        "description": "Temperature exceeded normal operating threshold"
    }
    
    memory = Memory(
        memory_id="anomaly_1",
        content=json.dumps(anomaly),
        metadata={
            "type": "anomaly",
            "device_id": "temp_sensor_1",
            "anomaly_type": "threshold_breach",
            "session_id": session_id,
            "source": "anomaly_detection"
        },
        importance=0.8  # High importance for anomalies
    )
    
    # Store in working memory tier
    memory_manager.add_memory(
        content=memory.content,
        metadata=memory.metadata,
        importance=memory.importance,
        memory_id=memory.memory_id,
        tier=MemoryTier.WORKING,
        session_id=session_id
    )
    print("Stored anomaly in working memory")
    
    # AI-generated insight
    insight = {
        "timestamp": datetime.datetime.now().isoformat(),
        "insight_type": "trend",
        "device_id": "temp_sensor_1",
        "description": "Temperature is rising steadily at approximately 5°F per reading, which may indicate a cooling system malfunction.",
        "recommendation": "Check cooling system components and airflow around the sensor."
    }
    
    memory = Memory(
        memory_id="insight_1",
        content=json.dumps(insight),
        metadata={
            "type": "insight",
            "device_id": "temp_sensor_1",
            "insight_type": "trend",
            "session_id": session_id,
            "source": "ai_analysis"
        },
        importance=0.9  # Very high importance for insights
    )
    
    # Store in working memory tier
    memory_manager.add_memory(
        content=memory.content,
        metadata=memory.metadata,
        importance=memory.importance,
        memory_id=memory.memory_id,
        tier=MemoryTier.WORKING,
        session_id=session_id
    )
    print("Stored AI insight in working memory")
    
    # LONG-TERM MEMORY TIER (Not implemented in MVP, but demo structure)
    # Historical summary would go here in future implementation
    # Check if LONG_TERM is in the MemoryTier enum
    if MemoryTier.LONG_TERM.value == "long_term":
        summary = {
            "device_id": "temp_sensor_1",
            "period": "last_24_hours",
            "metrics": {
                "avg_temperature": 82.5,
                "max_temperature": 95,
                "min_temperature": 70,
                "anomalies_detected": 1
            },
            "summary": "The device experienced one temperature threshold breach. Overall temperature trend shows gradual increase throughout monitoring period."
        }
        
        memory = Memory(
            memory_id="daily_summary",
            content=json.dumps(summary),
            metadata={
                "type": "summary",
                "device_id": "temp_sensor_1",
                "period": "daily",
                "session_id": session_id,
                "source": "automated_summary"
            },
            importance=0.7
        )
        
        # Store in long-term memory tier
        memory_manager.add_memory(
            content=memory.content,
            metadata=memory.metadata,
            importance=memory.importance,
            memory_id=memory.memory_id,
            tier=MemoryTier.LONG_TERM,
            session_id=session_id
        )
        print("Stored daily summary in long-term memory")
    else:
        print("Long-term memory not implemented in MVP")
    
    print("\nData successfully stored in Redis under session ID:", session_id)
    print("You can now view the data in Redis Commander")

if __name__ == "__main__":
    main()
