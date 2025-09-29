"""
Train Traffic Simulator
Simulates train movements through the network for testing and validation
"""

import datetime
from typing import List, Dict, Tuple
import random
from models import (
    Train, Section, Station, TrainSchedule, NetworkState,
    TrainType, TrackType
)
from optimizer import TrainScheduleOptimizer


class RailwayNetworkSimulator:
    """Simulates train movements and network dynamics"""
    
    def __init__(self):
        self.current_time = datetime.datetime.now()
        self.stations = []
        self.sections = []
        self.trains = []
        self.schedules = []
        
    def create_sample_network(self):
        """Creates a sample railway network for demonstration"""
        
        # Create stations along a route
        station_data = [
            ("STN01", "Delhi Junction", 0, 4, True),
            ("STN02", "Ghaziabad", 25, 3, False),
            ("STN03", "Meerut", 70, 2, True),
            ("STN04", "Muzaffarnagar", 120, 2, False),
            ("STN05", "Saharanpur", 165, 3, True),
        ]
        
        for sid, name, pos, platforms, has_loop in station_data:
            station = Station(
                id=sid,
                name=name,
                platform_count=platforms,
                position_km=pos,
                has_loop_line=has_loop
            )
            self.stations.append(station)
        
        # Create sections between stations
        for i in range(len(self.stations) - 1):
            from_station = self.stations[i]
            to_station = self.stations[i + 1]
            
            # Vary track types for complexity
            if i % 2 == 0:
                track_type = TrackType.SINGLE
            else:
                track_type = TrackType.DOUBLE
            
            section = Section(
                id=f"SEC{i+1:02d}",
                from_station=from_station,
                to_station=to_station,
                length_km=to_station.position_km - from_station.position_km,
                track_type=track_type,
                speed_limit_kmph=100 if track_type == TrackType.DOUBLE else 80,
                gradient=random.uniform(-0.5, 0.5)
            )
            self.sections.append(section)
        
        # Create reverse sections for double tracks
        for i, section in enumerate(list(self.sections)):
            if section.track_type == TrackType.DOUBLE:
                reverse_section = Section(
                    id=f"SEC{i+1:02d}R",
                    from_station=section.to_station,
                    to_station=section.from_station,
                    length_km=section.length_km,
                    track_type=section.track_type,
                    speed_limit_kmph=section.speed_limit_kmph,
                    gradient=-section.gradient
                )
                self.sections.append(reverse_section)
    
    def create_sample_trains(self, num_trains: int = 5):
        """Creates sample trains with different characteristics"""
        
        train_types = [
            (TrainType.SUPERFAST_EXPRESS, "Rajdhani Express", 160),
            (TrainType.EXPRESS, "Shatabdi Express", 140),
            (TrainType.PASSENGER, "Passenger", 100),
            (TrainType.LOCAL, "Local", 80),
            (TrainType.FREIGHT, "Freight", 60),
        ]
        
        for i in range(num_trains):
            train_type, base_name, speed = train_types[i % len(train_types)]
            
            # Randomly select origin and destination
            origin_idx = random.randint(0, len(self.stations) - 2)
            dest_idx = random.randint(origin_idx + 1, len(self.stations) - 1)
            
            train = Train(
                id=f"TRN{i+1:03d}",
                name=f"{base_name} {i+1:02d}",
                train_type=train_type,
                max_speed_kmph=speed,
                length_meters=random.randint(200, 600),
                scheduled_departure=self.current_time + datetime.timedelta(
                    minutes=random.randint(0, 60)
                ),
                origin=self.stations[origin_idx],
                destination=self.stations[dest_idx],
                current_position=self.stations[origin_idx].position_km
            )
            self.trains.append(train)
            
            # Create schedule for the train
            route = []
            for j in range(origin_idx, dest_idx):
                # Find the section connecting these stations
                for section in self.sections:
                    if (section.from_station == self.stations[j] and 
                        section.to_station == self.stations[j + 1]):
                        route.append(section)
                        break
            
            # Generate station stops
            station_stops = []
            current_time = train.scheduled_departure
            
            for j in range(origin_idx, dest_idx + 1):
                arrival_time = current_time
                if j < dest_idx:
                    # Calculate time to next station
                    section = route[j - origin_idx] if j > origin_idx else None
                    if section:
                        travel_time = (section.length_km / train.max_speed_kmph) * 60
                        current_time += datetime.timedelta(minutes=travel_time)
                
                # Add stop time at intermediate stations
                stop_duration = 2 if j != dest_idx else 0
                departure_time = arrival_time + datetime.timedelta(minutes=stop_duration)
                
                station_stops.append((
                    self.stations[j],
                    arrival_time,
                    departure_time
                ))
                
                if j < dest_idx:
                    current_time = departure_time
            
            schedule = TrainSchedule(
                train=train,
                route=route,
                station_stops=station_stops
            )
            self.schedules.append(schedule)
    
    def simulate_step(self, network_state: NetworkState, time_step_minutes: int = 5):
        """Simulates one time step of train movements"""
        
        network_state.timestamp += datetime.timedelta(minutes=time_step_minutes)
        
        for schedule in network_state.active_trains:
            train = schedule.train
            
            # Skip if train hasn't departed yet
            if network_state.timestamp < train.scheduled_departure:
                continue
            
            # Update train status
            if schedule.status == "SCHEDULED":
                schedule.status = "RUNNING"
            
            # Check if train completed its journey
            if schedule.current_section_index >= len(schedule.route):
                schedule.status = "COMPLETED"
                continue
            
            current_section = schedule.route[schedule.current_section_index]
            
            # Check if section is available
            if network_state.is_section_available(current_section, train):
                # Move train forward
                distance_to_travel = (train.max_speed_kmph / 60) * time_step_minutes
                
                # Check if train completes the section
                remaining_distance = current_section.length_km - (
                    train.current_position - current_section.from_station.position_km
                )
                
                if distance_to_travel >= remaining_distance:
                    # Train completes the section
                    train.current_position = current_section.to_station.position_km
                    network_state.update_train_position(schedule, None)
                    schedule.current_section_index += 1
                    
                    # Move to next section if available
                    if schedule.current_section_index < len(schedule.route):
                        next_section = schedule.route[schedule.current_section_index]
                        if network_state.is_section_available(next_section, train):
                            network_state.update_train_position(schedule, next_section)
                else:
                    # Train continues in current section
                    train.current_position += distance_to_travel
                    if current_section.id not in network_state.section_occupancy:
                        network_state.update_train_position(schedule, current_section)
            else:
                # Train is delayed due to section being occupied
                train.delay_minutes += time_step_minutes
                schedule.status = "DELAYED"
    
    def run_simulation(self, duration_hours: int = 4) -> Dict[str, any]:
        """Runs the simulation for specified duration"""
        
        # Initialize network state
        network_state = NetworkState(
            timestamp=self.current_time,
            stations=self.stations,
            sections=self.sections,
            active_trains=self.schedules
        )
        
        # Initialize optimizer
        optimizer = TrainScheduleOptimizer(network_state)
        
        # Run initial optimization
        optimization_result = optimizer.optimize_schedule()
        
        # Simulation results
        results = {
            "start_time": self.current_time,
            "duration_hours": duration_hours,
            "total_trains": len(self.trains),
            "optimization": optimization_result.to_dict(),
            "events": [],
            "final_statistics": {}
        }
        
        # Run simulation steps
        steps = (duration_hours * 60) // 5  # 5-minute steps
        
        for step in range(steps):
            # Log current state
            running_trains = sum(1 for s in self.schedules if s.status == "RUNNING")
            delayed_trains = sum(1 for s in self.schedules if s.status == "DELAYED")
            
            if step % 12 == 0:  # Log every hour
                event = {
                    "time": network_state.timestamp.isoformat(),
                    "running_trains": running_trains,
                    "delayed_trains": delayed_trains,
                    "section_occupancy": {
                        sid: len(trains) 
                        for sid, trains in network_state.section_occupancy.items()
                    }
                }
                results["events"].append(event)
            
            # Simulate train movements
            self.simulate_step(network_state, 5)
            
            # Re-optimize every 30 minutes
            if step % 6 == 0 and step > 0:
                optimization_result = optimizer.optimize_schedule()
                
                # Apply optimization recommendations
                # (In real system, this would update train controls)
        
        # Calculate final statistics
        completed_trains = sum(1 for s in self.schedules if s.status == "COMPLETED")
        total_delay = sum(t.delay_minutes for t in self.trains)
        
        results["final_statistics"] = {
            "completed_trains": completed_trains,
            "completion_rate": completed_trains / len(self.trains) * 100,
            "average_delay_minutes": total_delay / len(self.trains) if self.trains else 0,
            "total_delay_hours": total_delay / 60,
            "final_time": network_state.timestamp.isoformat()
        }
        
        return results
    
    def simulate_disruption(self, section_id: str) -> Dict[str, any]:
        """Simulates a disruption in a specific section"""
        
        # Find the section
        disrupted_section = None
        for section in self.sections:
            if section.id == section_id:
                disrupted_section = section
                break
        
        if not disrupted_section:
            return {"error": f"Section {section_id} not found"}
        
        # Mark section as blocked
        disrupted_section.is_blocked = True
        
        # Create network state
        network_state = NetworkState(
            timestamp=self.current_time,
            stations=self.stations,
            sections=self.sections,
            active_trains=self.schedules
        )
        
        # Run optimizer to handle disruption
        optimizer = TrainScheduleOptimizer(network_state)
        result = optimizer.handle_disruption(disrupted_section)
        
        return {
            "disrupted_section": section_id,
            "affected_trains": len([
                s for s in self.schedules 
                if disrupted_section in s.route
            ]),
            "optimization_result": result.to_dict()
        }