import replicate
import os
import time
from dotenv import load_dotenv
import logging

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
model_type = "tpals0409/romance-webtoon-character"
version_type = "64ad94c7f1fe7cfe73ee7b3d0f7deae8a59d201689eb12d07f74baa9325949e0"

def create_webtoon(user_id, character_info, seed_num, scene_info):
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
        "seed": seed_num,
        "prompt": "Make a cartoon scene using character information and scene information.\n"+
                   "Don't draw anyone other than the main character.\n"+
                   "[character_info]\n"+
                   f"{character_info}\n"+
                   "[scene]\n"+
                   f"{scene_info}\n"
    }
    prediction = replicate.predictions.create(
        version=version,
        input=prompt
    )
    while prediction.status not in ["succeeded", "failed", "canceled"]:
        time.sleep(5)
        prediction.reload()

    return prediction.output
