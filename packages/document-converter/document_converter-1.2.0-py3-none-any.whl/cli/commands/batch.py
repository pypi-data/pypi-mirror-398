import click
import os
import sys
import logging
from tqdm import tqdm
from converter.batch_processor import BatchProcessor
from core.worker_pool import WorkerPool
from core.registry import register_all_converters

logger = logging.getLogger(__name__)

@click.command('batch')
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.argument('output_dir', type=click.Path(file_okay=False))
@click.option('--from-format', help='Filter input by format (e.g. pdf)')
@click.option('--to-format', required=True, help='Target format (e.g. docx)')
@click.option('--workers', '-w', type=int, default=None, help='Number of worker threads')
@click.option('--recursive', '-r', is_flag=True, help='Scan directories recursively')
@click.option('--ocr/--no-ocr', default=False, help='Enable OCR')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--delete', is_flag=True, help='Delete source files after successful conversion')
@click.option('--delete-failures', is_flag=True, default=False, help='Also delete files that failed to convert (use with caution!)')
def batch_command(input_dir, output_dir, from_format, to_format, workers, recursive, ocr, quiet, verbose, delete, delete_failures):
    """Batch convert documents in a directory."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)
        
    if not quiet:
        click.echo(f"Scanning '{input_dir}'...")

    try:
        # Initialize BatchProcessor
        processor = BatchProcessor(max_workers=workers)
        register_all_converters(processor.engine)
        
        count = processor.scan_directory(
            input_dir, output_dir, 
            recursive=recursive, 
            from_format=from_format, 
            to_format=to_format,
            ocr_enabled=ocr # Option for engine
        )
        
        if not quiet:
            click.echo(f"Found {count} files to convert.")
            
        if count == 0:
            return

        # Setup progress bar
        if not quiet:
            pbar = tqdm(total=count, desc="Converting", unit="file", file=sys.stdout)
            def update_progress():
                pbar.update(1)
            
            report = processor.process_queue(progress_callback=update_progress)
            pbar.close()
        else:
            report = processor.process_queue()
            
        if not quiet:
            if report.failed == 0:
                click.echo(click.style(f"Batch completed. {report.success} converted.", fg='green'))
            else:
                click.echo(click.style(f"Batch completed. {report.success} converted, {report.failed} failed.", fg='yellow'))
                click.echo("Failures:")
                for path, reason in report.failures:
                    click.echo(f"  - {os.path.basename(path)}: {click.style(reason, fg='red')}")
        
        # Handle source file deletion after batch processing
        if delete and report.success > 0:
            deleted_count = 0
            failed_count = 0
            
            # Delete successful conversions
            for task in processor.tasks:
                input_file = task['input_path']
                # Check if this file was successful (not in failures list)
                failed_files = set(path for path, _ in report.failures)
                
                if input_file not in failed_files:
                    try:
                        os.remove(input_file)
                        deleted_count += 1
                        logger.info(f"Deleted source file after conversion: {input_file}")
                    except Exception as e:
                        failed_count += 1
                        logger.warning(f"Failed to delete source file {input_file}: {e}")
            
            # Optionally delete failures too
            if delete_failures and report.failed > 0:
                for failed_file, _ in report.failures:
                    try:
                        os.remove(failed_file)
                        deleted_count += 1
                        logger.info(f"Deleted failed source file: {failed_file}")
                    except Exception as e:
                        failed_count += 1
                        logger.warning(f"Failed to delete source file {failed_file}: {e}")
            
            if not quiet:
                click.echo()
                click.echo(click.style(f"✓ Deleted {deleted_count} source file(s)", fg='yellow'))
                if failed_count > 0:
                    click.echo(click.style(f"⚠ Failed to delete {failed_count} file(s)", fg='yellow'))
                
    except Exception as e:
        msg = f"Error during batch processing: {e}"
        click.echo(click.style(msg, fg='red'))
        if verbose:
            logger.exception(msg)
        sys.exit(1)
