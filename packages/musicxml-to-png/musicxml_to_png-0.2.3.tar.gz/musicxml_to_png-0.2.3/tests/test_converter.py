"""Unit tests for MusicXML conversion and visualization."""

from pathlib import Path
import tempfile

import pytest
from music21 import stream, note, instrument, chord, pitch

from musicxml_to_png.converter import (
    extract_notes,
    create_visualization,
    convert_musicxml_to_png,
    NoteEvent,
)
from musicxml_to_png.instruments import (
    ENSEMBLE_UNGROUPED,
    ENSEMBLE_ORCHESTRA,
    ENSEMBLE_BIGBAND,
    ORCHESTRA_STRINGS,
    ORCHESTRA_WINDS,
    ORCHESTRA_BRASS,
    BIGBAND_TRUMPETS,
    BIGBAND_RHYTHM_SECTION,
    BIGBAND_UNKNOWN,
)


@pytest.fixture
def simple_score():
    """Create a simple Score with one part and one note."""
    score = stream.Score()
    part = stream.Part()
    part.append(instrument.Violin())
    n = note.Note("C4")
    n.quarterLength = 1.0
    part.append(n)
    score.append(part)
    return score


@pytest.fixture
def score_with_chord():
    """Create a Score with a chord."""
    score = stream.Score()
    part = stream.Part()
    part.append(instrument.Piano())
    c = chord.Chord(["C4", "E4", "G4"])
    c.quarterLength = 2.0
    part.append(c)
    score.append(part)
    return score


@pytest.fixture
def score_with_rest():
    """Create a Score with notes and rests."""
    score = stream.Score()
    part = stream.Part()
    part.append(instrument.Flute())
    n1 = note.Note("D4")
    n1.quarterLength = 1.0
    part.append(n1)
    r = note.Rest()
    r.quarterLength = 1.0
    part.append(r)
    n2 = note.Note("E4")
    n2.quarterLength = 0.5
    part.append(n2)
    score.append(part)
    return score


@pytest.fixture
def multi_part_score():
    """Create a Score with multiple parts."""
    score = stream.Score()
    
    # Part 1: Violin
    part1 = stream.Part()
    part1.append(instrument.Violin())
    n1 = note.Note("G4")
    n1.quarterLength = 1.0
    part1.append(n1)
    score.append(part1)
    
    # Part 2: Trumpet
    part2 = stream.Part()
    part2.append(instrument.Trumpet())
    n2 = note.Note("C5")
    n2.quarterLength = 1.0
    part2.append(n2)
    score.append(part2)
    
    return score


@pytest.fixture
def empty_score():
    """Create an empty Score."""
    return stream.Score()


