import asyncio
import os
from pathlib import Path

import click

from kryten_playlist.catalog import enrich, ingest
from kryten_playlist.catalog.config import load_config


@click.group()
@click.option(
    "--db",
    default="data/catalog.db",
    help="Path to SQLite database",
    envvar="KRYTEN_DB_PATH",
    type=click.Path(path_type=Path),
)
@click.pass_context
def cli(ctx: click.Context, db: Path) -> None:
    """Kryten Catalog Management CLI."""
    ctx.ensure_object(dict)
    ctx.obj["db"] = str(db)


@cli.command(name="ingest")
@click.option(
    "--base-url",
    default="https://www.420grindhouse.com",
    help="MediaCMS Base URL",
    show_default=True,
)
@click.option("--timeout", default=30.0, help="Request timeout")
@click.option("--concurrency", default=24, help="Concurrency limit")
@click.pass_context
def ingest_cmd(
    ctx: click.Context, base_url: str, timeout: float, concurrency: int
) -> None:
    """Ingest catalog from MediaCMS."""
    asyncio.run(
        ingest.ingest_catalog(base_url, ctx.obj["db"], timeout, concurrency)
    )


@cli.group(name="enrich")
@click.option("--api-key", envvar="LLM_API_KEY", help="LLM API Key")
@click.option(
    "--api-base",
    envvar="LLM_API_BASE",
    default="https://api.openai.com/v1",
    help="LLM API Base URL",
    show_default=True,
)
@click.option(
    "--model",
    envvar="LLM_MODEL",
    default="gpt-4o-mini",
    help="LLM Model",
    show_default=True,
)
@click.option(
    "--timeout",
    default=240.0,
    help="LLM request timeout in seconds",
    show_default=True,
)
@click.pass_context
def enrich_group(
    ctx: click.Context, api_key: str | None, api_base: str, model: str, timeout: float
) -> None:
    """Enrich catalog items using LLM."""
    if api_key:
        ctx.obj["llm"] = enrich.LLMClient(
            api_key=api_key, api_base=api_base, model=model, timeout=timeout
        )


def _require_llm(ctx: click.Context) -> enrich.LLMClient:
    """Ensure LLM client is available."""
    if "llm" not in ctx.obj:
        click.echo("Error: LLM_API_KEY is required for this command.", err=True)
        ctx.exit(1)
    return ctx.obj["llm"]


@enrich_group.command(name="single")
@click.argument("query")
@click.option("--dry-run", is_flag=True, help="Don't save changes to DB")
@click.pass_context
def enrich_single_cmd(ctx: click.Context, query: str, dry_run: bool) -> None:
    """Enrich a single item by searching for it."""
    llm = _require_llm(ctx)
    asyncio.run(
        enrich.enrich_single(
            ctx.obj["db"], query, llm, dry_run=dry_run
        )
    )


@enrich_group.command(name="sample")
@click.option("--count", default=5, help="Number of items to sample")
@click.option("--dry-run", is_flag=True, help="Don't save changes to DB")
@click.option("--tv-only", is_flag=True, help="Only enrich TV shows")
@click.option("--movies-only", is_flag=True, help="Only enrich movies")
@click.option(
    "--all-items",
    is_flag=True,
    help="Sample from ALL items, not just unenriched ones",
)
@click.pass_context
def enrich_sample_cmd(
    ctx: click.Context,
    count: int,
    dry_run: bool,
    tv_only: bool,
    movies_only: bool,
    all_items: bool,
) -> None:
    """Enrich a random sample of items."""
    llm = _require_llm(ctx)
    asyncio.run(
        enrich.enrich_sample(
            ctx.obj["db"],
            count,
            llm,
            dry_run=dry_run,
            tv_only=tv_only,
            movies_only=movies_only,
            unenriched_only=not all_items,
        )
    )


@enrich_group.command(name="batch")
@click.option("--tv-only", is_flag=True, help="Only enrich TV shows")
@click.option("--movies-only", is_flag=True, help="Only enrich movies")
@click.option("--limit", type=int, help="Maximum items to process")
@click.option("--delay", default=0.5, help="Delay between API calls")
@click.option("--concurrency", default=1, help="Number of concurrent workers")
@click.option("--dry-run", is_flag=True, help="Don't save changes to DB")
@click.option("--force-all", is_flag=True, help="Re-process ALL items (ignore enriched status)")
@click.option("--raw-output", is_flag=True, help="Disable human-readable output formatting")
@click.option("--random-dry-run", is_flag=True, help="Process items in random order (implies --dry-run)")
@click.option("--verify", is_flag=True, help="Enable 2-pass verification (double checks facts with LLM)")
@click.pass_context
def enrich_batch_cmd(
    ctx: click.Context,
    tv_only: bool,
    movies_only: bool,
    limit: int | None,
    delay: float,
    concurrency: int,
    dry_run: bool,
    force_all: bool,
    raw_output: bool,
    random_dry_run: bool,
    verify: bool,
) -> None:
    """Enrich all unenriched items."""
    llm = _require_llm(ctx)
    
    if random_dry_run:
        dry_run = True

    asyncio.run(
        enrich.enrich_batch(
            ctx.obj["db"],
            llm,
            tv_only=tv_only,
            movies_only=movies_only,
            limit=limit,
            delay=delay,
            concurrency=concurrency,
            dry_run=dry_run,
            force_all=force_all,
            raw_output=raw_output,
            random_order=random_dry_run,
            verify=verify,
        )
    )


