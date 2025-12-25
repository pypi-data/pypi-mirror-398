import os
import fnmatch

from typing import Any, Dict, List, Union, Optional, Callable

from ..doc_node import DocNode, QADocNode
from lazyllm import LOG
from .base import NodeTransform

from lazyllm.components import AlpacaPrompter
from dataclasses import dataclass, field

from lazyllm import TrainableModule
from lazyllm.components.formatter import encode_query_with_filepaths
from ..prompts import LLMTransformParserPrompts

@dataclass
class TransformArgs():
    """
A document transformation parameter container for centralized management of processing configurations.

Args:
    f (Union[str, Callable]): Transformation function or registered function name.Can be either a callable function or a string identifier for registered functions.
    trans_node (bool): Whether to transform node types.When True, modifies the document node structure during processing.
    num_workers (int):Controls parallel processing threads.Values >0.
    kwargs (Dict):Additional parameters passed to the transformation function.
    pattern (Union[str, Callable[[str], bool]]):File name/content matching pattern.


Examples:
    
    >>> from lazyllm.tools import TransformArgs
    >>> args = TransformArgs(f=lambda text: text.lower(),num_workers=4,pattern=r'.*\.md$')
    >>>config = {'f': 'parse_pdf','kwargs': {'engine': 'pdfminer'},'trans_node': True}
    >>>args = TransformArgs.from_dict(config)
    print(args['f'])
    print(args.get('unknown'))
    """
    f: Union[str, Callable]
    trans_node: Optional[bool] = None
    num_workers: int = 0
    kwargs: Dict = field(default_factory=dict)
    pattern: Optional[Union[str, Callable[[str], bool]]] = None

    @staticmethod
    def from_dict(d):
        return TransformArgs(f=d['f'], trans_node=d.get('trans_node'), num_workers=d.get(
            'num_workers', 0), kwargs=d.get('kwargs', dict()), pattern=d.get('pattern'))

    def __getitem__(self, key):
        if key in self.__dict__: return getattr(self, key)
        raise KeyError(f'Key {key} is not found in transform args')

    def get(self, key):
        if key in self.__dict__: return getattr(self, key)
        return None

def build_nodes_from_splits(
    text_splits: List[str], doc: DocNode, node_group: str
) -> List[DocNode]:
    nodes: List[DocNode] = []
    for text_chunk in text_splits:
        if not text_chunk:
            continue
        node = DocNode(
            text=text_chunk,
            group=node_group,
            parent=doc,
        )
        nodes.append(node)

    doc.children[node_group] = nodes
    return nodes

def make_transform(t: Union[TransformArgs, Dict[str, Any]], group_name: Optional[str] = None) -> NodeTransform:
    if isinstance(t, dict): t = TransformArgs.from_dict(t)
    transform, trans_node, num_workers = t['f'], t['trans_node'], t['num_workers']
    num_workers = dict(num_workers=num_workers) if num_workers > 0 else dict()
    return (transform(**t['kwargs'], **num_workers).with_name(group_name, copy=False) if isinstance(transform, type)
            else transform.with_name(group_name) if isinstance(transform, NodeTransform)
            else FuncNodeTransform(transform, trans_node=trans_node, **num_workers).with_name(group_name, copy=False))


