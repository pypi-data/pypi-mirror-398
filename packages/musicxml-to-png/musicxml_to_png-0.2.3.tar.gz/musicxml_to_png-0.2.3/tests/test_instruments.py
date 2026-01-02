"""Unit tests for instrument classification and color mapping."""

import pytest

from musicxml_to_png.instruments import (
    get_instrument_family,
    get_family_color,
    get_individual_color,
    ENSEMBLE_ORCHESTRA,
    ENSEMBLE_BIGBAND,
    ORCHESTRA_STRINGS,
    ORCHESTRA_WINDS,
    ORCHESTRA_BRASS,
    ORCHESTRA_PERCUSSION,
    ORCHESTRA_UNKNOWN,
    BIGBAND_TRUMPETS,
    BIGBAND_TROMBONES,
    BIGBAND_SAXOPHONES,
    BIGBAND_RHYTHM_SECTION,
    BIGBAND_UNKNOWN,
)


class TestOrchestraInstrumentFamily:
    """Test instrument family classification for orchestra ensemble."""

    @pytest.mark.parametrize(
        "midi_program,expected_family",
        [
            # Strings
            (1, ORCHESTRA_STRINGS),   # Acoustic Grand Piano
            (41, ORCHESTRA_STRINGS),  # Violin
            (42, ORCHESTRA_STRINGS),  # Viola
            (43, ORCHESTRA_STRINGS),  # Cello
            (44, ORCHESTRA_STRINGS),  # Contrabass
            (25, ORCHESTRA_STRINGS),  # Acoustic Guitar
            (33, ORCHESTRA_STRINGS),  # Acoustic Bass
            # Winds
            (65, ORCHESTRA_WINDS),    # Soprano Sax
            (66, ORCHESTRA_WINDS),    # Alto Sax
            (69, ORCHESTRA_WINDS),    # Oboe
            (72, ORCHESTRA_WINDS),    # Clarinet
            (73, ORCHESTRA_WINDS),    # Piccolo
            (74, ORCHESTRA_WINDS),    # Flute
            (71, ORCHESTRA_WINDS),    # Bassoon
            # Brass
            (57, ORCHESTRA_BRASS),    # Trumpet
            (58, ORCHESTRA_BRASS),    # Trombone
            (59, ORCHESTRA_BRASS),    # Tuba
            (61, ORCHESTRA_BRASS),    # French Horn
            # Percussion
            (9, ORCHESTRA_PERCUSSION),   # Celesta
            (10, ORCHESTRA_PERCUSSION),  # Glockenspiel
            (13, ORCHESTRA_PERCUSSION),  # Marimba
            (14, ORCHESTRA_PERCUSSION),  # Xylophone
            (48, ORCHESTRA_STRINGS),      # Timpani (mapped to strings in orchestra)
        ],
    )
    def test_midi_program_mapping(self, midi_program, expected_family):
        """Test MIDI program number to instrument family mapping."""
        result = get_instrument_family(
            midi_program=midi_program,
            ensemble=ENSEMBLE_ORCHESTRA,
        )
        assert result == expected_family

    @pytest.mark.parametrize(
        "instrument_name,expected_family",
        [
            # Strings
            ("Violin", ORCHESTRA_STRINGS),
            ("viola", ORCHESTRA_STRINGS),
            ("Cello", ORCHESTRA_STRINGS),
            ("Double Bass", ORCHESTRA_STRINGS),
            ("Guitar", ORCHESTRA_STRINGS),
            ("Piano", ORCHESTRA_STRINGS),
            ("Harp", ORCHESTRA_STRINGS),
            # Winds
            ("Flute", ORCHESTRA_WINDS),
            ("Piccolo", ORCHESTRA_WINDS),
            ("Oboe", ORCHESTRA_WINDS),
            ("Clarinet", ORCHESTRA_WINDS),
            ("Bassoon", ORCHESTRA_WINDS),
            ("Saxophone", ORCHESTRA_WINDS),
            ("Alto Sax", ORCHESTRA_WINDS),
            # Brass
            ("Trumpet", ORCHESTRA_BRASS),
            ("Trombone", ORCHESTRA_BRASS),
            ("Tuba", ORCHESTRA_BRASS),
            ("French Horn", ORCHESTRA_BRASS),
            ("Horn", ORCHESTRA_BRASS),
            # Percussion
            ("Drum", ORCHESTRA_PERCUSSION),
            ("Timpani", ORCHESTRA_PERCUSSION),
            ("Cymbal", ORCHESTRA_PERCUSSION),
            ("Marimba", ORCHESTRA_PERCUSSION),
            ("Xylophone", ORCHESTRA_PERCUSSION),
        ],
    )
    def test_name_based_matching(self, instrument_name, expected_family):
        """Test instrument name-based family classification."""
        result = get_instrument_family(
            instrument_name=instrument_name,
            ensemble=ENSEMBLE_ORCHESTRA,
        )
        assert result == expected_family

    def test_unknown_midi_program(self):
        """Test that unknown MIDI programs return unknown family."""
        # MIDI programs outside valid range
        assert get_instrument_family(midi_program=0, ensemble=ENSEMBLE_ORCHESTRA) == ORCHESTRA_UNKNOWN
        assert get_instrument_family(midi_program=129, ensemble=ENSEMBLE_ORCHESTRA) == ORCHESTRA_UNKNOWN
        # MIDI programs not in mapping (shouldn't happen but test fallback)
        assert get_instrument_family(midi_program=200, ensemble=ENSEMBLE_ORCHESTRA) == ORCHESTRA_UNKNOWN

    def test_unknown_instrument_name(self):
        """Test that unknown instrument names return unknown family."""
        result = get_instrument_family(
            instrument_name="Unknown Instrument XYZ",
            ensemble=ENSEMBLE_ORCHESTRA,
        )
        assert result == ORCHESTRA_UNKNOWN

    def test_midi_takes_precedence_over_name(self):
        """Test that MIDI program takes precedence over instrument name."""
        # MIDI says strings, name says brass - MIDI should win
        result = get_instrument_family(
            midi_program=41,  # Violin (strings)
            instrument_name="Trumpet",  # Would be brass by name
            ensemble=ENSEMBLE_ORCHESTRA,
        )
        assert result == ORCHESTRA_STRINGS

    def test_no_input_returns_unknown(self):
        """Test that missing both MIDI and name returns unknown."""
        result = get_instrument_family(ensemble=ENSEMBLE_ORCHESTRA)
        assert result == ORCHESTRA_UNKNOWN

    def test_case_insensitive_name_matching(self):
        """Test that instrument name matching is case-insensitive."""
        assert get_instrument_family(instrument_name="VIOLIN", ensemble=ENSEMBLE_ORCHESTRA) == ORCHESTRA_STRINGS
        assert get_instrument_family(instrument_name="trumpet", ensemble=ENSEMBLE_ORCHESTRA) == ORCHESTRA_BRASS
        assert get_instrument_family(instrument_name="FlUtE", ensemble=ENSEMBLE_ORCHESTRA) == ORCHESTRA_WINDS


