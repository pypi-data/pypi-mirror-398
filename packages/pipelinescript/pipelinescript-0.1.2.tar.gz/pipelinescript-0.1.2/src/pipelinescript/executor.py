"""
Pipeline Executor - Execute Compiled Pipeline
=============================================

Executes compiled pipeline steps with context management.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import time

from .compiler import CompiledStep


@dataclass
class ExecutionContext:
    """Pipeline execution context."""
    data: Any = None
    model: Any = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    log: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def __getitem__(self, key):
        """Allow dict-like access."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.variables.get(key)
    
    def __setitem__(self, key, value):
        """Allow dict-like assignment."""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.variables[key] = value
    
    def get(self, key, default=None):
        """Get value with default."""
        try:
            return self[key]
        except (AttributeError, KeyError):
            return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'data': self.data,
            'model': self.model,
            'metrics': self.metrics,
            'log': self.log,
            **self.variables
        }


@dataclass
class ExecutionResult:
    """Result of pipeline execution."""
    success: bool
    context: ExecutionContext
    duration: float
    error: Optional[str] = None
    
    def __repr__(self):
        status = "✅ Success" if self.success else "❌ Failed"
        return f"<ExecutionResult: {status} ({self.duration:.2f}s)>"


class PipelineExecutor:
    """Executes compiled pipeline steps."""
    
    def __init__(self):
        self.context = ExecutionContext()
    
    def execute(self, steps: List[CompiledStep], 
                context: Optional[ExecutionContext] = None) -> ExecutionResult:
        """
        Execute compiled pipeline steps.
        
        Args:
            steps: List of compiled steps
            context: Optional execution context
            
        Returns:
            Execution result with context and metrics
        """
        if context is None:
            context = ExecutionContext()
        
        self.context = context
        start_time = time.time()
        
        try:
            for i, step in enumerate(steps):
                print(f"[{i+1}/{len(steps)}] Executing: {step.name}...")
                
                # Execute step
                context = step.function(context)
                
                # Show log if any
                if context['log'] and len(context['log']) > i:
                    print(f"    {context['log'][-1]}")
            
            duration = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                context=context,
                duration=duration
            )
        
        except Exception as e:
            duration = time.time() - start_time
            
            return ExecutionResult(
                success=False,
                context=context,
                duration=duration,
                error=str(e)
            )
    
    def execute_step(self, step: CompiledStep) -> ExecutionContext:
        """Execute a single step."""
        self.context = step.function(self.context)
        return self.context
    
    def get_context(self) -> ExecutionContext:
        """Get current execution context."""
        return self.context
    
    def reset(self):
        """Reset execution context."""
        self.context = ExecutionContext()
