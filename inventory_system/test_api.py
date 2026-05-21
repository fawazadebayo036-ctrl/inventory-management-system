
from google import genai

client = genai.Client(api_key="AIzaSyBi0_Tjy3HatbbyCNkypuRla2JP3Murl00")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say hello"
)

print(response.text)