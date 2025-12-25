import os
import json
import sys
from typing import List
import boto3
from botocore.exceptions import ClientError

class S3FileManager:
    def __init__(self, bucket: str, aws_region: str):
        self.bucket = bucket
        if not self.bucket:
            raise ValueError("Bucket parameter is required")

        region = aws_region

        client_params = {
            "service_name": "s3",
            "region_name": region,
        }

        self.s3 = boto3.client(**client_params)


    def load_json(self, key: str) -> dict:
        """
        Loads JSON data from a file.

        Args:
            key (str): Key or Path to the JSON file.
        Returns:
            dict: Parsed JSON data as a dictionary.
                  Returns an empty dictionary if the file does not exist,
                  if the JSON is invalid, or if an unexpected error occurs.
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except ClientError as e:
            pass
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid JSON in S3 object: {key}")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
        return {}


    def save_json(self, data: dict, key: str) -> None:
        """
        Saves a dictionary as a JSON file at the specified key or path.
        Creates directories if they do not exist.

        Args:
            data (dict): Data to save.
            key (str): Key or Path where the JSON file will be stored.
        """
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(data, ensure_ascii=False, indent=4),
                ContentType="application/json",
            )
        except Exception as e:
            print(f"[ERROR] Saving JSON to S3: {e}")


    def list_files(self, prefix: str, extension: str = ".json") -> List[str]:
        """
        Return a sorted list of files in the given folder that match the provided extension.
        This function:
          - Collects files pattern: `*{extension}`.
          - Sorts results in ascending order by filename (lexicographic).
          - Returns an empty list when no files match.
        Parameters
            prefix: str
                Absolute or relative path to the target folder.
            extension : str, optional
                File extension to match (default: ".json"). The value is appended directly to
                the glob pattern `*{extension}`; for reliable matching use a leading dot,
                e.g., ".json", ".txt".
        Returns
            List[pathlib.Path]
                A list of `Path` objects representing matching files. If the folder does not
                exist or no files match, returns an empty list.
        """
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)

            if "Contents" not in response:
                return []

            return sorted(
                obj["Key"]
                for obj in response["Contents"]
                if obj["Key"].endswith(extension)
            )

        except Exception as e:
            print(f"[ERROR] Listing files in S3: {e}")
            return []
