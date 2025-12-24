"""
Translate a key to text (with subs)
"""

from mclang import tl, init


def test_translate():
    # initilize builtin translator.
    init("tests/texts")

    # Translate and print text.
    case = tl("translation.test.args", "SUB1", "SUB2")
    assert case == "SUB1 SUB2"

    case = tl("translation.test.args", "SUB1")
    assert case == "SUB1 SUB1"

    case = tl("translation.test.complex", "SUB1", "SUB2")
    assert case == "Prefix, SUB2 again SUB1 and SUB1 lastly SUB2 and also SUB1 again!"


if __name__ == "__main__":
    test_translate()
