from openai import OpenAI

# 🔑 ВСТАВЬ СВОЙ КЛЮЧ СЮДА
API_KEY = "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"

client = OpenAI(api_key=API_KEY)


def explain_code(code: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Ты объясняешь Python-код простым и понятным языком, как учитель."
            },
            {
                "role": "user",
                "content": f"Объясни этот Python-код:\n\n{code}"
            }
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content