class AdaptiveTransform(NodeTransform):
    """A flexible document transformation system that applies different transforms based on document patterns.

AdaptiveTransform allows you to define multiple transformation strategies and automatically selects the appropriate one based on the document's file path or custom pattern matching. This is particularly useful when you have different types of documents that require different processing approaches.

Args:
    transforms (Union[List[Union[TransformArgs, Dict]], Union[TransformArgs, Dict]]): A list of transform configurations or a single transform configuration. 
    num_workers (int, optional): Number of worker threads for parallel processing. Defaults to 0.


Examples:
    >>> from lazyllm.tools.rag.transform import AdaptiveTransform, DocNode, SentenceSplitter
    >>> doc1 = DocNode(text="这是第一个文档的内容。它包含多个句子。")
    >>> doc2 = DocNode(text="这是第二个文档的内容。")
    >>> transforms = [
    ...     {
    ...         'f': SentenceSplitter,
    ...         'pattern': '*.txt',
    ...         'kwargs': {'chunk_size': 50, 'chunk_overlap': 10}
    ...     },
    ...     {
    ...         'f': SentenceSplitter,
    ...         'pattern': '*.pdf',
    ...         'kwargs': {'chunk_size': 100, 'chunk_overlap': 20}
    ...     }
    ... ]
    >>> adaptive = AdaptiveTransform(transforms)
    >>> results1 = adaptive.transform(doc1)
    >>> print(f"文档1转换结果: {len(results1)} 个块")
    >>> for i, result in enumerate(results1):
    ...     print(f"  块 {i+1}: {result.text}")
    >>> results2 = adaptive.transform(doc2)
    >>> print(f"文档2转换结果: {len(results2)} 个块")
    >>> for i, result in enumerate(results2):
    ...     print(f"  块 {i+1}: {result.text}")      
    """
    def __init__(self, transforms: Union[List[Union[TransformArgs, Dict]], Union[TransformArgs, Dict]],
                 num_workers: int = 0):
        super().__init__(num_workers=num_workers)
        if not isinstance(transforms, (tuple, list)): transforms = [transforms]
        self._transformers = [(t.get('pattern'), make_transform(t)) for t in transforms]

    def transform(self, document: DocNode, **kwargs) -> List[Union[str, DocNode]]:
        """Transform a document using the appropriate transformation strategy based on pattern matching.

This method evaluates each transform configuration in order and applies the first one that matches the document's path pattern. The matching logic supports both glob patterns and custom callable functions.

Args:
    document (DocNode): The document node to be transformed.
    **kwargs: Additional keyword arguments passed to the transform function.

**Returns:**

- List[Union[str, DocNode]]: A list of transformed results (strings or DocNode objects).
"""
        if not isinstance(document, DocNode): LOG.warning(f'Invalud document type {type(document)} got')
        for pt, transform in self._transformers:
            if pt and isinstance(pt, str) and not pt.startswith('*'): pt = os.path.join(os.getcwd(), pt)
            if not pt or (callable(pt) and pt(document.docpath)) or (
                    isinstance(pt, str) and fnmatch.fnmatch(document.docpath, pt)):
                return transform(document, **kwargs)
        LOG.warning(f'No transform found for document {document.docpath} with group name `{self._name}`')
        return []


class FuncNodeTransform(NodeTransform):
    """
A wrapper class for user-defined functions that transforms document nodes.

This wrapper supports two modes of operation:
    1. When trans_node is False (default): transforms text strings
    2. When trans_node is True: transforms DocNode objects

The wrapper can handle various function signatures:
    - str -> List[str]: transform=lambda t: t.split('\\n')
    - str -> str: transform=lambda t: t[:3]
    - DocNode -> List[DocNode]: pipeline(lambda x:x, SentenceSplitter)
    - DocNode -> DocNode: pipeline(LLMParser)

Args:
    func (Union[Callable[[str], List[str]], Callable[[DocNode], List[DocNode]]]): The user-defined function to be wrapped.
    trans_node (bool, optional): Determines whether the function operates on DocNode objects (True) or text strings (False). Defaults to None.
    num_workers (int): Controls the number of threads or processes used for parallel processing. Defaults to 0.


Examples:
    
    >>> import lazyllm
    >>> from lazyllm.tools.rag import FuncNodeTransform
    >>> from lazyllm.tools import Document, SentenceSplitter
    
    # Example 1: Text-based transformation (trans_node=False)
    >>> def split_by_comma(text):
    ...     return text.split(',')
    >>> text_transform = FuncNodeTransform(split_by_comma, trans_node=False)
    
    # Example 2: Node-based transformation (trans_node=True)
    >>> def custom_node_transform(node):
    ...     # Process the DocNode and return a list of DocNodes
    ...     return [node]  # Simple pass-through
    >>> node_transform = FuncNodeTransform(custom_node_transform, trans_node=True)
    
    # Example 3: Using with Document
    >>> m = lazyllm.OnlineEmbeddingModule(source="glm")
    >>> documents = Document(dataset_path='your_doc_path', embed=m, manager=False)
    >>> documents.create_node_group(name="custom", transform=text_transform)
    """
    def __init__(self, func: Union[Callable[[str], List[str]], Callable[[DocNode], List[DocNode]]],
                 trans_node: bool = None, num_workers: int = 0):
        super(__class__, self).__init__(num_workers=num_workers)
        self._func, self._trans_node = func, trans_node

    def transform(self, node: DocNode, **kwargs) -> List[Union[str, DocNode]]:
        """
Transform a document node using the wrapped user-defined function.

This method applies the user-defined function to either the text content of the node (when trans_node=False) or the node itself (when trans_node=True).

Args:
    node (DocNode): The document node to be transformed.
    **kwargs: Additional keyword arguments passed to the transformation function.

**Returns:**

- List[Union[str, DocNode]]: The transformed results, which can be either strings or DocNode objects depending on the function implementation.
"""
        result = self._func(node if self._trans_node else node.get_text(), **kwargs)
        return result if isinstance(result, list) else [result]


