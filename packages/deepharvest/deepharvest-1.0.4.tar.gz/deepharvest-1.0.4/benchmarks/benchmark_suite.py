"""
Benchmark Suite for DeepHarvest
"""
import asyncio
import time
import logging
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import psutil
import os

logger = logging.getLogger(__name__)


class BenchmarkSuite:
    """Run performance benchmarks"""
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict = {}
    
    async def benchmark_scrape_speed(self, urls: List[str], iterations: int = 5) -> Dict:
        """Benchmark HTML scrape speed"""
        from deepharvest.browser import BrowserScraper
        from deepharvest.core.crawler import CrawlConfig
        
        print(f"\n=== Benchmark: Scrape Speed ===")
        print(f"URLs: {len(urls)}, Iterations: {iterations}")
        
        config = CrawlConfig(seed_urls=urls)
        times = []
        
        for i in range(iterations):
            async with BrowserScraper(config) as scraper:
                start = time.time()
                for url in urls:
                    try:
                        result = await scraper.fetch(url, use_js=False)
                    except:
                        pass
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"  Iteration {i+1}: {elapsed:.2f}s")
        
        avg_time = sum(times) / len(times)
        result = {
            'benchmark': 'scrape_speed',
            'urls': len(urls),
            'iterations': iterations,
            'times': times,
            'average': avg_time,
            'urls_per_second': len(urls) / avg_time if avg_time > 0 else 0
        }
        
        self.results['scrape_speed'] = result
        return result
    
    async def benchmark_playwright_vs_aiohttp(self, urls: List[str]) -> Dict:
        """Compare Playwright vs aiohttp performance"""
        from deepharvest.browser import BrowserScraper
        from deepharvest.core.crawler import CrawlConfig
        import aiohttp
        
        print(f"\n=== Benchmark: Playwright vs aiohttp ===")
        
        config = CrawlConfig(seed_urls=urls)
        
        # Test Playwright
        playwright_times = []
        async with BrowserScraper(config) as scraper:
            for url in urls:
                start = time.time()
                try:
                    await scraper.fetch(url, use_js=True)
                except:
                    pass
                playwright_times.append(time.time() - start)
        
        # Test aiohttp
        aiohttp_times = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                start = time.time()
                try:
                    async with session.get(url) as resp:
                        await resp.text()
                except:
                    pass
                aiohttp_times.append(time.time() - start)
        
        result = {
            'benchmark': 'playwright_vs_aiohttp',
            'urls': len(urls),
            'playwright': {
                'times': playwright_times,
                'average': sum(playwright_times) / len(playwright_times) if playwright_times else 0,
                'total': sum(playwright_times)
            },
            'aiohttp': {
                'times': aiohttp_times,
                'average': sum(aiohttp_times) / len(aiohttp_times) if aiohttp_times else 0,
                'total': sum(aiohttp_times)
            },
            'speedup': sum(aiohttp_times) / sum(playwright_times) if sum(playwright_times) > 0 else 0
        }
        
        self.results['playwright_vs_aiohttp'] = result
        return result
    
    async def benchmark_extraction_quality(self, urls: List[str]) -> Dict:
        """Benchmark extraction quality"""
        from deepharvest.browser import BrowserScraper
        from deepharvest.core.crawler import CrawlConfig
        from deepharvest.extractors.text import TextExtractor
        
        print(f"\n=== Benchmark: Extraction Quality ===")
        
        config = CrawlConfig(seed_urls=urls)
        extractor = TextExtractor()
        
        results = []
        async with BrowserScraper(config) as scraper:
            for url in urls:
                try:
                    result = await scraper.fetch(url, use_js=False)
                    extracted = await extractor.extract(result)
                    
                    quality_score = 0.0
                    if extracted.get('text'):
                        text_len = len(extracted['text'])
                        quality_score = min(text_len / 1000.0, 1.0)  # Normalize
                    
                    results.append({
                        'url': url,
                        'quality_score': quality_score,
                        'text_length': len(extracted.get('text', ''))
                    })
                except:
                    pass
        
        avg_quality = sum(r['quality_score'] for r in results) / len(results) if results else 0
        
        result = {
            'benchmark': 'extraction_quality',
            'urls': len(urls),
            'results': results,
            'average_quality': avg_quality
        }
        
        self.results['extraction_quality'] = result
        return result
    
    async def benchmark_resource_usage(self, urls: List[str], concurrent: int = 10) -> Dict:
        """Benchmark CPU and memory usage under load"""
        from deepharvest.browser import BrowserScraper
        from deepharvest.core.crawler import CrawlConfig
        
        print(f"\n=== Benchmark: Resource Usage ===")
        print(f"Concurrent requests: {concurrent}")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        config = CrawlConfig(seed_urls=urls)
        memory_samples = []
        cpu_samples = []
        
        async def fetch_url(scraper, url):
            try:
                await scraper.fetch(url, use_js=False)
                # Sample memory and CPU
                memory_samples.append(process.memory_info().rss / 1024 / 1024)
                cpu_samples.append(process.cpu_percent())
            except:
                pass
        
        async with BrowserScraper(config) as scraper:
            tasks = []
            for url in urls[:concurrent]:
                tasks.append(fetch_url(scraper, url))
            
            start = time.time()
            await asyncio.gather(*tasks)
            elapsed = time.time() - start
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()
        
        result = {
            'benchmark': 'resource_usage',
            'concurrent': concurrent,
            'duration': elapsed,
            'memory': {
                'initial_mb': initial_memory,
                'final_mb': final_memory,
                'peak_mb': max(memory_samples) if memory_samples else final_memory,
                'average_mb': sum(memory_samples) / len(memory_samples) if memory_samples else final_memory
            },
            'cpu': {
                'initial_percent': initial_cpu,
                'final_percent': final_cpu,
                'average_percent': sum(cpu_samples) / len(cpu_samples) if cpu_samples else final_cpu
            }
        }
        
        self.results['resource_usage'] = result
        return result
    
    async def benchmark_async_vs_sync(self, urls: List[str]) -> Dict:
        """Compare async vs sync performance"""
        import requests
        
        print(f"\n=== Benchmark: Async vs Sync ===")
        
        # Async benchmark
        from deepharvest.browser import BrowserScraper
        from deepharvest.core.crawler import CrawlConfig
        
        config = CrawlConfig(seed_urls=urls)
        
        async_start = time.time()
        async with BrowserScraper(config) as scraper:
            tasks = [scraper.fetch(url, use_js=False) for url in urls]
            await asyncio.gather(*tasks)
        async_time = time.time() - async_start
        
        # Sync benchmark
        sync_start = time.time()
        for url in urls:
            try:
                requests.get(url, timeout=10)
            except:
                pass
        sync_time = time.time() - sync_start
        
        result = {
            'benchmark': 'async_vs_sync',
            'urls': len(urls),
            'async_time': async_time,
            'sync_time': sync_time,
            'speedup': sync_time / async_time if async_time > 0 else 0
        }
        
        self.results['async_vs_sync'] = result
        return result
    
    def generate_report(self) -> str:
        """Generate markdown benchmark report"""
        report_lines = [
            "# DeepHarvest Benchmark Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            ""
        ]
        
        for benchmark_name, result in self.results.items():
            report_lines.append(f"### {benchmark_name.replace('_', ' ').title()}")
            report_lines.append("")
            report_lines.append(f"```json")
            report_lines.append(json.dumps(result, indent=2))
            report_lines.append("```")
            report_lines.append("")
        
        report = "\n".join(report_lines)
        
        # Save report
        report_file = self.output_dir / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_file.write_text(report)
        
        return str(report_file)
    
    def export_json(self) -> str:
        """Export results as JSON"""
        json_file = self.output_dir / f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_file.write_text(json.dumps(self.results, indent=2))
        return str(json_file)


async def run_all_benchmarks(test_urls: List[str] = None):
    """Run all benchmarks"""
    if test_urls is None:
        test_urls = [
            "https://example.com",
            "https://httpbin.org/html",
            "https://httpbin.org/json"
        ]
    
    suite = BenchmarkSuite()
    
    print("Starting DeepHarvest Benchmark Suite...")
    
    await suite.benchmark_scrape_speed(test_urls, iterations=3)
    await suite.benchmark_playwright_vs_aiohttp(test_urls)
    await suite.benchmark_extraction_quality(test_urls)
    await suite.benchmark_resource_usage(test_urls, concurrent=5)
    await suite.benchmark_async_vs_sync(test_urls)
    
    report_file = suite.generate_report()
    json_file = suite.export_json()
    
    print(f"\nBenchmarks completed!")
    print(f"Report: {report_file}")
    print(f"JSON: {json_file}")
    
    return suite

