# ruff: noqa: E501, SLF001, D205, ANN003
import logging
import re
from abc import ABC, abstractmethod
from typing import Callable, Optional

# Configure logging
logger = logging.getLogger(__name__)

FIELDS_TO_CLEAN = [
    "id",
    "embeddings",
    "labels",
    "_type",
    "type",
    "_description",
    "project_key",
    "references",
    "object_id",
    "id",
    "start_char_idx",
    "end_char_idx",
    "latest_ingestion_id",
    "json_object",
]


class Tool(ABC):
    """Base class for all tools"""

    def tool_name(self):
        """Get the tool name"""
        return self.tool_name

    def tool_description(self):
        """Get the tool description"""
        return self.tool_description

    def set_assistant(self, assistant):
        """Set the assistant for the tool"""
        self.assistant = assistant

    def log_tool_call(self, results, tool_params):
        """Process the results of the tool in a standardized way."""
        self.assistant.log_tool_call(
            tool_name=self.tool_name(),
            params=tool_params,
            results=results,
        )
        return results

    def clean_results(self, results_to_clean: list) -> list:
        results = []
        for result in results_to_clean:
            for field in FIELDS_TO_CLEAN:
                if field in result:
                    del result[field]
            results.append(result)
        return results

    @abstractmethod
    def tool_function(self) -> Callable:
        """Get the tool function itself. This must be overriden in the child class."""


class SearchTool(Tool):
    def retrieve_with_semantic_search(self, indexes: list, query: str, top_k: Optional[int] = None):
        return self.assistant.warehouse.retrieve_with_semantic_search(
            query=query,
            n_objects=top_k or self.default_top_k,
            indexes=indexes,
            included_tags=self.included_tags,
            excluded_tags=self.excluded_tags,
            reformulate_query=self.reformulate_query,
            rerank=self.rerank,
            included_objects=self.included_objects,
            excluded_objects=self.excluded_objects,
            selected_documents=self.selected_documents,
        )

    def retrieve_with_full_text_search(
        self, indexes: list, query: str, top_k: Optional[int] = None
    ):
        return self.assistant.warehouse.retrieve_with_full_text_search(
            query=query,
            n_objects=top_k or self.default_top_k,
            indexes=indexes,
            included_tags=self.included_tags,
            excluded_tags=self.excluded_tags,
            reformulate_query=self.reformulate_query,
            rerank=self.rerank,
            included_objects=self.included_objects,
            excluded_objects=self.excluded_objects,
            selected_documents=self.selected_documents,
        )

    def retrieve_with_hybrid_search(self, indexes: list, query: str, top_k: Optional[int] = None):
        return self.assistant.warehouse.retrieve_with_hybrid_search(
            query=query,
            n_objects=top_k or self.default_top_k,
            indexes=indexes,
            included_tags=self.included_tags,
            excluded_tags=self.excluded_tags,
            reformulate_query=self.reformulate_query,
            rerank=self.rerank,
            included_objects=self.included_objects,
            excluded_objects=self.excluded_objects,
            selected_documents=self.selected_documents,
        )

    def finalize(self, results, query, top_k):
        self.assistant.store_in_cache(results)
        return self.log_tool_call(results=results, tool_params={"query": query, "top_k": top_k})


