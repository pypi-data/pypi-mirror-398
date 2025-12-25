# confee vs OmegaConf Comparison

**Language:** [한국어](./COMPARISON.ko.md) | English

## 🔍 Detailed Analysis

### 1️⃣ **File Loading & Merging**

#### OmegaConf Way
```python
from omegaconf import OmegaConf

conf = OmegaConf.load(config_file_path)
conf = OmegaConf.merge(*raw_confs)
```

#### confee ✅
```python
from confee import ConfigBase

class AppConfig(ConfigBase):
    name: str
    debug: bool = False

# Unified parser handles everything
config = AppConfig.load(config_file="config.yaml")
```

**Improvements:**
- ✅ Automatic YAML/JSON detection
- ✅ Type validation with Pydantic
- ✅ IDE autocomplete support
- ✅ Simpler API

---

### 2️⃣ **Environment Variable Override**

#### OmegaConf Way
```python
def omegaconf_from_env(parameter_cls):
    dotlist_keys = get_dotlist_keys(parameter_cls)
    for key in dotlist_keys:
        key_upper = key.upper()
        if key_upper in os.environ:
            dotlist.append(f"{key}={os.environ[key_upper]}")
    return OmegaConf.from_dotlist(dotlist)
```

#### confee ✅
```python
# Automatically handles CONFEE_ prefix for env vars
# CONFEE_DEBUG=true → debug=True
config = AppConfig.load()

# Custom prefix support
config = AppConfig.load(env_prefix="MYAPP_")
```

**Improvements:**
- ✅ Automatic prefix handling
- ✅ Custom prefix support
- ✅ Type coercion (true/yes/1/on → Boolean)
- ✅ Nested field support (CONFEE_DATABASE_HOST)

---

### 3️⃣ **CLI Override**

#### OmegaConf Way
```python
conf = OmegaConf.from_cli(args_list)
```

#### confee ✅
```python
# Automatically collects CLI args
config = AppConfig.load()

# Or explicitly
config = AppConfig.load(cli_args=["debug=true", "workers=8"])
```

**Improvements:**
- ✅ Clear key=value format
- ✅ Automatic type conversion
- ✅ Flexible boolean handling (true/yes/1/on)
- ✅ Nested field support (database.host=localhost)

---

### 4️⃣ **Nested Configuration**

#### OmegaConf Way
```python
def get_dotlist_keys(cls, root=''):
    for name, field in cls.__fields__.items():
        cur_name = root + "." + name if root else name
        if isinstance(field.annotation, ModelMetaclass):
            outputs.extend(get_dotlist_keys(field.annotation, cur_name))
```

#### confee ✅
```python
class DatabaseConfig(ConfigBase):
    host: str
    port: int

class AppConfig(ConfigBase):
    database: DatabaseConfig

# Nested structure works automatically
config = AppConfig.load(cli_args=["database.host=localhost"])
print(config.database.host)  # "localhost"
```

**Improvements:**
- ✅ Cleaner type definition
- ✅ IDE autocomplete support
- ✅ Nested access in CLI/ENV (a.b.c=value)
- ✅ Runtime validation

---

### 5️⃣ **Type Validation**

#### OmegaConf Way
```python
output_param = parameter_cls.parse_obj(OmegaConf.to_container(conf))
```

#### confee ✅
```python
# Automatic validation with Pydantic V2
config = AppConfig(name="myapp", workers=8)

# Or
config = AppConfig.from_dict(data)

# Clear error messages on type errors
```

**Improvements:**
- ✅ Pydantic V2 latest features
- ✅ Better error messages
- ✅ JSON Schema generation capability

---

### 6️⃣ **File Reference** 🆕

#### OmegaConf Way
```python
# Not supported
```

#### confee ✅
```yaml
# config.yaml
api_key: "@file:secrets/api_key.txt"
database: "@config:configs/database.yaml"
```

**Improvements:**
- ✅ Text file reference (@file:)
- ✅ YAML file reference (@config:)
- ✅ Nested file references support
- ✅ Sensitive information separation

---

### 7️⃣ **Auto Help Generation** 🆕

#### OmegaConf Way
```python
def make_help_str(parameter_cls, config_param_str: str):
    # Complex formatting logic
    help_str = f'Usage: {sys.argv[0]} [Arguments]\n'
    # ... complicated processing
```

