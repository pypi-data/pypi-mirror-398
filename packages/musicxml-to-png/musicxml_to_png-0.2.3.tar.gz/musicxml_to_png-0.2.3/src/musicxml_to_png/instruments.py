"""Instrument family classification and color mapping."""

from typing import Optional

# Ensemble types
ENSEMBLE_UNGROUPED = "ungrouped"
ENSEMBLE_ORCHESTRA = "orchestra"
ENSEMBLE_BIGBAND = "bigband"

# Orchestra instrument families
ORCHESTRA_STRINGS = "strings"
ORCHESTRA_WINDS = "winds"
ORCHESTRA_BRASS = "brass"
ORCHESTRA_PERCUSSION = "percussion"
ORCHESTRA_UNKNOWN = "unknown"

# Bigband instrument families
BIGBAND_TRUMPETS = "trumpets"
BIGBAND_TROMBONES = "trombones"
BIGBAND_SAXOPHONES = "saxophones"
BIGBAND_RHYTHM_SECTION = "rhythm_section"
BIGBAND_UNKNOWN = "unknown"

# Orchestra color palette
ORCHESTRA_COLORS = {
    ORCHESTRA_STRINGS: "#2E7D32",  # Green
    ORCHESTRA_WINDS: "#1976D2",    # Blue
    ORCHESTRA_BRASS: "#F57C00",    # Orange
    ORCHESTRA_PERCUSSION: "#C2185B",  # Pink/Magenta
    ORCHESTRA_UNKNOWN: "#757575",  # Gray
}

# Bigband color palette
BIGBAND_COLORS = {
    BIGBAND_TRUMPETS: "#FF6B35",      # Vibrant Orange-Red
    BIGBAND_TROMBONES: "#F7931E",    # Golden Orange
    BIGBAND_SAXOPHONES: "#4A90E2",   # Bright Blue
    BIGBAND_RHYTHM_SECTION: "#7B68EE",  # Medium Slate Blue
    BIGBAND_UNKNOWN: "#757575",      # Gray
}

# Individual instrument color palette (cycled for more than 20 instruments)
# Based on Matplotlib's tab20 palette for good contrast
INDIVIDUAL_COLOR_PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#393b79", "#637939", "#8c6d31", "#843c39", "#7b4173",
    "#5254a3", "#9c9ede", "#ad494a", "#d6616b", "#e7ba52",
]

