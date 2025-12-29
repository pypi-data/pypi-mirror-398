import click
import os
import sys
import logging
import json
from converter.engine import ConversionEngine
from converter.template_engine import TemplateEngine
from core.registry import register_all_converters

logger = logging.getLogger(__name__)

@click.command('convert')
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True), required=False)
@click.option('--output', '-o', 'output_path', type=click.Path(), help='Output path for single file conversion')
@click.option('--choose', '-c', is_flag=True, help='Interactive file picker mode')
@click.option('--format', '-f', help='Target format (if different from extension)')
@click.option('--template', '-t', help='Path to template file for custom output')
@click.option('--ocr/--no-ocr', default=False, help='Enable OCR for scanned documents')
@click.option('--lang', default='auto', help='Language for OCR (default: auto)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--delete', is_flag=True, help='Delete source file after successful conversion')
@click.option('--confirm-delete', is_flag=True, help='Ask for confirmation before deleting source file')
@click.option('--dry-run', is_flag=True, help='Simulate conversion without writing files')
def convert_command(input_paths, output_path, choose, format, template, ocr, lang, verbose, delete, confirm_delete, dry_run):
    """Convert one or more documents. Supports drag & drop of multiple files."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Normalize all input paths to absolute paths and handle spaces
    input_paths = tuple(os.path.abspath(p) for p in input_paths) if input_paths else ()
    
    # Determine mode: interactive, single file, or multiple files (drag & drop)
    if not input_paths and not output_path:
        choose = True
    
    # Handle multiple files (drag & drop scenario)
    if len(input_paths) > 1:
        mode_text = "[DRY-RUN] " if dry_run else ""
        click.echo(click.style(f"\n🎯 {mode_text}Processing {len(input_paths)} files (drag & drop mode)...\n", fg='cyan', bold=True))
        
        # Determine output format
        target_format = format if format else click.prompt("Target format (pdf/docx/txt/html/md)", default="pdf")
        if not target_format.startswith('.'):
            target_format = f".{target_format}"
        
        # Initialize engine once (using imports at top)
        engine = ConversionEngine()
        register_all_converters(engine)
        
        success_count = 0
        failed_files = []
        
        for idx, input_file in enumerate(input_paths, 1):
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(os.path.dirname(input_file), f"{base_name}{target_format}")
            
            click.echo(f"  [{idx}/{len(input_paths)}] {os.path.basename(input_file)} → {os.path.basename(output_file)}")
            
            try:
                success = engine.convert(input_file, output_file, dry_run=dry_run, ocr_enabled=ocr, ocr_lang=lang)
                if success:
                    success_count += 1
                    # Handle deletion for batch
                    if delete:
                        try:
                            os.remove(input_file)
                            click.echo(click.style(f"      ✓ Deleted source", fg='yellow'))
                        except Exception as e:
                            click.echo(click.style(f"      ⚠ Could not delete: {e}", fg='yellow'))
                else:
                    failed_files.append(os.path.basename(input_file))
            except Exception as e:
                failed_files.append(os.path.basename(input_file))
                click.echo(click.style(f"      ✗ Error: {e}", fg='red'))
        
        click.echo()
        click.echo(click.style(f"✅ Completed: {success_count}/{len(input_paths)} successful", fg='green', bold=True))
        if failed_files:
            click.echo(click.style(f"❌ Failed: {', '.join(failed_files)}", fg='red'))
        
        sys.exit(0 if success_count > 0 else 1)
    
    # Single file or interactive mode
    input_path = input_paths[0] if input_paths else None
    
    # Interactive file picker mode
    if choose or not input_path:
        # Clear screen for better UX
        os.system('cls' if os.name == 'nt' else 'clear')
        
        click.echo("=" * 70)
        click.echo(" " * 20 + "DOCUMENT CONVERTER v1.2.0")
        click.echo("=" * 70)
        click.echo()
        click.echo("Conversiones soportadas:")
        click.echo("  ✓ Formatos: PDF, DOCX, TXT, HTML, MD, ODT")
        click.echo("  ✓ PDF con soporte OCR para documentos escaneados")
        click.echo()
        click.echo("-" * 70)
        click.echo()

        from cli.ui.file_picker import pick_file_interactive, pick_output_file
        
        # Pick input file if not provided
        if not input_path:
            click.echo(click.style("\n🔍 Select input file:", fg='cyan', bold=True))
            input_path = pick_file_interactive(directory=".", pattern="*")
            if not input_path:
                click.echo(click.style("✗ No file selected. Exiting.", fg='yellow'))
                sys.exit(0)
            click.echo(click.style(f"✓ Selected: {input_path}", fg='green'))
        
        # Pick output file if not provided
        if not output_path:
            click.echo()  # Blank line for spacing
            # Suggest output name based on input
            input_name = os.path.splitext(os.path.basename(input_path))[0]
            default_ext = format if format else ".txt"
            if not default_ext.startswith('.'):
                default_ext = f".{default_ext}"
            
            click.echo(click.style("📝 Enter output filename (with extension):", fg='cyan', bold=True))
            output_path = pick_output_file(
                default_name=input_name + "_converted",
                default_ext=default_ext,
                prompt_text="Output file"
            )
            if not output_path:
                click.echo(click.style("✗ No output file specified. Exiting.", fg='yellow'))
                sys.exit(0)
    
    # Validate that we have required paths
    if not input_path or not output_path:
        click.echo(click.style("Error: Both input and output paths are required.", fg='red'))
        click.echo("Run without arguments for interactive mode, or provide both paths.")
        sys.exit(1)
        
    click.echo(f"Converting '{input_path}' to '{output_path}'...")
    
    try:
        # Template mode
        if template:
            if not os.path.exists(template):
                click.echo(click.style(f"Error: Template file not found: {template}", fg='red'))
                sys.exit(1)
                
            click.echo(f"Using template: {template}")
            
            # For template mode, input is treated as data context
            # Currently supporting JSON inputs
            # TODO: Support YAML or other data sources?
            # Also TODO: Support document-to-document with template styling if Engine supports it? 
            # For now, implementing Data(JSON) + Template -> Output
            
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    # Basic detection: try JSON
                    context = json.load(f)
            except json.JSONDecodeError:
                click.echo(click.style("Error: Input file must be valid JSON when using templates.", fg='red'))
                sys.exit(1)
            except Exception as e:
                click.echo(click.style(f"Error reading input: {e}", fg='red'))
                sys.exit(1)
                
            engine = TemplateEngine()
            
            with open(template, 'r', encoding='utf-8') as f:
                tmpl_content = f.read()
                
            result = engine.render(tmpl_content, context)
            
            # Ensure output dir
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
                
            click.echo(click.style("Template rendered successfully!", fg='green'))
            return

        # Standard conversion mode
        # Initialize engine (import already at top of file)
        engine = ConversionEngine()
        register_all_converters(engine)
        
        success = engine.convert(
            input_path, 
            output_path, 
            dry_run=dry_run,
            ocr_enabled=ocr, 
            ocr_lang=lang
        )
        
        if success:
            click.echo(click.style("Conversion successful!", fg='green'))
            
            # Handle source file deletion
            should_delete = delete or confirm_delete
            if should_delete:
                # Confirm deletion if requested
                if confirm_delete:
                    click.echo()
                    response = input(f"Delete source file '{input_path}'? (yes/no): ").strip().lower()
                    should_delete = response in ('yes', 'y')
                
                if should_delete:
                    try:
                        os.remove(input_path)
                        click.echo(click.style(f"✓ Deleted source file: {input_path}", fg='yellow'))
                        logger.info(f"Deleted source file after conversion: {input_path}")
                    except Exception as e:
                        click.echo(click.style(f"⚠ Warning: Could not delete source file: {e}", fg='yellow'))
                        logger.warning(f"Failed to delete source file {input_path}: {e}")
                else:
                    click.echo(click.style("Source file kept.", fg='cyan'))
        else:
            click.echo(click.style("Conversion failed.", fg='red'))
            sys.exit(1)
            
    except ImportError as e:
        click.echo(click.style(f"Error: Missing dependency. {e}", fg='red'))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))
        if verbose:
            logger.exception("Conversion error")
        sys.exit(1)
