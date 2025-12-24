from dataclasses import dataclass
from datetime import timedelta
from typing import Optional


@dataclass
class TimelineSpan:
    start: Optional[timedelta] = None
    end: Optional[timedelta] = None
    duration: timedelta = timedelta(0)
    start_trigger: str = "start"
    span_type: str = "content"
    num_segments: int = 0
