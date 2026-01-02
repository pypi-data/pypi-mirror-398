"""
Command Line Interface for the Data Pipeline.
"""


import typer
import sys
import os
import yaml
from pathlib import Path
from typing import Optional
from typing_extensions import Annotated
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from saara.pipeline import DataPipeline

# Initialize Typer app
app = typer.Typer(
    name="saara",
    help="🧠 Saara - Autonomous Document-to-LLM Data Factory",
    add_completion=False,
    no_args_is_help=True
)
console = Console()

# --- Shared Wizards ---
# (Kept mostly as-is, just removed argparse logic)

def interactive_mode():
    """Run the interactive setup wizard."""
    console.print(Panel.fit(
        "[bold cyan]🧠 Saara Data Engine[/bold cyan]\n\n"
        "Autonomous Document-to-LLM Data Factory\n"
        "[dim]Transform PDFs into training-ready datasets & fine-tuned models[/dim]",
        title="✨ Welcome",
        border_style="cyan"
    ))
    
    # Selection Mode with Table
    console.print("\n")
    mode_table = Table(title="Choose Your Workflow", show_header=True, header_style="bold magenta")
    mode_table.add_column("Option", style="cyan", width=8)
    mode_table.add_column("Mode", style="green")
    mode_table.add_column("Description", style="dim")
    
    mode_table.add_row("1", "📄 Dataset Creation", "Extract data from PDFs → Generate training datasets")
    mode_table.add_row("2", "🧠 Model Training", "Fine-tune LLMs on your prepared data")
    mode_table.add_row("3", "🧪 Model Evaluation", "Test & improve trained models")
    mode_table.add_row("4", "🚀 Model Deployment", "Deploy models locally or to cloud")
    
    console.print(mode_table)
    console.print()
    
    mode_choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4"], default="1")
    
    if mode_choice == "2":
        run_training_wizard()
        return
    elif mode_choice == "3":
        run_evaluation_wizard()
        return
    elif mode_choice == "4":
        run_deployment_wizard()
        return

    # --- Comprehensive Dataset Creation Flow ---
    run_dataset_creation_wizard()