@click.command(name="enrich-batch-standalone")
@click.option(
    "--config",
    type=click.Path(exists=False, dir_okay=False),
    callback=load_config,
    is_eager=True,
    expose_value=False,
    help="Path to configuration file",
)
@click.option(
    "--db",
    default="data/catalog.db",
    help="Path to SQLite database",
    envvar="KRYTEN_DB_PATH",
    type=click.Path(path_type=Path),
)
@click.option("--api-key", envvar="LLM_API_KEY", help="LLM API Key")
@click.option(
    "--api-base",
    envvar="LLM_API_BASE",
    default="https://api.openai.com/v1",
    help="LLM API Base URL",
    show_default=True,
)
@click.option(
    "--model",
    envvar="LLM_MODEL",
    default="gpt-4o-mini",
    help="LLM Model",
    show_default=True,
)
@click.option(
    "--timeout",
    default=240.0,
    help="LLM request timeout in seconds",
    show_default=True,
)
@click.option("--tv-only", is_flag=True, help="Only enrich TV shows")
@click.option("--movies-only", is_flag=True, help="Only enrich movies")
@click.option("--limit", type=int, help="Maximum items to process")
@click.option("--delay", default=0.5, help="Delay between API calls")
@click.option("--concurrency", default=1, help="Number of concurrent workers")
@click.option("--dry-run", is_flag=True, help="Don't save changes to DB")
@click.option("--force-all", is_flag=True, help="Re-process ALL items (ignore enriched status)")
@click.option("--raw-output", is_flag=True, help="Disable human-readable output formatting")
@click.option("--random-dry-run", is_flag=True, help="Process items in random order (implies --dry-run)")
@click.option("--verify", is_flag=True, help="Enable 2-pass verification (double checks facts with LLM)")
def enrich_batch_standalone(
    db: Path,
    api_key: str | None,
    api_base: str,
    model: str,
    timeout: float,
    tv_only: bool,
    movies_only: bool,
    limit: int | None,
    delay: float,
    concurrency: int,
    dry_run: bool,
    force_all: bool,
    raw_output: bool,
    random_dry_run: bool,
    verify: bool,
) -> None:
    """Standalone command for batch enrichment."""
    if not api_key:
        click.echo("Error: LLM_API_KEY is required for this command.", err=True)
        raise click.Abort()

    llm = enrich.LLMClient(
        api_key=api_key, api_base=api_base, model=model, timeout=timeout
    )
    
    if random_dry_run:
        dry_run = True

    asyncio.run(
        enrich.enrich_batch(
            str(db),
            llm,
            tv_only=tv_only,
            movies_only=movies_only,
            limit=limit,
            delay=delay,
            concurrency=concurrency,
            dry_run=dry_run,
            force_all=force_all,
            raw_output=raw_output,
            random_order=random_dry_run,
            verify=verify,
        )
    )


@click.command(name="ingest-standalone")
@click.option(
    "--config",
    type=click.Path(exists=False, dir_okay=False),
    callback=load_config,
    is_eager=True,
    expose_value=False,
    help="Path to configuration file",
)
@click.option(
    "--db",
    default="data/catalog.db",
    help="Path to SQLite database",
    envvar="KRYTEN_DB_PATH",
    type=click.Path(path_type=Path),
)
@click.option(
    "--base-url",
    default="https://www.420grindhouse.com",
    help="MediaCMS Base URL",
    show_default=True,
)
@click.option("--timeout", default=30.0, help="Request timeout")
@click.option("--concurrency", default=24, help="Concurrency limit")
def ingest_standalone(
    db: Path, base_url: str, timeout: float, concurrency: int
) -> None:
    """Standalone command for catalog ingest."""
    asyncio.run(
        ingest.ingest_catalog(base_url, str(db), timeout, concurrency)
    )


@enrich_group.command(name="stats")
@click.pass_context
def enrich_stats_cmd(ctx: click.Context) -> None:
    """Show enrichment statistics."""
    asyncio.run(enrich.show_enriched_stats(ctx.obj["db"]))


@cli.command(name="stats")
@click.pass_context
def stats_cmd(ctx: click.Context) -> None:
    """Show general catalog statistics."""
    asyncio.run(ingest.show_stats(ctx.obj["db"]))


if __name__ == "__main__":
    cli()
