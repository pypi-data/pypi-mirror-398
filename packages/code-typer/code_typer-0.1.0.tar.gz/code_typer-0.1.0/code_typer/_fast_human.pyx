# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""Fast Cython implementations of hot code paths in human_behavior.py"""

from libc.math cimport sqrt, log, sin, cos, M_PI
from libc.stdlib cimport rand, RAND_MAX
import random

# Pre-computed pattern data for fast matching
cdef list COMMON_PATTERNS = [
    b"def ", b"return ", b"import ", b"from ", b"class ",
    b"if ", b"else:", b"elif ", b"for ", b"while ",
    b"self.", b"self,", b"__init__", b"__name__",
    b"print(", b"len(", b"range(", b"str(", b"int(",
    b"True", b"False", b"None",
    b"SELECT ", b"FROM ", b"WHERE ", b"INSERT ", b"UPDATE ",
    b"CREATE ", b"DROP ", b"ALTER ", b"JOIN ", b"AND ", b"OR ",
    b"function ", b"const ", b"let ", b"var ", b"async ", b"await ",
    b"    ", b"\t",
    b"): ", b"-> ", b"=> ", b"== ", b"!= ", b"<= ", b">= ",
    b"**", b"++", b"--", b"&&", b"||",
]

# Pattern lengths for quick rejection
cdef list PATTERN_LENGTHS = [len(p) for p in COMMON_PATTERNS]
cdef int MAX_PATTERN_LEN = max(PATTERN_LENGTHS)
cdef int MIN_PATTERN_LEN = min(PATTERN_LENGTHS)


cpdef object check_pattern_match_fast(str content, int position):
    """Check if current position starts a common pattern.

    Returns the matched pattern string or None.
    """
    cdef:
        bytes remaining_bytes
        bytes pattern
        int remaining_len
        int pattern_len
        int i
        int n_patterns = len(COMMON_PATTERNS)

    # Convert slice to bytes for faster comparison
    remaining_len = len(content) - position
    if remaining_len < MIN_PATTERN_LEN:
        return None

    # Only take what we need
    if remaining_len > MAX_PATTERN_LEN:
        remaining_bytes = content[position:position + MAX_PATTERN_LEN].encode('utf-8')
    else:
        remaining_bytes = content[position:].encode('utf-8')

    remaining_len = len(remaining_bytes)

    for i in range(n_patterns):
        pattern = <bytes>COMMON_PATTERNS[i]
        pattern_len = PATTERN_LENGTHS[i]
        if pattern_len <= remaining_len:
            if remaining_bytes[:pattern_len] == pattern:
                return pattern.decode('utf-8')

    return None


cpdef str extract_current_word_fast(str content, int position):
    """Extract the word at/around current position."""
    cdef:
        int start = position
        int end = position
        int content_len = len(content)
        str char

    # Find word start
    while start > 0:
        char = content[start - 1]
        if not (char.isalnum() or char == '_'):
            break
        start -= 1

    # Find word end
    while end < content_len:
        char = content[end]
        if not (char.isalnum() or char == '_'):
            break
        end += 1

    return content[start:end]


cdef class FastRandom:
    """Fast random number generator using LCG."""
    cdef:
        unsigned long long state
        double base_speed

    def __init__(self, seed=None, double base_speed=1.0):
        if seed is None:
            self.state = <unsigned long long>rand()
        else:
            self.state = <unsigned long long>seed
        self.base_speed = base_speed

    cdef inline unsigned long long _next(self):
        # LCG parameters (same as glibc)
        self.state = (self.state * 1103515245 + 12345) & 0x7fffffff
        return self.state

    cpdef double random(self):
        """Return random float in [0, 1)."""
        return <double>self._next() / <double>0x7fffffff

    cpdef double uniform(self, double a, double b):
        """Return random float in [a, b]."""
        return a + (b - a) * self.random()

    cpdef double gauss(self, double mu, double sigma):
        """Return Gaussian random with given mean and std."""
        cdef double u1, u2, z0
        u1 = self.random()
        u2 = self.random()
        # Box-Muller transform
        if u1 < 1e-10:
            u1 = 1e-10
        z0 = sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2)
        return mu + z0 * sigma

    cpdef double scaled_uniform(self, double min_val, double max_val):
        """Get a random uniform value scaled by speed."""
        return self.uniform(min_val, max_val) / self.base_speed


cpdef double calculate_delay_fast(
    str char,
    str prev_char,
    bint in_pattern,
    double base_delay,
    double min_delay,
    double max_delay,
    double speed,
    double momentum,
    object rng,
    tuple pause_line_end
):
    """Calculate delay before typing a character.

    Returns delay in seconds.
    """
    cdef:
        double delay
        double effective_speed

    effective_speed = speed * momentum
    if effective_speed < 0.3:
        effective_speed = 0.3

    # Base delay
    delay = base_delay / effective_speed

    # Character difficulty
    if char in 'etaoins ':
        delay *= 0.7
    elif char in 'ETAOINS':
        delay *= 0.9
    elif char in '!@#$%^&*()_+-=[]{}|;:\'",./<>?`~\\':
        delay *= rng.uniform(1.2, 1.8)
    elif char == '\n':
        delay *= 0.4
    elif char == '\t':
        delay *= 0.3

    # Patterns are faster
    if in_pattern:
        delay *= rng.uniform(0.5, 0.7)

    # Add randomness
    delay *= rng.gauss(1.0, 0.25)

    # Context-based pauses (prev_char is "" when None in Python)
    if prev_char:
        if prev_char == '\n':
            delay += rng.uniform(pause_line_end[0], pause_line_end[1]) / effective_speed
        elif prev_char in '.!?':
            delay += rng.uniform(0.1, 0.3) / effective_speed
        elif prev_char in ':{':
            delay += rng.uniform(0.05, 0.15) / effective_speed

    # Clamp delay
    if delay < min_delay / effective_speed:
        delay = min_delay / effective_speed
    elif delay > max_delay * 2 / effective_speed:
        delay = max_delay * 2 / effective_speed

    return delay


cpdef double update_momentum_fast(
    double momentum,
    bint in_burst,
    bint in_slowdown,
    object rng
):
    """Update typing momentum.

    Returns new momentum value.
    """
    cdef:
        double p_burst_start = 0.08
        double p_burst_end = 0.15
        double p_slowdown = 0.05

    # Add micro-variations
    momentum *= rng.gauss(1.0, 0.08)

    # Clamp
    if momentum < 0.4:
        momentum = 0.4
    elif momentum > 2.2:
        momentum = 2.2

    return momentum
