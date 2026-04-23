# fast_analyzer.py

from . import MIDI
import collections
import math
import heapq
from typing import Any, Dict, List, Optional, Tuple, Set

# ---------------------------------------------------------------------------
# ─── BASIC LOOK-UP TABLES ─────────────────────────────────────────────────
# ---------------------------------------------------------------------------

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

MAJOR_KEY_MAP = {0:"C", 1:"G", 2:"D", 3:"A", 4:"E", 5:"B", 6:"F#",
                 -1:"F", -2:"Bb", -3:"Eb", -4:"Ab", -5:"Db", -6:"Gb"}
MINOR_KEY_MAP = {0:"A", 1:"E", 2:"B", 3:"F#", 4:"C#", 5:"G#", 6:"D#",
                 -1:"D", -2:"G", -3:"C", -4:"F", -5:"Bb", -6:"Eb"}

MOOD_TOKENS = {"Dark": 0, "Melancholic": 1, "Neutral": 2,
               "Uplifting": 3, "Energetic": 4, "Tense": 5, "Peaceful": 6,
               "Dramatic": 7, "Playful": 8, "Somber": 9, "Triumphant": 10,
               "Mysterious": 11, "Romantic": 12, "Aggressive": 13, "Happy": 14}

GENRE_TOKENS = {
    # Classical/Academic
    "Unknown": 0, "Solo Piano": 1, "Classical": 2, "Orchestral": 3,
    "Chamber Music": 4, "Baroque": 5, "Romantic": 6, "Impressionist": 7,
    "Minimalist": 8, "Choral": 9, "Opera": 10, "Ballet": 11,
    # Jazz
    "Jazz": 12, "Swing": 13, "Bebop": 14, "Smooth Jazz": 15, "Latin Jazz": 16,
    "Cool Jazz": 17, "Fusion": 18, "Dixieland": 19,
    # Blues
    "Blues": 20, "Delta Blues": 21, "Chicago Blues": 22,
    # Rock/Pop
    "Rock": 23, "Pop": 24, "Metal": 25, "Punk": 26, "Indie": 27,
    "Alternative": 28, "Grunge": 29, "Progressive Rock": 30,
    "Surf Rock": 31, "Psychedelic": 32, "Shoegaze": 33,
    # Electronic
    "Electronic": 34, "Ambient": 35, "Techno": 36, "House": 37,
    "Trance": 38, "Drum and Bass": 39, "Dubstep": 40, "Synthwave": 41,
    "IDM": 42, "Downtempo": 43, "Lo-Fi": 44, "Garage": 45, "Hardcore": 46,
    # R&B/Soul/Funk
    "R&B": 47, "Soul": 48, "Funk": 49, "Neo-Soul": 50, "Disco": 51,
    "Motown": 52,
    # Folk/Country
    "Folk": 53, "Country": 54, "Bluegrass": 55, "Celtic": 56,
    "Americana": 57, "Singer-Songwriter": 58,
    # Latin
    "Latin": 59, "Salsa": 60, "Bossa Nova": 61, "Tango": 62,
    "Reggaeton": 63, "Samba": 64, "Merengue": 65, "Cumbia": 66,
    # World
    "World": 67, "African": 68, "Middle Eastern": 69, "Asian": 70,
    "Caribbean": 71, "Flamenco": 72,
    # Other
    "Cinematic": 73, "New Age": 74, "Gospel": 75, "March": 76,
    "Waltz": 77, "Ragtime": 78, "Hip Hop": 79, "Reggae": 80,
    "Ska": 81, "Polka": 82, "Hymn": 83, "Show Tune": 84,
    "Holiday": 85, "Video Game": 86,
}

CHORD_TEMPLATES = {
    "maj": [0, 4, 7], "min": [0, 3, 7], "dim": [0, 3, 6],
    "aug": [0, 4, 8], "sus2": [0, 2, 7], "sus4": [0, 5, 7],
    "maj7": [0, 4, 7, 11], "min7": [0, 3, 7, 10], "dom7": [0, 4, 7, 10],
    "dim7": [0, 3, 6, 9], "hdim7": [0, 3, 6, 10],
    "maj9": [0, 4, 7, 11, 14], "min9": [0, 3, 7, 10, 14],
    "dom9": [0, 4, 7, 10, 14], "add9": [0, 4, 7, 14],
    "6": [0, 4, 7, 9], "min6": [0, 3, 7, 9],
}

# Numeric mapping for chord qualities
CHORD_QUALITY_MAP = {
    "maj": 0, "min": 1, "dim": 2, "aug": 3, "sus2": 4, "sus4": 5,
    "maj7": 6, "min7": 7, "dom7": 8, "dim7": 9, "hdim7": 10,
    "maj9": 11, "min9": 12, "dom9": 13, "add9": 14, "6": 15, "min6": 16
}

SONG_TYPE_LABELS = {
    0: "Homophonic", 1: "Melody and accompaniment", 2: "Polyphonic",
    3: "Drums only", 4: "Bass and drums", 5: "Solo instrument",
    6: "Solo piano", 7: "Chamber ensemble", 8: "Full ensemble",
}

ELEMENT_MAP = {
    "arpeggio": 0, "trill": 1, "grace_note": 2, "glissando": 3,
    "tremolo": 4, "ostinato": 5, "syncopation": 6, "run": 7, "mordent": 8,
}

NUM_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 
             5: "five", 6: "six", 7: "seven", 8: "eight",
             9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
             13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen"}

# GM Patch ranges for instrument families
PATCH_RANGES = {
    'piano': range(0, 8),
    'chromatic_perc': range(8, 16),
    'organ': range(16, 24),
    'guitar': range(24, 32),
    'bass': range(32, 40),
    'strings': range(40, 48),
    'ensemble': range(48, 56),
    'brass': range(56, 64),
    'reed': range(64, 72),
    'pipe': range(72, 80),
    'synth_lead': range(80, 88),
    'synth_pad': range(88, 96),
    'synth_fx': range(96, 104),
    'ethnic': range(104, 112),
    'percussive': range(112, 120),
    'sfx': range(120, 128),
}

# Specific patches of interest
ACOUSTIC_PIANO_PATCHES = {0, 1, 2}
ELECTRIC_PIANO_PATCHES = {4, 5}
HARPSICHORD_PATCHES = {6}
ORGAN_PATCHES = {16, 17, 18, 19, 20, 21, 22, 23}
ACOUSTIC_GUITAR_PATCHES = {24, 25, 26, 29, 30, 31}
ELECTRIC_GUITAR_PATCHES = {27, 28, 29, 30, 31}
DISTORTED_GUITAR_PATCHES = {29, 30}
ACOUSTIC_BASS_PATCHES = {32, 33}
ELECTRIC_BASS_PATCHES = {34, 35, 36, 37, 38, 39}
VIOLIN_FAMILY = {40, 41, 42, 43, 44}
CELLO_BASS_STRINGS = {44, 45}
CHOIR_PATCHES = {52, 53, 54}
BRASS_SECTION = {56, 57, 60, 61}
SAXOPHONE_PATCHES = {64, 65, 66, 67}
FLUTE_PATCHES = {72, 73}
SYNTH_BASS = {38, 39}

# ---------------------------------------------------------------------------
# ─── PERCUSSION GROUPS AND DRUM SETS ──────────────────────────────────────
# ---------------------------------------------------------------------------

PERCUSSION_GROUPS = MIDI.PERCUSSION_GROUPS

PERCUSSION_GROUP_NAMES = {
    1: "Bass Drums",
    2: "Stick",
    3: "Snares",
    4: "Claps",
    5: "Floor Toms",
    6: "Hi-Hats",
    7: "Toms",
    8: "Cymbals",
    9: "Bells",
    10: "Tambourine",
    11: "Cowbell",
    12: "Vibraslap",
    13: "Bongos",
    14: "Congas",
    15: "Timbales",
    16: "Agogô",
    17: "Cabasa",
    18: "Maracas",
    19: "Whistles",
    20: "Guiros",
    21: "Claves",
    22: "Wood Blocks",
    23: "Cuica",
    24: "Triangles",
}

DRUMS_SETS = MIDI.DRUMS_SETS

# Build reverse lookup for drum notes -> group
_DRUM_NOTE_TO_GROUP: Dict[int, Tuple[int, str, str]] = {}
for _gid, _notes in PERCUSSION_GROUPS.items():
    for _note, _name in _notes.items():
        _DRUM_NOTE_TO_GROUP[_note] = (_gid, PERCUSSION_GROUP_NAMES[_gid], _name)

_KK_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19,
             2.39, 3.66, 2.29, 2.88]
_KK_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75,
             3.98, 2.69, 3.34, 3.17]

# Maximum notes per channel before skipping detailed element detection
MAX_NOTES_FOR_ELEMENT_DETECTION = 50000

# ---------------------------------------------------------------------------
# ─── PURE PYTHON STATISTICS HELPERS ───────────────────────────────────────
# ---------------------------------------------------------------------------

def _mean(lst: List[float]) -> float:
    return sum(lst) / len(lst) if lst else 0.0


def _std(lst: List[float]) -> float:
    if len(lst) < 2:
        return 0.0
    m = _mean(lst)
    return (sum((x - m) ** 2 for x in lst) / (len(lst) - 1)) ** 0.5


def _median(lst: List[float]) -> float:
    if not lst:
        return 0.0
    s = sorted(lst)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return s[n // 2]


def _corrcoef(x: List[float], y: List[float]) -> float:
    """Pure Python Pearson correlation coefficient."""
    n = len(x)
    if n < 2:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / (n - 1)
    std_x = (sum((xi - mean_x) ** 2 for xi in x) / (n - 1)) ** 0.5
    std_y = (sum((yi - mean_y) ** 2 for yi in y) / (n - 1)) ** 0.5
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)

# ---------------------------------------------------------------------------
# ─── NUMBER-TO-WORDS CONVERSION HELPERS ────────────────────────────────────
# ---------------------------------------------------------------------------

def _count_to_words(count: int) -> str:
    """Convert a count to human-readable words (e.g., 'once', 'twice', 'three times')."""
    if count == 0:
        return "never"
    if count == 1:
        return "once"
    if count == 2:
        return "twice"
    
    number_words = {
        3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
        8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
        13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
        17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty",
        21: "twenty-one", 22: "twenty-two", 23: "twenty-three",
        24: "twenty-four", 25: "twenty-five", 26: "twenty-six",
        27: "twenty-seven", 28: "twenty-eight", 29: "twenty-nine",
        30: "thirty", 31: "thirty-one", 32: "thirty-two",
        33: "thirty-three", 34: "thirty-four", 35: "thirty-five",
        36: "thirty-six", 37: "thirty-seven", 38: "thirty-eight",
        39: "thirty-nine", 40: "forty", 41: "forty-one",
        42: "forty-two", 43: "forty-three", 44: "forty-four",
        45: "forty-five", 46: "forty-six", 47: "forty-seven",
        48: "forty-eight", 49: "forty-nine", 50: "fifty",
        51: "fifty-one", 52: "fifty-two", 53: "fifty-three",
        54: "fifty-four", 55: "fifty-five", 56: "fifty-six",
        57: "fifty-seven", 58: "fifty-eight", 59: "fifty-nine",
        60: "sixty", 61: "sixty-one", 62: "sixty-two",
        63: "sixty-three", 64: "sixty-four", 65: "sixty-five",
        66: "sixty-six", 67: "sixty-seven", 68: "sixty-eight",
        69: "sixty-nine", 70: "seventy", 71: "seventy-one",
        72: "seventy-two", 73: "seventy-three", 74: "seventy-four",
        75: "seventy-five", 76: "seventy-six", 77: "seventy-seven",
        78: "seventy-eight", 79: "seventy-nine", 80: "eighty",
        81: "eighty-one", 82: "eighty-two", 83: "eighty-three",
        84: "eighty-four", 85: "eighty-five", 86: "eighty-six",
        87: "eighty-seven", 88: "eighty-eight", 89: "eighty-nine",
        90: "ninety", 91: "ninety-one", 92: "ninety-two",
        93: "ninety-three", 94: "ninety-four", 95: "ninety-five",
        96: "ninety-six", 97: "ninety-seven", 98: "ninety-eight",
        99: "ninety-nine", 100: "one hundred",
        101: "one hundred one", 102: "one hundred two",
        103: "one hundred three", 104: "one hundred four",
        105: "one hundred five", 106: "one hundred six",
        107: "one hundred seven", 108: "one hundred eight",
        109: "one hundred nine", 110: "one hundred ten",
        111: "one hundred eleven", 112: "one hundred twelve",
        113: "one hundred thirteen", 114: "one hundred fourteen",
        115: "one hundred fifteen", 116: "one hundred sixteen",
        117: "one hundred seventeen", 118: "one hundred eighteen",
        119: "one hundred nineteen", 120: "one hundred twenty",
        121: "one hundred twenty-one", 122: "one hundred twenty-two",
        123: "one hundred twenty-three", 124: "one hundred twenty-four",
        125: "one hundred twenty-five", 126: "one hundred twenty-six",
        127: "one hundred twenty-seven", 128: "one hundred twenty-eight"
    }

    if count in number_words:
        return f"{number_words[count]} times"
    
    return "more than sixteen"


