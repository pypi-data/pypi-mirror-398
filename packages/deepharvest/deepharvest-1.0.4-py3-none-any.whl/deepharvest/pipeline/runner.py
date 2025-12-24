"""
Pipeline Runner for YAML Pipeline Execution
"""

import yaml
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from ..core.crawler import DeepHarvest, CrawlConfig
from ..browser import BrowserScraper
from ..utils.errors import DeepharvestError

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Execute YAML pipeline definitions"""

    def __init__(self, pipeline_file: str):
        self.pipeline_file = Path(pipeline_file)
        if not self.pipeline_file.exists():
            raise DeepharvestError(f"Pipeline file not found: {pipeline_file}")

        self.pipeline = self._load_pipeline()
        self.results: Dict[str, Any] = {}

    def _load_pipeline(self) -> Dict:
        """Load pipeline from YAML file"""
        with open(self.pipeline_file) as f:
            return yaml.safe_load(f)

    async def run(self):
        """Execute the pipeline"""
        logger.info(f"Running pipeline: {self.pipeline_file}")

        # Get pipeline steps
        steps = self.pipeline.get("steps", [])
        execution_mode = self.pipeline.get("execution", "sequential")  # sequential or parallel

        if execution_mode == "parallel":
            await self._run_parallel(steps)
        else:
            await self._run_sequential(steps)

        # Export results
        output = self.pipeline.get("output", {})
        if output:
            await self._export_results(output)

    async def _run_sequential(self, steps: List[Dict]):
        """Run steps sequentially"""
        for step in steps:
            await self._execute_step(step)

    async def _run_parallel(self, steps: List[Dict]):
        """Run steps in parallel"""
        tasks = [self._execute_step(step) for step in steps]
        await asyncio.gather(*tasks)

    async def _execute_step(self, step: Dict):
        """Execute a single pipeline step"""
        step_type = step.get("type")
        step_name = step.get("name", "unnamed")

        logger.info(f"Executing step: {step_name} ({step_type})")

        try:
            if step_type == "crawl":
                await self._step_crawl(step)
            elif step_type == "fetch":
                await self._step_fetch(step)
            elif step_type == "extract":
                await self._step_extract(step)
            elif step_type == "transform":
                await self._step_transform(step)
            else:
                logger.warning(f"Unknown step type: {step_type}")
        except Exception as e:
            logger.error(f"Step {step_name} failed: {e}")
            if step.get("retry", {}).get("enabled", False):
                await self._retry_step(step)
            else:
                raise

    async def _step_crawl(self, step: Dict):
        """Execute crawl step"""
        urls = step.get("urls", [])
        config_data = step.get("config", {})

        config = CrawlConfig(seed_urls=urls, **config_data)

        crawler = DeepHarvest(config)
        try:
            await crawler.initialize()
            await crawler.crawl()
            self.results[step.get("name")] = {
                "type": "crawl",
                "stats": {
                    "processed": crawler.stats.processed,
                    "success": crawler.stats.success,
                    "errors": crawler.stats.errors,
                },
            }
        finally:
            await crawler.shutdown()

    async def _step_fetch(self, step: Dict):
        """Execute fetch step"""
        urls = step.get("urls", [])
        use_js = step.get("use_js", True)

        config = CrawlConfig(seed_urls=urls)
        results = []

        async with BrowserScraper(config) as scraper:
            for url in urls:
                result = await scraper.fetch(url, use_js=use_js)
                results.append(
                    {
                        "url": url,
                        "status_code": result.status_code,
                        "html_length": len(result.html) if result.html else 0,
                    }
                )

        self.results[step.get("name")] = {"type": "fetch", "results": results}

    async def _step_extract(self, step: Dict):
        """Execute extract step"""
        # Extract step would use extractors
        logger.info("Extract step executed")
        self.results[step.get("name")] = {"type": "extract", "status": "completed"}

    async def _step_transform(self, step: Dict):
        """Execute transform step"""
        # Transform step would apply transformations
        logger.info("Transform step executed")
        self.results[step.get("name")] = {"type": "transform", "status": "completed"}

    async def _retry_step(self, step: Dict):
        """Retry a failed step"""
        retry_config = step.get("retry", {})
        max_retries = retry_config.get("max_retries", 3)
        delay = retry_config.get("delay", 1.0)

        for attempt in range(max_retries):
            try:
                await asyncio.sleep(delay)
                await self._execute_step(step)
                return
            except Exception as e:
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise

    async def _export_results(self, output: Dict):
        """Export pipeline results"""
        format_type = output.get("format", "json")
        path = output.get("path", "./pipeline_output.json")

        if format_type == "json":
            import json

            with open(path, "w") as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results exported to {path}")


async def run_pipeline(pipeline_file: str):
    """Run a pipeline from YAML file"""
    runner = PipelineRunner(pipeline_file)
    await runner.run()
