from lazyllm import ModuleBase
from .document import Document
from .graph_document import GraphDocument, UrlGraphDocument
from ..servers.graphrag.graphrag_server_module import GraphRagServerModule

from typing import Union


class GraphRetriever(ModuleBase):
    """GraphRAG-based retriever for querying knowledge graphs.

This class provides a simple interface for querying GraphRAG knowledge graphs built from Document instances. It acts as a wrapper around GraphDocument's query functionality, providing a consistent retriever interface similar to other retrievers in the LazyLLM framework.

Args:
    doc (Union[Document, GraphDocument]): Either a Document or GraphDocument instance. If a Document is provided, the retriever will attempt to retrieve the associated GraphDocument through a weak reference. If a GraphDocument is provided directly, it will be used as-is.
"""
    def __init__(self, doc: Union[Document, GraphDocument, UrlGraphDocument], **kwargs):
        super().__init__()
        assert isinstance(
            doc, (Document, GraphDocument, UrlGraphDocument)
        ), 'doc must be a Document or GraphDocument or UrlGraphDocument instance'
        self._graph_document = None
        self._graphrag_url = None
        if isinstance(doc, GraphDocument):
            self._graph_document = doc
        elif isinstance(doc, Document):
            self._graph_document = doc._graph_document()
        elif isinstance(doc, UrlGraphDocument):
            self._graphrag_url = doc._graphrag_url
        else:
            raise ValueError('doc must be a Document or GraphDocument instance')

    def forward(self, query: str) -> str:
        if self._graph_document:
            return self._graph_document.query(query)
        elif self._graphrag_url:
            return GraphRagServerModule.query_by_url(self._graphrag_url, query)
        else:
            raise ValueError('graph_document or graphrag_url is not set')

    def __repr__(self):
        return f'GraphRetriever(graph_document={self._graph_document})'
