"""Tests for icon generator."""

from pathlib import Path
import pytest
from icon_gen.generator import IconGenerator


def test_generator_initialization():
    """Test that generator initializes correctly."""
    generator = IconGenerator(output_dir="test_output")
    assert generator.output_dir == Path("test_output")
    assert generator.output_dir.exists()


def test_generate_icon(tmp_path):
    """Test generating a single icon."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    result = generator.generate_icon(
        'mdi:github',
        output_name='test_icon',
        color='white',
        size=64
    )
    
    assert result is not None
    assert result.exists()
    assert result.name == 'test_icon.svg'


def test_generate_batch(tmp_path):
    """Test generating multiple icons."""
    generator = IconGenerator(output_dir=str(tmp_path))
    
    icons = {
        'test1': 'mdi:github',
        'test2': 'mdi:twitter',
    }
    
    results = generator.generate_batch(icons, color='white', size=64)
    
    assert len(results) == 2
    assert all(r.exists() for r in results)