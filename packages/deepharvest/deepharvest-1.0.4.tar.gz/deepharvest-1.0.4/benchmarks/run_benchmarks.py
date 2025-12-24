"""
Run benchmark suite
"""
import asyncio
import click
from benchmark_suite import run_all_benchmarks


@click.command()
@click.option('--urls', multiple=True, help='URLs to benchmark')
@click.option('--output', default='./benchmark_results', help='Output directory')
def main(urls, output):
    """Run DeepHarvest benchmarks"""
    test_urls = list(urls) if urls else None
    asyncio.run(run_all_benchmarks(test_urls))


if __name__ == '__main__':
    main()

