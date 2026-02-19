#!/usr/bin/env python3
"""Simple script to truncate app.py to just the valid Python code."""

# Read the file as binary to avoid encoding issues
with open('app.py', 'rb') as f:
    content = f.read()

# Find the last occurrence of 'app.run(debug=True)'
search_bytes = b'app.run(debug=True)'
idx = content.rfind(search_bytes)

print(f'Found app.run(debug=True) at position: {idx}')

if idx != -1:
    # Calculate where to cut - after 'app.run(debug=True)'
    # We need to include the closing parenthesis
    end_idx = idx + len(search_bytes)
    
    # Truncate the content
    new_content = content[:end_idx]
    
    # Write back
    with open('app.py', 'wb') as f:
        f.write(new_content)
    
    print(f'File truncated successfully! New length: {len(new_content)}')
else:
    print('Could not find app.run(debug=True)')
