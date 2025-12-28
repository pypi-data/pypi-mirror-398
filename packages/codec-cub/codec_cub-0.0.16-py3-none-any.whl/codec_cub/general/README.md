# General File Handling Utilities

Core file handling abstractions and utilities used across codec-cub for file I/O, locking, monitoring, and metadata management.

## Overview

The `general` module provides foundational file handling components that power codec implementations, storage backends, and configuration management throughout codec-cub. It offers a clean abstraction layer with:

- **BaseFileHandler** - Protocol-based file handler base class
- **FileLock** - Cross-platform advisory file locking
- **FileInfo** - File metadata introspection and reporting
- **File utilities** - Touch, hashing, change detection, watching
- **TextIO utilities** - Standard stream helpers (stdout, stderr, null)
- **MockText** - StringIO-backed handler for testing

## Architecture

```
general/
├── base_file_handler.py  # BaseFileHandler[T] protocol and implementation
├── file_info.py          # FileInfo class for metadata (size, timestamps, mime)
├── file_lock.py          # FileLock for cross-platform advisory locking
├── helpers.py            # touch(), get_file_hash(), has_file_changed(), FileWatcher
├── mock_text.py          # MockText for in-memory testing
├── textio_utility.py     # stdout, stderr, NULL_FILE helpers
└── README.md             # This file
```

## Quick Start

### BaseFileHandler

Create custom file handlers by extending `BaseFileHandler`:

```python
from codec_cub.general.base_file_handler import BaseFileHandler

class CustomHandler(BaseFileHandler[dict]):
    """Custom file handler for your format."""

    def read(self, **kwargs) -> dict:
        """Read and parse file contents."""
        with self.handle() as f:
            return parse_custom_format(f.read())

    def write(self, data: dict, **kwargs) -> None:
        """Write data to file."""
        with self.handle() as f:
            f.write(format_custom_data(data))

# Use it
handler = CustomHandler(file="data.custom", touch=True)
data = handler.read()
handler.write({"updated": True})
```

### File Utilities

```python
from codec_cub.general import touch, get_file_hash, has_file_changed, FileWatcher

# Create file/directory
touch("path/to/file.txt", mkdir=True, create_file=True)

# Get file hash for change detection
hash1 = get_file_hash("config.json")
# ... modify file ...
hash2 = get_file_hash("config.json")
assert hash1 != hash2

# Check if file changed
if has_file_changed("data.db", last_hash):
    # Reload data
    pass

# Watch file for changes
watcher = FileWatcher("important.log")
if watcher.changed():
    # File was modified
    process_new_logs()
```

### File Locking

```python
from codec_cub.general.file_lock import FileLock
from pathlib import Path

# Prevent concurrent writes
lock_file = Path("data.json.lock")
with FileLock(lock_file):
    # Exclusive access - other processes will wait
    data = read_json("data.json")
    data["counter"] += 1
    write_json("data.json", data)
# Lock released automatically
```

### File Metadata

```python
from codec_cub.general.file_info import FileInfo

info = FileInfo("report.pdf")
print(f"Size: {info.size_bytes} bytes ({info.size_human})")
print(f"Modified: {info.modified_time}")
print(f"Created: {info.created_time}")
print(f"MIME: {info.mime_type}")
print(f"Extension: {info.extension}")
print(f"Is image: {info.is_image}")
print(f"Is text: {info.is_text}")

# Quick checks
if info.exists and info.size_bytes > 0:
    process_file(info.path)
```

### TextIO Utilities

```python
from codec_cub.general.textio_utility import stdout, stderr, NULL_FILE

# Context-managed stdout/stderr
with stdout() as out:
    out.write("This goes to stdout\n")

with stderr() as err:
    err.write("This goes to stderr\n")

# Null file for discarding output
with open(NULL_FILE, "w") as devnull:
    # All writes go nowhere
    devnull.write("Discarded")
```

### MockText (for testing)

```python
from codec_cub.general.mock_text import MockText

# In-memory text file for testing
mock = MockText(initial_content="line1\nline2\nline3\n")

# Read like a file
with mock.handle() as f:
    content = f.read()

# Write like a file
with mock.handle() as f:
    f.write("new content\n")

# Get accumulated content
assert mock.get_value() == "new content\n"
```

## Core Components

### BaseFileHandler[T]

**Protocol-based base class** for file handlers providing:

