"""
Unified reference formatting utilities for AI modes.
This module provides consistent reference formatting across ask, edit, and agent modes.
"""

import json
from typing import List, Any, Optional


def format_references_as_json(references: List[Any]) -> str:
    """
    Format references as JSON string wrapped in XML tags.
    
    Args:
        references: List of reference objects (file metadata, etc.)
        
    Returns:
        Formatted string with references in JSON format within XML tags
    """
    if not references:
        return ""
    
    # Convert references to JSON string
    try:
        references_json = json.dumps(references, indent=2)
    except (TypeError, ValueError) as e:
        # Fallback for non-serializable objects
        serializable_refs = []
        for ref in references:
            if isinstance(ref, dict):
                serializable_refs.append(ref)
            else:
                # Convert non-dict objects to string representation
                serializable_refs.append(str(ref))
        references_json = json.dumps(serializable_refs, indent=2)
    
    return f"\nHere are detailed references related to '@' mentioned in the message. \n<references>\n{references_json}\n</references>\n"


def append_references_to_content(content: str, references: List[Any]) -> str:
    """
    Append formatted references to content string.
    
    Args:
        content: Original content string
        references: List of reference objects
        
    Returns:
        Content with references appended in JSON format
    """
    if not references:
        return content
    
    references_text = format_references_as_json(references)
    return content + references_text


def process_user_message_with_references(message: dict) -> dict:
    """
    Process a user message to format references into the content.
    
    Args:
        message: Message dictionary with potential references field
        
    Returns:
        Processed message with references formatted into content and references field removed
    """
    if message.get("role") != "user" or "references" not in message:
        return message
    
    # Create a copy of the message
    processed_message = message.copy()
    
    # Format references into the content
    references = message.get("references", [])
    if references:
        content = message.get("content", "")
        processed_message["content"] = append_references_to_content(content, references)
    
    # Remove the references field from the processed message
    processed_message.pop("references", None)
    
    return processed_message


def process_message_history_with_references(history: List[dict]) -> List[dict]:
    """
    Process a list of messages to format references into content.
    
    Args:
        history: List of message dictionaries
        
    Returns:
        Processed history with references formatted into user message content
    """
    processed_history = []
    
    for message in history:
        processed_message = process_user_message_with_references(message)
        processed_history.append(processed_message)
    
    return processed_history 