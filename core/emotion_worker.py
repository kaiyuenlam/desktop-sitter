"""
emotion_worker.py
=================
Background thread that

1. receives (full‑res BGR frame, face‑rect) via q_in
2. crops the face, runs DeepFace → dominant emotion
3. queries Hugging‑Face BlenderBot with a Desk‑Sitter‑specific prompt
4. returns (emotion, chatbot_reply) via q_out

External deps:
    pip install deepface requests python-dotenv
"""

import threading, queue, time, cv2, os, tempfile, requests
from deepface import DeepFace
from dotenv import load_dotenv

# ------------------------------------------------------------
# Environment / API config
# ------------------------------------------------------------
load_dotenv()                                       # reads .env
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
HF_API_KEY = os.getenv("HF_API_KEY")
if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY missing. Add it to .env")

HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json",
}

# ------------------------------------------------------------
# Desk‑Sitter prompt template
# ------------------------------------------------------------
PROMPT_TEMPLATE = (
    "You are **Desktop‑Sitter**, a tiny desk companion robot that keeps me company "
    "while I work. You speak in a warm, first‑person tone using ONE or TWO short "
    "sentences. I'm currently showing a **{emotion}** expression. "
    "Offer a friendly comment or suggestion that will help me stay productive "
    "and healthy at my computer. Avoid mentioning facial analysis, cameras, or emotions directly."
)

# ------------------------------------------------------------
class EmotionWorker(threading.Thread):
    """
    In  : q_in.put_nowait((bgr_frame, (x,y,w,h)))
    Out : q_out.put((dominant_emotion, chatbot_reply))
    """

    def __init__(self, cooldown=10):
        super().__init__(daemon=True)
        self.q_in  = queue.Queue(maxsize=5)
        self.q_out = queue.Queue(maxsize=5)
        self._last_call = 0
        self.cooldown = cooldown  # minimum seconds between analyses

    # ---------------- private helpers -----------------------
    @staticmethod
    def _deepface_emotion(face_bgr: "np.ndarray") -> str:
        """Return 'happy', 'sad', ...  (fallback='neutral')."""
        # save to temp file because DeepFace prefers file path
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            cv2.imwrite(tmp.name, face_bgr)
            img_path = tmp.name
        try:
            res = DeepFace.analyze(img_path=img_path,
                                   actions=['emotion'],
                                   enforce_detection=False,
                                   detector_backend='opencv')
            if isinstance(res, list):
                res = res[0]
            return res.get('dominant_emotion', 'neutral')
        finally:
            os.remove(img_path)

    @staticmethod
    def _chatbot_reply(emotion: str) -> str:
        """Call Hugging‑Face endpoint with project‑specific prompt."""
        prompt = PROMPT_TEMPLATE.format(emotion=emotion)
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 70,
                "temperature": 0.7,
                "top_p": 0.9,
                "num_return_sequences": 1,
            },
        }
        r = requests.post(HF_API_URL, headers=HEADERS, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()
        return "I'm here if you need me!"

    # ---------------- thread loop ---------------------------
    def run(self):
        while True:
            frame, rect = self.q_in.get()          # blocks
            if time.time() - self._last_call < self.cooldown:
                continue                           # throttle analyses
            x, y, w, h = rect
            face_roi = frame[y:y + h, x:x + w]

            try:
                emotion = self._deepface_emotion(face_roi)
                reply   = self._chatbot_reply(emotion)
                self.q_out.put((emotion, reply))
                self._last_call = time.time()
            except Exception as e:
                # Still put something so main thread knows we finished
                self.q_out.put(("neutral", f"[error] {e}"))
