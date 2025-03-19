from google_images_download import google_images_download



# Initialize the downloader
downloader = google_images_download.googleimagesdownload()

# List of titles for which you want to download images
titles = [
    "Pneumonia X-ray",
    "Healthy Lung X-ray"
]

DIRECTORY = "data"

# Download images based on titles
for title in titles:
    arguments = {
        "keywords": title,
        "format": "png",
        "limit": 10,
        "print_urls": True,
        "output_directory":DIRECTORY,
        "no_directory": True,
    }
    
    # Download images
    downloader.download(arguments)

else: 
    print(f'{" FINISHED ":=^50}')
