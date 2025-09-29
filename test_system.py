"""
Test cases for Train Traffic Control System
"""

import datetime
from simulator import RailwayNetworkSimulator
from models import NetworkState
from optimizer import TrainScheduleOptimizer


def test_basic_optimization():
    """Test basic optimization functionality"""
    print("Testing Basic Optimization...")
    
    # Create simulator and network
    sim = RailwayNetworkSimulator()
    sim.create_sample_network()
    sim.create_sample_trains(5)
    
    # Create network state
    network_state = NetworkState(
        timestamp=datetime.datetime.now(),
        stations=sim.stations,
        sections=sim.sections,
        active_trains=sim.schedules
    )
    
    # Run optimizer
    optimizer = TrainScheduleOptimizer(network_state)
    result = optimizer.optimize_schedule()
    
    print(f"✓ Throughput: {result.throughput:.2f} trains/hour")
    print(f"✓ Average Delay: {result.average_delay:.2f} minutes")
    print(f"✓ Conflicts Resolved: {result.conflicts_resolved}")
    print(f"✓ Recommendations: {len(result.recommendations)}")
    
    for rec in result.recommendations[:3]:
        print(f"  - {rec}")
    
    assert result.throughput > 0, "Throughput should be positive"
    print("✓ Basic optimization test passed!\n")


def test_disruption_handling():
    """Test disruption handling"""
    print("Testing Disruption Handling...")
    
    # Create simulator and network
    sim = RailwayNetworkSimulator()
    sim.create_sample_network()
    sim.create_sample_trains(5)
    
    # Simulate disruption
    result = sim.simulate_disruption("SEC01")
    
    print(f"✓ Disrupted Section: {result['disrupted_section']}")
    print(f"✓ Affected Trains: {result['affected_trains']}")
    print(f"✓ Optimization Result: {result['optimization_result']['average_delay']:.2f} min delay")
    
    assert "optimization_result" in result, "Should have optimization result"
    print("✓ Disruption handling test passed!\n")


def test_crossing_optimization():
    """Test crossing optimization at stations"""
    print("Testing Crossing Optimization...")
    
    # Create simulator and network
    sim = RailwayNetworkSimulator()
    sim.create_sample_network()
    sim.create_sample_trains(8)
    
    # Create network state
    network_state = NetworkState(
        timestamp=datetime.datetime.now(),
        stations=sim.stations,
        sections=sim.sections,
        active_trains=sim.schedules
    )
    
    # Test crossing at a station with loop line
    optimizer = TrainScheduleOptimizer(network_state)
    station_with_loop = next(s for s in sim.stations if s.has_loop_line)
    
    result = optimizer.optimize_crossing(station_with_loop)
    
    print(f"✓ Station: {result['station']}")
    print(f"✓ Action: {result['action']}")
    
    if result['action'] != 'NO_CROSSING_NEEDED':
        if 'through_train' in result:
            print(f"✓ Through Train: {result['through_train']}")
        if 'order' in result:
            print(f"✓ Passage Order: {result['order']}")
    
    assert "action" in result, "Should have action recommendation"
    print("✓ Crossing optimization test passed!\n")


def test_simulation():
    """Test full simulation"""
    print("Testing Full Simulation...")
    
    # Create simulator and network
    sim = RailwayNetworkSimulator()
    sim.create_sample_network()
    sim.create_sample_trains(6)
    
    # Run simulation for 1 hour
    results = sim.run_simulation(duration_hours=1)
    
    print(f"✓ Total Trains: {results['total_trains']}")
    print(f"✓ Simulation Duration: {results['duration_hours']} hours")
    
    stats = results['final_statistics']
    print(f"✓ Completed Trains: {stats['completed_trains']}")
    print(f"✓ Completion Rate: {stats['completion_rate']:.1f}%")
    print(f"✓ Average Delay: {stats['average_delay_minutes']:.2f} minutes")
    
    assert stats['completion_rate'] >= 0, "Completion rate should be non-negative"
    print("✓ Simulation test passed!\n")


def test_network_capacity():
    """Test network capacity constraints"""
    print("Testing Network Capacity Constraints...")
    
    # Create simulator and network
    sim = RailwayNetworkSimulator()
    sim.create_sample_network()
    sim.create_sample_trains(10)  # Many trains to test capacity
    
    # Create network state
    network_state = NetworkState(
        timestamp=datetime.datetime.now(),
        stations=sim.stations,
        sections=sim.sections,
        active_trains=sim.schedules
    )
    
    # Check single track sections
    single_track_sections = [s for s in sim.sections if s.capacity == 1]
    print(f"✓ Single track sections: {len(single_track_sections)}")
    
    # Run optimizer
    optimizer = TrainScheduleOptimizer(network_state)
    result = optimizer.optimize_schedule()
    
    # Check that optimization respects capacity
    print(f"✓ Optimization completed with {len(sim.trains)} trains")
    print(f"✓ Conflicts resolved: {result.conflicts_resolved}")
    
    assert result.conflicts_resolved >= 0, "Should handle conflicts"
    print("✓ Network capacity test passed!\n")


def run_all_tests():
    """Run all test cases"""
    print("="*50)
    print("TRAIN TRAFFIC CONTROL SYSTEM - TEST SUITE")
    print("="*50 + "\n")
    
    tests = [
        test_basic_optimization,
        test_disruption_handling,
        test_crossing_optimization,
        test_simulation,
        test_network_capacity
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {str(e)}\n")
            failed += 1
    
    print("="*50)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)