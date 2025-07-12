#!/usr/bin/env python
import json
import sys
from typing import Optional, Dict, Any, List

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from enum import Enum

from core.memory_manager import MemoryManager, MemoryTier
from storage.redis_store import RedisStore

app = typer.Typer(help="Memory Manager CLI - Tiered memory for AI agents")
console = Console()

# Global memory manager instance
memory_manager = None


class CLIMemoryTier(str, Enum):
    """CLI-friendly memory tier enum."""
    SHORT_TERM = "short_term"
    WORKING = "working"
    ALL = "all"


def map_cli_tier_to_memory_tier(tier: CLIMemoryTier) -> Optional[MemoryTier]:
    """Map CLI tier to internal MemoryTier enum."""
    if tier == CLIMemoryTier.SHORT_TERM:
        return MemoryTier.SHORT_TERM
    elif tier == CLIMemoryTier.WORKING:
        return MemoryTier.WORKING
    # ALL maps to None which means search across all tiers
    return None


def get_memory_manager() -> MemoryManager:
    """Create or return the global memory manager instance."""
    global memory_manager
    
    if memory_manager is None:
        # Use the new MemoryManager constructor
        memory_manager = MemoryManager(
            redis_url="redis://localhost:6379/0",
            short_term_ttl=30 * 60,  # 30 minutes default
            model_token_limit=8192
        )
    
    return memory_manager


