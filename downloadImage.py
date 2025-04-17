#  import section 
import os
import glob
from icrawler.builtin import GoogleImageCrawler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_folder(path):
    """
    Create a directory if it doesn't exist.

    Args:
        path (str): The path of the folder to create.
    """
    try:
        # debugg Attribute
        logger.info(f'{path=}')

        os.makedirs(path, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory '{path}': {e}")


def download_images(query:str, output_dir:str, limit:int=10):
    """
    Download images from Google using the icrawler library.

    Args:
        query (str): The search keyword to query images for.
        output_dir (str): The path where downloaded images will be stored.
        limit (int): Maximum number of images to download.
    """
    try:
        logger.info(f"Downloading {limit} images for '{query}'...")
        crawler = GoogleImageCrawler(storage={"root_dir": output_dir})
        crawler.crawl(keyword=query, max_num=limit)
    except Exception as e:
        logger.error(f"Failed to download images for '{query}': {e}")


def rename_images_in_folder(folder_path, prefix):
    """
    Rename all files in the given folder with a specific prefix and index.

    Args:
        folder_path (str): Path to the folder containing downloaded images.
        prefix (str): Prefix to use when renaming files (e.g., category name).
    """
    try:
        images = glob.glob(os.path.join(folder_path, "*.*"))
        for i, img_path in enumerate(images):
            try:
                ext = os.path.splitext(img_path)[1]
                new_name = f"{prefix}_{i}{ext}"
                new_path = os.path.join(folder_path, new_name)
                os.rename(img_path, new_path)
            except Exception as e:
                logger.warning(f'Failed to rename {img_path}: {e}')
    except Exception as e:
        logger.error(f"Failed to access folder '{folder_path}': {e}")

def image_downloader(queries: dict[str:str], base_dir="static/data", limit=10,session_id=None):
    """
    Download and rename images for each query-category pair.

    Args:
        queries (dict): A dictionary where keys are search queries and values are folder/category names.
        base_dir (str): Root directory to store all image folders.
        limit (int): Number of images to download per category.
    """
    for query, folder_name in queries.items():
        output_path = os.path.join(base_dir, folder_name)
        create_folder(output_path)
        download_images(query, output_path, limit)
        rename_images_in_folder(output_path, folder_name)

    print(f"\n{' FINISHED ':=^50}")


if __name__ == "__main__":
    # Define the search queries and target folders
    queries = {
        "Pneumonia X-ray": "Pneumonia",
        "Healthy Lung X-ray": "Healthy"
    }
    # Run the image downloader with error handling
    image_downloader(queries, base_dir="data", limit=10)
