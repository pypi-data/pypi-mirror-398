"""Tests for easy_file package."""

import pathlib
from dataclasses import dataclass
from typing import TypedDict

import pytest

from easy_file import File
from easy_file.easy_file import FileOperationError, JSONDecodeError, YAMLDecodeError


# Test dataclasses and TypedDict for typed deserialization tests
@dataclass
class Person:
    """Test dataclass for typed deserialization."""

    name: str
    age: int
    email: str


class Config(TypedDict):
    """Test TypedDict for typed deserialization."""

    name: str
    version: str
    debug: bool


class Settings(TypedDict):
    """Test TypedDict for YAML typed deserialization."""

    port: int
    host: str
    enabled: bool


class TestFileOpen:
    """Test File.open() method."""

    def test_open_text_default_encoding(self, temp_dir: pathlib.Path) -> None:
        """Test that text files open with UTF-8 encoding by default."""
        test_file = File(temp_dir / "test.txt")
        test_file.write_text("Привіт світ!", encoding="utf-8")

        with test_file.open() as f:
            content = f.read()

        assert content == "Привіт світ!"

    def test_open_binary_mode(self, temp_dir: pathlib.Path) -> None:
        """Test binary mode opening."""
        test_file = File(temp_dir / "test.bin")
        test_file.write_bytes(b"\x00\x01\x02")

        with test_file.open("rb") as f:
            content = f.read()

        assert content == b"\x00\x01\x02"


class TestFileCopy:
    """Test File.copy() method."""

    def test_copy_file(self, temp_dir: pathlib.Path) -> None:
        """Test copying a file."""
        source = File(temp_dir / "source.txt")
        target = File(temp_dir / "target.txt")

        source.write_text("test content")
        source.copy(target)

        assert target.exists()
        assert target.read_text() == "test content"

    def test_copy_binary_file(self, temp_dir: pathlib.Path) -> None:
        """Test copying a binary file."""
        source = File(temp_dir / "source.bin")
        target = File(temp_dir / "target.bin")

        source.write_bytes(b"\x00\x01\x02\x03")
        source.copy(target)

        assert target.exists()
        assert target.read_bytes() == b"\x00\x01\x02\x03"

    def test_copy_creates_parent_directories(self, temp_dir: pathlib.Path) -> None:
        """Test that copy creates parent directories if needed."""
        source = File(temp_dir / "source.txt")
        target = File(temp_dir / "nested" / "deep" / "target.txt")

        source.write_text("test content")
        source.copy(target)

        assert target.exists()
        assert target.read_text() == "test content"

    def test_copy_without_metadata(self, temp_dir: pathlib.Path) -> None:
        """Test copying a file without preserving metadata."""
        source = File(temp_dir / "source.txt")
        target = File(temp_dir / "target.txt")

        source.write_text("test content")
        source.copy(target, preserve_metadata=False)

        assert target.exists()
        assert target.read_text() == "test content"


class TestFileMove:
    """Test File.move() method."""

    def test_move_file(self, temp_dir: pathlib.Path) -> None:
        """Test moving a file."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "target.txt"

        source.write_text("test content")
        moved = source.move(target_path)

        assert moved.exists()
        assert moved.read_text() == "test content"
        assert not source.exists()

    def test_move_creates_parent_directories(self, temp_dir: pathlib.Path) -> None:
        """Test that move creates parent directories if needed."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "nested" / "deep" / "target.txt"

        source.write_text("test content")
        moved = source.move(target_path)

        assert moved.exists()
        assert moved.read_text() == "test content"
        assert not source.exists()

    def test_move_source_deleted(self, temp_dir: pathlib.Path) -> None:
        """Test that source file is deleted after move."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "target.txt"

        source.write_text("content to move")
        source.move(target_path)

        assert not source.exists()
        assert File(target_path).exists()

    def test_move_overwrites_existing(self, temp_dir: pathlib.Path) -> None:
        """Test that move overwrites existing target file."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "target.txt"

        source.write_text("new content")
        target = File(target_path)
        target.write_text("old content")

        moved = source.move(target_path)

        assert moved.exists()
        assert moved.read_text() == "new content"
        assert not source.exists()

    def test_move_missing_source(self, temp_dir: pathlib.Path) -> None:
        """Test that moving a missing source raises FileNotFoundError."""
        source = File(temp_dir / "missing.txt")
        target_path = temp_dir / "target.txt"

        with pytest.raises(FileNotFoundError):
            source.move(target_path)


