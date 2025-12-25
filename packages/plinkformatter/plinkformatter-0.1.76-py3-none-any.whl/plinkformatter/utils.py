import os
import logging 
from typing import List


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper functions
def validate_files_exist_and_not_empty(prefix: str, extensions: List[str]) -> None:
    """
    Validate that the files with given prefix and extensions exist and are not empty.

    Args:
        prefix: The prefix of the files to check.
        extensions: A list of file extensions to check.
    """
    for ext in extensions:
        output_file = f"{prefix}.{ext}"
        logging.debug("Checking file: %s", output_file)
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"{output_file} does not exist.")
        if os.path.getsize(output_file) == 0:
            raise ValueError(f"{output_file} is empty.")