import json

import pytest

from src.simplecolorpalette import Color, ColorComponents, ColorPalette


def assert_color_components(color, expected, decimals=2) -> None:
    assert round(color.red, decimals) == expected['red']
    assert round(color.green, decimals) == expected['green']
    assert round(color.blue, decimals) == expected['blue']
    if 'opacity' in expected and expected['opacity'] is not None:
        assert round(color.opacity, decimals) == expected['opacity']


def test_color_creation_and_component_access() -> None:
    color = Color(
        ColorComponents(
            red=0.5,
            green=0.7,
            blue=0.3,
            opacity=0.8,
        ),
        name='Test',
    )

    assert color.name == 'Test'
    assert color.components.opacity == 0.8
    assert_color_components(color, {'red': 0.5, 'green': 0.7, 'blue': 0.3})


def test_color_creation_with_linear_values() -> None:
    color = Color(
        ColorComponents(
            red=0.5,
            green=0.7,
            blue=0.3,
        ),
        is_linear=True,
    )
    linear = color.linear_components
    assert_color_components(linear, {'red': 0.5, 'green': 0.7, 'blue': 0.3})


def test_color_component_validation() -> None:
    with pytest.raises(TypeError, match='must be a number'):
        Color(red='invalid', green=0, blue=0)


def test_color_opacity_handling() -> None:
    color = Color(red=0, green=0, blue=0)

    color.opacity = 1.5
    assert color.opacity == 1

    color.opacity = -0.5
    assert color.opacity == 0

    with pytest.raises(TypeError, match='must be a number'):
        color.opacity = 'invalid'


def test_palette_creation_and_validation() -> None:
    red = Color(red=1, green=0, blue=0)
    green = Color(red=0, green=1, blue=0)
    palette = ColorPalette(colors=[red, green], name='Test')

    assert len(palette.colors) == 2
    assert palette.name == 'Test'

    with pytest.raises(TypeError, match='instance of Color'):
        ColorPalette(colors=[{}])


def test_serialization_roundtrip() -> None:
    original = ColorPalette(
        colors=[
            Color(red=1, green=0, blue=0, name='Red'),
            Color(red=0, green=1, blue=0, opacity=0.5, name='Green'),
        ],
        name='Test',
    )

    serialized = original.serialize()
    deserialized = ColorPalette.deserialize(serialized)

    assert deserialized.name == original.name
    assert len(deserialized.colors) == len(original.colors)

    for i in range(len(original.colors)):
        o = original.colors[i]
        d = deserialized.colors[i]
        assert d.name == o.name
        assert d.opacity == o.opacity

        assert_color_components(
            d.linear_components,
            {
                'red': o.linear_components.red,
                'green': o.linear_components.green,
                'blue': o.linear_components.blue,
                'opacity': o.linear_components.opacity if hasattr(o.linear_components, 'opacity') else None
            },
            decimals=5,
        )


def test_deserialization_validation() -> None:
    with pytest.raises(ValueError, match='not valid JSON'):
        ColorPalette.deserialize('/')

    with pytest.raises(ValueError, match='Colors must be an array'):
        ColorPalette.deserialize('{}')

    with pytest.raises(ValueError, match='Components must be an array'):
        ColorPalette.deserialize(json.dumps({
            'colors': [{'components': 'invalid'}]
        }))

    with pytest.raises(ValueError, match='3 or 4 values'):
        ColorPalette.deserialize(json.dumps({
            'colors': [{'components': [1, 2]}]
        }))

    with pytest.raises(ValueError, match='must be numbers'):
        ColorPalette.deserialize(json.dumps({
            'colors': [{'components': [-1, 0, 0]}]
        }))


def test_color_component_modification() -> None:
    color = Color(red=0.5, green=0.5, blue=0.5)
    color.red = 1
    color.green = 0
    color.blue = 0
    assert_color_components(color, {'red': 1, 'green': 0, 'blue': 0})

    with pytest.raises(TypeError, match='number'):
        color.green = 'invalid'


def test_precision_rounding() -> None:
    color = Color(
        red=0.123456,
        green=0.12345,
        blue=0.123444,
        opacity=0.123449,
        is_linear=True,
    )
    linear = color.linear_components

    assert linear.red == 0.12346
    assert linear.green == 0.12345
    assert linear.blue == 0.12344
    assert linear.opacity == 0.12345


def test_precision_roundtrip() -> None:
    color = Color(
        red=0.123456,
        green=0.12345,
        blue=0.123444,
        opacity=0.123449,
        is_linear=True,
    )

    parsed = json.loads(json.dumps(color, default=lambda o: o.__dict__))
    assert parsed['components'] == [0.12346, 0.12345, 0.12344, 0.12345]


hex_string_cases = [
    ('#FF0000', {'red': 1, 'green': 0, 'blue': 0, 'opacity': None}),
    ('F00', {'red': 1, 'green': 0, 'blue': 0, 'opacity': None}),
    ('#FF000080', {'red': 1, 'green': 0, 'blue': 0, 'opacity': 0.5}),
    ('F008', {'red': 1, 'green': 0, 'blue': 0, 'opacity': 0.53}),
]


@pytest.mark.parametrize('hex_string, expected', hex_string_cases)
def test_hex_string_initialization(hex_string, expected):
    color = Color.from_hex_
