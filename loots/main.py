from openai import OpenAI
from dotenv import load_dotenv
from loots.models import Loot
import json
import os

load_dotenv()

system_prompt = """ 
I will provide an image of a loot table. Extract the text from the image, parse it, 
and identify the item names along with their respective quantities. 
The output should strictly be in JSON format as a list of dictionaries, 
where each dictionary contains two keys: 'item' (the name of the item) and 'quantity' (the corresponding quantity). 
For example: [{'item': 'Rune Ticket', 'quantity': 120}]. 
Do not include any additional information or commentary in the response, only the JSON output.

"""

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(
    api_key=os.environ.get(OPENAI_API_KEY),
)


def upload_image_and_get_cv(image_url: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url},
                    },
                ],
            }
        ],
    )

    return response.choices[0].message.content


def parse_cv_result_into_loots(message_content: str) -> list[Loot]:
    message_cleaned = message_content.strip('"').strip("```json\n").strip("\n```")
    message_unescaped = message_cleaned.encode().decode("unicode_escape")
    list_of_items = json.loads(message_unescaped)
    return [Loot(**item) for item in list_of_items]


# image_url = "https://media.discordapp.net/attachments/1266823873693880350/1314551692221743124/IMG_0377.png?ex=67542f2a&is=6752ddaa&hm=ac285325838159f3b73ff9635d4885a8346327cf9e150ffdea4f7a8976a5672b&=&format=webp&quality=lossless&width=400&height=560"
# res = upload_image_and_get_cv(image_url)
# res_2 = parse_cv_result_into_loots(res)