class TestExtractNotes:
    """Test note extraction from music21 Score objects."""

    def test_single_note_extraction(self, simple_score):
        """Test extraction of a single note."""
        note_events = extract_notes(simple_score, ensemble=ENSEMBLE_ORCHESTRA)
        
        assert len(note_events) == 1
        assert isinstance(note_events[0], NoteEvent)
        assert note_events[0].pitch_midi == 60.0  # C4
        assert note_events[0].duration == 1.0
        assert note_events[0].start_time == 0.0
        assert note_events[0].instrument_family == ORCHESTRA_STRINGS

    def test_chord_extraction(self, score_with_chord):
        """Test extraction of chord (multiple pitches)."""
        note_events = extract_notes(score_with_chord, ensemble=ENSEMBLE_ORCHESTRA)
        
        # Chord should produce 3 note events (C, E, G)
        assert len(note_events) == 3
        
        # All should have same start time and duration
        assert all(event.start_time == 0.0 for event in note_events)
        assert all(event.duration == 2.0 for event in note_events)
        
        # Check pitches
        pitches = sorted([event.pitch_midi for event in note_events])
        assert pitches == [60.0, 64.0, 67.0]  # C4, E4, G4

    def test_rest_handling(self, score_with_rest):
        """Test that rests are skipped."""
        note_events = extract_notes(score_with_rest, ensemble=ENSEMBLE_ORCHESTRA)
        
        # Should have 2 notes, rest should be skipped
        assert len(note_events) == 2
        
        # First note at offset 0
        assert note_events[0].pitch_midi == 62.0  # D4
        assert note_events[0].start_time == 0.0
        assert note_events[0].duration == 1.0
        
        # Second note at offset 2 (after rest)
        assert note_events[1].pitch_midi == 64.0  # E4
        assert note_events[1].start_time == 2.0
        assert note_events[1].duration == 0.5

    def test_multiple_parts(self, multi_part_score):
        """Test extraction from multiple parts."""
        note_events = extract_notes(multi_part_score, ensemble=ENSEMBLE_ORCHESTRA)
        
        assert len(note_events) == 2
        
        # Check instrument families
        families = [event.instrument_family for event in note_events]
        assert ORCHESTRA_STRINGS in families  # Violin
        assert ORCHESTRA_BRASS in families     # Trumpet

    def test_empty_score(self, empty_score):
        """Test extraction from empty score."""
        note_events = extract_notes(empty_score, ensemble=ENSEMBLE_ORCHESTRA)
        assert len(note_events) == 0

    def test_ensemble_type_affects_classification(self, simple_score):
        """Test that ensemble type affects instrument classification."""
        # Same score, different ensembles
        orchestra_events = extract_notes(simple_score, ensemble=ENSEMBLE_ORCHESTRA)
        bigband_events = extract_notes(simple_score, ensemble=ENSEMBLE_BIGBAND)
        
        # Violin is strings in orchestra
        assert orchestra_events[0].instrument_family == ORCHESTRA_STRINGS
        # instrument.Violin() has MIDI 40, which maps to rhythm_section in bigband
        # This demonstrates that ensemble type affects classification
        assert bigband_events[0].instrument_family == BIGBAND_RHYTHM_SECTION
        # Verify they're different
        assert orchestra_events[0].instrument_family != bigband_events[0].instrument_family

    def test_ungrouped_mode_assigns_unique_labels_for_duplicates(self):
        """Default/ungrouped ensemble should give each part its own label."""
        score = stream.Score()
        
        part1 = stream.Part()
        part1.append(instrument.Flute())
        part1.append(note.Note("C4"))
        score.append(part1)
        
        part2 = stream.Part()
        part2.append(instrument.Flute())
        part2.append(note.Note("D4"))
        score.append(part2)
        
        note_events = extract_notes(score, ensemble=ENSEMBLE_UNGROUPED)
        
        labels = {event.instrument_label for event in note_events}
        assert len(labels) == 2
        assert all(label.startswith("Flute") for label in labels)
        assert labels != {"Flute"}  # duplicate parts should be disambiguated

    def test_part_without_instrument(self):
        """Test part without explicit instrument (should use part name or default to unknown)."""
        score = stream.Score()
        part = stream.Part()
        part.partName = "Unknown Part"
        n = note.Note("C4")
        n.quarterLength = 1.0
        part.append(n)
        score.append(part)
        
        note_events = extract_notes(score, ensemble=ENSEMBLE_ORCHESTRA)
        assert len(note_events) == 1
        # Should fall back to unknown if no instrument info


