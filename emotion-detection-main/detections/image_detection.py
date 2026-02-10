import base64
import numpy as np
from io import BytesIO
from deepface import DeepFace
from PIL import Image
from flask import request

def process_image(file=None):
    try:
        if file:  # If file is uploaded
            image = Image.open(file)
        else:  # If Base64 image is sent (from Camera)
            data = request.json["image_base64"]
            image_data = base64.b64decode(data.split(",")[1])
            image = Image.open(BytesIO(image_data))

        # Convert image to NumPy array for DeepFace
        image_np = np.array(image)

        # Encode image properly for frontend
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")  # ✅ FIXED

        # Perform Emotion Detection
        result = DeepFace.analyze(img_path=image_np, actions=['emotion'], enforce_detection=False)
        detected_emotion = result[0]['dominant_emotion']

        return {"emotion": detected_emotion, "image_base64": f"data:image/jpeg;base64,{img_str}"}
    
    except Exception as e:
        return {"error": str(e)}
