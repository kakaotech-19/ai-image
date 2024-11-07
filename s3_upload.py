import requests
import boto3
import logging
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# AWS 설정
AWS_REGION = 'ap-northeast-2'  # 예: 'us-west-2'
BUCKET_NAME = 'kakaotech19-todak'  # 사용 중인 S3 버킷 이름

# S3 클라이언트 생성
s3_client = boto3.client('s3', region_name=AWS_REGION)

DEFAULT_PATH = 'webtoon-ai/'  # 디폴트 경로 설정


def download_webp(url: str, imgName: str) -> str:
    default_path = './uploads'
    if not os.path.exists(default_path):
        os.makedirs(default_path)
    try:
        response = requests.get(url)
        response.raise_for_status()  # 요청 에러가 있는 경우 예외 발생
        file_path = os.path.join(default_path, f'{imgName}.webp')
        with open(file_path, "wb") as f:
            f.write(response.content)
        logging.info(f"File downloaded successfully and saved to {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Error downloading file from {url}: {type(e).__name__}: {e}")
        return None


import posixpath

def upload_image_to_s3(file_path: str, member_id: str, date: Optional[str] = None, is_profile: bool = True) -> Optional[str]:
    if not BUCKET_NAME:
        logging.error("BUCKET_NAME is not set. Cannot upload to S3.")
        return None

    if not isinstance(file_path, str):
        logging.error(f"Invalid file_path type: {type(file_path)}. Expected str.")
        return None

    if not os.path.isfile(file_path):
        logging.error(f"Error: File {file_path} does not exist.")
        return None

    # S3에 저장할 객체 이름 설정 (posixpath 사용)
    if is_profile:
        object_name = posixpath.join(DEFAULT_PATH, member_id, os.path.basename(file_path))
    elif date:
        object_name = posixpath.join(DEFAULT_PATH, member_id, date, os.path.basename(file_path))
    else:
        logging.error("Invalid parameters: either date should be provided for webtoon images or is_profile should be True.")
        return None

    try:
        s3_client.upload_file(
            file_path,
            BUCKET_NAME,
            object_name,
            ExtraArgs={'ContentType': 'image/webp'}
        )

        s3_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_name}"
        logging.info(f"Image successfully uploaded to S3: {s3_url}")
        return s3_url
    except Exception as e:
        logging.error(f"Error uploading image to S3: {type(e).__name__}: {e}")
        return None

