import pytest

try:
    import tkinter  # noqa: F401
except ModuleNotFoundError:
    pytest.skip("tkinter not available", allow_module_level=True)

from bbox_overlay.cli import normalize_color, parse_boxes


def test_parse_boxes_dict_and_list():
    raw = '[{"x":1,"y":2,"w":3,"h":4,"label":"cat"}, [5,6,7,8,"dog"], [9,10,11,12]]'
    boxes = parse_boxes(raw)
    assert boxes == [
        (1, 2, 3, 4, "cat"),
        (5, 6, 7, 8, "dog"),
        (9, 10, 11, 12, None),
    ]


def test_parse_boxes_numeric_cast():
    boxes = parse_boxes('[{"x":1.9,"y":2.2,"w":3.7,"h":4.1}]')
    assert boxes == [(1, 2, 3, 4, None)]


def test_parse_boxes_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_boxes("not-json")


def test_parse_boxes_requires_list():
    with pytest.raises(ValueError, match="must be a JSON array"):
        parse_boxes('{"x":1,"y":2,"w":3,"h":4}')


def test_parse_boxes_missing_key():
    with pytest.raises(ValueError, match="missing key"):
        parse_boxes('[{"x":1,"y":2,"h":4}]')


def test_parse_boxes_label_must_be_string():
    with pytest.raises(ValueError, match="label must be a string"):
        parse_boxes('[{"x":1,"y":2,"w":3,"h":4,"label":123}]')


def test_parse_boxes_non_negative_dimensions():
    with pytest.raises(ValueError, match="non-negative"):
        parse_boxes('[{"x":1,"y":2,"w":-3,"h":4}]')


def test_normalize_color_adds_hash():
    assert normalize_color("fff") == "#fff"
    assert normalize_color("00ff00") == "#00ff00"


def test_normalize_color_passthrough():
    assert normalize_color("#123") == "#123"
    assert normalize_color("red") == "red"
