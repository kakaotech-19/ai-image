from fastapi import FastAPI, Body, UploadFile, File, Form, BackgroundTasks
import base64
import extract_profile
import make_profile
import make_scenario
import make_webtoon
import logging
import os
import requests
from typing import Optional
import boto3
from dotenv import load_dotenv
import posixpath
import re


# 로컬 개발 환경에서만 .env 파일을 로드
dotenv_path = '.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logging.info(f".env 파일({dotenv_path})을 성공적으로 로드했습니다.")
else:
    logging.info(f".env 파일({dotenv_path})이 존재하지 않습니다. 환경 변수를 직접 설정합니다.")

app = FastAPI()

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# 환경 변수 로드
models = dict()
models['romance'] = ["tpals0409/romance-webtoon-character", "64ad94c7f1fe7cfe73ee7b3d0f7deae8a59d201689eb12d07f74baa9325949e0"]
models['pixar'] = ["tpals0409/test_pixar", "32c27ef90bb8b1b2c272809059306a6ecc3e7b903b694857fefa0175d7726ca6"]

# 업로드할 파일 경로
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# AWS 설정
AWS_REGION = os.getenv('AWS_REGION', 'ap-northeast-2')
BUCKET_NAME = os.getenv('BUCKET_NAME')

# 로드된 환경 변수 로그에 출력
logging.info(f"AWS_REGION: {AWS_REGION}")
logging.info(f"BUCKET_NAME: {BUCKET_NAME}")

# S3 클라이언트 생성
s3_client = boto3.client('s3', region_name=AWS_REGION)

DEFAULT_PATH = 'webtoon-ai/'  # 디폴트 경로 설정

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def sanitize_member_id(member_id: str) -> str:
    # 허용할 문자 패턴을 정의 (예: 알파벳 소문자, 숫자, 언더스코어)
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', member_id)
    logging.info(f"Sanitized memberId: {sanitized}")
    return sanitized

def upload_image_to_s3(file_path: str, member_id: str, date: Optional[str] = None, is_profile: bool = True) -> Optional[str]:
    logging.info(f"Original member_id: {member_id}")
    member_id = sanitize_member_id(member_id)
    logging.info(f"Sanitized member_id: {member_id}")

    logging.info(f"Uploading {'profile' if is_profile else 'webtoon'} image for member_id: {member_id}")
    logging.info(f"DEFAULT_PATH: {DEFAULT_PATH}")
    logging.info(f"File Path: {file_path}")

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
        # 프로필 이미지의 경우, 'profile_leo.webp'로 명명
        filename = f"temp_profile.webp"
        object_name = posixpath.join(DEFAULT_PATH, member_id, filename)
    elif date:
        # 웹툰 이미지의 경우, 날짜 폴더 안에 저장
        object_name = posixpath.join(DEFAULT_PATH, member_id, date, os.path.basename(file_path))
    else:
        logging.error("Invalid parameters: either date should be provided for webtoon images or is_profile should be True.")
        return None

    logging.info(f"Object Name: {object_name}")

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

def download_webp(url: str, imgName: str) -> Optional[str]:
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

def process_profile_background(memberId: str, file_path: str, characterStyle: str, apiDomainUrl: str):
    model_type = models[characterStyle][0]
    version_type = models[characterStyle][1]

    try:
        logging.info(f"Processing profile for memberId: {memberId}")
        # 이미지 Base64 인코딩
        base64_image = encode_image(file_path)

        # extract_profile 모듈을 사용해 GPT 응답 받기
        user_id_response, gpt = extract_profile.get_gpt_response(memberId, base64_image)
        logging.info(f"Character Info: {gpt}")

        if user_id_response != memberId:
            logging.error("User ID mismatch")
            return

        # make_profile 모듈을 사용해 프로필 생성
        seed, image = make_profile.create_profile(model_type, version_type, gpt)
        logging.info(f"Seed: {seed}")
        logging.info(f"Image: {image}")

        # image는 단일 URL 문자열로 가정
        image_url = image

        if not image_url:
            logging.error("No image URL returned from create_profile")
            return

        # 이미지 URL을 로컬에 다운로드
        local_image_path = download_webp(image_url, f"temp_profile")
        if not local_image_path:
            logging.error(f"Failed to download profile image from URL: {image_url}")
            return

        # 이미지 S3에 업로드 (다운로드한 로컬 파일 경로 사용)
        logging.info(f"Uploading profile image: {local_image_path} for memberId: {memberId}")
        s3_url = upload_image_to_s3(local_image_path, memberId, is_profile=True)
        if s3_url:
            logging.info(f"Profile image uploaded to S3: {s3_url}")
            os.remove(local_image_path)
            logging.info(f"Local profile image {local_image_path} deleted after successful upload.")
        else:
            logging.error("Failed to upload profile image to S3.")

        # 원본 파일 삭제
        os.remove(file_path)
        logging.info(f"Local file {file_path} deleted after successful upload.")

        # 결과 데이터 준비
        result_data = {
            "memberId": sanitize_member_id(memberId),
            "characterInfo": gpt,
            "characterStyle": "romance",
            "seedNum": seed,
            "characterProfileImageUrl": s3_url
        }
        try:
            webhook_url = f"http://{apiDomainUrl}/api/v1/webhook/ai/character"  # 수정된 부분
            response = requests.post(webhook_url, json=result_data)  # 수정된 부분
            # response = requests.post(f"http://localhost:8080/api/v1/webhook/ai/character", json=result_data)
            if response.status_code == 200:
                logging.info("Profile data successfully posted")
            else:
                logging.error(f"Failed to post profile data. Status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error while posting profile data: {e}")

    except Exception as e:
        logging.error(f"Error in process_profile_background: {e}")

