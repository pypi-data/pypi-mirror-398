"""Tests for edge cases and error handling."""

import pathlib
import sys

import pytest

from easy_file import File


class TestEdgeCasesWriteMethods:
    """Test edge cases for write methods."""

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="chmod on directories doesn't prevent file creation on Windows",
    )
    def test_write_text_to_readonly_directory(self, temp_dir: pathlib.Path) -> None:
        """Test write_text fails on read-only directory."""
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()
        try:
            readonly_dir.chmod(0o555)  # Read-only
            test_file = File(readonly_dir / "file.txt")
            with pytest.raises(PermissionError):
                test_file.write_text("content")
        finally:
            # Cleanup
            readonly_dir.chmod(0o755)

    def test_write_text_empty_string(self, temp_dir: pathlib.Path) -> None:
        """Test write_text with empty string."""
        test_file = File(temp_dir / "empty.txt")
        test_file.write_text("")

        assert test_file.exists()
        assert test_file.read_text() == ""
        assert test_file.size == 0

    def test_write_bytes_empty_bytes(self, temp_dir: pathlib.Path) -> None:
        """Test write_bytes with empty bytes."""
        test_file = File(temp_dir / "empty.bin")
        test_file.write_bytes(b"")

        assert test_file.exists()
        assert test_file.read_bytes() == b""
        assert test_file.size == 0

    def test_write_text_overwrites_existing(self, temp_dir: pathlib.Path) -> None:
        """Test write_text overwrites existing file."""
        test_file = File(temp_dir / "overwrite.txt")
        test_file.write_text("old content")
        test_file.write_text("new content")

        assert test_file.read_text() == "new content"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="chmod on directories doesn't prevent file creation on Windows",
    )
    async def test_write_text_async_to_readonly_directory(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test write_text_async fails on read-only directory."""
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()
        try:
            readonly_dir.chmod(0o555)
            test_file = File(readonly_dir / "file.txt")
            with pytest.raises(PermissionError):
                await test_file.write_text_async("content")
        finally:
            readonly_dir.chmod(0o755)


class TestEdgeCasesReadManyAsync:
    """Test edge cases for read_many_async."""

    @pytest.mark.asyncio
    async def test_read_many_async_empty_list(self) -> None:
        """Test read_many_async with empty list."""
        result = await File.read_many_async([])
        assert result == []

    @pytest.mark.asyncio
    async def test_read_many_async_preserves_order(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test read_many_async preserves file order."""
        files = []
        for i in range(10):
            f = File(temp_dir / f"file{i}.txt")
            f.write_text(f"content {i}")
            files.append(str(f))

        contents = await File.read_many_async(files)

        for i, content in enumerate(contents):
            assert content == f"content {i}"

    @pytest.mark.asyncio
    async def test_read_many_async_with_duplicates(
        self, temp_dir: pathlib.Path
    ) -> None:
        """Test read_many_async with duplicate paths."""
        test_file = File(temp_dir / "file.txt")
        test_file.write_text("content")

        contents = await File.read_many_async(
            [str(test_file), str(test_file), str(test_file)]
        )

        assert contents == ["content", "content", "content"]


class TestEdgeCasesJson:
    """Test edge cases for JSON operations."""

    def test_dump_json_with_indent_zero(self, temp_dir: pathlib.Path) -> None:
        """Test dump_json with indent=0 creates compact JSON."""
        test_file = File(temp_dir / "compact.json")
        test_file.dump_json({"a": 1, "b": 2, "c": 3}, indent=0)

        content = test_file.read_text()
        # Compact JSON shouldn't have extra whitespace
        assert content == '{"a":1,"b":2,"c":3}'

    def test_load_json_with_bom(self, temp_dir: pathlib.Path) -> None:
        """Test load_json handles UTF-8 BOM."""
        test_file = File(temp_dir / "bom.json")
        # UTF-8 BOM + JSON
        test_file.write_bytes(b'\xef\xbb\xbf{"test": "data"}')

        # Should handle BOM gracefully or raise clear error
        try:
            data = test_file.load_json()
            assert data == {"test": "data"}
        except Exception as e:
            # If it fails, should be JSONDecodeError with clear message
            assert "BOM" in str(e) or "decode" in str(e).lower()