# Orchestra MIDI program mapping
ORCHESTRA_MIDI_MAPPING = {
    # Piano (1-8) - treat as strings-like
    1: ORCHESTRA_STRINGS,  # Acoustic Grand Piano
    2: ORCHESTRA_STRINGS,  # Bright Acoustic Piano
    3: ORCHESTRA_STRINGS,  # Electric Grand Piano
    4: ORCHESTRA_STRINGS,  # Honky-tonk Piano
    5: ORCHESTRA_STRINGS,  # Electric Piano 1
    6: ORCHESTRA_STRINGS,  # Electric Piano 2
    7: ORCHESTRA_STRINGS,  # Harpsichord
    8: ORCHESTRA_STRINGS,  # Clavi
    
    # Chromatic Percussion (9-16)
    9: ORCHESTRA_PERCUSSION,   # Celesta
    10: ORCHESTRA_PERCUSSION,  # Glockenspiel
    11: ORCHESTRA_PERCUSSION,  # Music Box
    12: ORCHESTRA_PERCUSSION,  # Vibraphone
    13: ORCHESTRA_PERCUSSION,  # Marimba
    14: ORCHESTRA_PERCUSSION,  # Xylophone
    15: ORCHESTRA_PERCUSSION,  # Tubular Bells
    16: ORCHESTRA_PERCUSSION,  # Dulcimer
    
    # Organ (17-24) - treat as winds-like
    17: ORCHESTRA_WINDS,  # Drawbar Organ
    18: ORCHESTRA_WINDS,  # Percussive Organ
    19: ORCHESTRA_WINDS,  # Rock Organ
    20: ORCHESTRA_WINDS,  # Church Organ
    21: ORCHESTRA_WINDS,  # Reed Organ
    22: ORCHESTRA_WINDS,  # Accordion
    23: ORCHESTRA_WINDS,  # Harmonica
    24: ORCHESTRA_WINDS,  # Tango Accordion
    
    # Guitar (25-32) - strings
    25: ORCHESTRA_STRINGS,  # Acoustic Guitar (nylon)
    26: ORCHESTRA_STRINGS,  # Acoustic Guitar (steel)
    27: ORCHESTRA_STRINGS,  # Electric Guitar (jazz)
    28: ORCHESTRA_STRINGS,  # Electric Guitar (clean)
    29: ORCHESTRA_STRINGS,  # Electric Guitar (muted)
    30: ORCHESTRA_STRINGS,  # Overdriven Guitar
    31: ORCHESTRA_STRINGS,  # Distortion Guitar
    32: ORCHESTRA_STRINGS,  # Guitar harmonics
    
    # Bass (33-40) - strings
    33: ORCHESTRA_STRINGS,  # Acoustic Bass
    34: ORCHESTRA_STRINGS,  # Electric Bass (finger)
    35: ORCHESTRA_STRINGS,  # Electric Bass (pick)
    36: ORCHESTRA_STRINGS,  # Fretless Bass
    37: ORCHESTRA_STRINGS,  # Slap Bass 1
    38: ORCHESTRA_STRINGS,  # Slap Bass 2
    39: ORCHESTRA_STRINGS,  # Synth Bass 1
    40: ORCHESTRA_STRINGS,  # Synth Bass 2
    
    # Strings (41-48)
    41: ORCHESTRA_STRINGS,  # Violin
    42: ORCHESTRA_STRINGS,  # Viola
    43: ORCHESTRA_STRINGS,  # Cello
    44: ORCHESTRA_STRINGS,  # Contrabass
    45: ORCHESTRA_STRINGS,  # Tremolo Strings
    46: ORCHESTRA_STRINGS,  # Pizzicato Strings
    47: ORCHESTRA_STRINGS,  # Orchestral Harp
    48: ORCHESTRA_STRINGS,  # Timpani
    
    # Ensemble (49-56) - mostly strings
    49: ORCHESTRA_STRINGS,  # String Ensemble 1
    50: ORCHESTRA_STRINGS,  # String Ensemble 2
    51: ORCHESTRA_STRINGS,  # SynthStrings 1
    52: ORCHESTRA_STRINGS,  # SynthStrings 2
    53: ORCHESTRA_WINDS,    # Choir Aahs
    54: ORCHESTRA_WINDS,    # Voice Oohs
    55: ORCHESTRA_WINDS,    # Synth Voice
    56: ORCHESTRA_BRASS,    # Orchestra Hit
    
    # Brass (57-64)
    57: ORCHESTRA_BRASS,  # Trumpet
    58: ORCHESTRA_BRASS,  # Trombone
    59: ORCHESTRA_BRASS,  # Tuba
    60: ORCHESTRA_BRASS,  # Muted Trumpet
    61: ORCHESTRA_BRASS,  # French Horn
    62: ORCHESTRA_BRASS,  # Brass Section
    63: ORCHESTRA_BRASS,  # SynthBrass 1
    64: ORCHESTRA_BRASS,  # SynthBrass 2
    
    # Reed (65-72) - winds
    65: ORCHESTRA_WINDS,  # Soprano Sax
    66: ORCHESTRA_WINDS,  # Alto Sax
    67: ORCHESTRA_WINDS,  # Tenor Sax
    68: ORCHESTRA_WINDS,  # Baritone Sax
    69: ORCHESTRA_WINDS,  # Oboe
    70: ORCHESTRA_WINDS,  # English Horn
    71: ORCHESTRA_WINDS,  # Bassoon
    72: ORCHESTRA_WINDS,  # Clarinet
    
    # Pipe (73-80) - winds
    73: ORCHESTRA_WINDS,  # Piccolo
    74: ORCHESTRA_WINDS,  # Flute
    75: ORCHESTRA_WINDS,  # Recorder
    76: ORCHESTRA_WINDS,  # Pan Flute
    77: ORCHESTRA_WINDS,  # Blown Bottle
    78: ORCHESTRA_WINDS,  # Shakuhachi
    79: ORCHESTRA_WINDS,  # Whistle
    80: ORCHESTRA_WINDS,  # Ocarina
    
    # Synth Lead (81-88) - treat as winds
    81: ORCHESTRA_WINDS,  # Lead 1 (square)
    82: ORCHESTRA_WINDS,  # Lead 2 (sawtooth)
    83: ORCHESTRA_WINDS,  # Lead 3 (calliope)
    84: ORCHESTRA_WINDS,  # Lead 4 (chiff)
    85: ORCHESTRA_WINDS,  # Lead 5 (charang)
    86: ORCHESTRA_WINDS,  # Lead 6 (voice)
    87: ORCHESTRA_WINDS,  # Lead 7 (fifths)
    88: ORCHESTRA_WINDS,  # Lead 8 (bass + lead)
    
    # Synth Pad (89-96) - treat as strings
    89: ORCHESTRA_STRINGS,  # Pad 1 (new age)
    90: ORCHESTRA_STRINGS,  # Pad 2 (warm)
    91: ORCHESTRA_STRINGS,  # Pad 3 (polysynth)
    92: ORCHESTRA_STRINGS,  # Pad 4 (choir)
    93: ORCHESTRA_STRINGS,  # Pad 5 (bowed)
    94: ORCHESTRA_STRINGS,  # Pad 6 (metallic)
    95: ORCHESTRA_STRINGS,  # Pad 7 (halo)
    96: ORCHESTRA_STRINGS,  # Pad 8 (sweep)
    
    # Synth Effects (97-104) - treat as unknown
    97: ORCHESTRA_UNKNOWN,  # FX 1 (rain)
    98: ORCHESTRA_UNKNOWN,  # FX 2 (soundtrack)
    99: ORCHESTRA_UNKNOWN,  # FX 3 (crystal)
    100: ORCHESTRA_UNKNOWN,  # FX 4 (atmosphere)
    101: ORCHESTRA_UNKNOWN,  # FX 5 (brightness)
    102: ORCHESTRA_UNKNOWN,  # FX 6 (goblins)
    103: ORCHESTRA_UNKNOWN,  # FX 7 (echoes)
    104: ORCHESTRA_UNKNOWN,  # FX 8 (sci-fi)
    
    # Ethnic (105-112) - mixed
    105: ORCHESTRA_WINDS,  # Sitar
    106: ORCHESTRA_STRINGS,  # Banjo
    107: ORCHESTRA_STRINGS,  # Shamisen
    108: ORCHESTRA_STRINGS,  # Koto
    109: ORCHESTRA_STRINGS,  # Kalimba
    110: ORCHESTRA_STRINGS,  # Bag pipe
    111: ORCHESTRA_WINDS,  # Fiddle
    112: ORCHESTRA_STRINGS,  # Shanai
    
    # Percussive (113-120) - percussion
    113: ORCHESTRA_PERCUSSION,  # Tinkle Bell
    114: ORCHESTRA_PERCUSSION,  # Agogo
    115: ORCHESTRA_PERCUSSION,  # Steel Drums
    116: ORCHESTRA_PERCUSSION,  # Woodblock
    117: ORCHESTRA_PERCUSSION,  # Taiko Drum
    118: ORCHESTRA_PERCUSSION,  # Melodic Tom
    119: ORCHESTRA_PERCUSSION,  # Synth Drum
    120: ORCHESTRA_PERCUSSION,  # Reverse Cymbal
    
    # Sound Effects (121-128) - percussion/unknown
    121: ORCHESTRA_PERCUSSION,  # Guitar Fret Noise
    122: ORCHESTRA_PERCUSSION,  # Breath Noise
    123: ORCHESTRA_PERCUSSION,  # Seashore
    124: ORCHESTRA_PERCUSSION,  # Bird Tweet
    125: ORCHESTRA_PERCUSSION,  # Telephone Ring
    126: ORCHESTRA_PERCUSSION,  # Helicopter
    127: ORCHESTRA_PERCUSSION,  # Applause
    128: ORCHESTRA_PERCUSSION,  # Gunshot
}

