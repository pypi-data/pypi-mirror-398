#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-06-15
"""
import cv2
from imgaug import augmenters as iaa
from visioncube import rgb_to_gray

from ..common import eval_arg, AbstractTransform, ImgaugAdapter, DEFAULT_IMAGE_FIELD

__all__ = [
    'GaussianBlur',
    'AverageBlur',
    'MedianBlur',
    'BilateralBlur',
    'MotionBlur',
    'RandomGaussianBlur',
    'RandomAverageBlur',
    'RandomMedianBlur',
    'RandomBilateralBlur',
    'RandomMotionBlur',
    'NonLocalMeanBlur',
    'MeanShiftBlur',
    'RandomMeanShiftBlur',
]

ATTRS = [DEFAULT_IMAGE_FIELD]


class GaussianBlur(ImgaugAdapter):

    def __init__(self, sigma: float = 3.0) -> None:
        """GaussianBlur, 高斯滤波, 滤波变换

        Args:
            sigma: Sigma, 标准差, [0.0, 3.0, 0.1], 3.0
        """
        sigma = eval_arg(sigma, None)
        super().__init__(iaa.GaussianBlur(sigma=sigma), ATTRS)


class AverageBlur(ImgaugAdapter):

    def __init__(self, kernel_size: int = 5) -> None:
        """AverageBlur, 均值滤波, 滤波变换

        Args:
            kernel_size: Kernel size, 核数, [1, 7, 1], 5
        """
        kernel_size = eval_arg(kernel_size, int)
        if kernel_size % 2 == 0:
            kernel_size += 1
        super().__init__(iaa.AverageBlur(k=kernel_size), ATTRS)


class MedianBlur(ImgaugAdapter):

    def __init__(self, kernel_size: int = 5):
        """MedianBlur, 中值滤波, 滤波变换

        Args:
            kernel_size: Kernel size, 核数, [1, 7, 1], 5
        """
        kernel_size = eval_arg(kernel_size, int)
        if kernel_size % 2 == 0:
            kernel_size += 1
        super().__init__(iaa.MedianBlur(k=kernel_size), ATTRS)


class BilateralBlur(ImgaugAdapter):

    def __init__(self, d: int = 5, sigma: float = 11.0):
        """BilateralBlur, 双边滤波, 滤波变换

        Args:
            d: Diameter, 直径, [1, 9, 1], 5
            sigma: Sigma, 标准差, (0.0, 100.0, 0.1], 11.0
        """
        d = eval_arg(d, int)
        sigma = eval_arg(sigma, None)
        if d % 2 == 0:
            d += 1
        super().__init__(iaa.BilateralBlur(d=d, sigma_color=sigma, sigma_space=sigma), ATTRS)


class MotionBlur(ImgaugAdapter):
    def __init__(
            self,
            kernel_size: int = 3,
            degree: float = 45.0,
            direction: float = 1.0
    ) -> None:
        """MotionBlur, 物体运动滤波, 滤波变换

        Args:
            kernel_size: Kernel size, 核数, [1, 9, 1], 3
            degree: Rotate angle, 旋转角度, [-180.0, 180.0, 0.1], 45.0
            direction: Direction, 方向, [-1.0, 1.0, 0.1], 1.0
        """
        kernel_size = eval_arg(kernel_size, int)
        degree = eval_arg(degree, None)
        direction = eval_arg(direction, None)

        super().__init__(iaa.MotionBlur(k=kernel_size, angle=degree, direction=direction), ATTRS)


class MeanShiftBlur(ImgaugAdapter):
    def __init__(self, spatial_radius: float = 5.0, color_radius: float = 5.0):
        """MeanShiftBlur, 均值迁移滤波, 滤波变换

        Args:
            spatial_radius: Spatial radius, 空间半径, [5.0, 40.0, 0.1], 5.0
            color_radius: Color radius, 颜色半径, [5.0, 40.0, 0.1], 5.0
        """
        spatial_radius = eval_arg(spatial_radius, None)
        color_radius = eval_arg(color_radius, None)

        super().__init__(iaa.MeanShiftBlur(spatial_radius=spatial_radius,
                                           color_radius=color_radius), ATTRS)


class RandomGaussianBlur(ImgaugAdapter):

    def __init__(
            self,
            sigma_min: float = 0.1,
            sigma_max: float = 3.0
    ) -> None:
        """RandomGaussianBlur, 随机高斯滤波, 滤波变换

        Args:
            sigma_min: Sigma minimum, 标准差最小值, [0.0, 3.0, 0.1], 0.1
            sigma_max: Sigma maximum, 标准差最大值, [0.0, 3.0, 0.1], 3.0
        """
        sigma_min = eval_arg(sigma_min, float)
        sigma_max = eval_arg(sigma_max, float)

        super().__init__(iaa.GaussianBlur(sigma=(sigma_min, sigma_max)), ATTRS)


class RandomAverageBlur(ImgaugAdapter):

    def __init__(self, kernel_size_min: int = 1, kernel_size_max: int = 7) -> None:
        """RandomAverageBlur, 随机均值滤波, 滤波变换

        Args:
            kernel_size_min: Kernel size minimum, 核数最小值, [1, 7, 1], 1
            kernel_size_max: Kernel size maximum, 核数最大值,, [1, 7, 1], 7
        """
        kernel_size_min = eval_arg(kernel_size_min, int)
        kernel_size_max = eval_arg(kernel_size_max, int)

        super().__init__(iaa.AverageBlur(k=(kernel_size_min, kernel_size_max)), ATTRS)


class RandomMedianBlur(ImgaugAdapter):

    def __init__(self, kernel_size_min: int = 1, kernel_size_max: int = 7) -> None:
        """RandomMedianBlur, 随机中值滤波, 滤波变换

        Args:
            kernel_size_min: Kernel size minimum, 核数最小值, [1, 7, 1], 1
            kernel_size_max: Kernel size maximum, 核数最大值,, [1, 7, 1], 7
        """
        k_min = eval_arg(kernel_size_min, int)
        k_max = eval_arg(kernel_size_max, int)

        super().__init__(iaa.MedianBlur(k=(k_min, k_max)), ATTRS)


class RandomBilateralBlur(ImgaugAdapter):

    def __init__(
            self,
            d_min: int = 1,
            d_max: int = 9,
            sigma_min: float = 10.0,
            sigma_max: float = 250.0
    ) -> None:
        """RandomBilateralBlur, 随机双边滤波, 滤波变换

        Args:
            d_min: Diameter min value, 直径最小值, [1, 9, 1], 1
            d_max: Diameter max value, 直径最大值, [1, 9, 1], 9
            sigma_min: Sigma min value, 标准差最小值, [10.0, 250.0, 0.1], 10.0
            sigma_max: Sigma max value, 标准差最大值, [10.0, 250.0, 0.1], 250.0
        """
        d_min = eval_arg(d_min, int)
        d_max = eval_arg(d_max, int)
        sigma_min = eval_arg(sigma_min, None)
        sigma_max = eval_arg(sigma_max, None)

        super().__init__(iaa.BilateralBlur(d=(d_min, d_max),
                                           sigma_color=(sigma_min, sigma_max),
                                           sigma_space=(sigma_min, sigma_max)), ATTRS)


class RandomMotionBlur(ImgaugAdapter):
    def __init__(
            self,
            kernel_size_min: int = 3,
            kernel_size_max: int = 7,
            degree_min: float = 0.0,
            degree_max: float = 360.0,
            direction_min: float = -1.0,
            direction_max: float = 1.0
    ) -> None:
        """RandomMotionBlur, 随机物体运动滤波, 滤波变换

        Args:
            kernel_size_min: Kernel size minimum, 核数最小值, [3, 7, 1], 3
            kernel_size_max: Kernel size maximum, 核数最小值, [3, 7, 1], 7
            degree_min: Angle minimum, 角度最小值, [0.0, 360.0, 0.1], 0.0
            degree_max: Angle maximum, 角度最大值, [0.0, 360.0, 0.1], 360.0
            direction_min: Direction minimum, 方向最小值, [-1.0, 1.0, 0.1], -1.0
            direction_max: Direction maximum, 方向最大值, [-1.0, 1.0, 0.1], 1.0
        """
        kernel_size_min = eval_arg(kernel_size_min, int)
        kernel_size_max = eval_arg(kernel_size_max, int)
        degree_min = eval_arg(degree_min, None)
        degree_max = eval_arg(degree_max, None)
        direction_min = eval_arg(direction_min, None)
        direction_max = eval_arg(direction_max, None)

        super().__init__(iaa.MotionBlur(k=(kernel_size_min, kernel_size_max),
                                        angle=(degree_min, degree_max),
                                        direction=(direction_min, direction_max)), ATTRS)


class RandomMeanShiftBlur(ImgaugAdapter):
    def __init__(
            self,
            spatial_radius_min: float = 5.0,
            spatial_radius_max: float = 40.0,
            color_radius_min: float = 5.0,
            color_radius_max: float = 40.0
    ) -> None:
        """RandomMeanShiftBlur, 随机均值迁移滤波, 滤波变换

        Args:
            spatial_radius_min: Spatial radius minimum, 空间半径最小值, [5.0, 40.0, 0.1], 5.0
            spatial_radius_max: Spatial radius maximum, 空间半径最大值, [5.0, 40.0, 0.1], 40.0
            color_radius_min: Color radius minimum, 颜色半径最小值, [5.0, 40.0, 0.1], 5.0
            color_radius_max: Color radius maximum, 颜色半径最大值, [5.0, 40.0, 0.1], 40.0
        """
        spatial_radius_min = eval_arg(spatial_radius_min, None)
        spatial_radius_max = eval_arg(spatial_radius_max, None)
        color_radius_min = eval_arg(color_radius_min, None)
        color_radius_max = eval_arg(color_radius_max, None)

        super().__init__(
            iaa.MeanShiftBlur(spatial_radius=(spatial_radius_min, spatial_radius_max),
                              color_radius=(color_radius_min, color_radius_max)),
            ATTRS
        )


class NonLocalMeanBlur(AbstractTransform):
    def __init__(
            self,
            method: str = 'gray',
            h: int = 3,
            hColor: int = 5,
            templateWindowSize: int = 7,
            searchWindowSize: int = 15
    ) -> None:
        """NonLocalMeanBlur, 非局部均值滤波, 滤波变换

        Args:
            method: Method, 通道方法, ['gray', 'color'], "gray"
            h: H, 滤波强度, [1, 30, 1], 3
            hColor: HColor, 颜色强度, [1, 100, 1], 5
            templateWindowSize: TemplateWindowSize, 模板窗口大小, [1, 15, 1], 7
            searchWindowSize: SearchWindowSize, 搜索窗口大小, [1, 100, 1], 15
        """
        super().__init__(use_gpu=False)

        self.method = method
        self.h = h
        self.hColor = hColor
        self.templateWindowSize = templateWindowSize
        self.searchWindowSize = searchWindowSize

    def _apply(self, sample):
        if sample.image is None:
            return sample

        if self.method not in ['gray', 'color']:
            raise ValueError("Method Error!")
        if self.method == "gray":
            gray = rgb_to_gray(sample.image)
            sample.image = cv2.fastNlMeansDenoising(
                gray, None, h=self.h, 
                templateWindowSize=self.templateWindowSize, 
                searchWindowSize=self.searchWindowSize
            )
        if self.method == "color":
            sample.image = cv2.fastNlMeansDenoisingColored(
                sample.image, None, h=self.h, hColor=self.hColor,
                templateWindowSize=self.templateWindowSize, 
                searchWindowSize=self.searchWindowSize
            )

        return sample
