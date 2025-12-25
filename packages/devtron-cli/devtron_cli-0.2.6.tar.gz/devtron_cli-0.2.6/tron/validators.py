import re

def validate_label_key(key):
    """
    Validate a label key according to the specified rules.
    
    Args:
        key (str): The label key to validate
        
    Returns:
        dict: Validation result with 'success' and 'error' fields
    """
    if not key:
        return {
            'success': False,
            'error': 'Label key is required'
        }
    
    # Check if key starts with devtron.ai/ - skip most validations
    if key.startswith('devtron.ai/'):
        # Only validate that key is not empty (already done above)
        return {'success': True}
    
    # Count slashes in key
    slash_count = key.count('/')
    
    # Maximum 1 slash is allowed
    if slash_count > 1:
        return {
            'success': False,
            'error': f'Label key can contain maximum 1 "/". Found {slash_count}'
        }
    
    # If key contains exactly 1 slash, split into prefix and suffix
    if slash_count == 1:
        parts = key.split('/', 1)
        prefix = parts[0]
        suffix = parts[1]
        
        # Validate prefix (DNS subdomain)
        if len(prefix) > 253:
            return {
                'success': False,
                'error': f'Label key prefix "{prefix}" exceeds maximum length of 253 characters'
            }
        
        # DNS subdomain validation regex
        dns_subdomain_regex = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$'
        if not re.match(dns_subdomain_regex, prefix):
            return {
                'success': False,
                'error': f'Label key prefix "{prefix}" must be a valid DNS subdomain format'
            }
        
        # Validate suffix using the general rules
        suffix_result = validate_general_label_name(suffix)
        if not suffix_result['success']:
            suffix_result['error'] = f'Label key suffix "{suffix}": {suffix_result["error"]}'
            return suffix_result
    else:
        # No slashes - validate the entire key using general rules
        general_result = validate_general_label_name(key)
        if not general_result['success']:
            general_result['error'] = f'Label key "{key}": {general_result["error"]}'
            return general_result
    
    return {'success': True}

def validate_general_label_name(name):
    """
    Validate a label name (suffix or key with no slashes) according to general rules.
    
    Args:
        name (str): The label name to validate
        
    Returns:
        dict: Validation result with 'success' and 'error' fields
    """
    # Maximum 63 characters
    if len(name) > 63:
        return {
            'success': False,
            'error': f'Must be maximum 63 characters. Found {len(name)}'
        }
    
    # Must start and end with alphanumeric character
    start_end_regex = r'^(([A-Za-z0-9].*[A-Za-z0-9])|[A-Za-z0-9])$'
    if not re.match(start_end_regex, name):
        return {
            'success': False,
            'error': 'Must start and end with an alphanumeric character'
        }
    
    # Can only contain alphanumeric chars and (-), (_), (.)
    allowed_chars_regex = r'^[A-Za-z0-9._-]+$'
    if not re.match(allowed_chars_regex, name):
        return {
            'success': False,
            'error': 'Can only contain alphanumeric characters and (-), (_), (.)'
        }
    
    return {'success': True}

def validate_label_value(value):
    """
    Validate a label value according to the specified rules.
    
    Args:
        value (str): The label value to validate
        
    Returns:
        dict: Validation result with 'success' and 'error' fields
    """
    # Value is required
    if not value:
        return {
            'success': False,
            'error': 'Label value is required'
        }
    
    # If value starts with devtron.ai/ ignore other validations
    if value.startswith('devtron.ai/'):
        return {'success': True}
    
    # Apply base label validation (same as general name validation)
    return validate_general_label_name(value)

def validate_labels(labels):
    """
    Validate a list of labels according to all specified rules.
    
    Args:
        labels (list): List of label dictionaries with 'key' and 'value' fields
        
    Returns:
        dict: Validation result with 'success' and 'errors' fields
    """
    if not labels:
        return {'success': True}  # Empty labels list is valid
    
    errors = []
    
    for i, label in enumerate(labels):
        # Validate key
        key_result = validate_label_key(label.get('key', ''))
        if not key_result['success']:
            errors.append(f"Label {i + 1} key: {key_result['error']}")
        
        # Validate value
        value_result = validate_label_value(label.get('value', ''))
        if not value_result['success']:
            errors.append(f"Label {i + 1} value: {value_result['error']}")
    
    if errors:
        return {
            'success': False,
            'errors': errors
        }
    
    return {'success': True}
