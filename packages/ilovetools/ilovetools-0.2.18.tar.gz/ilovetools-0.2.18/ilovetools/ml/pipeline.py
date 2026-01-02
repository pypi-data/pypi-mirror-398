"""
ML Pipeline utilities for workflow automation
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Dict, Any, Callable, Optional, Tuple
import json

__all__ = [
    # Full names
    'create_pipeline',
    'add_pipeline_step',
    'execute_pipeline',
    'validate_pipeline',
    'serialize_pipeline',
    'deserialize_pipeline',
    'pipeline_transform',
    'pipeline_fit_transform',
    'get_pipeline_params',
    'set_pipeline_params',
    'clone_pipeline',
    'pipeline_summary',
    # Abbreviated aliases
    'create_pipe',
    'add_step',
    'execute_pipe',
    'validate_pipe',
    'serialize_pipe',
    'deserialize_pipe',
    'pipe_transform',
    'pipe_fit_transform',
    'get_params',
    'set_params',
    'clone_pipe',
    'pipe_summary',
]


def create_pipeline(steps: Optional[List[Tuple[str, Callable]]] = None) -> Dict[str, Any]:
    """
    Create a new ML pipeline.
    
    Alias: create_pipe()
    
    Args:
        steps: Optional list of (name, function) tuples
    
    Returns:
        dict: Pipeline object
    
    Examples:
        >>> from ilovetools.ml import create_pipe  # Short alias
        
        >>> # Create empty pipeline
        >>> pipeline = create_pipe()
        >>> print(pipeline)
        {'steps': [], 'fitted': False, 'params': {}}
        
        >>> # Create with steps
        >>> def scale(X):
        ...     return [[x / 10 for x in row] for row in X]
        >>> 
        >>> pipeline = create_pipe([('scaler', scale)])
        >>> print(len(pipeline['steps']))
        1
        
        >>> from ilovetools.ml import create_pipeline  # Full name
        >>> pipeline = create_pipeline()
    
    Notes:
        - Foundation for ML workflows
        - Add steps incrementally
        - Execute in sequence
        - Reusable and modular
    """
    return {
        'steps': steps if steps is not None else [],
        'fitted': False,
        'params': {},
        'metadata': {
            'created': True,
            'n_steps': len(steps) if steps is not None else 0,
        }
    }


# Create alias
create_pipe = create_pipeline


def add_pipeline_step(
    pipeline: Dict[str, Any],
    name: str,
    function: Callable,
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Add a step to the pipeline.
    
    Alias: add_step()
    
    Args:
        pipeline: Pipeline object
        name: Step name
        function: Step function
        params: Optional step parameters
    
    Returns:
        dict: Updated pipeline
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> 
        >>> def scale(X):
        ...     return [[x / 10 for x in row] for row in X]
        >>> 
        >>> pipeline = add_step(pipeline, 'scaler', scale)
        >>> print(len(pipeline['steps']))
        1
        
        >>> # Add with parameters
        >>> def encode(X, mapping=None):
        ...     return X
        >>> 
        >>> pipeline = add_step(pipeline, 'encoder', encode, {'mapping': {'A': 0, 'B': 1}})
        >>> print(len(pipeline['steps']))
        2
        
        >>> from ilovetools.ml import add_pipeline_step  # Full name
        >>> pipeline = add_pipeline_step(pipeline, 'step3', lambda x: x)
    
    Notes:
        - Add steps in order
        - Each step has name and function
        - Optional parameters per step
        - Build complex workflows
    """
    step = {
        'name': name,
        'function': function,
        'params': params if params is not None else {}
    }
    
    pipeline['steps'].append(step)
    pipeline['metadata']['n_steps'] = len(pipeline['steps'])
    
    return pipeline


# Create alias
add_step = add_pipeline_step


