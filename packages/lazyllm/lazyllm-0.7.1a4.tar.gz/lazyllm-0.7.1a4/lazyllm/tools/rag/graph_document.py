import weakref
from pathlib import Path
from lazyllm import ModuleBase
from lazyllm.tools.servers.graphrag.graphrag_server_module import GraphRagServerModule

from .document import Document


class GraphDocument(ModuleBase):
    """GraphRAG-based document processing module for knowledge graph querying.

This class provides a high-level interface for working with GraphRAG (Graph-based Retrieval-Augmented Generation) on top of a Document instance. It manages the GraphRAG service lifecycle, including knowledge graph initialization, indexing, and querying capabilities.

Args:
    document (Document): The Document instance to build the knowledge graph from. The GraphRAG knowledge graph will be created in ``{document._manager._dataset_path}/.graphrag_kg``.


Examples:
    >>> import lazyllm
    >>> from lazyllm.tools import Document, GraphDocument, GraphRetriever
    >>> doc = Document(dataset_path='your_doc_path', name='test_graphrag')
    >>> graph_document = GraphDocument(doc)
    >>> graph_document.start()
    >>> user_input = input('Press Enter when files are ready in dataset path')
    >>> graph_document.init_graphrag_kg(regenerate_config=True)
    >>> # Now you need to edit $dataset_path/.graphrag_kg/settings.yaml
    >>> user_input = input('Press Enter when settings.yaml is ready')
    >>> graph_document.start_graphrag_index(override=True)
    >>> status_dict = graph_document.graphrag_index_status()
    >>> lazyllm.LOG.info(f'graphrag index status: {status_dict}')
    >>> # Wait until the index is completed
    >>> user_input = input('Press Enter to start graphrag retriever: ')
    >>> graph_retriever = GraphRetriever(graph_document)
    >>> your_query = input('Enter your query: ')
    >>> print(graph_retriever.forward(your_query))
    """
    def __init__(self, document: Document):
        super().__init__()
        self._kg_dir = str(Path(document._manager._dataset_path) / '.graphrag_kg')
        self._graphrag_server_module = GraphRagServerModule(kg_dir=self._kg_dir)
        self._graphrag_index_task_id = None
        self._document = document
        document._graph_document = weakref.ref(self)

    def start(self):
        self._graphrag_server_module.start()

    def stop(self):
        self._graphrag_server_module.stop()
        self._graphrag_index_task_id = None

    def init_graphrag_kg(self, regenerate_config: bool = True):
        """
Initialize the GraphRAG knowledge graph directory and prepare files. This method copies all files from the document dataset to the GraphRAG input directory and initializes the GraphRAG project structure. The files are renamed with UUID suffixes to avoid naming conflicts.

Args:
    regenerate_config (bool, optional): Whether to regenerate the GraphRAG configuration files. If True, existing configuration will be overwritten. Defaults to True.
"""
        m = self._graphrag_server_module
        kb_files = self._document._list_all_files_in_dataset()
        m.prepare_files(kb_files, regenerate_config=regenerate_config)

    def start_graphrag_index(self, override: bool = True) -> str:
        """
Start the GraphRAG indexing process. This method initiates the asynchronous indexing task that builds the knowledge graph from the prepared files. The indexing runs in the background and can be monitored using graphrag_index_status().

Args:
    override (bool, optional): Whether to override existing index if it exists. If True, any existing index will be deleted and recreated. Defaults to True.
"""
        m = self._graphrag_server_module
        res = m.create_index(override=override)
        self._graphrag_index_task_id = res['task_id']
        return 'Success'

    def graphrag_index_status(self) -> dict:
        """
Get the status of the current GraphRAG indexing task.

**Returns:**

- dict: A dictionary containing the indexing task status information.
"""
        m = self._graphrag_server_module
        res = m.index_status(self._graphrag_index_task_id)
        return res

    def query(self, query: str) -> str:
        """
Query the GraphRAG knowledge graph. This method performs a query against the indexed knowledge graph and returns an answer based on the graph structure and relationships.

Args:
    query (str): The natural language query to search the knowledge graph.

**Returns:**

- str: The answer to the query.
"""
        m = self._graphrag_server_module
        res = m.query(query)
        return res['answer']

    def __del__(self):
        self._graphrag_server_module.stop()
        self._document._graph_documents = None


class UrlGraphDocument(ModuleBase):
    """A lightweight wrapper for querying remote GraphRAG services via URL.

This class provides a simplified interface to query remote GraphRAG services that are already deployed and running.

Args:
    graphrag_url (str): The base URL of the remote GraphRAG service endpoint. Should be in the format 'http://hostname:port'.
"""
    def __init__(self, graphrag_url: str):
        super().__init__()
        self._graphrag_server_url = graphrag_url

    def forward(self, *args, **kw):
        return GraphRagServerModule.query_by_url(self._graphrag_server_url, *args, **kw)
