"""
Simple Crawl Example
"""
import asyncio
from deepharvest.core.crawler import DeepHarvest, CrawlConfig

async def main():
    # Configure crawler
    config = CrawlConfig(
        seed_urls=["https://example.com"],
        max_depth=3,
        output_dir="./example_output",
        enable_js=True,
        concurrent_requests=5
    )
    
    # Initialize and run crawler
    crawler = DeepHarvest(config)
    
    try:
        await crawler.initialize()
        await crawler.crawl()
    finally:
        await crawler.shutdown()
    
    print("Crawl completed!")

if __name__ == "__main__":
    asyncio.run(main())

