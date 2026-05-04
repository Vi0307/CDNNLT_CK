import json
import urllib.request
import urllib.error

url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=AIzaSyCVn1J5N9tofWG6OkGMwxhDvzn3CXUtEoQ'
data = json.dumps({'contents':[{'parts':[{'text':'Hello'}]}]}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    urllib.request.urlopen(req)
    print("SUCCESS: Key is valid and working!")
except urllib.error.HTTPError as e:
    print(f"ERROR CODE: {e.code}")
    print(f"REASON: {e.reason}")
    print(e.read().decode('utf-8'))
