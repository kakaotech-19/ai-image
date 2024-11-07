import replicate
import os
import re
import time
import logging
from dotenv import load_dotenv

load_dotenv(dotenv_path= 'keys.env')
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")


# 모델 및 버전 가져오기
model_type = "tpals0409/romance-webtoon-character"
version_type = "64ad94c7f1fe7cfe73ee7b3d0f7deae8a59d201689eb12d07f74baa9325949e0"

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
            "prompt": f"{info_profile}\n" + "a character of the upper body facing the front(clothes: white T-shirt)"
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
