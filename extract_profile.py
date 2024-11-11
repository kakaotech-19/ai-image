from dotenv import load_dotenv
import os
from openai import OpenAI
import logging

# 로컬 개발 환경에서만 .env 파일을 로드
dotenv_path = 'keys.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logging.info(f".env 파일({dotenv_path})을 성공적으로 로드했습니다.")
else:
    logging.info(f".env 파일({dotenv_path})이 존재하지 않습니다. 환경 변수를 직접 설정합니다.")

# 환경 변수 로드
OPENAI_KEY = os.getenv('OPENAI_KEY')

if not OPENAI_KEY:
    logging.error("OPENAI_KEY가 설정되지 않았습니다. 환경 변수를 확인하세요.")
    raise ValueError("OPENAI_KEY is not set. Please set it in the environment variables.")

# OpenAI 클라이언트 생성
client = OpenAI(
    api_key=OPENAI_KEY
)


def get_gpt_response(user_id, user_img):
    prompt = (
        "You are responsible for extracting features from the user's photos.\n"
        "The data you extracted is used to create a 2D character profile picture through the RoLA model.\n"
        "Please extract the user's image and make the data with JSON format.\n"
        "In particular, extract detailed data on hairstyles(length, style, color, bang, etc).\n"
        "If characters are wearing glasses, extract the type of glasses(color, shape, etc).\n"
        "#Don't extract information that changes every time(ex: clothes, emotion, back_ground, ect.)\n"
        "#Don't extract unspecified information"
    )

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages =[
            {
                'role': 'system',
                'content': prompt
            },
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image_url',
                        'image_url': {
                            "url": f"data:image/webp;base64, {user_img}"
                        }
                    }
                ] ,
            }
        ],
        max_tokens=1000,
        temperature = 0.5,
    )
    gpt = response.choices[0].message.content
    return user_id, gpt
