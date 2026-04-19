# representations.py

from typing import Any, Dict, List

def numeric_dict_to_tokenized_representation(numeric_dict: dict) -> list[int]:
    """
    Convert numeric_dict to a compact token sequence.
    
    Token vocabulary (256 tokens):
        0       : PAD
        1       : EOS (end of sequence)  
        2-49    : Field type headers (48 total)
        50-255  : Value tokens (context-dependent on preceding header)
    
    Encoding:
        - Scalar fields:    [HEADER, VALUE]
        - Lists:            [HEADER, LEN, VAL1, VAL2, ...]
        - Nested dicts:     [HEADER, VAL1, VAL2, ...] (fixed field order)
        - Continuous values: quantized to 0-63, offset by 50
        - Integer values:   direct value + 50
    """
    t = []
    O = 50  # Value offset

    def q(v, lo, hi):
        """Quantize float to 0-63 range, offset by O."""
        if hi <= lo:
            return O
        return int(max(0.0, min(1.0, (v - lo) / (hi - lo))) * 63) + O

    def v(x):
        """Encode integer value with offset."""
        return int(x) + O

    def clamp_v(x, mx=191):
        """Encode integer with upper clamp to stay in vocab."""
        return min(int(x), mx) + O

    # ── Field headers (2-49) ──────────────────────────────────────────────
    (F_SLEN, F_STYPE, F_GENRE, F_NTRK, F_NCH,
     F_INST, F_DRUM, F_DSET, F_DGRP, F_DGRPC,
     F_IFLG, F_KEY, F_SCL, F_TSIG,
     F_CHRD, F_CHCNT, F_NCR, F_DCT, F_CPRG,
     F_MOOD, F_RDEN, F_RCMP, F_TMP, F_TBPM,
     F_TONE, F_DYN, F_DRNG, F_AVL, F_VST,
     F_POLY, F_APOL, F_ADUR, F_NDENS,
     F_PMN, F_PMX, F_PRNG, F_AVP,
     F_ELEM, F_ECNT, F_LMEL, F_BMEL, F_AMEL,
     F_OINS, F_PINS, F_ODRM, F_PDRM,
     F_HCI, F_CIB) = range(2, 50)

    # ── Scalar fields ─────────────────────────────────────────────────────
    scalars = [
        (F_SLEN,  "song_len",               lambda x: q(x, 0, 10)),
        (F_STYPE, "song_type",               v),
        (F_GENRE, "genre",                   v),
        (F_NTRK,  "n_tracks",                lambda x: clamp_v(x)),
        (F_NCH,   "n_channels",              v),
        (F_KEY,   "key",                     v),
        (F_SCL,   "scale",                   v),
        (F_CHCNT, "chord_count",             lambda x: clamp_v(x)),
        (F_NCR,   "notes_chords_ratio",      lambda x: q(x, 0, 20)),
        (F_DCT,   "dominant_composition_type", v),
        (F_MOOD,  "mood",                    v),
        (F_RDEN,  "rhythm_density",          v),
        (F_RCMP,  "rhythmic_complexity",     v),
        (F_TMP,   "tempo",                   v),
        (F_TBPM,  "tempo_bpm",               lambda x: q(x, 40, 240)),
        (F_TONE,  "tone",                    v),
        (F_DYN,   "dynamics",                v),
        (F_DRNG,  "dynamic_range",           v),
        (F_AVL,   "avg_velocity",            lambda x: q(x, 0, 127)),
        (F_VST,   "velocity_std",            lambda x: q(x, 0, 50)),
        (F_POLY,  "polyphony",               v),
        (F_APOL,  "avg_polyphony_degree",    lambda x: q(x, 0, 16)),
        (F_ADUR,  "avg_note_duration_beats", lambda x: q(x, 0, 4)),
        (F_NDENS, "note_density_per_beat",   lambda x: q(x, 0, 25)),
        (F_PMN,   "pitch_min",               v),
        (F_PMX,   "pitch_max",               v),
        (F_PRNG,  "pitch_range",             v),
        (F_AVP,   "avg_pitch",               lambda x: q(x, 0, 127)),
        (F_AMEL,  "all_mono_melodies_count", lambda x: clamp_v(x, 95)),
        (F_HCI,   "has_count_in",            v),
        (F_CIB,   "count_in_beats",          lambda x: q(x, 0, 8)),
        (F_DGRPC, "drum_groups_count",       v),
    ]
    
    for hdr, key, enc in scalars:
        val = numeric_dict.get(key)
        if val is not None:
            t.extend([hdr, enc(val)])

    # ── Time signature (header + num + den) ───────────────────────────────
    ts_n, ts_d = numeric_dict.get("time_sig_num"), numeric_dict.get("time_sig_den")
    if ts_n is not None:
        t.extend([F_TSIG, v(ts_n), v(ts_d)])

    # ── Drum set (skip if -1 sentinel) ────────────────────────────────────
    ds = numeric_dict.get("drum_set")
    if ds is not None and ds >= 0:
        t.extend([F_DSET, v(ds)])

    # ── Instruments list ──────────────────────────────────────────────────
    insts = numeric_dict.get("instruments", [])
    if insts:
        t.append(F_INST)
        t.append(v(min(len(insts), 15)))
        for i in insts[:15]:
            t.extend([v(i["num"]), clamp_v(i["count"])])

    # ── Drums list ────────────────────────────────────────────────────────
    drums = numeric_dict.get("drums", [])
    if drums:
        t.append(F_DRUM)
        t.append(v(min(len(drums), 15)))
        for d in drums[:15]:
            t.append(v(d))

    # ── Drum groups list ──────────────────────────────────────────────────
    dgrps = numeric_dict.get("drum_groups", [])
    if dgrps:
        t.append(F_DGRP)
        t.append(v(min(len(dgrps), 15)))
        for g in dgrps[:15]:
            t.append(v(g["group_id"]))
            t.append(clamp_v(g["total_hits"]))
            note_ids = g.get("drum_note_ids", [])
            t.append(v(min(len(note_ids), 15)))
            for nid in note_ids[:15]:
                t.append(v(nid))

    # ── Instrument flags (fixed-order boolean sequence) ───────────────────
    flags = numeric_dict.get("instrument_flags", {})
    if flags:
        flag_keys = [
            'piano', 'chromatic_perc', 'organ', 'guitar', 'bass',
            'strings', 'ensemble', 'brass', 'reed', 'pipe',
            'synth_lead', 'synth_pad', 'synth_fx', 'synth',
            'ethnic', 'percussive', 'sfx', 'choir',
            'acoustic_piano', 'electric_piano', 'harpsichord',
            'acoustic_guitar', 'electric_guitar', 'distorted_guitar',
            'acoustic_bass', 'electric_bass', 'violin_family',
            'saxophone', 'flute', 'has_orchestral', 'piano_only',
            'acoustic_only', 'has_drums'
        ]
        t.append(F_IFLG)
        t.append(v(len(flag_keys)))
        for k in flag_keys:
            t.append(v(int(flags.get(k, False))))

    # ── Chords list ───────────────────────────────────────────────────────
    chords = numeric_dict.get("chords", [])
    if chords:
        t.append(F_CHRD)
        t.append(v(min(len(chords), 10)))
        for ch in chords[:10]:
            ctup = ch["chord"]
            t.append(v(len(ctup)))
            for c in ctup:
                t.append(v(c))
            t.append(clamp_v(ch["count"]))

    # ── Chord progressions list ───────────────────────────────────────────
    cprogs = numeric_dict.get("chord_progressions", [])
    if cprogs:
        t.append(F_CPRG)
        t.append(v(min(len(cprogs), 8)))
        for cp in cprogs[:8]:
            prog = cp["progression"]
            t.append(v(min(len(prog), 6)))
            for chord_tup in prog[:6]:
                t.append(v(len(chord_tup)))
                for c in chord_tup:
                    t.append(v(c))
            t.append(clamp_v(cp["count"]))

    # ── Elements list ─────────────────────────────────────────────────────
    elems = numeric_dict.get("elements", [])
    if elems:
        t.append(F_ELEM)
        t.append(v(min(len(elems), 9)))
        for e in elems[:9]:
            t.append(v(e))

    # ── Element counts dict ───────────────────────────────────────────────
    ecnts = numeric_dict.get("element_counts", {})
    if ecnts:
        elem_keys = ['arpeggio', 'trill', 'grace_note', 'glissando',
                     'tremolo', 'ostinato', 'syncopation', 'run', 'mordent']
        present = [(k, ecnts[k]) for k in elem_keys if k in ecnts]
        if present:
            t.append(F_ECNT)
            t.append(v(len(present)))
            for k, cnt in present:
                t.append(v(elem_keys.index(k)))
                t.append(clamp_v(cnt))

    # ── Lead melodies list ────────────────────────────────────────────────
    lmels = numeric_dict.get("lead_mono_melodies", [])
    if lmels:
        t.append(F_LMEL)
        t.append(v(min(len(lmels), 5)))
        for m in lmels[:5]:
            t.extend([v(m["instrument_num"]), v(m["channel"]),
                      clamp_v(m["note_count"]),
                      v(q(m["relative_length_beats"], 0, 100)),
                      v(q(m["relative_length_pct"], 0, 100)),
                      v(q(m["chord_pct"], 0, 10)),
                      v(q(m["overlap_pct"], 0, 100))])
            pitches = m.get("melody_pitches", [])
            t.append(v(min(len(pitches), 12)))
            for p in pitches[:12]:
                t.append(v(p))

    # ── Bass melodies list ────────────────────────────────────────────────
    bmels = numeric_dict.get("bass_mono_melodies", [])
    if bmels:
        t.append(F_BMEL)
        t.append(v(min(len(bmels), 5)))
        for m in bmels[:5]:
            t.extend([v(m["instrument_num"]), v(m["channel"]),
                      clamp_v(m["note_count"]),
                      v(q(m["relative_length_beats"], 0, 100)),
                      v(q(m["relative_length_pct"], 0, 100)),
                      v(q(m["chord_pct"], 0, 10)),
                      v(q(m["overlap_pct"], 0, 100))])
            pitches = m.get("melody_pitches", [])
            t.append(v(min(len(pitches), 12)))
            for p in pitches[:12]:
                t.append(v(p))

    # ── Opening instrument dict ───────────────────────────────────────────
    oins = numeric_dict.get("primary_opening_instrument")
    if oins and oins.get("patch", -1) >= 0:
        t.extend([F_OINS, v(oins["patch"]), v(oins["channel"])])

    # ── Predominant instrument dict ───────────────────────────────────────
    pins = numeric_dict.get("predominant_instrument")
    if pins and pins.get("patch", -1) >= 0:
        t.extend([F_PINS, v(pins["patch"]),
                  clamp_v(pins["note_count"]),
                  v(q(pins["dominance_pct"], 0, 100))])

    # ── Opening drum dict ─────────────────────────────────────────────────
    odrm = numeric_dict.get("primary_opening_drum")
    if odrm and odrm.get("note", -1) >= 0:
        t.extend([F_ODRM, v(odrm["note"]), v(odrm["group_id"])])

    # ── Predominant drum dict ─────────────────────────────────────────────
    pdrm = numeric_dict.get("predominant_drum")
    if pdrm and pdrm.get("note", -1) >= 0:
        t.extend([F_PDRM, v(pdrm["note"]), v(pdrm["group_id"]),
                  clamp_v(pdrm["hit_count"]),
                  v(q(pdrm["dominance_pct"], 0, 100))])

    t.append(1)  # EOS
    return t

