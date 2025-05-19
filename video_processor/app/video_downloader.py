from abc import ABC, abstractmethod
import requests
from urllib.parse import urlparse, unquote
import os
from tqdm import tqdm

from common.actverse_common.utils import sanitize_filename

class VideoDownloader(ABC):
    @abstractmethod
    def download(self) -> str:
        raise NotImplementedError
    

class VercelVideoDownloader(VideoDownloader):
    def download(self, url: str, download_path: str):
        response = requests.get(url, stream=True)
        
        os.makedirs(download_path, exist_ok=True)
        file_name = self._file_name_from_vercel_response(url, response)
        download_full_name = os.path.join(download_path, file_name)

        total_size = int(response.headers.get('content-length', 0))

        with open(download_full_name, "wb") as file:
            bar = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)
            bar.close()
        return download_full_name


    def _file_name_from_vercel_response(self, 
                                        url: str, 
                                        response: requests.Response) -> str:
        file_name = None
        if "Content-Disposition" in response.headers:
            for s in response.headers["Content-Disposition"].split(";"):
                if s.lstrip().startswith("filename="):
                    file_name = s.split("=")[1]
            return unquote(file_name.strip('"'))
        else:
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)
            return sanitize_filename(unquote(file_name))
        
            
