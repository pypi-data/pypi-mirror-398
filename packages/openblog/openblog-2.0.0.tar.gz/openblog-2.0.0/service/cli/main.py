#!/usr/bin/env python3
"""
OpenBlog CLI - AI-Powered Blog Generation

A beautiful, interactive command-line interface for generating
high-quality, SEO-optimized blog articles using AI.
"""

import asyncio
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import typer
from rich import print as rprint
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
)
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.tree import Tree
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
from rich.style import Style

from . import __version__

# Initialize Rich console
console = Console()

# Create the Typer app
app = typer.Typer(
    name="openblog",
    help="AI-Powered Blog Generation from your terminal",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# ============================================================================
# ASCII ART & BRANDING
# ============================================================================

LOGO = r"""[bold cyan]
   ____                   ____  _
  / __ \                 |  _ \| |
 | |  | |_ __   ___ _ __ | |_) | | ___   __ _
 | |  | | '_ \ / _ \ '_ \|  _ <| |/ _ \ / _` |
 | |__| | |_) |  __/ | | | |_) | | (_) | (_| |
  \____/| .__/ \___|_| |_|____/|_|\___/ \__, |
        | |                              __/ |
        |_|                             |___/
[/bold cyan]"""

LOGO_MINI = "[bold cyan]OpenBlog[/bold cyan]"
TAGLINE = "[dim italic]AI-Powered Blog Generation[/dim italic]"


def show_banner(mini: bool = False) -> None:
    """Display the OpenBlog banner."""
    if mini:
        rprint(f"\n{LOGO_MINI} {TAGLINE}\n")
    else:
        rprint(LOGO)
        rprint(Align.center(f"{TAGLINE}  [dim]v{__version__}[/dim]"))
        rprint()


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


# ============================================================================
# CONFIGURATION
# ============================================================================

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "it": "Italian (Italiano)",
    "pt": "Portuguese (Português)",
    "nl": "Dutch (Nederlands)",
    "pl": "Polish (Polski)",
    "ru": "Russian (Русский)",
    "ja": "Japanese (日本語)",
    "zh": "Chinese (中文)",
    "ko": "Korean (한국어)",
    "ar": "Arabic (العربية)",
    "hi": "Hindi (हिन्दी)",
    "tr": "Turkish (Türkçe)",
    "sv": "Swedish (Svenska)",
    "da": "Danish (Dansk)",
    "no": "Norwegian (Norsk)",
    "fi": "Finnish (Suomi)",
    "he": "Hebrew (עברית)",
}

AUDIENCE_LEVELS = {
    "general": "General Audience - Easy to understand for everyone",
    "business": "Business Professionals - Industry-focused content",
    "technical": "Technical Readers - In-depth technical details",
    "academic": "Academic - Research-oriented, scholarly tone",
    "beginner": "Beginners - Simple explanations, no jargon",
}

CONTENT_TONES = {
    "professional": "Professional & Authoritative",
    "conversational": "Conversational & Friendly",
    "educational": "Educational & Informative",
    "persuasive": "Persuasive & Compelling",
    "inspirational": "Inspirational & Motivating",
}

OUTPUT_FORMATS = {
    "html": "HTML - Ready for web publishing",
    "markdown": "Markdown - For static site generators",
    "json": "JSON - Full structured data",
}


def get_config() -> dict:
    """Load configuration from environment."""
    from dotenv import load_dotenv
    load_dotenv()

    return {
        "gemini_api_key": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        "api_url": os.getenv("OPENBLOG_API_URL", "http://localhost:8000"),
        "output_dir": os.getenv("OPENBLOG_OUTPUT_DIR", "./output"),
    }


# ============================================================================
# INTERACTIVE MENU HELPERS
# ============================================================================

def show_menu(title: str, options: Dict[str, str], show_back: bool = True) -> str:
    """Display an interactive menu and return the selected key."""
    rprint()
    rprint(f"[bold]{title}[/bold]")
    rprint()

    # Create options table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan bold", width=4)
    table.add_column("Option", style="white")

    keys = list(options.keys())
    for i, (key, description) in enumerate(options.items(), 1):
        table.add_row(f"[{i}]", description)

    if show_back:
        table.add_row("[0]", "[dim]← Back[/dim]")

    rprint(table)
    rprint()

    # Get selection
    max_choice = len(options)
    while True:
        try:
            choice = IntPrompt.ask(
                "[cyan]Select an option[/cyan]",
                default=1,
            )
            if show_back and choice == 0:
                return "__back__"
            if 1 <= choice <= max_choice:
                return keys[choice - 1]
            rprint(f"[red]Please enter a number between {'0' if show_back else '1'} and {max_choice}[/red]")
        except (ValueError, KeyboardInterrupt):
            if show_back:
                return "__back__"
            raise typer.Exit()


