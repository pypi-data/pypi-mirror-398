#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json


def json2code(data: list) -> str:
    """
    Convert data to Python code according to the specified rules.
    Args:
        data: List of variable dictionaries to convert
    Returns: Generated Python code as a string
    """
    # Ensure the data is a list
    if not isinstance(data, list):
        raise ValueError("Data must be a list")
    
    generated_code = []
    
    for element in data:
        key = element.get('key', '')
        dual = element.get('dual', False)
        pos = element.get('pos', [])
        neg = element.get('neg', [])
        
        # Check if pos is empty
        if not pos:
            print(f"Warning: pos is empty for key '{key}', skipping this element.")
            continue
        
        # Check if neg is empty when dual is enabled
        if dual and not neg:
            print(f"Warning: neg is empty for key '{key}' with dual=True, skipping this element.")
            continue
        
        # Step 2: Generate pk and epk if dual is enabled
        pk = key
        epk = None
        if dual:
            if pk.startswith('E'):
                epk = f'E_{pk}'
            else:
                epk = f'E{pk}'
        
        # Step 3: Process pos list
        pos_translations = []
        for item in pos:
            method = item.get('method', '')
            x = item.get('x', 0)
            y = item.get('y', 0)
            pos_translations.append(f"{method}({x}, {y})")
        
        # Format posv based on length
        if len(pos_translations) > 1:
            posv = f"[{', '.join(pos_translations)}]"
        else:
            posv = pos_translations[0]
        
        # Step 4: Process neg list if dual is enabled
        negv = None
        if dual:
            neg_translations = []
            for item in neg:
                method = item.get('method', '')
                x = item.get('x', 0)
                y = item.get('y', 0)
                neg_translations.append(f"{method}({x}, {y})")
            
            # Format negv based on length
            if len(neg_translations) > 1:
                negv = f"[{', '.join(neg_translations)}]"
            else:
                negv = neg_translations[0]
        
        # Step 6: Generate code lines for this element
        element_code = []
        
        # Base line for pos
        element_code.append(f"{pk} = {posv}")
        
        # Additional lines if dual is enabled
        if dual and epk and negv:
            element_code.append(f"{epk} = {negv}")
            element_code.append(f"if SIDE == 1: {pk}, {epk} = {epk}, {pk}")
        
        element_code.append('')  # empty

        # Add to generated code
        generated_code.extend(element_code)
    
    # Step 7: Join all lines and return
    return '\n'.join(generated_code)


# Test the function
if __name__ == "__main__":
    # Read the test.json file for testing
    with open('test.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    code = json2code(data)
    print(code)