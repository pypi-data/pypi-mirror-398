from mokaccino import Document


def test_build():
    d = Document()
    assert d is not None
    d = d.with_value("field", "v1")
    d = d.with_value("field", "v2")
    d = d.with_value("field", "v3")
    d = d.with_value("taste", "sweet")
    assert d is not None
    # Not the default str repr.
    assert "mokaccino.Document" not in str(d)
    assert next(vf for vf in d.field_values() if vf == ("field", "v2"))
    assert next(vf for vf in d.field_values() if vf == ("taste", "sweet"))

    d = Document().with_value("field", "v1")
    d2 = d.merge_with(Document().with_value("field", "v2"))
    assert next(vf for vf in d2.field_values() if vf == ("field", "v1"))
    assert next(vf for vf in d2.field_values() if vf == ("field", "v2"))


def test_inplace_change():
    d = Document()
    d.add_value("field", "v1")
    d.add_value("field", "v2")
    d.add_value("field", "v3")
    d.add_value("taste", "sweet")
    assert d is not None

    # Not the default str repr.
    assert "mokaccino.Document" not in str(d)
    assert next(vf for vf in d.field_values() if vf == ("field", "v2"))
    assert next(vf for vf in d.field_values() if vf == ("taste", "sweet"))

    d = Document().with_value("field", "v1")
    d2 = d.merge_with(Document().with_value("field", "v2"))
    assert next(vf for vf in d2.field_values() if vf == ("field", "v1"))
    assert next(vf for vf in d2.field_values() if vf == ("field", "v2"))
