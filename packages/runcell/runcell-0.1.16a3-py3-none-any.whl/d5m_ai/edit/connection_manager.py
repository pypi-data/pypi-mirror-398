import uuid

# Create a global registry to track all handlers and their waiters
handler_registry = {}


class ConnectionManager:
    @staticmethod
    def register_handler(handler):
        """Register a new handler in the global registry."""
        connection_id = str(uuid.uuid4())
        handler.connection_id = connection_id
        handler_registry[connection_id] = handler
        return connection_id
    
    @staticmethod
    def unregister_handler(connection_id):
        """Remove a handler from the global registry."""
        if connection_id in handler_registry:
            del handler_registry[connection_id]
    
    @staticmethod
    def get_handler(connection_id):
        """Get a handler by connection ID."""
        return handler_registry.get(connection_id)
    
    @staticmethod
    def get_registry():
        """Get the entire handler registry."""
        return handler_registry 