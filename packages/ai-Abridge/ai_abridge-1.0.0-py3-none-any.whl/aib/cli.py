"""AI Bridge CLI using Typer."""

from pathlib import Path
from typing import List, Optional

import typer

from .bridge import AIBridge
from .config import load_config

app = typer.Typer(
    name="ab",
    help="AI Bridge - A pure AI model bridge for multi-vendor LLM calls.",
    add_completion=False,
)


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="Prompt text to send to the AI model"),
    vendor: Optional[str] = typer.Option(
        None, "-v", "--vendor",
        help="Vendor name (gemini, kimi, qwen, openai)"
    ),
    model: Optional[str] = typer.Option(
        None, "-m", "--model",
        help="Model name"
    ),
    api_key: Optional[str] = typer.Option(
        None, "-k", "--api-key",
        help="API key (overrides config/env)"
    ),
    base_url: Optional[str] = typer.Option(
        None, "-u", "--base-url",
        help="Custom API endpoint (for relays/proxies)"
    ),
    timeout: Optional[float] = typer.Option(
        None, "--timeout",
        help="Request timeout in seconds"
    ),
    files: Optional[List[Path]] = typer.Option(
        None, "-f", "--file",
        help="File(s) to include (can specify multiple times)"
    ),
    config_path: Optional[Path] = typer.Option(
        None, "-c", "--config",
        help="Path to config file"
    ),
    temperature: Optional[float] = typer.Option(
        None, "-t", "--temperature",
        help="Sampling temperature (uses API default if not specified)"
    ),
    max_tokens: Optional[int] = typer.Option(
        None, "--max-tokens",
        help="Maximum tokens in response"
    ),
    show_usage: bool = typer.Option(
        False, "--usage",
        help="Show token usage after response"
    ),
):
    """
    Send a chat request to an AI model.
    
    Examples:
    
        ab chat "Hello, who are you?" -v gemini
        
        ab chat "Summarize this document" -v kimi -f doc.pdf
        
        ab chat "Analyze these images" -v openai -f img1.png -f img2.jpg
    """
    try:
        # Build AIBridge
        bridge = AIBridge(
            vendor=vendor,
            api_key=api_key,
            model=model,
            base_url=base_url,
            timeout=timeout,
            config_path=str(config_path) if config_path else None,
        )
        
        # Display info
        typer.echo(f"🤖 {bridge.vendor} | {bridge.model}", err=True)
        
        # Build kwargs - only include if specified
        kwargs = {}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        
        # Send request
        response = bridge.chat(
            prompt=prompt,
            files=files,
            **kwargs
        )
        
        # Output raw content
        typer.echo(response.content)
        
        # Show usage if requested
        if show_usage:
            u = response.usage
            typer.echo(
                f"\n📊 Tokens: {u.prompt_tokens} in / {u.completion_tokens} out / {u.total_tokens} total",
                err=True
            )
    
    except FileNotFoundError as e:
        typer.echo(f"❌ File error: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def config(
    path: Optional[Path] = typer.Option(
        None, "-p", "--path",
        help="Path to config file to check"
    ),
):
    """
    Show current configuration.
    """
    cfg = load_config(str(path) if path else None)
    
    typer.echo("📋 Current Configuration:")
    typer.echo(f"   Default vendor: {cfg.get('default_vendor', 'not set')}")
    typer.echo("")
    
    vendors = cfg.get("vendors", {})
    if not vendors:
        typer.echo("   No vendors configured.")
        typer.echo("")
        typer.echo("💡 Set up via:")
        typer.echo("   - Config file: ~/.aib/config.yaml")
        typer.echo("   - Environment: AIB_GEMINI_API_KEY, AIB_KIMI_API_KEY, etc.")
    else:
        for vendor, vcfg in vendors.items():
            api_key = vcfg.get("api_key", "")
            masked_key = f"{api_key[:8]}..." if api_key and len(api_key) > 8 else "(not set)"
            model = vcfg.get("model", "(default)")
            base_url = vcfg.get("base_url", "(official)")
            
            typer.echo(f"   [{vendor}]")
            typer.echo(f"      API Key: {masked_key}")
            typer.echo(f"      Model:   {model}")
            typer.echo(f"      URL:     {base_url}")


@app.command()
def version():
    """Show version information."""
    from . import __version__
    typer.echo(f"AI Bridge v{__version__}")


if __name__ == "__main__":
    app()
