# 🔥 PipelineScript - Human-Readable ML Pipeline Language

**Transform machine learning pipelines from code into conversation.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/pipelinescript.svg)](https://badge.fury.io/py/pipelinescript)

---

## 🚀 What is PipelineScript?

PipelineScript is a revolutionary **Domain-Specific Language (DSL)** that makes machine learning pipelines readable, debuggable, and accessible to everyone. No more nested code, complex APIs, or cryptic configurations.

### Before PipelineScript:
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

# Load data
data = pd.read_csv('data.csv')

# Clean
data = data.dropna()

# Encode categoricals
from sklearn.preprocessing import LabelEncoder
for col in data.select_dtypes(['object']).columns:
    data[col] = LabelEncoder().fit_transform(data[col])

# Split
X = data.drop('target', axis=1)
y = data['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Scale
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Train
model = XGBClassifier()
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred)}")

# Export
import pickle
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
```

### With PipelineScript:
```
load data.csv
clean missing
encode
split 80/20 --target target
scale
train xgboost
evaluate
export model.pkl
```

**That's it.** Same functionality, 90% less code, infinitely more readable.

---

## ✨ Key Features

### 1. 🗣️ Human-Readable Syntax
Write ML pipelines like you'd describe them to a colleague:
```
load sales.csv
filter revenue > 1000
clean outliers
split 75/25 --target revenue
train xgboost
evaluate
```

### 2. 🐛 Interactive Debugging
Step through your pipeline like a regular program:
```python
from pipelinescript import debug

debug("""
    load data.csv
    clean missing
    train xgboost
""")
```

Debugger commands:
- `step` - Execute next step
- `break 3` - Set breakpoint at step 3
- `context` - Show current data and model
- `inspect model` - Inspect specific variable
- `continue` - Run until completion

### 3. 📊 Built-in Visualization
Automatically visualize your pipeline structure:
```python
from pipelinescript import run

run(script, visualize=True)
```

Generates ASCII or graphical pipeline diagrams showing data flow.

### 4. 🔗 Method Chaining API
Prefer Python? Use the fluent API:
```python
from pipelinescript import Pipeline

result = (Pipeline()
    .load("data.csv")
    .clean_missing()
    .encode()
    .split(0.8, target="label")
    .train("xgboost")
    .evaluate()
    .export("model.pkl")
    .run())
```

### 5. ⚡ Quick Builders
Pre-built pipelines for common tasks:
```python
from pipelinescript.pipeline import quick_classification

# One line for complete classification pipeline
result = quick_classification("data.csv", "label", "xgboost")
```

---

## 📦 Installation

```bash
pip install pipelinescript
```

**Optional dependencies:**
```bash
# For XGBoost models
pip install xgboost

# For visualization
pip install matplotlib

# For all features
pip install pipelinescript[full]
```

---

## 🎯 Quick Start

### 1. Create a Pipeline File (`.psl`)

`my_pipeline.psl`:
```
load iris.csv
clean missing
encode
split 80/20 --target species
train random_forest
evaluate
export iris_model.pkl
```

### 2. Run It

**Command Line:**
```bash
pipelinescript run my_pipeline.psl
```

**Python:**
```python
from pipelinescript import run

result = run("my_pipeline.psl")

if result.success:
    print(f"✅ Accuracy: {result.context.metrics['accuracy']:.4f}")
