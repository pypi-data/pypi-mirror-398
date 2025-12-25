from typing import List


def chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split text into chunks of specified size with optional overlap.

    Args:
        text: The input text to split
        chunk_size: Size of each chunk (in words)
        overlap: Number of overlapping words between chunks

    Returns:
        List of text chunks
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    words = text.split()
    word_count = len(words)

    if word_count <= chunk_size:
        return [text]

    chunk_list = []
    start = 0
    while start < word_count:
        end = min(start + chunk_size, word_count)
        chunk_list.append(" ".join(words[start:end]))
        start += chunk_size - overlap

    return chunk_list
