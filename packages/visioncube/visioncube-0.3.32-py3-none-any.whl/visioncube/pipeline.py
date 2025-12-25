#!/usr/bin/env python3
import gc
import torch
import json
import random
from typing import Type, Mapping, Sequence, Optional

import yaml

from .docstring import parse_docstring
from .common import AbstractTransform


def format_operator_param(impl):
    results = []

    for name in dir(impl):
        clazz = getattr(impl, name)
        # noinspection PyTypeChecker
        if not isinstance(clazz, Type):
            continue
        # noinspection PyTypeChecker
        if not issubclass(clazz, AbstractTransform):
            continue
        if clazz.__init__.__doc__:
            doc = parse_docstring(clazz.__init__.__doc__)
            if 'args' in doc:
                new_args = []
                for arg_name, line in doc['args']:
                    tokens = line.split(', ')
                    tokens[0] = f'"{tokens[0]}"'
                    tokens[1] = f'"{tokens[1]}"'
                    line = ', '.join(tokens)
                    line = f'[{line}]'
                    new_args.append([arg_name, line])
                doc['args'] = new_args
            results.append((name, doc))
        else:
            co = clazz.__init__.__code__
            var_names = co.co_varnames[1:co.co_argcount]
            results.append((name, var_names))

    return results


def get_transforms(device="cpu"):
    if device == 'cuda':
        from visioncube import operators_cuda
        impl = operators_cuda
    else:
        from visioncube import operators
        impl = operators

    return format_operator_param(impl)


class TransformPipeline(object):
    """TransformPipeline

    Here is an example of the config file in yaml format:

    - name: RandomRotate
      kwargs:
        degree_min: -360
        degree_max: 360
        cval: 127


    - name: AdjustColorLevels
      kwargs:
        in_black: 50
        in_white: 200
    """

    def __init__(self, config_or_fp, training=False, device="cpu"):
        self.training = training

        self.call_list = []
        self.aug_list = None
        self.impl = None
        if 'cuda' in device:
            device = 'cuda'
        if isinstance(device, str) and device.upper() in ['CUDA', 'GPU']:
            from visioncube import operators_cuda
            self.impl = operators_cuda
        else:
            from visioncube import operators
            self.impl = operators

        if config_or_fp is not None:
            config = None
            if isinstance(config_or_fp, (list, tuple)):
                config = config_or_fp
            if config is None:
                config = self._load_yaml(config_or_fp)
            if config is None:
                config = self._load_json(config_or_fp)
            if config is None:
                raise ValueError('Invalid config.')

            for item in config:
                name = item['name']
                tag = item.get('tag')
                args = item.get('args', [])
                kwargs = item.get('kwargs', {})
                self.add_transform(tag, name, args, kwargs)

    @staticmethod
    def _load_yaml(path_or_fp):
        if isinstance(path_or_fp, str):
            with open(path_or_fp, 'r') as f:
                try:
                    return yaml.safe_load(f)
                except yaml.YAMLError:
                    return None
        else:
            try:
                return yaml.safe_load(path_or_fp)
            except yaml.YAMLError:
                return None

    @staticmethod
    def _load_json(path_or_fp):
        if isinstance(path_or_fp, str):
            with open(path_or_fp, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return None
        else:
            try:
                return json.load(path_or_fp)
            except json.JSONDecodeError:
                return None

    def add_transform(
            self,
            tag: Optional[str],
            name: Optional[str],
            args: Optional[Sequence],
            kwargs: Optional[Mapping],
    ) -> None:
        # Check tag and status.
        valid_tags = {None, 'train', 'test', 'aug'}
        if tag not in valid_tags:
            raise ValueError(f'tag should be one of {valid_tags}.')
        if self.training and tag == 'test':
            return
        if not self.training and tag in {'train', 'aug'}:
            return

        # Inner members are not allowed.
        if name.startswith('_'):
            raise ValueError(f'Invalid name "{name}".')

        Processing = getattr(self.impl, name)
        if Processing is None:
            raise ValueError(f'Cannot find "{name}".')
        if not callable(Processing):
            raise ValueError(f'"{name}" is not a valid image processing class.')

        # Create an instance for the class.
        proc_instance = Processing(*args, **kwargs)

        # Add the instance to the call_list.
        if tag == 'aug':
            if self.aug_list is None:
                self.aug_list = []
                self.call_list.append(self.aug_list)
            self.aug_list.append(proc_instance)
        else:
            self.call_list.append(proc_instance)

    def __call__(self, doc, device=None, use_tensor=False, use_homography=False):

        sample = self.impl.Sample(
            doc, 
            device=device, 
            output_tensor=use_tensor, 
            use_homography=use_homography
        )

        for call in self.call_list:
            if callable(call):
                sample = call(sample)
            else:
                sample = random.choice(call)(sample)

        doc = sample.output()

        return doc
