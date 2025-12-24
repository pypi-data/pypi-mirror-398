import requests
from typing import List

URL = "https://mercury-coder-ai.p.rapidapi.com/chat/completions"

API_KEYS: List[str] = [
    "a74bf07708mshe2753096dd4b303p130c57jsn6e957211b926",
    "KEY_2_HERE",
    "KEY_3_HERE",
]

SYSTEM_PROMPT = """
You are a coding assistant specialized in Genetic algorithms. Rules:
1. Return ONLY valid Python code.
2. Do not use Markdown formatting (no ```python).
3. Do not include explanations.
4. Import all necessary libraries (especially numpy).
5. The solution must use a Genetic Algorithm approach.
"""

def fitness(user_prompt: str, output_file: str = "solution.py") -> str:
    payload = {
        "model": "mercury-coder",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }

    last_error = None

    for key in API_KEYS:
        headers = {
            "x-rapidapi-key": key,
            "x-rapidapi-host": "mercury-coder-ai.p.rapidapi.com",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(URL, json=payload, headers=headers, timeout=20)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            print(content)
            return content

        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All API keys failed. Last error: {last_error}")
