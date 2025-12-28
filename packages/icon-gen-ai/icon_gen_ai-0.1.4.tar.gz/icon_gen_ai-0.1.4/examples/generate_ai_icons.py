"""Generate AI model icons: Claude, OpenAI, and Gemini."""

from pathlib import Path
import sys
import shutil

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from icon_gen.generator import IconGenerator


def main():
    """Generate white SVG icons for major AI models."""
    
    # Initialize generator
    generator = IconGenerator(output_dir="output")
    
    # Check if we have a local Claude icon
    local_claude = Path("input/claude.svg")
    
    # Define the AI model icons we want
    ai_icons = {}
    
    # Try to download from URL
    ai_icons['claude'] = {
        'url': 'https://upload.wikimedia.org/wikipedia/commons/b/b0/Claude_AI_symbol.svg'
    }
    
    # Add other icons
    ai_icons.update({
        'openai': 'simple-icons:openai',
        'gemini': 'simple-icons:googlegemini',
        'mistral': 'simple-icons:mistralai',
    })
    
    print("=" * 60)
    print("AI Model Icon Generator")
    print("=" * 60)
    print(f"Output directory: {generator.output_dir.absolute()}")
    print(f"Color: white")
    print(f"Size: 256px")
    print(f"Format: SVG")
    print()
    
    # Generate all icons with white color and 256px size
    generated = generator.generate_batch(ai_icons, color="white", size=256)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Successfully generated {len(generated) + (1 if local_claude.exists() else 0)}/{len(ai_icons) + (1 if local_claude.exists() else 0)} icons:")
    if local_claude.exists():
        print(f"  • claude.svg")
    for path in generated:
        print(f"  • {path.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()