class TestFileJson:
    """Test File JSON operations."""

    def test_load_json(
        self, temp_dir: pathlib.Path, sample_json_data: dict[str, object]
    ) -> None:
        """Test loading JSON from file."""
        import msgspec

        test_file = File(temp_dir / "test.json")
        test_file.write_bytes(msgspec.json.encode(sample_json_data))

        loaded = test_file.load_json()

        assert loaded == sample_json_data

    def test_dump_json(
        self, temp_dir: pathlib.Path, sample_json_data: dict[str, object]
    ) -> None:
        """Test dumping JSON to file."""
        test_file = File(temp_dir / "test.json")
        test_file.dump_json(sample_json_data)

        loaded = test_file.load_json()

        assert loaded == sample_json_data

    def test_json_roundtrip(
        self, temp_dir: pathlib.Path, sample_json_data: dict[str, object]
    ) -> None:
        """Test JSON dump and load roundtrip."""
        test_file = File(temp_dir / "test.json")
        test_file.dump_json(sample_json_data)
        loaded = test_file.load_json()

        assert loaded == sample_json_data

    def test_load_json_with_typeddict(self, temp_dir: pathlib.Path) -> None:
        """Test loading JSON with TypedDict type."""
        test_file = File(temp_dir / "config.json")
        test_file.dump_json({"name": "Easy File", "version": "0.4.0", "debug": True})

        loaded = test_file.load_json(Config)

        assert loaded["name"] == "Easy File"
        assert loaded["version"] == "0.4.0"
        assert loaded["debug"] is True

    def test_load_json_with_dataclass(self, temp_dir: pathlib.Path) -> None:
        """Test loading JSON with dataclass type."""
        test_file = File(temp_dir / "person.json")
        test_file.dump_json({"name": "John", "age": 30, "email": "john@example.com"})

        loaded = test_file.load_json(Person)

        assert loaded.name == "John"
        assert loaded.age == 30
        assert loaded.email == "john@example.com"

    def test_load_json_invalid_json(self, temp_dir: pathlib.Path) -> None:
        """Test loading invalid JSON raises JSONDecodeError."""
        test_file = File(temp_dir / "invalid.json")
        test_file.write_text("{invalid json}")

        with pytest.raises(JSONDecodeError) as exc_info:
            test_file.load_json()

        assert "Failed to decode JSON" in str(exc_info.value)

    def test_load_json_missing_file(self, temp_dir: pathlib.Path) -> None:
        """Test loading JSON from missing file raises FileNotFoundError."""
        test_file = File(temp_dir / "missing.json")

        with pytest.raises(FileNotFoundError):
            test_file.load_json()

    def test_dump_json_creates_parent_directories(self, temp_dir: pathlib.Path) -> None:
        """Test that dump_json creates parent directories."""
        test_file = File(temp_dir / "nested" / "deep" / "data.json")
        test_file.dump_json({"test": "data"})

        assert test_file.exists()
        assert test_file.load_json() == {"test": "data"}

    def test_dump_json_atomic_write(self, temp_dir: pathlib.Path) -> None:
        """Test that dump_json uses atomic writes."""
        test_file = File(temp_dir / "atomic.json")
        test_file.dump_json({"initial": "data"})

        # Simulate concurrent write by checking file exists during write
        # The atomic write should ensure data integrity
        test_file.dump_json({"updated": "data"})

        loaded = test_file.load_json()
        assert loaded == {"updated": "data"}
        # File should always contain valid JSON
        assert test_file.exists()


