import requests
import urllib3
from .s3_file_manager import S3FileManager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CacheManager:
    """Manager for caching data in S3 and making API requests"""
    
    def __init__(self, bucket: str, aws_region: str):
        self.s3 = S3FileManager(bucket=bucket, aws_region=aws_region)
    
    def load_cache_or_fetch(self, path: str, fetch_fn, clear_cache: bool = False):
        """
        Load data from a JSON cache stored in S3 using S3FileManager,
        or fetch the data and update the cache.

        Args:
            path (str): Cache key relative to "cache/", e.g. "logs/123.json"
            fetch_fn (Callable): Function returning JSON-serializable data
            clear_cache (bool): If True, delete existing cache before fetching
        Returns:
            Any: Cached or freshly fetched data
        """
        key = f"cache/{path}"
        if clear_cache:
            try:
                self.s3.s3.delete_object(Bucket=self.s3.bucket, Key=key)
            except Exception:
                pass
        data = self.s3.load_json(key)

        if data:
            return data

        data = fetch_fn()
        self.s3.save_json(data, key)

        return data

    def get_data_from_api(self, url: str, headers: dict, auth_api) -> list:
        """
        Sends a GET request to the specified API and returns the JSON response if successful.

        Args:
            url (str): The API endpoint URL.
            headers (dict): HTTP headers for the request.
            auth_api: Authentication object for the request.
        Returns:
            list or dict: JSON response from the API if successful, otherwise an empty list.
        """
        response = requests.get(url, headers=headers, auth=auth_api, verify=False)
        if response.ok:
            return response.json()
        return []

    def post_data_to_api(self, url: str, headers: dict, body: dict, auth_api) -> list:
        """
        Sends a POST request to the specified API with the given body and returns the JSON response if successful.

        Args:
            url (str): The API endpoint URL.
            headers (dict): HTTP headers for the request.
            body (dict): Data to send in the POST request.
            auth_api: Authentication object for the request.
        Returns:
            list or dict: JSON response from the API if successful, otherwise an empty list.
        """
        response = requests.post(url, headers=headers, auth=auth_api, data=body, verify=False)
        if response.ok:
            return response.json()
        return []
