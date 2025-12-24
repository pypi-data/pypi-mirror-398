"""
Converts a .lang string to a Lang.
"""

import mclang


def test_loads():
    lang = """
    test=This is cool!
    test2=It worked!
    key=va
    lue
    """

    doc = mclang.loads(lang)

    assert doc.tl("test") == "This is cool!"
    assert doc.tl("key") == "va\nlue"
