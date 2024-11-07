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


def get_gpt_response(user_id, diary_text):
    prompt = (
        "You are responsible for making the user's diary into a FOUR-SCENE scenario.\n"
        "I will draw a cartoon with the scene information you made.\n"
        "Use a way of describing the scene, not the content.\n"
        "Describe the background and scene simply.\n"
        "#Be careful not to let other people come out when you describe the situation.(Don't use 'they', 'friends', etc)\n"
        "#Not an incidental depiction, but a scene\n"
        "DON\'T USE MARKDOWN"
        "[user\'s diary]\n"
        f"\t{diary_text}"
        "[output]\n"
        "\tscene: \n"
        "\tbackground: \n"
    )
    scenario = []
    message = [
            {
                'role': 'system',
                'content': prompt
            },
            {
                'role': 'user',
                'content': 'make scene 1'
            }
        ]
    for scene in range(1, 5):  # Adjusted to start from 1 since 'scene 1' is already in messages
        try:
            response = client.chat.completions.create(
                model='gpt-4o-mini',  # Check if the model name is correct
                messages=message,
                max_tokens=1000,
                temperature=0.5,
            )
            context = response.choices[0].message.content.strip()  # Clean the response
            scenario.append(context)
            message.append({'role': 'assistant', 'content': context})
            if scene < 4:  # Avoid unnecessary 'user' prompts after the last scene
                message.append({'role': 'user', 'content': f'make scene {scene + 1}'})
        except Exception as e:
            print(f"An error occurred: {e}")
            scenario.append("Error generating scene.")  # Handle error gracefully
            break

    return user_id, scenario