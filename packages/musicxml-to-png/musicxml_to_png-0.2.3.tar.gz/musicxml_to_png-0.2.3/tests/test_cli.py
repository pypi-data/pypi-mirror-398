"""Unit tests for CLI interface."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from music21 import stream, note, instrument

from musicxml_to_png.cli import main


@pytest.fixture
def sample_musicxml_file(tmp_path):
    """Create a sample MusicXML file for testing."""
    score = stream.Score()
    part = stream.Part()
    part.append(instrument.Violin())
    n = note.Note("C4")
    n.quarterLength = 1.0
    part.append(n)
    score.append(part)
    
    input_path = tmp_path / "test.mxl"
    score.write("musicxml", input_path)
    return input_path


class TestCLIArguments:
    """Test CLI argument parsing and handling."""

    def test_basic_conversion(self, sample_musicxml_file, tmp_path, capsys):
        """Test basic conversion with required arguments."""
        with patch("sys.argv", ["musicxml-to-png", str(sample_musicxml_file)]):
            main()
        
        # Check that output file was created
        output_file = sample_musicxml_file.with_suffix(".png")
        assert output_file.exists()
        
        # Check success message
        captured = capsys.readouterr()
        assert "Successfully created visualization" in captured.out

    def test_custom_output_path(self, sample_musicxml_file, tmp_path, capsys):
        """Test conversion with custom output path."""
        output_path = tmp_path / "custom.png"
        
        with patch("sys.argv", [
            "musicxml-to-png",
            str(sample_musicxml_file),
            "-o", str(output_path),
        ]):
            main()
        
        assert output_path.exists()

    def test_custom_title(self, sample_musicxml_file, tmp_path, capsys):
        """Test conversion with custom title."""
        with patch("sys.argv", [
            "musicxml-to-png",
            str(sample_musicxml_file),
            "--title", "My Test Composition",
        ]):
            main()
        
        output_file = sample_musicxml_file.with_suffix(".png")
        assert output_file.exists()

    def test_no_grid_option(self, sample_musicxml_file, tmp_path, capsys):
        """Test --no-grid option."""
        with patch("sys.argv", [
            "musicxml-to-png",
            str(sample_musicxml_file),
            "--no-grid",
        ]):
            main()
        
        output_file = sample_musicxml_file.with_suffix(".png")
        assert output_file.exists()

    def test_minimal_mode(self, sample_musicxml_file, tmp_path, capsys):
        """Test --minimal option."""
        with patch("sys.argv", [
            "musicxml-to-png",
            str(sample_musicxml_file),
            "--minimal",
        ]):
            main()
        
        output_file = sample_musicxml_file.with_suffix(".png")
        assert output_file.exists()

    def test_ensemble_option(self, sample_musicxml_file, tmp_path, capsys):
        """Test --ensemble option."""
        with patch("sys.argv", [
            "musicxml-to-png",
            str(sample_musicxml_file),
            "--ensemble", "bigband",
        ]):
            main()
        
        output_file = sample_musicxml_file.with_suffix(".png")
        assert output_file.exists()

    def test_verbose_mode(self, sample_musicxml_file, tmp_path, capsys):
        """Test --verbose option."""
        with patch("sys.argv", [
            "musicxml-to-png",
            str(sample_musicxml_file),
            "--verbose",
        ]):
            main()
        
        output_file = sample_musicxml_file.with_suffix(".png")
        assert output_file.exists()

    def test_short_verbose_flag(self, sample_musicxml_file, tmp_path, capsys):
        """Test -v short flag for verbose."""
        with patch("sys.argv", [
            "musicxml-to-png",
            str(sample_musicxml_file),
            "-v",
        ]):
            main()
        
        output_file = sample_musicxml_file.with_suffix(".png")
        assert output_file.exists()


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_file_not_found_error(self, tmp_path, capsys):
        """Test error handling for missing file."""
        non_existent = tmp_path / "nonexistent.mxl"
        
        with patch("sys.argv", ["musicxml-to-png", str(non_existent)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_invalid_file_extension_warning(self, tmp_path, capsys):
        """Test warning for non-standard file extension."""
        # Create a file with non-standard extension
        test_file = tmp_path / "test.txt"
        test_file.write_text("not musicxml")
        
        # Create a valid MusicXML file with .xml extension for comparison
        score = stream.Score()
        part = stream.Part()
        part.append(instrument.Violin())
        n = note.Note("C4")
        n.quarterLength = 1.0
        part.append(n)
        score.append(part)
        
        xml_file = tmp_path / "test.xml"
        score.write("musicxml", xml_file)
        
        with patch("sys.argv", ["musicxml-to-png", str(xml_file)]):
            main()
        
        # Should still work, but might show warning
        output_file = xml_file.with_suffix(".png")
        assert output_file.exists()

    def test_invalid_musicxml_error(self, tmp_path, capsys):
        """Test error handling for invalid MusicXML."""
        invalid_file = tmp_path / "invalid.mxl"
        invalid_file.write_text("This is not valid MusicXML")
        
        with patch("sys.argv", ["musicxml-to-png", str(invalid_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "error" in captured.err.lower() or "failed" in captured.err.lower()

    def test_empty_musicxml_error(self, tmp_path, capsys):
        """Test error handling for empty MusicXML (no notes)."""
        score = stream.Score()
        part = stream.Part()
        part.append(instrument.Violin())
        # No notes
        score.append(part)
        
        empty_file = tmp_path / "empty.mxl"
        score.write("musicxml", empty_file)
        
        with patch("sys.argv", ["musicxml-to-png", str(empty_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "error" in captured.err.lower() or "no notes" in captured.err.lower()

    def test_minimal_mode_overrides_title(self, sample_musicxml_file, tmp_path, capsys):
        """Test that --minimal mode ignores title."""
        with patch("sys.argv", [
            "musicxml-to-png",
            str(sample_musicxml_file),
            "--minimal",
            "--title", "This should be ignored",
        ]):
            main()
        
        output_file = sample_musicxml_file.with_suffix(".png")
        assert output_file.exists()

