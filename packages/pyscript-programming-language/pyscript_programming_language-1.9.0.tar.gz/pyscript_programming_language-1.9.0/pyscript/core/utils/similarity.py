def get_similarity_ratio(string1, string2):
    string1 = [char for char in string1.lower() if not char.isspace()]
    string2 = [char for char in string2.lower() if not char.isspace()]

    bigram1 = set(string1[i] + string1[i + 1] for i in range(len(string1) - 1))
    bigram2 = set(string2[i] + string2[i + 1] for i in range(len(string2) - 1))

    max_bigrams_count = max(len(bigram1), len(bigram2))

    return 0.0 if max_bigrams_count == 0 else len(bigram1 & bigram2) / max_bigrams_count

def get_closest(names, name, cutoff=0.6):
    best_match = None
    best_score = 0.0

    for element in (names if isinstance(names, set) else set(names)):
        score = get_similarity_ratio(name, element)
        if score >= cutoff and score > best_score:
            best_score = score
            best_match = element

    return best_match