# Bigband MIDI program mapping
BIGBAND_MIDI_MAPPING = {
    # Piano (1-8) → rhythm_section
    1: BIGBAND_RHYTHM_SECTION,  # Acoustic Grand Piano
    2: BIGBAND_RHYTHM_SECTION,  # Bright Acoustic Piano
    3: BIGBAND_RHYTHM_SECTION,  # Electric Grand Piano
    4: BIGBAND_RHYTHM_SECTION,  # Honky-tonk Piano
    5: BIGBAND_RHYTHM_SECTION,  # Electric Piano 1
    6: BIGBAND_RHYTHM_SECTION,  # Electric Piano 2
    7: BIGBAND_RHYTHM_SECTION,  # Harpsichord
    8: BIGBAND_RHYTHM_SECTION,  # Clavi
    
    # Chromatic Percussion (9-16) → rhythm_section
    9: BIGBAND_RHYTHM_SECTION,   # Celesta
    10: BIGBAND_RHYTHM_SECTION,  # Glockenspiel
    11: BIGBAND_RHYTHM_SECTION,  # Music Box
    12: BIGBAND_RHYTHM_SECTION,  # Vibraphone
    13: BIGBAND_RHYTHM_SECTION,  # Marimba
    14: BIGBAND_RHYTHM_SECTION,  # Xylophone
    15: BIGBAND_RHYTHM_SECTION,  # Tubular Bells
    16: BIGBAND_RHYTHM_SECTION,  # Dulcimer
    
    # Organ (17-24) → rhythm_section (often used in bigband)
    17: BIGBAND_RHYTHM_SECTION,  # Drawbar Organ
    18: BIGBAND_RHYTHM_SECTION,  # Percussive Organ
    19: BIGBAND_RHYTHM_SECTION,  # Rock Organ
    20: BIGBAND_RHYTHM_SECTION,  # Church Organ
    21: BIGBAND_RHYTHM_SECTION,  # Reed Organ
    22: BIGBAND_RHYTHM_SECTION,  # Accordion
    23: BIGBAND_RHYTHM_SECTION,  # Harmonica
    24: BIGBAND_RHYTHM_SECTION,  # Tango Accordion
    
    # Guitar (25-32) → rhythm_section
    25: BIGBAND_RHYTHM_SECTION,  # Acoustic Guitar (nylon)
    26: BIGBAND_RHYTHM_SECTION,  # Acoustic Guitar (steel)
    27: BIGBAND_RHYTHM_SECTION,  # Electric Guitar (jazz)
    28: BIGBAND_RHYTHM_SECTION,  # Electric Guitar (clean)
    29: BIGBAND_RHYTHM_SECTION,  # Electric Guitar (muted)
    30: BIGBAND_RHYTHM_SECTION,  # Overdriven Guitar
    31: BIGBAND_RHYTHM_SECTION,  # Distortion Guitar
    32: BIGBAND_RHYTHM_SECTION,  # Guitar harmonics
    
    # Bass (33-40) → rhythm_section
    33: BIGBAND_RHYTHM_SECTION,  # Acoustic Bass
    34: BIGBAND_RHYTHM_SECTION,  # Electric Bass (finger)
    35: BIGBAND_RHYTHM_SECTION,  # Electric Bass (pick)
    36: BIGBAND_RHYTHM_SECTION,  # Fretless Bass
    37: BIGBAND_RHYTHM_SECTION,  # Slap Bass 1
    38: BIGBAND_RHYTHM_SECTION,  # Slap Bass 2
    39: BIGBAND_RHYTHM_SECTION,  # Synth Bass 1
    40: BIGBAND_RHYTHM_SECTION,  # Synth Bass 2
    
    # Strings (41-48) → unknown (not typical bigband)
    41: BIGBAND_UNKNOWN,  # Violin
    42: BIGBAND_UNKNOWN,  # Viola
    43: BIGBAND_UNKNOWN,  # Cello
    44: BIGBAND_UNKNOWN,  # Contrabass
    45: BIGBAND_UNKNOWN,  # Tremolo Strings
    46: BIGBAND_UNKNOWN,  # Pizzicato Strings
    47: BIGBAND_UNKNOWN,  # Orchestral Harp
    48: BIGBAND_RHYTHM_SECTION,  # Timpani
    
    # Ensemble (49-56) → mostly unknown
    49: BIGBAND_UNKNOWN,  # String Ensemble 1
    50: BIGBAND_UNKNOWN,  # String Ensemble 2
    51: BIGBAND_UNKNOWN,  # SynthStrings 1
    52: BIGBAND_UNKNOWN,  # SynthStrings 2
    53: BIGBAND_UNKNOWN,  # Choir Aahs
    54: BIGBAND_UNKNOWN,  # Voice Oohs
    55: BIGBAND_UNKNOWN,  # Synth Voice
    56: BIGBAND_UNKNOWN,  # Orchestra Hit
    
    # Brass (57-64) → trumpets or trombones
    57: BIGBAND_TRUMPETS,  # Trumpet
    58: BIGBAND_TROMBONES,  # Trombone
    59: BIGBAND_TROMBONES,  # Tuba
    60: BIGBAND_TRUMPETS,  # Muted Trumpet
    61: BIGBAND_UNKNOWN,  # French Horn (not typical bigband)
    62: BIGBAND_UNKNOWN,  # Brass Section
    63: BIGBAND_UNKNOWN,  # SynthBrass 1
    64: BIGBAND_UNKNOWN,  # SynthBrass 2
    
    # Reed (65-72) → saxophones
    65: BIGBAND_SAXOPHONES,  # Soprano Sax
    66: BIGBAND_SAXOPHONES,  # Alto Sax
    67: BIGBAND_SAXOPHONES,  # Tenor Sax
    68: BIGBAND_SAXOPHONES,  # Baritone Sax
    69: BIGBAND_SAXOPHONES,  # Oboe (woodwinds double)
    70: BIGBAND_SAXOPHONES,  # English Horn (woodwinds double)
    71: BIGBAND_SAXOPHONES,  # Bassoon (woodwinds double)
    72: BIGBAND_SAXOPHONES,  # Clarinet (woodwinds double)
    
    # Pipe (73-80) → saxophones (woodwinds double)
    73: BIGBAND_SAXOPHONES,  # Piccolo
    74: BIGBAND_SAXOPHONES,  # Flute
    75: BIGBAND_SAXOPHONES,  # Recorder
    76: BIGBAND_SAXOPHONES,  # Pan Flute
    77: BIGBAND_SAXOPHONES,  # Blown Bottle
    78: BIGBAND_SAXOPHONES,  # Shakuhachi
    79: BIGBAND_SAXOPHONES,  # Whistle
    80: BIGBAND_SAXOPHONES,  # Ocarina
    
    # Synth Lead (81-88) → rhythm_section
    81: BIGBAND_RHYTHM_SECTION,  # Lead 1 (square)
    82: BIGBAND_RHYTHM_SECTION,  # Lead 2 (sawtooth)
    83: BIGBAND_RHYTHM_SECTION,  # Lead 3 (calliope)
    84: BIGBAND_RHYTHM_SECTION,  # Lead 4 (chiff)
    85: BIGBAND_RHYTHM_SECTION,  # Lead 5 (charang)
    86: BIGBAND_RHYTHM_SECTION,  # Lead 6 (voice)
    87: BIGBAND_RHYTHM_SECTION,  # Lead 7 (fifths)
    88: BIGBAND_RHYTHM_SECTION,  # Lead 8 (bass + lead)
    
    # Synth Pad (89-96) → rhythm_section
    89: BIGBAND_RHYTHM_SECTION,  # Pad 1 (new age)
    90: BIGBAND_RHYTHM_SECTION,  # Pad 2 (warm)
    91: BIGBAND_RHYTHM_SECTION,  # Pad 3 (polysynth)
    92: BIGBAND_RHYTHM_SECTION,  # Pad 4 (choir)
    93: BIGBAND_RHYTHM_SECTION,  # Pad 5 (bowed)
    94: BIGBAND_RHYTHM_SECTION,  # Pad 6 (metallic)
    95: BIGBAND_RHYTHM_SECTION,  # Pad 7 (halo)
    96: BIGBAND_RHYTHM_SECTION,  # Pad 8 (sweep)
    
    # Synth Effects (97-104) → unknown
    97: BIGBAND_UNKNOWN,  # FX 1 (rain)
    98: BIGBAND_UNKNOWN,  # FX 2 (soundtrack)
    99: BIGBAND_UNKNOWN,  # FX 3 (crystal)
    100: BIGBAND_UNKNOWN,  # FX 4 (atmosphere)
    101: BIGBAND_UNKNOWN,  # FX 5 (brightness)
    102: BIGBAND_UNKNOWN,  # FX 6 (goblins)
    103: BIGBAND_UNKNOWN,  # FX 7 (echoes)
    104: BIGBAND_UNKNOWN,  # FX 8 (sci-fi)
    
    # Ethnic (105-112) → mostly unknown
    105: BIGBAND_UNKNOWN,  # Sitar
    106: BIGBAND_UNKNOWN,  # Banjo
    107: BIGBAND_UNKNOWN,  # Shamisen
    108: BIGBAND_UNKNOWN,  # Koto
    109: BIGBAND_UNKNOWN,  # Kalimba
    110: BIGBAND_UNKNOWN,  # Bag pipe
    111: BIGBAND_UNKNOWN,  # Fiddle
    112: BIGBAND_UNKNOWN,  # Shanai
    
    # Percussive (113-120) → rhythm_section
    113: BIGBAND_RHYTHM_SECTION,  # Tinkle Bell
    114: BIGBAND_RHYTHM_SECTION,  # Agogo
    115: BIGBAND_RHYTHM_SECTION,  # Steel Drums
    116: BIGBAND_RHYTHM_SECTION,  # Woodblock
    117: BIGBAND_RHYTHM_SECTION,  # Taiko Drum
    118: BIGBAND_RHYTHM_SECTION,  # Melodic Tom
    119: BIGBAND_RHYTHM_SECTION,  # Synth Drum
    120: BIGBAND_RHYTHM_SECTION,  # Reverse Cymbal
    
    # Sound Effects (121-128) → rhythm_section or unknown
    121: BIGBAND_RHYTHM_SECTION,  # Guitar Fret Noise
    122: BIGBAND_RHYTHM_SECTION,  # Breath Noise
    123: BIGBAND_UNKNOWN,  # Seashore
    124: BIGBAND_UNKNOWN,  # Bird Tweet
    125: BIGBAND_UNKNOWN,  # Telephone Ring
    126: BIGBAND_UNKNOWN,  # Helicopter
    127: BIGBAND_UNKNOWN,  # Applause
    128: BIGBAND_UNKNOWN,  # Gunshot
}

