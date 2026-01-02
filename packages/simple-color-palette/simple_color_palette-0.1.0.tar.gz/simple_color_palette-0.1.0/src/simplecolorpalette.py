import json
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Optional


@dataclass
class Components:
    """Simple Color Palette color components dataclass

    `red`, `green`, `blue`, and `opacity` are float values

    `red`, `green`, and `blue` can have values outside the 0.0-1.0 range and
    will be rounded to 5 decimal places

    `opacity` defaults to 1.0 if not specified, and will be clamped between 0.0
    and 1.0
    """

    red: float
    green: float
    blue: float
    opacity: float = 1.0

    def __post_init__(self) -> None:
        # round color components to 5 decimal places, up to the nearest even
        self.red = self._roundup(self.red)
        self.green = self._roundup(self.green)
        self.blue = self._roundup(self.blue)
        # clamp opacity between 0.0 and 1.0
        self.opacity = max(0.0, min(self.opacity, 1.0))

    @staticmethod
    def _roundup(value: float) -> float:
        """Round a float to 5 decimal places, rounding half up"""
        return float(
            Decimal(str(value)).quantize(
                Decimal('0.00001'), rounding=ROUND_HALF_UP
            )
        )


@dataclass
class Color:
    """Simple Color Palette color object dataclass

    - `components` is a `Components` dataclass instance
    - `name` is an optional name for the color
    """

    components: Components
    name: Optional[str] = None


@dataclass
class Palette:
    """
    Simple Color Palette dataclass

    - `colors` is a list of `Color` dataclass instances
    - `name` is an optional name for the palette
    """

    colors: list[Color]
    name: Optional[str] = None


def load(file_path: Path | str) -> Palette:
    """
    Load a Simple Color Palette from a *.color-palette or *.json file specified
    by `file_path`, and return a `Palette` dataclass instance

    `file_path` must use either a *.color-palette or *.json extension,
    otherwise a `ValueError` will be raised
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f'File not found: {file_path}')

    if file_path.suffix.lower() not in {'.color-palette', '.json'}:
        raise ValueError(f'Unsupported file format: {file_path.suffix}')

    with open(file_path, 'r') as color_palette_file:
        data = json.load(color_palette_file)

    colors = [
        Color(
            components=Components(*color_data['components']),
            name=color_data.get('name'),
        )
        for color_data in data['colors']
    ]
    # get palette name from JSON data or use file stem as default
    palette_name = data.get('name', file_path.stem)

    return Palette(colors=colors, name=palette_name)


def save(color_palette: Palette, file_path: Path | str) -> None:
    """
    Save the given `color_palette` to a *.color-palette file at `file_path`

    `file_path` must use either a *.color-palette or *.json extension,
    otherwise a `ValueError` will be raised

    The file will always be saved as a *.color-palette regardless of the
    provided extension, so long as it is one of the supported types

    If `color_palette.name` is not set, the file name (without extension) will
    be used as the palette name instead
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    if file_path.suffix.lower() not in {'.color-palette', '.json'}:
        raise ValueError(
            f'Unsupported file format: {file_path.suffix}. '
            'Use .color-palette or .json'
        )

    # NOTE: dataclasses.asdict() doesn't work here - we have to build the dict
    # manually, otherwise undefined color names would write out as `null`,
    # which is against the spec (and also breaks Components._roundup parsing)
    data = {
        'name': color_palette.name or file_path.stem,
        'colors': [
            {
                'components': [
                    color.components.red,
                    color.components.green,
                    color.components.blue,
                    # only include the opacity value if it's not 1.0
                    *(
                        [color.components.opacity]
                        if color.components.opacity != 1.0
                        else []
                    ),
                ],
                # include the color name if it exists
                **({'name': color.name} if color.name else {}),
            }
            for color in color_palette.colors
        ],
    }

    with open(file_path, 'w') as color_palette_file:
        json.dump(data, color_palette_file, indent=4)

    # ensure the file has a .color-palette extension
    file_path.rename(file_path.with_suffix('.color-palette'))


def from_hex(hex_string: str) -> Components:
    """Convert a hex color string to a `Components` dataclass instance"""
    hex_string = hex_string.lstrip('#')
    if len(hex_string) in {3, 4}:
        # expand shorthand colors (e.g., #123 -> #112233, #1234 -> #11223344)
        hex_string = ''.join(c * 2 for c in hex_string)

    if len(hex_string) not in {6, 8}:
        raise ValueError(
            'Hex color codes must contain 3, 4, 6, or 8 hexadecimal digits'
        )

    red = int(hex_string[0:2], 16) / 255.0
    green = int(hex_string[2:4], 16) / 255.0
    blue = int(hex_string[4:6], 16) / 255.0
    opacity = 1.0

    if len(hex_string) == 8:
        opacity = int(hex_string[6:8], 16) / 255.0

    return Components(red=red, green=green, blue=blue, opacity=opacity)


if __name__ == '__main__':  # DEMO
    # this isn't an exhaustive API demo, just a quick test of palette
    # definition and save/load
    cyan = Color(Components(red=0.0, green=1.0, blue=1.0), name='Cyan')
    magenta = Color(Components(red=1.0, green=0.0, blue=1.0), name='Magenta')
    yellow = Color(Components(red=1.0, green=1.0, blue=0.0), name='Yellow')

    palette = Palette(name='CMY', colors=[cyan, magenta, yellow])

    # save to JSON (as a *.color-palette file)
    palette_file_path = 'test/demo.color-palette'
    save(palette, palette_file_path)

    # load palette data from a *.color-palette file
    palette_data = load('test/demo.color-palette')
    print(palette_data)
