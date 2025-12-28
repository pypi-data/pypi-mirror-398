import requests

def text(api, model, prompt):
    url = "https://api.openai.com/v1/chat/completions"

    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        },
)
    data = r.json()
    print(data["choices"][0]["message"]["content"])

def image(api, model, text, size):
    url = "https://api.openai.com/v1/images/generations"
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "prompt": text,
            "n": 1,
            "size": size
        },
)
    print(r.json()["data"][0]["url"])