"""
PipelineScript - Human-Readable ML Pipeline Language
====================================================

A revolutionary DSL (Domain-Specific Language) for creating, debugging, 
and visualizing machine learning pipelines with simple, intuitive syntax.

Example:
    load data.csv
    clean missing
    split 80/20
    train xgboost
    evaluate
    export model.pkl

Features:
    - Human-readable syntax
    - Interactive debugging
    - Pipeline visualization
    - Step-by-step execution
    - Automatic error handling
    - Model export/import

Author: Idriss Bado
License: MIT
Version: 0.1.1
"""

from .parser import PipelineParser
from .compiler import PipelineCompiler
from .executor import PipelineExecutor
from .debugger import PipelineDebugger
from .visualizer import PipelineVisualizer
from .pipeline import Pipeline

__version__ = "0.1.0"
__author__ = "Idriss Bado"
__all__ = [
    "Pipeline",
    "PipelineParser",
    "PipelineCompiler", 
    "PipelineExecutor",
    "PipelineDebugger",
    "PipelineVisualizer",
    "run",
    "parse",
    "compile",
    "debug"
]


def run(script: str, debug: bool = False, visualize: bool = False):
    """
    Run a PipelineScript.
    
    Args:
        script: PipelineScript code (string or filepath)
        debug: Enable interactive debugging
        visualize: Show pipeline visualization
        
    Returns:
        Pipeline execution result
        
    Example:
        >>> result = run('''
        ...     load data.csv
        ...     train xgboost
        ...     evaluate
        ... ''')
    """
    pipeline = Pipeline()
    
    # Check if script is a filepath
    try:
        with open(script, 'r') as f:
            script = f.read()
    except (FileNotFoundError, OSError):
        pass  # Treat as raw script
    
    # Parse and compile
    parser = PipelineParser()
    ast = parser.parse(script)
    
    compiler = PipelineCompiler()
    compiled = compiler.compile(ast)
    
    # Visualize if requested
    if visualize:
        visualizer = PipelineVisualizer()
        visualizer.visualize_pipeline(ast)
    
    # Execute with or without debugging
    if debug:
        debugger = PipelineDebugger()
        return debugger.debug(compiled)
    else:
        executor = PipelineExecutor()
        return executor.execute(compiled)


def parse(script: str):
    """Parse PipelineScript into AST."""
    parser = PipelineParser()
    return parser.parse(script)


def compile(ast):
    """Compile AST into executable pipeline."""
    compiler = PipelineCompiler()
    return compiler.compile(ast)


def debug(script: str):
    """Run script in interactive debug mode."""
    return run(script, debug=True)