def _percentage_to_words(pct: float) -> str:
    """Convert percentage to human-readable words."""
    if pct <= 0:
        return "none"
    if pct >= 99.9:
        return "all"
    if abs(pct - 50) < 3:
        return "half"
    if abs(pct - 25) < 2:
        return "quarter"
    if abs(pct - 75) < 2:
        return "three quarters"
    if abs(pct - 33) < 2:
        return "third"
    if abs(pct - 66) < 2:
        return "two thirds"
    if pct < 2:
        return "negligible"
    if pct < 5:
        return "tiny fraction"
    if pct < 10:
        return "small portion"
    if pct < 20:
        return "minority"
    if pct < 30:
        return "less than third"
    if pct < 40:
        return "about third"
    if pct < 60:
        return "about half"
    if pct < 70:
        return "about two thirds"
    if pct < 80:
        return "majority"
    if pct < 90:
        return "most"
    if pct < 95:
        return "nearly all"
    return "almost all"


def _beats_to_words(beats: float) -> str:
    """Convert beat duration to human-readable words."""
    if beats < 0.125:
        return "very brief"
    if beats < 0.25:
        return "thirty-second note length"
    if beats < 0.5:
        return "sixteenth note length"
    if beats < 1.0:
        return "eighth note length"
    if beats < 2.0:
        return "quarter note length"
    if beats < 4.0:
        return "half note length"
    if beats < 8.0:
        return "whole note length"
    if beats < 16.0:
        return "double whole note length"
    return "very long"


def _note_count_to_words(count: int) -> str:
    """Convert instrument note count to human-readable words."""
    if count < 3:
        return "sparse notes"
    if count < 8:
        return "few notes"
    if count < 20:
        return "several notes"
    if count < 50:
        return "many notes"
    if count < 100:
        return "numerous notes"
    return "abundant notes"


def _melody_length_to_words(count: int) -> str:
    """Convert melody note count to human-readable length description."""
    if count < 5:
        return "brief melody"
    if count < 15:
        return "short melody"
    if count < 30:
        return "moderate melody"
    if count < 60:
        return "substantial melody"
    if count < 100:
        return "long melody"
    return "extensive melody"


def _hit_count_to_words(count: int) -> str:
    """Convert drum hit count to human-readable words."""
    if count < 3:
        return "sparse hits"
    if count < 8:
        return "few hits"
    if count < 20:
        return "several hits"
    if count < 50:
        return "many hits"
    if count < 100:
        return "numerous hits"
    return "abundant hits"


def _duration_to_words(minutes: float) -> str:
    """Convert duration in minutes to human-readable words."""
    if minutes < 0.25:
        return "a few seconds"
    if minutes < 0.5:
        return "under half a minute"
    if minutes < 0.75:
        return "about half a minute"
    if minutes < 1:
        return "under a minute"
    if minutes < 1.5:
        return "about a minute"
    if minutes < 2:
        return "over a minute"
    if minutes < 2.5:
        return "about two minutes"
    if minutes < 3:
        return "two and a half minutes"
    if minutes < 3.5:
        return "about three minutes"
    if minutes < 4:
        return "three and a half minutes"
    if minutes < 5:
        return "about four minutes"
    if minutes < 6:
        return "four and a half minutes"
    if minutes < 7:
        return "about five minutes"
    if minutes < 8:
        return "about six minutes"
    if minutes < 10:
        return "about seven minutes"
    if minutes < 15:
        return "about ten minutes"
    return "over ten minutes"


