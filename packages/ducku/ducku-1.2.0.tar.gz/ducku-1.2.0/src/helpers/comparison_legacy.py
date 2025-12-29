from difflib import SequenceMatcher
import re
from typing import List
from rapidfuzz.distance import Levenshtein
from src.helpers.logger import get_logger
logger = get_logger(__name__)

def normalize_string(s):
    s = s.lower()
    # Remove numbered list prefixes (e.g., "1. ", "2. ", "3. ") - MUST be done FIRST
    s = re.sub(r'^\d+\.\s*', '', s)
    # Remove bullet point prefixes (e.g., "* ", "- ")
    s = re.sub(r'^[\*\-]\s+', '', s)
    # Then normalize separators and remove special characters
    s = re.sub(r'[\-_ ]+', ' ', s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# levenshtein distnace related normalized string lengths [0, 1]
def normalized_levenshtein(s1, s2):
    d = Levenshtein.distance(s1, s2)
    return 1 - d / max(len(s1), len(s2))

# @TODO it became crazy mess. Plan:
# 1. Tokenize
# 2. Weighted Jaccard
def fuzzy_intersection(a_orig: List[str], b_orig: List[str], debug: bool = False):
    """Check if two lists have fuzzy intersection and return match details.
    
    Returns:
        None if no significant intersection found
        dict with keys: 'matched_a', 'matched_b', 'only_a', 'only_b' if intersection found
    """
    logger.debug("Fuzzy intersection check between lists: %s AND %s %d %d", a_orig, b_orig, len(a_orig), len(b_orig))
    
    # Normalize for comparison but keep track of originals
    a_normalized = [normalize_string(s) for s in a_orig]
    b_normalized = [normalize_string(s) for s in b_orig]
    
    if len(a_orig) < 3 or len(b_orig) < 3: # too short lists to make any decisions
        return None if not debug else False

    # Create unique normalized -> original mapping
    a_map = {}
    for orig, norm in zip(a_orig, a_normalized):
        if norm not in a_map:
            a_map[norm] = orig
    
    b_map = {}
    for orig, norm in zip(b_orig, b_normalized):
        if norm not in b_map:
            b_map[norm] = orig
    
    a_unique = list(a_map.keys())
    b_unique = list(b_map.keys())
    
    comparable = len(a_unique)/len(b_unique) if len(a_unique) < len(b_unique) else len(b_unique)/len(a_unique)
    logger.debug("Comparable: %s", comparable)
    if comparable < 0.3: # lists are too different
        return None if not debug else False
    
    avg_len = (len(a_unique) + len(b_unique)) / 2
    logger.debug("avg_len %s", avg_len)
    
    # Track matches with original strings
    matched_a = set()
    matched_b = set()
    used_b = set()  # prevent matching the same B token to multiple A tokens
    
    # Greedy best-match selection: for each A token, choose highest-similarity unused B token
    for s1_norm in a_unique:
        best_b = None
        best_score = 0.0
        for s2_norm in b_unique:
            if s2_norm in used_b:
                continue
            if not s1_norm or not s2_norm:
                continue
            nl = hybrid_similarity(s1_norm, s2_norm)
            logger.debug("%s < === > %s :: %s", s1_norm, s2_norm, nl)
            if nl > best_score:
                best_score = nl
                best_b = s2_norm
        if best_b is not None and best_score >= 0.5:
            logger.debug("Best match: %s <==> %s (%s)", s1_norm, best_b, best_score)
            matched_a.add(a_map[s1_norm])
            matched_b.add(b_map[best_b])
            used_b.add(best_b)

    # Require at least 2 actual matches (not just percentage)
    if len(matched_a) < 3:
        return None if not debug else False
    
    ni = len(matched_a) / avg_len # normalize against length
    logger.debug("matches %d", len(matched_a))
    logger.debug("matches / avg_len %s", ni)
    
    # Require significant overlap - 50% is reasonable for partial lists
    if ni < 0.5:
        return None if not debug else False
    
    # Return match details
    only_a = [s for s in a_orig if s not in matched_a]
    only_b = [s for s in b_orig if s not in matched_b]
    
    result = {
        'matched_a': sorted(matched_a),
        'matched_b': sorted(matched_b),
        'only_a': sorted(only_a),
        'only_b': sorted(only_b)
    }
    # Backward compatibility: when debug=True (legacy tests), return boolean
    return True if debug else result





#========================
NOISE = {"alpha", "beta", "and", "or", "a", "the", "of", "in", "on", "for", "with", "to", "is", "are", "by", "an", "this", "that", "it", "as", "at", "from", "but", "not", "be", "was", "were", "which"}

def tokenize(s):
    return [t for t in normalize_string(s).split() if t not in NOISE]

def fuzzy(a, b):
    return SequenceMatcher(None, normalize_string(a), normalize_string(b)).ratio()

def token_similarity(a, b):
    ta = tokenize(a)
    tb = tokenize(b)
    if not ta or not tb:
        return 0
    overlaps = 0
    # Count token overlaps only when tokens are EXACT matches
    # or share a strong common PREFIX (>= 80% of the shorter token).
    # Middle/end substrings do not count.
    def has_long_prefix_match(x: str, y: str) -> bool:
        if len(x) < 2 or len(y) < 2:
            return False
        # Consider a prefix match only if the longest common prefix
        # covers >= 80% of the SHORTER token and starts at position 0.
        # This allows 'user' vs 'users' and 'spell' vs 'spellcheck',
        # but rejects mid-word coincidences like 'try' in 'registry' vs 'entry'.
        if not x or not y:
            return False
        # Compute longest common prefix length, considering only alphanumeric chars
        # Strip to alphanumeric + underscore/hyphen/slash to avoid matching on special chars
        x_clean = ''.join(c for c in x if c.isalnum() or c in '_-/')
        y_clean = ''.join(c for c in y if c.isalnum() or c in '_-/')
        
        lcp = 0
        for cx, cy in zip(x_clean, y_clean):
            if cx == cy:
                lcp += 1
            else:
                break
        
        # Require at least 3 characters in common prefix to avoid "py" matching "pycache"
        if lcp < 3:
            return False
            
        return (lcp / min(len(x_clean), len(y_clean))) >= 0.8

    for x in ta:
        for y in tb:
            # Skip tokens shorter than 2 characters
            if len(x) < 2 or len(y) < 2:
                continue
            if x == y:
                overlaps += 1
            elif has_long_prefix_match(x, y):
                overlaps += 1

    # Note: we intentionally avoid composite or suffix-based matching for simplicity
    # and performance. We only consider beginning-anchored matches.

    base = overlaps / max(len(ta), len(tb))

    # Front-loaded positional weighting: reward exact leading-token matches
    # Only apply when tokens are identical AND sufficiently long (>5 chars)
    first_match_bonus = 0.0
    if ta and tb:
        if ta[0] == tb[0] and len(ta[0]) > 5:
            first_match_bonus += 0.2  # modest boost for strong, exact leading-token match
        elif len(tb) > 1 and ta[0] == tb[1] and len(ta[0]) > 5:
            first_match_bonus += 0.05  # minimal boost if leading token of A matches second of B exactly

    # Apply positional bonus only when base similarity is low
    adjusted = base + (first_match_bonus if base <= 0.5 else 0.0)
    # Cap total similarity at 1.0
    return min(1.0, adjusted)

def hybrid_similarity(a, b, debug=False):
    def log(*args):
        if debug:
            logger.debug(" ".join(str(a) for a in args))
    
    ts = token_similarity(a, b)
    log(f"Token similarity for '{a}' vs '{b}': {ts}")
    if ts > 0:
        log(f"Using token similarity: {ts}")
        return ts
    # Fallback to fuzzy, but only if there is a strong common PREFIX
    # Require LCP to cover at least 50% of the longer token to allow cases like
    # 'test' vs 'testing', while still rejecting weak beginnings like 'con' in
    # 'configuration' vs 'contributing'. Mid-word coincidences are already blocked.
    s1 = normalize_string(a)
    s2 = normalize_string(b)
    lcp = 0
    for cx, cy in zip(s1, s2):
        if cx == cy:
            lcp += 1
        else:
            break
    max_len = max(len(s1), len(s2)) if max(len(s1), len(s2)) > 0 else 1
    lcp_ratio = lcp / max_len
    if lcp_ratio < 0.5:
        # Allow high overall similarity when the first 2+ chars match
        # and normalized Levenshtein indicates very close strings (>= 0.8),
        # e.g., 'apple' vs 'aple'. Otherwise suppress fuzzy.
        nl = normalized_levenshtein(s1, s2)
        if not (nl >= 0.8 and lcp >= 2):
            log("Weak or no common prefix; suppressing fuzzy match.")
            return 0.0
    f = fuzzy(a, b)
    log(f"Using fuzzy similarity with prefix present: {f}")
    return f