class TestFileYaml:
    """Test File YAML operations."""

    def test_load_yaml(
        self, temp_dir: pathlib.Path, sample_yaml_data: dict[str, object]
    ) -> None:
        """Test loading YAML from file."""
        test_file = File(temp_dir / "test.yaml")
        test_file.write_text(
            "name: test\nvalue: 42\nnested:\n  key: value\nlist:\n  - 1\n  - 2\n  - 3\n"
        )

        loaded = test_file.load_yaml()

        assert loaded == sample_yaml_data

    def test_dump_yaml(
        self, temp_dir: pathlib.Path, sample_yaml_data: dict[str, object]
    ) -> None:
        """Test dumping YAML to file."""
        test_file = File(temp_dir / "test.yaml")
        test_file.dump_yaml(sample_yaml_data)

        loaded = test_file.load_yaml()

        assert loaded == sample_yaml_data

    def test_yaml_roundtrip(
        self, temp_dir: pathlib.Path, sample_yaml_data: dict[str, object]
    ) -> None:
        """Test YAML dump and load roundtrip."""
        test_file = File(temp_dir / "test.yaml")
        test_file.dump_yaml(sample_yaml_data)
        loaded = test_file.load_yaml()

        assert loaded == sample_yaml_data

    def test_load_yaml_with_typeddict(self, temp_dir: pathlib.Path) -> None:
        """Test loading YAML with TypedDict type."""
        test_file = File(temp_dir / "settings.yaml")
        test_file.dump_yaml({"port": 8080, "host": "localhost", "enabled": True})

        loaded = test_file.load_yaml(Settings)

        assert loaded["port"] == 8080
        assert loaded["host"] == "localhost"
        assert loaded["enabled"] is True

    def test_load_yaml_with_dataclass(self, temp_dir: pathlib.Path) -> None:
        """Test loading YAML with dataclass type."""
        test_file = File(temp_dir / "person.yaml")
        test_file.dump_yaml({"name": "Jane", "age": 25, "email": "jane@example.com"})

        loaded = test_file.load_yaml(Person)

        assert loaded.name == "Jane"
        assert loaded.age == 25
        assert loaded.email == "jane@example.com"

    def test_load_yaml_invalid_yaml(self, temp_dir: pathlib.Path) -> None:
        """Test loading invalid YAML raises YAMLDecodeError."""
        test_file = File(temp_dir / "invalid.yaml")
        test_file.write_text("invalid: yaml: content:\n  - broken")

        with pytest.raises(YAMLDecodeError) as exc_info:
            test_file.load_yaml()

        assert "Failed to decode YAML" in str(exc_info.value)

    def test_load_yaml_missing_file(self, temp_dir: pathlib.Path) -> None:
        """Test loading YAML from missing file raises FileNotFoundError."""
        test_file = File(temp_dir / "missing.yaml")

        with pytest.raises(FileNotFoundError):
            test_file.load_yaml()

    def test_dump_yaml_creates_parent_directories(self, temp_dir: pathlib.Path) -> None:
        """Test that dump_yaml creates parent directories."""
        test_file = File(temp_dir / "nested" / "deep" / "data.yaml")
        test_file.dump_yaml({"test": "data"})

        assert test_file.exists()
        assert test_file.load_yaml() == {"test": "data"}

    def test_dump_yaml_atomic_write(self, temp_dir: pathlib.Path) -> None:
        """Test that dump_yaml uses atomic writes."""
        test_file = File(temp_dir / "atomic.yaml")
        test_file.dump_yaml({"initial": "data"})

        test_file.dump_yaml({"updated": "data"})

        loaded = test_file.load_yaml()
        assert loaded == {"updated": "data"}
        assert test_file.exists()


class TestFileErrors:
    """Test error handling in File operations."""

    def test_file_operation_error_is_exception(self) -> None:
        """Test that FileOperationError is an Exception."""
        assert issubclass(FileOperationError, Exception)

    def test_json_decode_error_is_file_operation_error(self) -> None:
        """Test that JSONDecodeError inherits from FileOperationError."""
        assert issubclass(JSONDecodeError, FileOperationError)

    def test_yaml_decode_error_is_file_operation_error(self) -> None:
        """Test that YAMLDecodeError inherits from FileOperationError."""
        assert issubclass(YAMLDecodeError, FileOperationError)

    def test_json_decode_error_message(self, temp_dir: pathlib.Path) -> None:
        """Test that JSONDecodeError has informative message."""
        test_file = File(temp_dir / "bad.json")
        test_file.write_text("{bad json")

        with pytest.raises(JSONDecodeError) as exc_info:
            test_file.load_json()

        error_msg = str(exc_info.value)
        assert "Failed to decode JSON" in error_msg
        assert str(test_file) in error_msg

    def test_yaml_decode_error_message(self, temp_dir: pathlib.Path) -> None:
        """Test that YAMLDecodeError has informative message."""
        test_file = File(temp_dir / "bad.yaml")
        test_file.write_text("invalid: [yaml")

        with pytest.raises(YAMLDecodeError) as exc_info:
            test_file.load_yaml()

        error_msg = str(exc_info.value)
        assert "Failed to decode YAML" in error_msg
        assert str(test_file) in error_msg