```python
class BaseFileHandler[T](FileHandlerProtocol):
    """Minimal base for file-backed handlers."""

    file: Path               # Path to file
    touch: bool              # Create if missing
    encoding: str | None     # File encoding

    def handle(self) -> IO:  # Get file handle (context manager)
    def read(self) -> T:     # Abstract: read and parse
    def write(self, data: T) -> None:  # Abstract: format and write
    def close() -> None:     # Close file handle
```

**Key features:**
- Generic type parameter `[T]` for type-safe data
- Lazy file opening (opens on first access)
- Context manager support (`with handler: ...`)
- Lock hooks for concurrent access control
- Touch support for auto-creating files/dirs

**Subclasses in codec-cub:**
- `JSONFileHandler` (jsons module)
- `JSONLFileHandler` (jsonl module)
- `TOMLFileHandler` (toml module)
- `YAMLFileHandler` (yaml module)
- `XMLFileHandler` (xml module)
- `MsgPackFileHandler` (message_pack module)
- `TextFileHandler` (text module)

### FileLock

**Cross-platform advisory file locking** to prevent concurrent writes:

```python
class FileLock:
    """Context manager for file locking."""

    def __init__(self, lock_file: Path, timeout: float = 10.0)
    def acquire() -> None    # Acquire lock (blocks until available)
    def release() -> None    # Release lock
```

**Features:**
- Uses `fcntl.flock()` on Unix, `msvcrt.locking()` on Windows
- Timeout support to prevent infinite blocking
- Context manager for automatic release
- Advisory locking (cooperative processes only)

**Example:**
```python
with FileLock(Path("data.lock"), timeout=5.0):
    # Critical section - only one process at a time
    modify_shared_file()
```

### FileInfo

**File metadata introspection and reporting:**

```python
class FileInfo:
    """Comprehensive file metadata."""

    path: Path              # Absolute path
    exists: bool            # File exists
    size_bytes: int         # Size in bytes
    size_human: str         # Human-readable (e.g., "1.5 MB")
    modified_time: datetime # Last modified
    created_time: datetime  # Created time
    accessed_time: datetime # Last accessed
    mime_type: str          # MIME type
    extension: str          # File extension
    is_image: bool          # Is image file
    is_text: bool           # Is text file
    is_binary: bool         # Is binary file
```

**Use cases:**
- File upload validation
- Cache invalidation
- Logging and monitoring
- Backup management
- Format detection

### File Helpers

#### touch()

Create files and directories:

```python
def touch(
    path: StrPath,
    mkdir: bool = False,
    create_file: bool = False,
    exist_ok: bool = True,
) -> Path:
    """Create file and/or parent directories."""
```

**Examples:**
```python
# Just create directories
touch("data/cache/", mkdir=True)

# Create file and directories
touch("logs/app.log", mkdir=True, create_file=True)

# Update modification time
touch("existing.txt")  # Like Unix touch command
```

#### get_file_hash()

Compute SHA256 hash for change detection:

```python
def get_file_hash(path: StrPath, algorithm: str = "sha256") -> str:
    """Compute file hash."""
```

**Example:**
```python
before_hash = get_file_hash("config.toml")
# ... edit config ...
after_hash = get_file_hash("config.toml")
if before_hash != after_hash:
    reload_config()
```

#### has_file_changed()

Check if file changed since last hash:

```python
def has_file_changed(path: StrPath, previous_hash: str) -> bool:
    """True if file changed."""
```

**Example:**
```python
last_hash = "abc123..."
if has_file_changed("data.json", last_hash):
    # File was modified
    reload_data()
```

#### FileWatcher

Monitor file for changes:

```python
class FileWatcher:
    """Watch file for modifications."""

    def __init__(self, path: StrPath)
    def changed() -> bool    # Check if file changed
    def reset() -> None      # Reset baseline
```

**Example:**
```python
watcher = FileWatcher("settings.ini")

while True:
    if watcher.changed():
        print("Settings file updated!")
        reload_settings()
        watcher.reset()
    time.sleep(1)
```

### TextIO Utilities

**Standard stream helpers:**

```python
def stdout() -> TextIO:
    """Context manager for stdout."""

def stderr() -> TextIO:
    """Context manager for stderr."""

NULL_FILE: str = os.devnull  # Platform-specific null device
```

**Use cases:**
- CLI output management
- Logging configuration
- Testing output capture
- Output redirection

## Design Patterns

### Protocol-Based Handlers

`BaseFileHandler` uses Protocol pattern for flexibility:

```python
class FileHandlerProtocol[T](Protocol):
    """Protocol all file handlers should implement."""

    file: Path
    def read(self, **kwargs) -> T: ...
    def write(self, data: T, **kwargs) -> None: ...
    def close(self) -> None: ...
```

