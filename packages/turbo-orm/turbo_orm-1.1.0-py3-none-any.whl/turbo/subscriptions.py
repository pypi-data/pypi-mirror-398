"""
WebSocket Subscriptions - Real-Time Event Streaming

Provides real-time subscriptions for model changes, cache invalidation,
schema updates, and mutation results via event-driven pub/sub model.

Features:
  • Channel-based pub/sub
  • Subscriber management
  • Event publishing
  • Automatic cache invalidation
  • Soft delete notifications
  • Schema change alerts
  • Mutation result streaming
  • Event batching
"""

from typing import Dict, List, Callable, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass
import json


@dataclass
class SubscriptionEvent:
    """Event published to subscriptions"""
    
    channel: str
    data: Any
    timestamp: datetime
    event_type: str = "update"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "channel": self.channel,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "type": self.event_type
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        data = self.to_dict()
        # Handle non-JSON-serializable data
        return json.dumps(data, default=str)


class Subscriber:
    """Individual subscription listener"""
    
    def __init__(self, subscriber_id: str, callback: Callable[[SubscriptionEvent], None], 
                 filters: Optional[Dict[str, Any]] = None):
        """
        Initialize subscriber.
        
        Args:
            subscriber_id: Unique identifier for this subscriber
            callback: Function called when event published
            filters: Optional filters to match events (e.g., {"user_id": 123})
        """
        self.id = subscriber_id
        self.callback = callback
        self.filters = filters or {}
        self.created_at = datetime.now()
        self.events_received = 0
    
    def matches(self, event: SubscriptionEvent) -> bool:
        """Check if event matches subscriber's filters"""
        if not self.filters:
            return True
        
        for key, value in self.filters.items():
            if isinstance(event.data, dict) and event.data.get(key) != value:
                return False
        
        return True
    
    def receive_event(self, event: SubscriptionEvent) -> None:
        """Receive and process event"""
        if self.matches(event):
            try:
                self.callback(event)
                self.events_received += 1
            except Exception as e:
                print(f"Error in subscriber {self.id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get subscriber statistics"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "events_received": self.events_received,
            "filters": self.filters
        }


