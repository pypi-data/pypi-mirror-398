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

def apicheck(api):
    checkurl = "https://api.openai.com/v1/chat/completions"
    check = requests.post(
        checkurl,
        headers={
             "Authorization": f"Bearer {api}",
             "Content-Type": "application/json"
             },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "test"}]
        },
)

    if check.status_code == 200:
        print("gptio | Success / Text Service")
    else:
        print("gptio | Unsuccess / Text Service")

    imgcheck = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-image-1",
            "prompt": "test",
            "size": "1024x1024"
        }
    )

    if imgcheck.status_code == 200:
        print("gptio | Success / Image Service")
    else:
        print("gptio | Unsuccess / Image Service")

def send(api, model, text):
    url = "https://api.openai.com/v1/chat/completions"
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": text}]
        },
    )
    datas = r.json()
    return datas["choices"][0]["message"]["content"]