@app.command("add")
def add_memory(
    content: str = typer.Argument(..., help="Memory content"),
    metadata: str = typer.Option("{}", help="JSON metadata for the memory"),
    importance: float = typer.Option(0.0, help="Importance score (0-1)"),
    memory_id: Optional[str] = typer.Option(None, help="Custom memory ID (optional)"),
    tier: CLIMemoryTier = typer.Option(CLIMemoryTier.WORKING, help="Memory tier (short_term, working, all)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID for the memory")
):
    """Add a new memory to the specified tier."""
    try:
        # Parse metadata if provided
        metadata_dict = json.loads(metadata) if metadata else {}
        
        # Set memory tier
        memory_tier = map_cli_tier_to_memory_tier(tier)
        if tier == CLIMemoryTier.ALL:
            # Default to working memory if 'all' is specified for add operation
            memory_tier = MemoryTier.WORKING
            
        # For short-term memory, ensure type is set
        if memory_tier == MemoryTier.SHORT_TERM and "type" not in metadata_dict:
            metadata_dict["type"] = "conversation_turn"
            
        # For working memory, ensure type is set
        if memory_tier == MemoryTier.WORKING and "type" not in metadata_dict:
            metadata_dict["type"] = "session_context"
        
        # Add session_id to metadata if provided
        if session_id and "session_id" not in metadata_dict:
            metadata_dict["session_id"] = session_id
        
        # Add memory
        memory_id = get_memory_manager().add_memory(
            content=content,
            metadata=metadata_dict,
            importance=importance,
            memory_id=memory_id,
            tier=memory_tier,
            session_id=session_id
        )
        
        # Show memory tier in output
        tier_name = "short-term" if memory_tier == MemoryTier.SHORT_TERM else "working"
        console.print(f"✅ Memory added to [bold blue]{tier_name}[/bold blue] tier with ID: [bold green]{memory_id}[/bold green]")
        
        # Show TTL for short-term memory
        if memory_tier == MemoryTier.SHORT_TERM:
            ttl_minutes = get_memory_manager().short_term_ttl / 60
            console.print(f"   Will expire in [yellow]{ttl_minutes:.0f} minutes[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        sys.exit(1)


@app.command("get")
def get_memory(
    memory_id: str,
    tier: CLIMemoryTier = typer.Option(CLIMemoryTier.ALL, help="Memory tier (short_term, working, all)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to help locate the memory")
):
    """Get a memory by ID from the specified tier."""
    try:
        memory_tier = map_cli_tier_to_memory_tier(tier)
        memory = get_memory_manager().get_memory(memory_id, tier=memory_tier, session_id=session_id)
        
        if memory:
            # Determine which tier the memory belongs to based on metadata
            tier_name = "unknown"
            if "type" in memory.metadata:
                if memory.metadata["type"] == "conversation_turn":
                    tier_name = "short-term"
                elif memory.metadata["type"] == "session_context":
                    tier_name = "working"
            
            # Display memory with tier info
            console.print(f"[bold]Memory ID:[/bold] {memory.memory_id}")
            console.print(f"[bold]Tier:[/bold] [blue]{tier_name}[/blue]")
            console.print(f"[bold]Content:[/bold] {memory.content}")
            console.print(f"[bold]Importance:[/bold] {memory.importance}")
            console.print(f"[bold]Created:[/bold] {memory.created_at}")
            console.print(f"[bold]Last Accessed:[/bold] {memory.last_accessed_at}")
            
            # Format metadata for display
            formatted_metadata = json.dumps(memory.metadata, indent=2)
            console.print(f"[bold]Metadata:[/bold]\n{formatted_metadata}")
            
            # Show TTL info for short-term memory
            if tier_name == "short-term":
                console.print("[yellow]Note: This memory will auto-expire based on TTL settings[/yellow]")
        else:
            if tier == CLIMemoryTier.ALL:
                console.print(f"[bold yellow]Memory not found:[/bold yellow] {memory_id}", file=sys.stderr)
            else:
                console.print(f"[bold yellow]Memory not found in {tier.value} tier:[/bold yellow] {memory_id}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        sys.exit(1)


@app.command("list")
def list_memories(
    limit: int = typer.Option(10, help="Maximum number of memories to return"),
    offset: int = typer.Option(0, help="Pagination offset"),
    tier: CLIMemoryTier = typer.Option(CLIMemoryTier.ALL, help="Memory tier to list (short_term, working, all)"),
    session_id: Optional[str] = typer.Option(None, help="Filter by session ID")
):
    """List memories from specified tier with pagination."""
    try:
        memory_tier = map_cli_tier_to_memory_tier(tier)
        memories = get_memory_manager().list_memories(
            tier=memory_tier, 
            session_id=session_id,
            limit=limit, 
            offset=offset
        )
        
        if not memories:
            if tier == CLIMemoryTier.ALL:
                console.print("No memories found.")
            else:
                console.print(f"No memories found in {tier.value} tier.")
            return
        
        # Create a table
        title = "All Memories" if tier == CLIMemoryTier.ALL else f"{tier.value.capitalize()} Tier Memories"
        if session_id:
            title += f" (Session: {session_id})"
            
        table = Table(title=title, box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Tier", style="blue")
        table.add_column("Content", style="green")
        table.add_column("Importance", style="yellow")
        table.add_column("Created", style="magenta")
        
        for memory in memories:
            # Determine memory tier
            memory_tier_name = "unknown"
            if "type" in memory.metadata:
                if memory.metadata["type"] == "conversation_turn":
                    memory_tier_name = "short-term"
                elif memory.metadata["type"] == "session_context":
                    memory_tier_name = "working"
            
            # Truncate content if too long
            content = memory.content
            if len(content) > 40:
                content = content[:37] + "..."
                
            table.add_row(
                memory.memory_id,
                memory_tier_name,
                content,
                str(memory.importance),
                str(memory.created_at)
            )
            
        console.print(table)
        console.print(f"Showing {len(memories)} memories (offset: {offset})")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        sys.exit(1)


@app.command("search")
def search_memories(
    query: str = typer.Argument(..., help="JSON metadata query to search for"),
    limit: int = typer.Option(10, help="Maximum number of results"),
    tier: CLIMemoryTier = typer.Option(CLIMemoryTier.ALL, help="Memory tier to search (short_term, working, all)"),
    session_id: Optional[str] = typer.Option(None, help="Filter by session ID")
):
    """Search memories by metadata within the specified tier."""
    try:
        # Parse the query JSON
        query_dict = json.loads(query)
        
        # If session ID is provided but not in query, add it
        if session_id and "session_id" not in query_dict:
            query_dict["session_id"] = session_id
        
        # Get memory tier
        memory_tier = map_cli_tier_to_memory_tier(tier)
        
        # Search memories
        memories = get_memory_manager().search_by_metadata(
            query_dict, 
            tier=memory_tier,
            session_id=session_id, 
            limit=limit
        )
        
        if not memories:
            if tier == CLIMemoryTier.ALL:
                console.print("No matching memories found.")
            else:
                console.print(f"No matching memories found in {tier.value} tier.")
            return
        
        # Create table for display
        title = f"Search Results: {query}"
        if tier != CLIMemoryTier.ALL:
            title += f" in {tier.value} tier"
            
        table = Table(title=title, box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Tier", style="blue")
        table.add_column("Content", style="green")
        table.add_column("Importance", style="yellow")
        table.add_column("Created", style="magenta")
        
        for memory in memories:
            # Determine memory tier
            memory_tier_name = "unknown"
            if "type" in memory.metadata:
                if memory.metadata["type"] == "conversation_turn":
                    memory_tier_name = "short-term"
                elif memory.metadata["type"] == "session_context":
                    memory_tier_name = "working"
                    
            # Truncate content if too long
            content = memory.content
            if len(content) > 40:
                content = content[:37] + "..."
                
            table.add_row(
                memory.memory_id,
                memory_tier_name,
                content,
                str(memory.importance),
                str(memory.created_at)
            )
        
        console.print(table)
        console.print(f"Found {len(memories)} matching memories")
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/bold red] Invalid JSON query format", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        sys.exit(1)


@app.command("update")
def update_memory(
    memory_id: str = typer.Argument(..., help="ID of the memory to update"),
    content: Optional[str] = typer.Option(None, help="New content for the memory"),
    metadata: Optional[str] = typer.Option(None, help="JSON metadata to update or add"),
    importance: Optional[float] = typer.Option(None, help="New importance score (0-1)"),
    tier: CLIMemoryTier = typer.Option(CLIMemoryTier.ALL, help="Memory tier to update (short_term, working, all)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to help locate the memory")
):
    """Update an existing memory in the specified tier."""
    try:
        # Convert CLI tier enum to internal tier enum
        memory_tier = map_cli_tier_to_memory_tier(tier)
        
        # Get the existing memory first
        memory = get_memory_manager().get_memory(memory_id, tier=memory_tier, session_id=session_id)
        if not memory:
            if tier == CLIMemoryTier.ALL:
                console.print(f"[bold red]Memory not found:[/bold red] {memory_id}", file=sys.stderr)
            else:
                console.print(f"[bold red]Memory not found in {tier.value} tier:[/bold red] {memory_id}", file=sys.stderr)
            sys.exit(1)
            
        # Parse metadata if provided
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                console.print("[bold red]Error:[/bold red] Invalid JSON format for metadata", file=sys.stderr)
                sys.exit(1)
        
        # Add session_id to metadata if provided
        if session_id and "session_id" not in metadata_dict and metadata_dict:
            metadata_dict["session_id"] = session_id
        
        # Update the memory
        updated = get_memory_manager().update_memory(
            memory_id=memory_id,
            content=content,
            metadata=metadata_dict,
            importance=importance,
            tier=memory_tier,
            session_id=session_id
        )
        
        if updated:
            # Determine which tier the memory belongs to based on metadata
            tier_name = "unknown"
            updated_memory = get_memory_manager().get_memory(memory_id, tier=memory_tier, session_id=session_id)
            if updated_memory and "type" in updated_memory.metadata:
                if updated_memory.metadata["type"] == "conversation_turn":
                    tier_name = "short-term"
                elif updated_memory.metadata["type"] == "session_context":
                    tier_name = "working"
                    
            console.print(f"✅ Memory [bold]{memory_id}[/bold] in [blue]{tier_name}[/blue] tier updated successfully")
        else:
            console.print(f"[bold yellow]Warning:[/bold yellow] Memory not updated. No changes were made.", file=sys.stderr)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        sys.exit(1)


@app.command("delete")
def delete_memory(
    memory_id: str = typer.Argument(..., help="ID of the memory to delete"),
    tier: CLIMemoryTier = typer.Option(CLIMemoryTier.ALL, help="Memory tier to delete from (short_term, working, all)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to help locate the memory")
):
    """Delete a memory by ID from the specified tier."""
    try:
        # Convert CLI tier enum to internal tier enum
        memory_tier = map_cli_tier_to_memory_tier(tier)
        
        # Delete memory
        deleted = get_memory_manager().delete_memory(memory_id, tier=memory_tier, session_id=session_id)
        
        if deleted:
            if tier == CLIMemoryTier.ALL:
                console.print(f"✅ Memory [bold]{memory_id}[/bold] deleted successfully")
            else:
                console.print(f"✅ Memory [bold]{memory_id}[/bold] deleted from [blue]{tier.value}[/blue] tier successfully")
        else:
            if tier == CLIMemoryTier.ALL:
                console.print(f"[bold yellow]Warning:[/bold yellow] Memory not found: {memory_id}", file=sys.stderr)
            else:
                console.print(f"[bold yellow]Warning:[/bold yellow] Memory not found in {tier.value} tier: {memory_id}", file=sys.stderr)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        sys.exit(1)


@app.command("conversation-turn")
def add_conversation_turn(
    content: str = typer.Argument(..., help="Conversation turn content"),
    role: str = typer.Option("user", help="Role (user, assistant, system, etc.)"),
    session_id: str = typer.Option(..., help="Session ID for the conversation"),
    importance: float = typer.Option(0.5, help="Importance score (0-1)")
):
    """Add a conversation turn to short-term memory."""
    try:
        # Add conversation turn
        memory_id = get_memory_manager().add_conversation_turn(
            session_id=session_id,
            content=content,
            role=role,
            importance=importance
        )
        
        ttl_minutes = get_memory_manager().short_term_ttl / 60
        console.print(f"✅ Conversation turn added with ID: [bold green]{memory_id}[/bold green]")
        console.print(f"   Role: [blue]{role}[/blue], Session: [yellow]{session_id}[/yellow]")
        console.print(f"   Will expire in [yellow]{ttl_minutes:.0f} minutes[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        sys.exit(1)


@app.command("generate-prompt")
def generate_prompt(
    session_id: str = typer.Argument(..., help="Session ID for the conversation"),
    system_message: str = typer.Option("You are a helpful assistant.", help="System message for the prompt"),
    user_query: str = typer.Argument(..., help="User query to answer"),
    max_turns: int = typer.Option(5, help="Maximum number of conversation turns to include"),
    include_working: bool = typer.Option(True, help="Include working memory in prompt")
):
    """Generate a token-optimized prompt with conversation history and context."""
    try:
        # Generate prompt
        prompt, token_stats = get_memory_manager().generate_prompt(
            session_id=session_id,
            system_message=system_message,
            user_query=user_query,
            max_short_term_turns=max_turns,
            include_working_memory=include_working
        )
        
        # Display prompt and token statistics
        console.print("[bold green]Generated Prompt:[/bold green]")
        console.print("=" * 60)
        console.print(prompt)
        console.print("=" * 60)
        
        # Display token statistics
        console.print("\n[bold blue]Token Statistics:[/bold blue]")
        console.print(f"Total tokens:      [yellow]{token_stats['total']}[/yellow]")
        console.print(f"System message:    [yellow]{token_stats['system']}[/yellow]")
        console.print(f"Short-term memory: [yellow]{token_stats['short_term']}[/yellow]")
        console.print(f"Working memory:    [yellow]{token_stats['working']}[/yellow]")
        console.print(f"User query:        [yellow]{token_stats['user_query']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        sys.exit(1)


@app.callback()
def main():
    """Azentiq Memory Manager - Tiered memory for AI assistants.
    
    This CLI provides commands to interact with the Memory Manager.
    For the MVP, only session memory (Redis) is supported.
    """
    pass


if __name__ == "__main__":
    app()
