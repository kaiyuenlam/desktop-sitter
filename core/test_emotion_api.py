import cv2
import sys
import requests

def capture_image():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Failed to open camera")
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise RuntimeError("Failed to capture image")

    # Encode the image to JPEG format
    ret, buf = cv2.imencode('.jpg', frame)
    if not ret:
        raise RuntimeError("Failed to encode image")
    
    return buf.tobytes()

def send_image_to_api(api_url, image_bytes):
    endpoint = f"{api_url}/emotion"
    headers = {'Content-Type': 'application/octet-stream'}
    
    try:
        response = requests.post(endpoint, headers=headers, data=image_bytes)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_emotion_api.py <API_PUBLIC_URL>")
        sys.exit(1)

    api_url = sys.argv[1]
    
    try:
        image_bytes = capture_image()
        result = send_image_to_api(api_url, image_bytes)
        print("API Response:")
        print(result)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
