import unittest
from unittest.mock import patch
from io import BytesIO
from werkzeug.datastructures import FileStorage
from detections.detection import detect_text_emotion
from detections.image_detection import process_image
from detections.video_detection import process_video

class TestTextEmotionDetection(unittest.TestCase):
    def test_happy_text(self):
        result = detect_text_emotion("I am feeling great today")
        self.assertEqual(result[0]['Dominant_emotion']['label'], "joy")

class TestImageEmotionDetection(unittest.TestCase):
    def test_valid_image_path(self):
        result = process_image("sample_happy_face.jpg")  # Replace with an actual image file in your project
        self.assertIn("emotion", result)
        self.assertEqual(result["emotion"], "happy")  # Adjust based on actual model behavior

class TestVideoEmotionDetection(unittest.TestCase):

    @patch("detections.video_detection.DeepFace.analyze")
    def test_valid_video_path(self, mock_analyze):
        # Mock DeepFace's analyze return value
        mock_analyze.return_value = [
            {"dominant_emotion": "happy"},
            {"dominant_emotion": "happy"},
            {"dominant_emotion": "neutral"}
        ]

        # Simulate a video file upload
        with open("sample_video.mp4", "rb") as f:
            file_storage = FileStorage(
                stream=BytesIO(f.read()),
                filename="sample_video.mp4",
                content_type="video/mp4"
            )

        result = process_video(file_storage)

        if "error" in result:
            self.fail(f"Video processing failed with error: {result['error']}")
        else:
            self.assertIn("most_common_emotion", result)
            self.assertEqual(result["most_common_emotion"], "happy")
            
if __name__ == "__main__":
    unittest.main()
