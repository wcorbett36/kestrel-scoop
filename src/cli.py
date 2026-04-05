import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from src.crawler import KBConfig, DocCrawler
from src.manifest import ManifestTracker
from src.synthesizer import StrategicSynthesizer
from src.obsidian import ObsidianFormatter

load_dotenv()

app = typer.Typer(help="K-Compiler: Strategic Ingestion Engine")
console = Console()

@app.command()
def build(
    config_file: str = typer.Option("config.yaml", "--config", "-c", help="Path to config.yaml"),
    manifest_file: str = typer.Option(".kb_manifest.json", "--manifest", "-m", help="Path to manifest state"),
):
    """
    Compiles documentation from configured repositories into an Obsidian Wiki.
    """
    console.print("[bold green]Starting K-Compiler Build...[/bold green]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as progress:
        
        # 1. Pipeline Init
        task_init = progress.add_task("[cyan]Initializing compilation pipelines...", total=None)
        config = KBConfig(config_file)
        tracker = ManifestTracker(manifest_file)
        crawler = DocCrawler(config, tracker)
        progress.update(task_init, completed=1)

        # 2. Ingestion
        task_crawl = progress.add_task("[cyan]Crawling repositories for updates...", total=None)
        buffered_files_by_project = crawler.process()    
        has_changes = any(len(file_tuples) > 0 for file_tuples in buffered_files_by_project.values())
        progress.update(task_crawl, completed=1)
        
        if not has_changes:
            console.print("[bold yellow]No changes detected. Wiki compilation skipped (Delta: <2s).[/bold yellow]")
            return

        # 3. Node Synthesis
        task_nodes = progress.add_task("[cyan]Synthesizing Document Nodes...", total=None)
        synthesizer = StrategicSynthesizer(config)
        formatter = ObsidianFormatter(config.output_dir)
        
        profiles = {}
        for project_name, file_tuples in buffered_files_by_project.items():
            if not file_tuples:
                continue
                
            docs_content = ""
            source_paths_to_track = []
            
            for source_file, buffered_file in file_tuples:
                docs_content += f"# Document Chunk: {buffered_file.name}\n{buffered_file.read_text(encoding='utf-8')}\n\n"
                source_paths_to_track.append(source_file)
                
            profile = synthesizer.synthesize_node(project_name, docs_content)
            profiles[project_name] = profile
            
            formatter.write_project_node(project_name, profile)
            
            # Commit manifest updates per-project
            for spath in source_paths_to_track:
                tracker.update_record(spath)
                
        progress.update(task_nodes, completed=1)

        # 4. View Synthesis & MOCs
        if profiles:
            task_view = progress.add_task("[cyan]Extrapolating Strategic Views...", total=None)
            view = synthesizer.synthesize_view(profiles)
            
            global_view_name = "Global Ecosystem Status"
            formatter.write_strategic_view(global_view_name, view)
            
            nodes = list(profiles.keys())
            formatter.write_moc(nodes=nodes, views=[global_view_name])
            progress.update(task_view, completed=1)
            
    console.print(f"[bold green]Vault compilation successful! Output linked to: {config.output_dir}[/bold green]")

@app.command()
def clean():
    """
    Purges the generated wiki output and ephemeral state buffers.
    """
    import shutil
    from pathlib import Path
    
    paths_to_clean = ["./wiki", "./.kb_buffer", "./.kb_manifest.json"]
    for path_str in paths_to_clean:
        path = Path(path_str)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            console.print(f"[green]Cleaned {path_str}[/green]")
    console.print("[bold green]Environment is clean.[/bold green]")

if __name__ == "__main__":
    app()
