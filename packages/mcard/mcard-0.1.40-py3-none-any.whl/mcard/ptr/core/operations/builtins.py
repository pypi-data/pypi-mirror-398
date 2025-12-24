"""
Core builtin operations for PythonRuntime.
"""

import json
from typing import Any, Dict

from mcard import MCard


def op_identity(impl: Dict, target: MCard, ctx: Dict) -> Any:
    """Identity operation - returns target content unchanged."""
    return target.get_content()


def op_transform(impl: Dict, target: MCard, ctx: Dict) -> Any:
    """Transform operation - applies a named transformation."""
    transforms = {
        'upper_case': lambda t: t.get_content().decode('utf-8').upper().encode('utf-8'),
        'count_bytes': lambda t: len(t.get_content()),
    }
    func = impl.get('transform_function')
    return transforms.get(func, lambda t: t.get_content())(target)


def op_arithmetic(impl: Dict, target: MCard, ctx: Dict) -> Any:
    """Arithmetic operation on numeric target content."""
    params = {**impl.get('params', {}), **ctx}
    op, operand = params.get('op'), params.get('operand')
    
    try:
        val = float(target.get_content().decode('utf-8'))
    except ValueError:
        return "Error: Target content is not a valid number"
    
    ops = {
        'add': lambda x, y: x + y,
        'sub': lambda x, y: x - y,
        'mul': lambda x, y: x * y,
        'div': lambda x, y: x / y if y != 0 else "Error: Division by zero"
    }
    return ops.get(op, lambda x, y: f"Error: Unknown operation '{op}'")(val, operand)


def op_string(impl: Dict, target: MCard, ctx: Dict) -> Any:
    """String operation on target content."""
    params = {**impl.get('params', {}), **ctx}
    func = params.get('func')
    s = target.get_content().decode('utf-8')
    
    ops = {
        'reverse': lambda: s[::-1],
        'len': lambda: len(s),
        'split': lambda: s.split(params.get('delimiter', ' '))
    }
    return ops.get(func, lambda: f"Error: Unknown function '{func}'")()


def op_fetch_url(impl: Dict, target: MCard, ctx: Dict) -> Any:
    """Fetch content from a URL."""
    import urllib.request
    url = target.get_content().decode('utf-8').strip()
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.read().decode('utf-8')[:1000]
    except Exception as e:
        return f"Error fetching URL: {e}"


def op_session_record(impl: Dict, target: MCard, ctx: Dict) -> Any:
    """P2P Session Recording operation."""
    config = impl.get('config', {})
    ctx_params = ctx.get('params', {})
    
    # Extract session_id from various sources
    session_id = ctx.get('sessionId') or ctx_params.get('sessionId')
    
    # Check config with potential interpolation
    if not session_id and 'sessionId' in config:
        val = config['sessionId']
        if isinstance(val, str) and val.startswith('${') and val.endswith('}'):
            key = val[9:-1]  # strip '${params.' and '}'
            if '.' in key:
                key = key.split('.')[-1]
            session_id = ctx.get(key) or ctx_params.get(key)
        else:
            session_id = val

    # Fallback to target content inspection
    if not session_id:
        try:
            content = target.get_content().decode('utf-8')
            data = json.loads(content)
            if isinstance(data, dict):
                session_id = data.get('sessionId')
        except:
            pass
    
    if not session_id:
        return {'success': False, 'error': 'session_id is required'}
        
    return {'success': True, 'session_id': session_id, 'recorded': True}
