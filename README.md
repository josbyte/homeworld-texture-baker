# homeworld-texture-baker

Lightweight desktop tool for combining Homeworld-style diffuse, team, and glow textures into a single faster workflow.

It is aimed at modders and artists who want a practical alternative to heavier baking pipelines when working with Homeworld-inspired texture setups.

## What it does

- Supports `Homeworld Remastered` and `Homeworld 3` style workflows
- Loads and previews `BC`, `TEAM`, `MASK`, and `GLOW` textures
- Applies primary and secondary team colors
- Lets you place, rotate, and scale badges interactively
- Generates processed glow output for Remastered mode
- Loads faction presets from `faction_color_presets_named.json`

## Requirements

- Python `3.8+`
- `Pillow`
- `tkinter`

On Linux, `tkinter` may need to be installed from your system package manager, for example `python3-tk`.

## Quick start

```bash
git clone https://github.com/josbyte/homeworld-texture-baker.git
cd homeworld-texture-baker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python HW_texture_baker.py
```

## Basic workflow

1. Load the base texture plus the textures used by your selected mode.
2. Choose primary and secondary team colors manually or sample them from the TEAM preview.
3. Apply the team color pass.
4. Optionally place a badge with scale and rotation controls.
5. Export the final texture, plus glow output when using Remastered mode.

## Modes

- `Homeworld 3`: uses the `MASK` texture during color application
- `Homeworld Remastered`: uses the `GLOW` texture and exports processed glow output

## Supported formats

Input: `PNG`, `JPEG`, `BMP`, `TGA`, `DDS`, `TIFF`, `GIF`, `WebP`

Recommended output: `PNG`

## Notes on asset rights

This tool does not include original Homeworld assets and does not grant rights over third-party textures.

Users are responsible for making sure they have permission to use, modify, or redistribute any source textures they process with this tool.

## License

Licensed under `GPL-3.0`. See [LICENSE](LICENSE).

## Support

If you find a bug or want to suggest an improvement, open an issue on GitHub.
