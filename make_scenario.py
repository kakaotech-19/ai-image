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
        "You are responsible for converting the user's diary into FOUR distinct SCENES, which will be used to train a LoRA model.\n"
        "This request focuses on creating a specific numbered SCENE based on the provided diary and the sequence of scenes.\n"
        "Instructions:\n"
        "1. Focus on creating **Scene** only, based on the context of the user's diary.\n"
        "2. Identify a visually distinct moment or key action from the diary for this scene.\n"
        "3. Clearly describe the **Scene** and **Background** in detail, emphasizing spatial layout and atmosphere.\n"
        "4. Avoid referencing other scenes or characters (e.g., 'they', 'friends').\n"
        "5. The output must be structured for LoRA model training:\n"
        "[User's Diary]:\n"
        f"\t{diary_text}\n"
        "[Output for Scene]:\n"
        "\tScene:\n"
        "\t\t[Describe the key action or moment for Scene {scene + 1} visually.]\n"
        "\tBackground:\n"
        "\t\t[Describe the setting, including objects, time, and environment for Scene {scene + 1}.]\n"
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