"""
Shared helpers for frontend tools.

Provides common WebSocket communication patterns used by frontend-interactive tools.
"""

import asyncio
import uuid
from typing import Any, Dict, Optional


async def send_and_wait(
    handler,
    message_type: str,
    payload: Dict[str, Any],
    timeout: float = 90.0,
    error_message: Optional[str] = None,
) -> str:
    """
    Send a message to the frontend and wait for a response.
    
    This is the common pattern for frontend-interactive tools:
    1. Generate a request ID
    2. Set up a waiter future
    3. Send the message to frontend
    4. Wait for response with timeout
    
    Args:
        handler: The WebSocket handler instance.
        message_type: The type of message to send (e.g., "cell_execute").
        payload: Additional data to include in the message.
        timeout: Maximum time to wait for response in seconds.
        error_message: Custom error message for timeout. Defaults to generic message.
    
    Returns:
        The result from the frontend, or error message on timeout.
    """
    request_id = str(uuid.uuid4())
    handler.current_request_id = request_id

    # Prepare a brand-new waiter.
    if handler.waiter and not handler.waiter.done():
        handler.waiter.cancel()
    handler.waiter = asyncio.get_running_loop().create_future()

    # Build the message.
    message = {
        "type": message_type,
        "request_id": request_id,
        "connection_id": handler.connection_id,
    }
    # Add payload, filtering out None values.
    for key, value in payload.items():
        if value is not None:
            message[key] = value

    # Send the message to the browser.
    try:
        await handler._safe_write_message(message)
    except Exception as e:
        raise RuntimeError(f"Failed to send {message_type} request: {e}")

    # Await the result (or timeout).
    try:
        result = await asyncio.wait_for(handler.waiter, timeout=timeout)
    except asyncio.TimeoutError:
        if error_message:
            result = error_message
        else:
            result = f"Error: No result received from {message_type} (timeout)"
    finally:
        handler.waiter = None

    return result


async def request_permission_and_execute(
    handler,
    permission_message_type: str,
    permission_message: str,
    execute_message_type: str,
    execute_payload: Dict[str, Any],
    permission_timeout: float = 120.0,
    execute_timeout: float = 120.0,
    cancelled_message: str = "Operation cancelled by user.",
    permission_timeout_message: str = "Operation timed out waiting for user permission.",
) -> str:
    """
    Request user permission via frontend, then execute if granted.
    
    This pattern is used for potentially destructive operations like rerun_all_cells.
    
    Args:
        handler: The WebSocket handler instance.
        permission_message_type: Message type for permission request.
        permission_message: Message to display to user.
        execute_message_type: Message type for the actual operation.
        execute_payload: Data for the actual operation.
        permission_timeout: Timeout for permission response.
        execute_timeout: Timeout for operation execution.
        cancelled_message: Message when user denies permission.
        permission_timeout_message: Message when permission times out.
    
    Returns:
        The result from the operation, or appropriate error/cancel message.
    """
    request_id = str(uuid.uuid4())
    
    # Create a waiter for the permission response.
    permission_waiter = asyncio.get_running_loop().create_future()
    
    # Store the waiter temporarily.
    original_waiter = handler.waiter
    handler.waiter = permission_waiter
    
    try:
        # Send permission request to frontend.
        await handler._safe_write_message({
            "type": permission_message_type,
            "message": permission_message,
            "request_id": request_id,
            "connection_id": handler.connection_id,
        })
        
        # Wait for user response.
        try:
            permission_response = await asyncio.wait_for(permission_waiter, timeout=permission_timeout)
            if not permission_response or permission_response.get("allowed") != True:
                return cancelled_message
        except asyncio.TimeoutError:
            return permission_timeout_message
    finally:
        # Restore original waiter.
        handler.waiter = original_waiter

    # Permission granted, proceed with the operation.
    return await send_and_wait(
        handler,
        execute_message_type,
        execute_payload,
        timeout=execute_timeout,
    )