def select_language() -> str:
    """Interactive language selection."""
    rprint()
    rprint("[bold]Select Output Language[/bold]")
    rprint()

    # Group languages by region for easier navigation
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("", width=25)
    table.add_column("", width=25)
    table.add_column("", width=25)

    langs = list(SUPPORTED_LANGUAGES.items())
    rows = []
    for i in range(0, len(langs), 3):
        row = []
        for j in range(3):
            if i + j < len(langs):
                code, name = langs[i + j]
                row.append(f"[cyan]{code}[/cyan] {name}")
            else:
                row.append("")
        rows.append(row)

    for row in rows:
        table.add_row(*row)

    rprint(table)
    rprint()

    while True:
        choice = Prompt.ask(
            "[cyan]Enter language code[/cyan]",
            default="en"
        ).lower()
        if choice in SUPPORTED_LANGUAGES:
            return choice
        rprint(f"[red]Invalid language code. Please choose from: {', '.join(SUPPORTED_LANGUAGES.keys())}[/red]")


def select_file(file_types: List[str] = None, start_dir: str = ".") -> Optional[str]:
    """Interactive file browser."""
    current_dir = Path(start_dir).resolve()
    file_types = file_types or [".csv", ".json"]

    while True:
        rprint()
        rprint(f"[bold]Select File[/bold] [dim]({current_dir})[/dim]")
        rprint()

        # List directory contents
        items = []

        # Add parent directory option
        if current_dir.parent != current_dir:
            items.append(("📁", "..", "Parent directory", True))

        # Add directories first
        for item in sorted(current_dir.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                items.append(("📁", item.name, "Directory", True))

        # Add matching files
        for item in sorted(current_dir.iterdir()):
            if item.is_file() and item.suffix.lower() in file_types:
                size = item.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                items.append(("📄", item.name, size_str, False))

        if not items:
            rprint("[yellow]No matching files found in this directory.[/yellow]")
            if not Confirm.ask("Go to parent directory?", default=True):
                return None
            current_dir = current_dir.parent
            continue

        # Display items
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("#", style="cyan", width=4)
        table.add_column("", width=2)
        table.add_column("Name", style="white")
        table.add_column("Info", style="dim")

        for i, (icon, name, info, is_dir) in enumerate(items, 1):
            style = "bold" if is_dir else ""
            table.add_row(f"[{i}]", icon, f"[{style}]{name}[/{style}]", info)

        table.add_row("[0]", "❌", "[dim]Cancel[/dim]", "")

        rprint(table)
        rprint()

        # Manual path input option
        rprint("[dim]Or type a path directly[/dim]")
        rprint()

        choice = Prompt.ask("[cyan]Select[/cyan]", default="1")

        # Handle manual path
        if choice.startswith("/") or choice.startswith("~") or choice.startswith("."):
            path = Path(choice).expanduser().resolve()
            if path.is_file():
                return str(path)
            elif path.is_dir():
                current_dir = path
                continue
            else:
                rprint(f"[red]Path not found: {choice}[/red]")
                continue

        # Handle numeric selection
        try:
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(items):
                icon, name, info, is_dir = items[idx - 1]
                if name == "..":
                    current_dir = current_dir.parent
                elif is_dir:
                    current_dir = current_dir / name
                else:
                    return str(current_dir / name)
            else:
                rprint("[red]Invalid selection[/red]")
        except ValueError:
            rprint("[red]Please enter a number or path[/red]")


def parse_csv_file(filepath: str) -> List[Dict[str, Any]]:
    """Parse a CSV file into article configs."""
    articles = []

    with open(filepath, 'r', encoding='utf-8') as f:
        # Try to detect delimiter
        sample = f.read(1024)
        f.seek(0)

        # Check for common delimiters
        if '\t' in sample:
            delimiter = '\t'
        elif ';' in sample:
            delimiter = ';'
        else:
            delimiter = ','

        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            article = {}

            # Map common column names
            for key in ['topic', 'title', 'subject', 'headline']:
                if key in row and row[key]:
                    article['topic'] = row[key].strip()
                    break

            for key in ['keywords', 'tags', 'keyword']:
                if key in row and row[key]:
                    article['keywords'] = [k.strip() for k in row[key].split(',')]
                    break

            for key in ['company_url', 'company', 'url', 'website']:
                if key in row and row[key]:
                    article['company_url'] = row[key].strip()
                    break

            for key in ['language', 'lang']:
                if key in row and row[key]:
                    article['language'] = row[key].strip().lower()[:2]
                    break

            for key in ['audience', 'target_audience']:
                if key in row and row[key]:
                    article['audience'] = row[key].strip().lower()
                    break

            for key in ['word_count', 'words', 'length']:
                if key in row and row[key]:
                    try:
                        article['word_count'] = int(row[key])
                    except ValueError:
                        pass
                    break

            if article.get('topic'):
                articles.append(article)

    return articles


# ============================================================================
# INTERACTIVE MODE - MAIN FLOW
# ============================================================================

@app.command()
def interactive() -> None:
    """
    Start the interactive OpenBlog experience.

    A guided, menu-driven interface for generating blog articles.
    """
    clear_screen()
    show_banner()

    config = get_config()

    # Check API key
    if not config["gemini_api_key"]:
        rprint(Panel(
            "[yellow]No API key configured.[/yellow]\n\n"
            "Set your Gemini API key:\n"
            "[cyan]export GEMINI_API_KEY='your-key-here'[/cyan]\n\n"
            "Or use the API mode with a remote server.",
            title="[bold yellow]Configuration Required[/bold yellow]",
            border_style="yellow"
        ))
        rprint()

    # Main menu loop
    while True:
        main_menu = {
            "single": "✍️  Generate Single Article",
            "batch": "📚 Batch Generate (CSV/JSON)",
            "quick": "⚡ Quick Generate (minimal options)",
            "config": "⚙️  Configuration",
            "help": "❓ Help & Examples",
            "exit": "👋 Exit",
        }

        choice = show_menu("What would you like to do?", main_menu, show_back=False)

        if choice == "exit":
            rprint("\n[dim]Thanks for using OpenBlog! Happy writing! 👋[/dim]\n")
            raise typer.Exit()
        elif choice == "single":
            _interactive_single_article()
        elif choice == "batch":
            _interactive_batch()
        elif choice == "quick":
            _interactive_quick_generate()
        elif choice == "config":
            _interactive_config()
        elif choice == "help":
            _show_help()
        elif choice == "__back__":
            continue


def _interactive_single_article() -> None:
    """Interactive single article generation flow."""
    clear_screen()
    show_banner(mini=True)

    rprint(Panel(
        "[bold]Single Article Generation[/bold]\n\n"
        "Let's create a high-quality blog article step by step.",
        border_style="cyan"
    ))

    config = get_config()
    article_config = {}

    # Step 1: Topic
    rprint()
    rprint(Rule("[bold cyan]Step 1: Topic[/bold cyan]"))
    rprint()
    rprint("[dim]Enter the main topic or title for your article.[/dim]")
    rprint("[dim]Be specific! Good: 'How to Optimize React Performance in 2024'[/dim]")
    rprint("[dim]Too vague: 'React tips'[/dim]")
    rprint()

    article_config['topic'] = Prompt.ask("[cyan]📝 Topic[/cyan]")

    # Step 2: Keywords
    rprint()
    rprint(Rule("[bold cyan]Step 2: Keywords[/bold cyan]"))
    rprint()
    rprint("[dim]Enter target SEO keywords (comma-separated, optional)[/dim]")
    rprint()

    keywords_input = Prompt.ask("[cyan]🔑 Keywords[/cyan]", default="")
    if keywords_input:
        article_config['keywords'] = [k.strip() for k in keywords_input.split(",")]

    # Step 3: Company Context
    rprint()
    rprint(Rule("[bold cyan]Step 3: Company Context[/bold cyan]"))
    rprint()
    rprint("[dim]Enter your company website URL for brand context (optional)[/dim]")
    rprint("[dim]This helps the AI understand your brand voice and offerings.[/dim]")
    rprint()

    company_url = Prompt.ask("[cyan]🏢 Company URL[/cyan]", default="")
    if company_url:
        article_config['company_url'] = company_url

    # Step 4: Language
    rprint()
    rprint(Rule("[bold cyan]Step 4: Language[/bold cyan]"))
    rprint()

    article_config['language'] = select_language()

    # Step 5: Audience
    rprint()
    rprint(Rule("[bold cyan]Step 5: Target Audience[/bold cyan]"))
    rprint()

    article_config['audience'] = show_menu(
        "Who is this article for?",
        AUDIENCE_LEVELS,
        show_back=False
    )

    # Step 6: Tone
    rprint()
    rprint(Rule("[bold cyan]Step 6: Content Tone[/bold cyan]"))
    rprint()

    article_config['tone'] = show_menu(
        "What tone should the article have?",
        CONTENT_TONES,
        show_back=False
    )

    # Step 7: Word Count
    rprint()
    rprint(Rule("[bold cyan]Step 7: Article Length[/bold cyan]"))
    rprint()

    word_count_options = {
        "1000": "Short (~1,000 words) - Quick read, focused topic",
        "1500": "Medium (~1,500 words) - Standard blog post",
        "2000": "Long (~2,000 words) - Comprehensive coverage",
        "2500": "Extended (~2,500 words) - In-depth guide",
        "3000": "Ultimate (~3,000 words) - Complete resource",
    }

    word_count = show_menu("How long should the article be?", word_count_options, show_back=False)
    article_config['word_count'] = int(word_count)

    # Step 8: Output Format
    rprint()
    rprint(Rule("[bold cyan]Step 8: Output Format[/bold cyan]"))
    rprint()

    article_config['format'] = show_menu(
        "What format do you need?",
        OUTPUT_FORMATS,
        show_back=False
    )

    # Step 9: Output Directory
    rprint()
    rprint(Rule("[bold cyan]Step 9: Output Location[/bold cyan]"))
    rprint()

    default_output = config.get("output_dir", "./output")
    article_config['output_dir'] = Prompt.ask(
        "[cyan]📁 Output directory[/cyan]",
        default=default_output
    )

    # Review & Confirm
    rprint()
    rprint(Rule("[bold green]Review Your Settings[/bold green]"))
    rprint()

    review_table = Table(show_header=False, box=None, padding=(0, 2))
    review_table.add_column("Setting", style="dim")
    review_table.add_column("Value", style="cyan")

    review_table.add_row("Topic", article_config['topic'])
    review_table.add_row("Keywords", ", ".join(article_config.get('keywords', ['(auto-generated)'])))
    review_table.add_row("Company", article_config.get('company_url', '(none)'))
    review_table.add_row("Language", SUPPORTED_LANGUAGES.get(article_config['language'], article_config['language']))
    review_table.add_row("Audience", article_config['audience'])
    review_table.add_row("Tone", article_config['tone'])
    review_table.add_row("Length", f"~{article_config['word_count']:,} words")
    review_table.add_row("Format", article_config['format'].upper())
    review_table.add_row("Output", article_config['output_dir'])

    rprint(Panel(review_table, title="[bold]Article Configuration[/bold]", border_style="green"))
    rprint()

    if Confirm.ask("[green]Generate this article?[/green]", default=True):
        asyncio.run(_generate_article(article_config, config))
    else:
        rprint("[dim]Generation cancelled. Returning to menu...[/dim]")
        time.sleep(1)


def _interactive_batch() -> None:
    """Interactive batch generation flow."""
    clear_screen()
    show_banner(mini=True)

    rprint(Panel(
        "[bold]Batch Article Generation[/bold]\n\n"
        "Generate multiple articles from a CSV or JSON file.",
        border_style="cyan"
    ))

    config = get_config()

    # File source selection
    source_menu = {
        "browse": "📁 Browse for file",
        "path": "⌨️  Enter file path manually",
        "example": "📋 Show example file format",
    }

    source = show_menu("How would you like to provide the file?", source_menu)

    if source == "__back__":
        return

    if source == "example":
        _show_batch_example()
        return

    filepath = None

    if source == "browse":
        filepath = select_file([".csv", ".json"])
    elif source == "path":
        rprint()
        path_input = Prompt.ask("[cyan]Enter file path[/cyan]")
        path = Path(path_input).expanduser().resolve()
        if path.is_file():
            filepath = str(path)
        else:
            rprint(f"[red]File not found: {path_input}[/red]")
            time.sleep(2)
            return

    if not filepath:
        rprint("[dim]No file selected. Returning to menu...[/dim]")
        time.sleep(1)
        return

    # Parse file
    rprint()
    rprint(f"[dim]Loading {filepath}...[/dim]")

    try:
        if filepath.endswith('.json'):
            with open(filepath) as f:
                articles = json.load(f)
                if not isinstance(articles, list):
                    articles = [articles]
        else:
            articles = parse_csv_file(filepath)
    except Exception as e:
        rprint(f"[red]Error reading file: {e}[/red]")
        time.sleep(2)
        return

    if not articles:
        rprint("[red]No valid articles found in file.[/red]")
        time.sleep(2)
        return

    # Show preview
    rprint()
    rprint(f"[green]Found {len(articles)} articles to generate[/green]")
    rprint()

    preview_table = Table(title="Article Preview (first 5)")
    preview_table.add_column("#", style="dim", width=4)
    preview_table.add_column("Topic", style="cyan")
    preview_table.add_column("Keywords", style="dim")
    preview_table.add_column("Language", width=8)

    for i, article in enumerate(articles[:5], 1):
        preview_table.add_row(
            str(i),
            (article.get('topic', '') or '')[:50],
            ", ".join(article.get('keywords', []))[:30] or "-",
            article.get('language', 'en').upper()
        )

    if len(articles) > 5:
        preview_table.add_row("...", f"[dim]and {len(articles) - 5} more[/dim]", "", "")

    rprint(preview_table)
    rprint()

    # Global settings
    rprint(Rule("[bold cyan]Batch Settings[/bold cyan]"))
    rprint()

    # Language override
    if Confirm.ask("Override language for all articles?", default=False):
        batch_language = select_language()
        for article in articles:
            article['language'] = batch_language

    # Output directory
    output_dir = Prompt.ask(
        "[cyan]Output directory[/cyan]",
        default=config.get("output_dir", "./batch-output")
    )

    # Output format
    output_format = show_menu("Output format for all articles?", OUTPUT_FORMATS, show_back=False)

    # Concurrency
    concurrency = IntPrompt.ask(
        "[cyan]Concurrent generations[/cyan]",
        default=3
    )

    # Confirm
    rprint()
    if Confirm.ask(f"[green]Generate {len(articles)} articles?[/green]", default=True):
        asyncio.run(_run_batch_generation(
            articles=articles,
            output_dir=output_dir,
            output_format=output_format,
            concurrency=concurrency,
            config=config
        ))
    else:
        rprint("[dim]Batch cancelled. Returning to menu...[/dim]")
        time.sleep(1)


def _interactive_quick_generate() -> None:
    """Quick generation with minimal options."""
    clear_screen()
    show_banner(mini=True)

    rprint(Panel(
        "[bold]Quick Generate[/bold]\n\n"
        "Generate an article with just a topic. We'll handle the rest!",
        border_style="cyan"
    ))
    rprint()

    topic = Prompt.ask("[cyan]📝 What do you want to write about?[/cyan]")

    if not topic:
        rprint("[dim]No topic provided. Returning to menu...[/dim]")
        time.sleep(1)
        return

    config = get_config()

    article_config = {
        'topic': topic,
        'language': 'en',
        'audience': 'general',
        'tone': 'professional',
        'word_count': 1500,
        'format': 'html',
        'output_dir': config.get("output_dir", "./output"),
    }

    rprint()
    rprint("[dim]Generating with default settings...[/dim]")
    rprint(f"[dim]Language: English | Length: ~1,500 words | Format: HTML[/dim]")
    rprint()

    asyncio.run(_generate_article(article_config, config))


def _interactive_config() -> None:
    """Interactive configuration management."""
    clear_screen()
    show_banner(mini=True)

    config = get_config()

    rprint(Panel("[bold]Configuration[/bold]", border_style="cyan"))
    rprint()

    config_table = Table(show_header=False, box=None, padding=(0, 2))
    config_table.add_column("Setting", style="dim")
    config_table.add_column("Value")
    config_table.add_column("Status")

    # API Key
    api_key = config.get("gemini_api_key")
    if api_key:
        masked = f"{api_key[:8]}...{api_key[-4:]}"
        config_table.add_row("Gemini API Key", masked, "[green]✓ Configured[/green]")
    else:
        config_table.add_row("Gemini API Key", "(not set)", "[red]✗ Required[/red]")

    config_table.add_row("API URL", config.get("api_url", ""), "[green]✓[/green]")
    config_table.add_row("Output Directory", config.get("output_dir", ""), "[green]✓[/green]")

    rprint(config_table)
    rprint()

    rprint(Rule("Environment Variables"))
    rprint()
    rprint("[dim]Add these to your shell profile (~/.zshrc or ~/.bashrc):[/dim]")
    rprint()
    rprint("""[cyan]
export GEMINI_API_KEY="your-api-key-here"
export OPENBLOG_API_URL="http://localhost:8000"
export OPENBLOG_OUTPUT_DIR="./output"
[/cyan]""")

    rprint()
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def _show_help() -> None:
    """Show help and examples."""
    clear_screen()
    show_banner(mini=True)

    help_md = """
## Getting Started

OpenBlog generates high-quality, SEO-optimized blog articles using AI.

### Quick Start

1. **Set your API key:**
   ```
   export GEMINI_API_KEY="your-key"
   ```

2. **Run interactive mode:**
   ```
   openblog interactive
   ```

3. **Or quick generate:**
   ```
   openblog generate "Your Topic Here"
   ```

### Commands

| Command | Description |
|---------|-------------|
| `openblog interactive` | Guided interactive mode |
| `openblog generate "Topic"` | Generate single article |
| `openblog batch file.csv` | Batch generate |
| `openblog config` | View configuration |
| `openblog health` | Check API status |

### Tips

- **Be specific** with topics: "10 React Performance Tips for 2024" > "React tips"
- **Add keywords** to improve SEO targeting
- **Include company URL** for brand-aligned content
- **Use batch mode** for content calendars

### CSV Format for Batch

```csv
topic,keywords,language,word_count
"Article Title","keyword1,keyword2",en,2000
```
"""

    rprint(Panel(Markdown(help_md), title="[bold]Help & Examples[/bold]", border_style="cyan"))
    rprint()
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def _show_batch_example() -> None:
    """Show batch file format examples."""
    clear_screen()
    show_banner(mini=True)

    rprint(Panel("[bold]Batch File Format Examples[/bold]", border_style="cyan"))
    rprint()

    rprint("[bold]CSV Format:[/bold]")
    rprint()
    csv_example = '''topic,keywords,company_url,language,word_count,audience
"10 Tips for Better Sleep","sleep,health,wellness",https://example.com,en,2000,general
"Remote Work Best Practices","remote work,productivity",https://example.com,en,1500,business
"Introduction to Machine Learning","AI,ML,beginner guide",,en,2500,technical'''

    rprint(Syntax(csv_example, "csv", theme="monokai"))
    rprint()

    rprint("[bold]JSON Format:[/bold]")
    rprint()
    json_example = '''[
  {
    "topic": "10 Tips for Better Sleep",
    "keywords": ["sleep", "health", "wellness"],
    "company_url": "https://example.com",
    "language": "en",
    "word_count": 2000
  },
  {
    "topic": "Remote Work Best Practices",
    "keywords": ["remote work", "productivity"],
    "language": "en"
  }
]'''

    rprint(Syntax(json_example, "json", theme="monokai"))
    rprint()

    rprint("[bold]Column Reference:[/bold]")
    rprint()

    col_table = Table()
    col_table.add_column("Column", style="cyan")
    col_table.add_column("Required", style="yellow")
    col_table.add_column("Description")

    col_table.add_row("topic", "Yes", "Article title or topic")
    col_table.add_row("keywords", "No", "Comma-separated SEO keywords")
    col_table.add_row("company_url", "No", "Company website for context")
    col_table.add_row("language", "No", "2-letter code (en, es, fr, etc.)")
    col_table.add_row("word_count", "No", "Target length (default: 2000)")
    col_table.add_row("audience", "No", "general, business, technical, academic")

    rprint(col_table)
    rprint()
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


# ============================================================================
# GENERATION LOGIC
# ============================================================================

async def _generate_article(article_config: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Generate a single article with progress display."""

    stages = [
        ("research", "🔍 Researching topic", "Gathering sources and information"),
        ("outline", "📋 Creating outline", "Structuring the article"),
        ("draft", "✍️  Writing content", "Generating initial draft"),
        ("enhance", "✨ Enhancing", "Optimizing for SEO and readability"),
        ("citations", "📚 Adding citations", "Inserting references"),
        ("quality", "✅ Quality check", "Running quality analysis"),
        ("format", "📄 Formatting", "Generating final output"),
    ]

    output_dir = Path(article_config['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    rprint()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="cyan", finished_style="green"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        expand=True,
    ) as progress:
        main_task = progress.add_task(
            "[bold cyan]Generating article...",
            total=len(stages)
        )

        try:
            # Try local generation first
            if config.get("gemini_api_key"):
                result = await _generate_local(article_config, config, progress, main_task, stages)
            else:
                result = await _generate_via_api(article_config, config, progress, main_task, stages)

        except Exception as e:
            rprint(f"\n[red]Error during generation:[/red] {e}")
            return

    elapsed = time.time() - start_time

    # Save output
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in article_config['topic'])
    safe_name = safe_name.replace(" ", "-").lower()[:50]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    fmt = article_config.get('format', 'html')
    if fmt == "html":
        filename = f"{safe_name}-{timestamp}.html"
        content = result.get("html", result.get("content", ""))
    elif fmt == "markdown":
        filename = f"{safe_name}-{timestamp}.md"
        content = result.get("markdown", result.get("content", ""))
    else:
        filename = f"{safe_name}-{timestamp}.json"
        content = json.dumps(result, indent=2)

    output_path = output_dir / filename
    output_path.write_text(content, encoding='utf-8')

    # Show success
    rprint()
    rprint(Panel(
        f"[bold green]✓ Article Generated Successfully![/bold green]\n\n"
        f"[dim]Title:[/dim] {result.get('title', article_config['topic'])}\n"
        f"[dim]Words:[/dim] {len(content.split()):,}\n"
        f"[dim]Time:[/dim] {elapsed:.1f}s\n"
        f"[dim]File:[/dim] [cyan]{output_path}[/cyan]",
        border_style="green"
    ))
    rprint()

    # Preview option
    if Confirm.ask("Preview the article?", default=False):
        rprint()
        if fmt == "markdown":
            rprint(Panel(Markdown(content[:2000] + "..." if len(content) > 2000 else content)))
        else:
            # Show first 1000 chars for HTML/JSON
            rprint(Panel(content[:1000] + "..." if len(content) > 1000 else content))

    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


async def _generate_local(
    article_config: Dict[str, Any],
    config: Dict[str, Any],
    progress: Progress,
    main_task,
    stages: List[tuple]
) -> Dict[str, Any]:
    """Generate article locally using pipeline."""

    try:
        from pipeline.core import WorkflowEngine
        from pipeline.config import PipelineConfig, ArticleRequest
    except ImportError:
        # Fall back to API
        return await _generate_via_api(article_config, config, progress, main_task, stages)

    # Create request
    request = ArticleRequest(
        title=article_config['topic'],
        target_keywords=article_config.get('keywords', [article_config['topic'].split()[0]]),
        company_url=article_config.get('company_url'),
        audience_level=article_config.get('audience', 'general'),
        target_word_count=article_config.get('word_count', 2000),
        language=article_config.get('language', 'en'),
    )

    engine = WorkflowEngine(api_key=config["gemini_api_key"])

    # Simulate progress through stages
    for i, (stage_id, stage_name, stage_desc) in enumerate(stages):
        progress.update(main_task, description=f"{stage_name}")
        await asyncio.sleep(0.5)  # Small delay for visual feedback
        progress.advance(main_task)

    # Actually run the generation
    result = await engine.generate_article(request)

    return result


async def _generate_via_api(
    article_config: Dict[str, Any],
    config: Dict[str, Any],
    progress: Progress,
    main_task,
    stages: List[tuple]
) -> Dict[str, Any]:
    """Generate article via API."""
    import httpx

    api_url = config.get("api_url", "http://localhost:8000")

    payload = {
        "title": article_config['topic'],
        "target_keywords": article_config.get('keywords', []),
        "audience_level": article_config.get('audience', 'general'),
        "target_word_count": article_config.get('word_count', 2000),
        "language": article_config.get('language', 'en'),
    }

    if article_config.get('company_url'):
        payload['company_url'] = article_config['company_url']

    async with httpx.AsyncClient(timeout=600.0) as client:
        # Submit job
        progress.update(main_task, description="[cyan]Submitting job...")

        response = await client.post(f"{api_url}/write-async", json=payload)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get("job_id")

        if not job_id:
            raise Exception("No job ID returned from API")

        # Poll for completion
        while True:
            await asyncio.sleep(3)

            status_response = await client.get(f"{api_url}/jobs/{job_id}")
            status_response.raise_for_status()
            status_data = status_response.json()

            status = status_data.get("status")
            stage = status_data.get("current_stage", "Processing")
            pct = status_data.get("progress", 0)

            progress.update(main_task, description=f"[cyan]{stage}[/cyan]")
            progress.update(main_task, completed=int(pct * len(stages) / 100))

            if status == "completed":
                progress.update(main_task, completed=len(stages))
                return status_data.get("result", {})
            elif status in ("failed", "error", "timeout"):
                raise Exception(status_data.get("error", f"Job {status}"))


async def _run_batch_generation(
    articles: List[Dict[str, Any]],
    output_dir: str,
    output_format: str,
    concurrency: int,
    config: Dict[str, Any]
) -> None:
    """Run batch generation with progress tracking."""
    import httpx
    from asyncio import Semaphore

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    sem = Semaphore(concurrency)
    results = []
    api_url = config.get("api_url", "http://localhost:8000")

    rprint()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="cyan", finished_style="green"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        expand=True,
    ) as progress:
        main_task = progress.add_task(
            "[bold cyan]Generating articles...",
            total=len(articles)
        )

        async def process_one(idx: int, article: Dict[str, Any]) -> Dict[str, Any]:
            async with sem:
                topic = article.get('topic', f'Article {idx + 1}')
                short_topic = topic[:30] + "..." if len(topic) > 30 else topic

                try:
                    async with httpx.AsyncClient(timeout=600.0) as client:
                        payload = {
                            "title": topic,
                            "target_keywords": article.get('keywords', []),
                            "language": article.get('language', 'en'),
                            "target_word_count": article.get('word_count', 2000),
                        }
                        if article.get('company_url'):
                            payload['company_url'] = article['company_url']

                        response = await client.post(f"{api_url}/write", json=payload)
                        response.raise_for_status()
                        result = response.json()

                        # Save file
                        safe_name = "".join(
                            c if c.isalnum() or c in " -_" else ""
                            for c in topic
                        ).replace(" ", "-").lower()[:40]

                        ext = {"html": "html", "markdown": "md", "json": "json"}[output_format]
                        filename = f"{idx+1:03d}-{safe_name}.{ext}"

                        if output_format == "json":
                            content = json.dumps(result, indent=2)
                        elif output_format == "markdown":
                            content = result.get("markdown", result.get("content", ""))
                        else:
                            content = result.get("html", result.get("content", ""))

                        (output_path / filename).write_text(content, encoding='utf-8')

                        progress.advance(main_task)
                        return {"topic": topic, "status": "success", "file": filename}

                except Exception as e:
                    progress.advance(main_task)
                    return {"topic": topic, "status": "failed", "error": str(e)}

        tasks = [process_one(i, article) for i, article in enumerate(articles)]
        results = await asyncio.gather(*tasks)

    # Show results
    rprint()

    success = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]

    rprint(Panel(
        f"[bold green]✓ Batch Complete![/bold green]\n\n"
        f"[green]Succeeded:[/green] {len(success)}\n"
        f"[red]Failed:[/red] {len(failed)}\n"
        f"[dim]Output:[/dim] [cyan]{output_dir}[/cyan]",
        border_style="green" if not failed else "yellow"
    ))

    if failed:
        rprint()
        rprint("[bold red]Failed Articles:[/bold red]")
        for r in failed:
            rprint(f"  • {r['topic'][:40]}: [dim]{r.get('error', 'Unknown error')}[/dim]")

    rprint()
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


# ============================================================================
# NON-INTERACTIVE COMMANDS
# ============================================================================

def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        show_banner()
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback,
        is_eager=True, help="Show version and exit"
    ),
) -> None:
    """
    OpenBlog - Generate high-quality, SEO-optimized blog articles using AI.

    Run 'openblog interactive' for the guided experience.
    """
    pass


@app.command()
def generate(
    topic: str = typer.Argument(..., help="The topic or title for the blog article"),
    company_url: str = typer.Option(None, "--company", "-c", help="Company website URL"),
    keywords: str = typer.Option(None, "--keywords", "-k", help="Comma-separated keywords"),
    language: str = typer.Option("en", "--language", "-l", help="Output language (en, es, fr, etc.)"),
    audience: str = typer.Option("general", "--audience", "-a", help="Target audience"),
    word_count: int = typer.Option(2000, "--words", "-w", help="Target word count"),
    output_format: str = typer.Option("html", "--format", "-f", help="Output format"),
    output_dir: str = typer.Option("./output", "--output", "-o", help="Output directory"),
) -> None:
    """Generate a blog article (non-interactive)."""
    show_banner(mini=True)

    config = get_config()

    article_config = {
        'topic': topic,
        'keywords': [k.strip() for k in keywords.split(",")] if keywords else [],
        'company_url': company_url,
        'language': language,
        'audience': audience,
        'word_count': word_count,
        'format': output_format,
        'output_dir': output_dir,
    }

    asyncio.run(_generate_article(article_config, config))


@app.command()
def batch(
    input_file: str = typer.Argument(..., help="CSV or JSON file with articles"),
    output_dir: str = typer.Option("./batch-output", "--output", "-o", help="Output directory"),
    output_format: str = typer.Option("html", "--format", "-f", help="Output format"),
    concurrency: int = typer.Option(3, "--concurrency", "-n", help="Concurrent generations"),
) -> None:
    """Batch generate articles from file (non-interactive)."""
    show_banner(mini=True)

    config = get_config()

    # Load file
    if input_file.endswith('.json'):
        with open(input_file) as f:
            articles = json.load(f)
    else:
        articles = parse_csv_file(input_file)

    rprint(f"[cyan]Found {len(articles)} articles[/cyan]")

    asyncio.run(_run_batch_generation(
        articles=articles,
        output_dir=output_dir,
        output_format=output_format,
        concurrency=concurrency,
        config=config
    ))


@app.command()
def config() -> None:
    """View current configuration."""
    show_banner(mini=True)
    _interactive_config()


@app.command()
def health(
    api_url: str = typer.Option(None, "--api", help="API URL to check"),
) -> None:
    """Check API health status."""
    import httpx

    cfg = get_config()
    target_api = api_url or cfg.get("api_url", "http://localhost:8000")

    rprint(f"[dim]Checking {target_api}...[/dim]")

    try:
        response = httpx.get(f"{target_api}/health", timeout=10.0)
        response.raise_for_status()
        data = response.json()

        rprint()
        rprint("[bold green]✓ API is healthy[/bold green]")
        rprint()

        for key, value in data.items():
            rprint(f"  [dim]{key}:[/dim] {value}")
        rprint()

    except Exception as e:
        rprint()
        rprint(f"[bold red]✗ API is unreachable[/bold red]")
        rprint(f"[dim]{e}[/dim]")
        raise typer.Exit(1)


# ============================================================================
# ENTRY POINT
# ============================================================================

def cli() -> None:
    """Main CLI entry point."""
    # If no args, launch interactive mode
    if len(sys.argv) == 1:
        sys.argv.append("interactive")
    app()


if __name__ == "__main__":
    cli()
