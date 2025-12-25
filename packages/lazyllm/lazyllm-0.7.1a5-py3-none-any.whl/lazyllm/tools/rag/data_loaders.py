from typing import List, Optional, Dict, Union
from lazyllm import LOG
from lazyllm.common.common import once_wrapper

from .doc_node import DocNode, ImageDocNode
from .store import LAZY_ROOT_NAME, LAZY_IMAGE_GROUP
from .dataReader import SimpleDirectoryReader
from collections import defaultdict

type_mapping = {
    DocNode: LAZY_ROOT_NAME,
    ImageDocNode: LAZY_IMAGE_GROUP,
}

class DirectoryReader:
    """A directory reader class for loading and processing documents from file directories.

This class provides functionality to read documents from specified directories and convert them into document nodes. It supports both local and global file readers, and can handle different types of documents including images.

Args:
    input_files (Optional[List[str]]): A list of file paths to read. If None, files will be loaded when calling load_data method.
    local_readers (Optional[Dict]): A dictionary of local file readers specific to this instance. Keys are file patterns, values are reader functions.
    global_readers (Optional[Dict]): A dictionary of global file readers shared across all instances. Keys are file patterns, values are reader functions.


Examples:
    >>> from lazyllm.tools.rag.data_loaders import DirectoryReader
    >>> from lazyllm.tools.rag.readers import DocxReader, PDFReader
    >>> local_readers = {
    ...     "**/*.docx": DocxReader,
    ...     "**/*.pdf": PDFReader
    >>> }
    >>> reader = DirectoryReader(
    ...     input_files=["path/to/documents"],
    ...     local_readers=local_readers,
    ...     global_readers={}
    >>> )
    >>> documents = reader.load_data()
    >>> print(f"加载了 {len(documents)} 个文档")
    """
    def __init__(self, input_files: Optional[List[str]], local_readers: Optional[Dict] = None,
                 global_readers: Optional[Dict] = None) -> None:
        self._input_files = input_files
        self._local_readers, self._global_readers = local_readers, global_readers

    @once_wrapper
    def _lazy_init(self):
        self._reader = SimpleDirectoryReader(file_extractor={**self._global_readers, **self._local_readers})

    def load_data(self, input_files: Optional[List[str]] = None, metadatas: Optional[Dict] = None,
                  *, split_nodes_by_type: bool = False) -> List[DocNode]:
        """Load and process documents from the specified input files.

This method reads documents from the input files using the configured file readers (both local and global), processes them into document nodes, and optionally separates image nodes from text nodes.

Args:
    input_files (Optional[List[str]]): A list of file paths to read. If None, uses the files specified during initialization.
    metadatas (Optional[Dict]): Additional metadata to associate with the loaded documents.
    split_nodes_by_type (bool): Whether to separate image and other nodes from text nodes. If True, returns a tuple of (text_nodes, image_nodes). If False, returns all nodes together.

**Returns:**

- Union[List[DocNode], Tuple[List[DocNode], List[ImageDocNode]]]: If split_nodes_by_type is False, returns a list of all document nodes. If True, returns a tuple containing text nodes and image nodes separately.
"""
        self._lazy_init()
        input_files = input_files or self._input_files
        nodes: Union[List[DocNode], Dict[str, List[DocNode]]] = defaultdict(list) if split_nodes_by_type else []
        for doc in self._reader(input_files=input_files, metadatas=metadatas):
            doc._group = type_mapping.get(type(doc), LAZY_ROOT_NAME)
            nodes[doc._group].append(doc) if split_nodes_by_type else nodes.append(doc)
        if not nodes:
            LOG.error(f'No nodes load from path {input_files}, please check your data path.')
            raise ValueError(f'No nodes load from path {input_files}, please check your data path.')
        LOG.info('DirectoryReader loads data done!')
        return nodes
