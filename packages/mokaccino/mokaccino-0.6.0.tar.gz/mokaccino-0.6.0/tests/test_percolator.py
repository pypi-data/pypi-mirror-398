from mokaccino import Percolator, Query, Document
import pytest

def test_deserialise_fail():
    invalid_jsons = [
        "",
        "not a json",
        '{"invalid": "structure"}',
        '{"queries": ["not a query"]}',
    ]
    for invalid_json in invalid_jsons:
        with pytest.raises(RuntimeError):
            Percolator.from_json(invalid_json)
        

def test_percolator_works():
    p = Percolator()
    assert p is not None
    qids = [
        p.add_query(Query.parse("name:sausage")),
        p.add_query(Query.parse("name:amaz*")),
        p.add_query(Query.parse("price>12")),
        p.add_query(Query.parse("name:sausage OR price>12")),
    ]
    percolator_test(p, qids)

    # Test serialisation
    assert p.to_json() is not None

    p2 = Percolator.from_json(p.to_json())
    assert p2 is not None
    # The deserialized percolator should give the same results
    percolator_test(p2, qids)



def percolator_test(p: Percolator, qids: list[int]):
    

    assert p.percolate_list(Document()) == []
    assert p.percolate_list(Document().with_value("name", "burger")) == []
    assert p.percolate_list(Document().with_value("name", "sausage")) == [qids[0], qids[3]]
    assert p.percolate_list(Document().with_value("name", "amaz")) == [qids[1]]
    assert p.percolate_list(Document().with_value("name", "amazing")) == [qids[1]]
    assert p.percolate_list(Document().with_value("name", "amazon")) == [qids[1]]
    assert p.percolate_list(Document().with_value("price", "12")) == []
    assert p.percolate_list(Document().with_value("price", "13")) == [qids[2], qids[3]]
    assert p.percolate_list(
        Document().with_value("price", "13").with_value("name", "amazed")
    ) == [qids[1], qids[2], qids[3]]
