import os
import sys
from pathlib import Path
import io

if __name__ == "__main__":  # to make the tests run without the pytest cli
    import os, sys # three lines to use the local package and chdir
    os.chdir(os.path.dirname(__file__))
    sys.path.insert(0, os.path.dirname(__file__) + "/../")

import pytest

import xlwings_utils as xwu


def test_block0():
    this_block = xwu.block(number_of_rows=4, number_of_columns=6)
    this_block[1, 2] = 2
    this_block[2, 5] = 25
    assert this_block.dict == {(1, 2): 2, (2, 5): 25}
    assert this_block.value == [
        [None, 2, None, None, None, None],
        [None, None, None, None, 25, None],
        [None, None, None, None, None, None],
        [None, None, None, None, None, None],
    ]
    assert this_block.minimized().value == [[None, 2, None, None, None], [None, None, None, None, 25]]
    assert this_block.number_of_rows == 4
    assert this_block.number_of_columns == 6
    assert this_block.highest_used_row_number == 2
    assert this_block.highest_used_column_number == 5

    this_block.number_of_rows = 99
    this_block.number_of_columns = 99
    assert this_block.highest_used_row_number == 2
    assert this_block.highest_used_column_number == 5

    this_block.number_of_rows = 1
    this_block.number_of_columns = 3
    assert this_block.value == [[None, 2, None]]
    assert this_block.minimized().value == [[None, 2]]


def test_block1():
    this_block = xwu.block.from_value([[1, 2, 3], [4, 5, 6]])
    assert this_block.dict == {(1, 1): 1, (1, 2): 2, (1, 3): 3, (2, 1): 4, (2, 2): 5, (2, 3): 6}
    assert this_block.value == [[1, 2, 3], [4, 5, 6]]
    assert this_block.minimized().value == [[1, 2, 3], [4, 5, 6]]
    with pytest.raises(ValueError):
        this_block.number_of_rows = 0
    with pytest.raises(ValueError):
        this_block.number_of_columns = 0
    with pytest.raises(ValueError):
        this_block = xwu.block(number_of_rows=0, number_of_columns=1)
    with pytest.raises(ValueError):
        this_block = xwu.block(number_of_rows=1, number_of_columns=0)


def test_block2():
    this_block = xwu.block.from_value([[1, 2, 3], [4, 5, 6]]).reshape(number_of_rows=1)
    assert this_block.value == [[1, 2, 3]]

    this_block = xwu.block.from_value([[1, 2, 3], [4, 5, 6]]).reshape(number_of_rows=1, number_of_columns=2)
    assert this_block.value == [[1, 2]]

    this_block = xwu.block.from_value([[1, 2, 3], [4, 5, 6]]).reshape(number_of_rows=3, number_of_columns=4)
    assert this_block.value == [[1, 2, 3, None], [4, 5, 6, None], [None, None, None, None]]


def test_highest_used():
    this_block = xwu.block(number_of_rows=4, number_of_columns=4)
    assert this_block._highest_used_row_number is None
    assert this_block.highest_used_row_number == 1
    assert this_block.highest_used_column_number == 1
    this_block[2, 3] = 1
    assert this_block._highest_used_row_number is not None
    assert this_block.highest_used_row_number == 2
    assert this_block.highest_used_column_number == 3
    this_block[1, 2] = 1
    assert this_block._highest_used_row_number is not None
    assert this_block.highest_used_row_number == 2
    assert this_block.highest_used_column_number == 3
    this_block[3, 4] = 1
    assert this_block._highest_used_row_number is not None
    assert this_block.highest_used_row_number == 3
    assert this_block.highest_used_column_number == 4
    this_block[3, 4] = None
    assert this_block._highest_used_row_number is None
    assert this_block.highest_used_row_number == 2
    assert this_block.highest_used_column_number == 3
    this_block[2, 3] = None
    assert this_block._highest_used_row_number is None
    this_block[2, 3] = 1
    assert this_block._highest_used_row_number is None
    this_block[2, 3] = None
    this_block[1, 2] = None
    assert this_block._highest_used_row_number is None
    assert this_block.highest_used_row_number == 1
    assert this_block.highest_used_column_number == 1
    assert this_block._highest_used_row_number is not None


def test_block_one_dimension():
    this_block = xwu.block.from_value([1, 2, 3])
    assert this_block.value == [[1, 2, 3]]

    this_block = xwu.block.from_value([1, 2, 3], column_like=True)
    assert this_block.value == [[1], [2], [3]]


def test_block_scalar():
    this_block = xwu.block.from_value(1)
    assert this_block.value == [[1]]


