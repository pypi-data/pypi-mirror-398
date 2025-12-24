"""Webhook handling utilities."""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional


class WebhookEvent:
    """Webhook event data."""
    
    def __init__(self, event_type: str, data: Dict[str, Any]):
        """
        Initialize webhook event.
        
        Args:
            event_type: Event type (e.g., "render.completed")
            data: Event data
        """
        self.type = event_type
        self.data = data
    
    def __repr__(self) -> str:
        return f"WebhookEvent(type='{self.type}', data={self.data})"


class WebhookHandler:
    """Handler for Canvelete webhooks."""
    
    def __init__(self, secret: str):
        """
        Initialize webhook handler.
        
        Args:
            secret: Webhook secret for signature verification
        
        Example:
            handler = WebhookHandler(secret="your_webhook_secret")
        """
        self.secret = secret
    
    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Raw request body
            signature: Signature from X-Canvelete-Signature header
            timestamp: Optional timestamp from X-Canvelete-Timestamp header
        
        Returns:
            True if signature is valid
        
        Example:
            from flask import request
            
            @app.route("/webhooks/canvelete", methods=["POST"])
            def handle_webhook():
                signature = request.headers.get("X-Canvelete-Signature")
                
                if not handler.verify_signature(request.data, signature):
                    return "Invalid signature", 401
                
                # Process webhook...
                return "OK", 200
        """
        if not signature:
            return False
        
        # Construct signed payload
        if timestamp:
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        else:
            signed_payload = payload.decode('utf-8')
        
        # Compute expected signature
        expected_signature = hmac.new(
            self.secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(signature, expected_signature)
    
    def parse_event(self, payload: bytes) -> WebhookEvent:
        """
        Parse webhook event from payload.
        
        Args:
            payload: Raw request body
        
        Returns:
            WebhookEvent object
        
        Example:
            event = handler.parse_event(request.data)
            
            if event.type == "render.completed":
                print(f"Render completed: {event.data['url']}")
            elif event.type == "render.failed":
                print(f"Render failed: {event.data['error']}")
        """
        data = json.loads(payload)
        
        event_type = data.get("type", "unknown")
        event_data = data.get("data", {})
        
        return WebhookEvent(event_type, event_data)
    
    def construct_event(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> WebhookEvent:
        """
        Verify signature and parse event in one step.
        
        Args:
            payload: Raw request body
            signature: Signature from header
            timestamp: Optional timestamp from header
        
        Returns:
            WebhookEvent object
        
        Raises:
            ValueError: If signature is invalid
        
        Example:
            try:
                event = handler.construct_event(
                    request.data,
                    request.headers.get("X-Canvelete-Signature"),
                    request.headers.get("X-Canvelete-Timestamp")
                )
                
                # Process event...
                
            except ValueError as e:
                return "Invalid signature", 401
        """
        if not self.verify_signature(payload, signature, timestamp):
            raise ValueError("Invalid webhook signature")
        
        return self.parse_event(payload)


# Event type constants
class WebhookEventType:
    """Webhook event type constants."""
    
    RENDER_COMPLETED = "render.completed"
    RENDER_FAILED = "render.failed"
    RENDER_STARTED = "render.started"
    
    DESIGN_CREATED = "design.created"
    DESIGN_UPDATED = "design.updated"
    DESIGN_DELETED = "design.deleted"
    
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    
    CREDIT_LOW = "credit.low"
    CREDIT_DEPLETED = "credit.depleted"
    CREDIT_PURCHASED = "credit.purchased"
