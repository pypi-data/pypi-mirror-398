import asyncio
import aiohttp
from aiohttp import ClientSession
import os
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from tqdm import tqdm
import nest_asyncio
nest_asyncio.apply()

from .utils import _get_tile_xy

BASE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/geotiff"
CHUNCK_SIZE = 8192


async def _download_tile_async(url: str, destination: str, session: ClientSession) -> str:
    """Download a tile asynchronously if it doesn't already exist locally."""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to download {url}: Status {response.status}")
            content_type = response.headers.get("Content-Type", "")
            if "image/tif" not in content_type:
                raise ValueError(f"Invalid file type for URL {url}")
            
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with open(destination, "wb") as file:
                async for chunk in response.content.iter_chunked(CHUNCK_SIZE):
                    file.write(chunk)
        return destination
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {e}")


async def _download_tiles_async(urls: List[str], cache_folder: str) -> List[str]:
    """Download all tiles asynchronously."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            filepath = _construct_tile_filename(url, cache_folder)
            tasks.append(_download_tile_async(url, filepath, session))
        return await asyncio.gather(*tasks)


def _construct_tile_filename(url: str, cache_folder: str) -> str:
    """Generate a cache-friendly filename from a tile URL."""
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split("/")
    filename = f"{path_segments[-4]}_{path_segments[-3]}_{path_segments[-2]}_{os.path.basename(url)}"
    return os.path.join(cache_folder, filename)

async def _run_download_tiles(uncached_urls, cache_folder):
    """Helper function to run the async downloads."""
    return await _download_tiles_async(uncached_urls, cache_folder)

def _get_aws_terrain(
    bbx: Dict[str, float],
    zoom: int,
    cache_folder: str,
    use_cache: bool,
    verbose: bool,
) -> List[str]:
    def _filter_cached_and_uncached(urls: List[str]) -> Tuple[List[str], List[str]]:
        """Separate cached and uncached tile URLs."""
        cached, uncached = [], []
        for url in urls:
            filepath = _construct_tile_filename(url, cache_folder)
            if os.path.exists(filepath) and use_cache:
                cached.append(filepath)
            else:
                uncached.append(url)
        return cached, uncached

    # Define the base URL and assemble tile URLs
    tiles_df = _get_tile_xy(bbx, zoom)
    urls = [
        f"{BASE_URL}/{zoom}/{tile.tile_x}/{tile.tile_y}.tif"
        for tile in tiles_df.to_records(index=False)
    ]

    # Separate cached and uncached tiles
    cached_files, uncached_urls = _filter_cached_and_uncached(urls)

    if not uncached_urls:
        if verbose:
            print("All tiles retrieved from cache.")
        return cached_files

    # Download uncached tiles asynchronously
    downloaded_tiles = cached_files
    if verbose:
        uncached_urls = tqdm(uncached_urls, desc="Downloading tiles")

    loop = asyncio.get_event_loop()
    downloaded_tiles += loop.run_until_complete(_run_download_tiles(uncached_urls, cache_folder))

    return downloaded_tiles
