"""Status command for basic-memory CLI."""

import asyncio
from typing import Set

import typer
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from basic_memory import db
from basic_memory.cli.app import app
from basic_memory.config import config
from basic_memory.db import DatabaseType
from basic_memory.repository import DocumentRepository, EntityRepository
from basic_memory.services import FileSyncService
from basic_memory.services.file_sync_service import SyncReport

# Create rich console
console = Console()


async def get_sync_service(db_type=DatabaseType.FILESYSTEM) -> FileSyncService:
    """Get sync service instance."""
    async with db.engine_session_factory(db_path=config.database_path, db_type=db_type) as (
        engine,
        session_maker,
    ):
        document_repository = DocumentRepository(session_maker)
        entity_repository = EntityRepository(session_maker)
        sync_service = FileSyncService(document_repository, entity_repository)
        return sync_service


def add_files_to_tree(tree: Tree, paths: Set[str], style: str):
    """Add files to tree, grouped by directory."""
    # Group by directory
    by_dir = {}
    for path in sorted(paths):
        parts = path.split("/", 1)
        dir_name = parts[0] if len(parts) > 1 else ""
        file_name = parts[1] if len(parts) > 1 else parts[0]
        by_dir.setdefault(dir_name, []).append(file_name)

    # Add to tree
    for dir_name, files in sorted(by_dir.items()):
        if dir_name:
            branch = tree.add(f"[bold]{dir_name}/[/bold]")
        else:
            branch = tree

        for file_name in sorted(files):
            branch.add(f"[{style}]{file_name}[/{style}]")


def display_changes(title: str, changes: SyncReport, verbose: bool = False):
    """Display changes using Rich for better visualization."""
    if not verbose:
        # Current compact display by directory
        tree = Tree(title)
        
        if changes.total_changes == 0:
            tree.add("No changes")
            console.print(Panel(tree, expand=False))
            return
            
        # Group by directory and count changes
        by_dir = {}
        for change_type, paths in [
            ("new", changes.new),
            ("modified", changes.modified), 
            ("deleted", changes.deleted)
        ]:
            for path in paths:
                dir_name = path.split("/", 1)[0]
                by_dir.setdefault(dir_name, {"new": 0, "modified": 0, "deleted": 0})
                by_dir[dir_name][change_type] += 1
                
        # Show directory summaries
        for dir_name, counts in sorted(by_dir.items()):
            summary_parts = []
            if counts["new"]:
                summary_parts.append(f"[green]+{counts['new']} new[/green]")
            if counts["modified"]:
                summary_parts.append(f"[yellow]~{counts['modified']} modified[/yellow]")
            if counts["deleted"]:
                summary_parts.append(f"[red]-{counts['deleted']} deleted[/red]")
                
            tree.add(f"[bold]{dir_name}/[/bold] {' '.join(summary_parts)}")
            
    else:
        # Verbose display with full file paths
        tree = Tree(title)
        
        if changes.total_changes == 0:
            tree.add("No changes")
            console.print(Panel(tree, expand=False))
            return
            
        # Show total counts
        summary = []
        if changes.new:
            summary.append(f"[green]{len(changes.new)} new[/green]")
        if changes.modified:
            summary.append(f"[yellow]{len(changes.modified)} modified[/yellow]")
        if changes.deleted:
            summary.append(f"[red]{len(changes.deleted)} deleted[/red]")
        tree.add(f"Found {', '.join(summary)}")
        
        # Add file groups with full paths
        if changes.new:
            new_branch = tree.add("[green]New Files[/green]")
            add_files_to_tree(new_branch, changes.new, "green")
            
        if changes.modified:
            mod_branch = tree.add("[yellow]Modified[/yellow]")
            add_files_to_tree(mod_branch, changes.modified, "yellow")
            
        if changes.deleted:
            del_branch = tree.add("[red]Deleted[/red]")
            add_files_to_tree(del_branch, changes.deleted, "red")
    
    console.print(Panel(tree, expand=False))


async def run_status(sync_service: FileSyncService, verbose: bool = False):
    """Check sync status of files vs database."""

    # Check knowledge/ directory
    knowledge_changes = await sync_service.find_knowledge_changes(config.knowledge_dir)
    display_changes("Knowledge Files", knowledge_changes, verbose)

    # Check documents/ directory 
    document_changes = await sync_service.find_document_changes(config.documents_dir)
    display_changes("Documents", document_changes, verbose)


@app.command()
def status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed file information"),
):
    """Show sync status between files and database."""
    try:
        sync_service = asyncio.run(get_sync_service())
        asyncio.run(run_status(sync_service, verbose))
    except Exception as e:
        typer.echo(f"Error checking status: {e}", err=True)
        raise typer.Exit(1)