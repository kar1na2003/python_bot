"""
Visualization script to plot heuristic tuning results from CSV files.
Creates charts for performance trends and weight changes.
"""
import argparse
from pathlib import Path
from typing import List
import csv


def plot_performance_trend(csv_path: Path, output_prefix: str = None):
    """Plot performance metrics over iterations"""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. Install with: pip install matplotlib")
        return
    
    if output_prefix is None:
        output_prefix = str(csv_path.parent / "plot_performance")
    
    iterations = []
    win_rates = []
    labels = []
    
    with csv_path.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iterations.append(int(row["iteration"]))
            win_rates.append(float(row.get("win_rate", 0)))
            labels.append(row.get("label", ""))
    
    if not iterations:
        print(f"No data found in {csv_path}")
        return
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Win rate trend
    ax1.plot(iterations, win_rates, marker="o", linestyle="-", linewidth=2, markersize=6)
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Win Rate")
    ax1.set_title("Win Rate Trend Over Iterations")
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 1])
    
    # Mark before/after boundary if applicable
    before_count = sum(1 for l in labels if "current" in l.lower())
    if before_count > 0 and before_count < len(iterations):
        ax1.axvline(x=before_count + 0.5, color="red", linestyle="--", alpha=0.5, label="Tuning Start")
        ax1.legend()
    
    # Games vs iteration
    games_run = []
    with csv_path.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            games_run.append(int(row.get("games_run", 0)))
    
    ax2.bar(iterations, games_run, color="steelblue", alpha=0.7)
    ax2.set_xlabel("Iteration")
    ax2.set_ylabel("Games Run")
    ax2.set_title("Games Run Per Iteration")
    ax2.grid(True, alpha=0.3, axis="y")
    
    plt.tight_layout()
    output_file = f"{output_prefix}.png"
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"[OK] Performance plot saved to {output_file}")
    plt.close()


def plot_weight_changes(csv_path: Path, output_prefix: str = None):
    """Plot heuristic weight changes over iterations"""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. Install with: pip install matplotlib")
        return
    
    if output_prefix is None:
        output_prefix = str(csv_path.parent / "plot_weights")
    
    data = {}
    iterations = []
    
    with csv_path.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iteration = int(row["iteration"])
            iterations.append(iteration)
            label = row.get("label", "")
            
            # Extract all weight columns (skip iteration, timestamp, label)
            for key, value in row.items():
                if key not in ["iteration", "timestamp", "label"] and value:
                    if key not in data:
                        data[key] = []
                    try:
                        data[key].append(float(value))
                    except ValueError:
                        data[key].append(None)
    
    if not data:
        print(f"No weight data found in {csv_path}")
        return
    
    # Create subplot for top weights by variance
    weights_variance = {k: (max(v) - min(v)) if all(x is not None for x in v) else 0 
                       for k, v in data.items()}
    top_weights = sorted(weights_variance.items(), key=lambda x: x[1], reverse=True)[:6]
    
    fig, axes = plt.subplots(len(top_weights) if len(top_weights) > 0 else 1, 1, 
                            figsize=(12, 3 * max(len(top_weights), 1)))
    if len(top_weights) == 1:
        axes = [axes]
    
    for ax, (weight_name, _) in zip(axes, top_weights):
        values = data.get(weight_name, [])
        valid_iterations = [i for i, v in zip(iterations, values) if v is not None]
        valid_values = [v for v in values if v is not None]
        
        ax.plot(valid_iterations, valid_values, marker="o", linestyle="-", linewidth=2, markersize=6)
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Weight Value")
        ax.set_title(f"Heuristic Weight: {weight_name}")
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = f"{output_prefix}.png"
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"[OK] Weights plot saved to {output_file}")
    plt.close()


