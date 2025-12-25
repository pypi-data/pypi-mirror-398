import unicodedata
from functools import lru_cache

def CatUnifier(items, threshold=0.7):
    """
    CATEGORICAL UNIFICATION
    This function processes a common categorical data problem, inconsistent categorical data due to incorrect entries, spelling mistakes, different write/map data ... 
    data might have only four real categories but the output can show two times or even many times that number, which affects subsequent charts, machine learning models, and other processes
    It returns a list with the same order and length, but with corrected categories.    

    Parameters:
    -----------
    items : list
        List of text items (strings)
    
    threshold : float
        Similarity score between 0.0 and 1.0
        Example: 0.7 means 70% similar
    
    Returns:
    --------
    list
        New list with same length.
    
    Example:
    --------
    >>> data = ["Pencil", "Parrise", "Pencle", "Pris", "PParis" "pencl", "pencyl", "Paris"]
    >>> CatUnifier(data, threshold=0.7)
    ["Pencil", "Paris", "Pencil", "Paris", "Paris", "Pencil", "Pencil", "Paris"]
    
    """

    @lru_cache(maxsize=1024)
    def normalize_text(text):
        text = text.lower()
        text = ''.join(
            c for c in unicodedata.normalize('NFKD', text)
            if not unicodedata.combining(c)
        )
        return text
    
    @lru_cache(maxsize=1024)
    def similarity(s1, s2):
        if not s1 and not s2:
            return 1.0
        
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return 0.0
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len) if max_len > 0 else 1.0
    
    
    processed_items = [normalize_text(item) for item in items]
    result = list(items)
    n = len(items)
    assigned = [False] * n
    
    for i in range(n):
        if not assigned[i]:
            cluster = [i]
            assigned[i] = True
            
            for j in range(i + 1, n):
                if not assigned[j]:
                    sim = similarity(processed_items[i], processed_items[j])
                    if sim >= threshold:
                        cluster.append(j)
                        assigned[j] = True
            
            if len(cluster) > 1:
                freq = {}
                for idx in cluster:
                    item = items[idx]
                    freq[item] = freq.get(item, 0) + 1
                
                most_common = max(freq.items(), 
                                 key=lambda x: (x[1], -len(x[0])))[0]
                
                for idx in cluster:
                    result[idx] = most_common
    
    return result


def CatLists(items, threshold=0.7):

    """
    UNIQUE CATEGORIES
    
    This function processes a common categorical data problem, inconsistent categorical data due to incorrect entries, spelling mistakes, different write/map data ...
    It returns a list of unique-corrected categories.
    
    Parameters:
    -----------
    items : list
        List of text items (strings)
    
    threshold : float
        Similarity score between 0.0 and 1.0
        Example: 0.7 means 70% similar
    
    Returns:
    --------
    list
        New list with only one item from each similar group.
        Shorter than original list.
    
    Example:
    --------
    >>> data = ["Pencil", "Parrise", "Pencle", "Pris", "PParis" "pencl", "pencyl", "Paris"]
    >>> CatLists(data, 0.7)
    ["Pencil", "Paris"]
    
    Difference from unify_similar_items:
    ------------------------------------
    - This function returns shorter list (only unique)
    - CatUnifier returns same length list
    """

    @lru_cache(maxsize=1024)
    def normalize_text(text):
        text = text.lower()
        text = ''.join(
            c for c in unicodedata.normalize('NFKD', text)
            if not unicodedata.combining(c)
        )
        return text
    
    @lru_cache(maxsize=1024)
    def similarity(s1, s2):
        if not s1 and not s2:
            return 1.0
        
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return 0.0
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len) if max_len > 0 else 1.0
    

    clusters = []
    assigned = [False] * len(items)
    
    for i in range(len(items)):
        if not assigned[i]:
            cluster = [i]
            assigned[i] = True
            base_norm = normalize_text(items[i])
            
            for j in range(i + 1, len(items)):
                if not assigned[j]:
                    sim = similarity(base_norm, normalize_text(items[j]))
                    if sim >= threshold:
                        cluster.append(j)
                        assigned[j] = True
            
            clusters.append(cluster)
    
    representatives = []
    for cluster in clusters:
        freq = {}
        for idx in cluster:
            original_item = items[idx]
            freq[original_item] = freq.get(original_item, 0) + 1
        
        most_common = max(freq.items(), 
                         key=lambda x: (x[1], -len(x[0])))[0]
        representatives.append(most_common)
    
    return representatives
