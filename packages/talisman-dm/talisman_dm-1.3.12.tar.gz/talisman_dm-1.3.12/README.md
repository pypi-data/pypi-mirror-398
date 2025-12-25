# Talisman Document Model

Talisman Document Model (TDM) python implementation.

Easy way for document creation, modification, serialization and deserialization.

## Main concepts

Document is a special container for partially structured data representation.
It consists of content nodes, structure and extracted facts.

## Basic usage

### Document creation

To create document one of Document factory should be used.
For most cases ``tdm.DefaultDocumentFactory`` is the best choice.
If you need to create document with non-default domain validation, ``tdm.TalismanDocumentFactory`` could be used
(see **Domain** section for details).

The following code could be used to create empty document

```python
from tdm import DefaultDocumentFactory

# create empty document with randomly generated identifier
doc = DefaultDocumentFactory.create_document()

# create empty document with specified identifier
doc = DefaultDocumentFactory.create_document(id_='my document')
```

### Document content

Talisman document content could be represented as oriented partly-ordered acyclic graph.

#### Nodes

There are two principal types of nodes:

* data nodes – store some unstructured data pieces;
* service nodes – represent composite structure (such as lists, tables etc.).

All the nodes are inherited from `tdm.abstract.datamodel.AbstractNode` and are python frozen
[dataclasses](https://docs.python.org/3/library/dataclasses.html).

Each node contains at least some metadata and markup.
Both of metadata and markup is designed to enrich node with some additional information about its form or content.
The main difference is that the set of metadata for each node is used mostly for node display settings and fixed in advance,
while the possible markup is not fixed and can contain almost any information.

Node metadata type is defined by node class implementation, while for markup multipurpose `tdm.abstract.datamodel.markup.FrozenMarkup`
could be used. One should guarantee markup to contain immutable data structures.

For node updates dataclass [replace](https://docs.python.org/3/library/dataclasses.html#dataclasses.replace) method could be utilized.

Node implementations are stored in `tdm.datamodel.nodes` package.

Here is an example of creation and changing nodes.

```python
from tdm.datamodel.nodes import TextNode, TextNodeMetadata
from tdm.abstract.datamodel.markup import FrozenMarkup
from dataclasses import replace

# create text node with auto-generated identifier, default metadata and empty markup.
text_node = TextNode('text only is required, other fields could be omitted')

# replace metadata and markup
modified_node = replace(text_node, metadata=TextNodeMetadata(language='ru'), markup=FrozenMarkup.freeze({'markup key': 'value'}))

# you also could replace node's content, but such modified node couldn't be updated in the document (described below)
changed_content = replace(text_node, content="another text")
```

`TalismanDocument` has two methods to change document nodes: `with_nodes` and `without_nodes`
(both return new document as document is immutable).

```python
from dataclasses import replace

from tdm import DefaultDocumentFactory
from tdm.abstract.datamodel.markup import FrozenMarkup
from tdm.datamodel.nodes import ImageNode, TextNode, TextNodeMetadata

doc = DefaultDocumentFactory.create_document()

text_node = TextNode("some text", metadata=TextNodeMetadata(language='en'), id='0')
image_node = ImageNode("/path/to/image", id='1')

# add new nodes to the document
doc = doc.with_nodes([text_node, image_node])

# to recieve stored nodes you can get mapping identifier -> node
_ = doc.id2node  # {'0': text_node, '1': image_node}

# or get a mapping from type to nodes
_ = doc.nodes  # {TextNode: {text_node}, ImageNode: {image_node}}

# or filter some desired nodes
_ = tuple(doc.get_nodes(TextNode, filter_=lambda n: n.metadata.language == 'en'))  # (text_node,)

# to update nodes just add nodes with same identifier
modified_node = replace(text_node, markup=FrozenMarkup.freeze({'markup key': 'value'}))
doc = doc.with_nodes([modified_node])

_ = doc.id2node  # {'0': modified_node, '1': image_node}

# you can't change type of the node or its content

try:
  doc = doc.with_nodes([replace(text_node, content="another content")])  # can't update node's content
except ValueError:
  pass

try:
  doc = doc.with_nodes([ImageNode("/some/image", id='0')])  # can't update node's type
except ValueError:
  pass

# to remove nodes from document just call without_nodes method with nodes or node ids specified
modified = doc.without_nodes([image_node])  # the same:
modified = doc.without_nodes(['1'])  # the same
modified = doc.without_nodes(['0', image_node])  # you can combine nodes and identifiers
modified = doc.without_nodes(['1', '2', '3'])  # all excess identifiers are silently skipped

_ = modified.id2node  # {'0': modified_node}

# if some stored object depends on node to be removed (and no cascade flag enabled) ValueError is risen

translation_node = TextNode('некоторый текст', metadata=TextNodeMetadata(language='ru'))

from tdm.datamodel.node_links import TranslationNodeLink  # described below
from tdm.datamodel.mentions import NodeMention

translation_link = TranslationNodeLink(NodeMention(modified_node), NodeMention(translation_node), language='ru')
doc = doc.with_nodes([translation_node]).with_node_links([translation_link])

try:
  doc = doc.without_nodes(['0'])  # translation_link depends on modified_node
except ValueError:
  pass

doc = doc.without_nodes(['0'], cascade=True)  # successfully removed both modified_node and translation_link
```

#### Edges

Basically document nodes could be organized as tree-like ordered structures.
Almost each node could have children nodes.
Such connections represent document logical structure and as a rule correspond to document reading order.

Structural node links possibility depends on node types (**o** – ordered, **s** – singleton, **u** – unordered).

    Note: automatic validation is not implemented yet

| from\to     | `Text` | `Key` | `Image` | `File` | `List` | `JSON` | `Table` | `TableRow` | `TableCell` |
|-------------|:------:|:-----:|:-------:|:------:|:------:|:------:|:-------:|:----------:|:-----------:|
| `Text`      |   o    |   -   |    o    |   o    |   o    |   o    |    o    |     -      |      -      |
| `Key`       |   s    |   -   |    s    |   s    |   s    |   s    |    s    |     -      |      -      |
| `Image`     |   -    |   -   |    -    |   -    |   -    |   -    |    -    |     -      |      -      |
| `File`      |   -    |   -   |    -    |   -    |   -    |   -    |    -    |     -      |      -      |
| `List`      |   o    |   -   |    o    |   o    |   o    |   o    |    o    |     -      |      -      |
| `JSON`      |   -    |   u   |    -    |   -    |   -    |   -    |    -    |     -      |      -      |
| `Table`     |   -    |   -   |    -    |   -    |   -    |   -    |    -    |     o      |      -      |
| `TableRow`  |   -    |   -   |    -    |   -    |   -    |   -    |    -    |     -      |      o      |
| `TableCell` |   o    |   -   |    o    |   o    |   o    |   o    |    o    |     -      |      -      |

To add/modify document structure there are several TalismanDocument methods:

* `with_structure` – add some node structure links;
* `with_node_parent` – add one node structure link;
* `with_roots` – remove parent links from specified nodes;
* `with_main_root` – add/update node and remove parent link (if present). Mark this node as main root.

These methods have `update` parameter tht leads nodes update before structure update.
With `force` flag structure updates overwrite existing conflict edges (if possible).

```python
from tdm import DefaultDocumentFactory
from tdm.datamodel.nodes import TextNode, TextNodeMetadata, ImageNode, ListNode

doc = DefaultDocumentFactory.create_document()

header = TextNode("Header", metadata=TextNodeMetadata(header=True, header_level=1))
paragraph = TextNode("First paragraph")
list_node = ListNode()
item1 = TextNode("first item")
item2 = TextNode("second item")
image = ImageNode("/path/to/image")

# add separate nodes to document
with_nodes_doc = doc.with_nodes([header, paragraph, list_node, item1, item2, image])

# set nodes structure
with_structure_doc = with_nodes_doc.with_structure({
    header: [paragraph, list_node, image],
    list_node: [item1, item2]
})

# add nodes with structure to empty document
the_same_doc = doc.with_structure({
    header: [paragraph, list_node, image],
    list_node: [item1, item2]
}, update=True)

assert with_structure_doc == the_same_doc

_ = with_structure_doc.roots  # header
_ = with_structure_doc.child_nodes(header)  # (paragraph, list_node, image)
_ = with_structure_doc.parent(item1)  # list_node

try:
    _ = with_structure_doc.with_node_parent(item2, header)  # item2 already has parent node
except ValueError:
    pass

modified = with_structure_doc.with_node_parent(item2, header, force=True)  # rewrite node parent

# new structure links are appended to existing
_ = modified.child_nodes(header)  # (paragraph, list_node, image, item2)
_ = modified.child_nodes(list_node)  # (item1,)

modified = with_structure_doc.with_roots([list_node])  # remove parent for list_node

_ = modified.roots  # {header, list_node}
_ = modified.child_nodes(header)  # (paragraph, image) – other children with same order

try:
    _ = with_structure_doc.with_node_parent(header, item1)  # circular dependencies are not permitted
except ValueError:
    pass

try:
    _ = with_structure_doc.with_node_parent(header, item1, force=True)  # even with force flag
except ValueError:
    pass
```

Example for table constructing

```python
from typing import Dict, List

from tdm import DefaultDocumentFactory
from tdm.abstract.datamodel import AbstractNode
from tdm.datamodel.nodes import TableCellNode, TableCellNodeMetadata, TableNode, TableRowNode, TextNode, TextNodeMetadata

TABLE_WIDTH = 3
TABLE_HEIGHT = 4

doc = DefaultDocumentFactory.create_document()

# optional document header
header = TextNode("Some header", metadata=TextNodeMetadata(header=True, header_level=1))

table = TableNode()  # table node
table_structure: Dict[AbstractNode, List[AbstractNode]] = {
    header: [table],
    table: []  # will be filled below
}
for i in range(TABLE_HEIGHT):
    row = TableRowNode()
    table_structure[table].append(row)  # TableNode links to its rows
    table_structure[row] = []  # will be filled below
    for j in range(TABLE_WIDTH):
        cell = TableCellNode(metadata=TableCellNodeMetadata(header=(i == 0)))
        table_structure[row].append(cell)  # TableRowNode links to its cells
        table_structure[cell] = [TextNode(f"{i},{j}")]  # TableCellNode links to its content

doc = doc.with_structure(table_structure, update=True)  # add header with child table
```

#### Node semantic links

Along with structural links, document nodes can be linked by semantic links.
Semantic links (as opposed to structural links) have identifiers.
There are no restrictions on the multiplicity and the presence of cycles in the document content graph for semantic links.
Moreover, semantic links can link not a whole node, but part of document nodes.
Semantic links are directed and has some additional semantic meaning.

Now there are three types of node semantic links:

* `TranslationNodeLink` – means that one target node is a translation of source node. This link has additional parameter – language.
* `ReferenceNodeLink` – means that target node is a referenced node of source node.
  This link could be used to represent text footnotes or bibliography references.
* `EquivalenceNodeLink` – means that target node contains the same information (maybe in another form) that the source node.
  This link usually used for OCR retrieved texts representation.

Document has some methods for adding, modifying or retrieving node semantic links.
These methods are very similar to methods for nodes manipulation:

* `id2node_link` – mapping from identifier to semantic link;
* `node_links` – mapping from link type to semantic links of that type;
* `get_node_link` – get node semantic link by its identifier;
* `get_node_links` – get specified type node links (iterator);
* `related_node_links` – get specified type node links that are related for identifiable objects (usually nodes);
* `with_node_links` – add (or update) semantic node links;
* `without_node_links` – remove specified semantic node links.

```python
from dataclasses import replace

from tdm import DefaultDocumentFactory
from tdm.datamodel.node_links import EquivalenceNodeLink, TranslationNodeLink
from tdm.datamodel.mentions import ImageNodeMention, NodeMention
from tdm.datamodel.nodes import ImageNode, ImageNodeMetadata, TextNode, TextNodeMetadata

doc = DefaultDocumentFactory.create_document()

# image node with known size
image_node = ImageNode('/path/to/image', metadata=ImageNodeMetadata(width=200, height=100))

# some text nodes
text_node = TextNode('Some text.')
russian_text_node = TextNode('Некоторый текст.')

# translation link. Means that whole russian_text_node is translation of whole text_node to Russian.
translation_link = TranslationNodeLink(NodeMention(text_node), NodeMention(russian_text_node), language='ru')

# equivalence link. Means that text_node contains the same data that part of image_node 
text_on_image = EquivalenceNodeLink(
  source=ImageNodeMention(image_node, top=10, bottom=20, left=0, right=150),
  target=NodeMention(text_node)
)

doc_with_nodes = doc.with_nodes([image_node, text_node, russian_text_node])
doc_with_links = doc_with_nodes.with_node_links([translation_link, text_on_image])

# with update enabled, link nodes are updated
the_same_doc = doc.with_node_links([translation_link, text_on_image], update=True)

assert doc_with_links == the_same_doc

_ = doc_with_links.related_node_links(text_node)  # both translation_link (text_node is source) and text_on_image (text_node is target)

# get EquivalenceNodeLink for image_node
link = next(doc_with_links.related_node_links(image_node, EquivalenceNodeLink))  # returns only text_on_image link

assert link.target.node.metadata.language is None  # text_node has no language in metadata

updated_node = replace(text_node, metadata=TextNodeMetadata(language='en'))

one_more_link = EquivalenceNodeLink(NodeMention(image_node), NodeMention(updated_node))  # updated node as target
modified_doc = doc_with_links.with_node_links([one_more_link])  # without update flag target node will not be updated
assert modified_doc.get_node(updated_node.id) == text_node

modified_doc = doc_with_links.with_node_links([one_more_link], update=True)  # target node will be updated too
assert modified_doc.get_node(updated_node.id) == updated_node

doc_with_links = doc_with_links.with_nodes([updated_node])  # update text_node

# now equivalence link contains updated node
link = next(doc_with_links.related_node_links(image_node, EquivalenceNodeLink))
assert link.target.node.metadata.language == 'en'
```

### Document facts

Along with semi-structured content, TalismanDocument could be linked to knowledge base (via facts).
Facts represent concepts (some KB item), relations and concept and relation properties.

There are several fact types to represent almost any possible extracted knowledge in graph-like structure.

Each fact has unique identifier and status.
Possible statuses are:

* approved – fact is already approved to be correct and already stored in KB;
* declined – fact is already rejected (incorrect fact);
* auto – fact is marked to be approved automatically (correct fact not stored in KB yet);
* hidden – fact is neither approved nor declined, but is not relevant for downstream task;
* new – fact is neither approved nor declined.

Fact classes are placed in `tdm.datamodel.facts` package

#### Concept facts

Concept facts bind document to some KB object.
Along with identifier and status these facts contain additional required fields: `type_id` and `value`.
`type_id` is a KB concept type identifier that restricts possible concept relations and properties.
`value` is a single KB concept identifier (with confidence) or a tuple of such identifiers (with its confidences).
If concept fact is approved, it should contain the only `value` with approved concept identifier.
If concept fact is new, it should contain tuple of values (maybe empty)

```python
from tdm.datamodel.facts import ConceptFact, KBConceptValue, FactStatus

# not approved person fact with two hypothetical values
cpt = ConceptFact(FactStatus.NEW, "PERSON", (KBConceptValue("Alice", 0.8), KBConceptValue("Bob", 0.1)))
assert cpt.value == (KBConceptValue("Alice", 0.8), KBConceptValue("Bob", 0.1))

# approved fact with single value
cpt = ConceptFact(FactStatus.APPROVED, "PERSON", KBConceptValue("Alice"), id='1')  # if no confidence, 1.0 is assumed
cpt2 = ConceptFact(FactStatus.APPROVED, "PERSON", (KBConceptValue("Alice"),), id='1')  # single element tuple is replaced with element
assert cpt == cpt2

try:
    _ = ConceptFact(FactStatus.APPROVED, "PERSON", (KBConceptValue("Alice", 0.8), KBConceptValue("Bob", 0.1)))
except ValueError:
    pass  # approved facts should contain single value
```

#### Atomic value facts

Atomic value facts (as opposite to composite) represent simple (scalar) values for properties.
As well as concept facts they contain `type_id` and `value`.
`type_id` is a KB value type identifier that restricts possible values.
`value` is a single normalized property value (with confidence) or a tuple of such values (with confidences).
The same status restrictions are applicable for atomic value facts.

There are several the most basic scalar types supported by TDM (placed in `tdm.datamodel.values`):
`StringValue`, `IntValue`, `DoubleValue`, `TimestampValue`, `DateTimeValue`, `GeoPointValue`, `LinkValue`, `StringLocaleValue`.
Other values could be built as composite values.

```python
from dataclasses import replace

from tdm.datamodel.facts import AtomValueFact, FactStatus
from tdm.datamodel.values import Coordinates, Date, DateTimeValue, GeoPointValue, IntValue

# not approved fact with two hypothetical values
value = AtomValueFact(FactStatus.NEW, "AGE", (IntValue(24, 0.8), IntValue(25, 0.4)))
assert value.value == (IntValue(24, 0.8), IntValue(25, 0.4))

# value fact could contain different possible scalar values. Validation is possible with defined domain (described below)
value = AtomValueFact(FactStatus.NEW, "DATE", (DateTimeValue(Date(1999, 1, 2)), GeoPointValue(Coordinates(0, 0))))

try:
    _ = replace(value, status=FactStatus.APPROVED)
except ValueError:
    pass  # approved value couldn't contain more than one value

```

#### Value mentions

Each atomic value fact could be associated with part of the document content via `MentionFact`.
Mention facts contains two required fields: `mention` – node mention (whole node or part of the node) and `value` – atomic value fact.

```python
from tdm.datamodel.facts import AtomValueFact, FactStatus, MentionFact
from tdm.datamodel.mentions import NodeMention, TextNodeMention
from tdm.datamodel.nodes import ImageNode, TextNode
from tdm.datamodel.values import StringValue

text = TextNode("some text")
image = ImageNode("/path/to/image.png")

value = AtomValueFact(FactStatus.NEW, "STR", (StringValue("some"),))

# Associate value fact with part of text node
text_mention_fact = MentionFact(FactStatus.NEW, TextNodeMention(text, 0, 4), value)

# Associate the same value fact with whole image node
image_mention = MentionFact(FactStatus.NEW, NodeMention(image), value)
```

#### Composite value facts

In case property value can't be represented as an atomic value, composite values could be used.

Composite value is a set of named atomic values.
In TDM composite values are represented as a `CompositeValueFact` with set of `SlotFact`s that binds `AtomValueFact` to
`CompositeValueFact`.
Name of each atomic value (as part of composite value) is stored in slot's `type_id` field.

```python
from tdm.datamodel.facts import AtomValueFact, CompositeValueFact, FactStatus, ComponentFact
from tdm.datamodel.values import IntValue, StringValue

composite_fact = CompositeValueFact(FactStatus.NEW, 'ADDRESS')
# address fact value consists of parts: country, city, street, ...

country_atomic_fact = AtomValueFact(FactStatus.NEW, 'STR', (StringValue('Russia'),))
country_fact = ComponentFact(FactStatus.NEW, 'country', composite_fact, country_atomic_fact)

city_fact = ComponentFact(FactStatus.NEW, 'city', composite_fact, AtomValueFact(FactStatus.NEW, 'STR', (StringValue('Moscow')), ))

# target atom fact could have no normalized value 
street_fact = ComponentFact(FactStatus.NEW, 'street', composite_fact, AtomValueFact(FactStatus.NEW, 'STR'))

building_fact = ComponentFact(FactStatus.NEW, 'building', composite_fact, AtomValueFact(FactStatus.NEW, 'INT', (IntValue(25),)))
```

#### Relation facts

Relation fact represents some relationship between concepts mentioned in document.
Each relation fact links two concept facts with some predefined relationship type.
If fact is approved, it could additionally contain `value` (known concepts relationship KB identifier).

```python
from tdm.datamodel.facts import ConceptFact, FactStatus, KBConceptValue, RelationFact

# not approved person fact with two hypothetical values
person = ConceptFact(FactStatus.NEW, "PERSON", (KBConceptValue("Alice", 0.8), KBConceptValue("Bob", 0.1)))
organization = ConceptFact(FactStatus.NEW, "ORGANIZATION", (KBConceptValue("Google", 0.7), KBConceptValue("Amazon", 0.2)))

works_in = RelationFact(FactStatus.NEW, "works in", person, organization)  # relations could link concept facts without approved value

```

#### Property facts

TDM supports two kinds of properties:

* concept property
* relation property

Property fact links concept fact (or relation fact) with some value fact (both atomic and composite values are possible).

```python
from tdm.datamodel.facts import AtomValueFact, ConceptFact, FactStatus, KBConceptValue, PropertyFact, RelationFact, RelationPropertyFact
from tdm.datamodel.values import Date, DateTimeValue, IntValue

person = ConceptFact(FactStatus.NEW, "PERSON", (KBConceptValue("Alice", 0.8), KBConceptValue("Bob", 0.1)))
organization = ConceptFact(FactStatus.NEW, "ORGANIZATION", (KBConceptValue("Google", 0.7), KBConceptValue("Amazon", 0.2)))
works_in = RelationFact(FactStatus.NEW, "works in", person, organization)

age_value = AtomValueFact(FactStatus.NEW, "INT", (IntValue(20),))
age_property = PropertyFact(FactStatus.NEW, "age", person, age_value)  # property links concept fact with value fact

date = AtomValueFact(FactStatus.NEW, "DATE", (DateTimeValue(Date(2000, 9, 1)),))
works_since = RelationPropertyFact(FactStatus.NEW, "works since", works_in, date)
```

#### Document methods for facts

`TalismanDocument` has several methods to process facts.
These methods are very similar to methods for other identifiable document elements:

* `id2fact` – mapping from identifier to fact;
* `facts` – mapping from fact type to facts of that type;
* `get_fact` – get fact by its identifier;
* `get_facts` – get specified type facts;
* `related_facts` – get specified type facts that are related for identifiable objects (no transitive dependencies);
* `with_facts` – add (or update) facts;
* `without_facts` – remove specified facts.

```python
from tdm import DefaultDocumentFactory
from tdm.datamodel.facts import AtomValueFact, ConceptFact, FactStatus, KBConceptValue, MentionFact, PropertyFact, RelationFact, \
RelationPropertyFact
from tdm.datamodel.mentions import TextNodeMention
from tdm.datamodel.nodes import TextNode
from tdm.datamodel.values import Date, DateTimeValue, StringValue

doc = DefaultDocumentFactory.create_document()
text = TextNode('Alexander Pushkin was born on June 6, 1799')

person = ConceptFact(FactStatus.NEW, 'person')
name = AtomValueFact(FactStatus.NEW, "str", (StringValue('Alexander Pushkin'),))
name_mention = MentionFact(FactStatus.NEW, TextNodeMention(text, 0, 17), name)
name_property = PropertyFact(FactStatus.NEW, "name", person, name)

date = AtomValueFact(FactStatus.NEW, "date", (DateTimeValue(Date(1799, 6, 6)),))
date_mention = MentionFact(FactStatus.NEW, TextNodeMention(text, 30, 42), date)
birthday = PropertyFact(FactStatus.NEW, "birth date", person, date)

try:
  _ = doc.with_facts([name_property])
except ValueError:
  pass  # name_property refers to facts that are not contained in the document

# add all the facts to the document
modified = doc.with_nodes([text])  # text node added in the document
modified = modified.with_facts([person, name, name_mention, name_property, date, date_mention, birthday])

# using `update` flag, all nested identifiable objects are added (updated) too.
# Text node is added from mention facts, concept and value facts are added from property facts
the_same = doc.with_facts([name_mention, name_property, date_mention, birthday], update=True)

assert modified == the_same

# even deep nested facts could be added automatically
brin = ConceptFact(FactStatus.APPROVED, "person", KBConceptValue('Sergey Brin'))
google = ConceptFact(FactStatus.NEW, "organization", (KBConceptValue("Google"),))
date = AtomValueFact(FactStatus.APPROVED, "date", DateTimeValue(Date(1998, 9, 4)))
doc = doc.with_facts([
  RelationPropertyFact(
    status=FactStatus.NEW,
    type_id="event date",
    source=RelationFact(FactStatus.NEW, "found", brin, google, id='1'),
    target=date
  )
], update=True)

# to obtain stored facts `get_facts` or `related_facts` methods could be utilized

assert set(doc.get_facts(ConceptFact)) == {brin, google}  # get all concept facts
assert set(doc.get_facts(filter_=ConceptFact.status_filter(FactStatus.APPROVED))) == {brin, date}  # get all approved facts

assert set(doc.related_facts(brin)) == {RelationFact(FactStatus.NEW, "found", brin, google, id='1')}
```

_**Note:**_ When adding new PropertyFact, ComponentFact or RelationPropertyFact that link facts with existing `AtomValueFact` or 
`CompositeValueFact` instances in the document, it is useful to use the `link_fact_factory` method beforehand to prevent deduplication 
issues.
```python
from tdm import DefaultDocumentFactory
from tdm.datamodel.domain import AtomValueType, ConceptType, PropertyType
from tdm.datamodel.facts import AtomValueFact, ConceptFact, FactStatus, MentionFact, PropertyFact
from tdm.datamodel.mentions import TextNodeMention
from tdm.datamodel.nodes import TextNode
from tdm.datamodel.values import Date, DateTimeValue
from tdm.utils import link_fact_factory

doc = DefaultDocumentFactory.create_document()
text = TextNode('Alexander Pushkin was born on June 6, 1799')

cpt_type = ConceptType("Person", id="person")
date_type = AtomValueType("Date", DateTimeValue, id="date")
prp_type = PropertyType("Birthday", cpt_type, date_type, id="birthday")
new_prp_type = PropertyType("Important date", cpt_type, date_type, id="important")

person = ConceptFact(FactStatus.NEW, cpt_type)

date = AtomValueFact(FactStatus.NEW, "date", (DateTimeValue(Date(1799, 6, 6)),))
date_mention = MentionFact(FactStatus.NEW, TextNodeMention(text, 30, 42), date)
birth_prop = PropertyFact(FactStatus.NEW, prp_type, person, date)

# add all the facts to the document
with_birthday = doc.with_nodes([text]).with_facts([person, birth_prop, date, date_mention])

# BAD way of creation:
important_prop = PropertyFact(FactStatus.NEW, new_prp_type, person, date)
bad_doc = with_birthday.with_facts([important_prop])
assert len(tuple(bad_doc.related_facts(date, PropertyFact))) == 2  # date would duplicate in two properties

# CORRECT way of creation new chain of facts with copied value and new property fact
property_facts = link_fact_factory(new_prp_type)(source=person, target=date, doc=with_birthday)

# add facts to document
with_new_facts = with_birthday.with_facts(property_facts)
assert len(tuple(with_new_facts.related_facts(date, PropertyFact))) == 1  # date would not duplicate in two properties
```

#### Domain

To validate linked facts consistency domain could be utilized.

Domain consists of a set of domain types.
Domain types are identifiable and inherit base interface `tdm.abstract.datamodel.AbstractDomainType`.
Knowledge base domain could be represented as a graph with node types and edge types.

TalismanDocument supports following principal knowledge base entity types (one for each fact type).
All the domain type classes are in `tdm.datamodel.domain.types` package.

Node types:

* `ConceptType` – for `ConceptFact`s. Represents a set of knowledge base concepts (objects) that share the same set of possible relations
  and properties. These domain types define no additional restrictions;
* `AtomValueType` – for `AtomValueFact`. Represents a simple value that could be used in properties and as a part of composite value.
  These domain types restrict possible values of corresponding `AtomValueFact`s;
* `CompositeValueType` – for `CompositeValueFact`s. These domain types define no additional restrictions.

Link types (define restrictions for corresponding facts):

* `SlotType` – for `SlotFact`. Represents a possible link between `CompositeValueType` and `AtomValueType`.
* `RelationType` – for `RelationFact`. Represents a possible link between two `ConeptType`s.
* `PropertyType` – for `PropertyFact`. Represents a possible link between `ConceptType` and value type (`AtomValueType` or
  `CompositeValuetype`).
* `RelationPropertyType` – for `RelationPropertyFact`. epresents a possible link between `RelationType` and value type (`AtomValueType` or
  `CompositeValuetype`).

`tdm.datamodel.Domain` class is used for organization domain types as a graph. It supports types retrieving (methods are very similar to
`TalismanDocument` ones).

```python
from tdm.datamodel.domain import Domain
from tdm.datamodel.domain.types import ConceptType, RelationType

person = ConceptType('person', id='1')
organization = ConceptType('organization', id='2')
works_in = RelationType('works in', person, organization, id='3')

domain = Domain([person, organization, works_in])

assert domain.get_type('1') == person
assert next(domain.related_types(person)) == works_in
assert domain.id2type == {'1': person, '2': organization, '3': works_in}
```

#### Facts validation with domain

Domain could be set to document to be applied as facts validator.

With `tdm.datamodel.domain.set_default_domain` method you can set default domain.
All the documents created by `tdm.DefaultDocumentFactory` after default domain is set, will be linked with domain.
It leads to facts consistency validation. Moreover, all fact `type_id`s will be automatically replaced with corresponding domain types.

Once document is created, it uses domain that was set at creation time.

Using `tdm.TalismanDocumentFactory` non-default domain could be used for documents.

```python
from tdm import DefaultDocumentFactory
from tdm.datamodel.domain import AtomValueType, ConceptType, Domain, PropertyType, set_default_domain
from tdm.datamodel.facts import AtomValueFact, ConceptFact, FactStatus, PropertyFact
from tdm.datamodel.values import IntValue, StringValue

cpt_type = ConceptType("Персона", id="person")
value_type = AtomValueType("Число", IntValue, id="int")
prp_type = PropertyType("Возраст", cpt_type, value_type, id="age")
domain = Domain([cpt_type, value_type, prp_type])

# create document before default domain is set
doc1 = DefaultDocumentFactory.create_document()

set_default_domain(domain)

doc2 = DefaultDocumentFactory.create_document()  # this document contains default domain

set_default_domain(None)  # release default domain, but doc2 still has domain

prp = PropertyFact(
  FactStatus.NEW, "age",
  ConceptFact(FactStatus.NEW, "person", id="cpt"),
  AtomValueFact(FactStatus.NEW, "int", (StringValue("23"),), id="value"),
  id="prp"
)

# add facts without validation as domain 
doc1 = doc1.with_facts([prp], update=True)
assert doc1.get_fact("prp") == prp

try:
  _ = doc2.with_facts([prp], update=True)
except ValueError:
  pass  # atom value fact contains incorrect normalized value

doc2 = doc2.with_facts([PropertyFact(
  FactStatus.NEW, "age",
  ConceptFact(FactStatus.NEW, "person", id="cpt"),
  AtomValueFact(FactStatus.NEW, "int", (IntValue(23),), id="value"),  # corrected value
  id="prp"
)], update=True)

assert doc2.get_fact("cpt").type_id == cpt_type  # type id is replaced with domain type
assert doc2.get_fact("cpt") == ConceptFact(FactStatus.NEW, "person", id="cpt")  # it still equals to original fact
```

## Serialization

To serialize and deserialize a Talisman document `tdm.TalismanDocumentModel` could be utilized.
TalismanDocumentModel is a pydantic model, so you can write and read it to json with pydantic methods.

To serialize document `TalismanDocumentModel.serialize` method should be used.
It returns `TalismanDocumentModel` which could be converted to json.

```python
from tdm import DefaultDocumentFactory, TalismanDocumentModel

document = DefaultDocumentFactory.create_document()

# fill document with nodes, links and facts

model = TalismanDocumentModel.serialize(document)
json = model.model_dump_json()  # obtain json with pydantic model method
```

To deserialize `TalismanDocumentModel` to `TalismanDocuemnt`, `TalismanDocumentModel.deserialize` method should be used.

```python
from tdm import TalismanDocumentModel

obj = ...  # Obtain the serialized TalismanDocumentModel object
model = TalismanDocumentModel.model_validate(obj)  # parse it to TalismanDocumentModel

document = model.deserialize()
```

## Customization

### Node markup

#### Default node markup

Each document node (both data and service) could contain additional markup that stores some additional information about document node.
As opposed to node metadata, node markup is not fixed and could be extended with almost any possible information.
Talisman document node markup should implement `tdm.abstract.datamodel.AbstractMarkup` interface.
Markup is assumed to be a mapping. The only other requirement is node markup immutability.

There is a default node markup implementation `tdm.abstract.datamodel.FrozenMarkup`.
This markup should be instantiated with `FrozenMarkup.freeze` method to guarantee object immutability.

```python
from immutabledict import immutabledict

from tdm.abstract.datamodel import FrozenMarkup

markup = FrozenMarkup.freeze({
  'str': 'string',
  'int': 1,
  'float': 1.5,
  'tuple': (1, 2, 3),
  'list': [1, 2, 3],
  'nested': {
    'tuple of lists': (['item'], ['another'])
  }
})

frozen = immutabledict({
  'str': 'string',
  'int': 1,
  'float': 1.5,
  'tuple': (1, 2, 3),
  'list': (1, 2, 3),
  'nested': immutabledict({
    'tuple of lists': (('item',), ('another',))
  })
})

assert markup.markup == frozen
```

#### Markup customization

`FrozenMarkup` is simple immutable container that doesn't provide any methods for changing the stored markup.
For more convenient markup usage one could implement its own markup class with predefined structure.

Following example illustrates markup class implemented for `TextNode` (but it could be used for other node types).
Text node markup (`MyMarkup`) will contain int pointer (with other possible markup) that should point to some node's text character.

```python
from immutabledict import immutabledict
from typing_extensions import Self

from tdm.abstract.datamodel import AbstractMarkup


class MyMarkup(AbstractMarkup):
  """
  Custom markup class that stores int value and have additional methods for retrieving and modifying markup
  Custom markup classes should be immutable and hashable
  """

  def __init__(self, pointer: int, other: immutabledict):
    self._pointer = pointer
    self._other = other

  @property
  def markup(self) -> immutabledict:
    """
    this property should be defined to return correct immutabledict markup representation
    this representation is used for other markups construction (see `from_markup`) and for serialization
    """
    return immutabledict({
      'pointer': self._pointer,
      **self._other
    })

  @classmethod
  def from_markup(cls, markup: AbstractMarkup) -> Self:
    """
    this method should be defined for object construction from another markup object
    """
    kwargs: immutabledict = markup.markup
    pointer = kwargs.get('pointer', 0)
    other = immutabledict({k: v for k, v in kwargs.items() if k != 'pointer'})
    return MyMarkup(pointer, other)

  # user defined method for markup manipulation

  @property
  def pointer(self):
    """
    example property
    """
    return self._pointer

  def distance(self, pointer: int) -> int:
    """
    example non-modifier method
    """
    return abs(self._pointer - pointer)

  def set_pointer(self, pointer: int) -> Self:
    """
    example modifier method
    """
    if pointer < 0:
      raise ValueError  # modifiers could raise exceptions to avoid illegal markup states
    return MyMarkup(pointer, self._other)


# now you can use this markup with any node
from tdm.datamodel.nodes import TextNode
from tdm.abstract.datamodel import FrozenMarkup
from dataclasses import replace

markup = FrozenMarkup.freeze({'pointer': 1, 'another': 'some other markup values'})
node = TextNode('some text', markup=markup)

my_markup = MyMarkup.from_markup(markup)
assert my_markup == markup  # this is not required because markup constructor could add some fields (e.g. pointer)
assert FrozenMarkup.from_markup(my_markup) == my_markup  # this is always true

my_node = replace(node, markup=my_markup)
assert my_node == node  # node with custom markup is still equal to original node


def set_pointer(node: TextNode, pointer: int) -> TextNode:
  # to ensure pointer is correct we should create separate method for node markup update
  if len(node.content) <= pointer:
    raise ValueError
  return replace(node, markup=node.markup.set_pointer(pointer))  # here we additionally should guarantee node.markup is a MyMarkup object


try:
  _ = set_pointer(my_node, 10)
except ValueError:
  pass

changed = set_pointer(my_node, 5)


```

To reduce boilerplate code talisman-dm library provide some useful decorators to create node subclasses with desired markup implementation.
All the decorators are placed in `tdm.wrapper.node` package.

First of all we should define markup (and node) interface.
The interface methods should be decorated with `tdm.wrapper.node.getter` and `tdm.wrapper.node.modifier` methods to automatically generate
its implementation for wrapper node class.

Node wrapper could be generated with `tdm.wrapper.generate_wrapper` decorator.
It should decorate class that is subclass for some `AbstractNode` implementation, desired interface
and `tdm.wrapper.node.AbstractNodeWrapper`.
This decorator automatically generates implementations for all interface methods marked with method decorators.
Additionally, node wrapper could contain modifier methods additional validators that are performed just before markup changes.
These validators could have any name, but should be decorated with `tdm.wrapper.node.validate` decorator and have the same signature
that validated method.
All the getter method results could be post processed with `tdm.wwrapper.node.pos_process` decorator.
The method is applied for getter results.
Decorated post processor could also have any name.

```python
from abc import ABCMeta, abstractmethod

from immutabledict import immutabledict
from typing_extensions import Self

from tdm.abstract.datamodel import AbstractMarkup
from tdm.datamodel.nodes import TextNode
from tdm.wrapper.node import AbstractNodeWrapper, generate_wrapper, getter, modifier, post_process, validate


class MyMarkupInterface(metaclass=ABCMeta):
    """
    Special interface for both markup and node wrapper implementations with desired getters and modifiers 
    """

    @property
    @abstractmethod
    def pointer(self) -> int:
        """
        properties could not be additionally decorated.
        Node wrapper will automatically delegate it to markup
        """
        pass

    @getter
    @abstractmethod
    def distance(self, pointer: int) -> int:
        """
        all getters (methods that don't change the markup object) should be decorated with `getter`
        """
        pass

    @modifier
    @abstractmethod
    def set_pointer(self, pointer: int) -> Self:
        """
        all modifiers (methods that create new markup object) should be decorated with `modifier`
        """
        pass


class _MyMarkup(AbstractMarkup):
    """
    Custom markup class that stores int pointer and have additional methods for retrieving and modifying markup
    
    It could be non-public as user should not use it directly.
    """

    def __init__(self, pointer: int, other: immutabledict):
        self._pointer = pointer
        self._other = other

    @property
    def markup(self) -> immutabledict:
        """
        this property should be defined to return correct immutabledict markup representation
        this representation is used for other markups construction (see `from_markup`) and for serialization
        """
        return immutabledict({
            'pointer': self._pointer,
            **self._other
        })

    @classmethod
    def from_markup(cls, markup: AbstractMarkup) -> Self:
        """
        this method should be defined for object construction from another markup object
        """
        kwargs: immutabledict = markup.markup
        pointer = kwargs.get('pointer', 0)
        other = immutabledict({k: v for k, v in kwargs.items() if k != 'pointer'})
        return _MyMarkup(pointer, other)

    # user defined method for markup manipulation

    @property
    def pointer(self):  # implementation is the same
        return self._pointer

    def distance(self, pointer: int) -> int:  # implementation is the same
        return abs(self._pointer - pointer)

    def set_pointer(self, pointer: int) -> Self:  # implementation is the same
        if pointer < 0:
            raise ValueError  # modifiers could raise exceptions to avoid illegal markup states
        return _MyMarkup(pointer, self._other)


@generate_wrapper(_MyMarkup)
class TextNodeWrapper(TextNode, MyMarkupInterface, AbstractNodeWrapper[TextNode], metaclass=ABCMeta):
    @validate(MyMarkupInterface.set_pointer)  # validator for set_pointer method
    def _validate_value(self, pointer: int) -> None:
        """
        this method is called before markup update, so old markup object also could be used for validation.
        this method could use node for validation
        return value is ignored
        """
        if pointer >= len(self.content):
            raise ValueError

    @post_process(MyMarkupInterface.distance)  # post processor for distance getter
    def _post_process(self, result: int) -> int:
        """
        this method is called for node.markup.distance method result
        """
        return result + 1


# now you can use this node wrapper to modify text node markup
from tdm.datamodel.nodes import TextNode
from tdm.abstract.datamodel import FrozenMarkup

markup = FrozenMarkup.freeze({'pointer': 1, 'another': 'some other markup values'})
node = TextNode('some text', markup=markup)

wrapped_node = TextNodeWrapper.wrap(node)

assert wrapped_node == node  # wrapped node with custom markup is still equal to original node

try:
    _ = wrapped_node.set_pointer(10)  # validator will raise an error
except ValueError:
    pass

changed = wrapped_node.set_pointer(5)
```

#### Composite markup customization

Talisman document node could have several types of markup with different origins.
For example text node could have appearance markup (font, size, etc.) and text content markup (e.g. segmentation).
In order not to mix the markup, it is convenient to separate such markup with different top-level keys.

For such cases talisman-dm library provide `tdm.wrapper.node.composite_markup` decorator.
This decorator compose several markups with specified keys.
So the wrapped node could work with several markup objects at the same time.

```python
from abc import ABCMeta, abstractmethod
from typing import Tuple
from typing_extensions import Self
from immutabledict import immutabledict

from tdm.wrapper.node import modifier, composite_markup, generate_wrapper, AbstractNodeWrapper, validate
from tdm.datamodel.nodes import TextNode
from tdm.abstract.datamodel import AbstractMarkup


class AppearanceMarkup(metaclass=ABCMeta):
    """
    Interface for appearance markup
    """

    @property  # property could not be decorated
    @abstractmethod
    def fonts(self) -> Tuple[str, ...]:
        pass

    @modifier  # decorator for markup modifier
    @abstractmethod
    def add_font(self, start: int, end: int, font: str) -> Self:
        pass


class _AppearanceMarkupImpl(AbstractMarkup, AppearanceMarkup):
    """
    implementation could be non-public
    """

    def __init__(self, fonts: Tuple[Tuple[int, int, str], ...]):
        self._fonts = fonts

    @property
    def markup(self) -> immutabledict:  # markup piece implementation could suppose it is root node markup
        return immutabledict({'fonts': self._fonts})

    @classmethod
    def from_markup(cls, markup: AbstractMarkup) -> Self:
        markup = markup.markup
        return cls(markup.get('fonts', ()))

    @property
    def fonts(self) -> Tuple[str, ...]:
        return tuple(f for _, _, f in self._fonts)

    def add_font(self, start: int, end: int, font: str) -> Self:  # some validation could be added
        return _AppearanceMarkupImpl(self._fonts + ((start, end, font),))


class TextMarkup(metaclass=ABCMeta):
    """
    Interface for text genre markup
    """

    @property
    @abstractmethod
    def genre(self) -> str:
        pass

    @modifier
    @abstractmethod
    def set_genre(self, genre: str) -> Self:
        pass


class _TextMarkupImpl(AbstractMarkup, TextMarkup):
    def __init__(self, genre: str):
        self._genre = genre

    @property
    def markup(self) -> immutabledict:
        return immutabledict({'genre': self._genre})

    @classmethod
    def from_markup(cls, markup: AbstractMarkup) -> Self:
        return cls(markup.markup['genre'])

    @property
    def genre(self) -> str:
        return self._genre

    def set_genre(self, genre: str) -> Self:
        return _TextMarkupImpl(genre)


@composite_markup(appearance=_AppearanceMarkupImpl, text=_TextMarkupImpl)  # with this decorator we define top-level keys
class _CompositeTextNodeMarkup(AbstractMarkup, AppearanceMarkup, TextMarkup, metaclass=ABCMeta):
    """
    This class is fully automatically generated.
    It implements both `AppearanceMarkup` and `TextMarkup` interfaces
    All the markup other from defined top-level keys will remain untouched
    """
    pass


@generate_wrapper(_CompositeTextNodeMarkup)
class TextNodeWrapper(TextNode, AppearanceMarkup, TextMarkup, AbstractNodeWrapper[TextNode], metaclass=ABCMeta):
    @validate(AppearanceMarkup.add_font)
    def _validate_span(self, start: int, end: int, font: str) -> None:  # validators still could be used for markup methods
        if end >= len(self.content):
            raise ValueError


# now generated wrapper could be applied to work with both appearance and text genre

from tdm.abstract.datamodel import FrozenMarkup

node = TextNode('Some text', markup=FrozenMarkup.freeze({
    'appearance': {'fonts': ((0, 4, 'comic sans'),)},
    'text': {'genre': 'example'},
    'extra': 'some extra markup'
}))

wrapped = TextNodeWrapper.wrap(node)

assert node == wrapped  # node is equal to wrapped one

try:
    _ = wrapped.add_font(0, 10, 'out of bound span')
except ValueError:
    pass

modified = wrapped.add_font(5, 9, 'times new roman')

assert 'extra' in modified.markup.markup  # extra markup fields still presented in node

```