def generate_html_dashboard(reports_dir: Path):
    """Generate an HTML dashboard summarizing all results"""
    html_path = reports_dir / "dashboard.html"
    
    # Find latest CSV files
    perf_csv = None
    weights_csv = None
    for csv_file in reports_dir.glob("performance_*.csv"):
        if perf_csv is None or csv_file.stat().st_mtime > perf_csv.stat().st_mtime:
            perf_csv = csv_file
    
    for csv_file in reports_dir.glob("heuristic_weights_*.csv"):
        if weights_csv is None or csv_file.stat().st_mtime > weights_csv.stat().st_mtime:
            weights_csv = csv_file
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Heuristic Tuning Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            h1 { color: #333; }
            .container { background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #4CAF50; color: white; }
            tr:hover { background-color: #f5f5f5; }
            .metric { font-size: 24px; font-weight: bold; color: #4CAF50; }
            .improvement { color: #2196F3; }
            img { max-width: 100%; height: auto; margin-top: 20px; border: 1px solid #ddd; }
        </style>
    </head>
    <body>
        <h1>Heuristic Tuning Analysis Dashboard</h1>
        
        <div class="container">
            <h2>Analysis Summary</h2>
            <p>Generated: """ + str(Path(__file__).parent) + """</p>
            <p>This dashboard shows results from the heuristic analysis and tuning pipeline.</p>
        </div>
        
        <div class="container">
            <h2>Reports Generated</h2>
            <ul>
    """
    
    for csv_file in reports_dir.glob("*.csv"):
        html_content += f"<li><a href='{csv_file.name}'>{csv_file.name}</a></li>\n"
    
    for txt_file in reports_dir.glob("*.txt"):
        html_content += f"<li><a href='{txt_file.name}'>{txt_file.name}</a></li>\n"
    
    html_content += """
            </ul>
        </div>
        
        <div class="container">
            <h2>Next Steps</h2>
            <ol>
                <li>Review the CSV files for detailed metrics</li>
                <li>Run visualization with: <code>python visualize_results.py --csv performance_*.csv</code></li>
                <li>Analyze weight changes in heuristic_weights_*.csv</li>
                <li>Deploy best heuristic if improvements are significant</li>
            </ol>
        </div>
    </body>
    </html>
    """
    
    with html_path.open("w") as f:
        f.write(html_content)
    
    print(f"[OK] HTML dashboard saved to {html_path}")


def main():
    parser = argparse.ArgumentParser(description="Visualize heuristic tuning results")
    parser.add_argument("--csv", type=Path, 
                       help="Path to CSV file to visualize")
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"),
                       help="Reports directory (default: reports/)")
    parser.add_argument("--type", choices=["performance", "weights", "all"], default="all",
                       help="Type of visualization (default: all)")
    
    args = parser.parse_args()
    
    if args.csv:
        # Visualize specific CSV
        if args.csv.name.startswith("performance"):
            plot_performance_trend(args.csv)
        elif args.csv.name.startswith("heuristic_weights"):
            plot_weight_changes(args.csv)
        else:
            print("Unable to determine CSV type. Name should start with 'performance' or 'heuristic_weights'")
    else:
        # Generate report directory visualizations
        if not args.reports_dir.exists():
            print(f"Reports directory not found: {args.reports_dir}")
            return
        
        perf_csv = None
        weights_csv = None
        
        # Find latest files
        for csv_file in args.reports_dir.glob("performance_*.csv"):
            if perf_csv is None or csv_file.stat().st_mtime > perf_csv.stat().st_mtime:
                perf_csv = csv_file
        
        for csv_file in args.reports_dir.glob("heuristic_weights_*.csv"):
            if weights_csv is None or csv_file.stat().st_mtime > weights_csv.stat().st_mtime:
                weights_csv = csv_file
        
        if args.type in ["performance", "all"]:
            if perf_csv:
                plot_performance_trend(perf_csv)
            else:
                print("No performance CSV files found")
        
        if args.type in ["weights", "all"]:
            if weights_csv:
                plot_weight_changes(weights_csv)
            else:
                print("No weights CSV files found")
        
        # Generate HTML dashboard
        generate_html_dashboard(args.reports_dir)


if __name__ == "__main__":
    main()
