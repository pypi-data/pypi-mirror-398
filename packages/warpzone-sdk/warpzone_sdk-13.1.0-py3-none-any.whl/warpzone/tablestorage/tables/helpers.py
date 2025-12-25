# Invalid characters for partition key and row key in storage table
# https://learn.microsoft.com/en-gb/archive/blogs/jmstall/azure-storage-naming-rules
INVALID_CHARACTERS_DICTIONARY = {ord(c): "_" for c in r"\/#?"}


def chunkify(lst: list, max_chunk_size: int) -> list[list]:
    """Split list into n lists that does not exceed max_chunk_size.

    Args:
        lst (typing.List): Initial list of things.
        max_chunk_size (int): The maximum size of the chunks.

    Returns:
        list[list]: List of lists.
    """
    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be greater than 0.")

    if not lst:
        return []

    n = len(lst) // max_chunk_size + 1

    return [lst[i::n] for i in range(n)]


def generate_valid_table_keys(key: str) -> str:
    """Replace invalid characters in partition key
    and row key in table storage"""
    return key.translate(INVALID_CHARACTERS_DICTIONARY)