```

**That's it!** Your model is trained, evaluated, and exported.

---

## 📖 Language Reference

### Commands

#### Data Loading
```
load <filepath>              # Load data from file
```
Supported formats: CSV, Excel, JSON, Parquet

#### Data Cleaning
```
clean missing                # Remove rows with missing values
clean duplicates             # Remove duplicate rows
clean outliers               # Remove statistical outliers (IQR method)
```

#### Data Transformation
```
encode                       # Encode categorical variables
scale                        # Scale numeric features (StandardScaler)
filter <condition>           # Filter rows (e.g., "age > 18")
select <col1> <col2> ...     # Select specific columns
```

#### Train/Test Split
```
split 80/20                  # Split data 80% train, 20% test
split 0.8 --target label     # Split with specific target column
split 75/25 --target price   # Custom ratio with target
```

#### Model Training
```
train xgboost                # XGBoost (requires xgboost package)
train random_forest          # Random Forest
train logistic               # Logistic Regression
train linear                 # Linear Regression
train auto                   # Auto-select based on task
```

#### Evaluation
```
predict                      # Make predictions on test set
evaluate                     # Compute evaluation metrics
```

#### Model Export/Import
```
export model.pkl             # Save model to file
save model.pkl               # Alias for export
import model.pkl             # Load model from file
```

### Options

Options use `--flag` or `-f` syntax:
```
split 80/20 --target revenue
train xgboost --n_estimators 100
```

### Comments

Use `#` for comments:
```
# Load and prepare data
load data.csv
clean missing  # Remove nulls

# Train model
train xgboost
```

---

## 🔥 Examples

### Example 1: Basic Classification

```
load titanic.csv
clean missing
encode
split 80/20 --target survived
train random_forest
evaluate
export titanic_model.pkl
```

### Example 2: Regression with Preprocessing

```
load housing.csv
clean outliers
select bedrooms bathrooms sqft price
scale
split 75/25 --target price
train linear
evaluate
```

### Example 3: XGBoost with Feature Selection

```
load sales.csv
filter revenue > 1000
select date product revenue region
clean missing
encode
split 80/20 --target revenue
train xgboost
evaluate
export sales_model.pkl
```

### Example 4: Interactive Debugging

```python
from pipelinescript import debug

script = """
load data.csv
clean missing
split 80/20 --target label
train xgboost
evaluate
"""

result = debug(script)

# In debugger:
# (pdb) step           # Execute next step
# (pdb) context        # Show current state
# (pdb) inspect model  # Look at model
# (pdb) continue       # Run to completion
```

### Example 5: Python API

```python
from pipelinescript import Pipeline

# Method chaining
pipeline = (Pipeline()
    .load("data.csv")
    .clean_missing()
    .clean_outliers()
    .encode()
    .scale()
    .split(0.8, target="label")
    .train_xgboost()
    .evaluate()
    .export("model.pkl")
)

# Execute
result = pipeline.run()

# Show results
if result.success:
    print(f"Duration: {result.duration:.2f}s")
    print(f"Metrics: {result.context.metrics}")
```

### Example 6: Quick Builders

```python
from pipelinescript.pipeline import (
    quick_classification,
    quick_regression,
    quick_train
)

# Classification in one line
result = quick_classification("iris.csv", "species", "xgboost")

# Regression in one line
result = quick_regression("housing.csv", "price", "random_forest")

# Train and export in one line
result = quick_train("data.csv", "target", "model.pkl")
```

---

## 🎨 Visualization

### ASCII Pipeline Diagram

```python
from pipelinescript import run

run(script, visualize=True)
```

Output:
```
════════════════════════════════════════════════
    📊 PIPELINE VISUALIZATION
════════════════════════════════════════════════

    START
      │
      ▼
    ┌─────────────┐
    │ LOAD data.csv │
    └─────────────┘
      │
      ▼
    ┌──────────────┐
    │ CLEAN missing │
    └──────────────┘
      │
      ▼
    ┌──────────────┐
    │ TRAIN xgboost │
    └──────────────┘
      │
      ▼
    END
```

### Graphical Pipeline (with matplotlib)

```python
from pipelinescript import parse
from pipelinescript.visualizer import PipelineVisualizer

ast = parse(script)
visualizer = PipelineVisualizer()
visualizer.visualize_pipeline(ast, save_path="pipeline.png")
```

Generates a beautiful flowchart visualization.

---

## 🐛 Interactive Debugging

PipelineScript includes a powerful **interactive debugger** inspired by Python's `pdb`:

