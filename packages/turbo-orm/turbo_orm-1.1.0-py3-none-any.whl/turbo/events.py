"""
Event System - Real-time Model Hooks & Signals

Publish-Subscribe system for model events.
"""

from collections import defaultdict


class EventBus:
    """Singleton event bus"""

    _subscribers = defaultdict(list)

    @classmethod
    def subscribe(cls, event_name, handler):
        cls._subscribers[event_name].append(handler)

    @classmethod
    def emit(cls, event_name, *args, **kwargs):
        for handler in cls._subscribers[event_name]:
            handler(*args, **kwargs)

    @classmethod
    def clear(cls):
        cls._subscribers.clear()


def add_events_to_model():
    """Add event capabilities to Model"""
    from .model import Model

    # Add 'on' decorator/method
    @classmethod
    def on(cls, event_name):
        def decorator(func):
            # Register handler
            # Event name format: "ModelName.event" or just "event" for global
            full_event_name = f"{cls.__name__}.{event_name}"
            EventBus.subscribe(full_event_name, func)
            return func

        return decorator

    Model.on = on

    # Patch save/delete to emit events
    original_save = Model.save
    original_delete = Model.delete

    def save_with_events(self, db):
        is_new = self.id is None
        cls = self.__class__

        # Before Save
        EventBus.emit(f"{cls.__name__}.before_save", self)
        if is_new:
            EventBus.emit(f"{cls.__name__}.before_create", self)
        else:
            EventBus.emit(f"{cls.__name__}.before_update", self)

        original_save(self, db)

        # After Save
        EventBus.emit(f"{cls.__name__}.after_save", self)
        if is_new:
            EventBus.emit(f"{cls.__name__}.after_create", self)
        else:
            EventBus.emit(f"{cls.__name__}.after_update", self)

    def delete_with_events(self, db):
        cls = self.__class__
        EventBus.emit(f"{cls.__name__}.before_delete", self)

        original_delete(self, db)

        EventBus.emit(f"{cls.__name__}.after_delete", self)

    Model.save = save_with_events
    Model.delete = delete_with_events
