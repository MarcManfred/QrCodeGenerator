from colormap import hex2rgb
from qrcode.main import QRCode
import qrcode.constants
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import CircleModuleDrawer


class QrCodeGenerator:

    def __init__(
            self,
            url: str,
            image_path: str | None = None,
            qr_color: str | None = None):

        self._url = url
        self._image_path = image_path
        self._qr_color = "#000000" if qr_color is None else qr_color

    def create_round_qr(self, image):
        width, height = image.size
        left = 0
        top = height // 3
        right = width
        bottom = 2 * height // 3

        cropped_section = image.crop((left, top, right, bottom))
        rotated_crop = cropped_section.copy()
        rotated_crop = rotated_crop.rotate(90, expand=True)

        # fill top
        image.paste(cropped_section, (0, -cropped_section.size[1] // 2 + 20))
        # fill bottom
        image.paste(cropped_section,
                    (0, image.size[1] - cropped_section.size[1] // 2 - 20))
        # fill left
        image.paste(rotated_crop, (-rotated_crop.size[0] // 2 + 20, 0))
        # fill right
        image.paste(
            rotated_crop, (image.size[0] - rotated_crop.size[0] // 2 - 20, 0))

        # draw round border for qr code
        draw = ImageDraw.Draw(image)
        draw.ellipse(
            (30, 30, image.size[1] - 30, image.size[1] - 30),
            fill=None,
            outline='black'
        )

        # draw outside mask ring
        draw.ellipse(
            (-rotated_crop.size[0],
             -cropped_section.size[1],
             image.size[1] + rotated_crop.size[0],
             image.size[1] + cropped_section.size[1]
             ),
            fill=None,
            outline='white',
            width=340
        )
        return image

    def insert_logo(self, qr_image):
        # open image from path
        logo = Image.open(self._image_path)

        # basewidth of the image
        base_width = 300

        # image size
        w_percent = (base_width / float(logo.size[0]))
        hsize = int(float(logo.size[1]) * float(w_percent))
        logo = logo.resize((base_width, hsize), Image.Resampling.LANCZOS)

        # insert image
        pos = ((qr_image.size[0] - logo.size[0]) // 2,
               (qr_image.size[1] - logo.size[1]) // 2)
        qr_image.alpha_composite(logo.convert('RGBA'), pos)

        return qr_image

    def generate_code(self):
        qr_code = QRCode(
            version=10,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=18,
            mask_pattern=4
        )

        # adding URL to QR-code
        qr_code.add_data(self._url)

        # generating the QR code
        qr_code.make()
        # adding color to QR code
        qr_img = qr_code.make_image(
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer(resample_Method=None),
            color_mask=SolidFillColorMask(back_color=hex2rgb(
                "#ffffff"), front_color=hex2rgb(self._qr_color))
        ).convert('RGBA')

        qr_img = self.create_round_qr(image=qr_img)

        if self._image_path is not None:
            qr_img = self.insert_logo(qr_img)

        return qr_img

# code_generator = QrCodeGenerator(url="www.Kodols.net")
