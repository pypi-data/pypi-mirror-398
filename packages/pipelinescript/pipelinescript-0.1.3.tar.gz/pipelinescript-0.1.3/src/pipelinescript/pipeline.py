"""
Pipeline - High-Level Pipeline API
==================================

User-friendly interface for creating and running ML pipelines.
"""

from typing import Any, Optional, Dict, List
import pandas as pd

from .parser import PipelineParser
from .compiler import PipelineCompiler
from .executor import PipelineExecutor, ExecutionResult
from .debugger import PipelineDebugger
from .visualizer import PipelineVisualizer


class Pipeline:
    """
    High-level ML Pipeline API.
    
    Example:
        >>> pipeline = Pipeline()
        >>> pipeline.load("data.csv")
        >>> pipeline.clean("missing")
        >>> pipeline.split(0.8, target="label")
        >>> pipeline.train("xgboost")
        >>> pipeline.evaluate()
        >>> pipeline.export("model.pkl")
    """
    
    def __init__(self):
        self.parser = PipelineParser()
        self.compiler = PipelineCompiler()
        self.executor = PipelineExecutor()
        self.visualizer = PipelineVisualizer()
        self.script_lines: List[str] = []
    
    # ===== Data Loading =====
    
    def load(self, filepath: str):
        """Load data from file."""
        self.script_lines.append(f"load {filepath}")
        return self
    
    def load_csv(self, filepath: str):
        """Load CSV file."""
        return self.load(filepath)
    
    def load_excel(self, filepath: str):
        """Load Excel file."""
        return self.load(filepath)
    
    # ===== Data Cleaning =====
    
    def clean(self, strategy: str = "missing"):
        """
        Clean data.
        
        Args:
            strategy: 'missing', 'duplicates', or 'outliers'
        """
        self.script_lines.append(f"clean {strategy}")
        return self
    
    def clean_missing(self):
        """Remove missing values."""
        return self.clean("missing")
    
    def clean_duplicates(self):
        """Remove duplicate rows."""
        return self.clean("duplicates")
    
    def clean_outliers(self):
        """Remove outliers."""
        return self.clean("outliers")
    
    # ===== Data Transformation =====
    
    def filter(self, condition: str):
        """Filter data based on condition."""
        self.script_lines.append(f"filter {condition}")
        return self
    
    def select(self, *columns):
        """Select specific columns."""
        cols = ' '.join(columns)
        self.script_lines.append(f"select {cols}")
        return self
    
    def encode(self):
        """Encode categorical variables."""
        self.script_lines.append("encode")
        return self
    
    def scale(self):
        """Scale numeric features."""
        self.script_lines.append("scale")
        return self
    
    # ===== Train/Test Split =====
    
    def split(self, train_size: float = 0.8, target: Optional[str] = None):
        """
        Split data into train/test sets.
        
        Args:
            train_size: Proportion for training (0.0-1.0)
            target: Target column name
        """
        if target:
            self.script_lines.append(f"split {train_size} --target {target}")
        else:
            ratio = f"{int(train_size*100)}/{int((1-train_size)*100)}"
            self.script_lines.append(f"split {ratio}")
        return self
    
    # ===== Model Training =====
    
    def train(self, model: str = "auto"):
        """
        Train model.
        
        Args:
            model: 'xgboost', 'random_forest', 'logistic', 'linear', or 'auto'
        """
        self.script_lines.append(f"train {model}")
        return self
    
    def train_xgboost(self):
        """Train XGBoost model."""
        return self.train("xgboost")
    
    def train_random_forest(self):
        """Train Random Forest model."""
        return self.train("random_forest")
    
    def train_logistic(self):
        """Train Logistic Regression model."""
        return self.train("logistic")
    
    # ===== Prediction & Evaluation =====
    
    def predict(self):
        """Make predictions."""
        self.script_lines.append("predict")
        return self
    
    def evaluate(self):
        """Evaluate model performance."""
        self.script_lines.append("evaluate")
        return self
    
    # ===== Model Export/Import =====
    
    def export(self, filepath: str = "model.pkl"):
        """Export trained model."""
        self.script_lines.append(f"export {filepath}")
        return self
    
    def save(self, filepath: str = "model.pkl"):
        """Alias for export."""
        return self.export(filepath)
    
    def import_model(self, filepath: str):
        """Import trained model."""
        self.script_lines.append(f"import {filepath}")
        return self
    
    # ===== Execution =====
    
    def run(self, debug: bool = False, visualize: bool = False) -> ExecutionResult:
        """
        Execute the pipeline.
        
        Args:
            debug: Enable interactive debugging
            visualize: Show pipeline visualization
            
        Returns:
            Execution result
        """
        script = '\n'.join(self.script_lines)
        
        # Parse
        ast = self.parser.parse(script)
        
        # Compile
        steps = self.compiler.compile(ast)
        
        # Visualize if requested
        if visualize:
            self.visualizer.visualize_pipeline(ast)
        
        # Execute
        if debug:
            debugger = PipelineDebugger()
            context = debugger.debug(steps)
            return ExecutionResult(
                success=True,
                context=context,
                duration=0.0
            )
        else:
            return self.executor.execute(steps)
    
    def run_debug(self) -> ExecutionResult:
        """Run with debugging enabled."""
        return self.run(debug=True)
    
    def run_visualize(self) -> ExecutionResult:
        """Run with visualization."""
        return self.run(visualize=True)
    
    # ===== Utility Methods =====
    
    def get_script(self) -> str:
        """Get generated PipelineScript."""
        return '\n'.join(self.script_lines)
    
    def print_script(self):
        """Print generated PipelineScript."""
        print("\n" + "=" * 60)
        print("📝 GENERATED PIPELINESCRIPT")
        print("=" * 60)
        print(self.get_script())
        print("=" * 60)
    
    def visualize(self):
        """Visualize pipeline structure."""
        script = '\n'.join(self.script_lines)
        ast = self.parser.parse(script)
        self.visualizer.visualize_pipeline(ast)
    
    def reset(self):
        """Reset pipeline."""
        self.script_lines = []
        self.executor.reset()
        return self


# ===== Quick Pipeline Builders =====

def quick_classification(data_path: str, target: str, 
                        model: str = "xgboost") -> ExecutionResult:
    """
    Quick classification pipeline.
    
    Example:
        >>> result = quick_classification("data.csv", "label", "xgboost")
    """
    pipeline = Pipeline()
    return (pipeline
            .load(data_path)
            .clean_missing()
            .split(0.8, target=target)
            .train(model)
            .evaluate()
            .run())


def quick_regression(data_path: str, target: str,
                    model: str = "random_forest") -> ExecutionResult:
    """
    Quick regression pipeline.
    
    Example:
        >>> result = quick_regression("data.csv", "price", "random_forest")
    """
    pipeline = Pipeline()
    return (pipeline
            .load(data_path)
            .clean_missing()
            .clean_outliers()
            .split(0.8, target=target)
            .scale()
            .train(model)
            .evaluate()
            .run())


def quick_train(data_path: str, target: str, 
               output: str = "model.pkl") -> ExecutionResult:
    """
    Quick train and export pipeline.
    
    Example:
        >>> result = quick_train("data.csv", "label", "model.pkl")
    """
    pipeline = Pipeline()
    return (pipeline
            .load(data_path)
            .clean_missing()
            .encode()
            .split(0.8, target=target)
            .train("auto")
            .evaluate()
            .export(output)
            .run())
