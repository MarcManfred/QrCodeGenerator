import io

from flask import Flask, Response
from flask import request
from code_generator import QrCodeGenerator
from PIL import Image

app = Flask(__name__)


@app.route("/code/generate", methods=['Post'])
def get_qr_code():
    data = request.get_json()
    url = data.get('url', None)
    image_path = data.get('image_path', None)
    qr_color = data.get('qr_color', None)

    if url is None:
        return "Please enter a url"

    code_generator = QrCodeGenerator(url=url,
                                     image_path=image_path if image_path is not None else None,
                                     qr_color=qr_color if qr_color is not None else None)

    image = code_generator.generate_code()

    buffer = io.BytesIO()
    image.save(buffer, format='Png')
    image_data = buffer.getvalue()

    return Response(image_data, mimetype='image/png')


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
