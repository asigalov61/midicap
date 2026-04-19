#! /usr/bin/python3

r'''###############################################################################
###################################################################################
#
#
#	MIDI Cap Python Module
#	Version 1.0
#
#	Project Los Angeles
#
#	Tegridy Code 2026
#
#   https://github.com/Tegridy-Code/Project-Los-Angeles
#
#
###################################################################################
###################################################################################
#
#   Copyright 2026 Project Los Angeles / Tegridy Code
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
###################################################################################
'''

###################################################################################
###################################################################################

print('=' * 70)
print('Loading midicap Python module...')
print('Please wait...')
print('=' * 70)

__version__ = '1.0.0'

print('midicap module version', __version__)
print('=' * 70)

###################################################################################
###################################################################################

import os
import random
from typing import Dict, Any, Optional, List

from .analyzer import analyze_midi

###################################################################################

# =============================================================================
# FILLER WORD VARIATIONS FOR NON-DETERMINISTIC MODE
# First element in each list is used for deterministic mode
# =============================================================================

OPENING_PHRASES = [
    "The song unfolds as", "This piece reveals itself as",
    "This composition emerges as", "The track presents itself as",
    "This musical work takes shape as", "The arrangement develops as",
    "The piece stands as", "This recording unfolds as",
    "The composition reveals its nature as",
]

DURATION_PHRASES = [
    "{article} {duration}-duration {type} composition",
    "{article} {type} composition of {duration} length",
    "{article} {duration} {type} work",
    "{article} {type} piece spanning {duration} duration",
]

KEY_PHRASES = [
    "grounded in {key} {scale}", "rooted in {key} {scale}",
    "anchored in {key} {scale}", "set in {key} {scale}",
    "centered on {key} {scale}", "tonally anchored to {key} {scale}",
    "with {key} {scale} at its foundation",
]

WITH_DRUMS_PHRASES = [
    "accompanied by drums", "featuring percussion",
    "with drums providing the rhythmic foundation",
    "backed by percussion", "supported by a drum kit",
    "with drums driving the rhythm",
]

WITH_DRUM_SET_PHRASES = [
    "accompanied by {drum_set}", "featuring {drum_set}",
    "with {drum_set} laying down the groove",
    "backed by {drum_set}", "supported by {drum_set}",
    "with {drum_set} providing rhythmic texture",
]

GENRE_MOOD_INTROS = [
    "Carrying {article} {mood} {genre} essence,",
    "With its {mood} {genre} character,",
    "Embodying the spirit of {genre}, this {mood} piece",
    "This {mood} {genre} creation",
    "Infused with {article} {mood} {genre} energy,",
    "The {mood} undertone of this {genre} work",
    "This {genre} piece carries {article} {mood} quality,",
]

TEMPO_RHYTHM_PHRASES = [
    "moves with {tempo} tempo through {rhythm} rhythmic patterns",
    "flows at {tempo} tempo with {rhythm} rhythm",
    "unfolds at {tempo} pace with {rhythm} rhythmic motion",
    "progresses with {tempo} tempo, its {rhythm} rhythm giving shape to the melody",
    "advances with {tempo} tempo alongside {rhythm} rhythmic density",
    "travels at {tempo} speed with {rhythm} rhythmic character",
]

TONAL_DYNAMICS_PHRASES = [
    "The {tone} tonal palette pairs with {dynamics} dynamics",
    "A {tone} tonal character meets {dynamics} dynamic expression",
    "The {tone} register resonates with {dynamics} intensity",
    "Tonal colors settle in the {tone} range, delivered with {dynamics} force",
    "The {tone} frequency range carries {dynamics} dynamic weight",
    "Sonically, the {tone} tonal space combines with {dynamics} volume",
]

COMPLEXITY_PHRASES = [
    "The rhythmic approach feels {complexity}",
    "Rhythmic patterns show {complexity} character",
    "The groove carries {complexity} qualities",
    "Rhythmically, the piece leans toward the {complexity}",
    "The rhythmic fabric reveals {complexity} tendencies",
]

POLYPHONY_PHRASES = [
    "The texture reveals {polyphony} layering",
    "Voicing takes on {polyphony} characteristics",
    "The harmonic texture shows {polyphony} construction",
    "The writing style favors {polyphony} voicing",
    "The arrangement employs {polyphony} textures",
]

