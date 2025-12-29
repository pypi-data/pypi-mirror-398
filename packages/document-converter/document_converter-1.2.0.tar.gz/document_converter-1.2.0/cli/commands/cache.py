import click
import logging
from core.cache_manager import CacheManager

logger = logging.getLogger(__name__)

# Initialize manager (could be shared or instantiated per command)
# Instantiating per command is safer for CLI statelessness
def get_manager():
    return CacheManager()

@click.command('cache-clear')
def cache_clear_command():
    """Clear all cached conversion results."""
    try:
        manager = get_manager()
        manager.clear_all()
        click.echo(click.style("Cache successfully cleared.", fg='green'))
    except Exception as e:
        click.echo(click.style(f"Error clearing cache: {e}", fg='red'))

@click.command('cache-stats')
def cache_stats_command():
    """Show cache statistics (item count and size)."""
    try:
        manager = get_manager()
        stats = manager.get_stats()
        
        click.echo("Cache Statistics:")
        click.echo(f"  Items: {stats['items']}")
        
        # Format bytes
        size = stats['total_size_bytes']
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.2f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.2f} MB"
            
        click.echo(f"  Total Size: {size_str}")
        
    except Exception as e:
        click.echo(click.style(f"Error getting stats: {e}", fg='red'))
