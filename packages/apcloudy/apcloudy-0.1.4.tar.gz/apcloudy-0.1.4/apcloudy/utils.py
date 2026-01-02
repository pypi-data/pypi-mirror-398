"""
A collection of utility functions for handling chunking, batching,
and configuration validation processes.

This module provides tools to split lists or URLs into smaller chunks,
validate configurations, and construct API URLs effectively.
"""

from typing import List, TypeVar, Iterator
import math

from .config import config

T = TypeVar('T')


def chunk_urls(urls: List[str], parts: int) -> List[List[str]]:
    """
    Split URLs into approximately equal chunks for parallel processing

    Args:
        urls: List of URLs to split
        parts: Number of chunks to create

    Returns:
        List[List[str]]: List of URL chunks
    """
    if parts <= 0:
        raise ValueError("Parts must be greater than 0")

    if not urls:
        return []

    if parts >= len(urls):
        return [[url] for url in urls]

    avg = len(urls) // parts
    remainder = len(urls) % parts

    chunks = []
    start = 0

    for i in range(parts):
        # Add one extra item to first 'remainder' chunks
        chunk_size = avg + (1 if i < remainder else 0)
        chunks.append(urls[start:start + chunk_size])
        start += chunk_size

    return [chunk for chunk in chunks if chunk]  # Filter empty chunks


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split list into fixed-size chunks

    Args:
        items: List to split
        chunk_size: Size of each chunk

    Returns:
        List[List[T]]: List of chunks
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than 0")

    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])

    return chunks


def batch_iterator(items: List[T], batch_size: int) -> Iterator[List[T]]:
    """
    Create an iterator that yields batches of items

    Args:
        items: List to iterate over
        batch_size: Size of each batch

    Yields:
        List[T]: Batch of items
    """
    if batch_size <= 0:
        raise ValueError("Batch size must be greater than 0")

    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def calculate_optimal_chunks(total_items: int, max_items_per_chunk: int = 1000,
                             max_chunks: int = 100) -> int:
    """
    Calculate optimal number of chunks based on constraints

    Args:
        total_items: Total number of items to process
        max_items_per_chunk: Maximum items per chunk
        max_chunks: Maximum number of chunks

    Returns:
        int: Optimal number of chunks
    """
    if total_items <= 0:
        return 0

    # Calculate minimum chunks needed to respect max_items_per_chunk
    min_chunks = math.ceil(total_items / max_items_per_chunk)

    # Return the minimum between calculated chunks and max_chunks
    return min(min_chunks, max_chunks)


def validate_config() -> None:
    """
    Validate the configuration values
    """
    # Add validation logic as needed
    if not config.base_url:
        raise ValueError("Base URL is not set in the configuration")

    # Add more validations based on your config structure


def chunk_urls(urls: List[str], chunk_size: int = None) -> Iterator[List[str]]:
    """
    Split URLs into chunks for batch processing

    Args:
        urls: List of URLs to chunk
        chunk_size: Size of each chunk (uses config default if not provided)

    Yields:
        List[str]: Chunks of URLs
    """
    # Validate config before using default values
    validate_config()

    chunk_size = chunk_size or config.default_page_size

    for i in range(0, len(urls), chunk_size):
        yield urls[i:i + chunk_size]


def validate_job_args(job_args: dict) -> dict:
    """
    Validate and sanitize job arguments

    Args:
        job_args: Job arguments to validate

    Returns:
        dict: Validated job arguments
    """
    # Validate config to ensure limits are properly set
    validate_config()

    # Ensure job_args is not too large (prevent API payload issues)
    if len(str(job_args)) > 10000:  # 10KB limit
        raise ValueError("Job arguments too large. Keep under 10KB.")

    return job_args


def format_api_url(endpoint: str) -> str:
    """
    Format API endpoint URL

    Args:
        endpoint: API endpoint

    Returns:
        str: Full URL
    """
    # Validate config to ensure base_url is set
    validate_config()

    base_url = config.base_url.rstrip('/')
    endpoint = endpoint.lstrip('/')
    return f"{base_url}/{endpoint}"
