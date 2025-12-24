import pytest
import mclang


def test_simple_key_values():
    s = "a=1\nb=2\n"
    doc = mclang.loads(s)
    assert doc.tl("a") == "1"
    assert doc.tl("b") == "2"


def test_continuation_without_key_raises():
    s = "continued line without key\n"
    with pytest.raises(mclang.LANGDecoderError):
        mclang.loads(s)


def test_inline_comment_and_tabs_removed():
    s = "k=hello\tworld #comment\n"
    doc = mclang.loads(s)
    # tabs removed, inline comment removed (trailing space remains)
    assert doc.tl("k") == "helloworld "


def test_single_hash_line_raises():
    s = "# not allowed\n"
    with pytest.raises(mclang.LANGDecoderError):
        mclang.loads(s)


def test_encoder_decoder_roundtrip_multiline_value():
    lang = mclang.Lang({"key": "va\nlue", "other": "x"})
    dumped = mclang.dumps(lang)
    doc = mclang.loads(dumped)
    assert doc.tl("key") == "va\nlue"
    assert doc.tl("other") == "x"


def test_comments_preserved_after_roundtrip():
    s = "## c1\nk=1\n## c2\nk2=2\n"
    doc = mclang.loads(s)
    assert len(doc.comments) == 2
    dumped = mclang.dumps(doc)
    doc2 = mclang.loads(dumped)
    assert doc2.comments[0].text.strip() == "c1"
    assert doc2.comments[1].text.strip() == "c2"
