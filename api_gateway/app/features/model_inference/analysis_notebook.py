"""
노트북 분석 스크립트 생성을 위한 태스크
"""

import os
from typing import Literal

import nbformat
import requests

from actverse_common.logging import setup_logger

from google.oauth2 import service_account
from googleapiclient.discovery import build


logger = setup_logger(service_name="analysis_notebook")


class GoogleDriveClient:
    def __init__(self):
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        service_account_file = os.getenv("GOOGLE_CREDENTIALS")
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=credentials)

    def upload_notebook_file(self, file_path, file_name=None):
        file_name = file_name or os.path.basename(file_path)
        parent_folder_id = self.folder_id
        file_id = self.upload_file(file_path, parent_folder_id, file_name)
        colab_link = f"https://colab.research.google.com/drive/{file_id}"
        return colab_link


gdrive_client = GoogleDriveClient()

def generate_analysis_script(
    task_id: str,
    user_url: str,
    lang: Literal["ko", "en"] = "ko",
    max_retries: int = 0,
):
    """
    분석용 노트북 스크립트를 생성하는 태스크입니다.

    Args:
        task_id: 작업 ID
        user_url: 사용자 URL
        lang: 언어 ('ko' 또는 'en')
        max_retries: 재시도 횟수

    Returns:
        Colab 링크
    """
    logger.info(f"Starting notebook generation for {task_id}")
    

    try:
        assert lang in ["ko", "en"], f"lang must be either 'ko' or 'en', not {lang}"
        file_url = f"https://raw.githubusercontent.com/actnova-inc/actverse-analysis/main/bin/{lang}/custom_analysis.ipynb"
        script_path = f"/app/data_storage/notebooks/{lang}/custom_analysis_{task_id}.ipynb"
        os.makedirs(os.path.dirname(script_path), exist_ok=True)

        # 노트북 템플릿 다운로드
        logger.info(f"Downloading notebook template from {file_url}")
        notebook_object = load_notebook(file_url)

        # 사용자 URL 설정
        logger.info(f"Setting user URL: {user_url}")
        save_with_user_url(notebook_object, user_url, script_path)

        # Google Drive에 업로드
        logger.info("Uploading notebook to Google Drive")
        colab_link = gdrive_client.upload_notebook_file(script_path)

        logger.info(f"Notebook generated successfully: {colab_link}")

        return colab_link
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to generate notebook: {str(e)}")
        raise e


def load_notebook(url: str) -> nbformat.NotebookNode:
    """
    URL에서 Jupyter 노트북 파일을 다운로드합니다.

    Args:
        url: 노트북 파일 URL

    Returns:
        nbformat.NotebookNode: 노트북 객체
    """
    response = requests.get(url)
    response.raise_for_status()  # 오류 체크
    ipynb_content = response.content
    nb = nbformat.reads(ipynb_content, as_version=4)
    return nb


def save_with_user_url(
    notebook_object: nbformat.NotebookNode, user_url: str, output_path: str
):
    """
    사용자 URL을 노트북에 설정하고 저장합니다.

    Args:
        notebook_object: 노트북 객체
        user_url: 사용자 URL
        output_path: 저장 경로
    """
    # json_path에 URL 입력
    for cell in notebook_object.cells:
        if cell.cell_type == "code" and "json_path = input" in cell.source:
            cell.source = cell.source.replace(
                'input("Downloadable url or local file path:")', f'"{user_url}"'
            )

    # 수정된 Notebook 저장
    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(notebook_object, f)
