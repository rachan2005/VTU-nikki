"""CLI commands using Click"""
import click
import asyncio
from pathlib import Path
from datetime import date

from src.input import InputRouter, normalize_input_data
from src.date_management import DateManager
from src.ai.agent import DiaryGenerationAgent
from src.automation import ParallelSubmissionEngine
from src.db import init_db, get_db, SubmissionHistory
from src.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def cli():
    """VTU Diary Automation CLI"""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--dates', '-d', required=True, help='Date or range (YYYY-MM-DD or "YYYY-MM-DD to YYYY-MM-DD")')
@click.option('--skip-weekends/--no-skip-weekends', default=True, help='Skip weekends')
@click.option('--skip-holidays/--no-skip-holidays', default=True, help='Skip holidays')
@click.option('--dry-run', is_flag=True, help='Generate entries without submitting')
@click.option('--workers', '-w', default=5, help='Parallel submission workers')
@click.option('--confidence-threshold', '-c', default=0.75, type=float, help='Confidence threshold')
def submit(input_file, dates, skip_weekends, skip_holidays, dry_run, workers, confidence_threshold):
    """Submit diary entries from input file"""

    click.echo(f"🚀 VTU Diary Automation - Bulk Submit")
    click.echo(f"Input: {input_file}")
    click.echo(f"Dates: {dates}")
    click.echo(f"Workers: {workers}")
    click.echo("")

    try:
        # Process input
        click.echo("📥 Processing input...")
        router = InputRouter()
        input_data = router.process(input_file)
        normalized = normalize_input_data(input_data)
        click.echo(f"✓ Processed {len(normalized)} data chunks")

        # Parse dates
        click.echo("📅 Parsing dates...")
        date_manager = DateManager(skip_weekends=skip_weekends, skip_holidays=skip_holidays)
        target_dates = date_manager.parse_date_input(dates)
        click.echo(f"✓ Target dates: {len(target_dates)} days")

        # Generate entries
        click.echo("🤖 Generating diary entries with AI...")
        agent = DiaryGenerationAgent()

        if len(normalized) == 1:
            # Single input for all dates
            result = agent.generate_bulk(normalized[0]["raw_text"], target_dates)
        else:
            # Multiple inputs
            result = agent.generate_bulk(normalized, target_dates)

        click.echo(f"✓ Generated {len(result.entries)} entries")

        if result.warnings:
            click.echo(click.style(f"⚠ Warnings: {len(result.warnings)}", fg='yellow'))
            for w in result.warnings[:3]:
                click.echo(f"  - {w}")

        # Filter by confidence
        filtered = agent.filter_by_confidence(result, threshold=confidence_threshold)
        auto_submit = filtered["auto_submit"]
        needs_review = filtered["manual_review"]

        click.echo(f"✓ High confidence: {len(auto_submit)}")
        if needs_review:
            click.echo(click.style(f"⚠ Need review: {len(needs_review)}", fg='yellow'))

        if dry_run:
            click.echo("\n📋 DRY RUN - Generated entries (not submitted):")
            for entry in auto_submit[:5]:
                click.echo(f"\n  {entry.date} ({entry.hours}h):")
                click.echo(f"    {entry.activities[:80]}...")
                click.echo(f"    Skills: {', '.join(entry.skills)}")

            if len(auto_submit) > 5:
                click.echo(f"\n  ... and {len(auto_submit) - 5} more entries")

            return

        # Submit
        if auto_submit:
            click.echo(f"\n🌐 Submitting {len(auto_submit)} entries...")

            # Convert to dict format
            entries_dict = [entry.dict() for entry in auto_submit]

            # Run async submission
            engine = ParallelSubmissionEngine(max_workers=workers)
            results = asyncio.run(engine.submit_bulk(entries_dict))

            # Count success/fail
            success_count = sum(1 for r in results if r["status"] == "success")
            failed_count = len(results) - success_count

            click.echo(f"\n✅ Success: {success_count}")
            if failed_count > 0:
                click.echo(click.style(f"❌ Failed: {failed_count}", fg='red'))

            # Save to database
            db = get_db()
            for entry, result in zip(auto_submit, results):
                SubmissionHistory.create(
                    db,
                    date=entry.date,
                    hours=entry.hours,
                    activities=entry.activities,
                    learnings=entry.learnings,
                    blockers=entry.blockers,
                    links=entry.links,
                    skills=entry.skills,
                    status=result["status"],
                    confidence_score=entry.confidence
                )

            click.echo("✓ Saved to database")

    except Exception as e:
        click.echo(click.style(f"\n❌ Error: {e}", fg='red'))
        logger.exception("CLI submission failed")
        raise click.Abort()


@cli.command()
@click.option('--month', '-m', help='Month in YYYY-MM format')
@click.option('--status', '-s', help='Filter by status (success/failed)')
def history(month, status):
    """View submission history"""
    db = get_db()

    if month:
        year, mon = map(int, month.split('-'))
        entries = SubmissionHistory.get_month(db, year, mon)
        click.echo(f"\n📊 Submission History for {month}:")
    else:
        # Get all recent
        entries = db.query(SubmissionHistory).order_by(SubmissionHistory.submitted_at.desc()).limit(30).all()
        click.echo(f"\n📊 Recent Submissions:")

    if status:
        entries = [e for e in entries if e.status == status]

    click.echo("─" * 80)

    for entry in entries:
        status_icon = "✅" if entry.status == "success" else "❌"
        click.echo(
            f"{status_icon} {entry.date} | {entry.hours}h | "
            f"{', '.join(entry.skills[:3] if entry.skills else [])} | "
            f"Confidence: {entry.confidence_score:.2f}"
        )

    click.echo(f"\nTotal: {len(entries)} entries")


@cli.command()
def init():
    """Initialize database"""
    click.echo("Initializing database...")
    init_db()
    click.echo("✓ Database initialized")


if __name__ == '__main__':
    cli()