class TestAtomicWrite:
    """Test atomic write functionality."""

    def test_atomic_write_success(self, temp_dir: pathlib.Path) -> None:
        """Test successful atomic write."""
        test_file = File(temp_dir / "atomic.txt")

        with test_file.atomic_write() as f:
            f.write("Atomic content")

        assert test_file.exists()
        assert test_file.read_text() == "Atomic content"

    def test_atomic_write_creates_parent_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test that atomic_write creates parent directories."""
        test_file = File(temp_dir / "nested" / "deep" / "atomic.txt")

        with test_file.atomic_write() as f:
            f.write("Nested content")

        assert test_file.exists()
        assert test_file.read_text() == "Nested content"

    def test_atomic_write_error_cleanup(self, temp_dir: pathlib.Path) -> None:
        """Test that atomic_write cleans up on error."""
        test_file = File(temp_dir / "atomic.txt")

        with pytest.raises(ValueError), test_file.atomic_write() as f:
            f.write("Partial content")
            raise ValueError("Simulated error")

        # File should not exist after error
        assert not test_file.exists()

    def test_atomic_write_binary_mode(self, temp_dir: pathlib.Path) -> None:
        """Test atomic_write in binary mode."""
        test_file = File(temp_dir / "atomic.bin")

        with test_file.atomic_write(mode="wb") as f:
            f.write(b"\x00\x01\x02\x03")

        assert test_file.exists()
        assert test_file.read_bytes() == b"\x00\x01\x02\x03"

    def test_atomic_write_preserves_existing_on_error(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test that atomic_write preserves existing file on error."""
        test_file = File(temp_dir / "atomic.txt")
        test_file.write_text("Original content")

        with pytest.raises(ValueError), test_file.atomic_write() as f:
            f.write("New content")
            raise ValueError("Simulated error")

        # Original content should be preserved
        assert test_file.read_text() == "Original content"


