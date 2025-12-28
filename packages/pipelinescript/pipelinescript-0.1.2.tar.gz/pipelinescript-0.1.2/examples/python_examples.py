"""
PipelineScript Examples - Python API
====================================
"""

# Example 1: Using the DSL directly
print("=" * 70)
print("EXAMPLE 1: Direct DSL Execution")
print("=" * 70)

from pipelinescript import run

script = """
load iris.csv
clean missing
split 80/20 --target species
train xgboost
evaluate
"""

result = run(script)

if result.success:
    print(f"\n✅ Pipeline completed in {result.duration:.2f}s")
    print(f"📊 Metrics: {result.context.metrics}")
else:
    print(f"\n❌ Pipeline failed: {result.error}")


# Example 2: Using the Pipeline API
print("\n" + "=" * 70)
print("EXAMPLE 2: Pipeline API (Method Chaining)")
print("=" * 70)

from pipelinescript import Pipeline

pipeline = (Pipeline()
    .load("iris.csv")
    .clean_missing()
    .encode()
    .split(0.8, target="species")
    .train("random_forest")
    .evaluate()
    .export("iris_model.pkl")
)

# Show generated script
pipeline.print_script()

# Execute
result = pipeline.run()

if result.success:
    print(f"\n✅ Success!")
    if result.context.metrics:
        print(f"📊 Accuracy: {result.context.metrics.get('accuracy', 'N/A')}")


# Example 3: Interactive Debugging
print("\n" + "=" * 70)
print("EXAMPLE 3: Interactive Debugging")
print("=" * 70)

from pipelinescript import debug

debug_script = """
load iris.csv
clean missing
split 80/20 --target species
train xgboost
evaluate
"""

print("To debug interactively, run:")
print("  result = debug(debug_script)")
print("\nDebugger commands:")
print("  step  - Execute next step")
print("  run   - Run until completion")
print("  ctx   - Show current context")
print("  list  - List all steps")


# Example 4: Quick Builders
print("\n" + "=" * 70)
print("EXAMPLE 4: Quick Pipeline Builders")
print("=" * 70)

from pipelinescript.pipeline import quick_classification, quick_regression

print("Quick classification:")
print("  result = quick_classification('data.csv', 'label', 'xgboost')")

print("\nQuick regression:")
print("  result = quick_regression('data.csv', 'price', 'random_forest')")

print("\nQuick train & export:")
print("  result = quick_train('data.csv', 'target', 'model.pkl')")


# Example 5: Visualization
print("\n" + "=" * 70)
print("EXAMPLE 5: Pipeline Visualization")
print("=" * 70)

pipeline = (Pipeline()
    .load("data.csv")
    .clean_missing()
    .split(0.8, target="label")
    .train("xgboost")
    .evaluate()
)

print("Visualizing pipeline structure...")
pipeline.visualize()

print("\nRun with visualization:")
print("  result = run(script, visualize=True)")


# Example 6: Advanced - Custom preprocessing
print("\n" + "=" * 70)
print("EXAMPLE 6: Advanced Pipeline")
print("=" * 70)

advanced_script = """
load sales.csv
filter revenue > 1000
select date product revenue region
clean missing
clean outliers
encode
scale
split 75/25 --target revenue
train xgboost
evaluate
export sales_model.pkl
"""

print("Advanced pipeline with filtering and selection:")
print(advanced_script)


# Example 7: Step-by-step execution
print("\n" + "=" * 70)
print("EXAMPLE 7: Step-by-Step Execution")
print("=" * 70)

from pipelinescript import parse, compile
from pipelinescript.executor import PipelineExecutor

script = "load iris.csv\nclean missing\nencode"

# Parse
ast = parse(script)
print(f"Parsed {len(ast)} commands")

# Compile
compiled = compile(ast)
print(f"Compiled {len(compiled)} steps")

# Execute step-by-step
executor = PipelineExecutor()
for i, step in enumerate(compiled):
    print(f"\nExecuting step {i+1}: {step.name}")
    executor.execute_step(step)

print("\n✅ Manual execution complete!")


print("\n" + "=" * 70)
print("🎉 All examples completed!")
print("=" * 70)
print("\nNext steps:")
print("1. Create your own .psl files")
print("2. Use the Python API for more control")
print("3. Try interactive debugging")
print("4. Visualize your pipelines")
print("\nDocumentation: See README.md")
