"""
Custom Plugin Example
"""
from deepharvest.plugins.base import Plugin

class CustomExtractorPlugin(Plugin):
    """Custom content extractor"""
    
    async def initialize(self):
        """Initialize plugin"""
        print("Custom extractor initialized")
    
    async def process(self, url: str, response) -> dict:
        """Process content"""
        
        # Custom extraction logic
        result = {
            'custom_field': 'extracted value',
            'metadata': {
                'plugin': 'custom_extractor',
                'version': '1.0'
            }
        }
        
        return result
    
    async def shutdown(self):
        """Cleanup"""
        print("Custom extractor shutdown")

# Usage
async def main():
    from deepharvest.core.crawler import DeepHarvest, CrawlConfig
    
    config = CrawlConfig(
        seed_urls=["https://example.com"],
        # plugins=[CustomExtractorPlugin()]  # Would be added to config
    )
    
    crawler = DeepHarvest(config)
    await crawler.initialize()
    await crawler.crawl()
    await crawler.shutdown()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

