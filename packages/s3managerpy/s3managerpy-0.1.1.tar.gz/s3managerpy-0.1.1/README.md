# S3ManagerPy

A clean, reusable Python package for managing AWS S3 operations, designed to simplify file and folder management in Python projects. Works seamlessly with Django, Flask, FastAPI, or plain Python.

## Features
- Upload images and documents
- Download files (to disk or bytes)
- Copy, move, and delete files
- List folders or files
- Check if a file exists
- Generate pre-signed URLs
- Create folders (prefixes)

## Installation
```bash
pip install s3managerpy

## Environment Variables

The package can load AWS credentials from environment variables:

AWS_BUCKET_NAME – Your S3 bucket name

AWS_REGION – AWS region (e.g., us-east-1)

AWS_ACCESS_KEY_ID – AWS access key

AWS_SECRET_ACCESS_KEY – AWS secret key

AWS_CLOUDFRONT_DOMAIN – Optional CloudFront domain for CDN URLs

You can also pass these values directly when initializing S3Manager.

Usage
from s3managerpy import S3Manager

# Initialize S3 manager
s3 = S3Manager()

# --------------------------
# Uploading files
# --------------------------
# Upload an image
url = s3.upload_image(file, "avatars", "john")
print("Uploaded image URL:", url)

# Upload a document
doc_url = s3.upload_file(file, "documents", "resume_2025")
print("Uploaded document URL:", doc_url)

# --------------------------
# Downloading files
# --------------------------
# Download a file from S3 to local disk
s3.download("documents/resume_2025.pdf", "resume.pdf")

# Download file as bytes
file_bytes = s3.download("documents/resume_2025.pdf")
print("Downloaded bytes:", len(file_bytes))

# --------------------------
# File operations
# --------------------------
# Check if a file exists
exists = s3.file_exists("avatars/john.jpg")
print("File exists:", exists)

# Copy a file
s3.copy_file("avatars/john.jpg", "avatars/john_backup.jpg")

# Move (rename) a file
s3.move_file("avatars/john_backup.jpg", "avatars/john_final.jpg")

# Delete a file
s3.delete_file("avatars/john_final.jpg")

# Delete all files in a folder
s3.delete_folder("documents/temp_folder")

# --------------------------
# Folder operations
# --------------------------
# Create a new folder
s3.create_folder("projects/demo")

# List folders and files
folders = s3.list_folders("projects/")
print("Folders:", folders)
files = s3.list_files("projects/demo")
print("Files:", files)

# --------------------------
# Pre-signed URL
# --------------------------
signed_url = s3.get_signed_url("documents/resume_2025.pdf", expires=600)
print("Temporary download URL:", signed_url)

License

MIT License. See LICENSE
 for details.