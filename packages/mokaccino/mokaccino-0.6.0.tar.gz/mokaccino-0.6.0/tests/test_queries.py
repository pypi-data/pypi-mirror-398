from mokaccino import Query
import pytest

def test_query_parsing():
    q = Query.parse("name:sausage")
    assert q is not None
    assert "name=sausage" in str(q)
    with pytest.raises(RuntimeError):
        Query.parse("invalid query string")
    # See other examples of query parsing at
    # https://crates.io/crates/mokaccino


def test_final_queries():
    assert Query.from_kv("field", "value") is not None
    assert Query.from_kprefix("field", "value") is not None
    assert Query.from_klt("field", 123) is not None
    assert Query.from_kle("field", 123) is not None
    assert Query.from_keq("field", 123) is not None
    assert Query.from_kge("field", 123) is not None
    assert Query.from_kgt("field", 123) is not None

def test_combination():
    q1 = Query.from_kv("f", "v")
    assert Query.from_not(q1) is not None

    q2 = Query.from_kv("a", "b")
    assert Query.from_and([q1, q2]) is not None
    assert Query.from_or([q1, q2]) is not None

    assert ( q1 & q2 ) is not None
    assert "f=v" in str(q1 & q2)
    assert "a=b" in str(q1 & q2)

    assert ( q1 | q2 ) is not None
    assert ~q1 is not None

def test_representation():
    # String representation is not generic 
    # mokaccino.Query
    assert "mokaccino.Query" not in str(Query.from_kv("field", "value"))
    assert "field=value" in str(Query.from_kv("field", "value"))
