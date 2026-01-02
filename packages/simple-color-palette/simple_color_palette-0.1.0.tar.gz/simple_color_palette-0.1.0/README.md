# simple-color-palette-py
v0.1.0

### A Python package for the [Simple Color Palette](https://simplecolorpalette.com) format — a minimal JSON-based file format for defining color palettes (MIT license)

## Latest Changes
- Initial release

## Install

```sh
pip install simple-color-palette
```

## API Reference

### Dataclasses
`simplecolorpalette` provides Python `dataclass`es for defining a color `Palette`, its constituent `Color`s, and the RGB `Components` of those colors. Each dataclass field can be given either positionally or by keyword.

#### `Components`
Stores linear sRGB color channel data. Values outside the range of 0.0 to 1.0 are allowed for the `red`, `green`, and `blue` components. Opacity values outside the 0.0 to 1.0 range will be clamped.

| Field     | Type    | Required | Description                                                  |
| --------- | ------- | -------- | ------------------------------------------------------------ |
| `red`     | `float` | **Yes**  | Red channel (linear sRGB)                                    |
| `green`   | `float` | **Yes**  | Green channel (linear sRGB)                                  |
| `blue`    | `float` | **Yes**  | Blue channel (linear sRGB)                                   |
| `opacity` | `float` | No       | Optional opacity/alpha channel. Defaults to `1.0` if omitted |

```python
cyan_components = Components(red=0.0, green=1.0, blue=1.0)
magenta_components = Components(red=1.0, green=0.0, blue=1.0)
yellow_components = Components(red=1.0, green=1.0, blue=0.0)
```

#### `Color`
Represents a single color swatch in a palette; defined by its red, green, blue, and (optionally) alpha components.

| Field        | Type         | Required | Description                           |
| ------------ | ------------ | -------- | ------------------------------------- |
| `name`       | `str`        | No       | Optional color name (e.g., `'Cyan'`). |
| `components` | `Components` | **Yes**  | Linear sRGB RGB or RGBA components    |

```python
cyan = Color(name='Cyan', components=cyan_components)
magenta = Color(name='Magenta', components=magenta_components)
yellow = Color(name='Yellow', components=yellow_components)
```

#### `Palette`

Represents a named collection of colors.

| Field    | Type          | Required | Description                                               |
|----------|---------------|----------|-----------------------------------------------------------|
| `name`   | `str`         | No       | Palette display name (e.g., `'CMY'`)                      |
| `colors` | `list[Color]` | **Yes**  | List of color entries (must contain at least one `Color`) |

```python
palette = Palette(name='CMY', colors=[cyan, magenta, yellow])
```

## Functions

#### `load(path: pathlib.Path | str) -> Palette`
Loads a `*.color-palette` JSON file into a `Palette` object

```python
palette = load('/path/to/palette.color-palette')
print(palette.name)
print(palette.colors[0].components)
```

#### `save(palette: Palette, path: pathlib.Path | str) -> None`
Serializes a `Palette` object and writes it to disk in spec-compliant `*.color-palette` JSON format

> [!NOTE]
> If the `Palette` object passed to `save` does not have a defined `name`, the file name will be used (without the `*.color-palette` extension)

```python
save(palette, 'my_palette.color-palette')
```

Output format
```json
{
  "name": "CMY",
  "colors": [
    { "name": "Cyan", "components": [0.0, 1.0, 1.0] },
    { "name": "Magenta", "components": [1.0, 0.0, 1.0] },
    { "name": "Yellow", "components": [1.0, 1.0, 0.0] }
  ]
}
```

#### `from_hex(hex_string: str) -> Components`
Creates a `Components` object from a hex color code string, e.g. "#DEADBEEF"

| Parameter    | Type  | Description                                                          |
| ------------ | ----- | -------------------------------------------------------------------- |
| `hex_string` | `str` | 3, 4, 6, or 8-digit RGB hex color code (the leading '#' is optional) |

```python
hex_color = '#ff3344'
components = from_hex(hex_color)
print(components)
# >>> Components(red=1.0, green=0.2, blue=0.26667, opacity=1.0)

hex_color_with_opacity = '#4466ffcc'
components_with_opacity = from_hex(hex_color_with_opacity)
print(components_with_opacity)
# >>> Components(red=0.26667, green=0.4, blue=1.0, opacity=0.8)
```

## Usage Example

```python
import simplecolorpalette as scp

# define some colors - scp.Color dataclass objects
red_color = scp.Color(
	name='Red',
    components=scp.Components(red=1.0, green=0.0, blue=0.0,)
)

yellow_color = scp.Color(
    name='Yellow',
    components=scp.Components(red=1.0, green=1.0, blue=0.0)
)

green_color = scp.Color(
    name='Green',
    components=scp.Components(red=0.0, green=1.0, blue=0.0,)
)

# define the color palette - scp.Palette object
palette = scp.Palette(
	name='Traffic Lights',
	colors=[red_color, yellow_color, green_color],
)

# introspecting color components
print(red_color.components)
# >>> Components(red=1.0, green=0.0, blue=0.0, opacity=1.0)

# modifying color components
red_color.components.red = 0.9

# saving to JSON (as a *.color-palette file)
palette_file_path = 'path/to/palette.color-palette'
scp.save(palette, palette_file_path)

# loading palette data from a *.color-palette file
palette_data = scp.load('path/to/palette.color-palette')
print(palette_data)
# >>> Palette(colors=[Color(components=Components(red=0.9, green=0.0, blue=0.0, opacity=1.0), name='Red'), Color(components=Components(red=1.0, green=1.0, blue=0.0, opacity=1.0), name='Yellow'), Color(components=Components(red=0.0, green=1.0, blue=0.0, opacity=1.0), name='Green')], name='Traffic Lights')
```

> [!NOTE]
> - The `simplecolorpalette.save` and `simplecolorpalette.load` functions will accept file paths with either a `*.color-palette` or `*.json` file extension, other file extensions will raise a `ValueError`.
> - Output files saved with `save()` will use the `*.color-palette` extension.

If you want to access `Palette` data in `dict` format, use `dataclasses.asdict`:
```python
from dataclasses import asdict

...  # other stuff omitted for brevity

print(asdict(palette_data))
# >>> {'colors': [{'components': {'red': 0.9, 'green': 0.0, 'blue': 0.0, 'opacity': 1.0}, 'name': 'Red'}, {'components': {'red': 1.0, 'green': 1.0, 'blue': 0.0, 'opacity': 1.0}, 'name': 'Yellow'}, {'components': {'red': 0.0, 'green': 1.0, 'blue': 0.0, 'opacity': 1.0}, 'name': 'Green'}], 'name': 'Traffic Lights'}
```
