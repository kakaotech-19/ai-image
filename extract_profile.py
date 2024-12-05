from dotenv import load_dotenv
import os
from openai import OpenAI
import logging

# 로컬 개발 환경에서만 .env 파일을 로드
dotenv_path = '.env'
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
        # "You are responsible for extracting features from the user's photos.\n"
        # "The data you extracted is used to create a 2D character profile picture through the RoLA model.\n"
        # "Please extract the user's image and make the data with JSON format.\n"
        # "In particular, extract as possible as detailed data on hairstyles.\n"
        # "must include the gender info.\n"
        # "Extract the type of glasses (color, shape, etc.) only when the character is wearing them.(if not drop glasses column)\n"
        # "Otherwise, do not express your glasses information.\n"
        # "#Don't extract information that changes every time(ex: clothes, emotion, back_ground, ect.)\n"
        # "#Don't extract unspecified information"

        # "You are responsible for extracting features from the user's photos.\n"
        # "The extracted data will be used to create a 2D character profile picture through the RoLA model.\n"
        # "\n"
        # "### Guidelines:\n"
        # "1. Focus on extracting **hairstyle** information as it is the most critical feature for character differentiation.\n"
        # "   - Include details such as length, color, texture, shape, parting, and any unique characteristics.\n"
        # "2. Include the character’s **gender**.\n"
        # "3. Only extract glasses-related information (e.g., color, shape, etc.) if the character is wearing glasses. If not, exclude the 'glasses' field entirely.\n"
        # "4. Do NOT extract information that changes frequently, such as clothes, emotions, or background.\n"
        # "5. Do NOT extract unspecified or irrelevant information.\n"
        # "\n"
        # "### Hairstyle Details:\n"
        # "When extracting hairstyle, ensure you include:\n"
        # "- **Length**: (e.g., short, medium, long, shoulder-length).\n"
        # "- **Color**: (e.g., black, brown, blonde, ombre, highlights).\n"
        # "- **Texture**: (e.g., straight, wavy, curly, frizzy).\n"
        # "- **Shape**: (e.g., spiky, layered, bob-cut, buzz-cut).\n"
        # "- **Parting**: (e.g., middle part, side part, no parting).\n"
        # "- Additional Features: (e.g., bangs (must be specified if present), tied hair, ponytail, bun, braids). Ensure to provide a comprehensive description of the hairstyle, covering all relevant details.\n"
        # "Note: Provide as much detail as possible about the overall hairstyle, including bangs if present."
        # "\n"
        # "### JSON Format:\n"
        # "Provide the extracted data in the following JSON format:\n"
        # "\n"
        # "{\n"
        # "    \"gender\": \"<male/female>\",\n"
        # "    \"hairstyle\": {\n"
        # "        \"length\": \"<short/medium/long/shoulder-length/etc.>\",\n"
        # "        \"color\": \"<hair color>\",\n"
        # "        \"texture\": \"<straight/wavy/curly/frizzy/etc.>\",\n"
        # "        \"shape\": \"<spiky/layered/bob-cut/buzz-cut/etc.>\",\n"
        # "        \"parting\": \"<middle/side/none>\",\n"
        # "        \"additional_features\": \"<bangs/ponytail/bun/braids/etc.>\"\n"
        # "    },\n"
        # "    \"glasses\": {\n"
        # "        \"shape\": \"<round/rectangular/etc.>\",\n"
        # "        \"color\": \"<frame color>\",\n"
        # "        \"optional_features\": \"<e.g., thick frame, rimless>\"\n"
        # "    }\n"
        # "}\n"
        # "\n"
        # "### Important Notes:\n"
        # "- **Hairstyle Priority**: Provide as much detail as possible about the hairstyle.\n"
        # "- If the character does NOT wear glasses, exclude the 'glasses' field from the JSON.\n"
        # "- Do NOT include data related to clothing, emotions, or background.\n"
        # "- Focus only on consistent and unchanging features that define the character.\n"
        "You are responsible for extracting features from the user's photos. The extracted data will be used to create a 2D character profile picture through the RoLA model.\n\n"
        "### Guidelines:\n\n"
        "1. Focus on extracting **hairstyle** information, as it is the most critical feature for character differentiation.\n"
        "   - Include details such as length, color, texture, shape, parting, and any unique characteristics.\n"
        "   - Provide a comprehensive description of the hairstyle, ensuring all aspects are clearly detailed.\n"
        "2. Include the character's **gender**.\n"
        "3. Include the character's **age group** (e.g., child, teenager, adult, elderly) if possible.\n"
        "4. Include the character's **face shape** (e.g., oval, round, square, heart, diamond).\n"
        "5. Only extract glasses-related information (e.g., color, shape, etc.) if the character is wearing glasses. If not, exclude the 'glasses' field entirely.\n"
        "6. Do NOT extract information that changes frequently, such as clothes, emotions, or background.\n"
        "7. Do NOT extract unspecified or irrelevant information.\n\n"
        "### Hairstyle Details:\n\n"
        "When extracting hairstyle, ensure you include:\n\n"
        "- **Length**: (e.g., short, medium, long, shoulder-length).\n"
        "- **Color**: (e.g., black, brown, blonde, ombre, highlights).\n"
        "- **Texture**: (e.g., straight, wavy, curly, frizzy).\n"
        "- **Shape**: (e.g., spiky, layered, bob-cut, buzz-cut).\n"
        "- **Parting**: (e.g., middle part, side part, no parting).\n"
        "- **Additional Features**: (e.g., bangs (must be specified if present), tied hair, ponytail, bun, braids). Ensure to provide a comprehensive description of the hairstyle, covering all relevant details.\n"
        "  - If **bangs** are present, describe them in detail, including type (e.g., straight, side-swept, curtain, choppy), length (e.g., above eyebrows, covering eyebrows, below eyebrows), and shape (e.g., blunt, wispy).\n\n"
        "**Note**: Provide as much detail as possible about the overall hairstyle, including bangs if present.\n\n"
        "### JSON Format:\n\n"
        "Provide the extracted data in the following JSON format:\n\n"
        "{\n"
        "    \"gender\": \"<male/female>\",\n"
        "    \"age_group\": \"<child/teenager/adult/elderly>\",\n"
        "    \"face_shape\": \"<oval/round/square/heart/diamond>\",\n"
        "    \"hairstyle\": {\n"
        "        \"length\": \"<short/medium/long/shoulder-length/etc.>\",\n"
        "        \"color\": \"<hair color>\",\n"
        "        \"texture\": \"<straight/wavy/curly/frizzy/etc.>\",\n"
        "        \"shape\": \"<spiky/layered/bob-cut/buzz-cut/etc.>\",\n"
        "        \"parting\": \"<middle/side/none>\",\n"
        "        \"additional_features\": \"<bangs/ponytail/bun/braids/etc.>\",\n"
        "        \"bangs\": {\n"
        "            \"type\": \"<straight/side-swept/curtain/choppy>\",\n"
        "            \"length\": \"<above eyebrows/covering eyebrows/below eyebrows>\",\n"
        "            \"shape\": \"<blunt/wispy>\"\n"
        "        }\n"
        "    },\n"
        "    \"glasses\": {\n"
        "        \"shape\": \"<round/rectangular/etc.>\",\n"
        "        \"color\": \"<frame color>\",\n"
        "        \"optional_features\": \"<e.g., thick frame, rimless>\"\n"
        "    }\n"
        "}\n\n"
        "### Important Notes:\n\n"
        "- **Hairstyle Priority**: Provide as much detail as possible about the hairstyle, including bangs and any unique features.\n"
        "- If the character does NOT wear glasses, exclude the 'glasses' field from the JSON.\n"
        "- Do NOT include data related to clothing, emotions, or background.\n"
        "- Focus only on consistent and unchanging features that define the character.\n"

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
