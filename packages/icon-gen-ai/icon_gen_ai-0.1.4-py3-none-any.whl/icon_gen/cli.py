"""Command-line interface for icon-gen."""
import click
from pathlib import Path
from .generator import IconGenerator


@click.command()
@click.argument('icon_name')
@click.option('--color', default='white', help='Icon color (e.g., white, #FF0000)')
@click.option('--size', default=256, help='Icon size in pixels')
@click.option('--format', 'output_format', default='svg', 
              type=click.Choice(['png', 'svg', 'webp']))
@click.option('--output', '-o', help='Output file path')
@click.option('--bg-color', help='Background color (e.g., #8B76E9 or none for transparent)')
@click.option('--border-radius', default=0, help='Border radius (0=square, size/2=circle)')
def main(icon_name, color, size, output_format, output, bg_color, border_radius):
    """Generate icons from Iconify.
    
    Examples:
    
        icon-gen simple-icons:openai
        
        icon-gen simple-icons:openai --color white --size 512
        
        icon-gen mdi:github --bg-color "#8B76E9" --border-radius 20
        
        icon-gen simple-icons:openai -o my-icon.svg
    """
    try:
        # Initialize generator
        output_dir = "output" if not output else str(Path(output).parent)
        generator = IconGenerator(output_dir=output_dir)
        
        # Parse background color
        parsed_bg_color = None
        if bg_color and bg_color.lower() != 'none':
            parsed_bg_color = bg_color
        
        # Determine output name
        if output:
            output_name = Path(output).stem
        else:
            output_name = icon_name.replace(':', '_').replace('/', '_')
        
        click.echo(f"Generating {icon_name}...")
        click.echo(f"  Color: {color}")
        click.echo(f"  Size: {size}px")
        click.echo(f"  Background: {bg_color or 'transparent'}")
        click.echo(f"  Border radius: {border_radius}px")
        
        # Generate icon
        result = generator.generate_icon(
            icon_name=icon_name,
            output_name=output_name,
            color=color,
            size=size,
            format=output_format,
            bg_color=parsed_bg_color,
            border_radius=border_radius
        )
        
        if result:
            click.echo(f"✓ Success! Saved to: {result}")
        else:
            click.echo("✗ Failed to generate icon", err=True)
            raise click.Abort()
            
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    main()