Benefits:
- Duck typing compatible
- Easy to mock for testing
- Clear interface contract
- Type-safe with generics

### Context Manager Pattern

All handlers support context managers:

```python
with CustomHandler("data.txt") as handler:
    data = handler.read()
    # ... process ...
    handler.write(modified_data)
# Auto-close on exit
```

### Lazy Initialization

File handles open only when needed:

```python
handler = JSONFileHandler("big.json")  # No I/O yet
# ... later ...
data = handler.read()  # Opens file NOW
```

## Testing

### Using MockText

```python
def test_file_handler():
    mock = MockText(initial_content='{"test": true}')
    handler = JSONFileHandler(file=None)  # Use mock
    handler._handle = mock.handle()

    data = handler.read()
    assert data == {"test": True}
```

### Mocking BaseFileHandler

```python
from unittest.mock import Mock

def test_custom_logic():
    handler = Mock(spec=BaseFileHandler)
    handler.read.return_value = {"mocked": "data"}

    result = process_with_handler(handler)
    assert result == expected
```

## Integration with Other Modules

### Used by codec implementations:
- `jsons/` - JSON file handling
- `jsonl/` - JSONL (line-delimited JSON)
- `toml/` - TOML configuration
- `yamls/` - YAML documents
- `xmls/` - XML parsing
- `message_pack/` - MessagePack binary
- `text/` - Plain text files

### Used by storage backends:
- Datastore implementations
- Cache managers
- Settings handlers

### Used by monitoring:
- Log file watchers
- Configuration hot-reload
- File-based triggers

## Performance Characteristics

- **touch()**: O(1) - Fast directory/file creation
- **get_file_hash()**: O(n) where n = file size (streams in chunks)
- **FileWatcher**: O(1) - Stores single hash
- **FileLock**: O(1) - System call overhead only
- **FileInfo**: O(1) - Single stat() call

## Error Handling

### Common Exceptions

```python
# File doesn't exist
try:
    info = FileInfo("missing.txt")
    if not info.exists:
        raise FileNotFoundError(f"{info.path} not found")
except FileNotFoundError:
    # Handle missing file
    pass

# Lock timeout
try:
    with FileLock(Path("data.lock"), timeout=1.0):
        process_data()
except TimeoutError:
    # Lock acquisition timed out
    log.error("Could not acquire lock")

# Permission errors
try:
    touch("/root/protected.txt", create_file=True)
except PermissionError:
    # Insufficient permissions
    log.error("Permission denied")
```

## Best Practices

### 1. Always use context managers

```python
# Good
with handler.handle() as f:
    data = f.read()

# Bad
f = handler.handle()
data = f.read()
# Forgot to close!
```

### 2. Use touch=True for auto-creation

```python
# Creates parent directories automatically
handler = JSONFileHandler("data/cache/config.json", touch=True)
```

### 3. Lock for concurrent access

```python
# Multi-process safe
with FileLock(Path("shared.json.lock")):
    data = read_json("shared.json")
    data["counter"] += 1
    write_json("shared.json", data)
```

### 4. Monitor with FileWatcher

```python
# Efficient change detection
watcher = FileWatcher("config.toml")
if watcher.changed():
    reload_config()
    watcher.reset()
```

### 5. Validate with FileInfo

```python
# Check before processing
info = FileInfo(upload_path)
if not info.exists or info.size_bytes == 0:
    raise ValueError("Invalid file")
if not info.is_image:
    raise ValueError("Must be an image")
```

## Troubleshooting

### File locks not working?
- FileLock is **advisory** - all processes must cooperate
- Make sure all processes use the same lock file path
- Check timeout value - increase if processes are slow

### Touch creating wrong paths?
```python
# Be explicit about directories vs files
touch("dir/")              # Creates directory
touch("dir/file.txt")      # Creates file in directory
```

### Hash mismatches on Windows?
- Line endings may differ (CRLF vs LF)
- Use binary mode or normalize line endings
- Consider using FileWatcher which handles this

## Related Modules

- `codec_cub.jsons` - JSON file handling
- `codec_cub.text` - Text file utilities
- `codec_cub.message_pack` - Binary MessagePack
- `funcy_bear.protocols` - FileHandlerProtocol definition

## Contributing

When adding new file handlers:

1. Extend `BaseFileHandler[T]` with your type
2. Implement `read()` and `write()` methods
3. Use `self.handle()` for file access
4. Add tests with MockText
5. Document format-specific options

Keep those files handled, Bear! 🐻📁✨
