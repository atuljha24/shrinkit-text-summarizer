import logging
import time
from functools import wraps
from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from datetime import datetime
import threading
import queue
import os

@dataclass
class MetricsEvent:
    timestamp: float
    event_type: str
    duration_ms: Optional[float] = None
    metadata: Optional[Dict] = None

class MetricsCollector:
    def __init__(self, flush_interval: int = 60):
        self.events: List[MetricsEvent] = []
        self.lock = threading.Lock()
        self.flush_interval = flush_interval
        self.event_queue = queue.Queue()
        self._start_background_worker()
        
    def _start_background_worker(self):
        def worker():
            while True:
                try:
                    time.sleep(self.flush_interval)
                    self.flush_metrics()
                except Exception as e:
                    logging.error(f"Error in metrics worker: {e}")
                    
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        
    def track_event(self, event_type: str, metadata: Optional[Dict] = None):
        """Track a metrics event."""
        event = MetricsEvent(
            timestamp=time.time(),
            event_type=event_type,
            metadata=metadata
        )
        with self.lock:
            self.events.append(event)
            
    def track_duration(self, event_type: str):
        """Decorator to track duration of function calls."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    self.track_event(
                        event_type,
                        metadata={
                            'duration_ms': duration,
                            'success': True
                        }
                    )
                    return result
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    self.track_event(
                        event_type,
                        metadata={
                            'duration_ms': duration,
                            'success': False,
                            'error': str(e)
                        }
                    )
                    raise
            return wrapper
        return decorator
        
    def flush_metrics(self):
        """Flush metrics to disk."""
        with self.lock:
            if not self.events:
                return
                
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'metrics_{current_time}.json'
            
            os.makedirs('metrics', exist_ok=True)
            filepath = os.path.join('metrics', filename)
            
            metrics_data = [
                {
                    'timestamp': event.timestamp,
                    'event_type': event.event_type,
                    'duration_ms': event.duration_ms,
                    'metadata': event.metadata
                }
                for event in self.events
            ]
            
            with open(filepath, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
            self.events.clear()
            
    def get_metrics_summary(self) -> Dict:
        """Get summary of current metrics."""
        with self.lock:
            event_counts = {}
            total_durations = {}
            error_counts = {}
            
            for event in self.events:
                # Count events
                event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
                
                # Sum durations
                if event.metadata and 'duration_ms' in event.metadata:
                    if event.event_type not in total_durations:
                        total_durations[event.event_type] = []
                    total_durations[event.event_type].append(event.metadata['duration_ms'])
                    
                # Count errors
                if event.metadata and not event.metadata.get('success', True):
                    error_counts[event.event_type] = error_counts.get(event.event_type, 0) + 1
                    
            # Calculate averages
            avg_durations = {
                event_type: sum(durations) / len(durations)
                for event_type, durations in total_durations.items()
            }
            
            return {
                'event_counts': event_counts,
                'average_durations_ms': avg_durations,
                'error_counts': error_counts,
                'total_events': len(self.events)
            }

# Global metrics collector instance
metrics = MetricsCollector() 