```python
from pipelinescript import debug

debug("""
    load data.csv
    clean missing
    split 80/20 --target label
    train xgboost
    evaluate
""")
```

### Debugger Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `run` | `r` | Run until completion/breakpoint |
| `step` | `s`, `next`, `n` | Execute next step |
| `continue` | `c`, `cont` | Continue execution |
| `break <n>` | `b` | Set breakpoint at step n |
| `clear <n>` | | Clear breakpoint |
| `list` | `l`, `ls` | List all steps |
| `context` | `ctx`, `vars` | Show execution context |
| `inspect <var>` | `i`, `p` | Inspect variable |
| `restart` | | Restart from beginning |
| `quit` | `q`, `exit` | Quit debugger |

### Example Debugging Session

```
(pdb) list
Pipeline Steps:
══════════════════════════════════════════════
   → 1. load
     2. clean
     3. split
     4. train
     5. evaluate
══════════════════════════════════════════════

(pdb) break 4
🔴 Breakpoint set at step 4

(pdb) run
▶️  Step 1: load
   Loaded 150 rows from iris.csv

▶️  Step 2: clean
   Removed 0 rows with missing values

▶️  Step 3: split
   Split data: 120 train, 30 test (80/20)

🔴 Breakpoint at step 4

(pdb) context
📊 Execution Context:
══════════════════════════════════════════════
  data: DataFrame (150, 5)
    columns: ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species']
  X_train: (120, 4)
  X_test: (30, 4)

  Recent log entries:
    • Loaded 150 rows from iris.csv
    • Removed 0 rows with missing values
    • Split data: 120 train, 30 test (80/20)
══════════════════════════════════════════════

(pdb) step
▶️  Step 4: train
   Trained XGBClassifier

(pdb) inspect model
model: XGBClassifier
  Value: XGBClassifier(...)

(pdb) continue
▶️  Step 5: evaluate
   Accuracy: 0.9667

✅ Pipeline execution completed!
```

---

## 🏗️ Architecture

PipelineScript consists of five core components:

```
┌─────────────────────────────────────────────┐
│          PipelineScript Engine              │
├─────────────────────────────────────────────┤
│                                             │
│  1. Parser     →  Lexical analysis & AST   │
│  2. Compiler   →  AST to executable steps  │
│  3. Executor   →  Step execution engine    │
│  4. Debugger   →  Interactive debugging    │
│  5. Visualizer →  Pipeline visualization   │
│                                             │
└─────────────────────────────────────────────┘
```

### 1. Parser (`parser.py`)
- Lexical analysis (tokenization)
- Syntax parsing
- AST generation

### 2. Compiler (`compiler.py`)
- Compiles AST into executable steps
- Integrates with sklearn, xgboost
- Handles data transformations

### 3. Executor (`executor.py`)
- Executes compiled steps
- Manages execution context
- Handles errors and logging

### 4. Debugger (`debugger.py`)
- Interactive step-through execution
- Breakpoints and inspection
- Context visualization

### 5. Visualizer (`visualizer.py`)
- ASCII pipeline diagrams
- Graphical visualizations
- DAG export

---

## 🎯 Use Cases

### 1. **Rapid Prototyping**
Test different models and preprocessing strategies in minutes:
```
load data.csv
clean missing
split 80/20 --target label
train xgboost
evaluate
```

### 2. **Teaching & Learning**
Perfect for teaching ML concepts without drowning in code:
```
# Clear, readable steps students can understand
load iris.csv
split 70/30 --target species
train random_forest
evaluate
```

### 3. **Reproducible Research**
Pipeline scripts are version-controllable and self-documenting:
```
# research_pipeline.psl
load experiment_data.csv
clean outliers
split 80/20 --target outcome
train xgboost
evaluate
```

### 4. **Automated ML**
Easily generate and test multiple pipelines programmatically:
```python
models = ['xgboost', 'random_forest', 'logistic']

for model in models:
    pipeline = Pipeline().load("data.csv").clean_missing()
    pipeline.split(0.8, target="label").train(model).evaluate()
    result = pipeline.run()
    print(f"{model}: {result.context.metrics['accuracy']}")
```