NOTE_DURATION_PHRASES = [
    "Melodic lines favor {duration} values",
    "the writing gravitates toward {duration} note lengths",
    "{duration} durations form the foundation of melodic phrases",
    "phrases are built primarily from {duration} note values",
    "{duration} values dominate the melodic construction",
]

DYNAMIC_RANGE_PHRASES = [
    "Dynamic variation stays {range}",
    "the dynamic approach feels {range}",
    "Expressive dynamics remain {range}",
    "volume shifts are {range} throughout",
    "dynamic contrast shows {range} character",
]

TIME_SIG_PHRASES = [
    "The piece follows {time_sig}",
    "Rhythmic structure adheres to {time_sig}",
    "The meter of {time_sig} gives shape to the groove",
    "Written in {time_sig}, the piece maintains this pulse throughout",
    "The rhythmic foundation rests on {time_sig}",
]

INSTRUMENT_LIST_INTROS = [
    "The instrumentation brings together {count} voices: ",
    "The sonic palette comprises {count} instruments: ",
    "{count} instruments weave the musical fabric: ",
    "The arrangement calls upon {count} instruments: ",
    "Together, {count} instruments create the soundscape: ",
    "The tonal world is built from {count} instruments: ",
]

DRUM_INTROS = [
    "Percussive color comes from ",
    "The rhythmic foundation rests on ",
    "Drums add texture through ",
    "Percussive elements include ",
    "The drum kit contributes ",
    "Rhythmic punctuation arrives via ",
]

DRUM_PREDOMINANT_PHRASES = [
    "The tambourine emerges as the primary percussive voice, {dominance}",
    "Leading the percussion is tambourine, which is {dominance}",
    "The tambourine from the tambourine section takes the percussive lead, {dominance}",
    "Dominating the drum pattern is tambourine, {dominance}",
    "The main percussion voice, {dominance}, is tambourine",
]

CHORD_INTROS = [
    "Harmonic movement travels through ",
    "The harmonic language draws from ",
    "Chords paint with colors of ",
    "The harmony unfolds across ",
    "Harmonic content features ",
    "The chordal vocabulary includes ",
]

PROGRESSION_PHRASES = [
    "Recurring progressions weave through the piece: {progressions}",
    "The harmony cycles through patterns such as {progressions}",
    "Notable harmonic sequences include {progressions}",
    "Chord movement follows paths like {progressions}",
    "The piece navigates progressions including {progressions}",
]

COMPOSITION_TYPE_PHRASES = [
    "the harmonic structure leans heavily on {comp_type}",
    "the arrangement finds its foundation in {comp_type}",
    "{comp_type} form the backbone of the writing",
    "the piece is structurally grounded in {comp_type}",
    "{comp_type} serve as the primary compositional material",
]

ELEMENT_INTROS = [
    "Technical flourishes include ",
    "Ornamental details feature ",
    "The writing incorporates ",
    "Musical techniques on display include ",
    "Expressive devices encompass ",
    "The performance practice reveals ",
]

LEAD_MELODY_PHRASES = [
    "{article} {length} unfolds on the {instrument}",
    "The {instrument} carries {article} {length}",
    "{article} {length} finds its voice through the {instrument}",
    "The {instrument} delivers {article} {length}",
    "Melodic content emerges as {article} {length} on the {instrument}",
    "{article} {length} sings through the {instrument}",
]

BASS_MELODY_PHRASES = [
    "The low end moves with {article} {length} on the {instrument}",
    "{article} {length} anchors the harmony through the {instrument}",
    "The {instrument} provides {article} {length} in the bass register",
    "Bass motion takes shape as {article} {length} on the {instrument}",
    "The foundation carries {article} {length} performed on the {instrument}",
]

PREDOMINANT_INSTRUMENT_PHRASES = [
    "The {instrument} claims the most space, {dominance}",
    "Taking center stage is the {instrument}, {dominance}",
    "The {instrument} commands attention, being {dominance}",
    "The primary voice belongs to the {instrument}, {dominance}",
    "The {instrument} holds the largest presence, {dominance}",
]

COUNT_IN_PHRASES = [
    "{article} {count_in} signals the entrance",
    "The piece enters after {article} {count_in}",
    "{article} {count_in} precedes the main body",
    "The music proper begins following {article} {count_in}",
    "An introduction of {article} {count_in} leads into the piece",
]

OPENS_WITH_PHRASES = [
    "The piece opens with the {instrument}",
    "The first sounds emerge from the {instrument}",
    "Entry belongs to the {instrument}",
    "The {instrument} introduces the piece",
    "The musical journey begins with the {instrument}",
    "The {instrument} initiates the listening experience",
]

