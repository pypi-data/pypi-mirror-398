import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Retrieve Cloudinary credentials from environment variables
cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
api_key = os.getenv('CLOUDINARY_API_KEY')
api_secret = os.getenv('CLOUDINARY_API_SECRET')

# Configure Cloudinary
cloudinary.config(
  cloud_name = cloud_name,
  api_key = api_key,
  api_secret = api_secret
)

def upload_image(image, **kwargs):
    """
    Uploads an image to Cloudinary and returns the URL of the uploaded image.
    The image can be provided as a file path or bytes.
    Additional arguments can be passed to the Cloudinary uploader.

    :param image: Path to the image file or bytes of the image to be uploaded
    :param kwargs: Additional arguments for the Cloudinary uploader
    :return: URL of the uploaded image
    """
    try:
        # Ensure the image is private and signed by default
        kwargs.setdefault('type', 'private')
        kwargs.setdefault('sign_url', True)
        
        response = cloudinary.uploader.upload(image, **kwargs)
        return response
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")