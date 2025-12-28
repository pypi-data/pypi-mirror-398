"""Generate a white judge/law scale icon example."""

from pathlib import Path
import sys

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from icon_gen.generator import IconGenerator


def main():
    """Generate white SVG icon of scales of justice (judge/law symbol)."""
    
    # Initialize generator
    generator = IconGenerator(output_dir="output")
    
    # Available scale/judge icons from Iconify:
    # - 'fa6-solid:scale-balanced' - Font Awesome balanced scales (classic look)
    # - 'heroicons:scale' - HeroIcons scales (modern minimal)
    # - 'mdi:scale-balance' - Material Design Icons
    # - 'tabler:scale' - Tabler scales (clean outline)
    
    judge_icons = {
        'judge': 'mdi:scale-balance',  # Classic scales of justice
    }
    
    print("=" * 60)
    print("Judge/Law Icon Generator")
    print("=" * 60)
    print(f"Output directory: {generator.output_dir.absolute()}")
    print(f"Icon: Scales of Justice (Balance Scale)")
    print(f"Color: white")
    print(f"Size: 256px")
    print(f"Format: SVG")
    print()
    
    # Generate icon with white color and 256px size
    generated = generator.generate_batch(judge_icons, color="white", size=256)
    
    # Summary
    print("\n" + "=" * 60)
    if generated:
        print(f"✓ Successfully generated judge icon:")
        for path in generated:
            print(f"  • {path.name}")
    else:
        print("✗ Failed to generate icon")
    print("=" * 60)
    
    # Also show alternative options
    print("\nAlternative judge/law icons you can try:")
    print("  • 'heroicons:scale' - Modern minimal scales")
    print("  • 'mdi:scale-balance' - Material Design scales")
    print("  • 'tabler:scale' - Clean outline scales")
    print("  • 'fa:balance-scale' - Font Awesome v4 scales")
    print("\nTo use a different icon, edit the script and change:")
    print("  'judge': 'fa6-solid:scale-balanced'")
    print("to your preferred icon name.")
    print("=" * 60)


if __name__ == "__main__":
    main()