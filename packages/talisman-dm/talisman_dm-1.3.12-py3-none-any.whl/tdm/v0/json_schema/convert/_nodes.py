from collections import defaultdict
from typing import Callable, Dict, List, Tuple

from tdm.abstract.datamodel import AbstractNode, AbstractNodeLink, BaseNodeMetadata, FrozenMarkup
from tdm.datamodel.mentions import NodeMention
from tdm.datamodel.node_links import TranslationNodeLink
from tdm.datamodel.nodes import ImageNode, ImageNodeMetadata, JSONNode, KeyNode, ListNode, ListNodeMetadata, TableCellNode, \
    TableNode, TableRowNode, TextNode, TextNodeMetadata
from tdm.v0.json_schema.content import NodeType, TreeDocumentContentModel


def _convert_text_node(node: TreeDocumentContentModel) -> TextNode:
    return TextNode(
        content=node.text,
        markup=FrozenMarkup.freeze(node.markup.model_dump()),
        id=node.id,
        metadata=TextNodeMetadata(hidden=node.metadata.hidden, language=node.metadata.language)
    )


def _covert_key_node(node: TreeDocumentContentModel) -> KeyNode:
    return KeyNode(
        content=node.text,
        markup=FrozenMarkup.freeze(node.markup.model_dump()),
        id=node.id,
        metadata=TextNodeMetadata(hidden=node.metadata.hidden, language=node.metadata.language)
    )


def _convert_list_node(node: TreeDocumentContentModel) -> ListNode:
    return ListNode(id=node.id, metadata=ListNodeMetadata(hidden=node.metadata.hidden))


def _convert_json_node(node: TreeDocumentContentModel) -> JSONNode:
    return JSONNode(id=node.id, metadata=BaseNodeMetadata(hidden=node.metadata.hidden))


def _convert_table_node(node: TreeDocumentContentModel) -> TableNode:
    return TableNode(id=node.id, metadata=BaseNodeMetadata(hidden=node.metadata.hidden))


def _convert_table_row_node(node: TreeDocumentContentModel) -> TableRowNode:
    return TableRowNode(id=node.id, metadata=BaseNodeMetadata(hidden=node.metadata.hidden))


def _convert_image_node(node: TreeDocumentContentModel) -> ImageNode:
    return ImageNode(
        content=node.text,
        markup=FrozenMarkup.freeze(node.markup.model_dump()),
        id=node.id,
        metadata=ImageNodeMetadata(hidden=node.metadata.hidden)
    )


NODE_CONVERTERS: Dict[NodeType, Callable[[TreeDocumentContentModel], AbstractNode]] = {
    NodeType.HEADER: _convert_text_node,
    NodeType.TEXT: _convert_text_node,
    NodeType.LIST: _convert_list_node,
    NodeType.JSON: _convert_json_node,
    NodeType.KEY: _covert_key_node,
    NodeType.TABLE: _convert_table_node,
    NodeType.TABLE_ROW: _convert_table_row_node,
    NodeType.IMAGE: _convert_image_node
}


def build_structure(root: TreeDocumentContentModel) -> Tuple[List[AbstractNode], Dict[str, List[str]], List[AbstractNodeLink]]:
    nodes: list[AbstractNode] = []
    structure: dict[str, list[str]] = defaultdict(list)
    node_links: list[AbstractNodeLink] = []

    to_process = [root]  # old document is single tree, so we can start from root

    for node in to_process:
        # create new node for each document node with same type
        converted = NODE_CONVERTERS[node.metadata.node_type](node)
        nodes.append(converted)

        # create separate node with original text (current node is target, original text is source), type is the same
        if node.metadata.original_text is not None:
            if node.metadata.node_type is not NodeType.KEY:
                raise ValueError
            node_links.append(TranslationNodeLink(
                source=NodeMention(KeyNode(content=node.metadata.original_text)),
                target=NodeMention(converted)
            ))

        # text translations are moved to separate nodes linked by translation link (current node is source, translation is target)
        if node.metadata.text_translations:
            if node.metadata.node_type is not NodeType.TEXT and node.metadata.node_type is not NodeType.HEADER:
                raise ValueError
            node_links.extend(
                TranslationNodeLink(
                    source=NodeMention(converted),
                    target=NodeMention(TextNode(content=text, metadata=TextNodeMetadata(language=lang)))
                ) for lang, text in node.metadata.text_translations.items()
            )

        children = node.nodes
        if children:
            if isinstance(converted, TableRowNode):
                # table row should contain only cell nodes (there are no such nodes in old document)
                for c in children:
                    cell = TableCellNode()
                    nodes.append(cell)
                    structure[converted.id].append(cell.id)
                    structure[cell.id].append(c.id)
            else:
                structure[converted.id].extend(map(lambda n: n.id, children))
            to_process.extend(children)

    return nodes, structure, node_links