# Orchestra instrument name keywords
ORCHESTRA_NAME_KEYWORDS = {
    ORCHESTRA_STRINGS: [
        "violin", "viola", "cello", "contrabass", "double bass", "bass",
        "guitar", "harp", "piano", "pianoforte", "harpsichord", "clavichord",
        "banjo", "mandolin", "ukulele", "lute", "sitar", "shamisen", "koto",
        "strings", "string", "pizzicato", "tremolo",
    ],
    ORCHESTRA_WINDS: [
        "flute", "piccolo", "recorder", "oboe", "english horn", "cor anglais",
        "clarinet", "bassoon", "contrabassoon", "saxophone", "sax", "soprano",
        "alto", "tenor", "baritone", "bass clarinet", "bassoon", "fagotto",
        "organ", "accordion", "harmonica", "pan flute", "whistle", "ocarina",
        "shakuhachi", "bagpipe", "fiddle",
    ],
    ORCHESTRA_BRASS: [
        "trumpet", "cornet", "trombone", "tuba", "french horn", "horn",
        "euphonium", "baritone", "flugelhorn", "bugle", "brass", "muted",
    ],
    ORCHESTRA_PERCUSSION: [
        "drum", "timpani", "snare", "bass drum", "cymbal", "triangle",
        "tambourine", "marimba", "xylophone", "vibraphone", "glockenspiel",
        "celesta", "gong", "bell", "chime", "woodblock", "clap", "percussion",
        "tom", "hi-hat", "crash", "ride",
    ],
}

