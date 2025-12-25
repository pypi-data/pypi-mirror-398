"""
Vector database implementation for embedding storage and similarity search.
"""

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings

from aixtools.logging.logging_config import get_logger
from aixtools.utils.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_VDB_EMBEDDINGS_MODEL_NAME,
    OLLAMA_VDB_EMBEDDINGS_MODEL_NAME,
    OPENAI_API_KEY,
    OPENAI_VDB_EMBEDDINGS_MODEL_NAME,
    VDB_CHROMA_PATH,
    VDB_EMBEDDINGS_MODEL_FAMILY,
)

CREATE_DB = False

_vector_dbs = {}

logger = get_logger(__name__)


def get_vdb_embedding(model_family=VDB_EMBEDDINGS_MODEL_FAMILY) -> Embeddings:
    """Get the embedding model for vector storage"""
    match model_family:
        case "openai":
            return OpenAIEmbeddings(model=OPENAI_VDB_EMBEDDINGS_MODEL_NAME, api_key=OPENAI_API_KEY)  # type: ignore
        case "azure":
            return AzureOpenAIEmbeddings(  # type: ignore
                model=AZURE_VDB_EMBEDDINGS_MODEL_NAME, api_key=AZURE_OPENAI_API_KEY
            )
        case "ollama":
            return OllamaEmbeddings(model=OLLAMA_VDB_EMBEDDINGS_MODEL_NAME)  # type: ignore
        case _:
            raise ValueError(f"Model family {model_family} not supported")


def get_vector_db(collection_name: str) -> Chroma:
    """Implement singleton pattern for database connections"""
    # _vector_dbs will not be re-assigned, but it will be modified
    global _vector_dbs  # noqa: PLW0602, pylint: disable=protected-access,global-variable-not-assigned
    if collection_name not in _vector_dbs:
        print(f"Creating new DB connection: {collection_name=}")
        vdb = Chroma(
            persist_directory=str(VDB_CHROMA_PATH),
            collection_name=collection_name,
            embedding_function=get_vdb_embedding(),
        )
        _vector_dbs[collection_name] = vdb
    return _vector_dbs[collection_name]


def vdb_add(vdb: Chroma, text: str, doc_id: str, meta=list[dict] | dict | None, force=False) -> str | None:
    """
    Add a document to the database if it's not already there.
    """
    if not force and vdb_has_id(vdb, doc_id):
        return None  # Document already exists, return None
    if isinstance(meta, list):
        metadatas = meta
    elif isinstance(meta, dict):
        metadatas = [meta]
    else:
        metadatas = None
    ids = vdb.add_texts(texts=[text], ids=[doc_id], metadatas=metadatas)  # type: ignore
    if not ids:
        return None
    return ids[0]  # Return the id of the added document


def vdb_get_by_id(vdb: Chroma, doc_id: str):
    """Get document with by id"""
    collection = vdb._collection  # pylint: disable=protected-access
    return collection.get(ids=[doc_id])  # query by id


def vdb_has_id(vdb: Chroma, doc_id: str):
    """Check if a document with a given id exists in the database"""
    result = vdb_get_by_id(vdb, doc_id)
    return len(result["ids"]) > 0


# Load database
def vdb_query(  # noqa: PLR0913, pylint: disable=too-many-arguments,too-many-positional-arguments
    vdb: Chroma,
    query: str,
    filter: dict[str, str] | None = None,  # pylint: disable=redefined-builtin
    where_document: dict[str, str] | None = None,
    max_items=10,
    similarity_threshold=None,
):
    """
    Query vector database with a given query, return top k results.
    Args:
        query: str, query string
        max_items: int, maximum number of items to return
        similarity_threshold: float, similarity threshold to filter the results
    """
    results = vdb.similarity_search_with_relevance_scores(
        query, k=max_items, filter=filter, where_document=where_document
    )
    logger.debug(
        "Got %s results before filter, first one's similarity score is: %s",
        len(results),
        results[0][1] if results else None,
    )
    if similarity_threshold is not None:
        results = [(doc_id, score) for doc_id, score in results if score > similarity_threshold]
        print(f"Got {len(results)} results after filter")
    return results