def _time_sig_to_words(num: int, den: int) -> str:
    """Convert time signature to words."""
    if num == 4 and den == 4:
        return "common time"
    if num == 2 and den == 2:
        return "cut time"
    if num == 3 and den == 4:
        return "waltz time"
    if num == 6 and den == 8:
        return "compound duple"
    
    num_words = {1: "one", 2: "two", 3: "three", 4: "four", 
                 5: "five", 6: "six", 7: "seven", 8: "eight",
                 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
                 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen"}
    den_words = {2: "two", 4: "four", 8: "eight", 16: "sixteen"}
    
    num_str = num_words.get(num, str(num))
    den_str = den_words.get(den, str(den))
    return f"{num_str} {den_str}"


def _track_count_to_words(count: int) -> str:
    """Convert track count to human-readable words."""
    if count == 1:
        return "single track"
    if count < 4:
        return "few tracks"
    if count < 8:
        return "several tracks"
    if count < 16:
        return "many tracks"
    return "numerous tracks"


def _channel_count_to_words(count: int) -> str:
    """Convert channel count to human-readable words."""
    if count == 1:
        return "single channel"
    if count < 4:
        return "few channels"
    if count < 8:
        return "several channels"
    if count < 12:
        return "many channels"
    return "numerous channels"


def _melody_count_to_words(count: int) -> str:
    """Convert number of melodies found to words."""
    if count == 0:
        return "none"
    if count == 1:
        return "one"
    if count == 2:
        return "two"
    if count == 3:
        return "three"
    if count < 6:
        return "several"
    return "many"


def _group_count_to_words(count: int) -> str:
    """Convert number of drum groups to words."""
    if count == 0:
        return "none"
    if count == 1:
        return "one group"
    if count == 2:
        return "two groups"
    if count == 3:
        return "three groups"
    if count < 6:
        return f"{count} groups"
    return "many groups"


def _drum_set_to_words(set_num: int) -> str:
    """Convert drum set number to descriptive words."""
    set_name = DRUMS_SETS.get(set_num, "unknown")
    if set_name == "Standard":
        return "standard drum set"
    if set_name == "Room":
        return "room drum set"
    if set_name == "Power":
        return "power drum set"
    if set_name == "Electronic":
        return "electronic drum set"
    if set_name == "Analog":
        return "analog drum set"
    if set_name == "Jazz":
        return "jazz drum set"
    if set_name == "Brush":
        return "brush drum set"
    if set_name == "Orchestra":
        return "orchestra drum set"
    if set_name == "SFX":
        return "sound effects drum set"
    return f"{set_name.lower()} drum set"


def _dominance_to_words(pct: float) -> str:
    """Convert dominance percentage to descriptive words."""
    if pct >= 80:
        return "overwhelmingly dominant"
    if pct >= 60:
        return "strongly dominant"
    if pct >= 45:
        return "dominant"
    if pct >= 30:
        return "moderately prominent"
    if pct >= 20:
        return "somewhat prominent"
    if pct >= 10:
        return "slightly prominent"
    return "minimally present"


def _count_in_beats_to_words(beats: float) -> str:
    """Convert count-in duration in beats to descriptive words."""
    if beats <= 0.75:
        return "one beat count-in"
    if beats <= 1.5:
        return "two beat count-in"
    if beats <= 2.5:
        return "three beat count-in"
    if beats <= 3.5:
        return "four beat count-in"
    if beats <= 5.5:
        return "six beat count-in"
    if beats <= 7.5:
        return "eight beat count-in"
    rounded = int(round(beats))
    word = NUM_WORDS.get(rounded, str(rounded))
    return f"{word} beat count-in"


def _chord_count_to_words(count: int) -> str:
    """Convert chord count to human-readable words."""
    if count == 0:
        return "no chords"
    if count < 4:
        return "few chords"
    if count < 10:
        return "several chords"
    if count < 25:
        return "many chords"
    if count < 50:
        return "numerous chords"
    return "abundant chords"


def _notes_chords_ratio_to_words(ratio: float) -> str:
    """Convert notes-chords ratio to descriptive words."""
    if ratio == float('inf') or ratio > 1000:
        return "no chords"
    if ratio < 2.5:
        return "sparse chords"
    if ratio < 4:
        return "simple chords"
    if ratio < 6:
        return "moderate chords"
    if ratio < 10:
        return "rich chords"
    return "dense chords"


def _composition_dominance_to_words(chord_dominance_pct: float) -> str:
    """Convert chord dominance percentage to composition type words."""
    if chord_dominance_pct >= 50:
        return "chords"
    return "notes"

# ---------------------------------------------------------------------------
# ─── OTHER HELPERS ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _patch_name(patch: int) -> str:
    return MIDI.Number2patch.get(patch, f"patch_{patch}").lower()


def _drum_name(note: int) -> str:
    return MIDI.Notenum2percussion.get(note, f"drum_{note}").lower()


def _get_drum_group(note: int) -> Tuple[int, str, str]:
    """
    Get drum group information for a note number.
    Returns (group_id, group_name, drum_name).
    """
    return _DRUM_NOTE_TO_GROUP.get(note, (0, "other", MIDI.Notenum2percussion.get(note, f"drum_{note}")))


def _get_drum_set_name(patch: int) -> str:
    """Get the drum set name from a patch number on channel 10."""
    return DRUMS_SETS.get(patch, "standard").lower()


def _instrument_family(patch: int) -> str:
    family_id = patch // 8 if 0 <= patch <= 127 else -1
    return MIDI.MIDI_Instruments_Families.get(family_id, "unknown family").lower()


def _note_to_name(note: int) -> str:
    return NOTE_NAMES[note % 12].lower() + str(note // 12 - 1)


def _profile_chroma(note_list: List[int]) -> List[float]:
    chroma = [0.0] * 12
    for n in note_list:
        chroma[n % 12] += 1
    s = sum(chroma)
    return [c / s for c in chroma] if s > 0 else chroma


def _detect_key_krumhansl(notes: List[int]) -> Tuple[int, int]:
    if not notes:
        return 0, 0
    chroma = _profile_chroma(notes)
    best_key, best_mode, best_corr = 0, 0, -999.0
    for root in range(12):
        rolled = chroma[root:] + chroma[:root]
        for mode, profile in enumerate([_KK_MAJOR, _KK_MINOR]):
            corr = _corrcoef(rolled, profile)
            if corr > best_corr:
                best_corr, best_key, best_mode = corr, root, mode
    return best_key, best_mode


def _name_chord(pcs: set) -> Optional[str]:
    if len(pcs) < 2:
        return None
    # Try to match exact chord first
    for root in range(12):
        for quality, intervals in CHORD_TEMPLATES.items():
            template = set((root + i) % 12 for i in intervals)
            if template == pcs:
                return f"{NOTE_NAMES[root].lower()}{quality}"
    # Then try subset matching (for chords with extensions)
    for root in range(12):
        for quality, intervals in CHORD_TEMPLATES.items():
            template = set((root + i) % 12 for i in intervals)
            if template.issubset(pcs) and len(template) >= 3:
                return f"{NOTE_NAMES[root].lower()}{quality}"
    return None


def _detect_chords(notes_with_times: List[Tuple[int, int, int, int]],
                   ticks_per_beat: int) -> List[str]:
    """Detect chords with adaptive window sizing to prevent memory issues."""
    if not notes_with_times:
        return []
    
    # Calculate actual span of note starts
    min_tick = min(st for st, _, _, _ in notes_with_times)
    max_tick = max(st for st, _, _, _ in notes_with_times)
    total_span = max_tick - min_tick + 1
    
    # Use ticks_per_beat as base window, but ensure we don't create too many buckets
    # Target: 500-5000 buckets maximum for reasonable performance
    TARGET_MAX_BUCKETS = 3000
    window = max(ticks_per_beat, total_span // TARGET_MAX_BUCKETS + 1)
    
    buckets: Dict[int, List[int]] = collections.defaultdict(list)
    for (st, dur, ch, pitch) in notes_with_times:
        buckets[st // window].append(pitch % 12)
    
    chord_sequence = []
    for bid in sorted(buckets.keys()):
        pcs = set(buckets[bid])
        name = _name_chord(pcs)
        if name and (not chord_sequence or chord_sequence[-1] != name):
            chord_sequence.append(name)
    
    return chord_sequence


def _detect_chord_progressions(chord_sequence: List[str],
                                min_length: int = 3,
                                max_length: int = 5,
                                top_n: int = 8) -> List[Tuple[str, int]]:
    """
    Detect most common chord progressions of various lengths.
    Limits analysis to prevent excessive computation on long sequences.
    """
    if len(chord_sequence) < min_length:
        return []
    
    # Limit sequence length to prevent O(n²) behavior on very long songs
    MAX_CHORDS_FOR_ANALYSIS = 500
    if len(chord_sequence) > MAX_CHORDS_FOR_ANALYSIS:
        chord_sequence = chord_sequence[:MAX_CHORDS_FOR_ANALYSIS]
    
    progression_counts: Dict[str, int] = {}
    
    for length in range(min_length, min(max_length + 1, len(chord_sequence) + 1)):
        for i in range(len(chord_sequence) - length + 1):
            progression = " -> ".join(chord_sequence[i:i + length])
            progression_counts[progression] = progression_counts.get(progression, 0) + 1
    
    # Use heap for efficient top-n
    if len(progression_counts) <= top_n:
        return list(progression_counts.items())
    
    return heapq.nlargest(top_n, progression_counts.items(), key=lambda x: x[1])


def _chord_name_to_numeric(chord_name: str) -> tuple:
    """
    Convert chord name like 'cmaj' to numeric tuple like (0, 0).
    Returns (root,) for single notes, (root, quality) for chords.
    """
    root_map = {"c": 0, "c#": 1, "db": 1, "d": 2, "d#": 3, "eb": 3,
                "e": 4, "f": 5, "f#": 6, "gb": 6, "g": 7, "g#": 8, "ab": 8,
                "a": 9, "a#": 10, "bb": 10, "b": 11}
    
    if not chord_name:
        return ()
    
    chord_lower = chord_name.lower()
    
    # Find root (1-2 characters for sharp/flat)
    if len(chord_lower) >= 2 and chord_lower[1] in ('#', 'b'):
        root_str = chord_lower[:2]
        quality_str = chord_lower[2:]
    else:
        root_str = chord_lower[0]
        quality_str = chord_lower[1:]
    
    root = root_map.get(root_str, 0)
    
    if not quality_str:
        return (root,)
    
    quality = CHORD_QUALITY_MAP.get(quality_str, 0)
    return (root, quality)


def _progression_to_numeric(progression_str: str) -> tuple:
    """
    Convert progression string like 'cmaj -> fmin -> gmaj' to tuple of tuples.
    Example: ((0, 0), (5, 1), (7, 0))
    """
    chords = [c.strip() for c in progression_str.split("->")]
    return tuple(_chord_name_to_numeric(c) for c in chords)


def _count_chords_from_score(all_notes: List[Tuple[int, int, int, int]], 
                              ticks_per_beat: int) -> Dict[str, Any]:
    """
    Count chord events directly from the score.
    A chord is detected when 2+ notes start within 1/8th note window.
    Returns dict with chord_count, total_notes, notes_chords_ratio, 
    chord_dominance_pct for determining composition type.
    """
    if not all_notes:
        return {"chord_count": 0, "total_notes": 0, "notes_chords_ratio": 0.0, 
                "chord_dominance_pct": 0.0}
    
    # Sort by start time, then by pitch
    sorted_notes = sorted(all_notes, key=lambda x: (x[0], x[3]))
    
    # Group notes that start within 1/8th note of each other as potential chord
    window = max(ticks_per_beat // 2, 1)
    chord_count = 0
    i = 0
    n = len(sorted_notes)
    
    while i < n:
        j = i + 1
        while j < n and sorted_notes[j][0] - sorted_notes[i][0] <= window:
            j += 1
        
        # Check if this group has 2+ notes starting close together
        group_size = j - i
        if group_size >= 2:
            chord_count += 1
        
        i = j
    
    total_notes = len(all_notes)
    notes_chords_ratio = total_notes / chord_count if chord_count > 0 else float('inf')
    
    # Calculate tick-based chord dominance using sweep line
    events = []
    for st, dur, ch, pitch in all_notes:
        if dur > 0:
            events.append((st, 1))
            events.append((st + dur, -1))
    events.sort(key=lambda x: (x[0], x[1]))
    
    if not events:
        return {"chord_count": chord_count, "total_notes": total_notes, 
                "notes_chords_ratio": notes_chords_ratio if notes_chords_ratio != float('inf') else 0.0, 
                "chord_dominance_pct": 0.0}
    
    chord_ticks = 0
    single_ticks = 0
    prev_time = events[0][0]
    active = 0
    
    for time, delta in events:
        if time > prev_time:
            duration = time - prev_time
            if active >= 2:
                chord_ticks += duration
            elif active == 1:
                single_ticks += duration
        active += delta
        prev_time = time
    
    total_ticks = chord_ticks + single_ticks
    chord_dominance_pct = (chord_ticks / total_ticks * 100) if total_ticks > 0 else 0.0
    
    # Clamp infinite ratio to 0 for output
    final_ratio = notes_chords_ratio if notes_chords_ratio != float('inf') else 0.0
    
    return {
        "chord_count": chord_count,
        "total_notes": total_notes,
        "notes_chords_ratio": round(final_ratio, 2),
        "chord_dominance_pct": round(chord_dominance_pct, 2)
    }


def _get_instrument_flags(patches: List[int]) -> Dict[str, bool]:
    """Detect which instrument families are present."""
    flags = {
        'piano': False,
        'chromatic_perc': False,
        'organ': False,
        'guitar': False,
        'bass': False,
        'strings': False,
        'ensemble': False,
        'brass': False,
        'reed': False,
        'pipe': False,
        'synth_lead': False,
        'synth_pad': False,
        'synth_fx': False,
        'synth': False,
        'ethnic': False,
        'percussive': False,
        'sfx': False,
        'choir': False,
        # Specific subsets
        'acoustic_piano': False,
        'electric_piano': False,
        'harpsichord': False,
        'acoustic_guitar': False,
        'electric_guitar': False,
        'distorted_guitar': False,
        'acoustic_bass': False,
        'electric_bass': False,
        'violin_family': False,
        'saxophone': False,
        'flute': False,
        # Derived
        'has_orchestral': False,
        'piano_only': False,
        'acoustic_only': False,
        'has_drums': False,  # Will be set separately
    }
    
    for p in patches:
        for family, patch_range in PATCH_RANGES.items():
            if p in patch_range:
                flags[family] = True
                break
        
        # Specific patches
        if p in ACOUSTIC_PIANO_PATCHES:
            flags['acoustic_piano'] = True
        if p in ELECTRIC_PIANO_PATCHES:
            flags['electric_piano'] = True
        if p in HARPSICHORD_PATCHES:
            flags['harpsichord'] = True
        if p in ACOUSTIC_GUITAR_PATCHES:
            flags['acoustic_guitar'] = True
        if p in ELECTRIC_GUITAR_PATCHES:
            flags['electric_guitar'] = True
        if p in DISTORTED_GUITAR_PATCHES:
            flags['distorted_guitar'] = True
        if p in ACOUSTIC_BASS_PATCHES:
            flags['acoustic_bass'] = True
        if p in ELECTRIC_BASS_PATCHES:
            flags['electric_bass'] = True
        if p in VIOLIN_FAMILY:
            flags['violin_family'] = True
        if p in SAXOPHONE_PATCHES:
            flags['saxophone'] = True
        if p in FLUTE_PATCHES:
            flags['flute'] = True
        if p in CHOIR_PATCHES:
            flags['choir'] = True
    
    # Derived flags
    flags['synth'] = flags['synth_lead'] or flags['synth_pad'] or flags['synth_fx']
    flags['has_orchestral'] = (flags['strings'] or flags['brass'] or 
                               flags['reed'] or flags['pipe'])
    
    # Piano only: has piano, no other melodic instruments
    non_piano_melodic = (flags['strings'] or flags['brass'] or flags['reed'] or 
                         flags['pipe'] or flags['guitar'] or flags['organ'] or 
                         flags['ethnic'] or flags['choir'] or flags['synth'])
    flags['piano_only'] = flags['piano'] and not non_piano_melodic
    
    # Acoustic only: no synth
    flags['acoustic_only'] = not flags['synth']
    
    return flags


# ---------------------------------------------------------------------------
# ─── PATCH TIMELINE ────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _build_patch_timelines(tracks: List) -> Dict[int, List[Tuple[int, int]]]:
    """Build timeline of patch changes per channel. O(events)."""
    timelines: Dict[int, List[Tuple[int, int]]] = collections.defaultdict(list)
    for track in tracks:
        for event in track:
            if event[0] == 'patch_change':
                _, tick, ch, patch = event
                timelines[ch].append((tick, patch))
    for ch in timelines:
        timelines[ch].sort(key=lambda x: x[0])
    return timelines


def _get_patch_at_tick(timeline: List[Tuple[int, int]], tick: int) -> int:
    """Binary search for active patch at tick. O(log n)."""
    if not timeline:
        return 0
    lo, hi = 0, len(timeline) - 1
    result = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if timeline[mid][0] <= tick:
            result = timeline[mid][1]
            lo = mid + 1
        else:
            hi = mid - 1
    return result


# ---------------------------------------------------------------------------
# ─── FAST MONOPHONIC DETECTION ────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _calc_mono_stats(notes: List[Tuple[int, int, int]]) -> Dict[str, Any]:
    """
    Fast monophonic stats using sweep line. O(n log n).
    """
    if not notes:
        return {"chord_pct": 0.0, "overlap_pct": 0.0, "valid_note_count": 0, "overlap_count": 0}
    
    intervals = []
    for s, d, _ in notes:
        if d > 0:
            intervals.append((s, s + d))
    
    n = len(intervals)
    if n < 2:
        return {"chord_pct": 0.0, "overlap_pct": 0.0, "valid_note_count": n, "overlap_count": 0}
    
    intervals.sort()
    
    # Sequential overlap (legato bleeding)
    overlap_count = 0
    for i in range(n - 1):
        if intervals[i + 1][0] < intervals[i][1]:
            overlap_count += 1
    overlap_pct = (overlap_count / (n - 1)) * 100.0
    
    # Chord detection via sweep line
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))
    events.sort(key=lambda x: (x[0], x[1]))
    
    chord_ticks = 0
    prev_time = events[0][0]
    active = 0
    
    for time, delta in events:
        if time > prev_time and active >= 2:
            chord_ticks += time - prev_time
        active += delta
        prev_time = time
    
    total_span = intervals[-1][1] - intervals[0][0]
    chord_pct = (chord_ticks / total_span * 100.0) if total_span > 0 else 0.0
    
    return {
        "chord_pct": chord_pct,
        "overlap_pct": overlap_pct,
        "valid_note_count": n,
        "overlap_count": overlap_count,
    }


def _get_monophonic_melodies(
    patch_notes: Dict[Tuple[int, int], List[Tuple[int, int, int]]],
    ticks_per_beat: int,
    max_tick: int,
    chord_threshold_pct: float = 1.0,
    overlap_threshold_pct: float = 1.0
) -> List[Dict[str, Any]]:
    """Find monophonic melodies with safeguards for corrupted data."""
    
    # Sanity check on ticks_per_beat
    if ticks_per_beat <= 0:
        ticks_per_beat = 480  # Reasonable default
    
    melodies = []
    song_beats = max_tick / ticks_per_beat if max_tick > 0 else 1
    
    # Limit to reasonable number of (channel, patch) combinations
    MAX_COMBINATIONS = 200
    combinations = list(patch_notes.items())
    if len(combinations) > MAX_COMBINATIONS:
        # Sort by note count and take top combinations
        combinations.sort(key=lambda x: -len(x[1]))
        combinations = combinations[:MAX_COMBINATIONS]
    
    for (ch, patch), notes in combinations:
        if len(notes) < 3:
            continue
        
        # Skip channels with too many notes
        if len(notes) > MAX_NOTES_FOR_ELEMENT_DETECTION:
            continue
        
        stats = _calc_mono_stats(notes)
        
        if stats["chord_pct"] > chord_threshold_pct:
            continue
        if stats["overlap_pct"] > overlap_threshold_pct:
            continue
        
        valid_notes = [(s, d, p) for s, d, p in notes if d > 0]
        if len(valid_notes) < 3:
            continue
            
        valid_notes.sort(key=lambda x: x[0])
        
        patch_name = MIDI.Number2patch.get(patch, f"unknown_{patch}")
        family_name = _instrument_family(patch).lower()
        
        note_count = len(valid_notes)
        melody_start = valid_notes[0][0]
        melody_end = valid_notes[-1][0] + valid_notes[-1][1]
        melody_beats = (melody_end - melody_start) / ticks_per_beat
        relative_length_pct = (melody_beats / song_beats * 100) if song_beats > 0 else 0
        
        pitches = [n[2] for n in valid_notes]
        note_names = [_note_to_name(p) for p in pitches]
        avg_pitch = sum(pitches) / len(pitches) if pitches else 60
        
        # Categorize as lead or bass
        is_bass_patch = hasattr(MIDI, 'BASE_INSTRUMENTS') and patch in MIDI.BASE_INSTRUMENTS
        is_lead_patch = hasattr(MIDI, 'LEAD_INSTRUMENTS') and patch in MIDI.LEAD_INSTRUMENTS
        
        if is_bass_patch:
            category = "bass"
        elif is_lead_patch:
            category = "bass" if avg_pitch < 48 else "lead"
        else:
            default_octave = MIDI.Patch2octave.get(patch_name, 60) if hasattr(MIDI, 'Patch2octave') else 60
            category = "bass" if avg_pitch < default_octave - 6 else "lead"
        
        melodies.append({
            "channel": ch,
            "instrument_num": patch,
            "instrument_name": patch_name,
            "instrument_family": family_name,
            "category": category,
            "note_count": note_count,
            "relative_length_beats": round(melody_beats, 2),
            "relative_length_pct": round(relative_length_pct, 2),
            "chord_pct": round(stats["chord_pct"], 4),
            "overlap_pct": round(stats["overlap_pct"], 4),
            "melody": note_names,
            "melody_pitches": pitches[:12],
        })
    
    melodies.sort(key=lambda x: (0 if x["category"] == "lead" else 1, -x["note_count"]))
    return melodies


# ---------------------------------------------------------------------------
# ─── ORNAMENT DETECTORS ───────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _count_arpeggios(notes: List[Tuple[int, int, int]], tpb: int) -> int:
    count, i = 0, 0
    n = len(notes)
    if n < 4:
        return 0
    rapid, window = tpb // 4, tpb * 2
    while i < n - 3:
        seg = notes[i:i+4]
        starts = [s[0] for s in seg]
        if starts[-1] - starts[0] <= window:
            gaps = [starts[j+1] - starts[j] for j in range(3)]
            if all(0 < g <= rapid for g in gaps):
                if _name_chord({s[2] % 12 for s in seg}):
                    count += 1
                    i += 4
                    continue
        i += 1
    return count


def _count_trills(notes: List[Tuple[int, int, int]], tpb: int) -> int:
    count, i = 0, 0
    n = len(notes)
    if n < 6:
        return 0
    rapid = tpb // 4
    while i < n - 5:
        seg = notes[i:i+6]
        pitches = [s[2] for s in seg]
        starts = [s[0] for s in seg]
        gaps = [starts[j+1] - starts[j] for j in range(5)]
        if all(0 < g <= rapid for g in gaps):
            interval = abs(pitches[0] - pitches[1])
            if 1 <= interval <= 2 and all(abs(pitches[j] - pitches[j+1]) == interval for j in range(5)):
                count += 1
                i += 6
                continue
        i += 1
    return count


def _count_grace_notes(notes: List[Tuple[int, int, int]], tpb: int) -> int:
    if len(notes) < 2:
        return 0
    grace_dur = tpb // 8
    count = 0
    for i in range(len(notes) - 1):
        dur = notes[i][1]
        gap = notes[i+1][0] - notes[i][0]
        if dur <= grace_dur and gap <= grace_dur and notes[i+1][1] > 4 * dur:
            count += 1
    return count


def _count_glissando(notes: List[Tuple[int, int, int]], tpb: int) -> int:
    count, i = 0, 0
    n = len(notes)
    if n < 5:
        return 0
    rapid = tpb // 3
    while i < n - 4:
        seg = notes[i:i+5]
        pitches = [s[2] for s in seg]
        starts = [s[0] for s in seg]
        gaps = [starts[j+1] - starts[j] for j in range(4)]
        if all(0 < g <= rapid for g in gaps):
            diffs = [pitches[j+1] - pitches[j] for j in range(4)]
            if all(d == 1 for d in diffs) or all(d == -1 for d in diffs):
                count += 1
                i += 5
                continue
        i += 1
    return count


def _count_tremolo(notes: List[Tuple[int, int, int]], tpb: int) -> int:
    count, i = 0, 0
    n = len(notes)
    if n < 4:
        return 0
    rapid = tpb // 4
    while i < n - 3:
        seg = notes[i:i+4]
        if len({s[2] for s in seg}) == 1:
            starts = [s[0] for s in seg]
            if all(0 < starts[j+1] - starts[j] <= rapid for j in range(3)):
                count += 1
                i += 4
                continue
        i += 1
    return count


def _count_ostinato(notes: List[Tuple[int, int, int]], tpb: int) -> int:
    n = len(notes)
    if n < 9:
        return 0
    pitches = [n[2] for n in notes]
    count = 0
    for motif_len in range(3, 6):
        start = 0
        while start <= len(pitches) - motif_len * 3:
            motif = pitches[start:start+motif_len]
            reps, pos = 1, start + motif_len
            while pos + motif_len <= len(pitches):
                if pitches[pos:pos+motif_len] == motif:
                    reps += 1
                    pos += motif_len
                else:
                    break
            if reps >= 3:
                count += 1
                start = pos
            else:
                start += 1
    return count


def _count_syncopation(notes: List[Tuple[int, int, int]], tpb: int, ts_num: int = 4) -> int:
    if not notes:
        return 0
    sub = tpb // 2
    count = 0
    for start, dur, _ in notes:
        phase = start % tpb
        if sub // 2 <= phase <= tpb - sub // 2:
            if dur > tpb - phase:
                count += 1
    return count


def _count_runs(notes: List[Tuple[int, int, int]], tpb: int) -> int:
    """Detect scalar runs (fast consecutive scale passages)."""
    count, i = 0, 0
    n = len(notes)
    if n < 6:
        return 0
    rapid = tpb // 3
    while i < n - 5:
        seg = notes[i:i+6]
        pitches = [s[2] for s in seg]
        starts = [s[0] for s in seg]
        gaps = [starts[j+1] - starts[j] for j in range(5)]
        if all(0 < g <= rapid for g in gaps):
            diffs = [pitches[j+1] - pitches[j] for j in range(5)]
            # All steps are 1 or 2 semitones (scale-like)
            if all(d in (1, 2, -1, -2) for d in diffs):
                count += 1
                i += 6
                continue
        i += 1
    return count


def _count_mordents(notes: List[Tuple[int, int, int]], tpb: int) -> int:
    """Detect mordents (rapid alternation at start of note)."""
    count, i = 0, 0
    n = len(notes)
    if n < 3:
        return 0
    rapid = tpb // 6
    while i < n - 2:
        seg = notes[i:i+3]
        pitches = [s[2] for s in seg]
        starts = [s[0] for s in seg]
        # First two notes are rapid, third note returns to or stays at first pitch
        if starts[1] - starts[0] <= rapid and starts[2] - starts[1] <= rapid:
            if abs(pitches[0] - pitches[1]) in (1, 2):
                if pitches[2] == pitches[0]:
                    count += 1
                    i += 3
                    continue
        i += 1
    return count


# ---------------------------------------------------------------------------
# ─── ELEMENT DETECTION WITH LIMITS ────────────────────────────────────────
# ---------------------------------------------------------------------------

def _detect_elements_for_channel(notes: List[Tuple[int, int, int]], 
                                  tpb: int, 
                                  time_sig_num: int = 4) -> Dict[str, int]:
    """Detect musical elements with safeguard against very large note lists."""
    if len(notes) > MAX_NOTES_FOR_ELEMENT_DETECTION:
        # Too many notes - skip detailed element detection
        # Still do basic syncopation check on a sample
        sample_size = min(10000, len(notes))
        step = len(notes) // sample_size
        sampled = notes[::step]
        return {"syncopation": _count_syncopation(sampled, tpb, time_sig_num)}
    
    sorted_notes = sorted(notes, key=lambda x: x[0])
    
    return {
        "arpeggio": _count_arpeggios(sorted_notes, tpb),
        "trill": _count_trills(sorted_notes, tpb),
        "grace_note": _count_grace_notes(sorted_notes, tpb),
        "glissando": _count_glissando(sorted_notes, tpb),
        "tremolo": _count_tremolo(sorted_notes, tpb),
        "ostinato": _count_ostinato(sorted_notes, tpb),
        "syncopation": _count_syncopation(sorted_notes, tpb, time_sig_num),
        "run": _count_runs(sorted_notes, tpb),
        "mordent": _count_mordents(sorted_notes, tpb),
    }


# ---------------------------------------------------------------------------
# ─── ENHANCED GENRE CLASSIFICATION ────────────────────────────────────────
# ---------------------------------------------------------------------------

def _classify_genre(
    patches: List[int],
    patch_counter: Dict[int, int],
    has_drums: bool,
    tempo: float,
    time_sig_num: int,
    time_sig_den: int,
    polyphony: float,
    note_density: float,
    avg_velocity: float,
    scale: int,
    n_tracks: int,
    n_channels: int,
    song_type_token: int,
    element_counts: Dict[str, int],
    chord_sequence: List[str],
) -> str:
    """
    Enhanced genre classification with solo piano and comprehensive classical detection.
    """
    
    # Get instrument flags
    flags = _get_instrument_flags(patches)
    flags['has_drums'] = has_drums
    
    # Get element counts
    arpeggios = element_counts.get("arpeggio", 0)
    trills = element_counts.get("trill", 0)
    grace_notes = element_counts.get("grace_note", 0)
    glissandos = element_counts.get("glissando", 0)
    runs = element_counts.get("run", 0)
    mordents = element_counts.get("mordent", 0)
    syncopation = element_counts.get("syncopation", 0)
    ostinatos = element_counts.get("ostinato", 0)
    
    # Get dominant instrument
    dominant_patch = patch_counter.most_common(1)[0][0] if patch_counter else 0
    dominant_is_piano = 0 <= dominant_patch <= 7
    dominant_count = patch_counter.most_common(1)[0][1] if patch_counter else 0
    total_notes = sum(patch_counter.values()) if patch_counter else 1
    piano_dominance = patch_counter.get(dominant_patch, 0) / total_notes if dominant_is_piano else 0
    
    # Time signature analysis
    is_waltz_time = (time_sig_num == 3 and time_sig_den in (4, 8))
    is_march_time = (time_sig_num == 2 and time_sig_den == 4)
    is_68_time = (time_sig_num == 6 and time_sig_den == 8)
    
    # Chord analysis for jazz detection
    has_extended_chords = any(c for c in chord_sequence if '7' in c or '9' in c or '6' in c)
    has_diminished = any('dim' in c for c in chord_sequence)
    
    # ================================================================
    # SOLO PIANO DETECTION (highest priority for piano-only pieces)
    # ================================================================
    if flags['piano_only'] and not has_drums:
        # Sub-classify solo piano styles
        if is_waltz_time:
            if tempo > 140:
                return "Waltz"  # Fast waltz (Viennese)
            return "Waltz"
        
        if tempo > 180 and note_density > 6 and syncopation > 3:
            return "Ragtime"
        
        # Impressionist: arpeggios, moderate tempo, often major mode, moderate polyphony
        if arpeggios > 8 and 60 < tempo < 110 and scale == 0 and 2 < polyphony < 5:
            return "Impressionist"
        
        # Baroque: trills, mordents, moderate-fast tempo
        if (trills > 3 or mordents > 3) and tempo < 140:
            if flags['harpsichord']:
                return "Baroque"
            return "Baroque"
        
        # Romantic: high polyphony, wider dynamics, often minor
        if polyphony > 5 and tempo < 120:
            return "Romantic"
        
        # Minimalist: very sparse
        if polyphony < 2 and note_density < 2:
            return "Minimalist"
        
        # Classical era: balanced, moderate everything
        if 80 < tempo < 140 and 2 < polyphony < 5:
            return "Solo Piano"
        
        # Default to Solo Piano
        return "Solo Piano"
    
    # ================================================================
    # CLASSICAL/ACADEMIC MUSIC (with other instruments)
    # ================================================================
    if flags['has_orchestral'] and flags['acoustic_only'] and not has_drums and not flags['guitar']:
        # Choral: choir dominant, minimal other instruments
        if flags['choir'] and not flags['strings'] and not flags['brass']:
            return "Choral"
        
        # Opera: choir + orchestral
        if flags['choir'] and flags['has_orchestral']:
            return "Opera"
        
        # Large orchestral
        if n_tracks >= 10 or n_channels >= 12:
            return "Orchestral"
        
        # Chamber music: small ensemble
        if n_tracks <= 5 and n_channels <= 6:
            return "Chamber Music"
        
        # Baroque characteristics
        if trills > 2 or mordents > 2:
            if flags['harpsichord'] or flags['organ']:
                return "Baroque"
            return "Baroque"
        
        # Romantic characteristics
        if flags['strings'] and flags['piano'] and arpeggios > 3:
            return "Romantic"
        
        # Ballet: moderate-fast tempo, orchestral
        if 90 < tempo < 140 and flags['strings']:
            return "Ballet"
        
        return "Classical"
    
    # Piano + strings/brass with some modern elements but still classical feel
    if flags['piano'] and flags['has_orchestral'] and not has_drums and not flags['guitar']:
        if flags['synth_pad'] or flags['synth_fx']:
            return "Cinematic"
        return "Classical"
    
    # ================================================================
    # JAZZ FAMILY
    # ================================================================
    # Piano-based jazz
    if flags['piano'] and (flags['brass'] or flags['reed']) and not flags['synth_lead']:
        if has_drums:
            if tempo > 170:
                return "Bebop"
            if tempo > 130:
                if has_extended_chords:
                    return "Swing"
                return "Swing"
            if tempo < 100:
                if flags['saxophone'] and not flags['brass']:
                    return "Cool Jazz"
                return "Smooth Jazz"
            return "Jazz"
        # No drums - still jazz (maybe solo jazz piano with horn)
        return "Jazz"
    
    # Guitar-based jazz
    if flags['guitar'] and (flags['brass'] or flags['reed']) and not flags['synth'] and not flags['distorted_guitar']:
        if has_drums:
            return "Jazz"
        return "Jazz"
    
    # Smooth jazz: synth pad + sax
    if flags['synth_pad'] and flags['saxophone'] and not flags['distorted_guitar']:
        return "Smooth Jazz"
    
    # Jazz fusion: mix of jazz and rock/electronic
    if flags['piano'] and flags['has_orchestral'] and (flags['electric_guitar'] or flags['synth']):
        return "Fusion"
    
    # Dixieland: early jazz style
    if flags['brass'] and flags['reed'] and flags['piano'] and has_drums and tempo < 130:
        if n_tracks <= 6:
            return "Dixieland"
    
    # Latin jazz
    if flags['piano'] and flags['percussive'] and has_drums:
        return "Latin Jazz"
    
    # ================================================================
    # BLUES FAMILY
    # ================================================================
    if (flags['guitar'] or flags['piano']) and scale == 1 and has_drums and flags['acoustic_only']:
        if flags['electric_guitar'] or flags['electric_bass']:
            return "Chicago Blues"
        return "Delta Blues"
    
    # ================================================================
    # ELECTRONIC FAMILY
    # ================================================================
    if flags['synth']:
        if not has_drums:
            # Ambient/atmospheric
            if tempo < 80 and polyphony < 4:
                return "Ambient"
            if flags['synth_pad'] and not flags['synth_lead']:
                return "New Age"
            return "Ambient"
        
        # Electronic with drums - classify by tempo
        if tempo > 175:
            return "Drum and Bass"
        if tempo > 160:
            return "Hardcore"
        if tempo > 145:
            return "Techno"
        if tempo > 130:
            if flags['synth_pad'] and not flags['synth_lead']:
                return "Trance"
            return "House"
        if tempo > 120:
            if flags['synth_pad']:
                return "Garage"
            return "House"
        if tempo > 100:
            if flags['synth_lead'] and flags['synth_pad']:
                return "Synthwave"
            return "Electronic"
        if tempo > 80:
            if flags['piano'] and flags['synth_pad']:
                return "Lo-Fi"
            if flags['synth_lead']:
                return "Synthwave"
            return "Downtempo"
        # Slow electronic
        if flags['piano'] and flags['synth_pad']:
            return "Lo-Fi"
        if flags['synth_pad']:
            return "Ambient"
        return "Downtempo"
    
    # ================================================================
    # ROCK/METAL/PUNK FAMILY
    # ================================================================
    if flags['guitar'] and has_drums and flags['acoustic_only']:
        if flags['distorted_guitar']:
            if tempo > 160 and avg_velocity > 100:
                return "Metal"
            if tempo > 150 and avg_velocity > 95:
                return "Punk"
            if tempo > 130:
                return "Rock"
            return "Rock"
        # Clean guitar rock
        if tempo > 130:
            return "Rock"
        if tempo > 100:
            if flags['acoustic_guitar']:
                return "Folk"  # Acoustic guitar with drums
            return "Rock"
        return "Indie"
    
    # Surf rock: clean electric guitar, fast, reverb-like feel
    if flags['electric_guitar'] and not flags['distorted_guitar'] and has_drums and tempo > 130:
        return "Surf Rock"
    
    # Rock with synth elements
    if flags['guitar'] and has_drums and flags['synth']:
        if flags['synth_pad'] and tempo < 110:
            return "Shoegaze"
        if flags['synth_lead']:
            return "Psychedelic"
        if tempo > 140:
            return "Progressive Rock"
        return "Alternative"
    
    # Grunge: distorted guitar, mid-tempo, heavy
    if flags['distorted_guitar'] and has_drums and 100 < tempo < 140:
        return "Grunge"
    
    # Progressive rock: complex, varied instrumentation
    if flags['guitar'] and flags['has_orchestral'] and has_drums:
        return "Progressive Rock"
    
    # ================================================================
    # R&B/SOUL/FUNK/DISCO FAMILY
    # ================================================================
    if flags['piano'] and has_drums and not flags['guitar']:
        if flags['brass'] and tempo > 110:
            return "Funk"
        if flags['reed']:
            if tempo > 100:
                return "Funk"
            return "Soul"
        if tempo > 120:
            return "Disco"
        if tempo < 90:
            return "R&B"
        return "R&B"
    
    # Funk with guitar
    if flags['guitar'] and flags['brass'] and has_drums and tempo > 100:
        if syncopation > 5:
            return "Funk"
    
    # Motown: similar to R&B but specific era/style
    if flags['piano'] and flags['brass'] and has_drums and 100 < tempo < 130:
        return "Motown"
    
    # Neo-soul: modern R&B with jazz influence
    if flags['piano'] and flags['electric_bass'] and has_drums and tempo < 100:
        if has_extended_chords:
            return "Neo-Soul"
    
    # ================================================================
    # FOLK/COUNTRY/CELTIC FAMILY
    # ================================================================
    if flags['guitar'] and not has_drums:
        if flags['ethnic']:
            return "Celtic"
        if flags['organ'] or flags['piano']:
            return "Country"
        if flags['acoustic_guitar']:
            return "Singer-Songwriter"
        return "Folk"
    
    if flags['guitar'] and has_drums and flags['acoustic_only'] and tempo < 120:
        if flags['organ']:
            return "Bluegrass"
        if flags['acoustic_guitar']:
            return "Americana"
        return "Country"
    
    # Flamenco: Spanish guitar style
    if flags['acoustic_guitar'] and flags['ethnic'] and not has_drums:
        return "Flamenco"
    
    # ================================================================
    # LATIN FAMILY
    # ================================================================
    if flags['organ'] and has_drums:
        if is_waltz_time:
            return "Tango"
        if tempo > 150:
            return "Salsa"
        if tempo > 120:
            return "Salsa"
        return "Latin"
    
    if flags['guitar'] and has_drums and not flags['synth']:
        if tempo < 100 and not flags['distorted_guitar']:
            return "Bossa Nova"
        if flags['ethnic']:
            return "Cumbia"
    
    if flags['percussive'] and has_drums:
        if tempo > 140:
            return "Salsa"
        if tempo > 100:
            return "Merengue"
        return "Samba"
    
    # Reggaeton: specific rhythm pattern
    if flags['synth'] and has_drums and tempo > 90:
        if flags['electric_bass']:
            return "Reggaeton"
    
    # ================================================================
    # CINEMATIC/FILM SCORE
    # ================================================================
    if (flags['strings'] or flags['choir']) and flags['piano']:
        if has_drums:
            return "Cinematic"
        if flags['synth_pad']:
            return "Cinematic"
        if tempo < 130:
            return "Cinematic"
    
    # Video game music: often synth + orchestra hybrid
    if flags['synth'] and flags['has_orchestral'] and has_drums:
        return "Video Game"
    
    # ================================================================
    # REGGAE/SKA
    # ================================================================
    if flags['guitar'] and flags['organ'] and has_drums and tempo < 120:
        if tempo > 100:
            return "Ska"
        return "Reggae"
    
    # ================================================================
    # HIP HOP
    # ================================================================
    if has_drums and flags['bass'] and not flags['guitar'] and not flags['strings']:
        if flags['synth']:
            return "Hip Hop"
        if flags['electric_bass']:
            return "Hip Hop"
    
    # ================================================================
    # GOSPEL/HYMN
    # ================================================================
    if flags['choir'] and flags['organ'] and has_drums:
        return "Gospel"
    
    if flags['choir'] and flags['organ'] and not has_drums:
        return "Hymn"
    
    # ================================================================
    # MARCH/POLKA
    # ================================================================
    if flags['brass'] and has_drums and is_march_time and tempo > 100:
        return "March"
    
    if flags['brass'] and has_drums and tempo > 120 and time_sig_num == 2:
        return "Polka"
    
    # ================================================================
    # WORLD MUSIC
    # ================================================================
    if flags['ethnic'] and flags['acoustic_only']:
        if flags['percussive']:
            return "African"
        if any(104 <= p <= 107 for p in patches):  # Sitar, etc.
            return "Asian"
        if any(108 <= p <= 111 for p in patches):  # Balalaika, etc.
            return "Middle Eastern"
        return "World"
    
    if flags['ethnic']:
        return "World"
    
    # Caribbean
    if flags['percussive'] and has_drums and tempo > 100:
        return "Caribbean"
    
    # ================================================================
    # NEW AGE
    # ================================================================
    if flags['piano'] and (flags['synth_pad'] or flags['organ']) and not has_drums:
        if tempo < 100 and polyphony < 4:
            return "New Age"
    
    if flags['flute'] and flags['synth_pad'] and not has_drums:
        return "New Age"
    
    # ================================================================
    # SHOW TUNES
    # ================================================================
    if flags['piano'] and flags['strings'] and has_drums and not flags['synth']:
        if 100 < tempo < 140:
            return "Show Tune"
    
    # ================================================================
    # HOLIDAY (Christmas, etc.)
    # ================================================================
    # Could detect by specific melodic patterns, but that's complex
    # Skip for now
    
    # ================================================================
    # FALLBACKS
    # ================================================================
    if flags['piano'] and not has_drums and not flags['guitar']:
        return "Solo Piano"
    
    if flags['strings'] and not has_drums:
        return "Classical"
    
    if flags['guitar'] and has_drums:
        return "Rock"
    
    if flags['piano'] and has_drums:
        return "Pop"
    
    return "unknown"


# ---------------------------------------------------------------------------
# ─── ENHANCED SONG TYPE CLASSIFICATION ────────────────────────────────────
# ---------------------------------------------------------------------------

def _classify_song_type(
    channel_pitches: Dict[int, List[int]],
    has_drums: bool,
    inst_flags: Dict[str, bool],
    n_channels: int
) -> int:
    """Enhanced song type classification including solo piano detection."""
    melodic = [ch for ch in channel_pitches if ch != 9 and channel_pitches[ch]]
    if not melodic:
        return 3  # Drums only
    
    if len(melodic) == 1:
        # Solo instrument - check if piano
        if inst_flags.get('piano_only'):
            return 6  # Solo piano
        return 5  # Solo instrument
    
    # Full ensemble / orchestral
    if len(melodic) >= 8:
        return 8  # Full ensemble
    
    # Chamber ensemble: small acoustic group
    if 2 <= len(melodic) <= 5:
        if inst_flags.get('acoustic_only') and inst_flags.get('has_orchestral'):
            return 7  # Chamber ensemble
    
    # Bass and drums only
    if len(melodic) == 1 and has_drums:
        return 4  # Bass and drums
    
    ranges = [max(channel_pitches[ch]) - min(channel_pitches[ch]) for ch in melodic]
    if sum(r > 24 for r in ranges) >= 2:
        return 2  # Polyphonic
    if len(melodic) >= 2:
        sorted_r = sorted(ranges, reverse=True)
        return 1 if sorted_r[0] > sorted_r[1] * 1.5 else 0
    return 1


# ---------------------------------------------------------------------------
# ─── ENHANCED MOOD CLASSIFICATION ─────────────────────────────────────────
# ---------------------------------------------------------------------------

def _classify_mood(
    key_root: int,
    scale: int,
    tempo: float,
    avg_vel: float,
    pitch_range: int,
    polyphony: float,
    has_minor: bool,
    genre: str,
    time_sig_num: int
) -> str:
    """Enhanced mood classification considering genre context and happy detection."""
    
    # Genre-influenced moods
    if genre in ("Solo Piano", "Impressionist", "New Age", "Ambient"):
        if tempo < 80:
            return "Peaceful"
        if tempo < 110:
            return "Mysterious" if scale == 1 else "Romantic"
        return "Uplifting"
    
    if genre in ("Metal", "Punk", "Hardcore"):
        return "Aggressive"
    
    if genre in ("Blues", "Delta Blues", "Chicago Blues"):
        if tempo < 90:
            return "Somber"
        return "Melancholic"
    
    if genre in ("Waltz",):
        return "Romantic"
    
    if genre in ("March", "Polka"):
        return "Happy"
    
    if genre in ("Gospel", "Hymn"):
        return "Triumphant"
    
    if genre in ("Cinematic", "Orchestral"):
        if scale == 1 and tempo < 80:
            return "Dramatic"
        if scale == 0 and tempo > 120:
            return "Triumphant"
        return "Dramatic"
    
    if genre in ("Ragtime",):
        return "Happy"
    
    if genre in ("Ska",):
        return "Happy"
    
    if genre in ("Reggae",):
        return "Happy"
    
    if genre in ("Bossa Nova",):
        return "Peaceful"
    
    if genre in ("Disco", "Funk", "Dance"):
        return "Happy"
    
    if genre in ("Pop",):
        if scale == 0 and 100 <= tempo <= 130:
            return "Happy"
        return "Uplifting"
    
    if genre in ("Show Tune",):
        if scale == 0:
            return "Happy"
        return "Playful"
    
    if genre in ("Country", "Bluegrass", "Americana"):
        if scale == 0 and tempo > 100:
            return "Happy"
        return "Uplifting"
    
    if genre in ("Folk", "Singer-Songwriter"):
        if scale == 0:
            return "Happy"
        return "Melancholic"
    
    if genre in ("Celtic",):
        if scale == 0:
            return "Happy"
        return "Mysterious"
    
    if genre in ("Holiday",):
        return "Happy"
    
    # Standard mood classification
    if scale == 0:  # Major
        # Happy: moderate tempo, moderate velocity, not too complex
        if 100 <= tempo <= 130 and 70 <= avg_vel <= 100 and polyphony < 5:
            return "Happy"
        if tempo > 130 and avg_vel > 80:
            return "Energetic"
        if tempo > 120:
            return "Playful"
        if tempo < 80:
            return "Peaceful"
        if tempo < 100:
            return "Uplifting"
        return "Uplifting"
    else:  # Minor
        if tempo < 70 and avg_vel < 60:
            return "Melancholic"
        if tempo < 70:
            return "Somber"
        if tempo > 120:
            return "Tense"
        if tempo > 100:
            return "Dark"
        if avg_vel > 90:
            return "Energetic"
        if polyphony > 5:
            return "Dramatic"
        return "Dark"


# ---------------------------------------------------------------------------
# ─── FAST POLYPHONY CALCULATION ───────────────────────────────────────────
# ---------------------------------------------------------------------------

def _calc_avg_polyphony(all_notes: List[Tuple[int, int, int, int]], 
                        max_tick: int, ticks_per_beat: int) -> float:
    """O(n log n + samples) with safeguards against extreme values."""
    if not all_notes:
        return 0.0
    
    # Find actual span of music, not max_tick (which may include silence)
    min_tick = min(st for st, _, _, _ in all_notes)
    actual_max = max((st + dur for st, dur, _, _ in all_notes if dur > 0), default=min_tick)
    span = actual_max - min_tick
    
    if span <= 0:
        return 0.0
    
    events = []
    for st, dur, ch, _ in all_notes:
        if dur > 0:  # Only count notes with duration
            events.append((st, 1))
            events.append((st + dur, -1))
    
    if not events:
        return 0.0
    
    events.sort(key=lambda x: (x[0], x[1]))
    
    # Ensure reasonable sample interval
    sample_interval = max(ticks_per_beat // 4, 1)
    
    # Cap samples to avoid excessive computation (10k samples is plenty for accuracy)
    MAX_SAMPLES = 10000
    if span / sample_interval > MAX_SAMPLES:
        sample_interval = max(span // MAX_SAMPLES, 1)
    
    poly_values = []
    active = 0
    event_idx = 0
    n_events = len(events)
    
    for sample_tick in range(min_tick, actual_max, sample_interval):
        while event_idx < n_events and events[event_idx][0] <= sample_tick:
            active += events[event_idx][1]
            event_idx += 1
        poly_values.append(active)
    
    return _mean(poly_values) if poly_values else 0.0


# ---------------------------------------------------------------------------
# ─── DRUM GROUPS SUMMARY (OPTIMIZED) ──────────────────────────────────────
# ---------------------------------------------------------------------------

def _build_drum_groups_summary(drum_hits: collections.Counter) -> List[Dict]:
    """Build drum groups summary with O(D) complexity instead of O(D²)."""
    if not drum_hits:
        return []
    
    # Pre-compute group info for all drum notes
    note_to_group: Dict[int, Tuple[int, str, str]] = {}
    for note in drum_hits:
        if note not in note_to_group:
            note_to_group[note] = _get_drum_group(note)
    
    # Group notes by group_id
    groups: Dict[int, List[Tuple[int, int, str]]] = collections.defaultdict(list)
    for note, count in drum_hits.items():
        group_id, group_name, drum_name = note_to_group[note]
        groups[group_id].append((note, count, drum_name.lower()))
    
    # Build summary
    summary = []
    for group_id in sorted(groups.keys()):
        group_notes = groups[group_id]
        group_name = note_to_group[group_notes[0][0]][1].lower()
        total_hits = sum(count for _, count, _ in group_notes)
        drums_used = [drum_name for _, _, drum_name in group_notes]
        
        summary.append({
            "group_id": group_id,
            "group_name": group_name,
            "total_hits": total_hits,
            "total_hits_desc": _hit_count_to_words(total_hits).lower(),
            "drums_used": drums_used,
            "drum_note_ids": [note for note, _, _ in group_notes]
        })
    
    return summary


# ---------------------------------------------------------------------------
# ─── HUMAN DICT LOWERCASING ───────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _lowercase_human_dict(d):
    """
    Recursively lowercase all strings in human_dict except for chord names 
    and chord progressions.
    """
    if isinstance(d, dict):
        result = {}
        for k, v in d.items():
            # Keep chord and progression values as-is, also keep instrument names as-is
            if k in ("chord", "progression", "name", "instrument_name", "family", "instrument_family",
                     "drum_name", "group_name", "drums_used"):
                result[k] = v
            else:
                result[k] = _lowercase_human_dict(v)
        return result
    elif isinstance(d, list):
        return [_lowercase_human_dict(item) for item in d]
    elif isinstance(d, str):
        return d.lower()
    else:
        return d


# ---------------------------------------------------------------------------
# ─── MASTER ANALYSIS ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def analyze_midi(filepath: str, top_n_instruments: int = 5,
                 top_n_drums: int = 3, chord_threshold: float = 10.0,
                 overlap_threshold: float = 40.0,
                 top_n_chords: int = 5,
                 top_n_progressions: int = 5,
                 min_progression_length: int = 3,
                 max_progression_length: int = 5
                 ) -> Tuple[Dict, Dict]:
    
    """
    Perform comprehensive musical analysis of a MIDI file.

    Extracts and classifies musical features including metadata (tempo, time signature, key),
    instrumentation (GM patches, drum sets, instrument families), harmonic content (chords,
    progressions, composition type), rhythmic characteristics (density, complexity, note duration),
    melodic structure (monophonic melodies, pitch range), dynamics (velocity statistics), texture
    (polyphony degree, song type), stylistic classification (genre, mood), and ornamental elements
    (arpeggios, trills, grace notes, glissandos, tremolo, ostinato, syncopation, runs, mordents).

    Uses Krumhansl-Schmuckler algorithm for key detection, sweep-line algorithms for polyphony
    and chord dominance calculations, and heuristic-based classifiers for genre and mood.

    Args:
        filepath: Path to the MIDI file to analyze.
        top_n_instruments: Maximum number of instruments to include in ranked results.
        top_n_drums: Maximum number of drum types to include in ranked results.
        chord_threshold: Maximum chord percentage (0-100) for monophonic melody detection.
        overlap_threshold: Maximum overlap percentage (0-100) for monophonic melody detection.
        top_n_chords: Maximum number of distinct chords to return, ranked by frequency.
        top_n_progressions: Maximum number of chord progressions to return, ranked by frequency.
        min_progression_length: Minimum chord count for detected progressions.
        max_progression_length: Maximum chord count for detected progressions.

    Returns:
        A tuple of (human_dict, numeric_dict):
        
        human_dict: Human-readable analysis with descriptive word labels (e.g., "moderate tempo",
            "several chords", "about half"). Contains song metadata, instrument details with
            family classifications, drum details with percussion group names, chord names,
            progression strings, melody previews, and qualitative descriptions of all features.
            
        numeric_dict: Quantitative analysis with integer tokens for categorical features
            (genre, mood, tempo class, etc.), raw numeric values (BPM, velocity stats, pitch
            range, polyphony degree), chord tuples (root, quality), progression tuples,
            MIDI note numbers, patch IDs, and boolean instrument flags (0/1).

    Notes:
        - Key detection prefers MIDI key_signature metadata when present; falls back to
          Krumhansl-Schmuckler correlation analysis.
        - Chord detection uses adaptive window sizing with template matching against 16 quality types.
        - Genre classification uses hierarchical heuristic rules based on instrument presence,
          tempo ranges, time signatures, and musical element counts.
        - Mood classification incorporates genre context for genre-specific mood associations.
        - Monophonic melodies are categorized as "lead" or "bass" based on patch type and
          average pitch relative to instrument default octave.
        - Drum analysis maps MIDI note numbers to percussion groups (bass drums, snares, etc.)
          and identifies drum set type from channel 9 patch.
        - Count-in detection identifies drum-only passages before the first melodic note.
    """
    
    # ── 1. Load ─────────────────────────────────────────────────────────────
    with open(filepath, 'rb') as f:
        raw = f.read()
    score = MIDI.midi2score(raw)
    ticks_per_beat = score[0]
    tracks = score[1:]
    
    # ── 2. Build patch timelines ────────────────────────────────────────────
    patch_timelines = _build_patch_timelines(tracks)
    
    # ── 3. Collect metadata ─────────────────────────────────────────────────
    tempo_us = 500_000
    time_sig_num, time_sig_den = 4, 4
    key_sf, key_mi = 0, 0
    key_detected_from_sig = False
    
    all_notes = []
    channel_patches = {}
    channel_notes = collections.defaultdict(list)
    patch_notes = collections.defaultdict(list)
    drum_hits = collections.Counter()
    patch_counter = collections.Counter()
    velocities = []
    max_tick = 0
    tempo_map = [(0, tempo_us)]
    drum_events = []  # List of (tick, note) for all drum hits
    
    # Track drum set (patch on channel 9)
    drum_set_patch = 0  # Default to Standard
    
    for track in tracks:
        for event in track:
            etype = event[0]
            
            if etype == 'set_tempo':
                tempo_us = event[2]
                tempo_map.append((event[1], tempo_us))
            elif etype == 'time_signature':
                time_sig_num = event[2]
                time_sig_den = 2 ** event[3]
            elif etype == 'key_signature':
                key_sf, key_mi = event[2], event[3]
                key_detected_from_sig = True
            elif etype == 'patch_change':
                _, tick, ch, patch = event
                channel_patches[ch] = patch
                # Track drum set changes on channel 9
                if ch == 9:
                    drum_set_patch = patch
            elif etype == 'note':
                _, start, dur, ch, pitch, vel = event
                end = start + dur
                if end > max_tick:
                    max_tick = end
                
                if ch == 9:
                    drum_hits[pitch] += 1
                    drum_events.append((start, pitch))
                else:
                    active_patch = _get_patch_at_tick(patch_timelines.get(ch, []), start)
                    all_notes.append((start, dur, ch, pitch))
                    channel_notes[ch].append((start, dur, pitch))
                    patch_notes[(ch, active_patch)].append((start, dur, pitch))
                    velocities.append(vel)
                    patch_counter[active_patch] += 1
    
    tempo_map.sort()
    
    # ── 4. Duration ─────────────────────────────────────────────────────────
    def ticks_to_seconds(tick):
        t_sec, prev_t, prev_tempo = 0.0, 0, 500_000
        for tm_t, tm_tempo in tempo_map[1:]:
            if tick <= tm_t:
                break
            t_sec += (tm_t - prev_t) / ticks_per_beat * (prev_tempo / 1e6)
            prev_t, prev_tempo = tm_t, tm_tempo
        t_sec += (tick - prev_t) / ticks_per_beat * (prev_tempo / 1e6)
        return t_sec
    
    song_duration_min = ticks_to_seconds(max_tick) / 60.0
    song_len_label = ("Very Short" if song_duration_min < 1.5 else
                      "Short" if song_duration_min < 3.0 else
                      "Medium" if song_duration_min < 5.0 else
                      "Long" if song_duration_min < 8.0 else "Very Long")
    
    # ── 5. Tempo ────────────────────────────────────────────────────────────
    tempo_bpm = 60_000_000 / float(_median([t for _, t in tempo_map]))
    tempo_label, tempo_token = (("Very Slow", 0) if tempo_bpm < 60 else
                                ("Slow", 1) if tempo_bpm < 80 else
                                ("Moderate", 2) if tempo_bpm < 100 else
                                ("Moderately Fast", 3) if tempo_bpm < 120 else
                                ("Fast", 4) if tempo_bpm < 160 else ("Very Fast", 5))
    
    # ── 6. Rhythm density ───────────────────────────────────────────────────
    total_beats = max_tick / ticks_per_beat if ticks_per_beat > 0 else 1
    note_density = len(all_notes) / total_beats
    rhythm_label, rhythm_token = (("Slow", 0) if note_density < 1.5 else
                                  ("Moderate", 1) if note_density < 3 else
                                  ("Average", 2) if note_density < 6 else
                                  ("Busy", 3) if note_density < 10 else ("Very Busy", 4))
    
    # ── 7. Key ──────────────────────────────────────────────────────────────
    all_pitches = [n[3] for n in all_notes]
    
    if key_detected_from_sig:
        scale_token = key_mi
        key_map = MAJOR_KEY_MAP if scale_token == 0 else MINOR_KEY_MAP
        key_name = key_map.get(key_sf, "C")
        try:
            key_token = NOTE_NAMES.index(key_name)
        except ValueError:
            key_token, scale_token = _detect_key_krumhansl(all_pitches)
            key_name = NOTE_NAMES[key_token]
    else:
        key_token, scale_token = _detect_key_krumhansl(all_pitches)
        key_name = NOTE_NAMES[key_token]
    
    scale_label = "Major" if scale_token == 0 else "Minor"
    
    # ── 8. Instruments ──────────────────────────────────────────────────────
    has_drums = bool(drum_hits)
    top_drums = [note for note, _ in drum_hits.most_common(top_n_drums)]
    top_instr_patches = [p for p, _ in patch_counter.most_common(top_n_instruments)]
    
    patches_list = list(channel_patches.values())
    inst_flags = _get_instrument_flags(patches_list)
    inst_flags['has_drums'] = has_drums
    
    # ── 9. Chords (with counts, sorted by frequency descending) ─────────────
    chord_sequence = _detect_chords(all_notes, ticks_per_beat)
    chord_counts = collections.Counter(chord_sequence)
    # most_common() already returns in descending order of frequency
    most_common_chords_with_counts = chord_counts.most_common(top_n_chords)
    
    # ── 9b. Chord Progressions (with counts, sorted by frequency descending) ─
    chord_progressions = _detect_chord_progressions(
        chord_sequence,
        min_length=min_progression_length,
        max_length=max_progression_length,
        top_n=top_n_progressions
    )
    
    # ── 9c. Direct chord count and notes-chords ratio from score ────────────
    chord_stats = _count_chords_from_score(all_notes, ticks_per_beat)
    chord_count = chord_stats["chord_count"]
    total_notes = chord_stats["total_notes"]
    notes_chords_ratio = chord_stats["notes_chords_ratio"]
    chord_dominance_pct = chord_stats["chord_dominance_pct"]
    
    # Determine dominant composition type
    dominant_composition_type = "chords" if chord_dominance_pct >= 50 else "notes"
    dominant_composition_token = 1 if chord_dominance_pct >= 50 else 0
    
    # ── 10. Dynamics ────────────────────────────────────────────────────────
    avg_velocity = _mean(velocities) if velocities else 64.0
    vel_std = _std(velocities) if velocities else 0.0
    
    dyn_label, dyn_token = (("Soft (pp)", 0) if avg_velocity < 40 else
                            ("Quiet (p)", 1) if avg_velocity < 60 else
                            ("Average (mp)", 2) if avg_velocity < 80 else
                            ("Loud (mf)", 3) if avg_velocity < 100 else
                            ("Very Loud (f)", 4) if avg_velocity < 115 else ("Fortissimo (ff)", 5))
    
    dyn_range_label, dyn_range_token = (("Very Consistent", 0) if vel_std < 10 else
                                        ("Consistent", 1) if vel_std < 20 else
                                        ("Varied", 2) if vel_std < 30 else ("Highly Dynamic", 3))
    
    # ── 11. Pitch range ─────────────────────────────────────────────────────
    if all_pitches:
        pitch_min, pitch_max = min(all_pitches), max(all_pitches)
        pitch_range = pitch_max - pitch_min
        avg_pitch = _mean(all_pitches)
    else:
        pitch_min = pitch_max = pitch_range = 0
        avg_pitch = 60.0
    
    tone_label, tone_token = (("Bass", 0) if avg_pitch < 48 else
                              ("Low Midrange", 1) if avg_pitch < 60 else
                              ("Midrange", 2) if avg_pitch < 72 else
                              ("High Midrange", 3) if avg_pitch < 84 else ("Treble", 4))
    
    # ── 12. Song type (enhanced with instrument flags) ─────────────────────
    channel_pitch_lists = {ch: [n[2] for n in notes] for ch, notes in channel_notes.items()}
    n_channels = len(channel_notes) + (1 if has_drums else 0)
    song_type_token = _classify_song_type(channel_pitch_lists, has_drums, inst_flags, n_channels)
    song_type_label = SONG_TYPE_LABELS[song_type_token]
    
    # ── 13. Polyphony ───────────────────────────────────────────────────────
    avg_polyphony = _calc_avg_polyphony(all_notes, max_tick, ticks_per_beat)
    poly_label, poly_token = (("Monophonic", 0) if avg_polyphony < 1.5 else
                              ("Sparse", 1) if avg_polyphony < 3 else
                              ("Moderate", 2) if avg_polyphony < 6 else
                              ("Dense", 3) if avg_polyphony < 10 else ("Very Dense", 4))
    
    # ── 14. Musical elements (with limits) ──────────────────────────────────
    element_counts = {"arpeggio": 0, "trill": 0, "grace_note": 0, "glissando": 0,
                      "tremolo": 0, "ostinato": 0, "syncopation": 0, "run": 0, "mordent": 0}
    
    for ch, notes in channel_notes.items():
        channel_elements = _detect_elements_for_channel(notes, ticks_per_beat, time_sig_num)
        for key, value in channel_elements.items():
            element_counts[key] += value
    
    elements_found = [f"{k} ({v})" for k, v in element_counts.items() if v > 0]
    elements_tokens = [ELEMENT_MAP[k] for k, v in element_counts.items() if v > 0]
    
    # ── 15. Genre (enhanced) ────────────────────────────────────────────────
    genre_label = _classify_genre(
        patches_list, patch_counter, has_drums, tempo_bpm,
        time_sig_num, time_sig_den, avg_polyphony, note_density,
        avg_velocity, scale_token, len(tracks), n_channels,
        song_type_token, element_counts, chord_sequence
    )
    genre_token = GENRE_TOKENS.get(genre_label, 0)
    
    # ── 16. Mood (enhanced with genre context) ──────────────────────────────
    mood_label = _classify_mood(
        key_token, scale_token, tempo_bpm, avg_velocity, pitch_range,
        avg_polyphony, scale_token == 1, genre_label, time_sig_num
    )
    mood_token = MOOD_TOKENS.get(mood_label, 2)
    
    # ── 17. Time signature ──────────────────────────────────────────────────
    time_sig_label = _time_sig_to_words(time_sig_num, time_sig_den)
    
    # ── 18. Rhythmic complexity ─────────────────────────────────────────────
    if len(all_notes) >= 2:
        sorted_all = sorted(all_notes, key=lambda x: x[0])
        onsets = [n[0] for n in sorted_all]
        iois = [onsets[i+1] - onsets[i] for i in range(len(onsets)-1) if onsets[i+1] != onsets[i]]
        ioi_mean = _mean(iois)
        ioi_cv = _std(iois) / ioi_mean if iois and ioi_mean > 0 else 0.0
    else:
        ioi_cv = 0.0
    
    rhythmic_complexity_label, rhythmic_complexity_token = (
        ("Regular", 0) if ioi_cv < 0.3 else
        ("Moderately Complex", 1) if ioi_cv < 0.7 else
        ("Complex", 2) if ioi_cv < 1.2 else ("Highly Irregular", 3))
    
    # ── 19. Note duration ───────────────────────────────────────────────────
    if all_notes:
        avg_dur_beats = _mean([n[1] for n in all_notes]) / ticks_per_beat
        dur_label = next((lbl for (lo, hi), lbl in [
            ((0, 0.25), "Very Short (32nd)"), ((0.25, 0.5), "Short (16th)"),
            ((0.5, 1.0), "Eighth Note"), ((1.0, 2.0), "Quarter Note"),
            ((2.0, 4.0), "Half Note"), ((4.0, 9999), "Long (Whole+)")]
            if lo <= avg_dur_beats < hi), "Quarter Note")
    else:
        avg_dur_beats, dur_label = 0.0, "N/A"
    
    # ── 20. Counts ──────────────────────────────────────────────────────────
    n_tracks = len(tracks)
    
    # ── 21. Monophonic melodies ─────────────────────────────────────────────
    all_mono_melodies = _get_monophonic_melodies(
        patch_notes, ticks_per_beat, max_tick,
        chord_threshold_pct=chord_threshold,
        overlap_threshold_pct=overlap_threshold
    )
    
    lead_melodies = [m for m in all_mono_melodies if m["category"] == "lead"]
    bass_melodies = [m for m in all_mono_melodies if m["category"] == "bass"]
    
    def _fmt_human(melodies):
        return [{"instrument": m["instrument_name"],
                 "instrument_family": m["instrument_family"],
                 "note_count_desc": _melody_length_to_words(m["note_count"]),
                 "relative_length_desc": _percentage_to_words(m["relative_length_pct"]),
                 "duration_desc": _beats_to_words(m["relative_length_beats"]),
                 "chord_presence_desc": _percentage_to_words(m["chord_pct"]),
                 "duration_overlap_desc": _percentage_to_words(m["overlap_pct"]),
                 "melody_preview": m["melody"][:12],
                 "full_melody_length_desc": _note_count_to_words(len(m["melody"]))} for m in melodies]
    
    def _fmt_numeric(melodies):
        return [{"instrument_num": m["instrument_num"], "channel": m["channel"],
                 "note_count": m["note_count"],
                 "relative_length_beats": m["relative_length_beats"],
                 "relative_length_pct": m["relative_length_pct"],
                 "chord_pct": m["chord_pct"], "overlap_pct": m["overlap_pct"],
                 "melody_pitches": m["melody_pitches"]} for m in melodies]
    
    lead_human = _fmt_human(lead_melodies) if lead_melodies else None
    bass_human = _fmt_human(bass_melodies) if bass_melodies else None
    lead_numeric = _fmt_numeric(lead_melodies) if lead_melodies else []
    bass_numeric = _fmt_numeric(bass_melodies) if bass_melodies else []
    
    # ── 22. Instrument details ──────────────────────────────────────────────
    instrument_details = [{"instrument_name": MIDI.Number2patch.get(p, f"unknown_{p}").lower(),
                           "instrument_family": _instrument_family(p),
                           "note_count_desc": _note_count_to_words(c)}
                          for p, c in patch_counter.most_common(top_n_instruments)]
    
    # ── 23. Drum details with actual percussion groups ──────────────────────
    drum_details = []
    
    for note, count in drum_hits.most_common(top_n_drums):
        group_id, group_name, drum_name = _get_drum_group(note)
        drum_details.append({
            "drum_name": drum_name.lower(),
            "group": group_name.lower(),
            "hit_count_desc": _hit_count_to_words(count).lower()
        })
    
    # Build drum groups summary using optimized function
    drum_groups_summary = _build_drum_groups_summary(drum_hits)
    
    # ── 24. Drum set information ────────────────────────────────────────────
    drum_set_name = _get_drum_set_name(drum_set_patch)
    
    # ── 25. Patch analysis ──────────────────────────────────────────────────
    patch_analysis = []
    for (ch, patch), notes in patch_notes.items():
        if not notes:
            continue
        stats = _calc_mono_stats(notes)
        patch_analysis.append({
            "channel": NUM_WORDS[ch+1],
            "instrument": MIDI.Number2patch.get(patch, f"unknown_{patch}"),
            "total_notes_desc": _note_count_to_words(len(notes)),
            "valid_notes_desc": _note_count_to_words(stats["valid_note_count"]),
            "chord_presence_desc": _percentage_to_words(stats["chord_pct"]),
            "duration_overlap_desc": _percentage_to_words(stats["overlap_pct"]),
            "is_monophonic": 'monophonic' if (stats["chord_pct"] <= chord_threshold and 
                              stats["overlap_pct"] <= overlap_threshold) else 'polyphonic',
        })
    
    # ── 26. Instrument flags summary ────────────────────────────────────────
    inst_flags_summary = {k: v for k, v in inst_flags.items() if v}
    
    # ── 27. Format chords for human dict (with word counts) ─────────────────
    chords_human = [{"chord": chord_name, "count_desc": _count_to_words(count)} 
                    for chord_name, count in most_common_chords_with_counts] if most_common_chords_with_counts else None
    
    # ── 28. Format chord progressions for human dict (with word counts) ─────
    chord_progressions_human = [{"progression": prog, "count_desc": _count_to_words(count)} 
                                for prog, count in chord_progressions] if chord_progressions else None
    
    # ── 29. Format chords for numeric dict (with numeric tuple format) ──────
    chords_numeric = [{"chord": _chord_name_to_numeric(chord_name), "count": count} 
                      for chord_name, count in most_common_chords_with_counts] if most_common_chords_with_counts else []
    
    # ── 30. Format chord progressions for numeric dict (with tuple of tuples format) ─
    chord_progressions_numeric = [{"progression": _progression_to_numeric(prog), "count": count} 
                                  for prog, count in chord_progressions] if chord_progressions else []
    
    # ── 31. Format elements for human dict (sorted by descending frequency, with word counts) ─
    sorted_elements = sorted(
        [(k, v) for k, v in element_counts.items() if v > 0],
        key=lambda x: -x[1]
    )
    elements_human = [{k: _count_to_words(v)} for k, v in sorted_elements] if sorted_elements else None
    
    # ── 32. Format drum groups for human dict ───────────────────────────────
    drum_groups_human = [{"group_name": g["group_name"],
                          "total_hits_desc": g["total_hits_desc"],
                          "drums_used": g["drums_used"]}
                         for g in drum_groups_summary] if drum_groups_summary else None
    
    # ── 33. Format drum groups for numeric dict ────────────────────────────
    drum_groups_numeric = [{"group_id": g["group_id"],
                            "total_hits": g["total_hits"],
                            "drum_note_ids": g["drum_note_ids"]}
                           for g in drum_groups_summary] if drum_groups_summary else []
    
    # ── 34. Primary opening/start instrument ────────────────────────────────
    opening_patch = -1
    opening_channel = -1
    opening_instrument_name = "none"
    opening_instrument_family = "none"
    
    if all_notes:
        sorted_by_start = sorted(all_notes, key=lambda x: x[0])
        first_note = sorted_by_start[0]
        opening_channel = first_note[2]
        opening_tick = first_note[0]
        opening_patch = _get_patch_at_tick(patch_timelines.get(opening_channel, []), opening_tick)
        opening_instrument_name = _patch_name(opening_patch).lower()
        opening_instrument_family = _instrument_family(opening_patch).lower()
    
    # ── 35. Predominant instrument ──────────────────────────────────────────
    predominant_patch = -1
    predominant_count = 0
    predominant_instrument_name = "none"
    predominant_instrument_family = "none"
    predominant_percentage = 0.0
    
    if patch_counter:
        predominant_patch, predominant_count = patch_counter.most_common(1)[0]
        predominant_instrument_name = _patch_name(predominant_patch).lower()
        predominant_instrument_family = _instrument_family(predominant_patch).lower()
        total_instrument_notes = sum(patch_counter.values())
        predominant_percentage = (predominant_count / total_instrument_notes * 100) if total_instrument_notes > 0 else 0.0
    
    # ── 36. Primary opening/start drum ──────────────────────────────────────
    opening_drum_note = -1
    opening_drum_name = "none"
    opening_drum_group = "none"
    opening_drum_group_id = -1
    
    if drum_events:
        drum_events_sorted = sorted(drum_events, key=lambda x: x[0])
        opening_drum_note = drum_events_sorted[0][1]
        group_id, group_name, drum_name = _get_drum_group(opening_drum_note)
        opening_drum_name = drum_name.lower()
        opening_drum_group = group_name.lower()
        opening_drum_group_id = group_id
    
    # ── 37. Predominant/dominant drum ───────────────────────────────────────
    predominant_drum_note = -1
    predominant_drum_count = 0
    predominant_drum_name = "none"
    predominant_drum_group = "none"
    predominant_drum_group_id = -1
    predominant_drum_percentage = 0.0
    
    if drum_hits:
        predominant_drum_note, predominant_drum_count = drum_hits.most_common(1)[0]
        group_id, group_name, drum_name = _get_drum_group(predominant_drum_note)
        predominant_drum_name = drum_name.lower()
        predominant_drum_group = group_name.lower()
        predominant_drum_group_id = group_id
        total_drum_hits = sum(drum_hits.values())
        predominant_drum_percentage = (predominant_drum_count / total_drum_hits * 100) if total_drum_hits > 0 else 0.0
    
    # ── 38. Count-in detection ──────────────────────────────────────────────
    has_count_in = False
    count_in_beats = 0.0
    count_in_description = "none"
    
    if has_drums and all_notes:
        # Find when first melodic note starts
        first_melodic_tick = min(n[0] for n in all_notes)
        
        # Find drum hits that occur before first melodic note
        pre_melodic_drums = [tick for tick, _ in drum_events if tick < first_melodic_tick]
        
        if pre_melodic_drums:
            # Duration from song start to first melodic note (in beats)
            count_in_beats = first_melodic_tick / ticks_per_beat if ticks_per_beat > 0 else 0
            
            # Typical count-in is 0.5 to 8 beats
            if 0.5 <= count_in_beats <= 8:
                has_count_in = True
                count_in_description = _count_in_beats_to_words(count_in_beats)
    
    # ─── ASSEMBLE DICTIONARIES ───────────────────────────────────────────────
    human_dict = {
        "song_len": song_len_label,
        "song_duration": _duration_to_words(song_duration_min),
        "song_type": song_type_label,
        "genre": genre_label,
        "track_count": _track_count_to_words(n_tracks),
        "channel_count": _channel_count_to_words(n_channels),
        "instruments": instrument_details if instrument_details else None,
        "drums": drum_details if drum_details else None,
        "drum_set": _drum_set_to_words(drum_set_patch) if has_drums else None,
        "drum_groups": drum_groups_human,
        "drum_groups_count": _group_count_to_words(len(drum_groups_summary)) if has_drums else None,
        "patch_analysis": patch_analysis if patch_analysis else None,
        "instrument_flags": inst_flags_summary if inst_flags_summary else None,
        "key": key_name,
        "scale": scale_label,
        "time_signature": time_sig_label,
        "chords": chords_human,
        "chord_count": _chord_count_to_words(chord_count),
        "notes_chords_ratio": _notes_chords_ratio_to_words(notes_chords_ratio),
        "dominant_composition_type": dominant_composition_type,
        "chord_progressions": chord_progressions_human,
        "mood": mood_label,
        "rhythm_density": rhythm_label,
        "rhythmic_complexity": rhythmic_complexity_label,
        "tempo": tempo_label,
        "tone": tone_label,
        "dynamics": dyn_label,
        "dynamic_range": dyn_range_label,
        "polyphony": poly_label,
        "avg_note_duration": dur_label,
        "elements": elements_human,
        "lead_mono_melodies": lead_human,
        "bass_mono_melodies": bass_human,
        "all_mono_melodies_count": _melody_count_to_words(len(all_mono_melodies)),
        "primary_opening_instrument": {
            "name": opening_instrument_name,
            "family": opening_instrument_family
        } if opening_patch >= 0 else None,
        "predominant_instrument": {
            "name": predominant_instrument_name,
            "family": predominant_instrument_family,
            "dominance_desc": _dominance_to_words(predominant_percentage)
        } if predominant_patch >= 0 else None,
        "primary_opening_drum": {
            "name": opening_drum_name,
            "group": opening_drum_group
        } if opening_drum_note >= 0 else None,
        "predominant_drum": {
            "name": predominant_drum_name,
            "group": predominant_drum_group,
            "dominance_desc": _dominance_to_words(predominant_drum_percentage)
        } if predominant_drum_note >= 0 else None,
        "count_in": count_in_description if has_count_in else None,
    }
    
    numeric_dict = {
        "song_len": song_duration_min,
        "song_type": song_type_token,
        "genre": genre_token,
        "n_tracks": n_tracks,
        "n_channels": n_channels,
        "instruments": [{"num": p, "count": c} for p, c in patch_counter.most_common(top_n_instruments)],
        "drums": top_drums,
        "drum_set": drum_set_patch if has_drums else -1,
        "drum_set_name": drum_set_name if has_drums else None,
        "drum_groups": drum_groups_numeric,
        "drum_groups_count": len(drum_groups_summary),
        "instrument_flags": {k: int(v) for k, v in inst_flags.items()},
        "key": key_token,
        "scale": scale_token,
        "time_sig_num": time_sig_num,
        "time_sig_den": time_sig_den,
        "chords": chords_numeric,
        "chord_count": chord_count,
        "notes_chords_ratio": notes_chords_ratio,
        "dominant_composition_type": dominant_composition_token,
        "chord_progressions": chord_progressions_numeric,
        "mood": mood_token,
        "rhythm_density": rhythm_token,
        "rhythmic_complexity": rhythmic_complexity_token,
        "tempo": tempo_token,
        "tempo_bpm": round(tempo_bpm, 2),
        "tone": tone_token,
        "dynamics": dyn_token,
        "dynamic_range": dyn_range_token,
        "avg_velocity": round(avg_velocity, 2),
        "velocity_std": round(vel_std, 2),
        "polyphony": poly_token,
        "avg_polyphony_degree": round(avg_polyphony, 2),
        "avg_note_duration_beats": round(avg_dur_beats, 3),
        "note_density_per_beat": round(note_density, 3),
        "pitch_min": pitch_min,
        "pitch_max": pitch_max,
        "pitch_range": pitch_range,
        "avg_pitch": round(avg_pitch, 2),
        "elements": elements_tokens,
        "element_counts": {k: v for k, v in element_counts.items() if v > 0},
        "lead_mono_melodies": lead_numeric,
        "bass_mono_melodies": bass_numeric,
        "all_mono_melodies_count": len(all_mono_melodies),
        "primary_opening_instrument": {
            "patch": opening_patch,
            "channel": opening_channel
        },
        "predominant_instrument": {
            "patch": predominant_patch,
            "note_count": predominant_count,
            "dominance_pct": round(predominant_percentage, 2)
        },
        "primary_opening_drum": {
            "note": opening_drum_note,
            "group_id": opening_drum_group_id
        },
        "predominant_drum": {
            "note": predominant_drum_note,
            "group_id": predominant_drum_group_id,
            "hit_count": predominant_drum_count,
            "dominance_pct": round(predominant_drum_percentage, 2)
        },
        "has_count_in": has_count_in,
        "count_in_beats": round(count_in_beats, 2),
    }
    
    # Lowercase all human-readable strings except chords, progressions, and instrument names/families
    human_dict = _lowercase_human_dict(human_dict)
    
    return human_dict, numeric_dict