#### confee ✅
```python
# Automatic help generation with --help flag
python app.py --help

# Custom help flags
config = AppConfig.load(help_flags=["--help", "-h", "--info"])
```

**Improvements:**
- ✅ Automatic help generation
- ✅ Shows all options and defaults
- ✅ Custom help flag support

---

### 8️⃣ **Parse Order Control** 🆕

#### OmegaConf Way
```python
# Fixed order
# File → Env → CLI
```

#### confee ✅
```python
# Default: CLI > Env > File
config = AppConfig.load(config_file="config.yaml")

# Custom order
config = AppConfig.load(
    config_file="config.yaml",
    source_order=["file", "env"]  # Use only file and env
)
```

**Improvements:**
- ✅ Freely control parsing order
- ✅ Use only specific sources

---

### 9️⃣ **Configuration Inheritance**

#### OmegaConf Way
```python
# Manual merge handling
parent_dict = parent.model_dump()
child_dict = child.model_dump()
merged = {**parent_dict, **child_dict}
```

#### confee ✅
```python
# Simple override_with() method
defaults = AppConfig(host="prod-host")
custom = AppConfig(host="localhost")
merged = custom.override_with(defaults)
```

**Improvements:**
- ✅ Clear API (override_with)
- ✅ Explicit parent-child relationship

---

## 📊 Feature Comparison Table

| Feature | OmegaConf | confee | Notes |
|---------|-----------|--------|-------|
| File loading | ✅ | ✅ | YAML/JSON support |
| CLI override | ✅ | ✅ | key=value format |
| Environment variables | ✅ | ✅ | Prefix support |
| Multi-file merge | ✅ | ✅ | Automatic merging |
| Nested config | ✅ | ✅ | Pydantic support |
| Type validation | ✅ | ✅ | Pydantic V2 |
| Type hints/IDE | ❌ | ✅ | Autocomplete support |
| Strict/Non-strict mode | ❌ | ✅ | Mode selection |
| File references (@file:, @config:) | ❌ | ✅ | Sensitive info separation |
| Auto help generation | ✅ (complex) | ✅ (simple) | --help support |
| Nested CLI/ENV | ❌ | ✅ | database.host=value |
| Parse order control | ❌ | ✅ | source_order parameter |
| Configuration inheritance | Manual | ✅ | override_with() |

---

## 🎯 Migration Guide

### Before (OmegaConf Way)
```python
from omegaconf import OmegaConf

def load_param(parameter_cls, config_file_path=None, args_list=None):
    raw_confs = []
    
    if os.path.exists(config_file_path):
        raw_confs.append(OmegaConf.load(config_file_path))
    
    raw_confs.append(omegaconf_from_env(parameter_cls))
    raw_confs.append(OmegaConf.from_cli(args_list))
    
    conf = OmegaConf.merge(*raw_confs)
    return parameter_cls.parse_obj(OmegaConf.to_container(conf))
```

### After (confee)
```python
from confee import ConfigBase

class AppConfig(ConfigBase):
    name: str
    debug: bool = False

# One line is enough!
config = AppConfig.load(config_file="config.yaml")
```

---

## ✨ Key Improvements

1. **Simpler API** — Remove boilerplate code
2. **Type Safety** — Strong validation with Pydantic V2
3. **IDE Support** — Autocomplete and type hints
4. **Extensibility** — File references, inheritance, etc.
5. **Better Documentation** — Clear usage examples

---

## 🎓 When to Use What

### Use OmegaConf When:
- You need maximum flexibility with dynamic configs
- Your configuration structure is highly variable
- You're already familiar with OmegaConf patterns

### Use confee When:
- You want type-safe configuration with IDE support
- You prefer Pydantic-style configuration
- You need modern Python features (3.8+)
- You want simpler, more readable code

---

## 📚 Resources

- **confee GitHub**: https://github.com/bestend/confee
- **OmegaConf**: https://hydra.cc/docs/upgrades/0.11_to_1.0/changes_to_config_loader/
- **Pydantic**: https://docs.pydantic.dev/

---

## 🏁 Conclusion

confee combines the best features of OmegaConf with modern Python practices, offering a simpler, more type-safe, and more developer-friendly configuration management solution.

---

**Language:** [한국어](./comparison.ko.md) | English