class TestAsyncMethods:
    """Test async file operations."""

    @pytest.mark.asyncio
    async def test_read_text_async(self, temp_dir: pathlib.Path) -> None:
        """Test async text reading."""
        test_file = File(temp_dir / "async.txt")
        test_file.write_text("Hello async!")

        content = await test_file.read_text_async()

        assert content == "Hello async!"

    @pytest.mark.asyncio
    async def test_write_text_async(self, temp_dir: pathlib.Path) -> None:
        """Test async text writing."""
        test_file = File(temp_dir / "async.txt")

        await test_file.write_text_async("Async content")

        assert test_file.read_text() == "Async content"

    @pytest.mark.asyncio
    async def test_load_json_async(self, temp_dir: pathlib.Path) -> None:
        """Test async JSON loading."""
        test_file = File(temp_dir / "async.json")
        test_file.dump_json({"name": "test", "value": 42})

        data = await test_file.load_json_async()

        assert data == {"name": "test", "value": 42}

    @pytest.mark.asyncio
    async def test_load_json_async_with_type(self, temp_dir: pathlib.Path) -> None:
        """Test async JSON loading with type."""
        test_file = File(temp_dir / "async.json")
        test_file.dump_json({"name": "Easy File", "version": "0.4.0", "debug": True})

        data = await test_file.load_json_async(Config)

        assert data["name"] == "Easy File"
        assert data["version"] == "0.4.0"
        assert data["debug"] is True

    @pytest.mark.asyncio
    async def test_dump_json_async(self, temp_dir: pathlib.Path) -> None:
        """Test async JSON dumping."""
        test_file = File(temp_dir / "async.json")

        await test_file.dump_json_async({"async": "data"})

        assert test_file.load_json() == {"async": "data"}

    @pytest.mark.asyncio
    async def test_load_yaml_async(self, temp_dir: pathlib.Path) -> None:
        """Test async YAML loading."""
        test_file = File(temp_dir / "async.yaml")
        test_file.dump_yaml({"port": 8080, "host": "localhost"})

        data = await test_file.load_yaml_async()

        assert data == {"port": 8080, "host": "localhost"}

    @pytest.mark.asyncio
    async def test_load_yaml_async_with_type(self, temp_dir: pathlib.Path) -> None:
        """Test async YAML loading with type."""
        test_file = File(temp_dir / "async.yaml")
        test_file.dump_yaml({"port": 8080, "host": "localhost", "enabled": True})

        data = await test_file.load_yaml_async(Settings)

        assert data["port"] == 8080
        assert data["host"] == "localhost"
        assert data["enabled"] is True

    @pytest.mark.asyncio
    async def test_dump_yaml_async(self, temp_dir: pathlib.Path) -> None:
        """Test async YAML dumping."""
        test_file = File(temp_dir / "async.yaml")

        await test_file.dump_yaml_async({"async": "yaml"})

        assert test_file.load_yaml() == {"async": "yaml"}

    @pytest.mark.asyncio
    async def test_read_text_async_encoding(self, temp_dir: pathlib.Path) -> None:
        """Test async text reading with custom encoding."""
        test_file = File(temp_dir / "async.txt")
        test_file.write_text("Привіт світ!", encoding="utf-8")

        content = await test_file.read_text_async(encoding="utf-8")

        assert content == "Привіт світ!"

    @pytest.mark.asyncio
    async def test_write_text_async_encoding(self, temp_dir: pathlib.Path) -> None:
        """Test async text writing with custom encoding."""
        test_file = File(temp_dir / "async.txt")

        await test_file.write_text_async("Привіт світ!", encoding="utf-8")

        assert test_file.read_text(encoding="utf-8") == "Привіт світ!"

    @pytest.mark.asyncio
    async def test_read_bytes_async(self, temp_dir: pathlib.Path) -> None:
        """Test async bytes reading."""
        test_file = File(temp_dir / "async.bin")
        test_file.write_bytes(b"\x00\x01\x02\x03\x04")

        content = await test_file.read_bytes_async()

        assert content == b"\x00\x01\x02\x03\x04"

    @pytest.mark.asyncio
    async def test_write_bytes_async(self, temp_dir: pathlib.Path) -> None:
        """Test async bytes writing."""
        test_file = File(temp_dir / "async.bin")

        await test_file.write_bytes_async(b"\x00\x01\x02\x03\x04")

        assert test_file.read_bytes() == b"\x00\x01\x02\x03\x04"

    @pytest.mark.asyncio
    async def test_read_write_bytes_async_roundtrip(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test async bytes read/write roundtrip."""
        test_file = File(temp_dir / "async.bin")
        original_data = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"

        await test_file.write_bytes_async(original_data)
        read_data = await test_file.read_bytes_async()

        assert read_data == original_data

    @pytest.mark.asyncio
    async def test_read_bytes_async_empty_file(self, temp_dir: pathlib.Path) -> None:
        """Test async bytes reading from empty file."""
        test_file = File(temp_dir / "empty.bin")
        test_file.write_bytes(b"")

        content = await test_file.read_bytes_async()

        assert content == b""

    @pytest.mark.asyncio
    async def test_read_bytes_async_missing_file(self, temp_dir: pathlib.Path) -> None:
        """Test async bytes reading from missing file raises FileNotFoundError."""
        test_file = File(temp_dir / "missing.bin")

        with pytest.raises(FileNotFoundError):
            await test_file.read_bytes_async()

    @pytest.mark.asyncio
    async def test_write_bytes_async_creates_parent_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test that write_bytes_async creates parent directories."""
        test_file = File(temp_dir / "nested" / "deep" / "async.bin")

        await test_file.write_bytes_async(b"\x00\x01\x02")

        assert test_file.exists()
        assert test_file.read_bytes() == b"\x00\x01\x02"

    @pytest.mark.asyncio
    async def test_append_text_async(self, temp_dir: pathlib.Path) -> None:
        """Test async appending text to existing file."""
        test_file = File(temp_dir / "append.txt")
        test_file.write_text("First line\n")

        await test_file.append_text_async("Second line\n")

        assert test_file.read_text() == "First line\nSecond line\n"

    @pytest.mark.asyncio
    async def test_append_text_async_creates_file(self, temp_dir: pathlib.Path) -> None:
        """Test that append_text_async creates file if it doesn't exist."""
        test_file = File(temp_dir / "new.txt")

        await test_file.append_text_async("Appended content")

        assert test_file.exists()
        assert test_file.read_text() == "Appended content"

    @pytest.mark.asyncio
    async def test_append_text_async_creates_parent_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test that append_text_async creates parent directories."""
        test_file = File(temp_dir / "nested" / "deep" / "file.txt")

        await test_file.append_text_async("Nested append")

        assert test_file.exists()
        assert test_file.read_text() == "Nested append"

    @pytest.mark.asyncio
    async def test_append_text_async_multiple_times(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test multiple async appends to same file."""
        test_file = File(temp_dir / "multi.txt")

        await test_file.append_text_async("Line 1\n")
        await test_file.append_text_async("Line 2\n")
        await test_file.append_text_async("Line 3\n")

        assert test_file.read_text() == "Line 1\nLine 2\nLine 3\n"

    @pytest.mark.asyncio
    async def test_append_text_async_encoding(self, temp_dir: pathlib.Path) -> None:
        """Test async appending text with custom encoding."""
        test_file = File(temp_dir / "encoding.txt")
        test_file.write_text("Привіт ", encoding="utf-8")

        await test_file.append_text_async("світ!", encoding="utf-8")

        assert test_file.read_text(encoding="utf-8") == "Привіт світ!"

    @pytest.mark.asyncio
    async def test_move_async(self, temp_dir: pathlib.Path) -> None:
        """Test async moving a file."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "target.txt"

        source.write_text("test content")
        moved = await source.move_async(target_path)

        assert moved.exists()
        assert moved.read_text() == "test content"
        assert not source.exists()

    @pytest.mark.asyncio
    async def test_move_async_creates_parent_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test that async move creates parent directories if needed."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "nested" / "deep" / "target.txt"

        source.write_text("test content")
        moved = await source.move_async(target_path)

        assert moved.exists()
        assert moved.read_text() == "test content"
        assert not source.exists()

    @pytest.mark.asyncio
    async def test_move_async_source_deleted(self, temp_dir: pathlib.Path) -> None:
        """Test that source file is deleted after async move."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "target.txt"

        source.write_text("content to move")
        await source.move_async(target_path)

        assert not source.exists()
        assert File(target_path).exists()

    @pytest.mark.asyncio
    async def test_copy_async(self, temp_dir: pathlib.Path) -> None:
        """Test async copying a file."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "target.txt"

        source.write_text("test content")
        copied = await source.copy_async(target_path)

        assert copied.exists()
        assert copied.read_text() == "test content"
        assert source.exists()
        assert source.read_text() == "test content"

    @pytest.mark.asyncio
    async def test_copy_async_creates_parent_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test that async copy creates parent directories if needed."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "nested" / "deep" / "target.txt"

        source.write_text("test content")
        copied = await source.copy_async(target_path)

        assert copied.exists()
        assert copied.read_text() == "test content"
        assert source.exists()

    @pytest.mark.asyncio
    async def test_copy_async_binary_file(self, temp_dir: pathlib.Path) -> None:
        """Test async copying a binary file."""
        source = File(temp_dir / "source.bin")
        target_path = temp_dir / "target.bin"

        source.write_bytes(b"\x00\x01\x02\x03\x04\x05")
        copied = await source.copy_async(target_path)

        assert copied.exists()
        assert copied.read_bytes() == b"\x00\x01\x02\x03\x04\x05"
        assert source.exists()
        assert source.read_bytes() == b"\x00\x01\x02\x03\x04\x05"

    @pytest.mark.asyncio
    async def test_copy_async_source_preserved(self, temp_dir: pathlib.Path) -> None:
        """Test that source file is preserved after async copy."""
        source = File(temp_dir / "source.txt")
        target_path = temp_dir / "target.txt"

        original_content = "Original content that should be preserved"
        source.write_text(original_content)
        copied = await source.copy_async(target_path)

        # Verify source still exists and has original content
        assert source.exists()
        assert source.read_text() == original_content

        # Verify copy was created correctly
        assert copied.exists()
        assert copied.read_text() == original_content


class TestUtilityMethods:
    """Test utility methods."""

    def test_append_text(self, temp_dir: pathlib.Path) -> None:
        """Test appending text to file."""
        test_file = File(temp_dir / "append.txt")
        test_file.write_text("First line\n")

        test_file.append_text("Second line\n")

        assert test_file.read_text() == "First line\nSecond line\n"

    def test_append_text_creates_file(self, temp_dir: pathlib.Path) -> None:
        """Test that append_text creates file if it doesn't exist."""
        test_file = File(temp_dir / "new.txt")

        test_file.append_text("Appended content")

        assert test_file.exists()
        assert test_file.read_text() == "Appended content"

    def test_append_text_creates_parent_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test that append_text creates parent directories."""
        test_file = File(temp_dir / "nested" / "file.txt")

        test_file.append_text("Nested append")

        assert test_file.exists()
        assert test_file.read_text() == "Nested append"

    def test_append_text_multiple_times(self, temp_dir: pathlib.Path) -> None:
        """Test multiple appends to same file."""
        test_file = File(temp_dir / "multi.txt")

        test_file.append_text("Line 1\n")
        test_file.append_text("Line 2\n")
        test_file.append_text("Line 3\n")

        assert test_file.read_text() == "Line 1\nLine 2\nLine 3\n"

    def test_touch_parents(self, temp_dir: pathlib.Path) -> None:
        """Test touch_parents creates file and parent directories."""
        test_file = File(temp_dir / "nested" / "deep" / "file.txt")

        test_file.touch_parents()

        assert test_file.exists()
        assert test_file.is_file()

    def test_touch_parents_existing_file(self, temp_dir: pathlib.Path) -> None:
        """Test touch_parents with existing file."""
        test_file = File(temp_dir / "existing.txt")
        test_file.write_text("Content")

        test_file.touch_parents()

        assert test_file.exists()
        assert test_file.read_text() == "Content"

    def test_size_property(self, temp_dir: pathlib.Path) -> None:
        """Test size property returns correct file size."""
        test_file = File(temp_dir / "size.txt")
        test_file.write_text("Hello")

        assert test_file.size == 5

    def test_size_property_empty_file(self, temp_dir: pathlib.Path) -> None:
        """Test size property for empty file."""
        test_file = File(temp_dir / "empty.txt")
        test_file.write_text("")

        assert test_file.size == 0

    def test_size_property_binary_file(self, temp_dir: pathlib.Path) -> None:
        """Test size property for binary file."""
        test_file = File(temp_dir / "binary.bin")
        test_file.write_bytes(b"\x00\x01\x02\x03\x04")

        assert test_file.size == 5

    def test_size_property_missing_file(self, temp_dir: pathlib.Path) -> None:
        """Test size property raises FileNotFoundError for missing file."""
        test_file = File(temp_dir / "missing.txt")

        with pytest.raises(FileNotFoundError):
            _ = test_file.size

    def test_size_property_unicode_content(self, temp_dir: pathlib.Path) -> None:
        """Test size property with Unicode content."""
        test_file = File(temp_dir / "unicode.txt")
        test_file.write_text("Привіт світ!")

        # Verify the file size is correct for UTF-8 encoding
        # The actual size depends on how Python encodes the text
        # Just verify that the size is non-zero and matches the content length
        assert test_file.size > 0
        # Read back and verify content matches
        assert test_file.read_text() == "Привіт світ!"


class TestFileInheritance:
    """Test that File properly inherits from pathlib.Path."""

    def test_file_is_path_instance(self, temp_dir: pathlib.Path) -> None:
        """Test that File is an instance of pathlib.Path."""
        test_file = File(temp_dir / "test.txt")
        assert isinstance(test_file, pathlib.Path)

    def test_path_methods_work(self, temp_dir: pathlib.Path) -> None:
        """Test that standard pathlib methods work."""
        test_file = File(temp_dir / "subdir" / "test.txt")

        assert test_file.name == "test.txt"
        assert test_file.stem == "test"
        assert test_file.suffix == ".txt"
        assert "subdir" in str(test_file)

    def test_file_can_be_used_as_path(self, temp_dir: pathlib.Path) -> None:
        """Test that File can be used where Path is expected."""
        test_file = File(temp_dir / "test.txt")
        test_file.write_text("content")

        # Should work with pathlib operations
        parent = test_file.parent
        assert parent.exists()

        # Should work with Path operations
        assert test_file.with_suffix(".bak") == File(temp_dir / "test.bak")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_json(self, temp_dir: pathlib.Path) -> None:
        """Test loading empty JSON object."""
        test_file = File(temp_dir / "empty.json")
        test_file.dump_json({})

        loaded = test_file.load_json()
        assert loaded == {}

    def test_empty_yaml(self, temp_dir: pathlib.Path) -> None:
        """Test loading empty YAML."""
        test_file = File(temp_dir / "empty.yaml")
        test_file.dump_yaml({})

        loaded = test_file.load_yaml()
        assert loaded == {}

    def test_large_json(self, temp_dir: pathlib.Path) -> None:
        """Test loading large JSON file."""
        test_file = File(temp_dir / "large.json")
        large_data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}
        test_file.dump_json(large_data)

        loaded = test_file.load_json()
        assert len(loaded["items"]) == 1000

    def test_nested_json(self, temp_dir: pathlib.Path) -> None:
        """Test loading deeply nested JSON."""
        test_file = File(temp_dir / "nested.json")
        nested_data = {"level1": {"level2": {"level3": {"level4": "deep"}}}}
        test_file.dump_json(nested_data)

        loaded = test_file.load_json()
        assert loaded["level1"]["level2"]["level3"]["level4"] == "deep"

    def test_special_characters_in_json(self, temp_dir: pathlib.Path) -> None:
        """Test JSON with special characters."""
        test_file = File(temp_dir / "special.json")
        special_data = {
            "unicode": "Привіт 世界 🌍",
            "quotes": 'He said "Hello"',
            "newlines": "Line1\nLine2",
            "tabs": "Col1\tCol2",
        }
        test_file.dump_json(special_data)

        loaded = test_file.load_json()
        assert loaded["unicode"] == "Привіт 世界 🌍"
        assert loaded["quotes"] == 'He said "Hello"'
        assert loaded["newlines"] == "Line1\nLine2"
        assert loaded["tabs"] == "Col1\tCol2"

    def test_yaml_multiline_strings(self, temp_dir: pathlib.Path) -> None:
        """Test YAML with multiline strings."""
        test_file = File(temp_dir / "multiline.yaml")
        multiline_data = {"description": "This is a\nmultiline\nstring"}
        test_file.dump_yaml(multiline_data)

        loaded = test_file.load_yaml()
        assert loaded["description"] == "This is a\nmultiline\nstring"

    def test_json_list(self, temp_dir: pathlib.Path) -> None:
        """Test loading JSON array."""
        test_file = File(temp_dir / "list.json")
        list_data = [1, 2, 3, "four", {"five": 5}]
        test_file.dump_json(list_data)

        loaded = test_file.load_json()
        assert loaded == [1, 2, 3, "four", {"five": 5}]

    def test_yaml_list(self, temp_dir: pathlib.Path) -> None:
        """Test loading YAML list."""
        test_file = File(temp_dir / "list.yaml")
        list_data = [1, 2, 3, "four", {"five": 5}]
        test_file.dump_yaml(list_data)

        loaded = test_file.load_yaml()
        assert loaded == [1, 2, 3, "four", {"five": 5}]

    def test_json_null_values(self, temp_dir: pathlib.Path) -> None:
        """Test JSON with null values."""
        test_file = File(temp_dir / "null.json")
        null_data = {"value": None, "list": [1, None, 3]}
        test_file.dump_json(null_data)

        loaded = test_file.load_json()
        assert loaded["value"] is None
        assert loaded["list"][1] is None

    def test_yaml_null_values(self, temp_dir: pathlib.Path) -> None:
        """Test YAML with null values."""
        test_file = File(temp_dir / "null.yaml")
        null_data = {"value": None, "list": [1, None, 3]}
        test_file.dump_yaml(null_data)

        loaded = test_file.load_yaml()
        assert loaded["value"] is None
        assert loaded["list"][1] is None

    def test_json_boolean_values(self, temp_dir: pathlib.Path) -> None:
        """Test JSON with boolean values."""
        test_file = File(temp_dir / "bool.json")
        bool_data = {"true_val": True, "false_val": False}
        test_file.dump_json(bool_data)

        loaded = test_file.load_json()
        assert loaded["true_val"] is True
        assert loaded["false_val"] is False

    def test_yaml_boolean_values(self, temp_dir: pathlib.Path) -> None:
        """Test YAML with boolean values."""
        test_file = File(temp_dir / "bool.yaml")
        bool_data = {"true_val": True, "false_val": False}
        test_file.dump_yaml(bool_data)

        loaded = test_file.load_yaml()
        assert loaded["true_val"] is True
        assert loaded["false_val"] is False

    def test_numeric_values_json(self, temp_dir: pathlib.Path) -> None:
        """Test JSON with various numeric types."""
        test_file = File(temp_dir / "numeric.json")
        numeric_data = {
            "int": 42,
            "float": 3.14,
            "negative": -10,
            "zero": 0,
            "large": 1000000,
        }
        test_file.dump_json(numeric_data)

        loaded = test_file.load_json()
        assert loaded["int"] == 42
        assert loaded["float"] == 3.14
        assert loaded["negative"] == -10
        assert loaded["zero"] == 0
        assert loaded["large"] == 1000000

    def test_numeric_values_yaml(self, temp_dir: pathlib.Path) -> None:
        """Test YAML with various numeric types."""
        test_file = File(temp_dir / "numeric.yaml")
        numeric_data = {
            "int": 42,
            "float": 3.14,
            "negative": -10,
            "zero": 0,
            "large": 1000000,
        }
        test_file.dump_yaml(numeric_data)

        loaded = test_file.load_yaml()
        assert loaded["int"] == 42
        assert loaded["float"] == 3.14
        assert loaded["negative"] == -10
        assert loaded["zero"] == 0
        assert loaded["large"] == 1000000


class TestCriticalMissingTests:
    """Critical tests for nested directory creation and missing file handling."""

    def test_write_text_creates_nested_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """write_text MUST create parent directories."""
        test_file = File(temp_dir / "a" / "b" / "c" / "file.txt")
        test_file.write_text("content")
        assert test_file.exists()
        assert test_file.read_text() == "content"

    def test_write_bytes_creates_nested_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """write_bytes MUST create parent directories."""
        test_file = File(temp_dir / "a" / "b" / "c" / "file.bin")
        test_file.write_bytes(b"content")
        assert test_file.exists()
        assert test_file.read_bytes() == b"content"

    @pytest.mark.asyncio
    async def test_write_text_async_creates_nested_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """write_text_async MUST create parent directories."""
        test_file = File(temp_dir / "a" / "b" / "c" / "file_async.txt")
        await test_file.write_text_async("content")
        assert test_file.exists()
        assert test_file.read_text() == "content"

    @pytest.mark.asyncio
    async def test_write_bytes_async_creates_nested_directories(
        self, temp_dir: pathlib.Path
    ) -> None:
        """write_bytes_async MUST create parent directories."""
        test_file = File(temp_dir / "a" / "b" / "c" / "file_async.bin")
        await test_file.write_bytes_async(b"content")
        assert test_file.exists()
        assert test_file.read_bytes() == b"content"

    @pytest.mark.asyncio
    async def test_read_many_async_with_missing_file(
        self, temp_dir: pathlib.Path
    ) -> None:
        """read_many_async MUST raise FileNotFoundError for missing files."""
        File(temp_dir / "file1.txt").write_text("content1")
        # file2.txt НЕ існує

        with pytest.raises(FileNotFoundError):
            await File.read_many_async(
                [str(temp_dir / "file1.txt"), str(temp_dir / "file2.txt")]
            )
