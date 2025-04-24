"""
emotion_api.py  –  Cloud AI Analysis module
Provides a simple interface to send image bytes to the emotion API and retrieve the JSON response.
Read the ngrok public URL from url.txt.
"""
import os
import requests


def read_api_url(filepath: str = 'url.txt') -> str:
    """
    Read the API base URL from a text file.
    Expects the file to contain the URL on the first line.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"URL file not found: {filepath}")
    with open(filepath, 'r') as f:
        url = f.readline().strip()
    if not url:
        raise ValueError(f"Empty URL in {filepath}")
    return url.rstrip('/')


def send_image_to_api(image_bytes: bytes) -> dict:
    """
    Send the given JPEG image bytes to the emotion API and return the parsed JSON response.

    Returns a dict with at least a "status" key ("ok", "reinit_required", "error").
    """
    api_url = read_api_url()
    endpoint = f"{api_url}/emotion"
    headers = {'Content-Type': 'application/octet-stream'}
    try:
        resp = requests.post(endpoint, headers=headers, data=image_bytes, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"status": "error", "error": str(e)}


# Optional: standalone test entrypoint
if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 emotion_api.py <path_to_image.jpg>")
        exit(1)
    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(f"Image file not found: {img_path}")
        exit(1)
    with open(img_path, 'rb') as f:
        img_bytes = f.read()
    response = send_image_to_api(img_bytes)
    print(response)
