"""
Train Traffic Control System - Data Models
Defines the core data structures for railway network, trains, and scheduling
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import datetime


class TrainType(Enum):
    """Different types of trains with varying priorities"""
    SUPERFAST_EXPRESS = 1  # Highest priority
    EXPRESS = 2
    PASSENGER = 3
    LOCAL = 4
    FREIGHT = 5  # Lowest priority
    MAINTENANCE = 6


class TrackType(Enum):
    """Types of railway tracks"""
    SINGLE = 1  # Single track - trains can go in one direction at a time
    DOUBLE = 2  # Double track - separate tracks for each direction
    TRIPLE = 3  # Triple track
    QUADRUPLE = 4  # Quadruple track


@dataclass
class Station:
    """Represents a railway station"""
    id: str
    name: str
    platform_count: int
    position_km: float  # Position along the route in kilometers
    has_loop_line: bool = False  # Can trains wait here for crossing
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Section:
    """Represents a section of track between two stations"""
    id: str
    from_station: Station
    to_station: Station
    length_km: float
    track_type: TrackType
    speed_limit_kmph: float = 100.0
    gradient: float = 0.0  # Gradient percentage
    is_blocked: bool = False  # For maintenance or incidents
    
    @property
    def capacity(self) -> int:
        """Number of trains that can use this section simultaneously"""
        if self.track_type == TrackType.SINGLE:
            return 1
        elif self.track_type == TrackType.DOUBLE:
            return 2
        elif self.track_type == TrackType.TRIPLE:
            return 3
        else:
            return 4


@dataclass
class Train:
    """Represents a train with its characteristics"""
    id: str
    name: str
    train_type: TrainType
    max_speed_kmph: float
    length_meters: float
    scheduled_departure: datetime.datetime
    origin: Station
    destination: Station
    current_position: Optional[float] = None  # Current position in km
    current_speed_kmph: float = 0.0
    delay_minutes: float = 0.0
    
    @property
    def priority(self) -> int:
        """Priority based on train type (lower value = higher priority)"""
        return self.train_type.value
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class TrainSchedule:
    """Represents a train's scheduled journey through the network"""
    train: Train
    route: List[Section]
    station_stops: List[Tuple[Station, datetime.datetime, datetime.datetime]]  # (station, arrival, departure)
    current_section_index: int = 0
    status: str = "SCHEDULED"  # SCHEDULED, RUNNING, DELAYED, COMPLETED
    
    def get_next_station(self) -> Optional[Station]:
        """Get the next station on the route"""
        if self.current_section_index < len(self.route):
            return self.route[self.current_section_index].to_station
        return None
    
    def calculate_section_time(self, section: Section) -> float:
        """Calculate time to traverse a section in minutes"""
        # Adjust speed based on gradient
        effective_speed = self.train.max_speed_kmph * (1 - abs(section.gradient) / 100)
        effective_speed = min(effective_speed, section.speed_limit_kmph)
        
        # Time = distance / speed (converted to minutes)
        time_hours = section.length_km / effective_speed
        return time_hours * 60


@dataclass
class NetworkState:
    """Represents the current state of the railway network"""
    timestamp: datetime.datetime
    stations: List[Station]
    sections: List[Section]
    active_trains: List[TrainSchedule]
    section_occupancy: Dict[str, List[Train]] = field(default_factory=dict)
    station_occupancy: Dict[str, List[Train]] = field(default_factory=dict)
    
    def is_section_available(self, section: Section, train: Train = None) -> bool:
        """Check if a section is available for a train"""
        if section.is_blocked:
            return False
        
        current_trains = self.section_occupancy.get(section.id, [])
        
        # For single track, check if any train is using it
        if section.track_type == TrackType.SINGLE:
            return len(current_trains) == 0
        
        # For multiple tracks, check capacity
        return len(current_trains) < section.capacity
    
    def update_train_position(self, train_schedule: TrainSchedule, new_section: Optional[Section]):
        """Update train position in the network"""
        train = train_schedule.train
        
        # Remove from current section
        for section_id, trains in self.section_occupancy.items():
            if train in trains:
                trains.remove(train)
        
        # Add to new section if provided
        if new_section:
            if new_section.id not in self.section_occupancy:
                self.section_occupancy[new_section.id] = []
            self.section_occupancy[new_section.id].append(train)


@dataclass
class OptimizationResult:
    """Result from the optimization algorithm"""
    schedule: List[Tuple[Train, Section, datetime.datetime]]  # (train, section, time)
    throughput: float  # Trains per hour
    average_delay: float  # Minutes
    conflicts_resolved: int
    recommendations: List[str]
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "throughput": self.throughput,
            "average_delay": self.average_delay,
            "conflicts_resolved": self.conflicts_resolved,
            "recommendations": self.recommendations,
            "schedule": [
                {
                    "train_id": train.id,
                    "train_name": train.name,
                    "section_id": section.id,
                    "time": time.isoformat()
                }
                for train, section, time in self.schedule
            ]
        }