def run_dataset_creation_wizard():
    """Comprehensive dataset creation wizard with auto-detection and advanced options."""
    import requests
    
    console.print(Panel.fit(
        "[bold cyan]📄 Dataset Creation Wizard[/bold cyan]\n\n"
        "This wizard will guide you through creating high-quality training datasets from your PDFs.",
        title="Step 1: Configuration",
        border_style="cyan"
    ))
    
    # Step 1: Path Configuration
    console.print("\n[bold]📁 Step 1: Configure Paths[/bold]\n")
    
    base_dir = os.getcwd()
    raw_path = Prompt.ask(
        "Enter path to PDF files or folder",
        default=base_dir
    ).strip('"\'')
    
    raw_path_obj = Path(raw_path)
    if not raw_path_obj.exists():
        console.print(f"[red]❌ Path does not exist: {raw_path}[/red]")
        if not Confirm.ask("Continue anyway?", default=False):
            return
    else:
        # Count PDFs
        if raw_path_obj.is_dir():
            pdf_count = len(list(raw_path_obj.glob("**/*.pdf")))
            console.print(f"[green]✓ Found {pdf_count} PDF files in directory[/green]")
        else:
            console.print(f"[green]✓ Single file: {raw_path_obj.name}[/green]")
    
    output_path = Prompt.ask(
        "Enter output directory for datasets",
        default="./datasets"
    ).strip('"\'')
    
    # Create output directory
    Path(output_path).mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓ Output directory: {output_path}[/green]")
    
    # Step 2: Auto-detect Ollama Models
    console.print("\n[bold]🔍 Step 2: Detecting Available Models[/bold]\n")
    
    available_models = []
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.ok:
            models_data = response.json().get("models", [])
            available_models = [m["name"].split(":")[0] for m in models_data]
            available_models = list(set(available_models))  # Dedupe
            console.print(f"[green]✓ Ollama is running. Found {len(available_models)} models.[/green]")
        else:
            console.print("[yellow]⚠ Could not fetch Ollama models[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Ollama not running or unreachable: {e}[/red]")
        console.print("[dim]Start Ollama with: ollama serve[/dim]")
        if not Confirm.ask("Continue anyway?", default=False):
            return
    
    # Vision model selection
    console.print("\n[bold]👁️ Vision OCR Model:[/bold]")
    vision_models = {
        "1": ("moondream", "Moondream", "Fast, lightweight (~2GB VRAM)"),
        "2": ("qwen2.5vl", "Qwen2.5-VL", "High accuracy (~4GB VRAM)"),
    }
    
    v_table = Table(show_header=True, header_style="bold magenta")
    v_table.add_column("ID", style="cyan", width=4)
    v_table.add_column("Model", style="green")
    v_table.add_column("Description")
    v_table.add_column("Status", style="yellow")
    
    for key, (model_name, display_name, desc) in vision_models.items():
        status = "✓ Available" if model_name in available_models else "⚠ Not pulled"
        v_table.add_row(key, display_name, desc, status)
    
    console.print(v_table)
    v_choice = Prompt.ask("Choose vision model", choices=["1", "2"], default="1")
    vision_model = vision_models[v_choice][0]
    
    # Check if model needs to be pulled
    if vision_model not in available_models:
        console.print(f"[yellow]Model {vision_model} not found locally.[/yellow]")
        if Confirm.ask(f"Pull {vision_model} now?", default=True):
            console.print(f"[dim]Running: ollama pull {vision_model}[/dim]")
            os.system(f"ollama pull {vision_model}")
    
    # Analyzer model selection
    console.print("\n[bold]🧠 Analyzer/Labeling Model:[/bold]")
    analyzer_models = {
        "1": ("granite4", "Granite 4.0", "IBM enterprise model, balanced"),
        "2": ("llama3.2", "Llama 3.2", "Meta's latest, instruction-following"),
        "3": ("qwen2.5", "Qwen 2.5", "Alibaba, strong reasoning"),
        "4": ("mistral", "Mistral", "Fast, efficient"),
    }
    
    a_table = Table(show_header=True, header_style="bold magenta")
    a_table.add_column("ID", style="cyan", width=4)
    a_table.add_column("Model", style="green")
    a_table.add_column("Description")
    a_table.add_column("Status", style="yellow")
    
    for key, (model_name, display_name, desc) in analyzer_models.items():
        # Check both exact and partial matches
        is_available = any(model_name in m for m in available_models)
        status = "✓ Available" if is_available else "⚠ Not pulled"
        a_table.add_row(key, display_name, desc, status)
    
    console.print(a_table)
    a_choice = Prompt.ask("Choose analyzer model", choices=["1", "2", "3", "4"], default="1")
    analyzer_model = analyzer_models[a_choice][0]
    
    # Check if model needs to be pulled
    if not any(analyzer_model in m for m in available_models):
        console.print(f"[yellow]Model {analyzer_model} not found locally.[/yellow]")
        if Confirm.ask(f"Pull {analyzer_model} now?", default=True):
            console.print(f"[dim]Running: ollama pull {analyzer_model}[/dim]")
            os.system(f"ollama pull {analyzer_model}")
    
    # Step 3: Advanced Options
    console.print("\n[bold]⚙️ Step 3: Advanced Options[/bold]\n")
    
    show_advanced = Confirm.ask("Configure advanced options?", default=False)
    
    # Defaults
    chunk_size = 2500
    chunk_overlap = 600
    qa_per_chunk = 30
    generate_summaries = True
    generate_instructions = True
    dataset_name = "dataset"
    
    if show_advanced:
        dataset_name = Prompt.ask("Dataset name prefix", default="dataset")
        
        console.print("\n[dim]Chunking affects how documents are split for processing.[/dim]")
        chunk_size = int(Prompt.ask("Chunk size (characters)", default="2500"))
        chunk_overlap = int(Prompt.ask("Chunk overlap (characters)", default="600"))
        
        console.print("\n[dim]Generation settings affect output quality and speed.[/dim]")
        qa_per_chunk = int(Prompt.ask("Q&A pairs per chunk", default="30"))
        generate_summaries = Confirm.ask("Generate summaries?", default=True)
        generate_instructions = Confirm.ask("Generate instruction pairs?", default=True)
    
    # Step 4: Summary and Confirmation
    console.print("\n")
    summary_table = Table(title="📋 Configuration Summary", show_header=True, header_style="bold cyan")
    summary_table.add_column("Setting", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Source Path", str(raw_path))
    summary_table.add_row("Output Directory", output_path)
    summary_table.add_row("Dataset Name", dataset_name)
    summary_table.add_row("Vision Model", vision_models[v_choice][1])
    summary_table.add_row("Analyzer Model", analyzer_models[a_choice][1])
    summary_table.add_row("Chunk Size", f"{chunk_size} chars")
    summary_table.add_row("Q&A per Chunk", str(qa_per_chunk))
    summary_table.add_row("Summaries", "Yes" if generate_summaries else "No")
    summary_table.add_row("Instructions", "Yes" if generate_instructions else "No")
    
    console.print(summary_table)
    console.print()
    
    if not Confirm.ask("[bold]Proceed with dataset creation?[/bold]", default=True):
        console.print("[yellow]Aborted by user.[/yellow]")
        return
    
    # Step 5: Run Pipeline
    console.print("\n[bold cyan]🚀 Starting Dataset Creation Pipeline...[/bold cyan]\n")
    
    # Build config
    config_path = "config.yaml"
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
    
    # Apply all settings
    if 'pdf' not in config: config['pdf'] = {}
    if 'ollama' not in config: config['ollama'] = {}
    if 'output' not in config: config['output'] = {}
    if 'text' not in config: config['text'] = {}
    if 'labeling' not in config: config['labeling'] = {}
    
    config['pdf']['ocr_engine'] = vision_model
    config['ollama']['model'] = analyzer_model
    config['output']['directory'] = output_path
    config['text']['chunk_size'] = chunk_size
    config['text']['chunk_overlap'] = chunk_overlap
    config['labeling']['qa_per_chunk'] = qa_per_chunk
    config['labeling']['generate_summaries'] = generate_summaries
    config['labeling']['generate_instructions'] = generate_instructions
    
    # Initialize pipeline
    pipeline = DataPipeline(config)
    
    # Health check
    console.print("[dim]Checking pipeline health...[/dim]")
    if not pipeline.check_health():
        console.print("[red]❌ Health check failed. Please ensure Ollama is running with the selected models.[/red]")
        console.print(f"[dim]Try: ollama pull {analyzer_model}[/dim]")
        return
    
    # Process
    raw_path_obj = Path(raw_path)
    if raw_path_obj.is_file():
        result = pipeline.process_file(str(raw_path_obj), dataset_name)
    else:
        result = pipeline.process_directory(str(raw_path_obj), dataset_name)
    
    # Results
    if result.success:
        console.print("\n")
        console.print(Panel.fit(
            f"[bold green]✅ Dataset Creation Complete![/bold green]\n\n"
            f"Documents Processed: {result.documents_processed}\n"
            f"Total Chunks: {result.total_chunks}\n"
            f"Total Samples: {result.total_samples}\n"
            f"Duration: {result.duration_seconds:.1f}s",
            title="Success",
            border_style="green"
        ))
        
        console.print("\n[bold]📁 Generated Files:[/bold]")
        for dtype, files in result.output_files.items():
            if isinstance(files, dict):
                for fmt, fpath in files.items():
                    console.print(f"  • {dtype}/{fmt}: [cyan]{fpath}[/cyan]")
            else:
                console.print(f"  • {dtype}: [cyan]{files}[/cyan]")
        
        # Offer training
        console.print("\n")
        if Confirm.ask("Would you like to train a model on this dataset now?", default=False):
            # Find ShareGPT file
            sharegpt_file = f"{output_path}/{dataset_name}_sharegpt.jsonl"
            if not os.path.exists(sharegpt_file):
                sharegpt_files = list(Path(output_path).glob("*sharegpt*.jsonl"))
                if sharegpt_files:
                    sharegpt_file = str(sharegpt_files[0])
            
            run_training_wizard(default_data_path=sharegpt_file, config=config)
    else:
        console.print("\n[bold red]❌ Dataset creation failed[/bold red]")
        for error in result.errors:
            console.print(f"  • {error}")


def run_training_wizard(default_data_path: str = None, config: dict = None):
    """Run the interactive training setup."""
    console.print("\n[bold]Select Base Model to Train:[/bold]")
    t_table = Table(show_header=True, header_style="bold magenta")
    t_table.add_column("ID", style="cyan", width=4)
    t_table.add_column("Model", style="green")
    t_table.add_column("Type", style="yellow")
    
    t_table.add_row("1", "sarvamai/sarvam-1", "2B")
    t_table.add_row("2", "google/gemma-2b", "2B")
    t_table.add_row("3", "meta-llama/Llama-3.2-1B", "1B")
    t_table.add_row("4", "Qwen/Qwen2.5-7B", "7B")
    t_table.add_row("5", "mistralai/Mistral-7B-v0.1", "7B")
    t_table.add_row("6", "TinyLlama/TinyLlama-1.1B", "1.1B")
    t_table.add_row("7", "Other", "-")
    
    console.print(t_table)
    t_choice = Prompt.ask("Choose a base model", choices=["1", "2", "3", "4", "5", "6", "7"], default="2")
    
    model_id = "sarvamai/sarvam-1"
    if t_choice == "2":
        model_id = "google/gemma-2b"
    elif t_choice == "3":
        model_id = "meta-llama/Llama-3.2-1B"
    elif t_choice == "4":
        model_id = "Qwen/Qwen2.5-7B"
    elif t_choice == "5":
        model_id = "mistralai/Mistral-7B-v0.1"
    elif t_choice == "6":
        model_id = "TinyLlama/TinyLlama-1.1B"
    elif t_choice == "7":
        model_id = Prompt.ask("Enter HuggingFace Model ID (e.g. microsoft/phi-2)")
    
    console.print(f"[bold]Selected Model:[/bold] {model_id}")
    
    gated_models = ["google/gemma", "meta-llama/Llama-3", "mistralai/Mistral"]
    is_gated = any(gated in model_id for gated in gated_models)
    
    if is_gated:
        console.print("[yellow]⚠️ This model requires HuggingFace authentication.[/yellow]")
        if Confirm.ask("Do you want to login to HuggingFace now?", default=True):
            hf_token = Prompt.ask("Enter your HuggingFace token", password=True)
            try:
                from huggingface_hub import login
                login(token=hf_token)
                console.print("[green]✅ Successfully logged in![/green]")
            except Exception as e:
                console.print(f"[red]Login failed: {e}[/red]")
                return
    
    while True:
        if default_data_path:
            data_file = default_data_path
            default_data_path = None
        else:
            default_guess = "datasets/interactive_batch_sharegpt.jsonl"
            if not os.path.exists(default_guess):
                default_guess = "datasets/distilled_train.jsonl"
                
            data_file = Prompt.ask("Path to training dataset (.jsonl)", default=default_guess).strip('"\'')
            
        path_obj = Path(data_file)
        
        if path_obj.is_dir():
            jsonl_files = list(path_obj.glob("*.jsonl"))
            if jsonl_files:
                console.print(f"[green]Found {len(jsonl_files)} JSONL files.[/green]")
                
                sharegpt_files = [f for f in jsonl_files if 'sharegpt' in f.name.lower()]
                instruction_files = [f for f in jsonl_files if 'instruction' in f.name.lower()]
                qa_files = [f for f in jsonl_files if '_qa' in f.name.lower()]
                
                console.print("\n[bold]Select dataset type:[/bold]")
                console.print("  1. ShareGPT (Chat)")
                console.print("  2. Instruction")
                console.print("  3. Q&A")
                console.print("  4. All files")
                
                type_choice = Prompt.ask("Select type", choices=["1", "2", "3", "4"], default="1")
                
                if type_choice == "1":
                    selected_files = sharegpt_files
                elif type_choice == "2":
                    selected_files = instruction_files
                elif type_choice == "3":
                    selected_files = qa_files
                else:
                    selected_files = jsonl_files
                
                if not selected_files:
                    console.print("[red]No files of selected type found.[/red]")
                    continue
                
                data_file = [str(f) for f in selected_files]
                break
            else:
                console.print("[red]No .jsonl files found.[/red]")
                continue
        elif not path_obj.exists():
             console.print(f"[red]File or directory not found: {data_file}[/red]")
             default_data_path = None
             if not Confirm.ask("Try again?", default=True):
                 return
        else:
            break
        
    resume_path = None
    if Confirm.ask("Do you want to resume from a checkpoint?", default=False):
        resume_path = Prompt.ask("Enter path to checkpoint directory").strip('"\'')
    
    from saara.train import LLMTrainer
    
    if not config:
        config_path = "config.yaml"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        else:
            config = {}

    trainer = LLMTrainer(model_id=model_id, config=config)
    try:
        trainer.train(data_file, resume_from_checkpoint=resume_path)
    except Exception as e:
        console.print(f"[bold red]Training failed:[/bold red] {e}")


def run_evaluation_wizard(config: dict = None):
    """Run the model evaluation wizard."""
    console.print(Panel.fit(
        "[bold cyan]🧪 Model Evaluation[/bold cyan]\n\n"
        "Test your fine-tuned model using Granite 4 as a judge.",
        title="Evaluation Mode",
        border_style="cyan"
    ))
    
    models_dir = Path("models")
    if not models_dir.exists():
        console.print("[red]No models directory found. Please train a model first.[/red]")
        return
    
    finetuned_models = []
    for model_dir in models_dir.iterdir():
        if model_dir.is_dir():
            adapter_path = model_dir / "final_adapter"
            if adapter_path.exists():
                finetuned_models.append({
                    "name": model_dir.name,
                    "path": str(adapter_path),
                })
    
    if not finetuned_models:
        console.print("[yellow]No fine-tuned models found.[/yellow]")
        return
    
    console.print("\n[bold]Available Models:[/bold]\n")
    for i, m in enumerate(finetuned_models, 1):
        console.print(f" {i}. {m['name']}")
    
    choice = Prompt.ask("Select model", choices=[str(i) for i in range(1, len(finetuned_models)+1)], default="1")
    selected = finetuned_models[int(choice)-1]
    
    base_model = Prompt.ask("Enter base model ID", default="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    
    console.print("\n[bold]Select Mode:[/bold]")
    console.print("1. Standard Evaluation")
    console.print("2. Autonomous Learning")
    mode_choice = Prompt.ask("Select mode", choices=["1", "2"], default="1")
    
    from saara.evaluator import ModelEvaluator
    evaluator = ModelEvaluator(config)
    
    if mode_choice == "1":
        num_samples = int(Prompt.ask("Number of test samples", default="10"))
        evaluator.evaluate_adapter(base_model, selected["path"], num_samples=num_samples)
    else:
        topic = Prompt.ask("Enter topic to learn about")
        iterations = int(Prompt.ask("Learning iterations", default="10"))
        teacher_config = {"provider": "ollama", "model": "granite-code:8b"}
        evaluator.run_autonomous_learning(base_model, selected["path"], topic, num_iterations=iterations, teacher_config=teacher_config)


def run_deployment_wizard(config: dict = None):
    """Run the model deployment wizard."""
    console.print(Panel.fit(
        "[bold cyan]🚀 Model Deployment[/bold cyan]",
        title="Deployment Mode",
        border_style="green"
    ))
    console.print("[dim]Deployment wizard functionality not fully refactored in this snippet.[/dim]")


# --- Typer Commands ---

@app.command()
def run():
    """Start the interactive setup wizard."""
    interactive_mode()


@app.command()
def wizard():
    """Start the interactive setup wizard (Calculated alias)."""
    interactive_mode()


@app.command()
def process(
    file: str = typer.Argument(..., help="Path to PDF file"),
    name: str = typer.Option(None, "--name", "-n", help="Dataset name"),
    config: str = typer.Option("config.yaml", "--config", "-c", help="Config file path")
):
    """
    Process a single PDF file.
    """
    if not Path(file).exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(code=1)
        
    pipeline = DataPipeline(config)
    if not pipeline.check_health():
        console.print("[red]Health check failed. Ensure Ollama is running.[/red]")
        raise typer.Exit(code=1)
    
    result = pipeline.process_file(file, name)
    if result.success:
        console.print(f"\n[bold green]✅ Success![/bold green] Processed in {result.duration_seconds:.1f}s")
        console.print(f"   Total samples generated: {result.total_samples}")
    else:
        console.print(f"\n[bold red]❌ Failed[/bold red]")
        for error in result.errors:
            console.print(f"   • {error}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    directory: str = typer.Argument(..., help="Directory containing PDFs"),
    name: str = typer.Option("dataset", "--name", "-n", help="Dataset name"),
    config: str = typer.Option("config.yaml", "--config", "-c", help="Config file path")
):
    """
    Process all PDFs in a directory.
    """
    if not Path(directory).is_dir():
        console.print(f"[red]Error: Directory not found: {directory}[/red]")
        raise typer.Exit(code=1)
        
    pipeline = DataPipeline(config)
    if not pipeline.check_health():
        console.print("[red]Health check failed. Ensure Ollama is running.[/red]")
        raise typer.Exit(code=1)
    
    result = pipeline.process_directory(directory, name)
    if result.success:
        console.print(f"\n[bold green]✅ Success![/bold green] Processed {result.documents_processed} docs in {result.duration_seconds:.1f}s")
        console.print(f"   Total samples generated: {result.total_samples}")
    else:
        console.print(f"\n[bold red]❌ Failed[/bold red]")
        for error in result.errors:
            console.print(f"   • {error}")
        raise typer.Exit(code=1)


@app.command()
def health(
    config: str = typer.Option("config.yaml", "--config", "-c", help="Config file path")
):
    """
    Check pipeline health (Ollama connection).
    """
    pipeline = DataPipeline(config)
    healthy = pipeline.check_health()
    raise typer.Exit(code=0 if healthy else 1)


@app.command()
def serve(
    host: str = typer.Option('0.0.0.0', help='Host to bind to'),
    port: int = typer.Option(8000, "--port", "-p", help='Port to bind to'),
    config: str = typer.Option("config.yaml", "--config", "-c", help="Config file path")
):
    """
    Start the Saara web interface.
    """
    console.print(f"[bold cyan]Starting Saara web interface on http://{host}:{port}[/bold cyan]")
    import uvicorn
    uvicorn.run("saara.api:app", host=host, port=port, reload=True)


@app.command()
def distill(
    input_path: str = typer.Argument(None, help="Path to input file (markdown/text) or directory"),
    output: str = typer.Option("datasets/synthetic", "--output", "-o", help="Output directory"),
    data_type: str = typer.Option("all", "--type", "-t", help="Data type: factual, reasoning, conversational, instruction, all"),
    pairs: int = typer.Option(3, "--pairs", "-p", help="Pairs per type per chunk"),
    clean: bool = typer.Option(True, "--clean/--no-clean", help="Enable text sanitization"),
    filter_quality: bool = typer.Option(True, "--filter/--no-filter", help="Enable quality filtering"),
    config: str = typer.Option("config.yaml", "--config", "-c", help="Config file path")
):
    """
    Distill text into high-quality training data.
    
    Generates synthetic training samples with:
    - Text sanitization (removes OCR artifacts)
    - Semantic chunking (by headers)
    - Multi-type generation (factual, reasoning, conversational)
    - Quality filtering (removes low-quality samples)
    
    Examples:
        saara distill document.md --type reasoning
        saara distill ./texts --pairs 5 --output ./my_dataset
    """
    from saara.cleaner import TextCleaner, SemanticChunker
    from saara.synthetic_generator import SyntheticDataGenerator, DataType, QualityJudge
    import json
    
    console.print(Panel.fit(
        "[bold cyan]🔬 Synthetic Data Generation[/bold cyan]\n\n"
        "Creating high-quality training data with sanitization and quality control.",
        title="Distillation Pipeline",
        border_style="cyan"
    ))
    
    # Load config
    cfg = {}
    if os.path.exists(config):
        with open(config, "r") as f:
            cfg = yaml.safe_load(f) or {}
    
    # Determine input
    if not input_path:
        # Interactive mode - ask for input
        input_path = Prompt.ask("Enter path to input file or directory").strip('"\'')
    
    input_obj = Path(input_path)
    if not input_obj.exists():
        console.print(f"[red]❌ Input path not found: {input_path}[/red]")
        raise typer.Exit(code=1)
    
    # Collect input files
    if input_obj.is_file():
        input_files = [input_obj]
    else:
        input_files = list(input_obj.glob("**/*.md")) + list(input_obj.glob("**/*.txt"))
        console.print(f"[green]Found {len(input_files)} text files[/green]")
    
    if not input_files:
        console.print("[red]No input files found[/red]")
        raise typer.Exit(code=1)
    
    # Initialize components
    cleaner = TextCleaner(cfg) if clean else None
    chunker = SemanticChunker(cfg)
    generator = SyntheticDataGenerator(cfg)
    
    # Determine data types
    type_map = {
        "factual": [DataType.FACTUAL],
        "reasoning": [DataType.REASONING],
        "conversational": [DataType.CONVERSATIONAL],
        "instruction": [DataType.INSTRUCTION],
        "all": [DataType.FACTUAL, DataType.REASONING, DataType.CONVERSATIONAL],
    }
    selected_types = type_map.get(data_type.lower(), [DataType.ALL])
    
    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  Data types: {[t.value for t in selected_types]}")
    console.print(f"  Pairs per type: {pairs}")
    console.print(f"  Sanitization: {'Enabled' if clean else 'Disabled'}")
    console.print(f"  Quality filter: {'Enabled' if filter_quality else 'Disabled'}")
    console.print()
    
    # Process
    all_samples = []
    total_generated = 0
    total_passed = 0
    total_rejected = 0
    rejection_stats = {}
    
    from tqdm import tqdm
    
    for file_path in tqdm(input_files, desc="Processing files"):
        console.print(f"\n[dim]Processing: {file_path.name}[/dim]")
        
        # Read file
        text = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Step 1: Sanitize
        if cleaner:
            result = cleaner.clean(text)
            text = result.cleaned
            if result.removed_phrases:
                console.print(f"  [dim]Removed {len(result.removed_phrases)} filler phrases[/dim]")
        
        # Step 2: Chunk
        chunks = chunker.chunk_by_headers(text)
        console.print(f"  [dim]Created {len(chunks)} semantic chunks[/dim]")
        
        # Step 3: Generate
        for chunk in chunks:
            gen_result = generator.generate(
                chunk['content'],
                data_types=selected_types,
                pairs_per_type=pairs
            )
            
            all_samples.extend(gen_result.samples)
            total_generated += gen_result.total_generated
            total_passed += gen_result.total_passed
            total_rejected += gen_result.total_rejected
            
            for reason, count in gen_result.rejection_stats.items():
                rejection_stats[reason] = rejection_stats.get(reason, 0) + count
    
    # Save results
    Path(output).mkdir(parents=True, exist_ok=True)
    
    # Save as JSONL (Alpaca format)
    alpaca_path = Path(output) / "synthetic_alpaca.jsonl"
    with open(alpaca_path, 'w', encoding='utf-8') as f:
        for sample in all_samples:
            entry = {
                "instruction": sample.instruction,
                "input": sample.input_context,
                "output": sample.output,
                "type": sample.data_type
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # Save as ShareGPT format
    sharegpt_path = Path(output) / "synthetic_sharegpt.jsonl"
    with open(sharegpt_path, 'w', encoding='utf-8') as f:
        for sample in all_samples:
            entry = {
                "conversations": [
                    {"from": "human", "value": sample.instruction},
                    {"from": "gpt", "value": sample.output}
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # Summary
    console.print("\n")
    summary = Table(title="📊 Distillation Results", show_header=True, header_style="bold cyan")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green")
    
    summary.add_row("Files Processed", str(len(input_files)))
    summary.add_row("Total Generated", str(total_generated))
    summary.add_row("Passed Quality Filter", str(total_passed))
    summary.add_row("Rejected", str(total_rejected))
    summary.add_row("Pass Rate", f"{(total_passed/max(total_generated,1))*100:.1f}%")
    
    console.print(summary)
    
    if rejection_stats:
        console.print("\n[bold]Rejection Reasons:[/bold]")
        for reason, count in sorted(rejection_stats.items(), key=lambda x: -x[1]):
            console.print(f"  • {reason}: {count}")
    
    console.print(f"\n[bold green]✅ Output saved to:[/bold green]")
    console.print(f"  • Alpaca format: [cyan]{alpaca_path}[/cyan]")
    console.print(f"  • ShareGPT format: [cyan]{sharegpt_path}[/cyan]")




@app.command()
def train(
    data: Annotated[Optional[str], typer.Option("--data", "-d", help="Path to training data (jsonl)")] = None,
    model: str = typer.Option('sarvamai/sarvam-1', "--model", "-m", help='Base model ID'),
    config: str = typer.Option("config.yaml", "--config", "-c", help="Config file path")
):
    """
    Fine-tune model using SFT.
    """
    from saara.train import LLMTrainer
    
    if not data:
        data = "datasets/distilled_train.jsonl"
        
    trainer = LLMTrainer(model_id=model, config=DataPipeline(config).config)
    trainer.train(data)


@app.command()
def evaluate(
    base_model: str = typer.Argument(..., help="Base model ID (e.g. TinyLlama/...)"),
    adapter_path: str = typer.Argument(..., help="Path to adapter checkpoint"),
    config: str = typer.Option("config.yaml", "--config", "-c", help="Config file path")
):
    """
    Evaluate a fine-tuned model using Granite as a judge.
    """
    from saara.evaluator import ModelEvaluator
    evaluator = ModelEvaluator(config)
    evaluator.evaluate_adapter(base_model, adapter_path)


def main():
    """Main entry point."""
    app()

if __name__ == "__main__":
    main()

