document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("detectEmotion").addEventListener("click", function () {
        let textInput = document.getElementById("textInput").value.trim();
        let resultDiv = document.getElementById("result");

        resultDiv.innerHTML = "Analyzing...";

        if (!textInput) {
            resultDiv.innerHTML = "<span style='color: red;'>Please enter text.</span>";
            return;
        }

        fetch("http://127.0.0.1:5000/detect_test_emotion", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: textInput })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                resultDiv.innerHTML = `<span style='color: red;'>${data.error}</span>`;
            } else {
                let dominantEmotion = data.Dominant_emotion.label;
                let dominantScore = (data.Dominant_emotion.score * 100).toFixed(2) + "%";
                
                let analysisHTML = `<strong>Dominant Emotion:</strong> ${dominantEmotion} (${dominantScore})<br><br><strong>Emotion Analysis:</strong><br>`;
                
                data["Emotion Analysis"].forEach(emotion => {
                    analysisHTML += `${emotion.label}: ${(emotion.score * 100).toFixed(2)}%<br>`;
                });

                resultDiv.innerHTML = analysisHTML;
            }
        })
        .catch(error => {
            resultDiv.innerHTML = "<span style='color: red;'>Error processing request.</span>";
            console.error("Error:", error);
        });
    });
});