class LLMParser(NodeTransform):
    """
A text summarizer and keyword extractor that is responsible for analyzing the text input by the user and providing concise summaries or extracting relevant keywords based on the requested task.

Args:
    llm (TrainableModule): A trainable module.
    language (str): The language type, currently only supports Chinese (zh) and English (en).
    task_type (str): Currently supports two types of tasks: summary and keyword extraction.
    num_workers (int): Controls the number of threads or processes used for parallel processing.


Examples:
    
    >>> from lazyllm import TrainableModule
    >>> from lazyllm.tools.rag import LLMParser
    >>> llm = TrainableModule("internlm2-chat-7b")
    >>> summary_parser = LLMParser(llm, language="en", task_type="summary")
    """
    supported_languages = {'en': 'English', 'zh': 'Chinese'}

    def __init__(self, llm: TrainableModule, language: str, task_type: str,
                 prompts: Optional[LLMTransformParserPrompts] = None, num_workers: int = 30):
        super(__class__, self).__init__(num_workers=num_workers)
        assert language in self.supported_languages, f'Not supported language {language}'
        assert task_type in ['summary', 'keywords', 'qa', 'qa_img'], f'Not supported task_type {task_type}'
        self._task_type = task_type
        self._prompts = prompts or LLMTransformParserPrompts()
        task_prompt_tempalte = getattr(self._prompts, self._task_type)
        task_prompt = task_prompt_tempalte.format(language=self.supported_languages[language])
        if self._task_type == 'qa_img':
            prompt = dict(system=task_prompt, user='{input}')
        else:
            prompt = dict(system=task_prompt, user='#input:\n{input}\n#output:\n')
        self._llm = llm.share(prompt=AlpacaPrompter(prompt), stream=False, format=self._format)
        self._task_type = task_type

    def transform(self, node: DocNode, **kwargs) -> List[str]:
        """
Perform the set task on the specified document.

Args:
    node (DocNode): The document on which the extraction task needs to be performed.


Examples:
    
    >>> import lazyllm
    >>> from lazyllm.tools import LLMParser
    >>> llm = lazyllm.TrainableModule("internlm2-chat-7b").start()
    >>> m = lazyllm.TrainableModule("bge-large-zh-v1.5").start()
    >>> summary_parser = LLMParser(llm, language="en", task_type="summary")
    >>> keywords_parser = LLMParser(llm, language="en", task_type="keywords")
    >>> documents = lazyllm.Document(dataset_path="/path/to/your/data", embed=m, manager=False)
    >>> rm = lazyllm.Retriever(documents, group_name='CoarseChunk', similarity='bm25', topk=6)
    >>> doc_nodes = rm("test")
    >>> summary_result = summary_parser.transform(doc_nodes[0])
    >>> keywords_result = keywords_parser.transform(doc_nodes[0])
    """
        if self._task_type == 'qa_img':
            inputs = encode_query_with_filepaths('Extract QA pairs from images.', [node.image_path])
        else:
            inputs = node.get_text()
        result = self._llm(inputs)
        return [result] if isinstance(result, str) else result

    def _format(self, input):
        if isinstance(input, dict):
            input = input.get('output', input.get('text', input.get('content', str(input))))

        if not isinstance(input, str):
            input = str(input)

        if self._task_type == 'keywords':
            return [s.strip() for s in input.split(',')]
        elif self._task_type in ('qa', 'qa_img'):
            return [QADocNode(query=q.strip()[3:].strip(), answer=a.strip()[3:].strip()) for q, a in zip(
                list(filter(None, map(str.strip, input.split('\n'))))[::2],
                list(filter(None, map(str.strip, input.split('\n'))))[1::2])]
        return input
