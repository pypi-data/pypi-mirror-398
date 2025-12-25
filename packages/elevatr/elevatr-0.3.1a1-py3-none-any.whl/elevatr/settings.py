"""
Global settings that can be configured by the user.

ask_confirmation : bool
    Whether to ask for confirmation before downloading large files.
    If True, the user will be prompted to confirm the download if the file size exceeds the specified limit.
min_size_for_confirmation : float
    Minimum size in GB to ask for confirmation.
    If the estimated file size exceeds this value, the user will be asked for confirmation.
cache_folder : str
    Path to the cache folder for the package.
"""

ask_confirmation: bool = True
min_size_for_confirmation: float = 1  # 1 GB
cache_folder: str = "./cache"
