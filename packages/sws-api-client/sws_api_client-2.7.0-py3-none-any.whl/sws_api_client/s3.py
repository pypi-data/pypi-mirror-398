from pathlib import Path
from sws_api_client.sws_api_client import SwsApiClient
import requests

class S3:
    
    def __init__(self, sws_client: SwsApiClient) -> None:
        self.sws_client = sws_client
        
    def get_s3_bucket(self, extension: str):
        
        url = f'/observations/s3-presigned-url/{extension}'
        
        response = self.sws_client.discoverable.get('is_api', f'/observations/s3-presigned-url/{extension}')
        
        success:bool = response.get('success')
                
        if success:
            return {
                'key': response.get('key'),
                'url': response.get('url')
            }
            
        else:
            raise ValueError(f'Cannot call S3 api for obtaining keys')
            
            
    def upload_file_to_s3(self, file: str):
        
        file_path = Path(file)
        
        extension = file_path.suffix.replace('.', '')
        
        s3_upload_config = self.get_s3_bucket(extension=extension)
        
        presigned_url = s3_upload_config['url']
                
        headers = {'Content-Type': 'application/zip'}
        
        
        with open(file, 'rb') as file_data:
            response = requests.put(presigned_url, data=file_data, headers=headers)
        
        return s3_upload_config['key']