# il2cpp-strings-patcher
Utilities to extract and modify string literals in unencrypted global-metadata.dat file.
## Usage
### Install
The Python package is available on PyPI.
```bash
pip install il2cpp-strings-patcher
```
### Extract Literals
Extract all strings from a metadata file. Unlike [Il2CppDumper](https://github.com/Perfare/Il2CppDumper), this tool only extracts the text, and the image offset is not dumped.
```python
from il2cpp_strings import StringsPatcher

with open('/path/to/global-metadata.dat', 'r') as f:
    patcher = StringsPatcher(f)
    strings = [x.original_string for x in f.literals]
```
### Modify Literals and Save
```python
patcher.patch_literals({
    'old_literal_content1': 'new_literal_content1',
    'old_literal_content2': 'new_literal_content2',
})
# Generate new global-metadata.dat file
result = patcher.generate_patched_file()
with open('/path/to/new-global-metadata.dat', 'w') as f:
    f.write(result)
```
Or, if your need to match the original string and generate patched string in custom way:
```python
for literal in patcher.literals:
    # Replace all string literals that start with "some-string" with "my-string"
    if literal.original_string.startswith('some-string'):
        literal.patch('my-string')
result = patcher.generate_patched_file()
``` 