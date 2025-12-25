import hashlib
import uuid
from typing import Any, List, Union

from sayou.core.registry import register_component
from sayou.core.schemas import SayouNode, SayouOutput
from sayou.core.vocabulary import SayouAttribute, SayouClass, SayouPredicate

from ..interfaces.base_adapter import BaseAdapter


@register_component("adapter")
class DocumentChunkAdapter(BaseAdapter):
    """
    Standard Adapter for Sayou Chunking results.

    Converts `Chunk` objects (from sayou-chunking) into semantic `SayouNodes`.
    It maps metadata like 'semantic_type' to Ontology Classes (e.g., sayou:Topic)
    and preserves relationships like 'parent_id' as 'sayou:hasParent'.
    """

    component_name = "DocumentChunkAdapter"
    SUPPORTED_TYPES = ["document_chunk"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if isinstance(input_data, list):
            if len(input_data) == 0:
                return 0.1

            first = input_data[0]

            if hasattr(first, "doc_type") or (
                isinstance(first, dict) and "chunk_id" in first
            ):
                return 0.95

            if isinstance(first, dict):
                return 0.6

            return 0.3

        if hasattr(input_data, "doc_type") or (
            isinstance(input_data, dict) and "chunk_id" in input_data
        ):
            return 0.95

        return 0.0

    def _do_adapt(self, input_data: Union[List[Any], Any]) -> SayouOutput:
        """
        Convert chunks into a list of SayouNodes.

        Handles both Pydantic Chunk objects and dictionary representations.
        Generates deterministic URIs for nodes based on chunk IDs.

        Args:
            input_data (Union[List[Any], Any]): A single Chunk or list of Chunks.

        Returns:
            SayouOutput: The output containing the graph of nodes.
        """
        if not isinstance(input_data, list):
            input_data = [input_data]

        nodes = []

        for item in input_data:
            chunk_data = item.model_dump() if hasattr(item, "model_dump") else item

            if not isinstance(chunk_data, dict):
                self._log(f"Skipping invalid chunk data: {type(item)}", level="warning")
                continue

            content = chunk_data.get("content", "")
            meta = chunk_data.get("metadata", {})

            # 1. ID Mapping (Prefix 'sayou:doc:' added)
            raw_id = meta.get("chunk_id", "unknown")
            if not raw_id or raw_id == "unknown":
                if content:
                    raw_id = hashlib.md5(content.encode("utf-8")).hexdigest()
                else:
                    raw_id = str(uuid.uuid4())

            source_name = meta.get("filename") or meta.get("source")
            if source_name:
                safe_name = source_name.replace(" ", "_").replace(":", "")
                node_id = f"sayou:doc:{safe_name}:{raw_id}"
            else:
                node_id = f"sayou:doc:{raw_id}"

            # 2. Node Class Decision (Semantic Type Mapping)
            sem_type = meta.get("semantic_type", "text")
            is_header = meta.get("is_header", False)

            if is_header:
                node_class = SayouClass.TOPIC
            elif sem_type == "table":
                node_class = SayouClass.TABLE
            elif sem_type == "code_block":
                node_class = SayouClass.CODE
            elif sem_type == "list_item":
                node_class = SayouClass.LIST_ITEM
            else:
                node_class = SayouClass.TEXT

            # 3. Attributes (Vocabulary 사용)
            attributes = {
                SayouAttribute.TEXT: content,
                SayouAttribute.SEMANTIC_TYPE: sem_type,
                SayouAttribute.PAGE_INDEX: meta.get("page_num"),
                SayouAttribute.PART_INDEX: meta.get("part_index"),
                SayouAttribute.SOURCE: meta.get("source"),
            }
            # 기타 메타데이터 보존
            for k, v in meta.items():
                if k not in ["chunk_id", "semantic_type", "parent_id", "is_header"]:
                    attributes[f"meta:{k}"] = v

            # 4. Relationships (Vocabulary 사용)
            relationships = {}
            raw_parent_id = meta.get("parent_id")

            if raw_parent_id:
                if source_name:
                    safe_name = source_name.replace(" ", "_").replace(":", "")
                    std_parent_id = f"sayou:doc:{safe_name}:{raw_parent_id}"
                else:
                    std_parent_id = f"sayou:doc:{raw_parent_id}"

                relationships[SayouPredicate.HAS_PARENT] = [std_parent_id]

            # 5. Create Node
            node = SayouNode(
                node_id=node_id,
                node_class=node_class,
                friendly_name=f"DOC_NODE [{sem_type}] {raw_id}",
                attributes=attributes,
                relationships=relationships,
            )
            nodes.append(node)

        return SayouOutput(nodes=nodes, metadata={"source": "sayou-chunking"})