OPENS_AND_PERFORMS_PHRASES = [
    "The {instrument} both opens the piece and remains central throughout",
    "Serving as both entry point and focal point, the {instrument} anchors the piece",
    "The {instrument} introduces the composition while maintaining a primary role",
    "Opening the piece, the {instrument} continues as the central voice",
    "The {instrument} serves as both the doorway into and the heart of the piece",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _pick(phrases: List[str], deterministic: bool, rng: random.Random) -> str:
    """Pick a phrase - first for deterministic, random otherwise."""
    return phrases[0] if deterministic else rng.choice(phrases)


def _get_article(word: str) -> str:
    """Get the correct article (a/an) for a word."""
    if not word:
        return "a"
    word_clean = word.lstrip().lower()
    if not word_clean:
        return "a"
    
    # Vowel sounds
    if word_clean[0] in 'aeiou':
        return "an"
    
    # Silent 'h' words
    silent_h = ('honest', 'hour', 'honor', 'heir', 'herb')
    for s in silent_h:
        if word_clean.startswith(s):
            return "an"
    
    # 'eight' sounds like 'ate'
    if word_clean.startswith('eight'):
        return "an"
    
    # 'x' with ex- sound
    if word_clean.startswith('x'):
        return "an"
    
    return "a"


def _lowercase_instrument(name: str) -> str:
    """Ensure instrument name is lowercase."""
    if not name or name.lower() in ("none", "unknown instrument"):
        return "unknown instrument"
    return name.lower()


def _lowercase_drum(name: str) -> str:
    """Ensure drum name is lowercase."""
    if not name or name.lower() in ("none", "unknown drum"):
        return "unknown drum"
    return name.lower()


def _format_list(items: List[str], conjunction: str = "and") -> str:
    """Format a list with proper conjunction."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} {conjunction} {items[1]}"
    return ", ".join(items[:-1]) + f", {conjunction} {items[-1]}"


def _get_count_word(n: int) -> str:
    """Get word form of a number."""
    words = {
        1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
        15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
        19: "nineteen", 20: "twenty",
    }
    return words.get(n, str(n))


def _pluralize(word: str, count: int) -> str:
    """Simple pluralization for musical terms."""
    if count == 1:
        return word
    
    irregulars = {
        "arpeggio": "arpeggios", "trill": "trills", "grace note": "grace notes",
        "glissando": "glissandos", "tremolo": "tremolos", "ostinato": "ostinatos",
        "syncopation": "syncopations", "run": "runs", "mordent": "mordents",
    }
    
    word_lower = word.lower()
    if word_lower in irregulars:
        return irregulars[word_lower]
    if word.endswith(("s", "sh", "ch", "x")):
        return word + "es"
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


def _format_element(name: str, count_desc: str) -> str:
    """Format a musical element with its count description."""
    name = name.replace("_", " ")
    
    if count_desc == "once":
        return f"{_get_article(name)} {_pluralize(name, 1)}"
    elif count_desc == "twice":
        return f"two {_pluralize(name, 2)}"
    elif "times" in count_desc:
        try:
            count = int(count_desc.split()[0])
            return f"{count_desc} {_pluralize(name, count)}"
        except (ValueError, IndexError):
            return name
    elif count_desc == "never":
        return ""
    return name


def _clean_chord_name(chord: str) -> str:
    """Format chord name for readability - capitalize root only."""
    if not chord:
        return ""
    chord_clean = chord.strip()
    chord_lower = chord_clean.lower()
    
    # Handle sharp/flat roots
    if len(chord_lower) >= 2 and chord_lower[1] in ('#', 'b'):
        return chord_lower[0].upper() + chord_lower[1:]
    return chord_lower[0].upper() + chord_lower[1:]


def _clean_progression(prog: str) -> str:
    """Clean a chord progression string - format each chord consistently."""
    if not prog:
        return ""
    if " -> " in prog:
        chords = prog.split(" -> ")
        cleaned = [_clean_chord_name(c) for c in chords]
        return " -> ".join(cleaned)
    return _clean_chord_name(prog)


def _capitalize_sentence(text: str) -> str:
    """Capitalize the first letter of a sentence."""
    if not text:
        return text
    # Find the first alphabetic character
    for i, char in enumerate(text):
        if char.isalpha():
            return text[:i] + char.upper() + text[i+1:]
    return text


def _capitalize_first_word(text: str) -> str:
    """Capitalize only the first word of text."""
    if not text:
        return text
    return text[0].upper() + text[1:]


# =============================================================================
# MAIN DESCRIPTION GENERATOR
# =============================================================================

def generate_midi_description(
    human_dict: Dict[str, Any],
    numeric_dict: Dict[str, Any],
    deterministic: bool = True,
    seed: Optional[int] = None
) -> str:
    """
    Generate a detailed, poetic human-readable description of MIDI music.
    
    Parameters
    ----------
    human_dict : Dict[str, Any]
        The human-readable dictionary from analyze_midi()
    numeric_dict : Dict[str, Any]
        The numeric dictionary from analyze_midi()
    deterministic : bool
        If True, always generates the same description for the same inputs.
        If False, uses random filler word variations for diversity.
    seed : Optional[int]
        Random seed for reproducible non-deterministic output.
        Only used when deterministic=False.
    
    Returns
    -------
    str
        A detailed, poetic, and natural human-readable description.
    """
    # Initialize RNG
    if deterministic:
        rng = random.Random(42)
    elif seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()
    
    def pick(phrases: List[str]) -> str:
        return _pick(phrases, deterministic, rng)
    
    sentences: List[str] = []
    
    # ==========================================================================
    # EXTRACT ALL VALUES
    # ==========================================================================
    song_len = human_dict.get("song_len", "medium")
    song_type = human_dict.get("song_type", "unknown")
    key = human_dict.get("key", "c")
    scale = human_dict.get("scale", "major")
    mood = human_dict.get("mood", "neutral")
    tempo = human_dict.get("tempo", "moderate")
    rhythm_density = human_dict.get("rhythm_density", "average")
    rhythmic_complexity = human_dict.get("rhythmic_complexity", "regular")
    tone = human_dict.get("tone", "midrange")
    dynamics = human_dict.get("dynamics", "average (mp)")
    dynamic_range = human_dict.get("dynamic_range", "consistent")
    polyphony = human_dict.get("polyphony", "moderate")
    avg_note_duration = human_dict.get("avg_note_duration", "quarter note")
    time_sig = human_dict.get("time_signature", "common time")
    genre = human_dict.get("genre", "unknown")
    comp_type = human_dict.get("dominant_composition_type", "notes")
    
    has_drums = bool(human_dict.get("drums"))
    instruments = human_dict.get("instruments") or []
    drums = human_dict.get("drums") or []
    chords = human_dict.get("chords")
    progressions = human_dict.get("chord_progressions")
    elements = human_dict.get("elements")
    lead_melodies = human_dict.get("lead_mono_melodies")
    bass_melodies = human_dict.get("bass_mono_melodies")
    opening_instr = human_dict.get("primary_opening_instrument")
    pred_instr = human_dict.get("predominant_instrument")
    pred_drum = human_dict.get("predominant_drum")
    count_in = human_dict.get("count_in")
    drum_set = human_dict.get("drum_set")
    
    has_count_in = numeric_dict.get("has_count_in", False)
    
    # ==========================================================================
    # SENTENCE 1: OVERVIEW (Length, Type, Drums, Key)
    # ==========================================================================
    overview_parts = []
    
    # Duration and type - use article based on duration word
    duration_article = _get_article(song_len)
    duration_phrase = pick(DURATION_PHRASES).format(
        duration=song_len.lower(),
        type=song_type.lower(),
        article=duration_article
    )
    overview_parts.append(duration_phrase)
    
    # Drums
    if has_drums:
        if drum_set:
            drums_phrase = pick(WITH_DRUM_SET_PHRASES).format(drum_set=drum_set)
        else:
            drums_phrase = pick(WITH_DRUMS_PHRASES)
        overview_parts.append(drums_phrase)
    
    # Key
    key_phrase = pick(KEY_PHRASES).format(
        key=key.upper(),
        scale=scale.lower()
    )
    overview_parts.append(key_phrase)
    
    sentence1 = f"{pick(OPENING_PHRASES)} {', '.join(overview_parts)}."
    sentences.append(sentence1)
    
    # ==========================================================================
    # SENTENCE 2: GENRE, MOOD, TEMPO, RHYTHM
    # ==========================================================================
    # Genre/mood intro with correct article
    if genre and genre.lower() != "unknown":
        mood_article = _get_article(mood)
        genre_intro = pick(GENRE_MOOD_INTROS).format(
            mood=mood.lower(),
            genre=genre.lower(),
            article=mood_article
        )
    else:
        genre_intro = f"This {mood.lower()} piece"
    
    # Tempo and rhythm
    tempo_rhythm = pick(TEMPO_RHYTHM_PHRASES).format(
        tempo=tempo.lower(),
        rhythm=rhythm_density.lower()
    )
    
    sentence2 = f"{genre_intro} {tempo_rhythm}."
    sentences.append(sentence2)
    
    # ==========================================================================
    # SENTENCE 3: TONAL AND DYNAMICS
    # ==========================================================================
    tonal_dyn = pick(TONAL_DYNAMICS_PHRASES).format(
        tone=tone.lower(),
        dynamics=dynamics.lower()
    )
    sentences.append(f"{tonal_dyn}.")
    
    # ==========================================================================
    # SENTENCE 4+: ADDITIONAL CHARACTERISTICS
    # ==========================================================================
    # Rhythmic complexity (if notable)
    if rhythmic_complexity.lower() != "regular":
        complexity = pick(COMPLEXITY_PHRASES).format(
            complexity=rhythmic_complexity.lower()
        )
        sentences.append(f"{complexity}.")
    
    # Polyphony
    if polyphony.lower() not in ("monophonic", "sparse"):
        poly_phrase = pick(POLYPHONY_PHRASES).format(polyphony=polyphony.lower())
        sentences.append(f"{poly_phrase}.")
    
    # Note duration
    if avg_note_duration.lower() not in ("n/a", "quarter note"):
        dur_phrase = pick(NOTE_DURATION_PHRASES).format(duration=avg_note_duration.lower())
        sentences.append(_capitalize_first_word(dur_phrase) + ".")
    
    # Dynamic range
    if dynamic_range.lower() != "consistent":
        range_phrase = pick(DYNAMIC_RANGE_PHRASES).format(range=dynamic_range.lower())
        sentences.append(_capitalize_first_word(range_phrase) + ".")
    
    # Time signature (if unusual)
    if time_sig.lower() != "common time":
        sig_phrase = pick(TIME_SIG_PHRASES).format(time_sig=time_sig)
        sentences.append(f"{sig_phrase}.")
    
    # ==========================================================================
    # INSTRUMENTATION
    # ==========================================================================
    if instruments:
        n_instruments = len(instruments)
        count_word = _get_count_word(n_instruments)
        intro = pick(INSTRUMENT_LIST_INTROS).format(count=count_word)
        instr_names = [_lowercase_instrument(i["instrument_name"]) for i in instruments]
        sentences.append(f"{intro}{_format_list(instr_names)}.")
    
    # ==========================================================================
    # DRUMS
    # ==========================================================================
    if has_drums and drums:
        drum_names = [_lowercase_drum(d["drum_name"]) for d in drums]
        intro = pick(DRUM_INTROS)
        sentences.append(f"{intro}{_format_list(drum_names)}.")
        
        # Predominant drum
        if pred_drum:
            drum_desc = pick(DRUM_PREDOMINANT_PHRASES).format(
                dominance=pred_drum.get("dominance_desc", "present")
            )
            sentences.append(_capitalize_first_word(drum_desc) + ".")
    
    # ==========================================================================
    # HARMONY
    # ==========================================================================
    if chords:
        chord_names = [_clean_chord_name(c["chord"]) for c in chords[:5]]
        intro = pick(CHORD_INTROS)
        sentences.append(f"{intro}{_format_list(chord_names)}.")
        
        # Progressions
        if progressions:
            prog_strings = [_clean_progression(p["progression"]) for p in progressions[:3]]
            prog_desc = pick(PROGRESSION_PHRASES).format(
                progressions=_format_list(prog_strings)
            )
            sentences.append(_capitalize_first_word(prog_desc) + ".")
        
        # Composition type
        if comp_type:
            comp_desc = pick(COMPOSITION_TYPE_PHRASES).format(comp_type=comp_type)
            sentences.append(_capitalize_first_word(comp_desc) + ".")
    
    # ==========================================================================
    # MUSICAL ELEMENTS
    # ==========================================================================
    if elements:
        elem_strings = []
        for elem in elements:
            for elem_name, count_desc in elem.items():
                formatted = _format_element(elem_name, count_desc)
                if formatted:
                    elem_strings.append(formatted)
        
        if elem_strings:
            intro = pick(ELEMENT_INTROS)
            sentences.append(f"{intro}{_format_list(elem_strings)}.")
    
    # ==========================================================================
    # MELODIES
    # ==========================================================================
    if lead_melodies:
        for melody in lead_melodies[:2]:
            instr = _lowercase_instrument(melody["instrument"])
            length = melody["note_count_desc"]
            length_article = _get_article(length)
            desc = pick(LEAD_MELODY_PHRASES).format(
                length=length,
                instrument=instr,
                article=length_article
            )
            sentences.append(desc + ".")
    
    if bass_melodies:
        lead_instr_names = set()
        if lead_melodies:
            lead_instr_names = {m["instrument"].lower() for m in lead_melodies}
        
        for melody in bass_melodies[:1]:
            if melody["instrument"].lower() not in lead_instr_names:
                instr = _lowercase_instrument(melody["instrument"])
                length = melody["note_count_desc"]
                length_article = _get_article(length)
                desc = pick(BASS_MELODY_PHRASES).format(
                    length=length,
                    instrument=instr,
                    article=length_article
                )
                sentences.append(desc + ".")
    
    # ==========================================================================
    # PREDOMINANT INSTRUMENT
    # ==========================================================================
    if pred_instr and opening_instr:
        pred_name = pred_instr.get("name", "none")
        opening_name = opening_instr.get("name", "none")
        
        if pred_name.lower() != opening_name.lower() and pred_name.lower() != "none":
            instr = _lowercase_instrument(pred_name)
            desc = pick(PREDOMINANT_INSTRUMENT_PHRASES).format(
                instrument=instr,
                dominance=pred_instr.get("dominance_desc", "present")
            )
            sentences.append(desc + ".")
    
    # ==========================================================================
    # COUNT-IN
    # ==========================================================================
    if count_in and has_count_in:
        count_in_article = _get_article(count_in)
        desc = pick(COUNT_IN_PHRASES).format(
            count_in=count_in,
            article=count_in_article
        )
        sentences.append(desc + ".")
    
    # ==========================================================================
    # FINAL: OPENING INSTRUMENT
    # ==========================================================================
    if opening_instr and opening_instr.get("name", "none").lower() != "none":
        instr = _lowercase_instrument(opening_instr["name"])
        
        if pred_instr and pred_instr.get("name", "none").lower() == opening_instr.get("name", "none").lower():
            desc = pick(OPENS_AND_PERFORMS_PHRASES).format(instrument=instr)
        else:
            desc = pick(OPENS_WITH_PHRASES).format(instrument=instr)
        
        sentences.append(desc + ".")
    
    # ==========================================================================
    # JOIN AND CLEAN UP
    # ==========================================================================
    # Join all sentences with space
    description = " ".join(sentences)
    
    # Ensure each sentence starts with capital letter
    # Split by period-space pattern and capitalize each sentence
    parts = description.split(". ")
    parts = [p.strip() for p in parts if p.strip()]
    parts = [_capitalize_first_word(p) for p in parts]
    description = ". ".join(parts)
    
    # Add final period if missing
    if not description.endswith("."):
        description += "."
    
    # Normalize whitespace (but preserve sentence structure)
    description = " ".join(description.split())
    
    # Final cleanup of any double periods
    while ".." in description:
        description = description.replace("..", ".")
    
    return description.strip()

###################################################################################

def generate_midi_captions(midi_file: str,
    deterministic: bool = True,
    seed: Optional[int] = None
) -> str:
    """
    Generate a detailed, poetic human-readable description of MIDI music.
    
    Parameters
    ----------
    midi_file : str
        Input MIDI file
    deterministic : bool
        If True, always generates the same description for the same inputs.
        If False, uses random filler word variations for diversity.
    seed : Optional[int]
        Random seed for reproducible non-deterministic output.
        Only used when deterministic=False.
    
    Returns
    -------
    str
        A detailed, poetic, and natural human-readable description.
    """
    
    if os.path.exists(midi_file):
        try:
            human_dict, numeric_dict = analyze_midi(midi_file)
            return generate_midi_description(human_dict,
                                             numeric_dict,
                                             deterministic=deterministic,
                                             seed=seed
                                             )
        
        except:
            return ''

    else:
        return ''

print('Module is loaded!')
print('Enjoy! :)')
print('=' * 70)

###################################################################################
# This is the end of the midicap Python module
###################################################################################