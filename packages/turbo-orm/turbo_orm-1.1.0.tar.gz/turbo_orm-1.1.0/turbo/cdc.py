"""
Change Data Capture (CDC) - Stream Model Changes

Captures and streams database changes to external systems in real-time.
"""

import json
import datetime
import threading
import queue


class CDCEvent:
    """Represents a change event"""

    def __init__(self, model_name, event_type, record_id, before=None, after=None):
        self.model_name = model_name
        self.event_type = event_type  # insert, update, delete
        self.record_id = record_id
        self.before = before
        self.after = after
        self.timestamp = datetime.datetime.now()

    def to_dict(self):
        return {
            "model": self.model_name,
            "type": self.event_type,
            "id": self.record_id,
            "before": self.before,
            "after": self.after,
            "timestamp": self.timestamp.isoformat(),
        }


class CDCStream:
    """CDC Stream Manager"""

    def __init__(self, output="console"):
        """
        Args:
            output: 'console', 'file', or HTTP URL
        """
        self.output = output
        self.queue = queue.Queue()
        self.running = False
        self.thread = None

    def start(self):
        """Start the CDC stream"""
        self.running = True
        self.thread = threading.Thread(target=self._process_events, daemon=True)
        self.thread.start()
        print(f"📡 CDC Stream started (output: {self.output})")

    def stop(self):
        """Stop the CDC stream"""
        self.running = False
        if self.thread:
            self.thread.join()

    def publish(self, event):
        """Publish an event to the stream"""
        self.queue.put(event)

    def _process_events(self):
        """Process events from queue"""
        while self.running:
            try:
                event = self.queue.get(timeout=0.1)
                self._send_event(event)
            except queue.Empty:
                continue

    def _send_event(self, event):
        """Send event to configured output"""
        data = event.to_dict()

        if self.output == "console":
            print(
                f"[CDC] {event.event_type.upper()} {event.model_name}#{event.record_id}"
            )
        elif self.output == "file":
            with open("cdc_stream.jsonl", "a") as f:
                f.write(json.dumps(data) + "\n")
        elif self.output.startswith("http"):
            # HTTP webhook (would need requests library)
            try:
                import requests

                requests.post(self.output, json=data, timeout=1)
            except ImportError:
                print(f"Warning: requests not available for HTTP CDC")
            except Exception as e:
                print(f"CDC webhook error: {e}")


# Global CDC instance
_cdc_stream = None
_cdc_enabled = False


def enable_cdc(output="console"):
    """Enable CDC streaming"""
    global _cdc_stream, _cdc_enabled
    _cdc_stream = CDCStream(output)
    _cdc_stream.start()
    _cdc_enabled = True
    return _cdc_stream


def get_cdc_stream():
    global _cdc_stream, _cdc_enabled
    if _cdc_enabled and _cdc_stream is None:
        _cdc_stream = CDCStream()
        _cdc_stream.start()
    return _cdc_stream


def add_cdc_to_model():
    """Add CDC capabilities to Model"""
    from .model import Model

    # Patch save
    original_save = Model.save

    def save_with_cdc(self, db):
        is_new = self.id is None

        # Only capture if CDC is enabled
        if _cdc_enabled:
            # Capture before state
            before = None
            if not is_new:
                existing = self.__class__.get(db, self.id)
                if existing:
                    before = {k: getattr(existing, k) for k in self._fields.keys()}

        # Execute save
        original_save(self, db)

        # Publish CDC event if enabled
        if _cdc_enabled:
            after = {k: getattr(self, k) for k in self._fields.keys()}
            event_type = "insert" if is_new else "update"
            event = CDCEvent(
                model_name=self.__class__.__name__,
                event_type=event_type,
                record_id=self.id,
                before=before if not is_new else None,
                after=after,
            )
            get_cdc_stream().publish(event)

    Model.save = save_with_cdc

    # Patch delete
    original_delete = Model.delete

    def delete_with_cdc(self, db):
        # Capture before state if CDC enabled
        if _cdc_enabled:
            before = {k: getattr(self, k) for k in self._fields.keys()}

        # Execute delete
        original_delete(self, db)

        # Publish CDC event if enabled
        if _cdc_enabled:
            event = CDCEvent(
                model_name=self.__class__.__name__,
                event_type="delete",
                record_id=self.id,
                before=before,
                after=None,
            )
            get_cdc_stream().publish(event)

    Model.delete = delete_with_cdc