def execute_pipeline(
    pipeline: Dict[str, Any],
    X: List[List[float]],
    y: Optional[List] = None,
    fit: bool = False
) -> Any:
    """
    Execute pipeline on data.
    
    Alias: execute_pipe()
    
    Args:
        pipeline: Pipeline object
        X: Input data
        y: Optional target values
        fit: Whether to fit steps (for training)
    
    Returns:
        Transformed data
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step, execute_pipe  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> 
        >>> def scale(X):
        ...     return [[x / 10 for x in row] for row in X]
        >>> 
        >>> def add_one(X):
        ...     return [[x + 1 for x in row] for row in X]
        >>> 
        >>> pipeline = add_step(pipeline, 'scaler', scale)
        >>> pipeline = add_step(pipeline, 'adder', add_one)
        >>> 
        >>> X = [[10, 20], [30, 40]]
        >>> result = execute_pipe(pipeline, X)
        >>> print(result)
        [[2.0, 3.0], [4.0, 5.0]]
        
        >>> from ilovetools.ml import execute_pipeline  # Full name
        >>> result = execute_pipeline(pipeline, X)
    
    Notes:
        - Executes steps in sequence
        - Each step transforms data
        - Output of step N → input of step N+1
        - Fit mode for training
    """
    result = X
    
    for step in pipeline['steps']:
        function = step['function']
        params = step['params']
        
        # Execute step with parameters
        if params:
            # Check if function accepts params
            try:
                result = function(result, **params)
            except TypeError:
                result = function(result)
        else:
            result = function(result)
    
    if fit:
        pipeline['fitted'] = True
    
    return result


# Create alias
execute_pipe = execute_pipeline


