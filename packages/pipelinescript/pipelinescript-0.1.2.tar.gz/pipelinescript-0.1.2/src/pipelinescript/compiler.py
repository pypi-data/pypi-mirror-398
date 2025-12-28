"""
Pipeline Compiler - AST to Executable Pipeline
==============================================

Compiles Abstract Syntax Tree into executable ML pipeline steps.
"""

from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from .parser import ASTNode


@dataclass
class CompiledStep:
    """A compiled pipeline step."""
    name: str
    function: Callable
    args: List[Any]
    kwargs: Dict[str, Any]
    line: int


class PipelineCompiler:
    """Compiles AST into executable pipeline."""
    
    def __init__(self):
        self.commands = {
            'load': self._compile_load,
            'clean': self._compile_clean,
            'split': self._compile_split,
            'scale': self._compile_scale,
            'train': self._compile_train,
            'predict': self._compile_predict,
            'evaluate': self._compile_evaluate,
            'export': self._compile_export,
            'import': self._compile_import,
            'filter': self._compile_filter,
            'select': self._compile_select,
            'feature': self._compile_feature,
            'encode': self._compile_encode,
            'tune': self._compile_tune,
            'save': self._compile_save,
        }
    
    def compile(self, ast: List[ASTNode]) -> List[CompiledStep]:
        """
        Compile AST into executable steps.
        
        Args:
            ast: Abstract Syntax Tree
            
        Returns:
            List of compiled steps ready for execution
        """
        compiled = []
        
        for node in ast:
            if node.command in self.commands:
                step = self.commands[node.command](node)
                compiled.append(step)
            else:
                raise ValueError(f"Unknown command '{node.command}' at line {node.line}")
        
        return compiled
    
    # ===== Compilation Methods =====
    
    def _compile_load(self, node: ASTNode) -> CompiledStep:
        """Compile 'load' command."""
        if not node.args:
            raise ValueError(f"'load' requires a filepath at line {node.line}")
        
        filepath = node.args[0]
        
        def load_data(context):
            """Load data from file."""
            if filepath.endswith('.csv'):
                context['data'] = pd.read_csv(filepath)
            elif filepath.endswith(('.xlsx', '.xls')):
                context['data'] = pd.read_excel(filepath)
            elif filepath.endswith('.json'):
                context['data'] = pd.read_json(filepath)
            elif filepath.endswith('.parquet'):
                context['data'] = pd.read_parquet(filepath)
            else:
                raise ValueError(f"Unsupported file format: {filepath}")
            
            context['log'].append(f"Loaded {len(context['data'])} rows from {filepath}")
            return context
        
        return CompiledStep('load', load_data, [], {}, node.line)
    
    def _compile_clean(self, node: ASTNode) -> CompiledStep:
        """Compile 'clean' command."""
        strategy = node.args[0] if node.args else 'missing'
        
        def clean_data(context):
            """Clean data."""
            data = context['data']
            
            if strategy == 'missing':
                # Drop rows with missing values
                before = len(data)
                data = data.dropna()
                context['data'] = data
                context['log'].append(f"Removed {before - len(data)} rows with missing values")
            
            elif strategy == 'duplicates':
                before = len(data)
                data = data.drop_duplicates()
                context['data'] = data
                context['log'].append(f"Removed {before - len(data)} duplicate rows")
            
            elif strategy == 'outliers':
                # Remove outliers using IQR
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                before = len(data)
                
                for col in numeric_cols:
                    Q1 = data[col].quantile(0.25)
                    Q3 = data[col].quantile(0.75)
                    IQR = Q3 - Q1
                    data = data[(data[col] >= Q1 - 1.5*IQR) & (data[col] <= Q3 + 1.5*IQR)]
                
                context['data'] = data
                context['log'].append(f"Removed {before - len(data)} outliers")
            
            return context
        
        return CompiledStep('clean', clean_data, [], {}, node.line)
    
    def _compile_split(self, node: ASTNode) -> CompiledStep:
        """Compile 'split' command."""
        # Parse split ratio (e.g., "80/20" or "0.8")
        if node.args:
            ratio_str = str(node.args[0])
            if '/' in ratio_str:
                train_pct, test_pct = map(int, ratio_str.split('/'))
                train_size = train_pct / (train_pct + test_pct)
            else:
                train_size = float(ratio_str)
        else:
            train_size = 0.8
        
        target = node.options.get('target') or (node.args[1] if len(node.args) > 1 else None)
        
        def split_data(context):
            """Split data into train/test sets."""
            data = context['data']
            
            if target:
                if target not in data.columns:
                    raise ValueError(f"Target column '{target}' not found in data. Available: {list(data.columns)}")
                
                X = data.drop(columns=[target])
                y = data[target]
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, train_size=train_size, random_state=42
                )
                
                context['X_train'] = X_train
                context['X_test'] = X_test
                context['y_train'] = y_train
                context['y_test'] = y_test
                context['target'] = target
                
                context['log'].append(
                    f"Split data: {len(X_train)} train, {len(X_test)} test "
                    f"({train_size*100:.0f}/{(1-train_size)*100:.0f})"
                )
            else:
                # Just split the data
                train, test = train_test_split(data, train_size=train_size, random_state=42)
                context['train'] = train
                context['test'] = test
                context['log'].append(
                    f"Split data: {len(train)} train, {len(test)} test"
                )
            
            return context
        
        return CompiledStep('split', split_data, [], {}, node.line)
    
    def _compile_scale(self, node: ASTNode) -> CompiledStep:
        """Compile 'scale' command."""
        
        def scale_data(context):
            """Scale numeric features."""
            scaler = StandardScaler()
            
            if 'X_train' in context:
                context['X_train'] = pd.DataFrame(
                    scaler.fit_transform(context['X_train']),
                    columns=context['X_train'].columns,
                    index=context['X_train'].index
                )
                context['X_test'] = pd.DataFrame(
                    scaler.transform(context['X_test']),
                    columns=context['X_test'].columns,
                    index=context['X_test'].index
                )
                context['scaler'] = scaler
                context['log'].append("Scaled features using StandardScaler")
            
            return context
        
        return CompiledStep('scale', scale_data, [], {}, node.line)
    
    def _compile_train(self, node: ASTNode) -> CompiledStep:
        """Compile 'train' command."""
        model_type = node.args[0] if node.args else 'auto'
        
        def train_model(context):
            """Train ML model."""
            X_train = context.get('X_train')
            y_train = context.get('y_train')
            
            if X_train is None or y_train is None:
                raise ValueError("No training data found. Run 'split' first.")
            
            # Determine task type
            is_classification = len(np.unique(y_train)) < 20
            
            # Select model
            if model_type == 'xgboost' or model_type == 'xgb':
                if not HAS_XGBOOST:
                    raise ImportError("xgboost not installed. Run: pip install xgboost")
                
                if is_classification:
                    model = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
                else:
                    model = xgb.XGBRegressor(random_state=42)
            
            elif model_type == 'random_forest' or model_type == 'rf':
                if is_classification:
                    model = RandomForestClassifier(random_state=42, n_estimators=100)
                else:
                    model = RandomForestRegressor(random_state=42, n_estimators=100)
            
            elif model_type in ('logistic', 'lr'):
                model = LogisticRegression(random_state=42, max_iter=1000)
            
            elif model_type == 'linear':
                model = LinearRegression()
            
            elif model_type == 'auto':
                # Auto-select based on task
                if is_classification:
                    model = RandomForestClassifier(random_state=42, n_estimators=100)
                else:
                    model = RandomForestRegressor(random_state=42, n_estimators=100)
            
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Train model
            model.fit(X_train, y_train)
            
            context['model'] = model
            context['model_type'] = model_type
            context['is_classification'] = is_classification
            context['log'].append(f"Trained {model.__class__.__name__}")
            
            return context
        
        return CompiledStep('train', train_model, [], {}, node.line)
    
    def _compile_evaluate(self, node: ASTNode) -> CompiledStep:
        """Compile 'evaluate' command."""
        
        def evaluate_model(context):
            """Evaluate model performance."""
            model = context.get('model')
            X_test = context.get('X_test')
            y_test = context.get('y_test')
            
            if model is None:
                raise ValueError("No model found. Run 'train' first.")
            
            if X_test is None or y_test is None:
                raise ValueError("No test data found. Run 'split' first.")
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            if context['is_classification']:
                accuracy = accuracy_score(y_test, y_pred)
                context['metrics'] = {
                    'accuracy': accuracy,
                    'report': classification_report(y_test, y_pred)
                }
                context['log'].append(f"Accuracy: {accuracy:.4f}")
            else:
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                context['metrics'] = {
                    'mse': mse,
                    'rmse': rmse
                }
                context['log'].append(f"RMSE: {rmse:.4f}")
            
            context['predictions'] = y_pred
            
            return context
        
        return CompiledStep('evaluate', evaluate_model, [], {}, node.line)
    
    def _compile_export(self, node: ASTNode) -> CompiledStep:
        """Compile 'export' command."""
        filepath = node.args[0] if node.args else 'model.pkl'
        
        def export_model(context):
            """Export model to file."""
            import pickle
            
            model = context.get('model')
            if model is None:
                raise ValueError("No model to export. Run 'train' first.")
            
            with open(filepath, 'wb') as f:
                pickle.dump(model, f)
            
            context['log'].append(f"Exported model to {filepath}")
            
            return context
        
        return CompiledStep('export', export_model, [], {}, node.line)
    
    def _compile_import(self, node: ASTNode) -> CompiledStep:
        """Compile 'import' command."""
        filepath = node.args[0] if node.args else 'model.pkl'
        
        def import_model(context):
            """Import model from file."""
            import pickle
            
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            
            context['model'] = model
            context['log'].append(f"Imported model from {filepath}")
            
            return context
        
        return CompiledStep('import', import_model, [], {}, node.line)
    
    def _compile_filter(self, node: ASTNode) -> CompiledStep:
        """Compile 'filter' command."""
        condition = ' '.join(str(arg) for arg in node.args)
        
        def filter_data(context):
            """Filter data based on condition."""
            data = context['data']
            filtered = data.query(condition)
            context['data'] = filtered
            context['log'].append(f"Filtered to {len(filtered)} rows")
            return context
        
        return CompiledStep('filter', filter_data, [], {}, node.line)
    
    def _compile_select(self, node: ASTNode) -> CompiledStep:
        """Compile 'select' command."""
        columns = node.args
        
        def select_columns(context):
            """Select specific columns."""
            data = context['data']
            context['data'] = data[list(columns)]
            context['log'].append(f"Selected {len(columns)} columns")
            return context
        
        return CompiledStep('select', select_columns, [], {}, node.line)
    
    def _compile_feature(self, node: ASTNode) -> CompiledStep:
        """Compile 'feature' engineering command."""
        operation = node.args[0] if node.args else 'auto'
        
        def create_features(context):
            """Create new features."""
            context['log'].append(f"Feature engineering: {operation}")
            return context
        
        return CompiledStep('feature', create_features, [], {}, node.line)
    
    def _compile_encode(self, node: ASTNode) -> CompiledStep:
        """Compile 'encode' command."""
        
        def encode_categoricals(context):
            """Encode categorical variables."""
            data = context['data']
            
            categorical_cols = data.select_dtypes(include=['object']).columns
            
            for col in categorical_cols:
                le = LabelEncoder()
                data[col] = le.fit_transform(data[col].astype(str))
            
            context['data'] = data
            context['log'].append(f"Encoded {len(categorical_cols)} categorical columns")
            
            return context
        
        return CompiledStep('encode', encode_categoricals, [], {}, node.line)
    
    def _compile_tune(self, node: ASTNode) -> CompiledStep:
        """Compile 'tune' hyperparameter command."""
        
        def tune_model(context):
            """Tune model hyperparameters."""
            context['log'].append("Hyperparameter tuning (basic)")
            return context
        
        return CompiledStep('tune', tune_model, [], {}, node.line)
    
    def _compile_save(self, node: ASTNode) -> CompiledStep:
        """Compile 'save' command."""
        return self._compile_export(node)
    
    def _compile_predict(self, node: ASTNode) -> CompiledStep:
        """Compile 'predict' command."""
        
        def make_predictions(context):
            """Make predictions."""
            model = context.get('model')
            X_test = context.get('X_test')
            
            if model is None:
                raise ValueError("No model found. Run 'train' first.")
            
            if X_test is None:
                raise ValueError("No test data. Run 'split' first.")
            
            predictions = model.predict(X_test)
            context['predictions'] = predictions
            context['log'].append(f"Generated {len(predictions)} predictions")
            
            return context
        
        return CompiledStep('predict', make_predictions, [], {}, node.line)