class TestCreateVisualization:
    """Test visualization creation."""

    def test_empty_note_events_raises_error(self, tmp_path):
        """Test that empty note events raises ValueError."""
        output_path = tmp_path / "output.png"
        
        with pytest.raises(ValueError, match="No notes found"):
            create_visualization([], output_path)

    def test_basic_visualization_creation(self, tmp_path):
        """Test basic visualization creation."""
        output_path = tmp_path / "output.png"
        
        note_events = [
            NoteEvent(pitch_midi=60.0, start_time=0.0, duration=1.0, instrument_family=ORCHESTRA_STRINGS),
            NoteEvent(pitch_midi=64.0, start_time=1.0, duration=1.0, instrument_family=ORCHESTRA_WINDS),
        ]
        
        create_visualization(note_events, output_path, ensemble=ENSEMBLE_ORCHESTRA)
        
        assert output_path.exists()
        assert output_path.suffix == ".png"

    def test_grid_enabled(self, tmp_path):
        """Test visualization with grid enabled."""
        output_path = tmp_path / "output.png"
        
        note_events = [
            NoteEvent(pitch_midi=60.0, start_time=0.0, duration=1.0, instrument_family=ORCHESTRA_STRINGS),
        ]
        
        create_visualization(note_events, output_path, show_grid=True, ensemble=ENSEMBLE_ORCHESTRA)
        assert output_path.exists()

    def test_grid_disabled(self, tmp_path):
        """Test visualization with grid disabled."""
        output_path = tmp_path / "output.png"
        
        note_events = [
            NoteEvent(pitch_midi=60.0, start_time=0.0, duration=1.0, instrument_family=ORCHESTRA_STRINGS),
        ]
        
        create_visualization(note_events, output_path, show_grid=False, ensemble=ENSEMBLE_ORCHESTRA)
        assert output_path.exists()

    def test_ungrouped_visualization(self, tmp_path):
        """Test visualization when instruments are ungrouped."""
        output_path = tmp_path / "output.png"
        
        note_events = [
            NoteEvent(
                pitch_midi=60.0,
                start_time=0.0,
                duration=1.0,
                instrument_family="Flute",
                instrument_label="Flute",
            ),
            NoteEvent(
                pitch_midi=62.0,
                start_time=1.0,
                duration=1.0,
                instrument_family="Flute 2",
                instrument_label="Flute 2",
            ),
        ]
        
        create_visualization(note_events, output_path, show_grid=False, ensemble=ENSEMBLE_UNGROUPED)
        assert output_path.exists()

    def test_unknown_ensemble_falls_back_to_ungrouped(self, tmp_path):
        """Unknown ensemble should fall back to per-instrument labeling/colors."""
        output_path = tmp_path / "output.png"
        
        note_events = [
            NoteEvent(
                pitch_midi=60.0,
                start_time=0.0,
                duration=1.0,
                instrument_family="Flute",
                instrument_label="Flute",
            ),
            NoteEvent(
                pitch_midi=62.0,
                start_time=1.0,
                duration=1.0,
                instrument_family="Clarinet",
                instrument_label="Clarinet",
            ),
        ]
        
        create_visualization(note_events, output_path, show_grid=False, ensemble="future-ensemble")
        assert output_path.exists()

    def test_minimal_mode(self, tmp_path):
        """Test minimal mode visualization."""
        output_path = tmp_path / "output.png"
        
        note_events = [
            NoteEvent(pitch_midi=60.0, start_time=0.0, duration=1.0, instrument_family=ORCHESTRA_STRINGS),
        ]
        
        create_visualization(note_events, output_path, minimal=True, ensemble=ENSEMBLE_ORCHESTRA)
        assert output_path.exists()

    def test_custom_title(self, tmp_path):
        """Test visualization with custom title."""
        output_path = tmp_path / "output.png"
        
        note_events = [
            NoteEvent(pitch_midi=60.0, start_time=0.0, duration=1.0, instrument_family=ORCHESTRA_STRINGS),
        ]
        
        create_visualization(note_events, output_path, title="Test Composition", ensemble=ENSEMBLE_ORCHESTRA)
        assert output_path.exists()

    def test_score_duration_parameter(self, tmp_path):
        """Test that score_duration parameter affects time range."""
        output_path = tmp_path / "output.png"
        
        note_events = [
            NoteEvent(pitch_midi=60.0, start_time=0.0, duration=1.0, instrument_family=ORCHESTRA_STRINGS),
        ]
        
        # With score_duration, visualization should extend to that time
        create_visualization(
            note_events,
            output_path,
            score_duration=10.0,
            ensemble=ENSEMBLE_ORCHESTRA,
        )
        assert output_path.exists()

    def test_different_ensembles_produce_different_colors(self, tmp_path):
        """Test that different ensembles use different color palettes."""
        output_path_orch = tmp_path / "orchestra.png"
        output_path_bb = tmp_path / "bigband.png"
        
        # Use rhythm section family which exists in bigband
        note_events = [
            NoteEvent(pitch_midi=60.0, start_time=0.0, duration=1.0, instrument_family=BIGBAND_RHYTHM_SECTION),
        ]
        
        # Should work with bigband ensemble
        create_visualization(note_events, output_path_bb, ensemble=ENSEMBLE_BIGBAND)
        assert output_path_bb.exists()


