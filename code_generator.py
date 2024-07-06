import argparse
import csv
import io
from multiprocessing import Pool
import os
import sys

from colormap import hex2rgb
import qrcode
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import CircleModuleDrawer


EMBEDDED_IMAGE_SIZE = 200

class QrCodeGenerator:

    def __init__(
                self,
                url: str = '',
                image_path: str = None,
                qr_color: str = None):

        self.__url = url
        self.__image_path = image_path
        self.__qr_color = "#000000" if qr_color is None else qr_color

    def __create_round_qr(self, image):
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
        image.paste(cropped_section, (0, image.size[1] - cropped_section.size[1] // 2 - 20))
        # fill left
        image.paste(rotated_crop, (-rotated_crop.size[0] // 2 + 20, 0))
        # fill right
        image.paste(rotated_crop, (image.size[0] - rotated_crop.size[0] // 2 - 20, 0))

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

    def __insert_logo(self, qr_image):
        # open image from path
        logo = Image.open(self.__image_path)

        # basewidth of the image
        base_width = EMBEDDED_IMAGE_SIZE

        # image size
        w_percent = (base_width / float(logo.size[0]))
        hsize = int(float(logo.size[1]) * float(w_percent))
        logo = logo.resize((base_width, hsize), Image.LANCZOS)

        # insert image
        pos = ((qr_image.size[0] - logo.size[0]) // 2,
               (qr_image.size[1] - logo.size[1]) // 2)
        qr_image.alpha_composite(logo.convert('RGBA'), pos)

        return qr_image

    def generate_code(self, url=''):
        url = url if url else self.__url
        if not url:
            raise RuntimeError('Cannot generate QR code without a URL')
        qr_code = qrcode.QRCode(
            version=10,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=18,
            mask_pattern=4
        )

        # adding URL to QR-code
        qr_code.add_data(url)

        # generating the QR code
        qr_code.make()
        # adding color to QR code
        qr_img = qr_code.make_image(
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer(resample_Method=None),
            color_mask=SolidFillColorMask(back_color=hex2rgb("#ffffff"),
                                          front_color=hex2rgb(self.__qr_color))
        ).convert('RGBA')

        qr_img = self.__create_round_qr(image=qr_img)

        if self.__image_path is not None:
            qr_img = self.__insert_logo(qr_img)

        return qr_img


def generate_single_qr(url, image_path, color, qr_filename) -> None:
    """Save a single QR image to a file."""
    gen = QrCodeGenerator(url, image_path, color)
    gen.generate_code().save(qr_filename)

def generate_multiple_qrs(urls_csv, image_path, color, output_path) -> None:
    """Generate a QR image for each url in the given CSV filename."""
    # generator = QrCodeGenerator(image_path=image_path, qr_color=color)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    with open(urls_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header

        with Pool(processes=os.cpu_count()) as pool:  # use all cores
            for row in reader:
                url, filename = row
                print(f'generating QR for {url} in {output_path}/{filename}')
                pool.apply_async(generate_single_qr, (
                    url,
                    image_path,
                    color,
                    os.path.join(output_path, filename)))
            pool.close()
            pool.join()


def main():
    """Create QR codes from the command-line."""
    parser = argparse.ArgumentParser(
        description='Create QR codes from the command-line.',
        formatter_class=argparse.RawTextHelpFormatter)
    url_group = parser.add_mutually_exclusive_group(required=True)
    url_group.add_argument(
        '--url',
        type=str,
        help='The URL to generate a QR code for.')
    url_group.add_argument(
        '--urls',
        metavar='PATH',
        type=str,
        help='The path to a CSV file containing URLS and output paths.')
    parser.add_argument(
        '--outdir',
        type=str,
        default='out',
        help=('The output directory to save the generated QR codes to. '
              'Default: out.'))
    parser.add_argument(
        '-o',
        '--outfile',
        type=str,
        default='qr.png',
        help=('The filename of the generated QR code. '
              'Default: qr.png.\n'
              'Ignored when the URLs are read from a CSV file.'))
    parser.add_argument(
        '-i',
        '--image',
        type=str,
        default=None,
        help=('Image to place in the middle of the generated QR code. '
              'Default: None'))
    parser.add_argument(
        '-c',
        '--color',
        type=str,
        default='#000000',
        help='The color of the QR code. Default: #000000')
    args = parser.parse_args()

    if args.url:
        generate_single_qr(url=args.url, image_path=args.image,
            color=args.color,
            qr_filename=os.path.join(args.outdir, args.outfile))
    else:
        generate_multiple_qrs(args.urls, image_path=args.image,
            color=args.color, output_path=args.outdir)


if __name__ == '__main__':
    sys.exit(main())
