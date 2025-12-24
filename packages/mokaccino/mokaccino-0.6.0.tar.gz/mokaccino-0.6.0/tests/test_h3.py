
import pytest
from mokaccino import Query, Percolator, Document

def test_h3_query():
    # cell index for San Francisco
    # Resolution 5 cell: 85283473fffffff
    cell = "85283473fffffff"

    # Create a query for location in this cell
    q = Query.from_h3in("location", cell)

    p = Percolator()
    qid = p.add_query(q)

    # 1. Document inside the cell
    # A child cell (resolution 6) inside the parent cell
    # Parent: 85283473fffffff
    # Child:  862834737ffffff (This is just an example, need a real child)
    # Using the same cell should match (contains or equal)
    doc_match = Document().with_value("location", cell)
    matches = p.percolate_list(doc_match)
    assert qid in matches

    # 2. Document outside the cell
    # A different cell at same resolution
    other_cell = "85283477fffffff"
    doc_no_match = Document().with_value("location", other_cell)
    matches = p.percolate_list(doc_no_match)
    assert qid not in matches

def test_h3_query_parsing():
    q = Query.parse("location H3IN 85283473fffffff")
    assert q is not None
    # We can't inspect the query structure easily, but we can test it works
    p = Percolator()
    qid = p.add_query(q)

    doc_match = Document().with_value("location", "85283473fffffff")
    matches = p.percolate_list(doc_match)
    assert qid in matches

def test_invalid_h3_cell():
    with pytest.raises(RuntimeError, match="Invalid h3 cell index"):
        Query.from_h3in("location", "invalid_hex")
