import google.generativeai as genai

genai.configure(api_key="AIzaSyD_JUtNlEQcjjSp9XlSrQKAy4OMBRl9N5g")
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Explain how AI works")
print(response.text)