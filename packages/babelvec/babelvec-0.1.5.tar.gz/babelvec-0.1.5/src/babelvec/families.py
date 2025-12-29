#!/usr/bin/env python3
"""
Language Family Assignment for Joint Multilingual Training

This module provides 100% hardcoded family assignments for all 355 Wikipedia languages,
optimized for joint embedding model training. Languages are grouped by script + linguistic
family to maximize subword sharing and transfer learning.

Background
----------
Joint training dramatically improves low-resource language performance (Phase 9-10 research):
- Moroccan Arabic (ary→ar): 0.26 → 0.79 R@1 (+205%)
- Egyptian Arabic (arz→ar): 0.61 → 0.96 R@1 (+59%)

However, joint training HURTS high-resource languages:
- Portuguese→Spanish: 0.98 → 0.50 R@1 (-49%)
- Italian→French: 0.94 → 0.21 R@1 (-78%)

The solution is linguistically-informed family groupings that maximize subword sharing
while keeping groups small enough to avoid vocabulary dilution.

Methodology
-----------
1. Started with Glottolog API for linguistic classification
2. Found issues: API returns 404 for common codes (ar, fa, zh), depth-1 too broad
3. Explored depth levels: depth-2 optimal but still problematic (Arabic grouped with Hebrew)
4. Final solution: 100% hardcoded with linguistically meaningful splits:
   - Arabic separate from other Semitic (Hebrew, Aramaic)
   - Romance split into iberian, galloitalic, eastern, creole
   - Germanic split into west_continental, west_anglofrisian, north
   - Slavic split into east, west, south
   - Large families (Austronesian, Bantu) split into regional subgroups

Phase 11 Empirical Validation (December 2025)
---------------------------------------------
Computed word/trigram Jaccard overlap for all 56,616 language pairs to validate groupings:

Suspicious groupings identified and fixed:
- lrc (Luri): ~0 overlap with Iranian family → separated to iranian_luri
- pih (Pitcairn): <0.01 overlap with Anglo-Frisian → separated to germanic_pitcairn  
- ak (Akan): <0.01 overlap with Kwa family → separated to atlantic_akan
- Indo-Aryan northern/western/hindustani: HIGH overlap (0.15-0.25) → merged to indoaryan_central

Key findings:
- Same-family word overlap: mean=0.063, std=0.040
- Different-family word overlap: mean=0.031, std=0.017
- Separation ratio: 2.01x (same-family has 2x higher overlap)
- Baseline R@1 is strongest predictor of joint training benefit (r=0.725)

Results: 100 family groups, max size 20, 80% of languages in groups of 3+.

Usage
-----
    from babelvec.families import (
        get_family_key,
        get_family_languages,
        assign_families,
        get_training_groups,
        HARDCODED_FAMILIES,
    )
    
    # Get family for a single language
    family = get_family_key("ary")  # -> "arabic"
    
    # Get all languages in a family
    langs = get_family_languages("arabic")  # -> ["ar", "ary", "arz"]
    
    # Assign all languages to families
    families = assign_families()  # -> {"romance_galloitalic": ["fr", "it", ...], ...}
    
    # Create training groups (hybrid strategy)
    groups = get_training_groups(languages, article_counts, low_resource_threshold=50000)
    # -> {"separate": ["en", "fr", ...], "joint": {"arabic": ["ary", "arz"]}}
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


__all__ = [
    "WIKIPEDIA_LANGUAGES",
    "HARDCODED_FAMILIES",
    "SCRIPT_OVERRIDES",
    "EXCLUDE_LANGUAGES",
    "normalize_name",
    "get_family_key",
    "get_family_languages",
    "get_language_info",
    "assign_families",
    "LanguageInfo",
]


# =============================================================================
# WIKIPEDIA LANGUAGES (355 total)
# =============================================================================

WIKIPEDIA_LANGUAGES = [
    "aa", "ab", "ace", "ady", "af", "ak", "alt", "am", "ami", "an", "ang", "ann", "anp", "ar",
    "arc", "ary", "arz", "as", "ast", "atj", "av", "avk", "awa", "ay", "az", "azb", "ba", "ban",
    "bar", "bbc", "bcl", "bdr", "be", "bew", "bg", "bh", "bi", "bjn", "blk", "bm", "bn", "bo",
    "bpy", "br", "bs", "btm", "bug", "bxr", "ca", "cbk", "cdo", "ce", "ceb", "ch", "cho", "chr",
    "chy", "ckb", "co", "cr", "crh", "cs", "csb", "cu", "cv", "cy", "da", "dag", "de", "dga",
    "din", "diq", "dsb", "dtp", "dty", "dv", "dz", "ee", "el", "eml", "en", "eo", "es", "et",
    "eu", "ext", "fa", "fat", "ff", "fi", "fj", "fo", "fon", "fr", "frp", "frr", "fur", "fy",
    "ga", "gag", "gan", "gcr", "gd", "gl", "glk", "gn", "gom", "gor", "got", "gpe", "gsw", "gu",
    "guc", "gur", "guw", "gv", "ha", "hak", "haw", "he", "hi", "hif", "ho", "hr", "hsb", "ht",
    "hu", "hy", "hyw", "hz", "ia", "ib", "id", "ie", "ig", "igl", "ii", "ik", "ilo", "inh", "io",
    "is", "it", "iu", "ja", "jam", "jbo", "jv", "ka", "kaa", "kab", "kbd", "kbp", "kcg", "kg",
    "kge", "ki", "kj", "kk", "kl", "km", "kn", "knc", "ko", "koi", "kr", "krc", "ks", "ksh",
    "ku", "kus", "kv", "kw", "ky", "la", "lad", "lb", "lbe", "lez", "lfn", "lg", "li", "lij",
    "lld", "lmo", "ln", "lo", "lrc", "lt", "ltg", "lv", "lzh", "mad", "mai", "map", "mdf", "mg",
    "mh", "mhr", "mi", "min", "mk", "ml", "mn", "mni", "mnw", "mos", "mr", "mrj", "ms", "mt",
    "mus", "mwl", "my", "myv", "mzn", "na", "nah", "nan", "nap", "nds", "ne", "new", "ng",
    "nia", "nl", "nn", "no", "nov", "nqo", "nr", "nrm", "nso", "nup", "nv", "ny", "oc", "olo",
    "om", "or", "os", "pa", "pag", "pam", "pap", "pcd", "pcm", "pdc", "pfl", "pi", "pih", "pl",
    "pms", "pnb", "pnt", "ps", "pt", "pwn", "qu", "rki", "rm", "rmy", "rn", "ro", "roa", "rsk",
    "ru", "rue", "rup", "rw", "sa", "sah", "sat", "sc", "scn", "sco", "sd", "se", "sg", "sgs",
    "sh", "shi", "shn", "si", "sim", "sk", "skr", "sl", "sm", "smn", "sn", "so", "sq", "sr",
    "srn", "ss", "st", "stq", "su", "sv", "sw", "syl", "szl", "szy", "ta", "tay", "tcy", "tdd",
    "te", "tet", "tg", "th", "ti", "tig", "tk", "tl", "tly", "tn", "to", "tok", "tpi", "tr",
    "trv", "ts", "tt", "tum", "tw", "ty", "tyv", "udm", "ug", "uk", "ur", "uz", "ve", "vec",
    "vep", "vi", "vls", "vo", "vro", "wa", "war", "wo", "wuu", "xal", "xh", "xmf", "yi", "yo",
    "yue", "za", "zea", "zgh", "zh", "zu",
]


# =============================================================================
# HARDCODED FAMILY ASSIGNMENTS
# 99 family definitions covering all 355 Wikipedia languages
# Format: family_name -> [language_codes]
# =============================================================================

HARDCODED_FAMILIES = {
    # ----- ROMANCE -----
    "romance_iberian": ["es", "pt", "gl", "ast", "ext", "mwl", "an"],
    "romance_galloitalic": [
        "fr", "oc", "ca", "frp", "wa", "pcd", "nrm", "pms", "lij", "lmo",
        "eml", "vec", "fur", "lld", "rm", "co", "scn", "nap", "sc", "it",
    ],
    "romance_eastern": ["ro", "rup"],
    "romance_creole": ["ht", "pap", "cbk", "gcr"],
    "romance_other": ["la", "roa"],

    # ----- GERMANIC -----
    "germanic_west_continental": [
        "de", "lb", "gsw", "bar", "pdc", "pfl", "ksh", "li", "stq", "nds", "yi", "nl", "vls", "zea",
    ],
    # Note: pih (Pitcairn) has very low overlap (<0.01 word Jaccard) with other
    # Anglo-Frisian languages in empirical analysis. It's a creole with limited data.
    "germanic_west_anglofrisian": [
        "en", "sco", "frr", "fy", "af", "jam", "gpe", "pcm", "tpi", "bi", "srn",
    ],
    "germanic_pitcairn": ["pih"],  # Isolated - tiny corpus, low overlap with family
    "germanic_north": ["da", "sv", "no", "nn", "is", "fo"],
    "germanic_historical": ["ang", "got"],

    # ----- SLAVIC -----
    "slavic_east": ["ru", "uk", "be", "rue"],
    "slavic_west": ["pl", "cs", "sk", "csb", "szl", "hsb", "dsb"],
    "slavic_south": ["sr", "hr", "bs", "sl", "mk", "bg", "sh", "rsk"],
    "slavic_historical": ["cu"],

    # ----- BALTIC -----
    "baltic": ["lt", "ltg", "lv", "sgs"],

    # ----- INDO-ARYAN -----
    # Note: Empirical analysis (Phase 11) showed HIGH cross-family overlap between
    # northern/western/hindustani subfamilies (0.15-0.25 word Jaccard). These share
    # Devanagari script and have significant vocabulary overlap. Merged for joint training.
    "indoaryan_central": [
        "hi", "ur",  # Hindustani
        "ne", "mai", "bh", "anp", "awa", "dty", "gom", "sa", "pi",  # Northern
        "gu", "mr", "pa", "pnb", "sd", "skr", "ks",  # Western
    ],
    "indoaryan_eastern": ["bn", "as", "bpy", "or", "syl"],
    "indoaryan_insular": ["si", "dv"],
    "indoaryan_romani": ["rmy"],
    "indoaryan_fiji": ["hif"],

    # ----- IRANIAN -----
    # Note: lrc (Luri) uses a different script and has ~0 overlap with other Iranian
    # languages in empirical analysis (Phase 11). Separated to avoid hurting alignment.
    "iranian_western": ["fa", "ku", "ckb", "glk", "mzn", "tly", "tg"],
    "iranian_eastern": ["ps", "os"],
    "iranian_luri": ["lrc"],  # Isolated - different script, no overlap with family
    "iranian_other": ["diq"],

    # ----- ARABIC -----
    "arabic": ["ar", "ary", "arz"],

    # ----- OTHER SEMITIC -----
    "semitic_ethiopic": ["am", "ti", "tig"],
    "semitic_hebrew": ["he", "lad"],
    "semitic_aramaic": ["arc"],
    "semitic_maltese": ["mt"],

    # ----- BERBER -----
    "berber": ["kab", "shi", "zgh"],

    # ----- CUSHITIC -----
    "cushitic": ["aa", "so", "om"],

    # ----- CHADIC -----
    "chadic": ["ha"],

    # ----- TURKIC -----
    "turkic_oghuz": ["tr", "az", "azb", "tk", "gag"],
    "turkic_kipchak": ["kk", "ky", "tt", "ba", "krc", "kaa", "crh"],
    "turkic_siberian": ["sah", "tyv", "alt"],
    "turkic_other": ["cv", "uz", "ug"],

    # ----- SINITIC -----
    "sinitic_mandarin": ["zh", "gan"],
    "sinitic_other": ["yue", "wuu", "nan", "hak", "cdo", "lzh"],

    # ----- JAPONIC/KOREANIC -----
    "japonic": ["ja"],
    "koreanic": ["ko"],

    # ----- CELTIC -----
    "celtic_goidelic": ["ga", "gd", "gv"],
    "celtic_brythonic": ["cy", "br", "kw"],

    # ----- URALIC -----
    "uralic_finnic": ["fi", "et", "vep", "vro", "olo"],
    "uralic_saami": ["se", "smn"],
    "uralic_ugric": ["hu"],
    "uralic_permian": ["kv", "koi", "udm"],
    "uralic_volgaic": ["mhr", "mrj", "mdf", "myv"],

    # ----- GREEK -----
    "greek": ["el", "pnt"],

    # ----- ARMENIAN -----
    "armenian": ["hy", "hyw"],

    # ----- ALBANIAN -----
    "albanian": ["sq"],

    # ----- KARTVELIAN -----
    "kartvelian": ["ka", "xmf"],

    # ----- BASQUE -----
    "basque": ["eu"],

    # ----- TAI-KADAI -----
    "taikadai_southwestern": ["th", "lo"],
    "taikadai_other": ["za", "shn", "tdd"],

    # ----- AUSTROASIATIC -----
    "austroasiatic_vietic": ["vi"],
    "austroasiatic_khmer": ["km"],
    "austroasiatic_other": ["mnw", "sat"],

    # ----- DRAVIDIAN -----
    "dravidian_south": ["ta", "ml", "kn", "tcy"],
    "dravidian_south_central": ["te"],

    # ----- MONGOLIC -----
    "mongolic": ["mn", "bxr", "xal"],

    # ----- TIBETO-BURMAN -----
    "tibetoburman_tibetic": ["bo", "dz"],
    "tibetoburman_burmese": ["my", "rki"],
    "tibetoburman_other": ["ii", "mni", "new", "blk"],

    # ----- AUSTRONESIAN - PHILIPPINE -----
    "austronesian_philippine_central": ["tl", "ceb", "bcl", "war"],
    "austronesian_philippine_northern": ["ilo", "pag", "pam"],

    # ----- AUSTRONESIAN - MALAY -----
    "austronesian_malay": ["id", "ms", "min", "bjn", "bew", "ace"],

    # ----- AUSTRONESIAN - OCEANIC -----
    "austronesian_polynesian": ["haw", "mi", "sm", "to", "ty"],
    "austronesian_oceanic_other": ["fj", "mh", "na", "ch"],

    # ----- AUSTRONESIAN - OTHER -----
    "austronesian_javanese": ["jv", "su"],
    "austronesian_batak": ["bbc", "btm"],
    "austronesian_sulawesi": ["bug", "gor"],
    "austronesian_malagasy": ["mg"],
    "austronesian_formosan": ["ami", "szy", "tay", "trv", "pwn"],
    "austronesian_other": ["ban", "bdr", "dtp", "kge", "mad", "nia", "tet", "map"],

    # ----- ATLANTIC-CONGO - BANTU -----
    "bantu_southern": ["zu", "xh", "ss", "nr", "ts", "ve", "tn", "st", "nso"],
    "bantu_eastern": ["sw", "rw", "rn", "lg", "ny", "sn", "tum"],
    "bantu_central": ["kg", "ln", "ki", "kj", "ng", "hz"],

    # ----- ATLANTIC-CONGO - WEST AFRICAN -----
    "atlantic_yoruba_igbo": ["yo", "ig", "igl"],
    "atlantic_gur": ["dag", "dga", "gur", "kbp", "kus", "mos", "sg"],
    # Note: ak (Akan) has very low overlap (<0.01 word Jaccard) with other Kwa
    # languages in empirical analysis. Only 105 chars of data available.
    "atlantic_kwa": ["ee", "fat", "fon", "guw", "tw"],
    "atlantic_akan": ["ak"],  # Isolated - tiny corpus (105 chars), no overlap
    "atlantic_other": ["ff", "wo", "bm", "ann", "kcg", "nup"],

    # ----- CONSTRUCTED -----
    "constructed_auxlang": ["eo", "io", "ia", "ie", "vo", "nov", "lfn", "tok"],
    "constructed_other": ["jbo", "nqo", "avk"],

    # ----- CAUCASIAN -----
    "caucasian_northwest": ["ab", "ady", "kbd"],
    "caucasian_northeast": ["ce", "inh", "av", "lbe", "lez"],

    # ----- ESKIMO-ALEUT -----
    "eskimoaleut": ["iu", "ik", "kl"],

    # ----- NATIVE AMERICAN -----
    "american_algonquian": ["atj", "chy", "cr"],
    "american_muskogean": ["cho", "mus"],
    "american_athabaskan": ["nv"],
    "american_iroquoian": ["chr"],
    "american_quechua": ["qu"],
    "american_aymara": ["ay"],
    "american_guarani": ["gn"],
    "american_nahuatl": ["nah"],
    "american_arawak": ["guc"],

    # ----- AFRICAN ISOLATES/OTHER -----
    "african_saharan": ["kr", "knc"],
    "african_nilotic": ["din"],

    # ----- OTHER -----
    "pidgin_hiri": ["ho"],
    "papuan_sepik": ["sim"],
}


# =============================================================================
# SCRIPT OVERRIDES (for languages with ambiguous/mixed script detection)
# =============================================================================

SCRIPT_OVERRIDES = {
    "aa": "latn",    # Afar
    "cbk": "latn",   # Chavacano
    "gsw": "latn",   # Swiss German
    "hz": "latn",    # Herero
    "ib": "latn",    # Invalid code
    "ja": "jpan",    # Japanese (Kanji+Kana)
    "kr": "latn",    # Kanuri
    "lzh": "hani",   # Classical Chinese
    "map": "latn",   # Macro code
    "na": "latn",    # Nauru
    "nan": "hani",   # Min Nan Chinese
    "nds": "latn",   # Low German
    "ne": "deva",    # Nepali
    "new": "deva",   # Newari
    "roa": "latn",   # Macro code
    "rup": "latn",   # Aromanian
    "sgs": "latn",   # Samogitian
    "sim": "latn",   # Mende (Papua New Guinea)
    "vro": "latn",   # Võro
    "yue": "hani",   # Cantonese
}

# Languages to exclude from training (invalid/problematic codes)
EXCLUDE_LANGUAGES = {"ib"}


# =============================================================================
# INTERNAL: Build reverse lookup tables
# =============================================================================

def _build_lookup_tables():
    """Build reverse lookup: lang_code -> family_key."""
    lang_to_family = {}
    seen = set()
    
    for family_key, langs in HARDCODED_FAMILIES.items():
        for lang in langs:
            if lang not in seen and lang in WIKIPEDIA_LANGUAGES:
                lang_to_family[lang] = family_key
                seen.add(lang)
    
    return lang_to_family, seen


_LANG_TO_FAMILY, _COVERED_LANGS = _build_lookup_tables()


# =============================================================================
# NORMALIZATION
# =============================================================================

def normalize_name(name: str) -> str:
    """Normalize family/branch/script names to lowercase_with_underscores."""
    if not name:
        return "unknown"
    name = name.lower()
    name = re.sub(r"[\s\-\(\)]+", "_", name)
    name = re.sub(r"['\"]", "", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_") or "unknown"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class LanguageInfo:
    """Complete family information for a language."""
    code: str
    script: str
    family_key: str
    
    @property
    def is_excluded(self) -> bool:
        return self.code in EXCLUDE_LANGUAGES
    
    @property
    def is_covered(self) -> bool:
        return self.code in _COVERED_LANGS


# =============================================================================
# PUBLIC API
# =============================================================================

def get_family_key(lang_code: str) -> Optional[str]:
    """
    Get the family key for a language.
    
    Args:
        lang_code: Wikipedia language code (e.g., "fr", "ary", "zh")
        
    Returns:
        Family key (e.g., "romance_galloitalic", "arabic", "sinitic_mandarin")
        or None if language is excluded or not found
        
    Example:
        >>> get_family_key("fr")
        'romance_galloitalic'
        >>> get_family_key("ary")
        'arabic'
    """
    if lang_code in EXCLUDE_LANGUAGES:
        return None
    return _LANG_TO_FAMILY.get(lang_code)


def get_family_languages(family_key: str) -> list[str]:
    """
    Get all languages in a family group.
    
    Args:
        family_key: Family key (e.g., "arabic", "romance_galloitalic")
        
    Returns:
        List of language codes in the family, or empty list if not found
        
    Example:
        >>> get_family_languages("arabic")
        ['ar', 'ary', 'arz']
    """
    return HARDCODED_FAMILIES.get(family_key, [])


def get_language_info(lang_code: str) -> LanguageInfo:
    """
    Get complete family information for a language.
    
    Args:
        lang_code: Wikipedia language code
        
    Returns:
        LanguageInfo dataclass with code, script, and family_key
        
    Example:
        >>> info = get_language_info("fr")
        >>> info.family_key
        'romance_galloitalic'
        >>> info.script
        'latn'
    """
    family_key = _LANG_TO_FAMILY.get(lang_code, "unknown")
    script = SCRIPT_OVERRIDES.get(lang_code, "unknown")
    
    return LanguageInfo(
        code=lang_code,
        script=script,
        family_key=family_key,
    )


def assign_families(
    languages: Optional[list[str]] = None,
) -> dict[str, list[str]]:
    """
    Assign languages to family groups.
    
    Args:
        languages: List of language codes to assign. If None, uses all Wikipedia languages.
        
    Returns:
        Dict mapping family_key -> list of language codes
        
    Example:
        >>> families = assign_families(["en", "fr", "ar", "ary"])
        >>> families
        {
            'germanic_west_anglofrisian': ['en'],
            'romance_galloitalic': ['fr'],
            'arabic': ['ar', 'ary']
        }
    """
    if languages is None:
        languages = WIKIPEDIA_LANGUAGES
    
    families = defaultdict(list)
    
    for lang in languages:
        if lang in EXCLUDE_LANGUAGES:
            continue
        
        family_key = _LANG_TO_FAMILY.get(lang)
        if family_key:
            families[family_key].append(lang)
    
    return dict(families)


def get_training_groups(
    languages: Optional[list[str]] = None,
    article_counts: Optional[dict[str, int]] = None,
    low_resource_threshold: int = 50000,
) -> dict[str, list[str] | dict[str, list[str]]]:
    """
    Create training groups based on hybrid strategy.
    
    High-resource languages (>= threshold articles) are trained separately.
    Low-resource languages are trained jointly with their family if a
    high-resource relative exists.
    
    Args:
        languages: List of language codes. If None, uses all Wikipedia languages.
        article_counts: Dict mapping lang_code -> article count. If None, all
                       languages are treated as low-resource (joint training).
        low_resource_threshold: Article count threshold for high-resource (default 50k)
        
    Returns:
        {
            "separate": ["en", "fr", "de", ...],  # Train individually
            "joint": {
                "arabic": ["ar", "ary", "arz"],   # Train together
                ...
            }
        }
        
    Example:
        >>> counts = {"en": 6000000, "ar": 840000, "ary": 170000, "arz": 500000}
        >>> groups = get_training_groups(["en", "ar", "ary", "arz"], counts)
        >>> groups["separate"]
        ['en', 'ar']
        >>> groups["joint"]
        {'arabic': ['ary', 'arz']}
    """
    if languages is None:
        languages = WIKIPEDIA_LANGUAGES
    if article_counts is None:
        article_counts = {}
    
    families = assign_families(languages)
    
    # Find high-resource languages per family
    family_high_resource = defaultdict(list)
    for family_key, langs in families.items():
        for lang in langs:
            if article_counts.get(lang, 0) >= low_resource_threshold:
                family_high_resource[family_key].append(lang)
    
    separate = []
    joint = defaultdict(list)
    
    for lang in languages:
        if lang in EXCLUDE_LANGUAGES:
            continue
        
        count = article_counts.get(lang, 0)
        family_key = _LANG_TO_FAMILY.get(lang)
        
        if not family_key:
            # Unknown family - train separately
            separate.append(lang)
        elif count >= low_resource_threshold:
            # High-resource - train separately
            separate.append(lang)
        elif family_high_resource.get(family_key):
            # Low-resource with high-resource relative - train jointly
            joint[family_key].append(lang)
        else:
            # Low-resource isolate (no high-resource relative) - train separately
            separate.append(lang)
    
    return {
        "separate": separate,
        "joint": dict(joint),
    }


# =============================================================================
# STATISTICS
# =============================================================================

def get_statistics() -> dict:
    """
    Get statistics about the family assignments.
    
    Returns:
        Dict with coverage and distribution statistics
    """
    families = assign_families()
    sizes = [len(v) for v in families.values()]
    
    return {
        "total_languages": len(WIKIPEDIA_LANGUAGES),
        "covered_languages": len(_COVERED_LANGS),
        "excluded_languages": len(EXCLUDE_LANGUAGES),
        "total_families": len(families),
        "family_sizes": {
            "min": min(sizes),
            "max": max(sizes),
            "mean": sum(sizes) / len(sizes),
            "singletons": sum(1 for s in sizes if s == 1),
        },
        "languages_in_groups_3plus": sum(s for s in sizes if s >= 3),
        "languages_in_groups_5plus": sum(s for s in sizes if s >= 5),
    }


# =============================================================================
# CLI / MAIN
# =============================================================================

if __name__ == "__main__":
    stats = get_statistics()
    
    print("BabelVec Language Family Assignments")
    print("=" * 60)
    print(f"Total Wikipedia languages: {stats['total_languages']}")
    print(f"Covered by hardcoded families: {stats['covered_languages']}")
    print(f"Excluded: {stats['excluded_languages']}")
    print(f"Total family groups: {stats['total_families']}")
    print()
    print("Family size distribution:")
    print(f"  Min: {stats['family_sizes']['min']}")
    print(f"  Max: {stats['family_sizes']['max']}")
    print(f"  Mean: {stats['family_sizes']['mean']:.1f}")
    print(f"  Singletons: {stats['family_sizes']['singletons']}")
    print()
    print(f"Languages in groups of 3+: {stats['languages_in_groups_3plus']}")
    print(f"Languages in groups of 5+: {stats['languages_in_groups_5plus']}")
    print()
    print("Sample lookups:")
    for lang in ["en", "fr", "ar", "ary", "zh", "ja", "sw"]:
        family = get_family_key(lang)
        print(f"  {lang}: {family}")
