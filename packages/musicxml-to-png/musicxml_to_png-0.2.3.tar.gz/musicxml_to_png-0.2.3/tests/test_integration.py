"""Integration tests for end-to-end MusicXML to PNG conversion."""

from pathlib import Path

import pytest

from musicxml_to_png import convert_musicxml_to_png
from musicxml_to_png.instruments import ENSEMBLE_ORCHESTRA, ENSEMBLE_BIGBAND


@pytest.fixture
def fixtures_dir():
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def bigband_file(fixtures_dir):
    """Return path to bigband test file."""
    file_path = fixtures_dir / "test-bigband-1.mxl"
    if not file_path.exists():
        pytest.skip(f"Test fixture not found: {file_path}")
    return file_path


@pytest.fixture
def orchestra_file(fixtures_dir):
    """Return path to orchestra test file."""
    file_path = fixtures_dir / "test-orchestra-1.mxl"
    if not file_path.exists():
        pytest.skip(f"Test fixture not found: {file_path}")
    return file_path


class TestIntegration:
    """End-to-end integration tests using real MusicXML files."""

    def test_bigband_conversion(self, bigband_file, tmp_path):
        """Test conversion of bigband MusicXML file."""
        output_path = tmp_path / "bigband_output.png"
        
        result_path = convert_musicxml_to_png(
            input_path=bigband_file,
            output_path=output_path,
            ensemble=ENSEMBLE_BIGBAND,
        )
        
        assert result_path == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0  # File should not be empty

    def test_orchestra_conversion(self, orchestra_file, tmp_path):
        """Test conversion of orchestra MusicXML file."""
        output_path = tmp_path / "orchestra_output.png"
        
        result_path = convert_musicxml_to_png(
            input_path=orchestra_file,
            output_path=output_path,
            ensemble=ENSEMBLE_ORCHESTRA,
        )
        
        assert result_path == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_bigband_with_minimal_mode(self, bigband_file, tmp_path):
        """Test bigband conversion with minimal mode."""
        output_path = tmp_path / "bigband_minimal.png"
        
        result_path = convert_musicxml_to_png(
            input_path=bigband_file,
            output_path=output_path,
            ensemble=ENSEMBLE_BIGBAND,
            minimal=True,
        )
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_orchestra_with_no_grid(self, orchestra_file, tmp_path):
        """Test orchestra conversion with grid disabled."""
        output_path = tmp_path / "orchestra_no_grid.png"
        
        result_path = convert_musicxml_to_png(
            input_path=orchestra_file,
            output_path=output_path,
            ensemble=ENSEMBLE_ORCHESTRA,
            show_grid=False,
        )
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_bigband_with_custom_title(self, bigband_file, tmp_path):
        """Test bigband conversion with custom title."""
        output_path = tmp_path / "bigband_titled.png"
        
        result_path = convert_musicxml_to_png(
            input_path=bigband_file,
            output_path=output_path,
            ensemble=ENSEMBLE_BIGBAND,
            title="My Bigband Arrangement",
        )
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_orchestra_all_options(self, orchestra_file, tmp_path):
        """Test orchestra conversion with all options combined."""
        output_path = tmp_path / "orchestra_full.png"
        
        result_path = convert_musicxml_to_png(
            input_path=orchestra_file,
            output_path=output_path,
            ensemble=ENSEMBLE_ORCHESTRA,
            title="Full Options Test",
            show_grid=True,
            minimal=False,
        )
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_bigband_all_options(self, bigband_file, tmp_path):
        """Test bigband conversion with all options combined."""
        output_path = tmp_path / "bigband_full.png"
        
        result_path = convert_musicxml_to_png(
            input_path=bigband_file,
            output_path=output_path,
            ensemble=ENSEMBLE_BIGBAND,
            title="Bigband Full Options",
            show_grid=False,
            minimal=True,
        )
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_default_output_naming(self, bigband_file, tmp_path):
        """Test that default output uses input filename."""
        # Copy file to tmp_path to test default naming
        import shutil
        test_file = tmp_path / "test-bigband.mxl"
        shutil.copy(bigband_file, test_file)
        
        result_path = convert_musicxml_to_png(
            input_path=test_file,
            ensemble=ENSEMBLE_BIGBAND,
        )
        
        # Should create test-bigband.png
        expected_output = test_file.with_suffix(".png")
        assert result_path == expected_output
        assert expected_output.exists()

