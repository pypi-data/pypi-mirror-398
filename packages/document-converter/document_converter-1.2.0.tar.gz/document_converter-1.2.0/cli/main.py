"""
Document Converter CLI - Main Entry Point

Provides both command-line interface and interactive mode.
"""
import click
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CLI Mode (Click commands)
# ============================================================================

@click.group()
@click.version_option(version='1.2.0')
def cli():
    """Document Converter CLI tool."""
    pass

# Import and register commands
from cli.commands.convert import convert_command
from cli.commands.batch import batch_command
from cli.commands.info import info_command
from cli.commands.cache import cache_clear_command, cache_stats_command

cli.add_command(convert_command)
cli.add_command(batch_command)
cli.add_command(info_command)
cli.add_command(cache_clear_command)
cli.add_command(cache_stats_command)

# ============================================================================
# Interactive Mode (Menu-driven)
# ============================================================================

def clear_screen():
    """Clear console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_header():
    """Display application header."""
    print("=" * 70)
    print(" " * 20 + "DOCUMENT CONVERTER v1.2.0")
    print("=" * 70)
    print()

def show_main_menu():
    """Display main menu options."""
    print("Selecciona una opción:")
    print()
    print("  1. Convertir un archivo")
    print("  2. Batch - Convertir carpeta completa")
    print("  3. Ver información de archivo")
    print("  4. Ver estadísticas de caché")
    print("  5. Limpiar caché")
    print("  0. Salir")
    print()

def wait_for_enter():
    """Wait for user to press Enter."""
    input("\nPresiona Enter para continuar...")

def convertir_archivo_interactivo():
    """Interactive file conversion."""
    clear_screen()
    show_header()
    print("CONVERTIR ARCHIVO")
    print("-" * 70)
    print()
    
    # Show supported conversions
    print("Conversiones soportadas:")
    print("  ✓ Conversión bidireccional completa entre todos los formatos")
    print("  ✓ Formatos: PDF, DOCX, TXT, HTML, MD, ODT")
    print("  ✓ PDF con soporte OCR para documentos escaneados")
    print()
    print("-" * 70)
    print()
    
    # Get input file using interactive picker
    print("📂 Selecciona el archivo de entrada:")
    print()
    
    from cli.ui.file_picker import pick_file_interactive
    input_path = pick_file_interactive(directory=".", pattern="*")
    
    if not input_path:
        print()
        print("❌ No se seleccionó ningún archivo")
        wait_for_enter()
        return
    
    print()
    print(f"✓ Archivo seleccionado: {input_path}")
    
    # Get output file
    print()
    print("Archivo de salida:")
    output_path = input("  » ").strip()
    
    if not output_path:
        print("❌ Debes especificar un archivo de salida")
        wait_for_enter()
        return
    
    # Show tip
    print()
    print("💡 Tip: La extensión del archivo de salida determina el formato")
    print("   Ejemplo: 'salida.pdf' convierte a PDF, 'salida.html' a HTML")
    print()
    
    # Perform conversion
    print("🔄 Convirtiendo...")
    print()
    
    try:
        # Import here to avoid circular imports
        from converter.engine import ConversionEngine
        from core.registry import register_all_converters
        
        engine = ConversionEngine()
        register_all_converters(engine)
        
        success = engine.convert(input_path, output_path)
        
        print()
        if success:
            print("✅ ¡Conversión exitosa!")
            print(f"📄 Archivo guardado: {os.path.abspath(output_path)}")
            print()
            
            # Ask if user wants to delete source file
            print("🗑️  ¿Deseas borrar el archivo original?")
            delete_response = input("   (s/n): ").strip().lower()
            
            if delete_response in ('s', 'si', 'sí', 'yes', 'y'):
                try:
                    os.remove(input_path)
                    print(f"✓ Archivo original eliminado: {input_path}")
                except Exception as e:
                    print(f"⚠️  No se pudo eliminar el archivo: {e}")
            else:
                print("✓ Archivo original conservado")
        else:
            print("❌ La conversión falló")
            
    except Exception as e:
        print()
        print(f"❌ Error durante la conversión:")
        print(f"   {str(e)}")
    
    wait_for_enter()

def batch_interactivo():
    """Interactive batch processing."""
    clear_screen()
    show_header()
    print("BATCH - CONVERTIR CARPETA COMPLETA")
    print("-" * 70)
    print()
    
    # Get input directory
    while True:
        print("Carpeta de entrada:")
        input_dir = input("  » ").strip()
        
        if not input_dir:
            print("❌ Debes especificar una carpeta")
            continue
            
        if input_dir.lower() == 'cancelar':
            return
            
        if not os.path.exists(input_dir):
            print(f"❌ La carpeta '{input_dir}' no existe")
            retry = input("¿Intentar de nuevo? (s/n): ").lower()
            if retry != 's':
                return
            continue
            
        if not os.path.isdir(input_dir):
            print(f"❌ '{input_dir}' no es una carpeta válida")
            continue
            
        break
    
    # Get output directory
    print()
    print("Carpeta de salida:")
    output_dir = input("  » ").strip()
    
    if not output_dir:
        print("❌ Debes especificar una carpeta de salida")
        wait_for_enter()
        return
    
    # Get format to convert from
    print()
    print("Formato origen (txt, docx, pdf, html, md):")
    from_format = input("  » ").strip().lower()
    
    if not from_format:
        from_format = 'txt'
        print(f"  Usando formato por defecto: {from_format}")
    
    # Get format to convert to
    print()
    print("Formato destino (txt, docx, pdf, html, md):")
    to_format = input("  » ").strip().lower()
    
    if not to_format:
        to_format = 'pdf'
        print(f"  Usando formato por defecto: {to_format}")
    
    # Ask for worker count
    print()
    print("Número de workers paralelos (1-16, default=4):")
    workers_input = input("  » ").strip()
    
    try:
        max_workers = int(workers_input) if workers_input else 4
        max_workers = max(1, min(16, max_workers))
    except ValueError:
        max_workers = 4
    
    print(f"  Usando {max_workers} workers")
    
    # Perform batch conversion
    print()
    print("🔄 Escaneando archivos...")
    print()
    
    try:
        from converter.batch_processor import BatchProcessor
        from core.registry import register_all_converters
        
        processor = BatchProcessor(max_workers=max_workers)
        register_all_converters(processor.engine)
        
        count = processor.scan_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            from_format=from_format,
            to_format=to_format
        )
        
        print(f"📁 Encontrados {count} archivos para convertir")
        
        if count == 0:
            print("⚠️  No se encontraron archivos para procesar")
            wait_for_enter()
            return
        
        print()
        confirm = input("¿Continuar con la conversión? (s/n): ").lower()
        if confirm != 's':
            print("Operación cancelada")
            wait_for_enter()
            return
        
        print()
        print("🔄 Procesando archivos...")
        
        # Simple progress counter
        progress = [0]
        def show_progress():
            progress[0] += 1
            print(f"  Procesado {progress[0]}/{count} archivos", end='\r')
        
        report = processor.process_queue(progress_callback=show_progress)
        
        print()
        print()
        print("✅ Proceso completado")
        print(f"   Total: {report.total}")
        print(f"   Exitosos: {report.success}")
        print(f"   Fallidos: {report.failed}")
        
        # Ask if user wants to delete source files
        if report.success > 0:
            print()
            print("🗑️  ¿Deseas borrar los archivos originales convertidos exitosamente?")
            delete_response = input("   (s/n): ").strip().lower()
            
            if delete_response in ('s', 'si', 'sí', 'yes', 'y'):
                deleted_count = 0
                failed_count = 0
                
                # Delete successful conversions
                failed_files = set(path for path, _ in report.failures)
                
                for task in processor.tasks:
                    input_file = task['input_path']
                    
                    if input_file not in failed_files:
                        try:
                            os.remove(input_file)
                            deleted_count += 1
                        except Exception as e:
                            failed_count += 1
                
                print(f"✓ Eliminados {deleted_count} archivo(s) original(es)")
                if failed_count > 0:
                    print(f"⚠️  No se pudieron eliminar {failed_count} archivo(s)")
            else:
                print("✓ Archivos originales conservados")
        
    except Exception as e:
        print()
        print(f"❌ Error durante el procesamiento:")
        print(f"   {str(e)}")
    
    wait_for_enter()

def info_interactivo():
    """Interactive file info display."""
    clear_screen()
    show_header()
    print("VER INFORMACIÓN DE ARCHIVO")
    print("-" * 70)
    print()
    
    while True:
        print("Archivo a inspeccionar:")
        file_path = input("  » ").strip()
        
        if not file_path:
            print("❌ Debes especificar un archivo")
            continue
            
        if file_path.lower() == 'cancelar':
            return
            
        if not os.path.exists(file_path):
            print(f"❌ El archivo '{file_path}' no existe")
            retry = input("¿Intentar de nuevo? (s/n): ").lower()
            if retry != 's':
                return
            continue
            
        break
    
    print()
    print("📄 Información del archivo:")
    print("-" * 70)
    
    try:
        # Basic file info
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_path)[1]
        
        print(f"Nombre: {os.path.basename(file_path)}")
        print(f"Ruta: {os.path.abspath(file_path)}")
        print(f"Tamaño: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
        print(f"Extensión: {file_ext}")
        
        # Try to detect format
        from converter.base.format_detector import FormatDetector
        detector = FormatDetector()
        detected = detector.detect(file_path)
        
        if detected:
            print(f"Formato detectado: {detected.upper()}")
        
    except Exception as e:
        print(f"❌ Error al leer información: {str(e)}")
    
    wait_for_enter()

def mostrar_cache_stats():
    """Display cache statistics."""
    clear_screen()
    show_header()
    print("ESTADÍSTICAS DE CACHÉ")
    print("-" * 70)
    print()
    
    try:
        from core.cache_manager import CacheManager
        
        cache = CacheManager()
        stats = cache.get_stats()
        
        print(f"📊 Elementos en caché: {stats['items']}")
        print(f"💾 Tamaño total: {stats['total_size_bytes']:,} bytes")
        print(f"    ({stats['total_size_bytes'] / 1024 / 1024:.2f} MB)")
        
        if stats['items'] > 0:
            avg_size = stats['total_size_bytes'] / stats['items']
            print(f"📏 Tamaño promedio: {avg_size:,.0f} bytes")
        
    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {str(e)}")
    
    wait_for_enter()

def limpiar_cache():
    """Clear all cache."""
    clear_screen()
    show_header()
    print("LIMPIAR CACHÉ")
    print("-" * 70)
    print()
    
    print("⚠️  Esto eliminará todos los archivos en caché.")
    confirm = input("¿Estás seguro? (s/n): ").lower()
    
    if confirm != 's':
        print("Operación cancelada")
        wait_for_enter()
        return
    
    try:
        from core.cache_manager import CacheManager
        
        cache = CacheManager()
        cache.clear()
        
        print()
        print("✅ Caché limpiado exitosamente")
        
    except Exception as e:
        print()
        print(f"❌ Error al limpiar caché: {str(e)}")
    
    wait_for_enter()

def interactive_mode():
    """Main interactive mode loop."""
    while True:
        clear_screen()
        show_header()
        show_main_menu()
            
        opcion = input("Opción: ").strip()
            
        if opcion == '1':
            convertir_archivo_interactivo()
        elif opcion == '2':
            batch_interactivo()
        elif opcion == '3':
            info_interactivo()
        elif opcion == '4':
            mostrar_cache_stats()
        elif opcion == '5':
            limpiar_cache()
        elif opcion == '0':
            clear_screen()
            print()
            print("¡Gracias por usar Document Converter!")
            print()
            break
        else:
            print()
            print("❌ Opción no válida. Por favor selecciona 0-5.")
            wait_for_enter()

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    from cli.ui import reset_terminal, ensure_clean_exit
    
    # Clean terminal at startup for fresh start
    reset_terminal()
    
    try:
        if len(sys.argv) == 1:
            # No arguments = Interactive mode
            interactive_mode()
        else:
            # With arguments = CLI mode
            cli()
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
    finally:
        # Clean terminal state when the entire program exits
        ensure_clean_exit()