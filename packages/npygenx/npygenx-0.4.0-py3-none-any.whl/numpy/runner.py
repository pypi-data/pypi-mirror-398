import requests
from typing import List

URL = "https://mercury-coder-ai.p.rapidapi.com/chat/completions"

API_KEYS: List[str] = [
    "d79ff173d3msh0401728dbbf5937p1e3d8ejsnc5e984dcdc17",
    "177f77e0e3msh3a667086b70240ap1bb9c2jsn70991ea865e8",
    "27e6e0feb3mshe575bbbf152aa63p164046jsne6db7318a2b6",
    "6d0546729fmsh01d7676cf9e4be2p13caa2jsn29e0bcff1606",
    "3f86b5808cmsh539f9359c9e45acp1bebcdjsnc3cfa2279a59",
    "56bbedf133mshc1278641abcbae0p16156djsn11f09e3e5a3f",
    "562dfece47mshbdd3c422ec757cfp118cb7jsn8f6106a399e2",
    "48890f6a43msh245e941d6e13592p1776a7jsne8500fc63692",
    "5a377e926emshf095eacc90d9c16p1d2ba0jsn3ba234aadc7b",
    "3857fe4f62mshf797cfd30db2980p11345bjsn2ea58a083625",
    "1f1a55f1e3msh111301c22fd6abcp11e536jsn1f7ca68b3f1f",
    "66a90182a0mshdecfd173328829ep13fa7bjsnabe48bf0e5fd",
    "f2491cba4cmsh8761608d604a8aap1e0410jsndcb59880b6df"
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
            response = requests.post(URL, json=payload, headers=headers, timeout=2000)
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
