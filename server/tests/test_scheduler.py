"""
Integration tests for the APScheduler job scheduling.

Tests validate that:
- Scheduler correctly registers the weekly scraper job
- Cron expression matches the spec (Sunday 3 AM UTC)
"""

from unittest.mock import AsyncMock, patch
import pytest
from apscheduler.triggers.cron import CronTrigger


@pytest.mark.asyncio
async def test_scheduler_registers_weekly_job_with_correct_cron():
    """
    Verify that the scheduler registers a job with the correct cron timing.
    
    Expected: Job runs weekly on Sunday at 3 AM UTC.
    Spec from project README: "Weekly Sundays 3AM"
    """
    from app.data.scheduler import scheduler, start_scheduler, stop_scheduler
    
    # Ensure a clean scheduler state
    if scheduler.running:
        stop_scheduler()
    scheduler.remove_all_jobs()
    
    # Register job via production entrypoint
    start_scheduler()
    job = scheduler.get_job("weekly_scrape")
    
    # Assert: Job was added to the scheduler
    assert job is not None, "Job should be added successfully"
    assert job.id == "weekly_scrape", "Job ID should match"
    
    # Assert: Job has correct trigger
    assert isinstance(job.trigger, CronTrigger), "Job should use CronTrigger"
    trigger_text = str(job.trigger)
    assert "day_of_week='sun'" in trigger_text
    assert "hour='3'" in trigger_text
    assert "minute='0'" in trigger_text

    stop_scheduler()


@pytest.mark.asyncio
async def test_scheduler_job_calls_scraper_and_retrain():
    """
    Verify that the weekly job invokes the scraper and model retraining.
    
    Note: This test mocks the actual scraper and trainer to avoid hitting real APIs.
    """
    from app.data.scheduler import weekly_scrape_and_retrain
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Create a mock database session
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Patch the dependencies that weekly_scrape_and_retrain uses
    with patch("app.data.scheduler.async_session") as mock_session_maker:
        with patch("app.data.scraper.DeckScraper") as mock_scraper_class:
            with patch("app.services.cr_api.CRApiClient") as mock_api_class:
                with patch("app.ml.trainer.retrain_model", new_callable=AsyncMock) as mock_retrain:
                    # Setup mocks
                    mock_session_maker.return_value.__aenter__.return_value = mock_db
                    mock_scraper_instance = AsyncMock()
                    mock_scraper_class.return_value = mock_scraper_instance
                    mock_scraper_instance.scrape_top_ladder.return_value = 5
                    mock_scraper_instance.compute_synergies.return_value = 20
                    mock_api_instance = AsyncMock()
                    mock_api_class.return_value = mock_api_instance

                    # Act: Call the weekly job function
                    await weekly_scrape_and_retrain()

                    # Assert: Scraper methods were called
                    mock_scraper_instance.scrape_top_ladder.assert_called_once_with(max_players=50)
                    mock_scraper_instance.compute_synergies.assert_called_once()
                    mock_retrain.assert_called_once()
                    mock_api_instance.close.assert_called_once()
