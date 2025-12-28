# Easy File

<p align="center">
<a href="https://pypi.python.org/pypi/easy_file">
    <img src="https://img.shields.io/pypi/v/easy_file.svg" alt="PyPI Version">
</a>
<a href="https://pypi.python.org/pypi/easy_file">
    <img src="https://img.shields.io/pypi/pyversions/easy_file.svg" alt="Python Versions">
</a>
<a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
</a>
<a href="https://github.com/ruslan-rv-ua/easy_file/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/ruslan-rv-ua/easy_file/release.yml" alt="Build Status">
</a>
</p>

**Files for humans.**

Easy File is a modern, type-safe file operations library that extends Python's `pathlib.Path` with powerful features like fast JSON/YAML serialization, atomic writes, async support, and automatic directory creation.

## Why Easy File?

```python
# Standard library
import pathlib
import json

path = pathlib.Path("config/app.json")
path.parent.mkdir(parents=True, exist_ok=True)
with open(path, 'w', encoding='utf-8') as f:
    json.dump({"name": "My App"}, f, indent=2)

# Easy File
from easy_file import File

File("config/app.json").dump_json({"name": "My App"})
```

## Features

### 🚀 **Performance**
- **1.5-2× faster** JSON/YAML operations using [msgspec](https://github.com/jcrist/msgspec)
- Efficient async I/O with `asyncio.to_thread()`

### 🛡️ **Safety**
- **Atomic writes** guarantee data integrity
- **Type-safe** deserialization with TypedDict and dataclasses
- **UTF-8 by default** - no more encoding headaches

### 🎯 **Convenience**
- **Automatic directory creation** - no more `mkdir(parents=True)`
- **Intuitive API** - method chaining and fluent interfaces
- **Full pathlib compatibility** - drop-in replacement for `Path`

### ⚡ **Modern Python**
- Full async/await support
- Type hints everywhere
- Python 3.12+ compatible

## Installation

```bash
pip install easy_file
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add easy_file
```

## Quick Start

### Basic File Operations

```python
from easy_file import File

# Read and write text (UTF-8 by default)
f = File("data.txt")
f.write_text("Hello World!")
content = f.read_text()  # "Hello World!"

# Binary operations
f.write_bytes(b"\x00\x01\x02")
data = f.read_bytes()  # b"\x00\x01\x02"

# Append text
f.append_text("\nNew line")

# File size
print(f"File size: {f.size} bytes")
```

### JSON Operations

```python
# Simple JSON
config = File("config.json")
config.dump_json({
    "name": "My App",
    "version": "1.0.0",
    "debug": True
})

data = config.load_json()
print(data["name"])  # "My App"

# Compact JSON (no formatting)
config.dump_json(data, indent=0)
```

### YAML Operations

```python
# YAML serialization
settings = File("settings.yaml")
settings.dump_yaml({
    "database": {
        "host": "localhost",
        "port": 5432
    },
    "cache": {
        "enabled": True,
        "ttl": 3600
    }
})

data = settings.load_yaml()
print(data["database"]["host"])  # "localhost"
```

### File Management

```python
# Copy files (with method chaining)
source = File("document.txt").write_text("Important data")
backup = source.copy("backup/document.txt")

# Move/rename files
archived = source.move("archive/old_document.txt")

# Create file with parent directories
File("deep/nested/path/file.txt").touch_parents()
```

## Type-Safe Deserialization

Easy File supports typed deserialization with full IDE autocomplete and runtime validation.

### Using TypedDict

```python
from typing import TypedDict
from easy_file import File

class AppConfig(TypedDict):
    name: str
    version: str
    debug: bool
    max_connections: int

# Save config
config = File("config.json")
config.dump_json({
    "name": "My App",
    "version": "2.0.0",
    "debug": False,
    "max_connections": 100
})

# Load with type safety
data: AppConfig = config.load_json(AppConfig)

# IDE autocomplete works!
print(data["name"])  # ✓ Type-safe
print(data["invalid"])  # ✗ IDE warning
```

### Using Dataclasses

```python
from dataclasses import dataclass
from easy_file import File

@dataclass
class User:
    id: int
    name: str
    email: str
    is_active: bool = True

# Save user
user_file = File("user.json")
user_file.dump_json({
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "is_active": True
})

# Load with validation
user: User = user_file.load_json(User)

# Access as object attributes
print(user.name)  # "Alice"
print(user.email)  # "alice@example.com"
```

### Works with YAML too!

```python
from typing import TypedDict

class DatabaseConfig(TypedDict):
    host: str
    port: int
    username: str
    password: str

db_config = File("database.yaml")
db_config.dump_yaml({
    "host": "localhost",
    "port": 5432,
    "username": "admin",
    "password": "secret"
})

config: DatabaseConfig = db_config.load_yaml(DatabaseConfig)
print(f"Connecting to {config['host']}:{config['port']}")
```

## Async Operations

All I/O operations have async counterparts for non-blocking execution.

### Async File I/O

```python
import asyncio
from easy_file import File

async def main():
    f = File("async_data.txt")
    
    # Text operations
    await f.write_text_async("Hello async world!")
    content = await f.read_text_async()
    await f.append_text_async("\nMore content")
    
    # Binary operations
    await f.write_bytes_async(b"\x00\x01\x02")
    data = await f.read_bytes_async()
    
    # File management
    await f.copy_async("backup.txt")
    await f.move_async("archive/data.txt")

asyncio.run(main())
```

### Async JSON/YAML

```python
async def process_config():
    config = File("config.json")
    
    # Save config asynchronously
    await config.dump_json_async({
        "api_key": "secret",
        "timeout": 30
    })
    
    # Load and process
    data = await config.load_json_async()
    print(f"Timeout: {data['timeout']}s")

asyncio.run(process_config())
```

### Parallel File Reading

Read multiple files concurrently - perfect for batch processing:

```python
async def read_all_logs():
    log_files = [
        "logs/app.log",
        "logs/error.log", 
        "logs/access.log",
        "logs/debug.log"
    ]
    
    # Read all files in parallel
    contents = await File.read_many_async(log_files)
    
    for filename, content in zip(log_files, contents):
        print(f"{filename}: {len(content)} bytes")

asyncio.run(read_all_logs())
```

## Atomic Writes

Data integrity is critical. Easy File uses atomic writes to prevent data corruption.

### Automatic Atomic Writes

JSON and YAML operations use atomic writes by default:

```python
# These operations are atomic
config = File("config.json")
config.dump_json({"critical": "data"})  # ✓ Atomic

settings = File("settings.yaml")
settings.dump_yaml({"important": "config"})  # ✓ Atomic
```

### Manual Atomic Writes

Use the `atomic_write` context manager for custom atomic operations:

```python
from easy_file import File

important_file = File("critical_data.txt")

# Write atomically
with important_file.atomic_write() as f:
    f.write("Critical information\n")
    f.write("Must be written completely\n")
    # If any error occurs here, original file is unchanged

# Binary atomic write
with important_file.atomic_write(mode="wb") as f:
    f.write(b"Binary critical data")
```

### How It Works

1. Writes to a temporary file in the same directory
2. Flushes and syncs to disk
3. Atomically replaces the target file
4. Cleans up temp file on errors

This ensures your data is **never corrupted** by crashes or errors during writes.

## Error Handling

Easy File provides custom exceptions for clear error handling:

```python
from easy_file import File, JSONDecodeError, YAMLDecodeError, FileOperationError

try:
    config = File("config.json").load_json()
except JSONDecodeError as e:
    print(f"Invalid JSON format: {e}")
except FileNotFoundError:
    print("Config file not found")
except FileOperationError as e:
    print(f"File operation failed: {e}")
```

### Exception Hierarchy

```
Exception
└── FileOperationError          # Base class for all Easy File errors
    ├── JSONDecodeError         # JSON parsing failed
    └── YAMLDecodeError         # YAML parsing failed
```

## Utility Methods

### Create Files and Directories

```python
# Create file with all parent directories
File("deep/nested/path/file.txt").touch_parents()

# Alternative using write methods (creates parents automatically)
File("auto/created/dirs/data.json").dump_json({"auto": True})
```

### Append to Files

```python
log = File("app.log")

# Append text (creates file if needed)
log.append_text("Application started\n")
log.append_text("Processing data\n")
log.append_text("Application finished\n")

# Async append
await log.append_text_async("Async log entry\n")
```

### Get File Information

```python
f = File("document.txt")
f.write_text("Hello World!")

print(f"Size: {f.size} bytes")        # 12 bytes
print(f"Name: {f.name}")               # document.txt
print(f"Extension: {f.suffix}")        # .txt
print(f"Parent: {f.parent}")           # Current directory
print(f"Absolute: {f.absolute()}")     # Full path
```

## Complete API Reference

### File Creation
- `File(path)` - Create a File object

### Text Operations
- `read_text(encoding='utf-8')` - Read text from file
- `write_text(data, encoding='utf-8')` - Write text to file
- `append_text(text, encoding='utf-8')` - Append text to file
- `read_text_async(encoding='utf-8')` - Async text read
- `write_text_async(data, encoding='utf-8')` - Async text write
- `append_text_async(text, encoding='utf-8')` - Async append

### Binary Operations
- `read_bytes()` - Read bytes from file
- `write_bytes(data)` - Write bytes to file
- `read_bytes_async()` - Async bytes read
- `write_bytes_async(data)` - Async bytes write

### JSON Operations
- `load_json(type=None)` - Load JSON (optionally typed)
- `dump_json(data, indent=2)` - Save JSON with formatting
- `load_json_async(type=None)` - Async JSON load
- `dump_json_async(data, indent=2)` - Async JSON save

### YAML Operations
- `load_yaml(type=None)` - Load YAML (optionally typed)
- `dump_yaml(data)` - Save YAML
- `load_yaml_async(type=None)` - Async YAML load
- `dump_yaml_async(data)` - Async YAML save

### File Management
- `copy(target, preserve_metadata=True)` - Copy file
- `move(target)` - Move/rename file
- `copy_async(target, preserve_metadata=True)` - Async copy
- `move_async(target)` - Async move
- `touch_parents()` - Create file and parent directories
- `open(mode, encoding=None)` - Open file (UTF-8 default)
- `atomic_write(mode='w', encoding=None)` - Atomic write context manager

### Batch Operations
- `File.read_many_async(paths)` - Read multiple files in parallel (class method)

### Properties
- `size` - File size in bytes

### Inherited from pathlib.Path
All standard `pathlib.Path` methods and properties are available:
- `exists()`, `is_file()`, `is_dir()`
- `name`, `stem`, `suffix`, `parent`
- `absolute()`, `resolve()`, `relative_to()`
- `glob()`, `rglob()`, `iterdir()`
- `chmod()`, `stat()`, `unlink()`
- And many more!

## Real-World Examples

### Configuration Management

```python
from easy_file import File
from typing import TypedDict

class Config(TypedDict):
    api_key: str
    base_url: str
    timeout: int
    debug: bool

# Load config with validation
config_file = File("config.json")
if not config_file.exists():
    # Create default config
    config_file.dump_json({
        "api_key": "",
        "base_url": "https://api.example.com",
        "timeout": 30,
        "debug": False
    })

config: Config = config_file.load_json(Config)
```

### Logging System

```python
from datetime import datetime
from easy_file import File

class Logger:
    def __init__(self, log_file: str):
        self.log = File(log_file)
        self.log.touch_parents()
    
    def info(self, message: str):
        timestamp = datetime.now().isoformat()
        self.log.append_text(f"[{timestamp}] INFO: {message}\n")
    
    def error(self, message: str):
        timestamp = datetime.now().isoformat()
        self.log.append_text(f"[{timestamp}] ERROR: {message}\n")

logger = Logger("logs/app.log")
logger.info("Application started")
logger.error("Something went wrong")
```

### Data Processing Pipeline

```python
import asyncio
from easy_file import File

async def process_data_files():
    # Read all input files in parallel
    input_files = ["data1.json", "data2.json", "data3.json"]
    data_list = await File.read_many_async(input_files)
    
    # Process each file
    results = []
    for data_str in data_list:
        import json
        data = json.loads(data_str)
        # Process data...
        results.append({"processed": True, "count": len(data)})
    
    # Save results atomically
    output = File("results/summary.json")
    await output.dump_json_async({
        "total_files": len(input_files),
        "results": results
    })

asyncio.run(process_data_files())
```

### Backup System

```python
from easy_file import File
from datetime import datetime

def backup_config(source_path: str):
    source = File(source_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup/{source.stem}_{timestamp}{source.suffix}"
    
    # Create backup with metadata preserved
    backup = source.copy(backup_name, preserve_metadata=True)
    print(f"Backed up to: {backup}")

backup_config("config.json")
```

## Migration Guide

### From pathlib.Path

```python
# Before (pathlib)
from pathlib import Path

p = Path("data.txt")
p.write_text("content", encoding="utf-8")
content = p.read_text(encoding="utf-8")

# After (easy_file)
from easy_file import File

f = File("data.txt")
f.write_text("content")  # UTF-8 by default
content = f.read_text()  # UTF-8 by default
```

### From open() + json

```python
# Before
import json
from pathlib import Path

path = Path("config.json")
path.parent.mkdir(parents=True, exist_ok=True)
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

with open(path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# After
from easy_file import File

File("config.json").dump_json(data)
config = File("config.json").load_json()
```

## Performance

Easy File is built for speed using [msgspec](https://github.com/jcrist/msgspec):

- **JSON**: ~1.5-2× faster than standard `json` module
- **YAML**: ~1.5-2× faster than PyYAML
- **Minimal overhead**: Thin wrapper around msgspec and pathlib
- **Efficient async**: Uses `asyncio.to_thread()` for optimal performance

## Requirements

- Python 3.12+
- msgspec >= 0.18.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Install development dependencies (`uv sync`)
4. Make your changes and add tests
5. Run tests (`uv run pytest`)
6. Run type checking (`uv run mypy src/`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **GitHub**: [https://github.com/ruslan-rv-ua/easy_file](https://github.com/ruslan-rv-ua/easy_file)
- **PyPI**: [https://pypi.org/project/easy_file/](https://pypi.org/project/easy_file/)
- **Issues**: [https://github.com/ruslan-rv-ua/easy_file/issues](https://github.com/ruslan-rv-ua/easy_file/issues)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

Made with ❤️ by [Ruslan Iskov](https://github.com/ruslan-rv-ua)