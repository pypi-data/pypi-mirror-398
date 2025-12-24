"""
Distributed Crawl Example
"""
import asyncio
from deepharvest.distributed.coordinator import DistributedCoordinator

async def main():
    # Initialize coordinator
    coordinator = DistributedCoordinator(redis_url="redis://localhost:6379")
    
    # Initialize with 5 workers
    await coordinator.initialize(num_workers=5)
    
    # Start crawl
    seed_urls = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]
    
    try:
        await coordinator.start_crawl(seed_urls)
    finally:
        await coordinator.shutdown()
    
    print("Distributed crawl completed!")

if __name__ == "__main__":
    asyncio.run(main())

