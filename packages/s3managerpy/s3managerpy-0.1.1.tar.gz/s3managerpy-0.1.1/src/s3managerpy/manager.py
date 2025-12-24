import boto3
from botocore.exceptions import NoCredentialsError
import os
import mimetypes


class S3Manager:
    """
    A clean, reusable, production-ready helper class for managing AWS S3 operations.

    This class abstracts the most common S3 operations:
    - Upload images/documents
    - Download files (to disk or bytes)
    - Copy, move, delete files
    - List folders or files
    - Check file existence
    - Generate pre-signed URLs
    - Create folders (prefixes)

    Works anywhere: Django, Flask, FastAPI, or plain Python.

    Environment Variables Supported:
        AWS_BUCKET_NAME
        AWS_REGION
        AWS_ACCESS_KEY_ID
        AWS_SECRET_ACCESS_KEY
        AWS_CLOUDFRONT_DOMAIN

    Example:
        s3 = S3Manager()
        url = s3.upload_image(file, "avatars", "john")
    """

    def __init__(
        self,
        bucket_name: str = None,
        region: str = None,
        access_key: str = None,
        secret_key: str = None,
        cloudfront_domain: str = None,
    ):
        """
        Initialize the S3 client.

        Args:
            bucket_name (str): AWS bucket name.
            region (str): AWS region.
            access_key (str): AWS Access Key ID.
            secret_key (str): AWS Secret Access Key.
            cloudfront_domain (str): CloudFront domain.

        Example:
            s3 = S3Manager(bucket_name="my-bucket", region="us-east-1")
        """

        self.bucket_name = bucket_name or os.getenv("AWS_BUCKET_NAME")
        region = region or os.getenv("AWS_REGION")
        access_key = access_key or os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.cloudfront_domain = cloudfront_domain or os.getenv(
            "AWS_CLOUDFRONT_DOMAIN"
        )

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    # -------------------------------------------------------------------
    # INTERNAL HANDLER
    # -------------------------------------------------------------------

    def _upload(self, file, folder: str, name: str, content_disposition="inline"):
        """
        Internal upload handler used by image/file uploads.

        Args:
            file: File-like object.
            folder (str): Target folder.
            name (str): File name.
            content_disposition (str): Inline or attachment.

        Returns:
            str: Public URL.

        Example:
            s3._upload(file, "docs", "resume")
        """
        ext = file.name.rsplit(".", 1)[-1].lower()
        base_name = name.rsplit(".", 1)[0]
        file_path = os.path.join(folder, f"{base_name}.{ext}").replace("\\", "/")

        content_type, _ = mimetypes.guess_type(file.name)
        content_type = content_type or "application/octet-stream"

        try:
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                file_path,
                ExtraArgs={
                    "ContentType": content_type,
                    "ContentDisposition": content_disposition,
                },
            )

            if self.cloudfront_domain:
                return f"https://{self.cloudfront_domain}/{file_path}"

            return f"https://{self.bucket_name}.s3.amazonaws.com/{file_path}"

        except NoCredentialsError:
            return "AWS credentials not found"
        except Exception as e:
            return str(e)

    # -------------------------------------------------------------------
    # UPLOAD METHODS
    # -------------------------------------------------------------------

    def upload_image(self, file, folder: str, name: str):
        """
        Upload an image file to S3.

        Allowed: jpg, jpeg, png, webp

        Example:
            s3 = S3Manager()
            url = s3.upload_image(file, "avatars", "john")

        Returns:
            str: Public URL.
        """
        valid = ["jpg", "jpeg", "png", "webp"]
        ext = file.name.rsplit(".", 1)[-1].lower()

        if ext not in valid:
            return "Invalid image type"

        return self._upload(file, folder, name)

    def upload_file(self, file, folder: str, name: str):
        """
        Upload a document to S3.

        Allowed: pdf, csv, doc, docx, txt

        Example:
            s3 = S3Manager()
            url = s3.upload_file(file, "docs", "resume")

        Returns:
            str: Public URL.
        """
        valid = ["pdf", "csv", "doc", "docx", "txt"]
        ext = file.name.rsplit(".", 1)[-1].lower()

        if ext not in valid:
            return "Invalid file format"

        return self._upload(
            file,
            folder,
            name,
            content_disposition=f'attachment; filename="{name}.{ext}"',
        )

    # -------------------------------------------------------------------
    # DOWNLOAD METHODS
    # -------------------------------------------------------------------

    def download(self, key: str, destination: str) -> bool:
        """
        Download a file from S3 to local disk.

        Args:
            key (str): S3 path.
            destination (str): Local save path.

        Example:
            s3 = S3Manager()
            s3.download("docs/resume.pdf", "resume.pdf")

        Returns:
            bool: True if successful.
        """
        try:
            self.s3_client.download_file(self.bucket_name, key, destination)
            return True
        except Exception:
            return False

    def download_bytes(self, key: str) -> bytes:
        """
        Download file content as bytes (no local save).

        Example:
            s3 = S3Manager()
            data = s3.download_bytes("images/avatar.png")
            open("copy.png", "wb").write(data)

        Returns:
            bytes
        """
        try:
            resp = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return resp["Body"].read()
        except Exception:
            return b""

    # -------------------------------------------------------------------
    # FILE OPERATIONS
    # -------------------------------------------------------------------

    def delete_file(self, key: str) -> bool:
        """
        Delete a single file.

        Example:
            s3.delete_file("images/john.png")
        """
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        return True

    def delete_folder(self, folder: str) -> bool:
        """
        Delete everything inside a folder.

        Example:
            s3.delete_folder("avatars/")
        """
        objects = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name, Prefix=f"{folder}/"
        )

        if "Contents" in objects:
            keys = [{"Key": obj["Key"]} for obj in objects["Contents"]]
            self.s3_client.delete_objects(
                Bucket=self.bucket_name, Delete={"Objects": keys}
            )

        return True

    def copy_file(self, old_key: str, new_key: str) -> bool:
        """
        Copy file inside S3.

        Example:
            s3.copy_file("docs/resume.pdf", "backup/resume.pdf")
        """
        self.s3_client.copy_object(
            Bucket=self.bucket_name,
            CopySource={"Bucket": self.bucket_name, "Key": old_key},
            Key=new_key,
        )
        return True

    def move_file(self, old_key: str, new_key: str) -> bool:
        """
        Move/rename file inside S3.

        Example:
            s3.move_file("temp/file.png", "images/file.png")
        """
        self.copy_file(old_key, new_key)
        self.delete_file(old_key)
        return True

    def create_folder(self, folder_name: str) -> bool:
        """
        Create a folder (prefix).

        Example:
            s3.create_folder("invoices/")
        """
        if not folder_name.endswith("/"):
            folder_name += "/"

        self.s3_client.put_object(Bucket=self.bucket_name, Key=folder_name)
        return True

    # -------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------

    def file_exists(self, key: str) -> bool:
        """
        Check if file exists.

        Example:
            exists = s3.file_exists("uploads/photo.jpg")
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except:
            return False

    def list_folders(self, prefix: str = ""):
        """
        List folders.

        Example:
            folders = s3.list_folders("uploads/")
        """
        res = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name, Prefix=prefix, Delimiter="/"
        )
        return [f["Prefix"] for f in res.get("CommonPrefixes", [])]

    def list_files(self, folder: str):
        """
        List files inside a folder with full URLs.

        Example:
            files = s3.list_files("avatars/")
        """
        res = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name, Prefix=f"{folder}/", Delimiter="/"
        )
        if "Contents" not in res:
            return []

        urls = []
        for obj in res["Contents"]:
            key = obj["Key"]

            if self.cloudfront_domain:
                urls.append(f"https://{self.cloudfront_domain}/{key}")
            else:
                urls.append(f"https://{self.bucket_name}.s3.amazonaws.com/{key}")

        return urls

    def get_signed_url(self, key: str, expires=3600):
        """
        Generate a pre-signed temporary URL.

        Example:
            url = s3.get_signed_url("docs/invoice.pdf")
        """
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires,
        )