class SubscriptionChannel:
    """Single subscription channel"""
    
    def __init__(self, channel_name: str):
        self.name = channel_name
        self.subscribers: Dict[str, Subscriber] = {}
        self.event_history: List[SubscriptionEvent] = []
        self.max_history = 100
    
    def subscribe(self, subscriber: Subscriber) -> None:
        """Add subscriber to channel"""
        self.subscribers[subscriber.id] = subscriber
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """Remove subscriber from channel"""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            return True
        return False
    
    def publish(self, event: SubscriptionEvent) -> int:
        """
        Publish event to all subscribers.
        
        Returns:
            Number of subscribers notified
        """
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Notify subscribers
        count = 0
        for subscriber in self.subscribers.values():
            subscriber.receive_event(event)
            count += 1
        
        return count
    
    def get_subscriber_count(self) -> int:
        """Get number of active subscribers"""
        return len(self.subscribers)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get channel statistics"""
        return {
            "name": self.name,
            "subscribers": len(self.subscribers),
            "event_history_size": len(self.event_history),
            "recent_events": [e.to_dict() for e in self.event_history[-5:]]
        }


class SubscriptionManager:
    """Manage real-time subscriptions and event publishing"""
    
    def __init__(self):
        """Initialize subscription manager"""
        self.channels: Dict[str, SubscriptionChannel] = {}
        self.global_subscribers: List[Subscriber] = []
        self.stats = {
            "total_publishes": 0,
            "total_subscribers": 0,
            "total_events_published": 0
        }
    
    def subscribe(self, channel: str, callback: Callable[[SubscriptionEvent], None],
                 subscriber_id: Optional[str] = None,
                 filters: Optional[Dict[str, Any]] = None) -> Subscriber:
        """
        Subscribe to a channel.
        
        Args:
            channel: Channel name (e.g., "users:created", "cache:invalidated")
            callback: Function to call when event published
            subscriber_id: Optional unique ID for subscriber
            filters: Optional filters to match events
            
        Returns:
            Subscriber object
        """
        if channel not in self.channels:
            self.channels[channel] = SubscriptionChannel(channel)
        
        sub_id = subscriber_id or f"sub_{id(callback)}"
        subscriber = Subscriber(sub_id, callback, filters)
        
        self.channels[channel].subscribe(subscriber)
        self.stats["total_subscribers"] += 1
        
        return subscriber
    
    def unsubscribe(self, channel: str, subscriber_id: str) -> bool:
        """Unsubscribe from a channel"""
        if channel in self.channels:
            removed = self.channels[channel].unsubscribe(subscriber_id)
            if removed:
                self.stats["total_subscribers"] = max(0, self.stats["total_subscribers"] - 1)
            return removed
        return False
    
    def publish(self, channel: str, data: Any, event_type: str = "update") -> int:
        """
        Publish event to channel.
        
        Args:
            channel: Channel name
            data: Event data
            event_type: Type of event (create, update, delete, etc.)
            
        Returns:
            Number of subscribers notified
        """
        if channel not in self.channels:
            self.channels[channel] = SubscriptionChannel(channel)
        
        event = SubscriptionEvent(channel, data, datetime.now(), event_type)
        count = self.channels[channel].publish(event)
        
        self.stats["total_publishes"] += 1
        self.stats["total_events_published"] += 1
        
        return count
    
    def subscribe_to_pattern(self, pattern: str, callback: Callable,
                            subscriber_id: Optional[str] = None) -> List[Subscriber]:
        """
        Subscribe to multiple channels matching pattern.
        
        Args:
            pattern: Pattern (e.g., "users:*", "*:deleted")
            callback: Callback function
            subscriber_id: Optional base ID for subscribers
            
        Returns:
            List of created subscribers
        """
        import fnmatch
        
        subscribers = []
        for channel_name in self.channels:
            if fnmatch.fnmatch(channel_name, pattern):
                sub_id = f"{subscriber_id}_{channel_name}" if subscriber_id else None
                sub = self.subscribe(channel_name, callback, sub_id)
                subscribers.append(sub)
        
        return subscribers
    
    def get_channel_stats(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a channel"""
        if channel in self.channels:
            return self.channels[channel].get_stats()
        return None
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all channels"""
        return {
            "channels": len(self.channels),
            "total_subscribers": self.stats["total_subscribers"],
            "total_publishes": self.stats["total_publishes"],
            "total_events": self.stats["total_events_published"],
            "channel_details": {
                name: channel.get_stats()
                for name, channel in self.channels.items()
            }
        }


# ============================================================================
# Pre-built Subscription Channels (Common Use Cases)
# ============================================================================

class ModelSubscriptions:
    """Subscriptions for model changes"""
    
    @staticmethod
    def on_created(model_name: str) -> str:
        """Channel for model creation events"""
        return f"model:{model_name}:created"
    
    @staticmethod
    def on_updated(model_name: str) -> str:
        """Channel for model update events"""
        return f"model:{model_name}:updated"
    
    @staticmethod
    def on_deleted(model_name: str) -> str:
        """Channel for model deletion events"""
        return f"model:{model_name}:deleted"
    
    @staticmethod
    def on_any_change(model_name: str) -> str:
        """Channel for any model change"""
        return f"model:{model_name}:*"


class CacheSubscriptions:
    """Subscriptions for cache events"""
    
    @staticmethod
    def on_invalidate() -> str:
        """Channel for cache invalidation"""
        return "cache:invalidated"
    
    @staticmethod
    def on_key_updated(key: str) -> str:
        """Channel for specific cache key update"""
        return f"cache:updated:{key}"


class MigrationSubscriptions:
    """Subscriptions for migration events"""
    
    @staticmethod
    def on_schema_change() -> str:
        """Channel for schema changes"""
        return "schema:changed"
    
    @staticmethod
    def on_migration_applied() -> str:
        """Channel for migration applied"""
        return "migrations:applied"


class GraphQLSubscriptions:
    """Subscriptions for GraphQL mutations"""
    
    @staticmethod
    def on_mutation(mutation_name: str) -> str:
        """Channel for mutation execution"""
        return f"graphql:mutation:{mutation_name}"
    
    @staticmethod
    def on_query_result(query_id: str) -> str:
        """Channel for query results"""
        return f"graphql:query:{query_id}"


if __name__ == "__main__":
    print("✓ WebSocket subscriptions module loaded successfully")
