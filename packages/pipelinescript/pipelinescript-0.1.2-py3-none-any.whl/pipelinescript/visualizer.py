"""
Pipeline Visualizer - Visual Pipeline Representation
===================================================

Visualize pipeline structure, execution flow, and results.
"""

from typing import List, Dict, Any, Optional
import io

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .parser import ASTNode
from .executor import ExecutionResult


class PipelineVisualizer:
    """Visualize ML pipelines."""
    
    def __init__(self):
        self.ascii_art = True
    
    def visualize_pipeline(self, ast: List[ASTNode], 
                          save_path: Optional[str] = None):
        """
        Visualize pipeline structure.
        
        Args:
            ast: Abstract Syntax Tree
            save_path: Optional path to save visualization
        """
        if HAS_MATPLOTLIB and not self.ascii_art:
            self._visualize_graphical(ast, save_path)
        else:
            self._visualize_ascii(ast)
    
    def _visualize_ascii(self, ast: List[ASTNode]):
        """Create ASCII art visualization."""
        print("\n" + "=" * 60)
        print("📊 PIPELINE VISUALIZATION")
        print("=" * 60)
        print()
        
        for i, node in enumerate(ast):
            # Command box
            cmd = node.command.upper()
            args_str = ' '.join(str(arg) for arg in node.args[:2])
            
            if i == 0:
                print("    START")
                print("      │")
            
            # Draw box
            print("      ▼")
            print("    ┌─" + "─" * (len(cmd) + len(args_str) + 2) + "┐")
            print(f"    │ {cmd} {args_str} │")
            print("    └─" + "─" * (len(cmd) + len(args_str) + 2) + "┘")
            
            if i < len(ast) - 1:
                print("      │")
        
        print("      │")
        print("      ▼")
        print("     END")
        print()
        print("=" * 60)
    
    def _visualize_graphical(self, ast: List[ASTNode], save_path: Optional[str]):
        """Create graphical visualization using matplotlib."""
        fig, ax = plt.subplots(figsize=(10, len(ast) * 1.5))
        
        # Draw pipeline steps
        for i, node in enumerate(ast):
            y = len(ast) - i
            
            # Draw box
            box = plt.Rectangle((0.2, y - 0.3), 0.6, 0.6, 
                               facecolor='lightblue', 
                               edgecolor='black', 
                               linewidth=2)
            ax.add_patch(box)
            
            # Add text
            text = f"{node.command.upper()}"
            if node.args:
                text += f"\n{node.args[0]}"
            
            ax.text(0.5, y, text, 
                   ha='center', va='center',
                   fontsize=10, fontweight='bold')
            
            # Draw arrow
            if i < len(ast) - 1:
                ax.arrow(0.5, y - 0.3, 0, -0.3,
                        head_width=0.05, head_length=0.1,
                        fc='black', ec='black')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, len(ast) + 1)
        ax.axis('off')
        ax.set_title('ML Pipeline Flow', fontsize=14, fontweight='bold')
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=150)
            print(f"💾 Saved pipeline visualization to {save_path}")
        else:
            plt.savefig('pipeline.png', bbox_inches='tight', dpi=150)
            print("💾 Saved pipeline visualization to pipeline.png")
        
        plt.close()
    
    def visualize_results(self, result: ExecutionResult, 
                         save_path: Optional[str] = None):
        """
        Visualize execution results.
        
        Args:
            result: Execution result
            save_path: Optional path to save visualization
        """
        if not HAS_MATPLOTLIB:
            self._print_results_ascii(result)
            return
        
        context = result.context
        metrics = context.metrics
        
        if not metrics:
            print("⚠️  No metrics to visualize")
            return
        
        # Create figure
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot 1: Metrics
        ax1 = axes[0]
        metric_names = list(metrics.keys())
        metric_values = [metrics[k] for k in metric_names if isinstance(metrics[k], (int, float))]
        
        if metric_values:
            ax1.bar(range(len(metric_values)), metric_values)
            ax1.set_xticks(range(len(metric_values)))
            ax1.set_xticklabels([k for k in metric_names if isinstance(metrics[k], (int, float))], 
                               rotation=45)
            ax1.set_title('Model Metrics')
            ax1.set_ylabel('Value')
        
        # Plot 2: Execution timeline
        ax2 = axes[1]
        log = context.log
        
        if log:
            ax2.barh(range(len(log)), [1] * len(log))
            ax2.set_yticks(range(len(log)))
            ax2.set_yticklabels([entry[:30] + '...' if len(entry) > 30 else entry 
                                for entry in log])
            ax2.set_title('Execution Steps')
            ax2.set_xlabel('Completed')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=150)
            print(f"💾 Saved results visualization to {save_path}")
        else:
            plt.savefig('results.png', bbox_inches='tight', dpi=150)
            print("💾 Saved results visualization to results.png")
        
        plt.close()
    
    def _print_results_ascii(self, result: ExecutionResult):
        """Print results in ASCII format."""
        print("\n" + "=" * 60)
        print("📊 EXECUTION RESULTS")
        print("=" * 60)
        
        if result.success:
            print("✅ Status: SUCCESS")
        else:
            print("❌ Status: FAILED")
            if result.error:
                print(f"   Error: {result.error}")
        
        print(f"⏱️  Duration: {result.duration:.2f}s")
        
        if result.context.metrics:
            print("\n📈 Metrics:")
            for key, value in result.context.metrics.items():
                if key != 'report' and isinstance(value, (int, float)):
                    print(f"   {key}: {value:.4f}")
        
        if result.context.log:
            print("\n📝 Execution Log:")
            for entry in result.context.log:
                print(f"   • {entry}")
        
        print("=" * 60)
    
    def create_pipeline_dag(self, ast: List[ASTNode]) -> str:
        """
        Create a DAG (Directed Acyclic Graph) representation.
        
        Args:
            ast: Abstract Syntax Tree
            
        Returns:
            DOT language representation
        """
        dot = ["digraph Pipeline {"]
        dot.append("  rankdir=TB;")
        dot.append("  node [shape=box, style=filled, fillcolor=lightblue];")
        dot.append("")
        
        # Add nodes
        for i, node in enumerate(ast):
            label = f"{node.command}"
            if node.args:
                label += f"\\n{node.args[0]}"
            
            dot.append(f'  step{i} [label="{label}"];')
        
        # Add edges
        for i in range(len(ast) - 1):
            dot.append(f"  step{i} -> step{i+1};")
        
        dot.append("}")
        
        return "\n".join(dot)
    
    def export_dag(self, ast: List[ASTNode], filepath: str = "pipeline.dot"):
        """Export pipeline as DOT file."""
        dag = self.create_pipeline_dag(ast)
        
        with open(filepath, 'w') as f:
            f.write(dag)
        
        print(f"💾 Exported pipeline DAG to {filepath}")
        print("   To visualize: dot -Tpng pipeline.dot -o pipeline.png")


def visualize(ast: List[ASTNode]):
    """Convenience function to visualize pipeline."""
    visualizer = PipelineVisualizer()
    visualizer.visualize_pipeline(ast)
