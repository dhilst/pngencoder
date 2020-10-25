import os
import sys
from typing import *
from typing import BinaryIO
from typing_extensions import *  # type: ignore
from itertools import product
import argparse
import tempfile

import requests
from PIL import Image, ImageDraw  # type: ignore


def download_image(url: str) -> str:
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as fil:
        fil.write(requests.get(args.image).content)
        return fil.name


def encode(args: argparse.Namespace):
    if args.from_url:
        args.image = download_image(args.image)

    img = Image.open(args.image)
    output_img = Image.new("RGB", img.size)
    if args.input_data:
        data = args.input_data
        datab = data.encode("utf8")
        datalen = len(data)
    elif args.input_file:
        datab = args.input_file.read()
        datalen = os.stat(args.input_file.name).st_size

    if datalen > img.height * img.width:
        raise Exception("Input data is too large, you need an bigger image or split your input")

    i = 0
    j = 0
    bits = 2
    point: Tuple[int, int]
    for point in product(range(img.width), range(img.height)):
        r, g, b, *a = img.getpixel(point)
        x, y = point
        if i < datalen:
            if x == 0 and y in (0, 1, 2, 3):
                # encode length
                b = datalen >> y * 8
            else:
                d = (datab[i] >> j) & 0b11
                b = b & ~0b11 | d
                j += 2
                if j >= 8:
                    i += 1
                    j = 0
        output_img.putpixel(point, (r, g, b))
    output_img.save(args.output_path, "PNG")


def decode(args):
    if args.from_url:
        args.image = download_image(args.image)

    img = Image.open(args.image)

    data_size: int = 0
    if args.output_path:
        data = open(args.output_path, "wb")
    else:
        data = bytearray()
    i = 0
    j = 0
    bits = 2
    byteread = 0
    for point in product(range(img.width), range(img.height)):
        r, g, b = img.getpixel(point)
        x, y = point
        if x == 0 and y in (0, 1, 2, 3):
            data_size |= b << y * 8
        elif i < data_size:
            d = b & 0b11
            byteread = byteread | (d << j)
            j += 2
            if j >= 8:
                j = 0
                if args.output_path:
                    data.write(bytes([byteread]))
                else:
                    data.append(byteread)
                byteread = 0
                i += 1
        else:
            break
    if not args.output_path:
        print(data.decode("utf8"))


def main() -> None:
    argparser = argparse.ArgumentParser("Encode data in PNG images")
    argparser.add_argument("image", type=str, metavar="image", help="Input image")
    argparser.add_argument("--encode", action="store_true", help="Encode data")
    argparser.add_argument("--input-data", type=str, help="Input data as string")
    argparser.add_argument(
        "--input-file", type=argparse.FileType("rb"), help="Input data as file"
    )
    argparser.add_argument("--decode", action="store_true", help="Decode data")
    argparser.add_argument(
        "--output-path", type=str, help="Output image path"
    )
    argparser.add_argument("--from-url", action="store_true", help="Input is an URL")

    args = argparser.parse_args()
    if args.encode:
        encode(args)
    elif args.decode:
        decode(args)


if __name__ == "__main__":
    main()
