#!/usr/bin/env python3
"""
Visualization script for benchmark results
"""
import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys

# Set matplotlib to use non-interactive backend
plt.switch_backend('Agg')


def load_benchmark_results(file_path="logs/benchmark_results.json"):
    """Load benchmark results from JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data['results']
    except FileNotFoundError:
        print(f"Results file {file_path} not found. Please run benchmark first.")
        return None
    except Exception as e:
        print(f"Error loading results: {e}")
        return None


def create_comparison_charts(results, output_dir="logs"):
    """Create comparison charts from benchmark results"""
    if not results:
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract data
    backends = [r['backend_name'] for r in results]
    messages_per_sec = [r['messages_per_second'] for r in results]
    memory_usage = [r['memory_usage'] for r in results]
    cpu_usage = [r['cpu_usage'] for r in results]
    add_rule_time = [r['add_rule_time'] * 1000 for r in results]  # Convert to ms
    process_time = [r['process_message_time'] * 1000 for r in results]  # Convert to ms
    
    # Create comprehensive comparison chart
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('IoT Rules Engine Storage Backend Comparison', fontsize=16, fontweight='bold')
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    # 1. Messages per Second
    bars1 = ax1.bar(backends, messages_per_sec, color=colors[:len(backends)], alpha=0.8)
    ax1.set_ylabel('Messages per Second')
    ax1.set_title('Throughput Performance')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars1, messages_per_sec):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + max(messages_per_sec)*0.01,
                f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Memory Usage
    bars2 = ax2.bar(backends, memory_usage, color=colors[:len(backends)], alpha=0.8)
    ax2.set_ylabel('Memory Usage (MB)')
    ax2.set_title('Memory Consumption')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars2, memory_usage):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + max(memory_usage)*0.01,
                f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. CPU Usage
    bars3 = ax3.bar(backends, cpu_usage, color=colors[:len(backends)], alpha=0.8)
    ax3.set_ylabel('CPU Usage (%)')
    ax3.set_title('CPU Utilization')
    ax3.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars3, cpu_usage):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + max(cpu_usage)*0.01,
                f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # 4. Response Times
    x = np.arange(len(backends))
    width = 0.35
    
    bars4a = ax4.bar(x - width/2, add_rule_time, width, label='Add Rule Time', 
                     color=colors[0], alpha=0.8)
    bars4b = ax4.bar(x + width/2, process_time, width, label='Process Message Time', 
                     color=colors[1], alpha=0.8)
    
    ax4.set_ylabel('Time (ms)')
    ax4.set_title('Response Times')
    ax4.set_xticks(x)
    ax4.set_xticklabels(backends)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars4a, add_rule_time):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + max(add_rule_time)*0.01,
                f'{value:.2f}', ha='center', va='bottom', fontsize=8)
    
    for bar, value in zip(bars4b, process_time):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + max(process_time)*0.01,
                f'{value:.2f}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    chart_path = os.path.join(output_dir, 'storage_backend_comparison.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Comparison chart saved to: {chart_path}")
    
    # Create individual performance overview chart
    create_performance_overview(results, output_dir)


def create_performance_overview(results, output_dir):
    """Create a comprehensive performance overview chart"""
    if not results:
        return
    
    backends = [r['backend_name'] for r in results]
    messages_per_sec = [r['messages_per_second'] for r in results]
    
    # Create a nice looking single metric chart
    plt.figure(figsize=(12, 8))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    bars = plt.bar(backends, messages_per_sec, color=colors[:len(backends)], 
                   alpha=0.8, edgecolor='black', linewidth=1.5)
    
    plt.ylabel('Messages Processed per Second', fontsize=14, fontweight='bold')
    plt.title('IoT Rules Engine Performance Comparison\nStorage Backend Throughput', 
              fontsize=16, fontweight='bold', pad=20)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, value in zip(bars, messages_per_sec):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + max(messages_per_sec)*0.01,
                f'{value:.1f}\nmsg/sec', ha='center', va='bottom', 
                fontweight='bold', fontsize=12)
    
    # Customize appearance
    plt.xticks(fontsize=12, fontweight='bold')
    plt.yticks(fontsize=12)
    
    # Add some styling
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_linewidth(2)
    plt.gca().spines['bottom'].set_linewidth(2)
    
    plt.tight_layout()
    overview_path = os.path.join(output_dir, 'performance_overview.png')
    plt.savefig(overview_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Performance overview chart saved to: {overview_path}")


def create_detailed_metrics_chart(results, output_dir):
    """Create detailed metrics comparison"""
    if not results:
        return
    
    backends = [r['backend_name'] for r in results]
    
    # Normalize metrics for radar chart
    metrics = {
        'Throughput': [r['messages_per_second'] for r in results],
        'Memory Efficiency': [100 - min(100, r['memory_usage'] * 10) for r in results],  # Inverted
        'CPU Efficiency': [100 - min(100, r['cpu_usage']) for r in results],  # Inverted
        'Add Rule Speed': [100 - min(100, r['add_rule_time'] * 10000) for r in results],  # Inverted
        'Process Speed': [100 - min(100, r['process_message_time'] * 1000) for r in results]  # Inverted
    }
    
    # Create radar chart
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]  # Close the plot
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, backend in enumerate(backends):
        values = [metrics[metric][i] for metric in metrics.keys()]
        values += values[:1]  # Close the plot
        
        ax.plot(angles, values, 'o-', linewidth=2, label=backend, color=colors[i])
        ax.fill(angles, values, alpha=0.25, color=colors[i])
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics.keys())
    ax.set_ylim(0, 100)
    ax.set_title('Detailed Performance Metrics\n(Higher is Better)', size=16, fontweight='bold', pad=30)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    
    plt.tight_layout()
    radar_path = os.path.join(output_dir, 'detailed_metrics_radar.png')
    plt.savefig(radar_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Detailed metrics radar chart saved to: {radar_path}")


def main():
    """Main function to create visualization charts"""
    print("Loading benchmark results...")
    results = load_benchmark_results()
    
    if results:
        print("Creating visualization charts...")
        create_comparison_charts(results)
        create_detailed_metrics_chart(results, "logs")
        print("\nVisualization complete!")
        print("Charts saved in the 'logs' directory:")
        print("  - storage_backend_comparison.png")
        print("  - performance_overview.png") 
        print("  - detailed_metrics_radar.png")
    else:
        print("No benchmark results found. Please run 'python scripts/benchmark.py' first.")


if __name__ == "__main__":
    main()
