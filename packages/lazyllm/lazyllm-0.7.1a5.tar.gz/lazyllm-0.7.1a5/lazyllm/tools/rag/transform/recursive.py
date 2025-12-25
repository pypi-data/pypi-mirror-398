from typing import List, Tuple
from functools import partial
from .character import CharacterSplitter
from .base import _UNSET

class RecursiveSplitter(CharacterSplitter):
    """
Split text by characters recursively.

Args:
    chunk_size (int): The size of the chunk after splitting.
    overlap (int): The length of the overlapping content between two adjacent chunks.
    num_workers (int): Controls the number of threads or processes used for parallel processing.
    keep_separator (bool): Whether to keep the separator in the split text. Defaults to False.
    is_separator_regex (bool): Whether the separator is a regular expression. Defaults to False.
    separators (List[str]): The separators to use for splitting. Defaults to ['

', '
', ' ', '']. If you want to split by multiple separators, you can set this parameter.


Examples:
    
    >>> import lazyllm
    >>> from lazyllm.tools import RecursiveSplitter
    >>> splitter = RecursiveSplitter(separators=['
    
    ', '
    ', ' ', ''])
    >>> documents = Document(dataset_path='your_doc_path', embed=m, manager=False)
    >>> documents.create_node_group(name="recursive", transform=RecursiveSplitter, chunk_size=1024, chunk_overlap=100)
    """
    def __init__(self, chunk_size: int = _UNSET, overlap: int = _UNSET, num_workers: int = _UNSET,
                 keep_separator: bool = _UNSET, is_separator_regex: bool = _UNSET,
                 separators: List[str] = _UNSET, **kwargs):
        super().__init__(chunk_size=chunk_size, overlap=overlap, num_workers=num_workers,
                         keep_separator=keep_separator, is_separator_regex=is_separator_regex)
        separators = self._get_param_value('separators', separators, None)

        self._separators = separators if separators else ['\n\n', '\n', ' ', '']
        self._cached_recursive_split_fns = [
            partial(self._default_split, self._get_separator_pattern(sep))
            for sep in self._separators
        ] + [list]

    def _get_splits_by_fns(self, text: str) -> Tuple[List[str], bool]:
        character_split_fns = self._character_split_fns
        if character_split_fns == []:
            character_split_fns = self._cached_recursive_split_fns
        splits = []
        for split_fn in character_split_fns:
            splits = split_fn(text)
            if len(splits) > 1:
                break

        return splits, False
