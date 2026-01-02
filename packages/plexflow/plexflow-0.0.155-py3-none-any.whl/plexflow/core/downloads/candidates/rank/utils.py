import math

def rank_candidate(seeds, size_bytes):
    return seeds / math.sqrt(max(1, size_bytes))