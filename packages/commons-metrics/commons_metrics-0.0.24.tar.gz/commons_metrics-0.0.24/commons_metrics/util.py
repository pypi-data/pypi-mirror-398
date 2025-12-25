import boto3
import json

class Util:
    """Utility class for common operations"""
    
    @staticmethod
    def get_secret_aws(secret_name: str, logger, region_name: str):
        """
        Retrieves AWS Secrets Manager secret and returns database credentials
        """
        try:
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=region_name
            )

            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            secret_string = get_secret_value_response['SecretString']
            secret_json = json.loads(secret_string)

            required_keys = ["password", "host", "port", "username", "dbname"]
            missing_keys = [key for key in required_keys if key not in secret_json]

            if missing_keys:
                msg = f"Missing required keys in AWS secret: {missing_keys}"
                logger.error(msg)
                raise KeyError(msg)

            return secret_json

        except Exception as e:
            msg = f"Error getting the secret '{secret_name}': {str(e)}"
            logger.error(msg)
            raise Exception(msg)