class SearchOnChunksTool(SearchTool):
    def __init__(
        self,
        mode: str = "semantic",
        included_tags: list = [],
        excluded_tags: list = [],
        included_objects: list = [],
        excluded_objects: list = [],
        selected_documents: list = [],
        rerank: bool = False,
        reformulate_query: bool = False,
        default_top_k: int = 5,
        **kwargs,
    ):
        self.mode = mode
        self.included_tags = included_tags
        self.excluded_tags = excluded_tags
        self.included_objects = included_objects
        self.excluded_objects = excluded_objects
        self.selected_documents = selected_documents
        self.rerank = rerank
        self.reformulate_query = reformulate_query
        self.default_top_k = default_top_k
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and will be removed in the future")

    def tool_name(self):
        return f"search_on_chunks_{self.mode}"

    def tool_description(self):
        text = f"Retrieve relevant chunks from Knowledge Database for a given query ({self.mode})"
        if self.rerank:
            text += " with optimal reranking"
        if self.reformulate_query:
            text += " with query reformulation"
        return text

    def tool_function(self) -> Callable:
        functions = {
            "semantic": self.retrieve_relevant_chunks_with_semantic_search,
            "full_text": self.retrieve_relevant_chunks_with_full_text_search,
            "hybrid": self.retrieve_relevant_chunks_with_hybrid_search,
        }
        return functions.get(self.mode, self.retrieve_relevant_chunks_with_semantic_search)

    def retrieve_relevant_chunks_with_semantic_search(
        self, query: str, top_k: Optional[int] = None
    ) -> list:
        """
        Retrieve the 'top_k' chunks from the chunks collection of the Knowledge Database that are relevant to the 'query'.
        The search uses a semantic search approach (embeddings vector search)
        """
        return self._search(query, top_k)

    def retrieve_relevant_chunks_with_full_text_search(
        self, query: str, top_k: Optional[int] = None
    ) -> list:
        """
        Retrieve the 'top_k' chunks from the chunks collection of the Knowledge Database that are relevant to the 'query'.
        The search uses a full-text search approach (text search)
        """
        return self._search(query, top_k)

    def retrieve_relevant_chunks_with_hybrid_search(
        self, query: str, top_k: Optional[int] = None
    ) -> list:
        """
        Retrieve the 'top_k' chunks from the chunks collection of the Knowledge Database that are relevant to the 'query'.
        The search uses a hybrid search approach (embeddings vector search + text search with an optimal sorting of the results)
        """
        return self._search(query, top_k)

    def _search(self, query: str, top_k: Optional[int] = None) -> list:
        """Search inside the chunks collection from Knowledge Warehouse"""
        retrieve_function = {
            "semantic": self.retrieve_with_semantic_search,
            "full_text": self.retrieve_with_full_text_search,
            "hybrid": self.retrieve_with_hybrid_search,
        }[self.mode]
        retrieval_results = retrieve_function(indexes=["chunks"], query=query, top_k=top_k)
        fields_to_keep = [
            "chunk_ids",
            "type",
            "content",
            "name",
            "document_id",
            "reference_url",
            "score",
        ]
        results = []
        for result in retrieval_results:
            result_dict = {k: result[k] for k in fields_to_keep if k in result}
            if "chunk_ids" in result:
                result_dict["uuid"] = result["chunk_ids"][0]
            results.append(result_dict)
        results = self.clean_results(results)
        return self.finalize(results, query, top_k)


class SearchOnObjectsTool(SearchTool):
    def __init__(
        self,
        mode: str = "semantic",
        included_tags: list = [],
        excluded_tags: list = [],
        included_objects: list = [],
        excluded_objects: list = [],
        selected_documents: list = [],
        rerank: bool = False,
        reformulate_query: bool = False,
        default_top_k: int = 5,
        **kwargs,
    ):
        self.mode = mode
        self.included_tags = included_tags
        self.excluded_tags = excluded_tags
        self.included_objects = included_objects
        self.excluded_objects = excluded_objects
        self.selected_documents = selected_documents
        self.rerank = rerank
        self.reformulate_query = reformulate_query
        self.default_top_k = default_top_k
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and will be removed in the future")

    def tool_name(self):
        return f"search_on_objects_{self.mode}"

    def tool_description(self):
        text = f"Retrieve relevant objects from Knowledge Database for a given query ({self.mode})"
        if self.rerank:
            text += " with optimal reranking"
        if self.reformulate_query:
            text += " with query reformulation"
        return text

    def tool_function(self) -> Callable:
        functions = {
            "semantic": self.retrieve_relevant_objects_with_semantic_search,
            "full_text": self.retrieve_relevant_objects_with_full_text_search,
            "hybrid": self.retrieve_relevant_objects_with_hybrid_search,
        }
        return functions.get(self.mode, self.retrieve_relevant_objects_with_semantic_search)

    def retrieve_relevant_objects_with_semantic_search(
        self, query: str, top_k: Optional[int] = None
    ) -> list:
        """
        Retrieve the 'top_k' objects from the objects collection of the Knowledge Database that are relevant to the 'query'.
        The search uses a semantic search approach (embeddings vector search)
        """
        return self._search(query, top_k)

    def retrieve_relevant_objects_with_full_text_search(
        self, query: str, top_k: Optional[int] = None
    ) -> list:
        """
        Retrieve the 'top_k' objects from the objects collection of the Knowledge Database that are relevant to the 'query'.
        The search uses a full-text search approach (text search)
        """
        return self._search(query, top_k)

    def retrieve_relevant_objects_with_hybrid_search(
        self, query: str, top_k: Optional[int] = None
    ) -> list:
        """
        Retrieve the 'top_k' objects from the objects collection of the Knowledge Database that are relevant to the 'query'.
        The search uses a hybrid search approach (embeddings vector search + text search with an optimal sorting of the results)
        """
        return self._search(query, top_k)

    def _search(self, query: str, top_k: Optional[int] = None) -> list:
        """Search inside the objects collection from Knowledge Warehouse"""
        retrieve_function = {
            "semantic": self.retrieve_with_semantic_search,
            "full_text": self.retrieve_with_full_text_search,
            "hybrid": self.retrieve_with_hybrid_search,
        }[self.mode]
        retrieval_results = retrieve_function(indexes=["objects"], query=query, top_k=top_k)
        for result in retrieval_results:
            if "object_id" in result:
                result["uuid"] = result["object_id"]
        results = self.clean_results(retrieval_results)
        return self.finalize(results, query, top_k)


