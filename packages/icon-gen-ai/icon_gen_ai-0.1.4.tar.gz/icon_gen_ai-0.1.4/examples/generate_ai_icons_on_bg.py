"""Generate AI model icons with custom backgrounds and gradients."""

from pathlib import Path
import sys

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from icon_gen.generator import IconGenerator


def main():
    """Generate AI icons with custom backgrounds and colors."""
    
    # Initialize generator
    generator = IconGenerator(output_dir="output")
    
    # Define icons with custom styling
    ai_icons = {
        'claude_white_purple_bg': {
            'url': 'https://upload.wikimedia.org/wikipedia/commons/b/b0/Claude_AI_symbol.svg',
            'color': 'white', 
            'bg_color': '#8B76E9',
            'border_radius': 0,  # Square
            'size': 256
        },

        'gemini_white_pink_bg': {
            'icon': 'simple-icons:googlegemini',
            'color': 'white',
            'bg_color': '#EA2081',
            'border_radius': 128,  # Circle (half of size)
            'size': 256
        },
        
        'mistral_white_gradient_bg': {
            'icon': 'simple-icons:mistralai',
            'color': 'white',
            'bg_color': ('#8B76E9', '#EA2081'),  # Gradient
            'border_radius': 40,  # Rounded corners
            'size': 256
        },
        
        'openai_gradient_transparent_bg': {
            'icon': 'simple-icons:openai',
            'color': ('#8B76E9', '#EA2081'),  # Gradient icon
            'bg_color': None,  # Transparent background
            'size': 256
        }
    }
    
    print("=" * 70)
    print("AI Model Icon Generator - With Custom Backgrounds & Gradients")
    print("=" * 70)
    print(f"Output directory: {generator.output_dir.absolute()}")
    print()
    print("Generating icons:")
    print("  • OpenAI   - White on square purple (#8B76E9)")
    print("  • Gemini   - White on circular pink (#EA2081)")
    print("  • Mistral  - White on gradient rounded square")
    print("  • Claude   - Gradient icon on transparent background")
    print()
    
    # Generate all icons
    generated = generator.generate_batch(ai_icons)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✓ Successfully generated {len(generated)}/{len(ai_icons)} icons")
    print("=" * 70)


if __name__ == "__main__":
    main()