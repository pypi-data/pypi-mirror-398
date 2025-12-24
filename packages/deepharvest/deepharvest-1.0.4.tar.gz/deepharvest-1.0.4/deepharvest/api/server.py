"""
API Server for DeepHarvest
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from aiohttp import web, ClientSession
import json
from ..core.crawler import DeepHarvest, CrawlConfig, CrawlStrategy
from ..browser import BrowserScraper

logger = logging.getLogger(__name__)


class DeepHarvestAPI:
    """REST API server for DeepHarvest"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()
        self.crawler: Optional[DeepHarvest] = None

    def _setup_routes(self):
        """Setup API routes"""
        self.app.router.add_post("/api/v1/crawl", self.handle_crawl)
        self.app.router.add_get("/api/v1/status", self.handle_status)
        self.app.router.add_get("/api/v1/health", self.handle_health)
        self.app.router.add_post("/api/v1/fetch", self.handle_fetch)

    async def handle_crawl(self, request: web.Request) -> web.Response:
        """Handle crawl request"""
        try:
            data = await request.json()
            urls = data.get("urls", [])
            config_data = data.get("config", {})

            config = CrawlConfig(seed_urls=urls, **config_data)

            self.crawler = DeepHarvest(config)
            await self.crawler.initialize()

            # Start crawl in background
            asyncio.create_task(self.crawler.crawl())

            return web.json_response(
                {"status": "started", "urls": urls, "message": "Crawl started"}
            )
        except Exception as e:
            logger.error(f"Crawl error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def handle_status(self, request: web.Request) -> web.Response:
        """Handle status request"""
        if not self.crawler:
            return web.json_response({"status": "idle", "message": "No active crawl"})

        stats = self.crawler.stats
        return web.json_response(
            {
                "status": "running",
                "stats": {
                    "processed": stats.processed,
                    "success": stats.success,
                    "errors": stats.errors,
                    "bytes_downloaded": stats.bytes_downloaded,
                },
            }
        )

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({"status": "healthy"})

    async def handle_fetch(self, request: web.Request) -> web.Response:
        """Handle single URL fetch"""
        try:
            data = await request.json()
            url = data.get("url")
            use_js = data.get("use_js", True)

            if not url:
                return web.json_response({"error": "URL required"}, status=400)

            config = CrawlConfig(seed_urls=[url])
            async with BrowserScraper(config) as scraper:
                result = await scraper.fetch(url, use_js=use_js)

                return web.json_response(
                    {
                        "url": url,
                        "html": result.html[:1000] if result.html else "",  # Truncate for response
                        "status_code": result.status_code,
                        "has_screenshot": result.screenshot is not None,
                    }
                )
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def run(self):
        """Run the API server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"DeepHarvest API server running on http://{self.host}:{self.port}")

        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down API server...")
            if self.crawler:
                await self.crawler.shutdown()
            await runner.cleanup()


async def serve(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server"""
    api = DeepHarvestAPI(host, port)
    await api.run()
