"""
Research Agent using LangGraph with Azentiq Memory Manager integration.

This module implements a research agent that can search for information,
extract entities and relationships, and build a knowledge graph over time.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

# LangChain and LangGraph imports
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolExecutor, ToolInvocation
except ImportError:
    raise ImportError(
        "LangGraph not installed. Please install with: pip install langgraph"
    )

# Azentiq Memory Manager imports
from azentiq_memory_manager import MemoryManager
from azentiq_memory_manager.tiers import MemoryTier
from azentiq_memory_manager.progression import ProgressionEngine

# Local imports
from .graph_memory_adapter import AzentiqGraphMemory

logger = logging.getLogger(__name__)

# Mock tools for demo purposes - replace with real implementations
@tool
def search_tool(query: str) -> str:
    """
    Search for information on a given query.
    
    Args:
        query: The search query
        
    Returns:
        Search results as text
    """
    return f"Mock search results for '{query}': Information about the topic including entities like 'Python', 'LangGraph', 'Memory Management', etc."

@tool
def extract_entities_tool(text: str) -> List[Dict[str, Any]]:
    """
    Extract entities from text.
    
    Args:
        text: Text to extract entities from
        
    Returns:
        List of extracted entities with their types
    """
    # Mock implementation - in production, use a real NER model
    return [
        {"entity": "Python", "type": "language", "confidence": 0.9},
        {"entity": "LangGraph", "type": "library", "confidence": 0.95},
        {"entity": "Memory Management", "type": "concept", "confidence": 0.8}
    ]

@tool
def summarize_tool(documents: List[str]) -> str:
    """
    Summarize a list of documents.
    
    Args:
        documents: List of documents to summarize
        
    Returns:
        Summary text
    """
    return f"Summary of {len(documents)} documents: The documents discuss various aspects of Python programming, LangGraph, and memory management techniques."

class ResearchAgent:
    """
    Research agent using LangGraph with Azentiq Memory Manager.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", openai_api_key: Optional[str] = None):
        """
        Initialize the research agent.
        
        Args:
            redis_url: Redis connection URL
            openai_api_key: OpenAI API key (defaults to environment variable)
        """
        # Set up OpenAI API key
        self.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set it via the openai_api_key parameter or OPENAI_API_KEY environment variable."
            )
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(redis_url=redis_url)
        
        # Initialize progression engine with research template
        self.progression_engine = ProgressionEngine(
            memory_manager=self.memory_manager,
            template_name="langgraph_research"
        )
        
        # Initialize graph memory
        self.graph_memory = AzentiqGraphMemory(
            memory_manager=self.memory_manager,
            progression_engine=self.progression_engine
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=self.api_key
        )
        
        # Initialize tools
        self.tools = [search_tool, extract_entities_tool, summarize_tool]
        self.tool_executor = ToolExecutor(self.tools)
        
        # Build the graph
        self.graph = self.build_graph()
        
        logger.info("Research agent initialized")
    
    def build_graph(self) -> StateGraph:
        """
        Build the research agent graph.
        
        Returns:
            Compiled StateGraph
        """
        builder = StateGraph()
        
        # Define state
        builder.add_node("researcher", self.researcher)
        builder.add_node("search", self.search)
        builder.add_node("process_results", self.process_results)
        builder.add_node("extract_knowledge", self.extract_knowledge)
        builder.add_node("respond", self.respond)
        
        # Define edges
        builder.add_edge("researcher", "search")
        builder.add_edge("search", "process_results")
        builder.add_edge("process_results", "extract_knowledge")
        builder.add_edge("extract_knowledge", "respond")
        builder.add_edge("respond", END)
        
        # Set entry point
        builder.set_entry_point("researcher")
        
        # Compile graph with memory
        return builder.compile(checkpointer=self.graph_memory)
    
    def researcher(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        First step: Understand the user query and formulate research plan.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state
        """
        # Get user query
        query = state.get("query", "")
        
        # Store query in memory
        self.memory_manager.add_memory(
            content=query,
            metadata={
                "type": "research_query",
                "timestamp": datetime.now().isoformat(),
                "session_id": self.graph_memory.session_id
            },
            importance=0.8,
            tier=MemoryTier.SHORT_TERM,
            session_id=self.graph_memory.session_id
        )
        
        # Formulate research plan
        plan_response = self.llm.invoke([
            HumanMessage(content=f"Create a research plan for the query: {query}. "
                                 f"Break it down into key topics to investigate.")
        ])
        
        # Store the plan in state
        return {
            "query": query,
            "research_plan": plan_response.content,
            "search_topics": self.extract_search_topics(plan_response.content),
            "results": [],
            "entities": [],
            "relationships": []
        }
    
    def extract_search_topics(self, plan: str) -> List[str]:
        """
        Extract search topics from research plan.
        
        Args:
            plan: Research plan text
            
        Returns:
            List of search topics
        """
        # Simple mock implementation - in production use LLM
        import re
        topics = re.findall(r'[•\-*] ([^\n]+)', plan)
        return topics[:3] if topics else [plan.split('\n')[0]]
    
    def search(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for information on the topics.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state
        """
        search_topics = state.get("search_topics", [])
        results = []
        
        for topic in search_topics:
            # Execute search tool
            result = self.tool_executor.invoke(
                {"tool": "search_tool", "tool_input": topic}
            )
            
            # Store result in memory
            memory_id = self.graph_memory.add_node_output(
                node_name="search",
                output=result,
                importance=0.7
            )
            
            results.append({
                "topic": topic,
                "result": result,
                "memory_id": memory_id
            })
        
        # Update state
        return {
            **state,
            "results": results
        }
    
    def process_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process search results.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state
        """
        results = state.get("results", [])
        processed_results = []
        
        for result_item in results:
            # Extract entities from result
            entities = self.tool_executor.invoke({
                "tool": "extract_entities_tool",
                "tool_input": result_item["result"]
            })
            
            # Store node output
            self.graph_memory.add_node_output(
                node_name="process_results",
                output={"topic": result_item["topic"], "entities": entities},
                importance=0.7
            )
            
            processed_results.append({
                "topic": result_item["topic"],
                "entities": entities
            })
        
        # Update state
        return {
            **state,
            "processed_results": processed_results
        }
    
    def extract_knowledge(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities and relationships from processed results.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state
        """
        processed_results = state.get("processed_results", [])
        entities = []
        relationships = []
        
        # Extract entities
        for result in processed_results:
            for entity_data in result["entities"]:
                entity = entity_data["entity"]
                entity_type = entity_data["type"]
                
                # Store entity in memory
                entity_id = self.graph_memory.add_entity(
                    entity=entity,
                    entity_type=entity_type,
                    data=entity_data
                )
                
                entities.append({
                    "id": entity_id,
                    "entity": entity,
                    "type": entity_type
                })
        
        # Generate relationships (simple mock implementation)
        if len(entities) >= 2:
            for i in range(len(entities) - 1):
                # Create a relationship between adjacent entities
                rel_id = self.graph_memory.add_relationship(
                    source_entity=entities[i]["entity"],
                    target_entity=entities[i+1]["entity"],
                    relationship_type="related_to",
                    data={"confidence": 0.7}
                )
                
                relationships.append({
                    "id": rel_id,
                    "source": entities[i]["entity"],
                    "target": entities[i+1]["entity"],
                    "type": "related_to"
                })
        
        # Update state
        return {
            **state,
            "extracted_entities": entities,
            "extracted_relationships": relationships
        }
    
    def respond(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate response to the user.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with response
        """
        query = state.get("query", "")
        results = state.get("results", [])
        entities = state.get("extracted_entities", [])
        relationships = state.get("extracted_relationships", [])
        
        # Collect result texts
        result_texts = [r["result"] for r in results]
        
        # Generate summary if we have results
        summary = ""
        if result_texts:
            summary = self.tool_executor.invoke({
                "tool": "summarize_tool",
                "tool_input": result_texts
            })
        
        # Store summary in memory
        if summary:
            self.memory_manager.add_memory(
                content=summary,
                metadata={
                    "type": "research_summary",
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self.graph_memory.session_id
                },
                importance=0.8,
                tier=MemoryTier.WORKING,
                session_id=self.graph_memory.session_id
            )
        
        # Generate response
        response_content = f"Research results for '{query}':\n\n{summary}\n\n"
        response_content += f"Discovered {len(entities)} key entities and {len(relationships)} relationships."
        
        # Update state
        return {
            **state,
            "summary": summary,
            "response": response_content
        }
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the research agent on a query.
        
        Args:
            query: Research query
            
        Returns:
            The final state with research results
        """
        logger.info(f"Running research agent with query: {query}")
        
        # Execute the graph
        result = self.graph.invoke({
            "query": query
        })
        
        logger.info("Research agent execution completed")
        return result
    
    def get_knowledge_graph(self) -> Dict[str, Any]:
        """
        Get the current knowledge graph.
        
        Returns:
            Knowledge graph data
        """
        return self.graph_memory.get_knowledge_graph()
