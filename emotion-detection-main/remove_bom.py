#!/usr/bin/env python3
"""Script to remove BOM from app.py."""

# Read the file as binary
with open('app.py', 'rb') as f:
    content = f.read()

# Check if file starts with BOM
print(f'First 5 bytes: {repr(content[:5])}')

# Remove BOM if present (UTF-8 BOM is 0xEF 0xBB 0xBF)
if content.startswith(b'\xef\xbb\xbf'):
    print('BOM found! Removing...')
    content = content[3:]
elif content.startswith(b'\xff\xfe'):
    print('UTF-16 LE BOM found! This file might be corrupted.')
elif content.startswith(b'\xfe\xff'):
    print('UTF-16 BE BOM found! This file might be corrupted.')
else:
    print('No standard BOM found. Checking for other issues...')

# Also check for U+FEFF anywhere in the file
if b'\xef\xbb\xbf' in content:
    print('BOM found in middle of file! Removing all BOMs...')
    content = content.replace(b'\xef\xbb\xbf', b'')

# Write back without BOM
with open('app.py', 'wb') as f:
    f.write(content)

print(f'File saved. New length: {len(content)}')
print(f'First 5 bytes now: {repr(content[:5])}')