class SemanticSearchOnChunksTool(SearchOnChunksTool):
    def __init__(self, **kwargs):
        super().__init__(mode="semantic", **kwargs)


class SemanticSearchOnObjectsTool(SearchOnObjectsTool):
    def __init__(self, **kwargs):
        super().__init__(mode="semantic", **kwargs)


class FullTextSearchOnObjectsTool(SearchOnObjectsTool):
    def __init__(self, **kwargs):
        super().__init__(mode="full_text", **kwargs)


class HybridSearchOnChunksTool(SearchOnChunksTool):
    def __init__(self, **kwargs):
        super().__init__(mode="hybrid", **kwargs)


class HybridSearchOnObjectsTool(SearchOnObjectsTool):
    def __init__(self, **kwargs):
        super().__init__(mode="hybrid", **kwargs)


DESCRIPTION_TEMPLATE = """
Retrieve items (chunks, objects) from Knowledge Database graph with a provided templated query in the Cypher language.
This is the template query:
```cypher
{query_template}
```
The variables in the template are: {variables}
The variables have to be provided as a dictionary in the input parameters
The input parameter 'template_variables' should be a dictionary with the variables as keys and the values as values
The values can be provided as a string, a number, a boolean, a list, a dictionary, or a null value
"""


class SearchTemplatedQueryTool(Tool):
    def __init__(
        self,
        query_template: str,
        **kwargs,
    ):
        self.query_template = query_template
        self.variables = self._extract_variables_from_query_template(query_template)
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and will be removed in the future")

    def tool_name(self):
        return "search_templated_query"

    def tool_description(self):
        return DESCRIPTION_TEMPLATE.format(
            query_template=self.query_template, variables=self.variables
        )

    def tool_function(self) -> Callable:
        return self.retrieve_items_from_knowledge_database_graph_with_templated_query

    def _extract_variables_from_query_template(self, query_template: str) -> set[str]:
        """
        Extracts all named parameters from a Cypher query template.

        The function looks for two types of parameter syntax:
        1. $variableName (e.g., $username)
        2. {variableName} (e.g., {username})
        """
        pattern = r"(?:\$|{)(\w+)}?"
        matches = re.findall(pattern, query_template)
        return set(matches)

    def retrieve_items_from_knowledge_database_graph_with_templated_query(
        self, template_variables: dict
    ) -> list:
        """
        Retrieve items from the Knowledge Database graph with a provided templated query in the Cypher language.
        template_variables: dict with the template variables as keys and the values as values
        """
        results = self.assistant.warehouse.retrieve_with_templated_query(
            query_template=self.query_template,
            template_variables=template_variables,
        )
        results = self.clean_results(results)
        self.assistant.store_in_cache(results)
        return self.log_tool_call(
            results=results, tool_params={"template_variables": template_variables}
        )
