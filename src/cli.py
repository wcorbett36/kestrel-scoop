import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from src.crawler import KBConfig, DocCrawler
from src.manifest import ManifestTracker
from src.synthesizer import StrategicSynthesizer, split_text_segments, ProjectProfile, DocChunkSummary
from src.obsidian import ObsidianFormatter
from src.ontology import OntologyDefiner, OntologyHarvester
from src.errors import BuildError, SynthesisStep
from src.preflight import check_local_llm_reachable

load_dotenv()

app = typer.Typer(help="K-Compiler: Strategic Ingestion Engine")
console = Console(stderr=True)


def _print_build_error(err: BuildError) -> None:
    lines = [f"[bold red]{err.message}[/bold red]"]
    if err.project_name:
        lines.append(f"Project: [cyan]{err.project_name}[/cyan]")
    if err.detail:
        lines.append(f"Detail: {err.detail}")
    if err.hint:
        lines.append(f"Hint: {err.hint}")
    console.print(Panel("\n".join(lines), title=f"Build failed — {err.step.value}", border_style="red"))


@app.command()
def build(
    config_file: str = typer.Option("config.yaml", "--config", "-c", help="Path to config.yaml"),
    manifest_file: str = typer.Option(".kb_manifest.json", "--manifest", "-m", help="Path to manifest state"),
    skip_preflight: bool = typer.Option(
        False,
        "--skip-preflight",
        help="Skip GET /health check for OPENAI_API_BASE (offline or custom routing)",
    ),
):
    """
    Compiles documentation from configured repositories into an Obsidian Wiki.
    """
    console.print("[bold green]Starting K-Compiler Build...[/bold green]")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
        ) as progress:

            task_init = progress.add_task("[cyan]Initializing compilation pipelines...", total=None)
            config = KBConfig(config_file)
            tracker = ManifestTracker(manifest_file)
            crawler = DocCrawler(config, tracker)
            progress.update(task_init, completed=1)

            task_crawl = progress.add_task("[cyan]Crawling repositories for updates...", total=None)
            results_by_project = crawler.process()
            has_changes = any(len(state.get("changed", [])) > 0 for state in results_by_project.values())
            progress.update(task_crawl, completed=1)

            if not has_changes:
                console.print("[bold yellow]No changes detected. Wiki compilation skipped (Delta: <2s).[/bold yellow]")
                return

            if not skip_preflight:
                task_pf = progress.add_task("[cyan]Checking LLM endpoint...", total=None)
                check_local_llm_reachable()
                progress.update(task_pf, completed=1)

            task_nodes = progress.add_task("[cyan]Synthesizing Document Nodes...", total=None)
            synthesizer = StrategicSynthesizer(config)
            formatter = ObsidianFormatter(config.output_dir)

            profiles = {}
            profiles = {}
            for project_name, file_state in results_by_project.items():
                changed_files = file_state.get("changed", [])
                unchanged_files = file_state.get("unchanged", [])

                if not changed_files and not unchanged_files:
                    continue

                if not changed_files:
                    cached_profile = tracker.get_project_profile(project_name)
                    if cached_profile:
                        # Re-write the updated node anyway to guarantee disk state
                        profile = ProjectProfile(**cached_profile)
                        formatter.write_project_node(project_name, profile)
                        profiles[project_name] = profile
                        continue

                docs_content = ""
                chunk_summaries = []

                if config.chunk_repo_synthesis:
                    for source_file in unchanged_files:
                        for c_dict in tracker.get_file_chunks(source_file):
                            chunk_summaries.append(DocChunkSummary(**c_dict))

                for source_file, buffered_file in changed_files:
                    try:
                        text = buffered_file.read_text(encoding="utf-8")
                    except UnicodeDecodeError as e:
                        raise BuildError(
                            step=SynthesisStep.READ_FILE,
                            message="Could not decode file as UTF-8",
                            project_name=project_name,
                            detail=str(source_file),
                        ) from e
                    except OSError as e:
                        raise BuildError(
                            step=SynthesisStep.READ_FILE,
                            message=f"Could not read file: {e}",
                            project_name=project_name,
                            detail=str(source_file),
                        ) from e

                    docs_content += f"# Document Chunk: {buffered_file.name}\n{text}\n\n"

                    if config.chunk_repo_synthesis:
                        rel_label = str(source_file)
                        segments = split_text_segments(text, config.max_chunk_chars)
                        n_seg = len(segments)
                        new_file_chunks = []
                        for i, seg in enumerate(segments):
                            if not seg.strip():
                                continue
                            label = f"{rel_label} (part {i + 1}/{n_seg})" if n_seg > 1 else rel_label
                            try:
                                chunk = synthesizer.synthesize_chunk(label, seg)
                                chunk_summaries.append(chunk)
                                new_file_chunks.append(chunk.model_dump())
                            except Exception as e:
                                raise BuildError(
                                    step=SynthesisStep.MAP_CHUNK,
                                    message=str(e),
                                    project_name=project_name,
                                    detail=label,
                                    hint="Check MLX/server logs and LLM_MAX_RETRIES for transient failures.",
                                ) from e
                        tracker.update_file_record(source_file, new_file_chunks)
                    else:
                        tracker.update_file_record(source_file, [])

                try:
                    if config.chunk_repo_synthesis:
                        profile = synthesizer.synthesize_node_from_chunks(project_name, chunk_summaries)
                    else:
                        profile = synthesizer.synthesize_node(project_name, docs_content)
                except BuildError:
                    raise
                except Exception as e:
                    if config.chunk_repo_synthesis:
                        step = (
                            SynthesisStep.REDUCE
                            if chunk_summaries
                            else SynthesisStep.EMPTY_FALLBACK
                        )
                        detail = (
                            "merge chunk summaries"
                            if step == SynthesisStep.REDUCE
                            else "empty-doc fallback node"
                        )
                    else:
                        step = SynthesisStep.SINGLE_SHOT
                        detail = "single-shot node synthesis"
                    raise BuildError(
                        step=step,
                        message=str(e),
                        project_name=project_name,
                        detail=detail,
                    ) from e

                tracker.update_project_profile(project_name, profile.model_dump())
                formatter.write_project_node(project_name, profile)
                profiles[project_name] = profile

            progress.update(task_nodes, completed=1)

            if profiles:
                task_view = progress.add_task("[cyan]Extrapolating Strategic Views...", total=None)
                try:
                    view = synthesizer.synthesize_view(profiles)
                except Exception as e:
                    raise BuildError(
                        step=SynthesisStep.STRATEGIC_VIEW,
                        message=str(e),
                        hint=(
                            "Project nodes under ./wiki and .kb_manifest.json may already be updated for "
                            "completed projects. Fix the model/backend and re-run build."
                        ),
                    ) from e

                global_view_name = "Global Ecosystem Status"
                formatter.write_strategic_view(global_view_name, view)

                nodes = list(profiles.keys())
                formatter.write_moc(nodes=nodes, views=[global_view_name])
                progress.update(task_view, completed=1)

        console.print(f"[bold green]Vault compilation successful! Output linked to: {config.output_dir}[/bold green]")

    except BuildError as err:
        _print_build_error(err)
        if os.getenv("K_COMPILER_DEBUG"):
            console.print_exception()
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if os.getenv("K_COMPILER_DEBUG"):
            console.print_exception()
        raise typer.Exit(code=1)


