"""
IoT Monitoring Agent using LangChain and Azentiq Memory Manager.

This agent processes telemetry data from IoT devices, detects anomalies,
and can answer natural language queries about the device history.
"""
import sys
import os
import sys
import uuid
import json
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any, Optional, Union, Tuple
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('iot_agent')

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import from LangChain packages
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from core.interfaces import MemoryTier

from .memory_adapter import AzentiqMemory, IoTMemoryManager

class IoTAgent:
    """IoT monitoring agent using LangChain and Azentiq Memory Manager."""
    
    def __init__(
        self, 
        session_id: str,
        openai_api_key: str,
        redis_url: str = "redis://localhost:6379/0",
        model_name: str = "gpt-4"
    ):
        """Initialize the IoT agent with memory manager and LLM.
        
        Args:
            session_id: Unique identifier for this session
            openai_api_key: API key for OpenAI
            redis_url: URL to Redis instance
            model_name: Name of the OpenAI model to use
        """
        # Store parameters
        self.session_id = session_id
        
        try:
            # Initialize conversation memory adapter
            self.memory = AzentiqMemory(
                session_id=session_id,
                redis_url=redis_url,
                memory_key="history",  # Match the prompt template's variable
                input_key="input",
                output_key="response",  # ConversationChain uses 'response' as the default output key
                return_messages=True
            )
            
            # Initialize IoT-specific memory manager
            self.iot_memory = IoTMemoryManager(session_id=session_id, redis_url=redis_url)
            
            # Initialize the LLM
            self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name=model_name)
            
            # Create a conversation chain
            prompt = PromptTemplate(
                input_variables=["history", "input"],
                template="""You are an AI assistant monitoring IoT devices. You have access to device telemetry, anomalies, and insights.
                
                {history}
                Human: {input}
                AI: """
            )
            
            self.chain = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                prompt=prompt,
                verbose=True
            )
            
            print(f"Created agent with session ID: {session_id}")
            
        except Exception as e:
            print(f"Error initializing IoT agent: {e}")
            raise
    
    def set_device_thresholds(self, device_id: str, thresholds: Dict[str, Dict[str, float]]):
        """Set thresholds for anomaly detection for a device.
        
        Args:
            device_id: Identifier for the device
            thresholds: Dict of metrics with min/max thresholds, e.g.,
                {"temperature": {"min": 10.0, "max": 30.0},
                 "humidity": {"min": 20.0, "max": 80.0}}
        """
        # Store thresholds in memory with appropriate metadata
        self.iot_memory.memory_manager.add_memory(
            content=str(thresholds),
            metadata={
                "type": "thresholds",
                "device_id": device_id,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.7,
            tier=MemoryTier.WORKING,
            session_id=self.session_id
        )
    
    def process_telemetry(self, device_id: str, metrics: Dict[str, float]) -> List[Dict]:
        """Process incoming telemetry data from an IoT device.
        
        Args:
            device_id: ID of the IoT device
            metrics: Dictionary of metric readings
            
        Returns:
            List of detected anomalies, if any
        """
        logger.info(f"Processing telemetry for device {device_id}: {metrics}")
        
        # Store telemetry in memory
        self._store_telemetry(device_id, metrics)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(device_id, metrics)
        if anomalies:
            logger.info(f"Detected {len(anomalies)} anomalies for device {device_id}")
        
        # Store any detected anomalies
        for anomaly in anomalies:
            self._store_anomaly(
                device_id=device_id,
                anomaly_type=anomaly["type"],
                description=anomaly["description"],
                metrics=metrics
            )
            
            # Generate and store insight about this anomaly
            if random.random() > 0.5:  # Only generate insights sometimes to avoid spamming
                logger.info(f"Generating insight for anomaly {anomaly['type']} on device {device_id}")
                insight = self._generate_anomaly_insight(device_id, anomalies)
                # Store insight in memory adapter
                self._store_insight(device_id, "anomaly_insight", insight)
        
        # Periodically detect trends (every 5th reading)
        if random.random() > 0.8:
            logger.info(f"Performing trend analysis for device {device_id}")
            trends = self._detect_trends(device_id)
            if trends and "trend_text" in trends:
                self._store_insight(device_id, "trend_analysis", trends["trend_text"])
            
        return anomalies
    
    def _get_threshold_for_metric(self, device_id: str, metric_name: str) -> Dict[str, float]:
        """Get thresholds for a specific device and metric.
        
        Args:
            device_id: ID of the device
            metric_name: Name of the metric
            
        Returns:
            Dictionary with min and max thresholds
        """
        # Try to get thresholds from Redis
        memories = self.iot_memory.memory_manager.search_by_metadata(
            query={"type": "thresholds", "device_id": device_id, "session_id": self.session_id}
        )
        
        # Parse the thresholds from the memory content
        if memories:
            # Get the most recent threshold configuration
            memory = memories[0]
            try:
                # The content is a string representation of a dictionary
                import ast
                thresholds_dict = ast.literal_eval(memory.content)
                if metric_name in thresholds_dict:
                    return thresholds_dict[metric_name]
            except (ValueError, SyntaxError):
                pass
                
        # Return default thresholds if not found
        return {"min": 0.0, "max": 100.0}  # Default thresholds
    
    def _detect_anomalies(self, device_id: str, metrics: Dict[str, float]) -> List[Dict]:
        """Detect anomalies in device telemetry.
        
        Args:
            device_id: ID of the IoT device
            metrics: Dictionary of metric readings
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check against thresholds
        for metric_name, value in metrics.items():
            # Get thresholds for this metric
            thresholds = self._get_threshold_for_metric(device_id, metric_name)
            
            # Try to convert the value to a float for comparison
            try:
                float_value = float(value)
                
                # Check if below minimum threshold
                if "min" in thresholds and float_value < float(thresholds["min"]):
                    anomalies.append({
                        "type": f"low_{metric_name}",
                        "description": f"{metric_name.capitalize()} reading of {value} is below minimum threshold of {thresholds['min']}",
                        "severity": "warning"
                    })
                
                # Check if above maximum threshold
                if "max" in thresholds and float_value > float(thresholds["max"]):
                    anomalies.append({
                        "type": f"high_{metric_name}",
                        "description": f"{metric_name.capitalize()} reading of {value} is above maximum threshold of {thresholds['max']}",
                        "severity": "warning"
                    })
            except (ValueError, TypeError):
                # If we can't convert the value to a float, skip this metric
                pass
        
        return anomalies
    
    def _detect_trends(self, device_id: str) -> Optional[str]:
        """Detect trends in device history.
        
        Args:
            device_id: ID of the IoT device
            
        Returns:
            String description of detected trend, if any
        """
        # Retrieve recent telemetry for this device
        telemetry_memories = self.iot_memory.memory_manager.search_by_metadata(
            query={"device_id": device_id, "type": "telemetry", "session_id": self.session_id},
            tier=MemoryTier.SHORT_TERM,
            limit=10
        )
        
        # Convert to a more usable format
        history = []
        for memory in telemetry_memories:
            try:
                metrics = json.loads(memory.content)
                history.append({
                    "timestamp": memory.metadata.get("timestamp"),
                    "metrics": metrics
                })
            except json.JSONDecodeError:
                # Skip this entry if we can't parse the content
                continue
        
        trends = []
        
        # Get list of metrics in the latest reading
        latest_metrics = list(history[-1]["metrics"].keys())
        
        for metric_name in latest_metrics:
            values = [h["metrics"].get(metric_name, 0) for h in history]
            
            # Calculate simple trend
            if all(values[i] < values[i+1] for i in range(len(values)-1)):
                trends.append(f"{metric_name.capitalize()} has been steadily increasing")
            elif all(values[i] > values[i+1] for i in range(len(values)-1)):
                trends.append(f"{metric_name.capitalize()} has been steadily decreasing")
            
            # Check for oscillation
            ups = sum(1 for i in range(len(values)-1) if values[i] < values[i+1])
            downs = sum(1 for i in range(len(values)-1) if values[i] > values[i+1])
            
            if ups >= 2 and downs >= 2:
                trends.append(f"{metric_name.capitalize()} shows oscillating pattern")
        
        if trends:
            return "Trend analysis for device " + device_id + ": " + "; ".join(trends)
        
        return None
    
    def _generate_anomaly_insight(self, device_id: str, anomalies: List[Dict]) -> str:
        """Generate insights about anomalies using LLM."""
        # Prepare anomaly history
        anomaly_list = "\n".join([f"- {a['type']}: {a['description']}" for a in anomalies])
        
        # Get historical context
        device_history = self.iot_memory.get_device_history(device_id)
        
        # Create system message
        system_message = SystemMessage(content=f"""
        You are an IoT monitoring assistant analyzing sensor data.
        Generate insights about anomalies detected for device {device_id}.
        Consider historical context and identify potential causes and recommendations.
        Be concise and factual, focusing on operational impacts.
        """)
        
        # Create human message with anomaly details and history
        human_message = HumanMessage(content=f"""
        Analyze these anomalies for device {device_id}:
        {anomaly_list}
        
        Historical context:
        {device_history}
        """)
        
        # Log request to GPT
        logger.info(f"=== GPT REQUEST (ANOMALY INSIGHT) ===\nDevice: {device_id}\nAnomalies: {len(anomalies)}\nSystem prompt length: {len(system_message.content)}\nHuman message length: {len(human_message.content)}")
        
        # Send to LLM for analysis
        start_time = time.time()
        response = self.llm.invoke([system_message, human_message])
        processing_time = time.time() - start_time
        
        # Extract the string content from AIMessage
        if isinstance(response, AIMessage):
            insight = response.content
        else:
            insight = str(response)
        
        # Log response from GPT
        logger.info(f"=== GPT RESPONSE (ANOMALY INSIGHT) ===\nProcessing time: {processing_time:.2f}s\nResponse length: {len(insight)}\nPreview: {insight[:100]}...")
            
        return insight
    
    def query(self, query_text: str) -> str:
        """Process a natural language query about device status."""
        # Get relevant context from memory
        logger.info(f"Processing query: {query_text}")
        context = self.iot_memory.get_relevant_context(query_text)
        
        # Add context to the query
        if context:
            enriched_query = f"{query_text}\n\nContext:\n{context}"
            logger.info(f"Enriched query with {len(context)} chars of context")
        else:
            enriched_query = query_text
            logger.info("No additional context found for query")
            
        # Process with conversation chain
        logger.info("Sending query to LLM...")
        start_time = time.time()
        response = self.chain.invoke({"input": enriched_query})
        processing_time = time.time() - start_time
        logger.info(f"Received LLM response in {processing_time:.2f}s: {response['response'][:100]}...")
        return response["response"]
    
    def _store_telemetry(self, device_id: str, metrics: Dict[str, Any]) -> str:
        """Store device telemetry in Redis short-term memory.
        
        Args:
            device_id: Identifier for the device
            metrics: Dict of metric name to value
            
        Returns:
            memory_id: ID of the stored memory
        """
        return self.iot_memory.memory_manager.add_memory(
            content=json.dumps(metrics),
            metadata={
                "type": "telemetry",
                "device_id": device_id,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.5,
            tier=MemoryTier.SHORT_TERM,
            session_id=self.session_id
        )
        
    def _store_anomaly(self, device_id: str, anomaly_type: str, description: str, metrics: Dict[str, Any]) -> str:
        """Store device anomaly in Redis working memory.
        
        Args:
            device_id: Identifier for the device
            anomaly_type: Type of anomaly detected
            description: Human-readable description
            metrics: Metrics related to the anomaly
            
        Returns:
            memory_id: ID of the stored memory
        """
        # Extract relevant metrics for the anomaly storage
        metric_name = list(metrics.keys())[0] if metrics else "unknown"
        metric_value = metrics.get(metric_name) if metrics else None
        threshold = self._get_threshold_for_metric(device_id, metric_name)
        
        return self.iot_memory.memory_manager.add_memory(
            content=json.dumps({
                "anomaly_type": anomaly_type,
                "description": description,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "threshold": threshold
            }),
            metadata={
                "type": "anomaly",
                "device_id": device_id,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.9,
            tier=MemoryTier.WORKING,
            session_id=self.session_id
        )
        
    def _store_insight(self, device_id: str, insight_type: str, content: str) -> str:
        """Store device insight in Redis working memory.
        
        Args:
            device_id: Identifier for the device
            insight_type: Type of insight (trend, prediction, etc.)
            content: Content of the insight
            
        Returns:
            memory_id: ID of the stored memory
        """
        return self.iot_memory.memory_manager.add_memory(
            content=content,
            metadata={
                "type": insight_type,
                "device_id": device_id,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.8,
            tier=MemoryTier.WORKING,
            session_id=self.session_id
        )
        
    def _retrieve_relevant_context(self, query: str) -> str:
        """Retrieve relevant context for answering a query.
        
        Args:
            query: User's query
            
        Returns:
            context: Relevant context from memory
        """
        # Get recent telemetry, anomalies and insights from memory
        # First, get device mentions from query
        # This is a simplified implementation - in a real system, we would use
        # more sophisticated NLP to extract device references
        context = []
        
        # Check for device ID mentions
        for device_id in ["device_1", "device_2", "device_3", "thermostat", "server"]:
            if device_id in query.lower():
                # For each device mentioned, get its recent history
                memories = self.iot_memory.memory_manager.search_by_metadata(
                    query={"device_id": device_id, "session_id": self.session_id},
                    limit=10
                )
                
                if memories:
                    context.append(f"\n--- {device_id.upper()} HISTORY ---")
                    for memory in memories:
                        memory_type = memory.metadata.get("type", "unknown")
                        timestamp = memory.metadata.get("timestamp", "unknown time")
                        context.append(f"[{memory_type} - {timestamp}] {memory.content}")
        
        # If no specific device was mentioned, get recent memories of all types
        if not context:
            # Get recent memories from all devices
            memories = self.iot_memory.memory_manager.search_by_metadata(
                query={"session_id": self.session_id},  # Match all memories for this session
                limit=15
            )
            
            # Sort by timestamp (most recent first)
            memories.sort(key=lambda m: m.metadata.get("timestamp", ""), reverse=True)
            
            if memories:
                context.append("\n--- RECENT DEVICE ACTIVITY ---")
                for memory in memories[:10]:  # Limit to 10 most recent items
                    device_id = memory.metadata.get("device_id", "unknown device")
                    memory_type = memory.metadata.get("type", "unknown")
                    timestamp = memory.metadata.get("timestamp", "unknown time")
                    context.append(f"[{device_id} - {memory_type} - {timestamp}] {memory.content}")
        
        # Return the context as string
        return "\n".join(context)


# Utility function to generate simulated telemetry data
def generate_simulated_telemetry(device_id: str, baseline: Dict[str, float], 
                               variance: Dict[str, float], anomaly_chance: float = 0.1) -> Dict[str, float]:
    """Generate simulated telemetry data for testing.
    
    Args:
        device_id: ID of the IoT device
        baseline: Baseline values for each metric
        variance: Maximum variance for each metric
        anomaly_chance: Probability of generating an anomaly
        
    Returns:
        Dictionary of simulated metric readings
    """
    metrics = {}
    
    # Decide if this reading will be an anomaly
    is_anomaly = random.random() < anomaly_chance
    
    for metric, base_value in baseline.items():
        # Calculate normal variation
        variation = random.uniform(-variance[metric], variance[metric])
        
        # If anomaly, occasionally make larger variations
        if is_anomaly and random.random() < 0.3:
            variation *= 5  # Much larger variation for anomalies
            
        metrics[metric] = round(base_value + variation, 2)
    
    return metrics
