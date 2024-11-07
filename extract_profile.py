from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv(dotenv_path= 'keys.env')

client = OpenAI(
    api_key= os.getenv('OPENAI_KEY')
)


def get_gpt_response(user_id, user_img):
    prompt = (
        "You are responsible for extracting features from the user's photos.\n"
        "The data you extracted is used to create a 2D character profile picture through the RoLA model.\n"
        "Please extract the user's image and make the data with JSON format.\n"
        "data format: gender, age(ex: 20s, 30s, 40s, ...), hair, glasses(if yes -> {shape, color} else: don't write ), eyes, mouth, skin-tone"
        "In particular, extract detailed data on hairstyles(length, style, color, bang)\n"
        "#Don't extract information that changes every time(ex: clothes, emotion, back_ground, ect.)\n"
        "#Don't extract information that unknown"
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
