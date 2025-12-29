import click
import os
import sys
import logging
from converter.base.format_detector import FormatDetector
from converter.engine import ConversionEngine
from core.registry import register_all_converters

@click.command('info')
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed metadata')
def info_command(input_path, verbose):
    """Show document metadata and format information."""
    try:
        # Detect format
        detector = FormatDetector()
        detected_format = detector.detect(input_path)
        
        click.echo(f"File: {click.format_filename(input_path)}")
        click.echo(f"Detected Format: {click.style(detected_format.upper(), fg='cyan')}")
        
        if detected_format == 'unknown':
            click.echo(click.style("Unknown format. Cannot extract metadata.", fg='yellow'))
            return

        # Get Metadata
        # We need the engine to find the right converter
        engine = ConversionEngine()
        register_all_converters(engine)
        
        try:
            converter = engine.get_converter(detected_format)
            metadata = converter.extract_metadata(input_path)
            
            if metadata:
                click.echo("\nMetadata:")
                for key, value in metadata.items():
                    # Format key nicely
                    formatted_key = key.replace('_', ' ').title()
                    click.echo(f"  {click.style(formatted_key, bold=True)}: {value}")
            else:
                click.echo("\nNo metadata found.")
        except ValueError:
            click.echo(click.style(f"\nNo converter available for format '{detected_format}'", fg='yellow'))
            supported = sorted(engine.get_supported_formats())
            click.echo("Supported formats: " + ", ".join(supported))

    except Exception as e:
        click.echo(click.style(f"Error getting info: {e}", fg='red'))
        if verbose:
            logging.exception("Full traceback:")
        sys.exit(1)