def validate_pipeline(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate pipeline structure and steps.
    
    Alias: validate_pipe()
    
    Args:
        pipeline: Pipeline object
    
    Returns:
        dict: Validation results
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step, validate_pipe  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> pipeline = add_step(pipeline, 'scaler', lambda x: x)
        >>> 
        >>> validation = validate_pipe(pipeline)
        >>> print(validation['valid'])
        True
        >>> print(validation['n_steps'])
        1
        
        >>> from ilovetools.ml import validate_pipeline  # Full name
        >>> validation = validate_pipeline(pipeline)
    
    Notes:
        - Check pipeline structure
        - Verify all steps are callable
        - Ensure no duplicate names
        - Validate before execution
    """
    errors = []
    warnings = []
    
    # Check if pipeline has steps
    if not pipeline.get('steps'):
        warnings.append("Pipeline has no steps")
    
    # Check for duplicate step names
    step_names = [step['name'] for step in pipeline['steps']]
    if len(step_names) != len(set(step_names)):
        errors.append("Duplicate step names found")
    
    # Check if all steps are callable
    for step in pipeline['steps']:
        if not callable(step.get('function')):
            errors.append(f"Step '{step['name']}' function is not callable")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'n_steps': len(pipeline['steps']),
    }


# Create alias
validate_pipe = validate_pipeline


def serialize_pipeline(pipeline: Dict[str, Any], include_functions: bool = False) -> str:
    """
    Serialize pipeline to JSON string.
    
    Alias: serialize_pipe()
    
    Args:
        pipeline: Pipeline object
        include_functions: Whether to include function code (not recommended)
    
    Returns:
        str: JSON string
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step, serialize_pipe  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> pipeline = add_step(pipeline, 'scaler', lambda x: x)
        >>> 
        >>> serialized = serialize_pipe(pipeline)
        >>> print(type(serialized))
        <class 'str'>
        
        >>> from ilovetools.ml import serialize_pipeline  # Full name
        >>> serialized = serialize_pipeline(pipeline)
    
    Notes:
        - Save pipeline to file
        - Version control
        - Share with team
        - Functions not serialized by default
    """
    # Create serializable version
    serializable = {
        'steps': [],
        'fitted': pipeline.get('fitted', False),
        'params': pipeline.get('params', {}),
        'metadata': pipeline.get('metadata', {}),
    }
    
    for step in pipeline['steps']:
        step_data = {
            'name': step['name'],
            'params': step['params'],
        }
        
        if include_functions:
            # Warning: This is not recommended for production
            step_data['function_name'] = step['function'].__name__
        
        serializable['steps'].append(step_data)
    
    return json.dumps(serializable, indent=2)


# Create alias
serialize_pipe = serialize_pipeline


def deserialize_pipeline(json_string: str) -> Dict[str, Any]:
    """
    Deserialize pipeline from JSON string.
    
    Alias: deserialize_pipe()
    
    Args:
        json_string: JSON string
    
    Returns:
        dict: Pipeline object (without functions)
    
    Examples:
        >>> from ilovetools.ml import serialize_pipe, deserialize_pipe  # Short aliases
        
        >>> # Assume we have a serialized pipeline
        >>> json_str = '{"steps": [], "fitted": false, "params": {}}'
        >>> 
        >>> pipeline = deserialize_pipe(json_str)
        >>> print(pipeline['fitted'])
        False
        
        >>> from ilovetools.ml import deserialize_pipeline  # Full name
        >>> pipeline = deserialize_pipeline(json_str)
    
    Notes:
        - Load pipeline from file
        - Restore structure
        - Functions must be re-added
        - Useful for configuration
    """
    data = json.loads(json_string)
    
    pipeline = {
        'steps': [],
        'fitted': data.get('fitted', False),
        'params': data.get('params', {}),
        'metadata': data.get('metadata', {}),
    }
    
    # Note: Functions are not deserialized
    # They must be re-added manually
    for step_data in data.get('steps', []):
        pipeline['steps'].append({
            'name': step_data['name'],
            'function': None,  # Must be set manually
            'params': step_data.get('params', {}),
        })
    
    return pipeline


# Create alias
deserialize_pipe = deserialize_pipeline


def pipeline_transform(
    pipeline: Dict[str, Any],
    X: List[List[float]]
) -> List[List[float]]:
    """
    Transform data using fitted pipeline.
    
    Alias: pipe_transform()
    
    Args:
        pipeline: Fitted pipeline object
        X: Input data
    
    Returns:
        list: Transformed data
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step, pipe_transform  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> 
        >>> def scale(X):
        ...     return [[x / 10 for x in row] for row in X]
        >>> 
        >>> pipeline = add_step(pipeline, 'scaler', scale)
        >>> pipeline['fitted'] = True
        >>> 
        >>> X = [[10, 20], [30, 40]]
        >>> result = pipe_transform(pipeline, X)
        >>> print(result)
        [[1.0, 2.0], [3.0, 4.0]]
        
        >>> from ilovetools.ml import pipeline_transform  # Full name
        >>> result = pipeline_transform(pipeline, X)
    
    Notes:
        - Use after fitting
        - Transform new data
        - Same transformations as training
        - No fitting during transform
    """
    if not pipeline.get('fitted'):
        raise ValueError("Pipeline must be fitted before transform")
    
    return execute_pipeline(pipeline, X, fit=False)


# Create alias
pipe_transform = pipeline_transform


def pipeline_fit_transform(
    pipeline: Dict[str, Any],
    X: List[List[float]],
    y: Optional[List] = None
) -> List[List[float]]:
    """
    Fit pipeline and transform data.
    
    Alias: pipe_fit_transform()
    
    Args:
        pipeline: Pipeline object
        X: Input data
        y: Optional target values
    
    Returns:
        list: Transformed data
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step, pipe_fit_transform  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> 
        >>> def scale(X):
        ...     return [[x / 10 for x in row] for row in X]
        >>> 
        >>> pipeline = add_step(pipeline, 'scaler', scale)
        >>> 
        >>> X = [[10, 20], [30, 40]]
        >>> result = pipe_fit_transform(pipeline, X)
        >>> print(result)
        [[1.0, 2.0], [3.0, 4.0]]
        >>> print(pipeline['fitted'])
        True
        
        >>> from ilovetools.ml import pipeline_fit_transform  # Full name
        >>> result = pipeline_fit_transform(pipeline, X)
    
    Notes:
        - Fit and transform in one call
        - Use for training data
        - Pipeline becomes fitted
        - Convenient for workflows
    """
    return execute_pipeline(pipeline, X, y=y, fit=True)


# Create alias
pipe_fit_transform = pipeline_fit_transform


def get_pipeline_params(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get all pipeline parameters.
    
    Alias: get_params()
    
    Args:
        pipeline: Pipeline object
    
    Returns:
        dict: All parameters
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step, get_params  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> pipeline = add_step(pipeline, 'scaler', lambda x: x, {'factor': 10})
        >>> 
        >>> params = get_params(pipeline)
        >>> print(params)
        {'scaler__factor': 10}
        
        >>> from ilovetools.ml import get_pipeline_params  # Full name
        >>> params = get_pipeline_params(pipeline)
    
    Notes:
        - Get all step parameters
        - Nested parameter names
        - Useful for inspection
        - Format: step__param
    """
    all_params = {}
    
    for step in pipeline['steps']:
        step_name = step['name']
        step_params = step['params']
        
        for param_name, param_value in step_params.items():
            key = f"{step_name}__{param_name}"
            all_params[key] = param_value
    
    return all_params


# Create alias
get_params = get_pipeline_params


def set_pipeline_params(
    pipeline: Dict[str, Any],
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Set pipeline parameters.
    
    Alias: set_params()
    
    Args:
        pipeline: Pipeline object
        params: Parameters to set (format: step__param)
    
    Returns:
        dict: Updated pipeline
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step, set_params  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> pipeline = add_step(pipeline, 'scaler', lambda x: x, {'factor': 10})
        >>> 
        >>> pipeline = set_params(pipeline, {'scaler__factor': 20})
        >>> print(pipeline['steps'][0]['params']['factor'])
        20
        
        >>> from ilovetools.ml import set_pipeline_params  # Full name
        >>> pipeline = set_pipeline_params(pipeline, {'scaler__factor': 30})
    
    Notes:
        - Update step parameters
        - Use double underscore notation
        - Useful for tuning
        - Format: step__param
    """
    for param_key, param_value in params.items():
        if '__' in param_key:
            step_name, param_name = param_key.split('__', 1)
            
            # Find step and update parameter
            for step in pipeline['steps']:
                if step['name'] == step_name:
                    step['params'][param_name] = param_value
                    break
    
    return pipeline


# Create alias
set_params = set_pipeline_params


def clone_pipeline(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a deep copy of pipeline.
    
    Alias: clone_pipe()
    
    Args:
        pipeline: Pipeline object
    
    Returns:
        dict: Cloned pipeline
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step, clone_pipe  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> pipeline = add_step(pipeline, 'scaler', lambda x: x)
        >>> 
        >>> cloned = clone_pipe(pipeline)
        >>> print(len(cloned['steps']))
        1
        >>> print(cloned is pipeline)
        False
        
        >>> from ilovetools.ml import clone_pipeline  # Full name
        >>> cloned = clone_pipeline(pipeline)
    
    Notes:
        - Create independent copy
        - Modify without affecting original
        - Useful for experiments
        - Functions are shared (not deep copied)
    """
    cloned = {
        'steps': [],
        'fitted': pipeline.get('fitted', False),
        'params': pipeline.get('params', {}).copy(),
        'metadata': pipeline.get('metadata', {}).copy(),
    }
    
    for step in pipeline['steps']:
        cloned['steps'].append({
            'name': step['name'],
            'function': step['function'],  # Shared reference
            'params': step['params'].copy(),
        })
    
    return cloned


# Create alias
clone_pipe = clone_pipeline


def pipeline_summary(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get pipeline summary statistics.
    
    Alias: pipe_summary()
    
    Args:
        pipeline: Pipeline object
    
    Returns:
        dict: Summary information
    
    Examples:
        >>> from ilovetools.ml import create_pipe, add_step, pipe_summary  # Short aliases
        
        >>> pipeline = create_pipe()
        >>> pipeline = add_step(pipeline, 'scaler', lambda x: x)
        >>> pipeline = add_step(pipeline, 'encoder', lambda x: x)
        >>> 
        >>> summary = pipe_summary(pipeline)
        >>> print(summary['n_steps'])
        2
        >>> print(summary['step_names'])
        ['scaler', 'encoder']
        
        >>> from ilovetools.ml import pipeline_summary  # Full name
        >>> summary = pipeline_summary(pipeline)
    
    Notes:
        - Quick overview
        - Step count and names
        - Fitted status
        - Parameter count
    """
    step_names = [step['name'] for step in pipeline['steps']]
    
    total_params = sum(len(step['params']) for step in pipeline['steps'])
    
    return {
        'n_steps': len(pipeline['steps']),
        'step_names': step_names,
        'fitted': pipeline.get('fitted', False),
        'total_params': total_params,
        'has_metadata': 'metadata' in pipeline,
    }


# Create alias
pipe_summary = pipeline_summary
