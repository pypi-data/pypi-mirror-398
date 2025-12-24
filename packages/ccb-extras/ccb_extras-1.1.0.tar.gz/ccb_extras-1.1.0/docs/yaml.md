# yaml.py

`YamlFile` simplifies working with YAML files, especially application config files.

- **Read and write YAML files**: Map a YAML file to a Python dictionary.
- **Default values**: Initialize the file with default YAML values if the file does not exist.
- **Stable formatting**: File formatting is preserved as much as possible, courtesy of the `ruamel-yaml` dependency.
- **Nested keys**: Simple accessor to get and set values deep in a hierarchy.

## Example Usage

### Get a dictionary from a file.

*config.yaml* (created and formatted manually)

```yaml
cookies:
  key1: value1
  key2: value2
```

*python*

```python
cfg = YamlFile('config.yaml')
print(type(cfg.get_value('cookies')))  # <class 'ruamel.yaml.comments.CommentedMap'>
print(cfg.get_value('cookies'))  # {'key1': 'value1', 'key2': 'value2'}
requests.get('https://…', cookies=cfg.get_value('cookies'))
```

### Dump the document to a string.

*python*

```python
print(YamlFile('config.yaml').to_string)
```

*output*

```
%YAML 1.2
---
cookies:
  key1: value1
  key2: value2
```

### Get and set a data structure in a file.

*python*

```python
identifiers = YamlFile('identifiers.yaml')
identifiers.set_value('ids', ['test1', 'test2', 'test3'])
print(type(identifiers.get_value('ids')))  # <class 'list'>
print(identifiers.get_value('ids'))  # ['test1', 'test2', 'test3']
```

*identifiers.yaml* (automatically created and formatted by `YamlFile`)

```yaml
%YAML 1.2
--- {ids: [test1, test2, test3]}
```

### Read and write with hierarchical keys.

*python*

```python
yaml = YamlFile('test.yaml')
yaml.set_delimited_value("127.0.0.1", 'localhost', key_delimiter='.')
print(yaml.get_delimited_value("127/0/0/1", key_delimiter='/'))  # localhost
```

*test.yaml*

```yaml
%YAML 1.2
--- {'127': {'0': {'0': {'1': localhost}}}}
```

### Initialize a file with default values.

*python*

```python
defaults = """
    a: b
    c: 123
"""
yaml = YamlFile('defaults.yaml', default_values=defaults)
print(yaml.get_value('c'))  # 123
```

*defaults.yaml*

```yaml
%YAML 1.2
---
a: b
c: 123
```