def numeric_dict_to_feature_vector(numeric_dict: dict) -> list[float]:
    """
    Convert numeric_dict into a fixed-length 1D float vector.
    
    Total Length: 194 features.
    - Continuous values are min-max normalized to [0.0, 1.0].
    - Categorical integers are normalized to [0.0, 1.0] based on their known max ranges.
    - Variable lists (instruments, chords, etc.) are padded with 0.0 to fixed max lengths.
    - Missing keys gracefully default to 0.0.
    """
    vec: List[float] = []
    
    def norm(val: Any, min_v: float, max_v: float) -> float:
        """Safe min-max normalization to [0.0, 1.0]."""
        if val is None:
            return 0.0
        try:
            v = float(val)
        except (ValueError, TypeError):
            return 0.0
        if max_v == min_v:
            return 0.0
        return max(0.0, min(1.0, (v - min_v) / (max_v - min_v)))
    
    def get(key: str, default=None):
        return numeric_dict.get(key, default)

    # =====================================================================
    # 1. GLOBAL SCALARS (36 features)
    # =====================================================================
    vec.append(norm(get("song_len"), 0, 10))                     # 0: Duration (mins)
    vec.append(norm(get("song_type"), 0, 8))                     # 1: Song type token
    vec.append(norm(get("genre"), 0, 86))                        # 2: Genre token
    vec.append(norm(get("n_tracks"), 0, 50))                     # 3: Track count
    vec.append(norm(get("n_channels"), 0, 16))                   # 4: Channel count
    vec.append(norm(get("key"), 0, 11))                          # 5: Key root token
    vec.append(norm(get("scale"), 0, 1))                         # 6: Scale token (Major/Minor)
    vec.append(norm(get("time_sig_num"), 0, 16))                 # 7: Time sig numerator
    vec.append(norm(get("time_sig_den"), 0, 16))                 # 8: Time sig denominator
    vec.append(norm(get("chord_count"), 0, 500))                 # 9: Total chords
    vec.append(norm(get("notes_chords_ratio"), 0, 20))           # 10: Notes/Chords ratio
    vec.append(norm(get("dominant_composition_type"), 0, 1))     # 11: Chords vs Notes dominant
    vec.append(norm(get("mood"), 0, 14))                         # 12: Mood token
    vec.append(norm(get("rhythm_density"), 0, 4))                # 13: Rhythm density token
    vec.append(norm(get("rhythmic_complexity"), 0, 3))           # 14: Rhythmic complexity token
    vec.append(norm(get("tempo"), 0, 5))                         # 15: Tempo token
    vec.append(norm(get("tempo_bpm"), 40, 240))                  # 16: Exact BPM
    vec.append(norm(get("tone"), 0, 4))                          # 17: Average pitch token
    vec.append(norm(get("dynamics"), 0, 5))                      # 18: Dynamics token
    vec.append(norm(get("dynamic_range"), 0, 3))                 # 19: Dynamic range token
    vec.append(norm(get("avg_velocity"), 0, 127))                # 20: Average velocity
    vec.append(norm(get("velocity_std"), 0, 50))                 # 21: Velocity std deviation
    vec.append(norm(get("polyphony"), 0, 4))                     # 22: Polyphony token
    vec.append(norm(get("avg_polyphony_degree"), 0, 16))         # 23: Avg polyphony degree
    vec.append(norm(get("avg_note_duration_beats"), 0, 4))       # 24: Avg note duration
    vec.append(norm(get("note_density_per_beat"), 0, 25))        # 25: Note density
    vec.append(norm(get("pitch_min"), 0, 127))                   # 26: Min pitch
    vec.append(norm(get("pitch_max"), 0, 127))                   # 27: Max pitch
    vec.append(norm(get("pitch_range"), 0, 127))                 # 28: Pitch range
    vec.append(norm(get("avg_pitch"), 0, 127))                   # 29: Average pitch
    vec.append(norm(get("all_mono_melodies_count"), 0, 20))      # 30: Total melodies found
    vec.append(norm(get("has_count_in"), 0, 1))                  # 31: Count-in boolean
    vec.append(norm(get("count_in_beats"), 0, 8))                # 32: Count-in duration
    vec.append(norm(get("drum_set"), -1, 127))                   # 33: Drum set patch (-1 becomes 0)
    vec.append(norm(get("drum_groups_count"), 0, 24))            # 34: Drum groups used
    vec.append(0.0)                                              # 35: (Padding)

    # =====================================================================
    # 2. INSTRUMENT FLAGS (33 features)
    # =====================================================================
    flags = get("instrument_flags", {})
    flag_keys = [
        'piano', 'chromatic_perc', 'organ', 'guitar', 'bass',
        'strings', 'ensemble', 'brass', 'reed', 'pipe',
        'synth_lead', 'synth_pad', 'synth_fx', 'synth',
        'ethnic', 'percussive', 'sfx', 'choir',
        'acoustic_piano', 'electric_piano', 'harpsichord',
        'acoustic_guitar', 'electric_guitar', 'distorted_guitar',
        'acoustic_bass', 'electric_bass', 'violin_family',
        'saxophone', 'flute', 'has_orchestral', 'piano_only',
        'acoustic_only', 'has_drums'
    ]
    for k in flag_keys:
        vec.append(float(flags.get(k, 0)))                      # 36-68

    # =====================================================================
    # 3. TOP INSTRUMENTS (10 features) - Top 5 * (Patch, Count)
    # =====================================================================
    insts = get("instruments", [])[:5]
    for i in range(5):
        if i < len(insts):
            vec.append(norm(insts[i]["num"], 0, 127))
            vec.append(norm(insts[i]["count"], 0, 5000))
        else:
            vec.append(0.0)  # Patch
            vec.append(0.0)  # Count
    # Indices 69-78

    # =====================================================================
    # 4. TOP DRUMS (3 features) - Top 3 Note IDs
    # =====================================================================
    drums = get("drums", [])[:3]
    for i in range(3):
        vec.append(norm(drums[i], 0, 127) if i < len(drums) else 0.0)
    # Indices 79-81

    # =====================================================================
    # 5. TOP DRUM GROUPS (16 features) - Top 8 * (GroupID, TotalHits)
    # =====================================================================
    dgrps = get("drum_groups", [])[:8]
    for i in range(8):
        if i < len(dgrps):
            vec.append(norm(dgrps[i]["group_id"], 0, 24))
            vec.append(norm(dgrps[i]["total_hits"], 0, 5000))
        else:
            vec.append(0.0)  # Group ID
            vec.append(0.0)  # Total Hits
    # Indices 82-97

    # =====================================================================
    # 6. TOP CHORDS (15 features) - Top 5 * (Root, Quality, Count)
    # =====================================================================
    chords = get("chords", [])[:5]
    for i in range(5):
        if i < len(chords):
            ctup = chords[i]["chord"]
            root = ctup[0] if len(ctup) > 0 else 0
            qual = ctup[1] if len(ctup) > 1 else 0
            vec.append(norm(root, 0, 11))
            vec.append(norm(qual, 0, 16))
            vec.append(norm(chords[i]["count"], 0, 500))
        else:
            vec.extend([0.0, 0.0, 0.0])
    # Indices 98-112

    # =====================================================================
    # 7. TOP CHORD PROGRESSIONS (33 features) - Top 3 * (5 Chords * 2 values + Count)
    # =====================================================================
    cprogs = get("chord_progressions", [])[:3]
    for i in range(3):
        if i < len(cprogs):
            prog = cprogs[i]["progression"][:5]
            count = cprogs[i]["count"]
            # Flatten up to 5 chords (each is a tuple of root/quality)
            for j in range(5):
                if j < len(prog):
                    ctup = prog[j]
                    root = ctup[0] if len(ctup) > 0 else 0
                    qual = ctup[1] if len(ctup) > 1 else 0
                    vec.append(norm(root, 0, 11))
                    vec.append(norm(qual, 0, 16))
                else:
                    vec.extend([0.0, 0.0]) # Pad missing chords in progression
            vec.append(norm(count, 0, 100))
        else:
            # Pad entirely missing progressions with 11 zeros (10 chord vals + 1 count)
            vec.extend([0.0] * 11)
    # Indices 113-145

    # =====================================================================
    # 8. MUSICAL ELEMENTS HISTOGRAM (9 features)
    # =====================================================================
    # Reconstruct fixed-order histogram from the variable dict
    elem_keys = ['arpeggio', 'trill', 'grace_note', 'glissando',
                 'tremolo', 'ostinato', 'syncopation', 'run', 'mordent']
    ecnts = get("element_counts", {})
    for k in elem_keys:
        vec.append(norm(ecnts.get(k, 0), 0, 100))
    # Indices 146-154

    # =====================================================================
    # 9. TOP LEAD MELODIES (14 features) - Top 2 * 7 features
    # =====================================================================
    lmels = get("lead_mono_melodies", [])[:2]
    for i in range(2):
        if i < len(lmels):
            m = lmels[i]
            vec.extend([
                norm(m["instrument_num"], 0, 127),
                norm(m["channel"], 0, 15),
                norm(m["note_count"], 0, 2000),
                norm(m["relative_length_beats"], 0, 1000),
                norm(m["relative_length_pct"], 0, 100),
                norm(m["chord_pct"], 0, 10),
                norm(m["overlap_pct"], 0, 100)
            ])
        else:
            vec.extend([0.0] * 7)
    # Indices 155-168

    # =====================================================================
    # 10. TOP BASS MELODIES (14 features) - Top 2 * 7 features
    # =====================================================================
    bmels = get("bass_mono_melodies", [])[:2]
    for i in range(2):
        if i < len(bmels):
            m = bmels[i]
            vec.extend([
                norm(m["instrument_num"], 0, 127),
                norm(m["channel"], 0, 15),
                norm(m["note_count"], 0, 2000),
                norm(m["relative_length_beats"], 0, 1000),
                norm(m["relative_length_pct"], 0, 100),
                norm(m["chord_pct"], 0, 10),
                norm(m["overlap_pct"], 0, 100)
            ])
        else:
            vec.extend([0.0] * 7)
    # Indices 169-182

    # =====================================================================
    # 11. PRIMARY / PREDOMINANT INSTRUMENTS & DRUMS (12 features)
    # =====================================================================
    oins = get("primary_opening_instrument")
    vec.append(norm(oins["patch"], 0, 127) if oins and oins.get("patch", -1) >= 0 else 0.0)
    vec.append(norm(oins["channel"], 0, 15) if oins and oins.get("patch", -1) >= 0 else 0.0)
    
    pins = get("predominant_instrument")
    vec.append(norm(pins["patch"], 0, 127) if pins and pins.get("patch", -1) >= 0 else 0.0)
    vec.append(norm(pins["note_count"], 0, 5000) if pins and pins.get("patch", -1) >= 0 else 0.0)
    vec.append(norm(pins["dominance_pct"], 0, 100) if pins and pins.get("patch", -1) >= 0 else 0.0)
    
    odrm = get("primary_opening_drum")
    vec.append(norm(odrm["note"], 0, 127) if odrm and odrm.get("note", -1) >= 0 else 0.0)
    vec.append(norm(odrm["group_id"], 0, 24) if odrm and odrm.get("note", -1) >= 0 else 0.0)
    
    pdrm = get("predominant_drum")
    vec.append(norm(pdrm["note"], 0, 127) if pdrm and pdrm.get("note", -1) >= 0 else 0.0)
    vec.append(norm(pdrm["group_id"], 0, 24) if pdrm and pdrm.get("note", -1) >= 0 else 0.0)
    vec.append(norm(pdrm["hit_count"], 0, 5000) if pdrm and pdrm.get("note", -1) >= 0 else 0.0)
    vec.append(norm(pdrm["dominance_pct"], 0, 100) if pdrm and pdrm.get("note", -1) >= 0 else 0.0)
    # Indices 183-193

    # Sanity check (Optional, can be commented out in production)
    if len(vec) != 194:
        raise ValueError(f"Vector length mismatch! Expected 194, got {len(vec)}")

    return vec