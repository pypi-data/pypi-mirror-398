import typer
import shutil
import tarfile
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from pathlib import Path
from typing import Optional
from ide_updater.config import load_config, save_config, ensure_dirs

# Modules will be imported dynamically or explicitly later
from ide_updater.modules.vscode import VSCodeUpdater
from ide_updater.modules.cursor import CursorUpdater
from ide_updater.modules.kiro import KiroUpdater

app = typer.Typer(help="CLI tool to update Linux IDEs (VS Code, Cursor, Kiro)")
console = Console()

@app.callback()
def callback():
    """
    IDE Updater - Keep your development environment fresh.
    """
    # Check if we're in PATH (helpful for first-time users)
    import os
    import shutil
    local_bin = Path.home() / ".local" / "bin"
    if local_bin.exists() and str(local_bin) not in os.environ.get("PATH", ""):
        # Only show this once, not every time
        path_warning_shown = os.environ.get("IDE_UPDATER_PATH_WARNING_SHOWN", "0")
        if path_warning_shown != "1":
            console.print(
                "[yellow]⚠️  Note:[/yellow] If you just installed with pipx and see this message, "
                "your PATH may not be set up yet.\n"
                "Run: [bold]pipx ensurepath[/bold] then restart your terminal.\n"
                "Or run: [bold]source ~/.bashrc[/bold]\n"
            )
            os.environ["IDE_UPDATER_PATH_WARNING_SHOWN"] = "1"
    pass

@app.command()
def init():
    """Initialize configuration and directories."""
    config = load_config()
    ensure_dirs(config)
    save_config(config)
    console.print(f"[green]Initialized configuration at {config['install_dir']}[/green]")

def get_updaters(config):
    updaters = []
    if config["ides"]["vscode"]["enabled"]:
        updaters.append(VSCodeUpdater(config))
    if config["ides"]["cursor"]["enabled"]:
        updaters.append(CursorUpdater(config))
    if config["ides"]["kiro"]["enabled"]:
        updaters.append(KiroUpdater(config))
    return updaters

def _update_ide(updater, config):
    """Internal function to update a single IDE."""
    console.print(f"Checking [bold]{updater.name}[/bold]...")
    
    try:
        latest_version = updater.get_latest_version()
        # In a real scenario, we'd check against a local version.
        # For now, we assume 'update' implies force update or re-install if local version check isn't robust.
        # But let's try to be smart.
        
        console.print(f"Latest version: [green]{latest_version}[/green]")
        
        url = updater.get_download_url()
        console.print(f"Downloading from: {url}")
        
        # Determine filename
        filename = url.split("/")[-1]
        # Sanitization mainly for Cursor/Kiro which might have weird URLs
        if "cursor" in updater.name.lower() and not filename.endswith(".AppImage"):
             filename = "cursor.AppImage"
        if "kiro" in updater.name.lower() and not filename:
             filename = "kiro.AppImage"
        if "visual studio code" in updater.name.lower() and not filename.endswith(".tar.gz"):
            # VS Code usually ends in .tar.gz from the link, but let's be safe
            filename = "vscode.tar.gz"

        dest_path = Path(config["temp_dir"]) / filename
        updater.download(url, dest_path)
        
        console.print("[green]Download complete.[/green]")
        console.print("[bold blue]Installing...[/bold blue]")
        
        install_dir = Path(config["install_dir"])
        
        # Installation logic
        if str(dest_path).endswith(".AppImage"):
            dest_path.chmod(0o755)
            # Create a clean name e.g. Cursor.AppImage
            clean_name = f"{updater.name.replace(' ', '')}.AppImage"
            target_path = install_dir / clean_name
            shutil.move(str(dest_path), str(target_path))
            console.print(f"[green]Installed to {target_path}[/green]")
            
        elif str(dest_path).endswith(".tar.gz"):
            # For VS Code, we want a clean directory.
            # e.g. ~/Applications/VSCode-linux-x64 -> ~/Applications/VSCode
            
            # 1. Extract to temp dir first to inspect structure
            extract_temp = Path(config["temp_dir"]) / "extracted"
            if extract_temp.exists():
                shutil.rmtree(extract_temp)
            extract_temp.mkdir()
            
            with tarfile.open(dest_path, "r:gz") as tar:
                tar.extractall(path=extract_temp)
            
            # 2. Find the root inside extracted
            extracted_items = list(extract_temp.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                source_folder = extracted_items[0]
            else:
                source_folder = extract_temp

            # 3. Move to install_dir
            # e.g. VSCode
            final_folder_name = updater.name.replace(" ", "")
            final_path = install_dir / final_folder_name
            
            if final_path.exists():
                shutil.rmtree(final_path)
            
            shutil.move(str(source_folder), str(final_path))
            console.print(f"[green]Installed to {final_path}[/green]")
            
        else:
            console.print(f"[yellow]Unknown file type for {dest_path}. Saved at {dest_path}[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Update failed for {updater.name}: {e}[/red]")


@app.command()
def update(ide: Optional[str] = typer.Argument(None, help="The IDE to update. If omitted, updates all.")):
    """
    Update one or all IDEs.
    """
    config = load_config()
    ensure_dirs(config) # Safety check
    
    updaters = get_updaters(config)
    
    if ide:
        # Update specific
        target = None
        for u in updaters:
            if u.name.lower().replace(" ", "") == ide.lower().replace(" ", "") or \
               (ide.lower() in u.name.lower()):
                target = u
                break
        
        if not target:
            console.print(f"[red]IDE '{ide}' not found or not enabled.[/red]")
            return
        
        _update_ide(target, config)
    else:
        # Update all
        console.print(f"[bold]Updating all {len(updaters)} enabled IDEs...[/bold]")
        for u in updaters:
            _update_ide(u, config)
            console.print("-" * 40)

@app.command()
def check():
    """Check for updates for enabled IDEs."""
    config = load_config()
    console.print("[bold blue]Checking for updates...[/bold blue]")
    
    updaters = get_updaters(config)
    
    table = Table(title="IDE Status")
    table.add_column("IDE", style="cyan")
    table.add_column("Installed Version", style="blue")
    table.add_column("Latest Version", style="green")
    table.add_column("Status", style="magenta")

    for updater in updaters:
        try:
            latest = updater.get_latest_version()
            current = updater.get_current_version()
            
            status = "Available"
            if current == "not installed":
                status = "Not Installed"
            elif current != "unknown" and latest != "unknown":
                 if current == latest:
                     status = "Up to date"
                 else:
                     status = "Update Available"

            table.add_row(updater.name, current, latest, status)
        except Exception as e:
            table.add_row(updater.name, "unknown", "Error", str(e))
            
    console.print(table)
