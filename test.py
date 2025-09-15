import os
print(os.environ)
api_key = os.environ.get("GOOGLE_API_KEY")

if api_key:
    print("API Key:", api_key)
else:
    print("API Key not found.")