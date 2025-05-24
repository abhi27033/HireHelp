import requests, fitz, os, json

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def parse_resume(pdf_path):
    url = "https://emsiservices.com/skills/versions/latest/extract"
    auth_url = "https://auth.emsicloud.com/connect/token"
    payload = {
        "client_id": "hlslf2pxdiyjncuo",
        "client_secret": "R8iK5f97",
        "grant_type": "client_credentials",
        "scope": "emsi_open"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(auth_url, data=payload, headers=headers)
    access_token = ''

    if response.status_code == 200:
        response_data = response.json()
        access_token = response_data.get('access_token')
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    resume_text = extract_text_from_pdf(pdf_path).lower()
    payload = {
        "text": resume_text,
        "confidenceThreshold": 0.8
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    skills = response.json().get('data', [])
    skills_json = []

    for skill in skills:
        skill_name = skill['skill']['name']
        skills_json.append(skill_name)

    return skills_json
    