"""
Secure error handling for production.
Prevents information disclosure while maintaining useful error messages.
"""
import os
import logging

def get_error_detail(e: Exception, default_message: str, operation: str = "operation") -> str:
    """
    Get safe error detail message.
    In production, returns generic message. In development, returns detailed message.
    """
    is_production = os.getenv("NODE_ENV") == "production" or os.getenv("RAILWAY_ENVIRONMENT")
    
    if is_production:
        # Log full error details to server logs (not exposed to client)
        logging.error(f"{operation} failed: {type(e).__name__}: {str(e)}")
        return default_message
    else:
        # In development, show more details for debugging
        return f"{operation} failed: {str(e)}"