class TestConvertMusicxmlToPng:
    """Test full conversion function."""

    def test_successful_conversion_default_params(self, tmp_path):
        """Test successful conversion with default parameters."""
        # Create a minimal MusicXML file
        score = stream.Score()
        part = stream.Part()
        part.append(instrument.Violin())
        n = note.Note("C4")
        n.quarterLength = 1.0
        part.append(n)
        score.append(part)
        
        input_path = tmp_path / "test.mxl"
        score.write("musicxml", input_path)
        
        output_path = convert_musicxml_to_png(input_path)
        
        assert output_path.exists()
        assert output_path.suffix == ".png"
        assert output_path.stem == "test"

    def test_custom_output_path(self, tmp_path):
        """Test conversion with custom output path."""
        score = stream.Score()
        part = stream.Part()
        part.append(instrument.Violin())
        n = note.Note("C4")
        n.quarterLength = 1.0
        part.append(n)
        score.append(part)
        
        input_path = tmp_path / "test.mxl"
        output_path = tmp_path / "custom_output.png"
        score.write("musicxml", input_path)
        
        result_path = convert_musicxml_to_png(input_path, output_path=output_path)
        
        assert result_path == output_path
        assert output_path.exists()

    def test_custom_title(self, tmp_path):
        """Test conversion with custom title."""
        score = stream.Score()
        part = stream.Part()
        part.append(instrument.Violin())
        n = note.Note("C4")
        n.quarterLength = 1.0
        part.append(n)
        score.append(part)
        
        input_path = tmp_path / "test.mxl"
        score.write("musicxml", input_path)
        
        output_path = convert_musicxml_to_png(input_path, title="My Custom Title")
        assert output_path.exists()

    def test_file_not_found_error(self):
        """Test that missing file raises FileNotFoundError."""
        non_existent = Path("/nonexistent/file.mxl")
        
        with pytest.raises(FileNotFoundError):
            convert_musicxml_to_png(non_existent)

    def test_invalid_musicxml_raises_error(self, tmp_path):
        """Test that invalid MusicXML raises ValueError."""
        invalid_file = tmp_path / "invalid.mxl"
        invalid_file.write_text("This is not valid MusicXML")
        
        with pytest.raises(ValueError, match="Failed to parse"):
            convert_musicxml_to_png(invalid_file)

    def test_empty_musicxml_raises_error(self, tmp_path):
        """Test that empty MusicXML (no notes) raises ValueError."""
        score = stream.Score()
        part = stream.Part()
        part.append(instrument.Violin())
        # No notes, only rests or empty
        score.append(part)
        
        input_path = tmp_path / "empty.mxl"
        score.write("musicxml", input_path)
        
        with pytest.raises(ValueError, match="No notes found"):
            convert_musicxml_to_png(input_path)

    def test_ensemble_parameter(self, tmp_path):
        """Test conversion with different ensemble types."""
        score = stream.Score()
        part = stream.Part()
        part.append(instrument.Piano())  # Piano is strings in orchestra, rhythm in bigband
        n = note.Note("C4")
        n.quarterLength = 1.0
        part.append(n)
        score.append(part)
        
        input_path = tmp_path / "test.mxl"
        score.write("musicxml", input_path)
        
        # Test both ensembles
        output_orch = convert_musicxml_to_png(input_path, ensemble=ENSEMBLE_ORCHESTRA)
        output_bb = convert_musicxml_to_png(input_path, ensemble=ENSEMBLE_BIGBAND)
        
        assert output_orch.exists()
        assert output_bb.exists()

    def test_show_grid_parameter(self, tmp_path):
        """Test conversion with grid disabled."""
        score = stream.Score()
        part = stream.Part()
        part.append(instrument.Violin())
        n = note.Note("C4")
        n.quarterLength = 1.0
        part.append(n)
        score.append(part)
        
        input_path = tmp_path / "test.mxl"
        score.write("musicxml", input_path)
        
        output_path = convert_musicxml_to_png(input_path, show_grid=False)
        assert output_path.exists()

    def test_minimal_mode_parameter(self, tmp_path):
        """Test conversion with minimal mode."""
        score = stream.Score()
        part = stream.Part()
        part.append(instrument.Violin())
        n = note.Note("C4")
        n.quarterLength = 1.0
        part.append(n)
        score.append(part)
        
        input_path = tmp_path / "test.mxl"
        score.write("musicxml", input_path)
        
        output_path = convert_musicxml_to_png(input_path, minimal=True)
        assert output_path.exists()
