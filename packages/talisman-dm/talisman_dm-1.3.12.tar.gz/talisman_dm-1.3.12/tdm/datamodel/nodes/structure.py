from dataclasses import dataclass
from typing import Optional

from tdm.abstract.datamodel import AbstractNode, BaseNodeMetadata
from tdm.abstract.json_schema import generate_model


@dataclass(frozen=True)
class ListNodeMetadata(BaseNodeMetadata):
    """
    List node metadata

    Attributes
    --------
    bullet:
        bullet type used for each list item
    """
    bullet: Optional[str] = None


@generate_model(label='list')
@dataclass(frozen=True)
class ListNode(AbstractNode[ListNodeMetadata]):
    """
    Service node to represent ordered list.
    Each direct child is an item of this list.
    """
    pass


@generate_model(label='json')
@dataclass(frozen=True)
class JSONNode(AbstractNode[BaseNodeMetadata]):
    """
    Service node to represent key-value mapping.
    Children nodes are keys in key-value pairs.

    Each direct child should be ``KeyNode``.
    """
    pass


@generate_model(label='table')
@dataclass(frozen=True)
class TableNode(AbstractNode[BaseNodeMetadata]):
    """
    Service node to represent table.
    Children nodes are rows of the table.

    Each direct child should be ``TableRowNode``.
    """
    pass


@generate_model(label='row')
@dataclass(frozen=True)
class TableRowNode(AbstractNode[BaseNodeMetadata]):
    """
    Service node to represent table row.
    Children nodes ore cells of the table row.

    Each direct child should be ``TableCell``.
    Nodes of this type could be direct children only for a ``TableNode``
    """
    pass


@dataclass(frozen=True)
class TableCellNodeMetadata(BaseNodeMetadata):
    """
    Table cell metadata.

    Attributes
    --------
    header:
        header indicator
    colspan:
        width of the cell (in columns)
    rowspan:
        height of the cell (in rows)
    """
    header: Optional[bool] = None
    colspan: Optional[int] = None
    rowspan: Optional[int] = None


@generate_model(label='cell')
@dataclass(frozen=True)
class TableCellNode(AbstractNode[TableCellNodeMetadata]):
    """
    Service node to represent table cell.
    Children nodes ore the cell content.

    Nodes of this type could be direct children only for a ``TableRowNode``
    """
    pass
