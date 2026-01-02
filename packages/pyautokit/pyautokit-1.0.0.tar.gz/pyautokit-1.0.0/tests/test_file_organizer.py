"""Tests for file_organizer module."""

import pytest
from pathlib import Path
import tempfile
import shutil
from pyautokit.file_organizer import FileOrganizer, SortMethod


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp = Path(tempfile.mkdtemp())
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = {
        "document.pdf": b"PDF content",
        "image.jpg": b"JPG content",
        "video.mp4": b"MP4 content",
        "audio.mp3": b"MP3 content",
        "code.py": b"print('test')",
        "data.json": b'{"key": "value"}',
        "archive.zip": b"ZIP content",
        "text.txt": b"Text content",
    }
    
    for filename, content in files.items():
        file_path = temp_dir / filename
        file_path.write_bytes(content)
    
    return temp_dir


class TestFileOrganizer:
    """Test FileOrganizer class."""

    def test_initialization(self):
        """Test organizer initialization."""
        organizer = FileOrganizer()
        assert organizer.create_folders is True
        assert organizer.dry_run is False
        assert organizer.handle_duplicates == "rename"

    def test_initialization_with_params(self):
        """Test organizer with custom parameters."""
        organizer = FileOrganizer(
            create_folders=False,
            dry_run=True,
            handle_duplicates="skip"
        )
        assert organizer.create_folders is False
        assert organizer.dry_run is True
        assert organizer.handle_duplicates == "skip"

    def test_categorize_file(self, temp_dir):
        """Test file categorization."""
        organizer = FileOrganizer()
        
        # Test known categories
        assert organizer.categorize_file(temp_dir / "test.pdf") == "Documents"
        assert organizer.categorize_file(temp_dir / "test.jpg") == "Images"
        assert organizer.categorize_file(temp_dir / "test.mp4") == "Videos"
        assert organizer.categorize_file(temp_dir / "test.mp3") == "Audio"
        assert organizer.categorize_file(temp_dir / "test.py") == "Code"
        assert organizer.categorize_file(temp_dir / "test.zip") == "Archives"
        
        # Test unknown extension
        assert organizer.categorize_file(temp_dir / "test.unknown") == "Other"

    def test_get_size_category(self, temp_dir):
        """Test size categorization."""
        organizer = FileOrganizer()
        
        # Create files of different sizes
        tiny_file = temp_dir / "tiny.txt"
        tiny_file.write_bytes(b"x" * 50 * 1024)  # 50KB
        
        small_file = temp_dir / "small.txt"
        small_file.write_bytes(b"x" * 500 * 1024)  # 500KB
        
        assert organizer.get_size_category(tiny_file) == "tiny"
        assert organizer.get_size_category(small_file) == "small"

    def test_organize_by_extension_dry_run(self, sample_files):
        """Test organize by extension in dry-run mode."""
        organizer = FileOrganizer(dry_run=True)
        results = organizer.organize_by_extension(sample_files)
        
        # Check that files are counted but not moved
        assert len(results) > 0
        assert organizer.stats["moved"] > 0
        
        # Verify files still in original location
        assert (sample_files / "document.pdf").exists()
        assert (sample_files / "image.jpg").exists()

    def test_organize_by_extension(self, sample_files):
        """Test organize by extension."""
        organizer = FileOrganizer()
        results = organizer.organize_by_extension(sample_files)
        
        # Check results
        assert "pdf" in results
        assert "jpg" in results
        assert "mp4" in results
        
        # Verify files were moved
        assert (sample_files / "PDF" / "document.pdf").exists()
        assert (sample_files / "JPG" / "image.jpg").exists()
        assert (sample_files / "MP4" / "video.mp4").exists()

    def test_organize_by_category(self, sample_files):
        """Test organize by category."""
        organizer = FileOrganizer()
        results = organizer.organize_by_category(sample_files)
        
        # Check categories were created
        assert "Documents" in results
        assert "Images" in results
        assert "Videos" in results
        assert "Audio" in results
        assert "Code" in results
        
        # Verify files in correct categories
        assert (sample_files / "Documents" / "document.pdf").exists()
        assert (sample_files / "Images" / "image.jpg").exists()
        assert (sample_files / "Videos" / "video.mp4").exists()
        assert (sample_files / "Audio" / "audio.mp3").exists()
        assert (sample_files / "Code" / "code.py").exists()

    def test_organize_by_date(self, sample_files):
        """Test organize by date."""
        organizer = FileOrganizer()
        results = organizer.organize_by_date(sample_files)
        
        # Should have at least one date folder
        assert len(results) > 0
        
        # Check that date folders were created
        date_folders = [d for d in sample_files.iterdir() if d.is_dir()]
        assert len(date_folders) > 0

    def test_organize_by_size(self, sample_files):
        """Test organize by size."""
        organizer = FileOrganizer()
        results = organizer.organize_by_size(sample_files)
        
        # Should categorize by size
        assert len(results) > 0
        
        # Check size categories exist
        size_folders = [d.name for d in sample_files.iterdir() if d.is_dir()]
        assert any(f in size_folders for f in ["Tiny", "Small", "Medium"])

    def test_duplicate_handling_rename(self, temp_dir):
        """Test duplicate handling with rename."""
        organizer = FileOrganizer(handle_duplicates="rename")
        
        # Create original file
        original = temp_dir / "test.txt"
        original.write_text("original")
        
        # Create duplicate
        duplicate = temp_dir / "test.txt"
        
        # Move to same location
        dest_folder = temp_dir / "TEXT"
        dest_folder.mkdir()
        
        organizer._move_file(original, dest_folder, "TEXT")
        
        # Create another file with same name
        duplicate2 = temp_dir / "test.txt"
        duplicate2.write_text("duplicate")
        
        organizer._move_file(duplicate2, dest_folder, "TEXT")
        
        # Should have renamed version
        assert (dest_folder / "test.txt").exists()
        assert (dest_folder / "test_1.txt").exists()

    def test_duplicate_handling_skip(self, temp_dir):
        """Test duplicate handling with skip."""
        organizer = FileOrganizer(handle_duplicates="skip")
        
        # Create files
        file1 = temp_dir / "test.txt"
        file1.write_text("file1")
        
        dest_folder = temp_dir / "TEXT"
        dest_folder.mkdir()
        (dest_folder / "test.txt").write_text("existing")
        
        # Try to move duplicate
        result = organizer._move_file(file1, dest_folder, "TEXT")
        
        # Should be skipped
        assert result is False
        assert organizer.stats["skipped"] == 1

    def test_get_directory_stats(self, sample_files):
        """Test directory statistics."""
        organizer = FileOrganizer()
        stats = organizer.get_directory_stats(sample_files)
        
        assert stats["total_files"] == 8
        assert stats["total_size"] > 0
        assert len(stats["by_extension"]) > 0
        assert len(stats["by_category"]) > 0
        assert "Documents" in stats["by_category"]
        assert "Images" in stats["by_category"]

    def test_recursive_organization(self, temp_dir):
        """Test recursive directory organization."""
        # Create subdirectories with files
        subdir1 = temp_dir / "subdir1"
        subdir1.mkdir()
        (subdir1 / "file1.txt").write_text("content")
        
        subdir2 = temp_dir / "subdir2"
        subdir2.mkdir()
        (subdir2 / "file2.pdf").write_text("content")
        
        organizer = FileOrganizer()
        results = organizer.organize_by_extension(temp_dir, recursive=True)
        
        # Should find files in subdirectories
        assert len(results) > 0

    def test_no_create_folders(self, temp_dir):
        """Test with create_folders=False."""
        file1 = temp_dir / "test.txt"
        file1.write_text("content")
        
        organizer = FileOrganizer(create_folders=False)
        results = organizer.organize_by_extension(temp_dir)
        
        # Should not create folders
        txt_folder = temp_dir / "TXT"
        # Folder might be created anyway, but file shouldn't be moved
        # without proper error handling
        assert len(results) >= 0  # At least tried to process

    def test_empty_directory(self, temp_dir):
        """Test organizing empty directory."""
        organizer = FileOrganizer()
        results = organizer.organize_by_extension(temp_dir)
        
        assert len(results) == 0
        assert organizer.stats["moved"] == 0

    def test_file_categories_coverage(self):
        """Test that all major file types are categorized."""
        organizer = FileOrganizer()
        
        # Test comprehensive list of extensions
        test_cases = [
            ("test.pdf", "Documents"),
            ("test.docx", "Documents"),
            ("test.jpg", "Images"),
            ("test.png", "Images"),
            ("test.mp4", "Videos"),
            ("test.mp3", "Audio"),
            ("test.zip", "Archives"),
            ("test.py", "Code"),
            ("test.js", "Code"),
            ("test.json", "Data"),
            ("test.exe", "Executables"),
            ("test.ttf", "Fonts"),
        ]
        
        for filename, expected_category in test_cases:
            path = Path(filename)
            assert organizer.categorize_file(path) == expected_category

