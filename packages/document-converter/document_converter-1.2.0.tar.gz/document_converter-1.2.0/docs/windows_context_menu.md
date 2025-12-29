# Windows Context Menu Integration

This directory contains tools to integrate DocumentConverter into the Windows File Explorer context menu.
This allows you to right-click on supported files (**PDF, DOCX, TXT, HTML, MD, ODT**) and select **"Convert with DocumentConverter"** to quickly convert them.

**Note:** The option will NOT appear for unsupported file types (like images or system files) to keep your context menu clean.

## Contents

- `add_context_menu.reg`: Registry script template.
- `install_context_menu.bat`: Automated installer script.

## Setup Instructions

1. **Build the Executable**
   Ensure you have built the standalone executable first. It should be located in `dist/document-converter.exe`.
   ```bash
   python -m PyInstaller --clean document-converter.spec
   ```

2. **Run Installer**
   - Navigate to `tools/windows`.
   - Right-click `install_context_menu.bat`.
   - Select **"Run as Administrator"**.
   - Follow the on-screen prompts.

## How it works

The script creates a registry key at `HKEY_CLASSES_ROOT\*\shell\DocumentConverter`.
It configures the command to run:
```
"C:\Path\To\Your\document-converter.exe" convert "%1" --choose
```
This passes the selected file as the input argument and opens the interactive picker for the output format/name.

## Uninstallation

To remove the context menu entry, open Registry Editor (`regedit`), navigate to `HKEY_CLASSES_ROOT\*\shell\` and delete the `DocumentConverter` key.