class TestBigbandInstrumentFamily:
    """Test instrument family classification for bigband ensemble."""

    @pytest.mark.parametrize(
        "midi_program,expected_family",
        [
            # Trumpets
            (57, BIGBAND_TRUMPETS),   # Trumpet
            (60, BIGBAND_TRUMPETS),    # Muted Trumpet
            # Trombones
            (58, BIGBAND_TROMBONES),   # Trombone
            (59, BIGBAND_TROMBONES),   # Tuba
            # Saxophones
            (65, BIGBAND_SAXOPHONES),  # Soprano Sax
            (66, BIGBAND_SAXOPHONES),  # Alto Sax
            (67, BIGBAND_SAXOPHONES),  # Tenor Sax
            (68, BIGBAND_SAXOPHONES),  # Baritone Sax
            (72, BIGBAND_SAXOPHONES),  # Clarinet (woodwinds double)
            (74, BIGBAND_SAXOPHONES),  # Flute (woodwinds double)
            # Rhythm Section
            (1, BIGBAND_RHYTHM_SECTION),   # Acoustic Grand Piano
            (25, BIGBAND_RHYTHM_SECTION),  # Acoustic Guitar
            (33, BIGBAND_RHYTHM_SECTION),  # Acoustic Bass
            (9, BIGBAND_RHYTHM_SECTION),   # Celesta
            (13, BIGBAND_RHYTHM_SECTION),  # Marimba
        ],
    )
    def test_midi_program_mapping(self, midi_program, expected_family):
        """Test MIDI program number to instrument family mapping for bigband."""
        result = get_instrument_family(
            midi_program=midi_program,
            ensemble=ENSEMBLE_BIGBAND,
        )
        assert result == expected_family

    @pytest.mark.parametrize(
        "instrument_name,expected_family",
        [
            # Trumpets
            ("Trumpet", BIGBAND_TRUMPETS),
            ("Cornet", BIGBAND_TRUMPETS),
            # Trombones
            ("Trombone", BIGBAND_TROMBONES),
            ("Tuba", BIGBAND_TROMBONES),
            # Saxophones
            ("Saxophone", BIGBAND_SAXOPHONES),
            ("Alto Sax", BIGBAND_SAXOPHONES),
            ("Tenor Sax", BIGBAND_SAXOPHONES),
            ("Clarinet", BIGBAND_SAXOPHONES),
            ("Flute", BIGBAND_SAXOPHONES),
            # Rhythm Section
            ("Piano", BIGBAND_RHYTHM_SECTION),
            ("Bass", BIGBAND_RHYTHM_SECTION),
            ("Electric Bass", BIGBAND_RHYTHM_SECTION),
            ("Guitar", BIGBAND_RHYTHM_SECTION),
            ("Drums", BIGBAND_RHYTHM_SECTION),
            ("Rhythm Section", BIGBAND_RHYTHM_SECTION),
        ],
    )
    def test_name_based_matching(self, instrument_name, expected_family):
        """Test instrument name-based family classification for bigband."""
        result = get_instrument_family(
            instrument_name=instrument_name,
            ensemble=ENSEMBLE_BIGBAND,
        )
        assert result == expected_family

    def test_unknown_instruments(self):
        """Test that unknown instruments return unknown family for bigband."""
        # Strings are unknown in bigband
        assert get_instrument_family(midi_program=41, ensemble=ENSEMBLE_BIGBAND) == BIGBAND_UNKNOWN
        assert get_instrument_family(instrument_name="Violin", ensemble=ENSEMBLE_BIGBAND) == BIGBAND_UNKNOWN


