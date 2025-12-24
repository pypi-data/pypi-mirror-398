#!/usr/bin/env python3
"""
OpenBlog CLI - AI-Powered Blog Generation

A simple, powerful command-line tool for generating high-quality,
SEO-optimized blog articles using AI. No server needed.
"""

import sys

# Check Python version FIRST before any other imports
if sys.version_info < (3, 9):
    print()
    print("\033[31m")  # Red color
    print("  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("  ┃                                                                   ┃")
    print("  ┃   ██████╗ ██╗   ██╗████████╗██╗  ██╗ ██████╗ ███╗   ██╗           ┃")
    print("  ┃   ██╔══██╗╚██╗ ██╔╝╚══██╔══╝██║  ██║██╔═══██╗████╗  ██║           ┃")
    print("  ┃   ██████╔╝ ╚████╔╝    ██║   ███████║██║   ██║██╔██╗ ██║           ┃")
    print("  ┃   ██╔═══╝   ╚██╔╝     ██║   ██╔══██║██║   ██║██║╚██╗██║           ┃")
    print("  ┃   ██║        ██║      ██║   ██║  ██║╚██████╔╝██║ ╚████║           ┃")
    print("  ┃   ╚═╝        ╚═╝      ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝           ┃")
    print("  ┃                                                                   ┃")
    print("  ┃            ⚠️  VERSION ERROR - UPGRADE REQUIRED ⚠️                ┃")
    print("  ┃                                                                   ┃")
    print("  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
    print("\033[0m")  # Reset color
    print()
    print(f"  \033[33m►\033[0m  OpenBlog requires \033[1mPython 3.9+\033[0m")
    print(f"  \033[31m✗\033[0m  You have \033[1mPython {sys.version_info.major}.{sys.version_info.minor}\033[0m")
    print()
    print("  \033[36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("  \033[1m  QUICK FIX (copy & paste these commands):\033[0m")
    print("  \033[36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print()
    print("  \033[32m$\033[0m pip install --upgrade python")
    print()
    print("  \033[36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print()
    sys.exit(1)

import asyncio
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich.rule import Rule

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

LOGO = r"""
[bold cyan]
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║     ██████╗ ██████╗ ███████╗███╗   ██╗██████╗ ██╗      ██████╗   ║
    ║    ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║     ██╔════╝   ║
    ║    ██║   ██║██████╔╝█████╗  ██╔██╗ ██║██████╔╝██║     ██║  ███╗  ║
    ║    ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██╗██║     ██║   ██║  ║
    ║    ╚██████╔╝██║     ███████╗██║ ╚████║██████╔╝███████╗╚██████╔╝  ║
    ║     ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═════╝ ╚══════╝ ╚═════╝   ║
    ║                                                                   ║
    ║              [white]AI-Powered Blog Generation[/white]                        ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
[/bold cyan]
"""

LOGO_MINI = "[bold cyan]◆ OpenBlog[/bold cyan]"
TAGLINE = "[dim]━━━ AI-Powered Blog Generation ━━━[/dim]"

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG_DIR = Path.home() / ".openblog"
CONFIG_FILE = CONFIG_DIR / "config.json"
DOWNLOADS_DIR = Path.home() / "Downloads"


def get_config() -> dict:
    """Load configuration from config file."""
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config: dict) -> None:
    """Save configuration to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


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
# GEMINI API - DIRECT CALLS
# ============================================================================

BLOG_GENERATION_PROMPT = '''You are a professional blog writer and SEO expert. Generate a high-quality,
SEO-optimized blog article based on the following specifications.

Topic: {topic}
Keywords: {keywords}
Language: {language}
Target Audience: {audience}
Tone: {tone}
Target Word Count: {word_count}
{company_context}

Requirements:
1. Write engaging, informative content that provides real value
2. Use the target keywords naturally throughout the article
3. Include a compelling introduction that hooks the reader
4. Structure with clear headings and subheadings (H2, H3)
5. Include practical examples, tips, or actionable advice
6. End with a strong conclusion and call-to-action
7. Optimize for SEO while maintaining readability
8. Match the specified tone and audience level

Output the article in the following JSON format:
{{
  "title": "SEO-optimized title",
  "meta_description": "Compelling meta description under 160 chars",
  "html": "Full article in HTML with proper heading tags",
  "markdown": "Full article in Markdown format",
  "word_count": <actual word count>,
  "keywords_used": ["list", "of", "keywords", "used"],
  "reading_time_minutes": <estimated reading time>
}}

Generate the complete article now.'''


async def generate_blog_with_gemini(
    topic: str,
    keywords: List[str],
    language: str,
    audience: str,
    tone: str,
    word_count: int,
    company_context: str,
    api_key: str
) -> Dict[str, Any]:
    """Generate a blog article using Gemini API directly."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise Exception(
            "google-genai not installed.\n\n"
            "   Run: pip install google-genai"
        )

    # Create the client
    client = genai.Client(api_key=api_key)

    # Build the prompt
    company_section = f"Company Context: {company_context}" if company_context else ""

    prompt = BLOG_GENERATION_PROMPT.format(
        topic=topic,
        keywords=", ".join(keywords) if keywords else topic,
        language=language,
        audience=audience,
        tone=tone,
        word_count=word_count,
        company_context=company_section
    )

    # Generate content
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.0-flash-exp",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=8192,
            response_mime_type="application/json"
        )
    )

    # Parse response
    try:
        result = json.loads(response.text)
        # Handle if result is a list
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        return result
    except json.JSONDecodeError:
        # If not valid JSON, wrap the content
        return {
            "title": topic,
            "html": response.text,
            "markdown": response.text,
            "word_count": len(response.text.split()),
        }


# ============================================================================
# SUPPORTED OPTIONS
# ============================================================================

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
}

AUDIENCE_LEVELS = {
    "general": "General Audience",
    "business": "Business Professionals",
    "technical": "Technical Readers",
    "beginner": "Beginners",
}

CONTENT_TONES = {
    "professional": "Professional",
    "conversational": "Conversational",
    "educational": "Educational",
    "persuasive": "Persuasive",
}


# ============================================================================
# COMMANDS
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

    Get started:

        openblog config    Set up your Gemini API key
        openblog generate  Generate a blog article
    """
    pass


@app.command()
def config() -> None:
    """Configure your Gemini API key."""
    clear_screen()
    show_banner()

    rprint(Panel(
        "[bold]Configuration[/bold]\n\n"
        "OpenBlog uses Google's Gemini AI to generate blog articles.\n"
        "You need a free API key to get started.",
        border_style="cyan"
    ))
    rprint()

    current_config = get_config()

    # Show current status
    if current_config.get("gemini_key"):
        key = current_config["gemini_key"]
        masked = f"{key[:8]}...{key[-4:]}"
        rprint(f"[green]Current API key:[/green] {masked}")
        rprint()

        if not Confirm.ask("Update API key?", default=False):
            rprint("\n[dim]Configuration unchanged.[/dim]\n")
            return
        rprint()

    # Instructions
    rprint(Rule("[bold cyan]Get Your Free API Key[/bold cyan]"))
    rprint()
    rprint("[bold]1.[/bold] Visit: [cyan]https://aistudio.google.com/apikey[/cyan]")
    rprint("[bold]2.[/bold] Click 'Create API Key'")
    rprint("[bold]3.[/bold] Copy the key and paste below")
    rprint()

    # Get API key
    api_key = Prompt.ask("[cyan]Enter your Gemini API key[/cyan]")

    if not api_key or len(api_key) < 10:
        rprint("\n[red]Invalid API key. Please try again.[/red]\n")
        raise typer.Exit(1)

    # Save config
    current_config["gemini_key"] = api_key.strip()
    save_config(current_config)

    rprint()
    rprint(Panel(
        "[bold green]Configuration saved![/bold green]\n\n"
        f"Config file: [dim]{CONFIG_FILE}[/dim]\n\n"
        "You're ready to generate blog articles!\n\n"
        "[cyan]Try:[/cyan] openblog generate \"Your Topic Here\"",
        border_style="green"
    ))
    rprint()


@app.command()
def generate(
    topic: str = typer.Argument(..., help="The topic or title for the blog article"),
    keywords: Optional[str] = typer.Option(None, "--keywords", "-k", help="Comma-separated SEO keywords"),
    company_url: Optional[str] = typer.Option(None, "--company", "-c", help="Company website for context"),
    language: str = typer.Option("en", "--language", "-l", help="Output language code (en, es, fr, etc.)"),
    audience: str = typer.Option("general", "--audience", "-a", help="Target audience (general, business, technical, beginner)"),
    tone: str = typer.Option("professional", "--tone", "-t", help="Content tone (professional, conversational, educational, persuasive)"),
    word_count: int = typer.Option(1500, "--words", "-w", help="Target word count"),
    output_format: str = typer.Option("html", "--format", "-f", help="Output format (html, markdown, json)"),
) -> None:
    """Generate a blog article on any topic."""
    show_banner(mini=True)

    # Check config
    config_data = get_config()

    if not config_data.get("gemini_key"):
        rprint()
        rprint(Panel(
            "[bold red]No API key configured![/bold red]\n\n"
            "OpenBlog needs a Gemini API key to generate articles.\n\n"
            "[bold]Quick setup:[/bold]\n\n"
            "  [cyan]openblog config[/cyan]\n\n"
            "[bold]Get your free API key at:[/bold]\n\n"
            "  [cyan]https://aistudio.google.com/apikey[/cyan]",
            border_style="red",
            title="[bold]Configuration Required[/bold]"
        ))
        rprint()
        raise typer.Exit(1)

    # Parse keywords
    keyword_list = [k.strip() for k in keywords.split(",")] if keywords else []

    # Show what we're generating
    rprint()
    rprint(Panel(
        f"[bold]Topic:[/bold] {topic}\n"
        f"[dim]Keywords:[/dim] {', '.join(keyword_list) if keyword_list else '(auto)'}\n"
        f"[dim]Language:[/dim] {SUPPORTED_LANGUAGES.get(language, language)}\n"
        f"[dim]Audience:[/dim] {AUDIENCE_LEVELS.get(audience, audience)}\n"
        f"[dim]Tone:[/dim] {CONTENT_TONES.get(tone, tone)}\n"
        f"[dim]Length:[/dim] ~{word_count:,} words",
        title="[bold cyan]Generating Article[/bold cyan]",
        border_style="cyan"
    ))
    rprint()

    # Generate with progress
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="cyan", finished_style="green"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        expand=True,
    ) as progress:
        task = progress.add_task("[cyan]Generating article...", total=100)

        async def run_generation():
            progress.update(task, completed=10, description="[cyan]Connecting to Gemini...")

            try:
                # Fetch company context if URL provided
                company_context = ""
                if company_url:
                    progress.update(task, completed=20, description="[cyan]Analyzing company context...")
                    # For now, just pass the URL - Gemini will understand
                    company_context = f"Company website: {company_url}"

                progress.update(task, completed=30, description="[cyan]Generating content...")

                result = await generate_blog_with_gemini(
                    topic=topic,
                    keywords=keyword_list,
                    language=language,
                    audience=audience,
                    tone=tone,
                    word_count=word_count,
                    company_context=company_context,
                    api_key=config_data["gemini_key"]
                )

                progress.update(task, completed=90, description="[cyan]Saving files...")
                return result

            except Exception as e:
                raise e

        try:
            result = asyncio.run(run_generation())
            progress.update(task, completed=100, description="[green]Done!")
        except Exception as e:
            rprint(f"\n[red]Error:[/red] {e}")
            raise typer.Exit(1)

    elapsed = time.time() - start_time

    # Save to Downloads folder
    safe_topic = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)
    safe_topic = safe_topic.replace(" ", "-").lower()[:40]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_name = f"{safe_topic}-{timestamp}"

    # Determine content and extension
    if output_format == "markdown":
        content = result.get("markdown", result.get("html", ""))
        ext = "md"
    elif output_format == "json":
        content = json.dumps(result, indent=2)
        ext = "json"
    else:
        content = result.get("html", result.get("markdown", ""))
        ext = "html"

    # Save main file
    output_path = DOWNLOADS_DIR / f"{base_name}.{ext}"
    output_path.write_text(content, encoding='utf-8')

    # Also save JSON for reference
    json_path = DOWNLOADS_DIR / f"{base_name}.json"
    json_path.write_text(json.dumps(result, indent=2), encoding='utf-8')

    # Show success
    actual_words = result.get("word_count", len(content.split()))

    rprint()
    rprint(Panel(
        f"[bold green]Article Generated Successfully![/bold green]\n\n"
        f"[bold]Title:[/bold] {result.get('title', topic)}\n"
        f"[bold]Words:[/bold] {actual_words:,}\n"
        f"[bold]Time:[/bold] {elapsed:.1f}s\n\n"
        f"[bold]Saved to:[/bold]\n"
        f"  [cyan]{output_path}[/cyan]\n"
        f"  [cyan]{json_path}[/cyan]",
        border_style="green"
    ))
    rprint()

    # Preview option
    if Confirm.ask("Preview the article?", default=False):
        rprint()
        preview_content = result.get("markdown", result.get("html", ""))[:2000]
        if len(preview_content) < len(result.get("markdown", result.get("html", ""))):
            preview_content += "\n\n[dim]... (truncated)[/dim]"
        rprint(Panel(Markdown(preview_content), title="[bold]Preview[/bold]"))

    rprint()


@app.command()
def quick(
    topic: str = typer.Argument(..., help="What do you want to write about?"),
) -> None:
    """Generate an article with just a topic (quick mode)."""
    # Delegate to generate with defaults
    show_banner(mini=True)

    config_data = get_config()

    if not config_data.get("gemini_key"):
        rprint()
        rprint(Panel(
            "[bold red]No API key configured![/bold red]\n\n"
            "[cyan]openblog config[/cyan]  to set up your free Gemini API key",
            border_style="red"
        ))
        rprint()
        raise typer.Exit(1)

    rprint(f"\n[dim]Quick generating article about: {topic}[/dim]")
    rprint("[dim]Using defaults: English, 1500 words, Professional tone[/dim]\n")

    # Run generate with defaults
    ctx = typer.Context(app)
    generate(
        topic=topic,
        keywords=None,
        company_url=None,
        language="en",
        audience="general",
        tone="professional",
        word_count=1500,
        output_format="html"
    )


@app.command()
def batch(
    input_file: str = typer.Argument(..., help="CSV or JSON file with articles to generate"),
) -> None:
    """Generate multiple articles from a CSV or JSON file."""
    show_banner(mini=True)

    config_data = get_config()

    if not config_data.get("gemini_key"):
        rprint()
        rprint(Panel(
            "[bold red]No API key configured![/bold red]\n\n"
            "[cyan]openblog config[/cyan]  to set up your free Gemini API key",
            border_style="red"
        ))
        rprint()
        raise typer.Exit(1)

    # Load file
    input_path = Path(input_file)

    if not input_path.exists():
        rprint(f"\n[red]File not found:[/red] {input_file}\n")
        raise typer.Exit(1)

    # Parse articles
    articles = []

    if input_path.suffix.lower() == '.json':
        with open(input_path) as f:
            data = json.load(f)
            articles = data if isinstance(data, list) else [data]
    else:
        # CSV
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                article = {}
                for key in ['topic', 'title', 'subject']:
                    if key in row and row[key]:
                        article['topic'] = row[key].strip()
                        break
                for key in ['keywords', 'tags']:
                    if key in row and row[key]:
                        article['keywords'] = row[key].strip()
                        break
                for key in ['language', 'lang']:
                    if key in row and row[key]:
                        article['language'] = row[key].strip().lower()[:2]
                        break
                if article.get('topic'):
                    articles.append(article)

    if not articles:
        rprint("\n[red]No valid articles found in file.[/red]\n")
        raise typer.Exit(1)

    rprint()
    rprint(f"[cyan]Found {len(articles)} articles to generate[/cyan]")
    rprint()

    # Preview
    preview_table = Table(title="Articles to Generate")
    preview_table.add_column("#", style="dim", width=4)
    preview_table.add_column("Topic", style="cyan")
    preview_table.add_column("Keywords", style="dim")

    for i, article in enumerate(articles[:5], 1):
        preview_table.add_row(
            str(i),
            (article.get('topic', '') or '')[:50],
            (article.get('keywords', '') or '')[:30] or "-"
        )

    if len(articles) > 5:
        preview_table.add_row("...", f"[dim]and {len(articles) - 5} more[/dim]", "")

    rprint(preview_table)
    rprint()

    if not Confirm.ask(f"Generate {len(articles)} articles?", default=True):
        rprint("\n[dim]Cancelled.[/dim]\n")
        raise typer.Exit()

    # Generate each article
    rprint()

    success_count = 0
    failed_count = 0

    for i, article in enumerate(articles, 1):
        topic = article.get('topic', f'Article {i}')
        rprint(f"[cyan][{i}/{len(articles)}][/cyan] Generating: {topic[:50]}...")

        try:
            keyword_list = []
            if article.get('keywords'):
                keyword_list = [k.strip() for k in article['keywords'].split(",")]

            result = asyncio.run(generate_blog_with_gemini(
                topic=topic,
                keywords=keyword_list,
                language=article.get('language', 'en'),
                audience=article.get('audience', 'general'),
                tone=article.get('tone', 'professional'),
                word_count=article.get('word_count', 1500),
                company_context="",
                api_key=config_data["gemini_key"]
            ))

            # Save
            safe_topic = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)
            safe_topic = safe_topic.replace(" ", "-").lower()[:40]
            filename = f"{i:03d}-{safe_topic}.html"

            content = result.get("html", result.get("markdown", ""))
            (DOWNLOADS_DIR / filename).write_text(content, encoding='utf-8')

            rprint(f"  [green]Saved:[/green] {filename}")
            success_count += 1

        except Exception as e:
            rprint(f"  [red]Failed:[/red] {e}")
            failed_count += 1

    # Summary
    rprint()
    rprint(Panel(
        f"[bold]Batch Complete![/bold]\n\n"
        f"[green]Succeeded:[/green] {success_count}\n"
        f"[red]Failed:[/red] {failed_count}\n\n"
        f"[dim]Output:[/dim] [cyan]{DOWNLOADS_DIR}[/cyan]",
        border_style="green" if failed_count == 0 else "yellow"
    ))
    rprint()


@app.command()
def status() -> None:
    """Check your configuration status."""
    show_banner(mini=True)

    config_data = get_config()

    rprint()

    status_table = Table(title="Configuration Status", show_header=False)
    status_table.add_column("Setting", style="dim")
    status_table.add_column("Value")
    status_table.add_column("Status")

    # API Key
    api_key = config_data.get("gemini_key")
    if api_key:
        masked = f"{api_key[:8]}...{api_key[-4:]}"
        status_table.add_row("Gemini API Key", masked, "[green]Configured[/green]")
    else:
        status_table.add_row("Gemini API Key", "(not set)", "[red]Not configured[/red]")

    # Config file
    if CONFIG_FILE.exists():
        status_table.add_row("Config File", str(CONFIG_FILE), "[green]Exists[/green]")
    else:
        status_table.add_row("Config File", str(CONFIG_FILE), "[yellow]Not created[/yellow]")

    # Output directory
    status_table.add_row("Output Directory", str(DOWNLOADS_DIR), "[green]Ready[/green]")

    rprint(status_table)
    rprint()

    if not api_key:
        rprint("[yellow]Run 'openblog config' to set up your API key.[/yellow]")
        rprint()


# ============================================================================
# ENTRY POINT
# ============================================================================

def cli() -> None:
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    cli()
