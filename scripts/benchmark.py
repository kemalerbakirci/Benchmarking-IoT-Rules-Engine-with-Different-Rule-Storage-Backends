#!/usr/bin/env python3
"""
Benchmark script for comparing different storage backends
"""
import time
import json
import random
import sys
import os
from typing import Dict, List, Any
import psutil

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from rules_engine.storage import InMemoryStorage, SQLiteStorage, RedisStorage
from rules_engine.engine import RulesEngine


class BenchmarkResult:
    """Container for benchmark results"""
    def __init__(self, backend_name: str):
        self.backend_name = backend_name
        self.add_rule_time = 0.0
        self.process_message_time = 0.0
        self.memory_usage = 0.0
        self.cpu_usage = 0.0
        self.messages_per_second = 0.0
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'backend_name': self.backend_name,
            'add_rule_time': self.add_rule_time,
            'process_message_time': self.process_message_time,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'messages_per_second': self.messages_per_second
        }


def create_test_rules() -> List[tuple]:
    """Create a set of test rules"""
    return [
        ('temperature > 25', 'High temperature alert'),
        ('humidity < 30', 'Low humidity warning'),
        ('pressure > 1013', 'High pressure detected'),
        ('temperature < 0', 'Freezing temperature alert'),
        ('humidity > 80', 'High humidity warning'),
        ('pressure < 950', 'Low pressure alert'),
        ('temperature > 40', 'Critical temperature'),
        ('humidity > 90', 'Excessive humidity'),
        ('pressure > 1050', 'Extreme pressure'),
        ('temperature < -10', 'Extreme cold')
    ]


def generate_test_messages(count: int) -> List[Dict[str, Any]]:
    """Generate random test messages"""
    messages = []
    for _ in range(count):
        message = {
            'temperature': random.uniform(-20, 50),
            'humidity': random.uniform(10, 100),
            'pressure': random.uniform(900, 1100),
            'timestamp': time.time()
        }
        messages.append(message)
    return messages


def benchmark_storage_backend(storage_class, name: str, num_rules: int = 10, num_messages: int = 1000) -> BenchmarkResult:
    """Benchmark a single storage backend"""
    print(f"\nBenchmarking {name}...")
    
    result = BenchmarkResult(name)
    
    # Initialize storage and engine
    try:
        storage = storage_class()
        engine = RulesEngine(storage)
    except Exception as e:
        print(f"Failed to initialize {name}: {e}")
        return result
    
    # Benchmark rule addition
    print(f"  Adding {num_rules} rules...")
    rules = create_test_rules()
    start_time = time.time()
    
    for i in range(num_rules):
        rule = rules[i % len(rules)]
        engine.add_rule(rule[0], rule[1])
    
    result.add_rule_time = time.time() - start_time
    
    # Generate test messages
    messages = generate_test_messages(num_messages)
    
    # Benchmark message processing
    print(f"  Processing {num_messages} messages...")
    process = psutil.Process()
    
    # Get initial system stats
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    cpu_times_start = process.cpu_times()
    
    start_time = time.time()
    
    for message in messages:
        engine.process_message(message)
    
    end_time = time.time()
    result.process_message_time = end_time - start_time
    result.messages_per_second = num_messages / result.process_message_time
    
    # Get final system stats
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    cpu_times_end = process.cpu_times()
    
    result.memory_usage = final_memory - initial_memory
    
    # Calculate CPU usage (simplified)
    cpu_time_used = (cpu_times_end.user - cpu_times_start.user) + (cpu_times_end.system - cpu_times_start.system)
    result.cpu_usage = (cpu_time_used / result.process_message_time) * 100 if result.process_message_time > 0 else 0
    
    print(f"  Results: {result.messages_per_second:.2f} msg/sec, {result.memory_usage:.2f} MB memory")
    
    return result


def run_benchmark() -> List[BenchmarkResult]:
    """Run benchmarks for all storage backends"""
    print("Starting IoT Rules Engine Benchmark")
    print("=" * 50)
    
    results = []
    
    # Test configurations
    backends = [
        (InMemoryStorage, "InMemory"),
        (SQLiteStorage, "SQLite"),
        (RedisStorage, "Redis")
    ]
    
    for storage_class, name in backends:
        try:
            result = benchmark_storage_backend(storage_class, name)
            results.append(result)
        except Exception as e:
            print(f"Error benchmarking {name}: {e}")
    
    return results


def save_results(results: List[BenchmarkResult]):
    """Save benchmark results to JSON file"""
    output_file = "logs/benchmark_results.json"
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Convert results to dictionary format
    results_data = {
        'timestamp': time.time(),
        'results': [result.to_dict() for result in results]
    }
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\nResults saved to {output_file}")


def print_summary(results: List[BenchmarkResult]):
    """Print benchmark summary"""
    print("\nBenchmark Summary")
    print("=" * 50)
    print(f"{'Backend':<15} {'Msg/Sec':<12} {'Memory (MB)':<12} {'CPU %':<10}")
    print("-" * 50)
    
    for result in results:
        print(f"{result.backend_name:<15} {result.messages_per_second:<12.2f} "
              f"{result.memory_usage:<12.2f} {result.cpu_usage:<10.2f}")


if __name__ == "__main__":
    results = run_benchmark()
    save_results(results)
    print_summary(results)
    print("\nBenchmark completed!")
    print("Run 'python scripts/visualize.py' to generate charts.")
