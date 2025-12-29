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
@click.option(
    "--config",
    type=click.Path(exists=False, dir_okay=False),
    callback=load_config,
    is_eager=True,
    expose_value=False,
    help="Path to configuration file",
    default="",
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
@click.option("--alternate-api-key", envvar="LLM_ALTERNATE_API_KEY", help="Alternate LLM API Key")
@click.option("--alternate-api-base", envvar="LLM_ALTERNATE_API_BASE", help="Alternate LLM API Base URL")
@click.option("--alternate-model", envvar="LLM_ALTERNATE_MODEL", help="Alternate LLM Model")
@click.option("--verify-api-key", envvar="LLM_VERIFY_API_KEY", help="Verifier LLM API Key")
@click.option("--verify-api-base", envvar="LLM_VERIFY_API_BASE", help="Verifier LLM API Base URL")
@click.option("--verify-model", envvar="LLM_VERIFY_MODEL", help="Verifier LLM Model")
@click.option("--rate-limit-delay", default=0.0, help="Minimum seconds between API calls")
@click.option("--humanizer-jitter", default=0, help="Random jitter in milliseconds to add to delay")
@click.pass_context
def enrich_group(
    ctx: click.Context, 
    api_key: str | None, 
    api_base: str, 
    model: str, 
    timeout: float,
    alternate_api_key: str | None,
    alternate_api_base: str | None,
    alternate_model: str | None,
    verify_api_key: str | None,
    verify_api_base: str | None,
    verify_model: str | None,
    rate_limit_delay: float,
    humanizer_jitter: int,
) -> None:
    """Enrich catalog items using LLM."""
    ctx.obj["rate_limit_delay"] = rate_limit_delay
    ctx.obj["humanizer_jitter"] = humanizer_jitter
    
    # Debug config loading
    # logger.info(f"Rate limit: {rate_limit_delay}, Jitter: {humanizer_jitter}")
    
    if api_key:
        ctx.obj["llm"] = enrich.LLMClient(
            api_key=api_key, api_base=api_base, model=model, timeout=timeout
        )
        
    # Setup alternate client
    if alternate_model:
        ctx.obj["alternate_llm"] = enrich.LLMClient(
            api_key=alternate_api_key or api_key,
            api_base=alternate_api_base or api_base,
            model=alternate_model,
            timeout=timeout
        )
        
    # Setup verifier client
    if verify_model:
        ctx.obj["verifier_llm"] = enrich.LLMClient(
            api_key=verify_api_key or api_key,
            api_base=verify_api_base or api_base,
            model=verify_model,
            timeout=timeout
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
@click.option("--unenriched-only", is_flag=True, default=True, help="Only enrich unenriched items")
@click.option("--concurrency", default=1, help="Number of concurrent workers")
@click.option("--batch-size", default=100, help="Batch size for DB commits")
@click.option("--enriched-only", is_flag=True, help="Only re-enrich items that already have descriptions")
@click.option("--verify-model", help="Model to use for verification pass (e.g. meta-llama/llama-3.3-70b-instruct:free)")
@click.pass_context
def enrich_sample_cmd(
    ctx: click.Context, count: int, dry_run: bool, tv_only: bool, movies_only: bool, unenriched_only: bool, concurrency: int, batch_size: int, enriched_only: bool, verify_model: str | None
) -> None:
    """Enrich a random sample of items."""
    llm = _require_llm(ctx)
    
    # Setup verifier client if model provided
    verifier_client = None
    if verify_model:
        verifier_client = enrich.LLMClient(
            api_key=llm.api_key, 
            api_base=llm.api_base, 
            model=verify_model, 
            timeout=llm.timeout
        )
    elif "verifier_llm" in ctx.obj:
        verifier_client = ctx.obj["verifier_llm"]

    # Setup alternate client
    alternate_client = ctx.obj.get("alternate_llm")

    # If enriched_only is True, we must ensure unenriched_only is False so the logic in enrich_sample works
    if enriched_only:
        unenriched_only = False

    # Apply global rate limit settings if available and not overridden
    # Note: enrich_sample doesn't accept delay/jitter arguments directly, so we use ctx settings
    delay = ctx.obj.get("rate_limit_delay", 0.0)
    jitter = ctx.obj.get("humanizer_jitter", 0)
        
    asyncio.run(
        enrich.enrich_sample(
            ctx.obj["db"],
            count,
            llm,
            dry_run=dry_run,
            tv_only=tv_only,
            movies_only=movies_only,
            unenriched_only=unenriched_only,
            concurrency=concurrency,
            batch_size=batch_size,
            enriched_only=enriched_only,
            verifier_client=verifier_client,
            alternate_client=alternate_client,
            delay=delay,
            jitter=jitter
        )
    )


@enrich_group.command(name="batch")
@click.option("--tv-only", is_flag=True, help="Only enrich TV shows")
@click.option("--movies-only", is_flag=True, help="Only enrich movies")
@click.option("--limit", type=int, help="Maximum items to process")
@click.option("--delay", type=float, help="Delay between API calls (overrides config)")
@click.option("--concurrency", default=1, help="Number of concurrent workers")
@click.option("--dry-run", is_flag=True, help="Don't save changes to DB")
@click.option("--force-all", is_flag=True, help="Re-process ALL items (ignore enriched status)")
@click.option("--raw-output", is_flag=True, help="Disable human-readable output formatting")
@click.option("--random-order", is_flag=True, help="Process items in random order")
@click.option("--verify", is_flag=True, help="Enable 2-pass verification (double checks facts with LLM)")
@click.option("--batch-size", default=100, help="Batch size for DB commits")
@click.option("--verify-model", help="Model to use for verification pass")
@click.pass_context
def enrich_batch_cmd(
    ctx: click.Context,
    tv_only: bool,
    movies_only: bool,
    limit: int | None,
    delay: float | None,
    concurrency: int,
    dry_run: bool,
    force_all: bool,
    raw_output: bool,
    random_order: bool,
    verify: bool,
    batch_size: int,
    verify_model: str | None,
) -> None:
    """Batch enrich catalog items."""
    llm = _require_llm(ctx)
    
    # Resolve delay and jitter from config/context if not provided
    if delay is None:
        delay = ctx.obj.get("rate_limit_delay", 0.5)
        
    jitter = ctx.obj.get("humanizer_jitter", 0)

    
    # Setup verifier client if model provided
    verifier_client = None
    if verify_model:
        verifier_client = enrich.LLMClient(
            api_key=llm.api_key, 
            api_base=llm.api_base, 
            model=verify_model, 
            timeout=llm.timeout
        )
        verify = True # Auto-enable verify flag
    elif "verifier_llm" in ctx.obj:
        verifier_client = ctx.obj["verifier_llm"]
        if verify_model is None: # Only enable verify if not explicitly controlled (though verify arg is passed)
             # Wait, verify flag is separate. If user didn't pass --verify, but configured a verifier, should we auto-enable?
             # For 'batch' command, there is a --verify flag.
             # If user has a configured verifier in config, they probably want to use it IF they pass --verify.
             # But if they pass --verify-model, we force verify=True.
             pass

    # Setup alternate client
    alternate_client = ctx.obj.get("alternate_llm")

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
            random_order=random_order,
            verify=verify,
            batch_size=batch_size,
            verifier_client=verifier_client,
            alternate_client=alternate_client,
            jitter=jitter
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
    default="",
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
@click.option("--timeout", default=240.0, help="LLM request timeout in seconds", show_default=True)
@click.option("--tv-only", is_flag=True, help="Only enrich TV shows")
@click.option("--movies-only", is_flag=True, help="Only enrich movies")
@click.option("--limit", type=int, help="Maximum items to process")
@click.option("--delay", type=float, help="Delay between API calls (overrides config)")
@click.option("--rate-limit-delay", default=0.0, help="Minimum seconds between API calls")
@click.option("--humanizer-jitter", default=0, help="Random jitter in milliseconds to add to delay")
@click.option("--concurrency", default=1, help="Number of concurrent workers")
@click.option("--dry-run", is_flag=True, help="Don't save changes to DB")
@click.option("--force-all", is_flag=True, help="Re-process ALL items (ignore enriched status)")
@click.option("--raw-output", is_flag=True, help="Disable human-readable output formatting")
@click.option("--random-dry-run", is_flag=True, help="Process items in random order (implies --dry-run)")
@click.option("--verify", is_flag=True, help="Enable 2-pass verification (double checks facts with LLM)")
@click.pass_context
def enrich_batch_standalone(
    ctx: click.Context,
    db: Path,
    api_key: str | None,
    api_base: str,
    model: str,
    timeout: float,
    tv_only: bool,
    movies_only: bool,
    limit: int | None,
    delay: float | None,
    rate_limit_delay: float,
    humanizer_jitter: int,
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

    # Resolve delay
    if delay is None:
        delay = rate_limit_delay
        if delay == 0.0:
            delay = 0.5  # Default if nothing configured

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
            jitter=humanizer_jitter,
        )
    )


@click.command(name="ingest-standalone")
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
def ingest_standalone(db: Path, base_url: str, timeout: float, concurrency: int) -> None:
    """Standalone command for catalog ingestion."""
    asyncio.run(
        ingest.ingest_catalog(base_url, str(db), timeout, concurrency)
    )




if __name__ == "__main__":
    cli()
