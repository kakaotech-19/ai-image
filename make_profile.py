import replicate
import os
import re
import time
import logging
from dotenv import load_dotenv


# 로컬 개발 환경에서만 .env 파일을 로드
dotenv_path = '.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logging.info(f".env 파일({dotenv_path})을 성공적으로 로드했습니다.")
else:
    logging.info(f".env 파일({dotenv_path})이 존재하지 않습니다. 환경 변수를 직접 설정합니다.")

# 환경 변수 로드
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

if not REPLICATE_API_TOKEN:
    logging.error("REPLICATE_API_TOKEN이 설정되지 않았습니다. 환경 변수를 확인하세요.")
    raise ValueError("REPLICATE_API_TOKEN is not set. Please set it in the environment variables.")

# REPLICATE_API_TOKEN 설정
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# 모델 및 버전 가져오기
models = dict()
models['romance'] = ["tpals0409/romance-webtoon-character", "64ad94c7f1fe7cfe73ee7b3d0f7deae8a59d201689eb12d07f74baa9325949e0"]
models['pixar'] = ["tpals0409/pixar-style", "f4cc445314637e21fcf76fd8330dbf6f2ffc178b10ae035db48c0e6f8c3f0acb"]


# 예측 생성
def create_profile(model_type, version_type, info_profile):
    model = replicate.models.get(model_type)
    version = model.versions.get(version_type)
    prompt = {
            "model": "dev",
            "lora_scale": 1,
            "num_outputs": 1,
            "aspect_ratio": "1:1",
            "guidance_scale": 3.5,
            "output_quality": 70,
            "prompt_strength": 0.8,
            "extra_lora_scale": 1,
            "num_inference_steps": 28,
            "prompt": f"{info_profile}\n" + "a character of the upper body facing the front."
        }
    prediction = replicate.predictions.create(
        version=version,
        input=prompt
    )

    # 예측 상태 확인 및 대기
    while prediction.status not in ["succeeded", "failed", "canceled"]:
        time.sleep(5)
        prediction.reload()

    # 시드 번호 및 출력 URL 추출
    seed_number = None
    if prediction.logs:
        match = re.search(r"Using seed: (\d+)", prediction.logs)
        if match:
            seed_number = match.group(1)

    if not seed_number:
        logging.error("No seed number found in the logs.")

    if not prediction.output:
        logging.error("No output available.")

    # output이 리스트일 경우 첫 번째 요소 반환
    output = prediction.output[0] if isinstance(prediction.output, list) and len(prediction.output) > 0 else None

    return seed_number, output