def test_transpose():
    this_block = xwu.block.from_value([[1, 2, 3], [4, 5, 6]])
    transposed_block = this_block.transposed()
    assert transposed_block.value == [[1, 4], [2, 5], [3, 6]]


def test_delete_none():
    this_block = xwu.block.from_value([[1, 2, None], [4, 5, None]])
    assert len(this_block.dict) == 4
    this_block[1, 1] = None
    assert len(this_block.dict) == 3
    this_block[1, 1] = None
    assert len(this_block.dict) == 3
    assert this_block.value == [[None, 2, None], [4, 5, None]]


def test_raise():
    this_block = xwu.block(number_of_rows=4, number_of_columns=6)
    with pytest.raises(IndexError):
        a = this_block[0, 1]
    with pytest.raises(IndexError):
        a = this_block[5, 1]

    with pytest.raises(IndexError):
        a = this_block[1, 0]
    with pytest.raises(IndexError):
        a = this_block[1, 7]

    with pytest.raises(IndexError):
        this_block[0, 1] = 1
    with pytest.raises(IndexError):
        this_block[5, 1] = 1

    with pytest.raises(IndexError):
        this_block[1, 0] = 1
    with pytest.raises(IndexError):
        this_block[1, 7] = 1


def test_lookup():
    bl = xwu.block.from_value([[1, "One", "Un"], [2, "Two", "Deux"], [3, "Three", "Trois"]])
    assert bl.lookup(1) == "One"
    assert bl.lookup(3, column2=3) == "Trois"
    with pytest.raises(ValueError):
        bl.lookup(4)
    assert bl.lookup(4, default="x") == "x"
    with pytest.raises(ValueError):
        bl.lookup(1, column1=4)
    with pytest.raises(ValueError):
        bl.lookup(1, column1=3)
    assert bl.lookup_row(1) == 1
    assert bl.lookup_row(3) == 3


def test_vookup():
    bl = xwu.block.from_value([[1, "One", "Un"], [2, "Two", "Deux"], [3, "Three", "Trois"]])
    assert bl.vlookup(1) == "One"
    assert bl.vlookup(3, column2=3) == "Trois"
    with pytest.raises(ValueError):
        bl.vlookup(4)
    assert bl.vlookup(4, default="x") == "x"
    with pytest.raises(ValueError):
        bl.vlookup(1, column1=4)
    with pytest.raises(ValueError):
        bl.vlookup(1, column1=3)


def test_hlookup():
    bl = xwu.block.from_value([[1, 2, 3], "One Two Three".split(), "Un Deux Trois".split()])

    assert bl.hlookup(1) == "One"
    assert bl.hlookup(3, row2=3) == "Trois"
    with pytest.raises(ValueError):
        bl.hlookup(4)
    assert bl.hlookup(4, default="x") == "x"
    with pytest.raises(ValueError):
        bl.hlookup(1, row1=4)
    with pytest.raises(ValueError):
        bl.hlookup(1, row1=3)
    assert bl.lookup_column(1) == 1
    assert bl.lookup_column(3) == 3


def test_capture(capsys):
    print("abc")
    print("def")
    capture = xwu.Capture()
    out, err = capsys.readouterr()
    assert out == "abc\ndef\n"
    assert capture.str_keep == ""
    assert capture.value_keep == []

    with capture:
        print("abc")
        print("def")
    out, err = capsys.readouterr()
    assert out == ""
    assert capture.str_keep == "abc\ndef\n"
    assert capture.value_keep == [["abc"], ["def"]]
    assert capture.str == "abc\ndef\n"
    assert capture.value == []

    with capture:
        print("abc")
        print("def")
    out, err = capsys.readouterr()
    capture.clear()
    assert capture.str_keep == ""

    with capture:
        print("abc")
        print("def")
    with capture:
        print("ghi")
        print("jkl")
    out, err = capsys.readouterr()
    assert out == ""
    assert capture.str_keep == "abc\ndef\nghi\njkl\n"
    assert capture.value_keep == [["abc"], ["def"], ["ghi"], ["jkl"]]
    assert capture.value == [["abc"], ["def"], ["ghi"], ["jkl"]]
    assert capture.value == []

    capture.enabled = True
    print("abc")
    print("def")
    capture.enabled = False
    print("xxx")
    print("yyy")
    capture.enabled = True
    print("ghi")
    print("jkl")
    assert capture.str_keep == "abc\ndef\nghi\njkl\n"

    # include_print is not testable with pytest


if __name__ == "__main__":
    pytest.main(["-vv", "-s", "-x", __file__])
