from ...imports import *
def is_string_in_range(string, size_range):
    """Check if string length is within the given range."""
    if not isinstance(string, str):
        return False
    str_length = len(string.strip())
    return size_range[0] <= str_length <= size_range[1]

def title_add(current_string="", size_range=None):
    """Pads the string to reach or approach the max range."""
    if not size_range or not isinstance(current_string, str):
        return current_string

    title_potentials = [
        'The Daily Dialectics', 
        'Daily Dialectics', 'thedailydialectics', 'TDD'
    ]
    
    result = current_string.strip()
    str_space = ' | '
    target_min, target_max = size_range[0], size_range[1]

    # If already in range, return as is
    if is_string_in_range(result, size_range):
        return result

    # Pad until within or as close as possible to max range
    while len(result) < target_min:
        remaining_space = target_max - len(result)
        if remaining_space <= len(str_space):
            break

        # Find the longest potential that fits
        best_fit = None
        for potential in sorted(title_potentials, key=len, reverse=True):
            addition = f"{str_space}{potential}"
            if len(result) + len(addition) <= target_max:
                best_fit = addition
                break
        
        if best_fit:
            result += best_fit
        else:
            break  # No more fitting options

    return result

def pad_to_max(typ, string):
    """Pad string to reach or approach the max range."""
    if not isinstance(string, str):
        return ""
    
    string = string.strip()
    limits = META_VARS.get(typ)
    if not limits:
        return string

    max_range = limits["max"]
    
    # If already in or above max range, return as is
    if len(string) >= max_range[0]:
        return string
    
    # Pad to reach max range
    return title_add(string, max_range)

def process_metadata(data):
    """Process all metadata fields to target max ranges."""
    if not isinstance(data, dict):
        return data

    # Process title
    if 'title' in data:
        data['title'] = pad_to_max('title', data['title'])
    
    # Process description
    if 'description' in data:
        data['description'] = pad_to_max('description', data['description'])
    
    # Add other fields as needed
    return data


