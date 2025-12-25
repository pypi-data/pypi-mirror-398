#!/usr/bin/env python3

import cv2 as cv
from matplotlib import pyplot as plt

from visioncube import TransformPipeline


def main():
    path = '/data/cat.jpg'
    image = cv.imread(path, cv.IMREAD_COLOR)
    image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

    pipeline = TransformPipeline('test_image_transforms.yml', training=False, device='gpu')

    plt.subplot(3, 3, 1)
    plt.imshow(image)
    for i in range(8):
        plt.subplot(3, 3, i + 2)
        image1 = pipeline({'image': image})['image']
        plt.imshow(image1)
    plt.show()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