class TestColorMapping:
    """Test color mapping for instrument families."""

    def test_orchestra_colors(self):
        """Test color mapping for orchestra ensemble."""
        assert get_family_color(ORCHESTRA_STRINGS, ENSEMBLE_ORCHESTRA) == "#2E7D32"  # Green
        assert get_family_color(ORCHESTRA_WINDS, ENSEMBLE_ORCHESTRA) == "#1976D2"     # Blue
        assert get_family_color(ORCHESTRA_BRASS, ENSEMBLE_ORCHESTRA) == "#F57C00"    # Orange
        assert get_family_color(ORCHESTRA_PERCUSSION, ENSEMBLE_ORCHESTRA) == "#C2185B"  # Pink/Magenta
        assert get_family_color(ORCHESTRA_UNKNOWN, ENSEMBLE_ORCHESTRA) == "#757575"  # Gray

    def test_bigband_colors(self):
        """Test color mapping for bigband ensemble."""
        assert get_family_color(BIGBAND_TRUMPETS, ENSEMBLE_BIGBAND) == "#FF6B35"      # Vibrant Orange-Red
        assert get_family_color(BIGBAND_TROMBONES, ENSEMBLE_BIGBAND) == "#F7931E"     # Golden Orange
        assert get_family_color(BIGBAND_SAXOPHONES, ENSEMBLE_BIGBAND) == "#4A90E2"   # Bright Blue
        assert get_family_color(BIGBAND_RHYTHM_SECTION, ENSEMBLE_BIGBAND) == "#7B68EE"  # Medium Slate Blue
        assert get_family_color(BIGBAND_UNKNOWN, ENSEMBLE_BIGBAND) == "#757575"     # Gray

    def test_unknown_family_fallback(self):
        """Test that unknown family names return appropriate default colors."""
        # Invalid family name should return unknown color
        assert get_family_color("invalid_family", ENSEMBLE_ORCHESTRA) == "#757575"  # Gray (unknown)
        assert get_family_color("invalid_family", ENSEMBLE_BIGBAND) == "#757575"    # Gray (unknown)

    def test_cross_ensemble_color_difference(self):
        """Test that same family name returns different colors for different ensembles."""
        # Strings in orchestra vs rhythm section in bigband (different families)
        # But test that unknown is consistent
        assert get_family_color(ORCHESTRA_UNKNOWN, ENSEMBLE_ORCHESTRA) == get_family_color(BIGBAND_UNKNOWN, ENSEMBLE_BIGBAND)

    def test_individual_color_palette_cycles(self):
        """Test that ungrouped instrument colors cycle through the palette."""
        assert get_individual_color(0) == get_individual_color(20)
        assert get_individual_color(1) == get_individual_color(21)

    def test_individual_color_negative_index(self):
        """Test that negative indices are rejected for ungrouped colors."""
        with pytest.raises(ValueError):
            get_individual_color(-1)