# Bigband instrument name keywords
BIGBAND_NAME_KEYWORDS = {
    BIGBAND_TRUMPETS: [
        "trumpet", "cornet", "flugelhorn", "bugle",
    ],
    BIGBAND_TROMBONES: [
        "trombone", "tuba", "euphonium", "baritone horn",
    ],
    BIGBAND_SAXOPHONES: [
        "saxophone", "sax", "soprano sax", "alto sax", "tenor sax", "baritone sax",
        "flute", "piccolo", "clarinet", "oboe", "bassoon", "english horn",
        "woodwind", "reed",
    ],
    BIGBAND_RHYTHM_SECTION: [
        "piano", "pianoforte", "keyboard", "organ", "harpsichord",
        "bass", "double bass", "acoustic bass", "electric bass", "upright bass",
        "drum", "drums", "snare", "bass drum", "cymbal", "hi-hat", "crash", "ride",
        "guitar", "acoustic guitar", "electric guitar", "rhythm", "rhythm section",
        "percussion", "vibraphone", "marimba", "xylophone",
    ],
}


def get_instrument_family(
    midi_program: Optional[int] = None,
    instrument_name: Optional[str] = None,
    ensemble: str = ENSEMBLE_ORCHESTRA,
) -> str:
    """
    Determine instrument family from MIDI program number and/or instrument name.
    
    Args:
        midi_program: MIDI program number (1-128)
        instrument_name: Name of the instrument (case-insensitive)
        ensemble: Ensemble type (orchestra or bigband), defaults to orchestra
    
    Returns:
        Instrument family string based on the ensemble type
    """
    # Select the appropriate mapping based on ensemble type
    if ensemble == ENSEMBLE_BIGBAND:
        midi_mapping = BIGBAND_MIDI_MAPPING
        name_keywords = BIGBAND_NAME_KEYWORDS
        unknown_family = BIGBAND_UNKNOWN
    else:  # Default to orchestra
        midi_mapping = ORCHESTRA_MIDI_MAPPING
        name_keywords = ORCHESTRA_NAME_KEYWORDS
        unknown_family = ORCHESTRA_UNKNOWN
    
    # First, try MIDI program number
    if midi_program is not None and 1 <= midi_program <= 128:
        return midi_mapping.get(midi_program, unknown_family)
    
    # Fall back to instrument name matching
    if instrument_name:
        name_lower = instrument_name.lower()
        # Collect all (keyword, family) pairs and sort by keyword length (longest first)
        # This ensures more specific keywords (e.g., "bassoon") match before generic ones (e.g., "bass")
        # across all families, preventing "bass" from matching "bassoon" before "bassoon" is checked
        keyword_family_pairs = []
        for family, keywords in name_keywords.items():
            for keyword in keywords:
                keyword_family_pairs.append((keyword, family))
        
        # Sort by keyword length (longest first) to prioritize specific matches
        keyword_family_pairs.sort(key=lambda x: len(x[0]), reverse=True)
        
        for keyword, family in keyword_family_pairs:
            if keyword in name_lower:
                return family
    
    return unknown_family


def get_family_color(family: str, ensemble: str = ENSEMBLE_ORCHESTRA) -> str:
    """
    Get the color for an instrument family based on ensemble type.
    
    Args:
        family: Instrument family string
        ensemble: Ensemble type (orchestra or bigband), defaults to orchestra
    
    Returns:
        Hex color code string
    """
    if ensemble == ENSEMBLE_BIGBAND:
        colors = BIGBAND_COLORS
        unknown_family = BIGBAND_UNKNOWN
    else:  # Default to orchestra
        colors = ORCHESTRA_COLORS
        unknown_family = ORCHESTRA_UNKNOWN
    
    return colors.get(family, colors[unknown_family])


def get_individual_color(index: int) -> str:
    """
    Get a color for an individual instrument by index, cycling the palette.
    
    Args:
        index: Non-negative instrument index used for color assignment
    
    Returns:
        Hex color code string
    """
    if index < 0:
        raise ValueError("Color index must be non-negative")
    return INDIVIDUAL_COLOR_PALETTE[index % len(INDIVIDUAL_COLOR_PALETTE)]