### 5. **Production Pipelines**
Export trained pipelines as standalone Python scripts or containers.

---

## 🔬 Advanced Usage

### Custom Preprocessing

```python
from pipelinescript import Pipeline

pipeline = Pipeline()
pipeline.load("data.csv")

# Custom filtering
pipeline.filter("age > 18 and income < 100000")

# Select features
pipeline.select("age", "income", "education")

# Continue pipeline
pipeline.clean_missing().encode().scale()
pipeline.split(0.8, target="default").train("xgboost")

result = pipeline.run()
```

### Accessing Context

```python
result = pipeline.run()

if result.success:
    # Access data
    print(result.context.data.head())
    
    # Access model
    model = result.context.model
    
    # Access metrics
    print(result.context.metrics)
    
    # Access predictions
    predictions = result.context.predictions
    
    # Access log
    for entry in result.context.log:
        print(entry)
```

### Extending PipelineScript

Add custom commands by extending the compiler:

```python
from pipelinescript.compiler import PipelineCompiler
from pipelinescript.parser import ASTNode

class CustomCompiler(PipelineCompiler):
    def __init__(self):
        super().__init__()
        self.commands['my_command'] = self._compile_my_command
    
    def _compile_my_command(self, node: ASTNode):
        def custom_step(context):
            # Your custom logic
            return context
        
        return CompiledStep('my_command', custom_step, [], {}, node.line)
```

---

## 🚧 Roadmap

- [ ] **v0.2.0**: GPU support (RAPIDS, cuML)
- [ ] **v0.3.0**: Deep learning models (PyTorch, TensorFlow)
- [ ] **v0.4.0**: AutoML integration
- [ ] **v0.5.0**: Distributed training (Ray, Dask)
- [ ] **v0.6.0**: Model serving integration
- [ ] **v0.7.0**: Pipeline scheduling and monitoring
- [ ] **v1.0.0**: Production-ready feature complete

---

## 🤝 Contributing

Contributions welcome! Areas needing help:

1. **Additional model types** (SVM, KNN, etc.)
2. **More preprocessing** options
3. **Better visualizations**
4. **Documentation** improvements
5. **Test coverage**

See `CONTRIBUTING.md` for guidelines.

---

## 📄 License

MIT License - see `LICENSE` file.

---

## 🙏 Acknowledgments

PipelineScript was inspired by:
- SQL's declarative simplicity
- UNIX pipes' composability
- scikit-learn's consistent API
- The need for ML democratization

---

## 📊 Comparison

| Feature | PipelineScript | Sklearn | Keras | MLflow |
|---------|---------------|---------|-------|--------|
| **Human-readable syntax** | ✅ | ❌ | ❌ | ❌ |
| **Interactive debugging** | ✅ | ❌ | ❌ | ❌ |
| **Built-in visualization** | ✅ | ❌ | ✅ | ✅ |
| **One-line pipelines** | ✅ | ❌ | ❌ | ❌ |
| **No code required** | ✅ | ❌ | ❌ | ❌ |
| **Production ready** | 🚧 | ✅ | ✅ | ✅ |

---

## 🎓 Examples & Tutorials

See the `examples/` directory for:

- `simple_classification.psl` - Basic classification
- `xgboost_pipeline.psl` - XGBoost example
- `regression.psl` - Regression pipeline
- `python_examples.py` - Python API examples
- `iris.csv` - Sample dataset

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/idrissbado/PipelineScript/issues)
- **Discussions**: [GitHub Discussions](https://github.com/idrissbado/PipelineScript/discussions)
- **Email**: idrissbadoolivier@gmail.com

---

## 🌟 Star History

If you find PipelineScript useful, please star the repo! ⭐

---

<div align="center">

**🔥 Built with ❤️ by [Idriss Bado](https://github.com/idrissbado)**

*Making machine learning pipelines human again.*

</div>
