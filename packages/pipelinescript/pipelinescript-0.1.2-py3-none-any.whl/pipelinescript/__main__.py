"""
PipelineScript CLI
==================

Command-line interface for PipelineScript.
"""

import sys
import argparse
from pathlib import Path

from . import run, debug, parse
from .visualizer import PipelineVisualizer


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PipelineScript - Human-Readable ML Pipeline Language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pipelinescript run pipeline.psl
  pipelinescript debug pipeline.psl
  pipelinescript visualize pipeline.psl
  pipelinescript parse pipeline.psl

For more information: https://github.com/idrissbado/PipelineScript
        """
    )
    
    parser.add_argument(
        "command",
        choices=["run", "debug", "visualize", "parse", "version"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "filepath",
        nargs="?",
        help="Path to .psl script file"
    )
    
    parser.add_argument(
        "-v", "--visualize",
        action="store_true",
        help="Show visualization during execution"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file for visualization"
    )
    
    args = parser.parse_args()
    
    # Version command
    if args.command == "version":
        from . import __version__
        print(f"PipelineScript v{__version__}")
        return
    
    # Commands requiring filepath
    if not args.filepath:
        print(f"Error: '{args.command}' command requires a filepath")
        parser.print_help()
        sys.exit(1)
    
    filepath = Path(args.filepath)
    
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    # Read script
    with open(filepath, 'r') as f:
        script = f.read()
    
    # Execute command
    try:
        if args.command == "run":
            result = run(script, visualize=args.visualize)
            
            if result.success:
                print(f"\n✅ Pipeline completed successfully in {result.duration:.2f}s")
                
                if result.context.metrics:
                    print("\n📊 Metrics:")
                    for key, value in result.context.metrics.items():
                        if key != 'report' and isinstance(value, (int, float)):
                            print(f"  {key}: {value:.4f}")
            else:
                print(f"\n❌ Pipeline failed: {result.error}")
                sys.exit(1)
        
        elif args.command == "debug":
            debug(script)
        
        elif args.command == "visualize":
            ast = parse(script)
            visualizer = PipelineVisualizer()
            
            if args.output:
                visualizer.visualize_pipeline(ast, save_path=args.output)
            else:
                visualizer.visualize_pipeline(ast)
        
        elif args.command == "parse":
            ast = parse(script)
            print(f"\n✅ Parsed {len(ast)} commands:\n")
            
            for i, node in enumerate(ast, 1):
                args_str = ' '.join(str(arg) for arg in node.args)
                opts_str = ' '.join(f'--{k} {v}' for k, v in node.options.items())
                
                print(f"  {i}. {node.command} {args_str} {opts_str}".strip())
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
