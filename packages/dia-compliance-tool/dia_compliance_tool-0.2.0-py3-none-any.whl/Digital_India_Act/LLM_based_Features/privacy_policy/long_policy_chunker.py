from typing import List

def chunk_text(text: str, max_words: int=800, overlap: int=50) -> List[str]:
    """
    Chunk the policy extracted with overlap.
    Can use token-aware chunker for better performance in terms of LLM cost control.
    max_words can be tuned according to the context window of the LLM
    """

    chunks = []
    current = []
    count = 0

    word = ""
    for ch in text:
        if ch.isspace():
            if word:
                current.append(word)
                count+=1
                word = ""

                if count >= max_words:
                    chunks.append(" ".join(current))

                    if overlap > 0:
                        current = current[-overlap:]
                        count = len(current)
                    else:
                        current = []
                        count = 0
        else:
            word += ch

    if word:
        current.append(word)
    if current:
        chunks.append(" ".join(current))

    return chunks