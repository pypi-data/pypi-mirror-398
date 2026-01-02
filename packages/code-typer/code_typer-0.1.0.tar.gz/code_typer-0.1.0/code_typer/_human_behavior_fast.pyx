# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
"""
Cython-optimized functions for human behavior simulation.

These functions are called frequently during typing simulation
and benefit from C-level performance.
"""

from libc.stdlib cimport rand, RAND_MAX
from libc.math cimport exp, log
import cython


# Character difficulty lookup (pre-computed)
cdef dict CHAR_DIFFICULTY = {
    ord(c): 0.8 for c in "etaoinsrhldcumwfgypbvkjxqz"
}
CHAR_DIFFICULTY.update({
    ord(c): 1.0 for c in "ETAOINSRHLDCUMWFGYPBVKJXQZ0123456789"
})
CHAR_DIFFICULTY.update({
    ord(c): 1.5 for c in "!@#$%^&*()_+-=[]{}|;':\",./<>?`~\\"
})
CHAR_DIFFICULTY[ord(' ')] = 0.6
CHAR_DIFFICULTY[ord('\n')] = 0.3
CHAR_DIFFICULTY[ord('\t')] = 0.5


# Nearby keys for typo generation
cdef dict NEARBY_KEYS = {
    ord('a'): b'sqwz', ord('b'): b'vghn', ord('c'): b'xdfv', ord('d'): b'erfcxs',
    ord('e'): b'wrsdf', ord('f'): b'rtgvcd', ord('g'): b'tyhbvf', ord('h'): b'yujnbg',
    ord('i'): b'uojkl', ord('j'): b'uikmnh', ord('k'): b'ioljm', ord('l'): b'opk',
    ord('m'): b'njk', ord('n'): b'bhjm', ord('o'): b'ipkl', ord('p'): b'ol',
    ord('q'): b'wa', ord('r'): b'edft', ord('s'): b'awedxz', ord('t'): b'rfgy',
    ord('u'): b'yihj', ord('v'): b'cfgb', ord('w'): b'qase', ord('x'): b'zsdc',
    ord('y'): b'tghu', ord('z'): b'asx',
}


cdef inline double random_double() noexcept nogil:
    """Generate a random double between 0 and 1."""
    return <double>rand() / <double>RAND_MAX


cdef inline double gauss(double mu, double sigma) noexcept nogil:
    """Generate a Gaussian-distributed random number using Box-Muller."""
    cdef double u1, u2, z0
    u1 = random_double()
    u2 = random_double()
    # Avoid log(0)
    if u1 < 1e-10:
        u1 = 1e-10
    z0 = (-2.0 * log(u1)) ** 0.5 * cos(2.0 * 3.14159265358979323846 * u2)
    return mu + sigma * z0


cdef extern from "math.h":
    double cos(double x) nogil


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef double calculate_delay_fast(
    str char,
    str prev_char,
    bint in_pattern,
    double speed,
    double base_delay,
    double min_delay,
    double max_delay
):
    """Calculate typing delay for a character.

    Args:
        char: Current character
        prev_char: Previous character (empty string if none)
        in_pattern: Whether we're in a recognized pattern
        speed: Speed multiplier
        base_delay: Base delay in seconds
        min_delay: Minimum delay
        max_delay: Maximum delay

    Returns:
        Delay in seconds before typing this character
    """
    cdef:
        double delay
        double difficulty
        double variation
        int char_ord = ord(char[0]) if len(char) > 0 else 0
        int prev_ord = ord(prev_char[0]) if len(prev_char) > 0 else 0

    # Base delay adjusted for speed
    delay = base_delay / speed

    # Adjust for character difficulty
    difficulty = CHAR_DIFFICULTY.get(char_ord, 1.0)
    delay *= difficulty

    # Patterns are typed faster (muscle memory)
    if in_pattern:
        delay *= 0.6

    # Add variation (humans aren't perfectly consistent)
    variation = gauss(1.0, 0.15)
    if variation < 0.5:
        variation = 0.5
    elif variation > 1.5:
        variation = 1.5
    delay *= variation

    # Special pauses
    if prev_ord == ord('\n'):
        delay += 0.15 / speed  # Line end pause
    elif prev_ord in (ord('.'), ord('!'), ord('?')):
        delay += 0.1 / speed  # Sentence end pause

    # Clamp to bounds
    if delay < min_delay / speed:
        delay = min_delay / speed
    elif delay > max_delay / speed:
        delay = max_delay / speed

    return delay


cpdef str generate_typo_fast(str correct_char):
    """Generate a plausible typo for a character.

    Args:
        correct_char: The intended character

    Returns:
        A nearby key, or the original if no typo generated
    """
    cdef:
        int char_ord
        bytes nearby
        int idx
        int nearby_len
        char typo_char

    if len(correct_char) == 0:
        return correct_char

    char_ord = ord(correct_char[0].lower())

    if char_ord not in NEARBY_KEYS:
        return correct_char

    nearby = NEARBY_KEYS[char_ord]
    nearby_len = len(nearby)

    if nearby_len == 0:
        return correct_char

    # Pick a random nearby key
    idx = <int>(random_double() * nearby_len)
    if idx >= nearby_len:
        idx = nearby_len - 1

    typo_char = nearby[idx]

    # Preserve case
    if correct_char[0].isupper():
        return chr(typo_char).upper()
    return chr(typo_char)
