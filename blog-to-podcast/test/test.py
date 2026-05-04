from google import genai

client = genai.Client(api_key="AIzaSyCVn1J5N9tofWG6OkGMwxhDvzn3CXUtEoQ")

for m in client.models.list():
    print(m.name)