@app.command()
def clean():
    """
    Purges the generated wiki output and ephemeral state buffers.
    """
    import shutil
    from pathlib import Path as P

    paths_to_clean = ["./wiki", "./.kb_buffer", "./.kb_manifest.json"]
    for path_str in paths_to_clean:
        path = P(path_str)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            console.print(f"[green]Cleaned {path_str}[/green]")
@app.command()
def extract_ontology(
    config_file: str = typer.Option("config.yaml", "--config", "-c", help="Path to config.yaml"),
    manifest_file: str = typer.Option(".kb_manifest.json", "--manifest", "-m", help="Path to manifest state"),
):
    """
    Two-Tier Process: Generates a deep ontology per repo via Frontier LLM,
    harvests facts via Local LLM, and drops knowledge artifacts directly into wiki.
    """
    console.print("[bold green]Starting Two-Tier Ontology Extraction...[/bold green]")
    try:
        config = KBConfig(config_file)
        tracker = ManifestTracker(manifest_file)
        crawler = DocCrawler(config, tracker)
        synthesizer = StrategicSynthesizer(config)
        definer = OntologyDefiner(synthesizer)
        harvester = OntologyHarvester(synthesizer)
        formatter = ObsidianFormatter(config.output_dir)

        console.print("[cyan]Crawling repositories...[/cyan]")
        results_by_project = crawler.process()

        for project_name, file_state in results_by_project.items():
            console.print(f"\\n[bold]Processing {project_name}[/bold]")
            changed_files = file_state.get("changed", [])
            unchanged_files = file_state.get("unchanged", [])
            
            project_config = next((p for p in config.projects if p.get("name") == project_name), {})
            focus = project_config.get("focus", "General codebase")
            
            console.print(f"  [cyan]1. Requesting Frontier LLM to build ontology schema for '{focus}'...[/cyan]")
            schema = definer.build_schema(project_name, focus)
            
            chunks = []
            console.print(f"  [cyan]2. Local LLM harvesting facts against schema...[/cyan]")
            for item in changed_files:
                source_file, buffered_file = item
                text = buffered_file.read_text(encoding="utf-8")
                segments = split_text_segments(text, config.max_chunk_chars)
                for i, seg in enumerate(segments):
                    chunks.append(harvester.extract_facts(f"{source_file.name} [{i}]", seg, schema))

            for source_file in unchanged_files:
                text = source_file.read_text(encoding="utf-8")
                segments = split_text_segments(text, config.max_chunk_chars)
                for i, seg in enumerate(segments):
                    chunks.append(harvester.extract_facts(f"{source_file.name} [{i}]", seg, schema))
                    
            if not chunks:
                console.print("  [yellow]No docs found to harvest.[/yellow]")
                continue
                
            console.print(f"  [cyan]3. Frontier LLM merging {len(chunks)} extracted chunks into structural state...[/cyan]")
            state = harvester.merge_facts(project_name, schema, chunks)
            
            out_path = formatter.write_ontology_state(project_name, state)
            console.print(f"  [green]Ontology state recorded to {out_path}[/green]")
            
        console.print("\\n[bold green]Ontology Extraction Complete![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if os.getenv("K_COMPILER_DEBUG"):
            console.print_exception()
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
