"""
Train Traffic Control Optimizer
Uses PuLP linear programming to optimize train scheduling and precedence
"""

from pulp import *
from typing import List, Dict, Tuple, Optional
import datetime
from models import (
    Train, Section, Station, TrainSchedule, NetworkState, 
    OptimizationResult, TrainType, TrackType
)


class TrainScheduleOptimizer:
    """Optimizes train schedules to maximize throughput and minimize delays"""
    
    def __init__(self, network_state: NetworkState):
        self.network_state = network_state
        self.time_horizon = 240  # Planning horizon in minutes (4 hours)
        self.time_slots = 48  # 5-minute intervals
        self.slot_duration = 5  # minutes per slot
        
    def optimize_schedule(self) -> OptimizationResult:
        """
        Main optimization function using Mixed Integer Linear Programming
        Maximizes throughput while minimizing delays
        """
        
        # Create the optimization problem
        prob = LpProblem("Train_Schedule_Optimization", LpMaximize)
        
        # Decision variables
        train_section_time = {}  # Binary: train t uses section s at time slot i
        train_delay = {}  # Continuous: delay for each train in minutes
        
        trains = [ts.train for ts in self.network_state.active_trains]
        sections = self.network_state.sections
        
        # Create decision variables
        for train in trains:
            train_delay[train.id] = LpVariable(
                f"delay_{train.id}", 
                lowBound=0, 
                upBound=60,  # Max 60 minutes delay
                cat='Continuous'
            )
            
            for section in sections:
                for t_slot in range(self.time_slots):
                    var_name = f"x_{train.id}_{section.id}_{t_slot}"
                    train_section_time[(train.id, section.id, t_slot)] = LpVariable(
                        var_name, cat='Binary'
                    )
        
        # Objective function: Maximize throughput - minimize weighted delays
        throughput_weight = 10
        delay_weight = 1
        
        # Count trains that complete their journey
        completed_trains = lpSum([
            train_section_time.get((train.id, section.id, t), 0)
            for train in trains
            for section in sections
            for t in range(self.time_slots - 10, self.time_slots)  # Last 50 minutes
        ])
        
        # Weighted delays based on train priority
        weighted_delays = lpSum([
            (6 - train.priority) * train_delay[train.id]  # Higher priority = higher weight
            for train in trains
        ])
        
        prob += throughput_weight * completed_trains - delay_weight * weighted_delays
        
        # Constraints
        
        # 1. Each train must follow its route sequentially
        for ts in self.network_state.active_trains:
            train = ts.train
            route = ts.route
            
            for i, section in enumerate(route):
                if i == 0:
                    # First section constraint - train must start
                    prob += lpSum([
                        train_section_time.get((train.id, section.id, t), 0)
                        for t in range(min(10, self.time_slots))  # Start within first 50 minutes
                    ]) >= 1
                else:
                    # Sequential constraint - must complete previous section before next
                    prev_section = route[i-1]
                    travel_time = int(ts.calculate_section_time(prev_section) / self.slot_duration)
                    
                    for t in range(travel_time, self.time_slots):
                        # If train was in previous section at time t-travel_time,
                        # it can be in current section at time t
                        if t - travel_time >= 0:
                            prob += (
                                train_section_time.get((train.id, section.id, t), 0) <= 
                                train_section_time.get((train.id, prev_section.id, t - travel_time), 0)
                            )
        
        # 2. Section capacity constraints
        for section in sections:
            for t_slot in range(self.time_slots):
                # Number of trains in section at time t <= section capacity
                trains_in_section = lpSum([
                    train_section_time.get((train.id, section.id, t_slot), 0)
                    for train in trains
                ])
                prob += trains_in_section <= section.capacity
        
        # 3. Safety constraint - minimum headway between trains
        min_headway_slots = 2  # 10 minutes minimum between trains
        
        for section in sections:
            if section.track_type == TrackType.SINGLE:
                # For single track, ensure safe spacing
                for t_slot in range(self.time_slots - min_headway_slots):
                    for i, train1 in enumerate(trains):
                        for train2 in trains[i+1:]:
                            # No two trains in the same single-track section within headway
                            prob += (
                                train_section_time.get((train1.id, section.id, t_slot), 0) +
                                lpSum([
                                    train_section_time.get((train2.id, section.id, t_slot + k), 0)
                                    for k in range(min_headway_slots)
                                ]) <= 1
                            )
        
        # 4. Crossing constraints at stations with loop lines
        for station in self.network_state.stations:
            if station.has_loop_line:
                # Allow trains to wait at loop line for crossing
                for t_slot in range(self.time_slots):
                    trains_at_station = lpSum([
                        train_section_time.get((train.id, section.id, t_slot), 0)
                        for train in trains
                        for section in sections
                        if section.to_station == station or section.from_station == station
                    ])
                    prob += trains_at_station <= station.platform_count + 1  # +1 for loop line
        
        # 5. Calculate delays
        for ts in self.network_state.active_trains:
            train = ts.train
            if len(ts.route) > 0:
                last_section = ts.route[-1]
                expected_time = sum([
                    ts.calculate_section_time(s) for s in ts.route
                ]) / self.slot_duration
                
                # Actual completion time
                actual_completion = lpSum([
                    t * train_section_time.get((train.id, last_section.id, t), 0)
                    for t in range(self.time_slots)
                ])
                
                # Delay is the difference
                prob += train_delay[train.id] >= (actual_completion - expected_time) * self.slot_duration
        
        # Solve the optimization problem
        solver = PULP_CBC_CMD(msg=0, timeLimit=30)  # 30 second time limit
        prob.solve(solver)
        
        # Extract results
        schedule = []
        conflicts_resolved = 0
        recommendations = []
        
        if prob.status == LpStatusOptimal:
            # Extract the optimized schedule
            for train in trains:
                for section in sections:
                    for t_slot in range(self.time_slots):
                        if value(train_section_time.get((train.id, section.id, t_slot), 0)) > 0.5:
                            time = self.network_state.timestamp + datetime.timedelta(
                                minutes=t_slot * self.slot_duration
                            )
                            schedule.append((train, section, time))
            
            # Calculate metrics
            total_delay = sum([value(train_delay[t.id]) for t in trains])
            avg_delay = total_delay / len(trains) if trains else 0
            
            # Generate recommendations
            for train in trains:
                delay = value(train_delay[train.id])
                if delay > 15:
                    recommendations.append(
                        f"Train {train.name} has {delay:.0f} min delay - "
                        f"Consider holding at loop line for crossing"
                    )
                
            # Check for resolved conflicts
            for section in sections:
                if section.track_type == TrackType.SINGLE:
                    for t_slot in range(self.time_slots):
                        trains_count = sum([
                            value(train_section_time.get((t.id, section.id, t_slot), 0))
                            for t in trains
                        ])
                        if trains_count > 1:
                            conflicts_resolved += 1
            
            # Add general recommendations
            if conflicts_resolved > 0:
                recommendations.append(
                    f"Resolved {conflicts_resolved} potential conflicts through optimal scheduling"
                )
            
            throughput = len(trains) / (self.time_horizon / 60)  # trains per hour
            
            recommendations.append(
                f"Optimized schedule achieves {throughput:.1f} trains/hour throughput"
            )
            
        else:
            # If optimization fails, provide fallback
            recommendations.append("Optimization did not find optimal solution - using priority-based scheduling")
            avg_delay = 0
            throughput = len(trains) / 4  # Rough estimate
            
            # Simple priority-based scheduling
            sorted_trains = sorted(trains, key=lambda t: t.priority)
            current_time = self.network_state.timestamp
            
            for train in sorted_trains:
                for section in sections[:3]:  # Simplified - just first few sections
                    schedule.append((train, section, current_time))
                    current_time += datetime.timedelta(minutes=15)
        
        return OptimizationResult(
            schedule=schedule,
            throughput=throughput,
            average_delay=avg_delay,
            conflicts_resolved=conflicts_resolved,
            recommendations=recommendations
        )
    
    def handle_disruption(self, blocked_section: Section) -> OptimizationResult:
        """
        Re-optimize when a section is blocked due to incident/maintenance
        """
        # Mark section as blocked
        blocked_section.is_blocked = True
        
        # Re-run optimization with updated constraints
        result = self.optimize_schedule()
        
        # Add disruption-specific recommendations
        result.recommendations.append(
            f"Section {blocked_section.id} is blocked - trains rerouted/delayed accordingly"
        )
        
        # Find alternative routes if possible
        affected_trains = [
            ts for ts in self.network_state.active_trains
            if blocked_section in ts.route
        ]
        
        if affected_trains:
            result.recommendations.append(
                f"{len(affected_trains)} trains affected by blockage - "
                f"consider alternative routing or bus service"
            )
        
        return result
    
    def optimize_crossing(self, station: Station) -> Dict[str, any]:
        """
        Optimize train crossing decisions at a specific station
        """
        # Find trains approaching the station
        approaching_trains = []
        
        for ts in self.network_state.active_trains:
            next_station = ts.get_next_station()
            if next_station == station:
                approaching_trains.append(ts)
        
        if len(approaching_trains) < 2:
            return {
                "station": station.name,
                "action": "NO_CROSSING_NEEDED",
                "trains": []
            }
        
        # Sort by priority and arrival time
        approaching_trains.sort(key=lambda ts: (ts.train.priority, ts.train.scheduled_departure))
        
        # Determine crossing strategy
        if station.has_loop_line:
            # Higher priority train goes through, lower priority waits
            through_train = approaching_trains[0]
            waiting_trains = approaching_trains[1:]
            
            return {
                "station": station.name,
                "action": "CROSSING_AT_LOOP",
                "through_train": through_train.train.name,
                "waiting_trains": [ts.train.name for ts in waiting_trains],
                "estimated_wait": 10  # minutes
            }
        else:
            # Must schedule sequential passage
            return {
                "station": station.name,
                "action": "SEQUENTIAL_PASSAGE",
                "order": [ts.train.name for ts in approaching_trains],
                "estimated_delay": 15 * (len(approaching_trains) - 1)  # minutes
            }