def process_webtoon_background(memberId: str, date: str, content: str, characterInfo: str, seedNum: int, characterStyle: str, apiDomainUrl: str):
    try:
        logging.info(f"Processing webtoon for memberId: {memberId}, date: {date}")
        # 시나리오 생성
        user_id_response, scenario = make_scenario.get_gpt_response(memberId, content)
        logging.info(f"Scenario: {scenario}")
        model_type = models[characterStyle][0]
        version_type = models[characterStyle][1]
        results = []
        for i, scene in enumerate(scenario):
            logging.info(f"Processing scenario {i}: {scene}")
            image_urls = make_webtoon.create_webtoon(memberId, characterInfo, seedNum, scene, model_type, version_type)
            logging.info(f"Webtoon images created: {image_urls}")

            # image_urls는 리스트라고 가정합니다.
            for j, image_url in enumerate(image_urls):
                logging.info(f"Processing image {j} for scenario {i}: {image_url}")

                # 이미지 다운로드
                local_image_path = download_webp(image_url, f"{i+1}")
                if local_image_path:
                    # S3에 이미지 업로드 (memberId를 문자열로 변환)
                    logging.info(f"Uploading webtoon image: {local_image_path} for memberId: {memberId}")
                    s3_url = upload_image_to_s3(local_image_path, memberId, date=date, is_profile=False)
                    if s3_url:
                        logging.info(f"Webtoon image uploaded to S3: {s3_url}")
                        results.append({"scenario": scene, "image": s3_url})
                        # 로컬 파일 삭제
                        os.remove(local_image_path)
                        logging.info(f"Local file {local_image_path} deleted after successful upload.")
                    else:
                        logging.error(f"Failed to upload webtoon image {j} for scenario {i} to S3.")
                else:
                    logging.error(f"Failed to download image from {image_url}")

        # 결과를 POST 요청으로 다른 서비스에 전송
        result_data = {
            "memberId": memberId,
            "date": date,
            "webtoonFolderUrl": f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{DEFAULT_PATH}{memberId}/{date}/",
            "webtoonImages": results
        }
        try:
            webhook_url = f"http://{apiDomainUrl}/api/v1/webhook/ai/webtoon"  # 수정된 부분
            response = requests.post(webhook_url, json=result_data)  # 수정된 부분
            # response = requests.post("http://localhost:8080/api/v1/webhook/ai/webtoon", json=result_data)
            if response.status_code == 200:
                logging.info("Webtoon data successfully posted")
            else:
                logging.error(f"Failed to post webtoon data. Status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error while posting webtoon data: {e}")

    except Exception as e:
        logging.error(f"Error in process_webtoon_background: {e}")

@app.post('/character', summary="프로필 이미지 처리", description="사용자의 프로필 이미지를 처리하고 S3에 업로드합니다.")
async def process_profile(
    memberId: str = Form(...),
    characterStyle: str = Form(...),
    userImage: UploadFile = File(...),
    apiDomainUrl: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    try:
        logging.info(f"Received /ai/character request for memberId: {memberId}")
        # 파일 저장 경로 설정 및 저장
        file_path = os.path.join(UPLOAD_FOLDER, userImage.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await userImage.read())
        logging.info(f"File saved to {file_path}")

        # 백그라운드 작업 실행
        background_tasks.add_task(process_profile_background, memberId, file_path, characterStyle, apiDomainUrl)

        return {"message": "Profile processing started"}
    except Exception as e:
        logging.error(f"Error in /ai/character endpoint: {e}")
        return {"message": "Failed to start profile processing"}

@app.post('/webtoon', summary="웹툰 생성", description="웹툰을 생성하고 S3에 업로드합니다.")
async def process_webtoon(
    memberId: str = Body(...),  # int -> str
    date: str = Body(...),
    content: str = Body(...),
    characterInfo: str = Body(...),
    seedNum: int = Body(...),
    characterStyle: str = Body(...),
    apiDomainUrl: str = Body(...),
    background_tasks: BackgroundTasks = None
):
    try:
        logging.info(f"Received /ai/webtoon request for memberId: {memberId}, date: {date}")
        # 로그 남기기
        logging.info(f"Received parameters: memberId={memberId}, date={date}, content={content}, "
                     f"characterInfo={characterInfo}, seedNum={seedNum}, characterStyle={characterStyle}")

        # 백그라운드 작업 실행
        background_tasks.add_task(process_webtoon_background, memberId, date, content, characterInfo, seedNum, characterStyle, apiDomainUrl)

        return {"message": "Webtoon processing started"}
    except Exception as e:
        logging.error(f"Error in /ai/webtoon endpoint: {e}")
        return {"message": "Failed to start webtoon processing"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5001))
    uvicorn.run(app, host=host, port=port, log_level="info")