"""
Pipeline Debugger - Interactive Debugging
=========================================

Step-through debugging with breakpoints and variable inspection.
"""

from typing import List, Dict, Any, Optional
import cmd

from .compiler import CompiledStep
from .executor import PipelineExecutor, ExecutionContext


class PipelineDebugger(cmd.Cmd):
    """Interactive debugger for ML pipelines."""
    
    intro = """
╔════════════════════════════════════════════╗
║   PipelineScript Interactive Debugger    ║
╚════════════════════════════════════════════╝

Type 'help' for available commands.
Type 'run' to start execution.
"""
    
    prompt = "(pdb) "
    
    def __init__(self):
        super().__init__()
        self.steps: List[CompiledStep] = []
        self.executor = PipelineExecutor()
        self.current_step = 0
        self.breakpoints = set()
        self.running = False
    
    def debug(self, steps: List[CompiledStep]):
        """
        Start interactive debugging session.
        
        Args:
            steps: Compiled pipeline steps
        """
        self.steps = steps
        self.current_step = 0
        self.running = False
        
        print(f"\nLoaded {len(steps)} pipeline steps:")
        for i, step in enumerate(steps):
            print(f"  {i+1}. {step.name}")
        print()
        
        self.cmdloop()
        
        return self.executor.get_context()
    
    # ===== Debugger Commands =====
    
    def do_run(self, arg):
        """Run pipeline until completion or breakpoint."""
        self.running = True
        
        while self.current_step < len(self.steps) and self.running:
            if self.current_step in self.breakpoints:
                print(f"\n🔴 Breakpoint at step {self.current_step + 1}")
                self.running = False
                self._show_step()
                break
            
            self._execute_current_step()
        
        if self.current_step >= len(self.steps):
            print("\n✅ Pipeline execution completed!")
            self._show_results()
    
    def do_step(self, arg):
        """Execute next step (alias: s, next, n)."""
        if self.current_step >= len(self.steps):
            print("⚠️  Pipeline execution completed. No more steps.")
            return
        
        self._execute_current_step()
    
    do_s = do_next = do_n = do_step
    
    def do_continue(self, arg):
        """Continue execution (alias: c, cont)."""
        self.do_run(arg)
    
    do_c = do_cont = do_continue
    
    def do_break(self, arg):
        """Set breakpoint at step number (alias: b)."""
        try:
            step_num = int(arg) - 1
            if 0 <= step_num < len(self.steps):
                self.breakpoints.add(step_num)
                print(f"🔴 Breakpoint set at step {step_num + 1}")
            else:
                print(f"⚠️  Invalid step number. Range: 1-{len(self.steps)}")
        except ValueError:
            print("⚠️  Usage: break <step_number>")
    
    do_b = do_break
    
    def do_clear(self, arg):
        """Clear breakpoint at step number."""
        try:
            step_num = int(arg) - 1
            if step_num in self.breakpoints:
                self.breakpoints.remove(step_num)
                print(f"Cleared breakpoint at step {step_num + 1}")
            else:
                print(f"⚠️  No breakpoint at step {step_num + 1}")
        except ValueError:
            print("⚠️  Usage: clear <step_number>")
    
    def do_list(self, arg):
        """List all pipeline steps (alias: l, ls)."""
        print("\nPipeline Steps:")
        print("=" * 50)
        
        for i, step in enumerate(self.steps):
            marker = "→" if i == self.current_step else " "
            bp_marker = "🔴" if i in self.breakpoints else "  "
            print(f"{bp_marker} {marker} {i+1}. {step.name}")
        
        print("=" * 50)
    
    do_l = do_ls = do_list
    
    def do_context(self, arg):
        """Show current execution context (alias: ctx, vars)."""
        context = self.executor.get_context()
        
        print("\n📊 Execution Context:")
        print("=" * 50)
        
        # Show data
        if context['data'] is not None:
            data = context['data']
            if hasattr(data, 'shape'):
                print(f"  data: DataFrame {data.shape}")
                print(f"    columns: {list(data.columns)}")
            else:
                print(f"  data: {type(data).__name__}")
        
        # Show model
        if context['model'] is not None:
            model = context['model']
            print(f"  model: {type(model).__name__}")
        
        # Show metrics
        if context['metrics']:
            print(f"  metrics: {context['metrics']}")
        
        # Show train/test split
        if context.get('X_train') is not None:
            print(f"  X_train: {context['X_train'].shape}")
            print(f"  X_test: {context['X_test'].shape}")
        
        # Show log
        if context['log']:
            print(f"\n  Recent log entries:")
            for entry in context['log'][-3:]:
                print(f"    • {entry}")
        
        print("=" * 50)
    
    do_ctx = do_vars = do_context
    
    def do_inspect(self, arg):
        """Inspect a variable (alias: i, print, p)."""
        context = self.executor.get_context()
        
        if not arg:
            self.do_context(arg)
            return
        
        value = context.get(arg)
        
        if value is None:
            print(f"⚠️  Variable '{arg}' not found")
        else:
            print(f"\n{arg}: {type(value).__name__}")
            
            if hasattr(value, 'shape'):
                print(f"  Shape: {value.shape}")
                if hasattr(value, 'head'):
                    print("\n  Preview:")
                    print(value.head())
            else:
                print(f"  Value: {value}")
    
    do_i = do_print = do_p = do_inspect
    
    def do_restart(self, arg):
        """Restart pipeline from beginning."""
        self.executor.reset()
        self.current_step = 0
        print("\n🔄 Pipeline restarted")
    
    def do_quit(self, arg):
        """Quit debugger (alias: q, exit)."""
        print("\n👋 Exiting debugger...")
        return True
    
    do_q = do_exit = do_quit
    
    def do_help(self, arg):
        """Show help for commands."""
        if not arg:
            print("""
Available Commands:
══════════════════════════════════════════════
  run, r            - Run until completion/breakpoint
  step, s, next, n  - Execute next step
  continue, c       - Continue execution
  break, b <num>    - Set breakpoint at step
  clear <num>       - Clear breakpoint
  list, l, ls       - List all steps
  context, ctx      - Show execution context
  inspect, i <var>  - Inspect variable
  restart           - Restart from beginning
  quit, q, exit     - Quit debugger
  help [command]    - Show help
══════════════════════════════════════════════
""")
        else:
            super().do_help(arg)
    
    do_r = do_run
    
    # ===== Helper Methods =====
    
    def _execute_current_step(self):
        """Execute the current step."""
        if self.current_step >= len(self.steps):
            return
        
        step = self.steps[self.current_step]
        
        print(f"\n▶️  Step {self.current_step + 1}: {step.name}")
        
        try:
            self.executor.execute_step(step)
            
            # Show log
            context = self.executor.get_context()
            if context['log']:
                print(f"   {context['log'][-1]}")
            
            self.current_step += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.running = False
    
    def _show_step(self):
        """Show current step info."""
        if self.current_step >= len(self.steps):
            return
        
        step = self.steps[self.current_step]
        print(f"\nCurrent step: {self.current_step + 1}. {step.name}")
    
    def _show_results(self):
        """Show final results."""
        context = self.executor.get_context()
        
        print("\n" + "=" * 50)
        print("📊 FINAL RESULTS")
        print("=" * 50)
        
        if context['metrics']:
            print("\n📈 Metrics:")
            for key, value in context['metrics'].items():
                if key != 'report':
                    print(f"  {key}: {value}")
        
        if context['log']:
            print("\n📝 Execution Log:")
            for entry in context['log']:
                print(f"  • {entry}")
        
        print("=" * 50)


def debug_pipeline(steps: List[CompiledStep]):
    """Convenience function to start debugging."""
    debugger = PipelineDebugger()
    return debugger.debug(steps)
