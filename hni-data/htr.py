from flask import Flask, request, jsonify
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import io

app = Flask(__name__)

# Load the processor and model (changed to a general handwritten model)
processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')

@app.route('/transcribe', methods=['POST'])
def transcribe_image():
    try:
        # Check if an image file is included in the request
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Read and process the image
        image = Image.open(file.stream).convert('RGB')
        pixel_values = processor(images=image, return_tensors="pt").pixel_values

        # Generate transcription with beam search for better accuracy
        generated_ids = model.generate(pixel_values, max_length=512, num_beams=4, early_stopping=True)
        transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return jsonify({'transcription': transcription})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
