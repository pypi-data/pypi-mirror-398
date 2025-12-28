# icon-gen

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/yauheniya-ai/icon-gen)
[![Coverage](https://img.shields.io/badge/coverage-48%25-yellow.svg)](https://github.com/yauheniya-ai/icon-gen)

Generate customizable icons from Iconify with easy export to PNG, SVG, WebP formats.

## Features

- Access 200,000+ icons from Iconify
- Customize colors and sizes
- Custom backgrounds
- Adjustable border radius
- Export to SVG format
- Simple and intuitive API
- CLI and Python API

## Installation

```bash
pip install icon-gen
```

## Quick Start
```python
from icon_gen import IconGenerator

# Initialize generator
generator = IconGenerator(output_dir="output")

# Generate multiple icons at once
ai_icons = {
    'openai': 'simple-icons:openai',
    'gemini': 'simple-icons:googlegemini',
    'mistral': 'simple-icons:mistralai',
    'claude': {
        'url': 'https://upload.wikimedia.org/wikipedia/commons/b/b0/Claude_AI_symbol.svg'
    }
}

generator.generate_batch(ai_icons, color='white', size=256)
```

## Example Output

<div align="center" style="padding: 40px; border-radius: 10px;">
  <img src="./output/claude_white_purple_bg.svg" width="70" alt="Claude">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="40" height="1" alt="">
  <img src="./output/gemini_white_pink_bg.svg" width="70" alt="Gemini">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="40" height="1" alt="">
  <img src="./output/mistral_white_gradient_bg.svg" width="70" alt="Mistral">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="40" height="1" alt="">
  <img src="./output/openai_gradient_transparent_bg.svg" width="70" alt="OpenAI">
</div>

## Finding Icons

Browse available icons at [Iconify](https://icon-sets.iconify.design/)

Icon naming format: `collection:icon-name`
- `simple-icons:openai` - Company logos
- `mdi:github` - Material Design Icons
- `fa6-solid:scale-balanced` - Font Awesome icons
- `heroicons:scale` - HeroIcons

## Examples

Check out the `examples/` directory for more use cases:
- `generate_ai_icons.py` - Generate AI model icons (Claude, OpenAI, Gemini)
- `generate_judge_icon.py` - Generate legal/law icons

## Development

```bash
# Clone the repository
git clone https://github.com/yauheniya-ai/icon-gen.git
cd icon-gen

# Install all dependencies (including dev tools)
uv sync

# Run tests
uv run pytest
```

## License

MIT License - see LICENSE file for details

## Author

Yauheniya Varabyova (yauheniya.ai@gmail.com)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
