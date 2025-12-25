# ImageProcessing

Image pre-processing and post-processing module

## Installation
###  Get from PyPI
```shell
pip install visioncube
```
### Build from source
```shell
git clone https://gitlab.edgeai.org:8888/aa-team/visioncube.git
```

## Usage
### Pipeline
> Parameters in Pipeline:
> - device:
>   - cpu: backend is imgaug and opencv
>   - cuda: backend is pytorch
> - tag: 
>   - None: Applying pipeline during train and test
>   - train: Only train
>   - test: Only test
>   - aug: Randomly using an operator in the pipeline

#### Yaml config
You can write a yaml file in the following format and save it as `config.yml`.
```shell
- name: Add
  kwargs:
    value: 100
    
    
- name: AdjustColorLevels
  kwargs:
    in_black: 50
    in_white: 200
```

```python
import cv2 as cv

from visioncube import TransformPipeline

image_path = ''
mask_path = ''
heatmap_path = ''

image = cv.imread(image_path, cv.IMREAD_COLOR)
image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

doc = {
    'image': image,                           # Required
    'bboxes': [], # [[x1, y1, x2, y2, label]] # Optional
    'mask': cv.imread(mask_path, 0),          # Optional
    'heatmap': cv.imread(heatmap_path),       # Optional
    'keypoints': [], # [[x1, y1], [x2, y2]]   # Optional
}

# device in {'cpu', 'cuda'}
pipeline = TransformPipeline('config.yml', training=False, device='cuda')
image1 = pipeline(doc)['image']
```
#### No configuration
```python
import cv2 as cv

from visioncube import TransformPipeline

image_path = ''
mask_path = ''
heatmap_path = ''

image = cv.imread(image_path, cv.IMREAD_COLOR)
image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

doc = {
    'image': image,                           # Required
    'bboxes': [], # [[x1, y1, x2, y2, label]] # Optional
    'mask': cv.imread(mask_path, 0),          # Optional
    'heatmap': cv.imread(heatmap_path),       # Optional
    'keypoints': [], # [[x1, y1], [x2, y2]]   # Optional
}

# device in {'cpu', 'cuda'}
pipeline = TransformPipeline(
    [
        {
            'name': 'Add', 
            'tag': None,
            'kwargs': {
                'value': 100
            }
        },
        {
            'name': 'AdjustColorLevels',
            'tag': None,
            'kwargs': {
                'in_black': 50,
                'in_white': 200,
            }
        },
    ], 
    training=True, 
    device='cuda'
)
image1 = pipeline(doc)['image']
```

### Functional
#### Function
```python
import cv2 as cv

from visioncube import add, adjust_color_levels

image_path = ''
image = cv.imread(image_path, cv.IMREAD_COLOR)

image = add(image, 100)
image = adjust_color_levels(image, in_black=50, in_white=200)
```

#### Operators
#### CPU Operators
```python
import cv2 as cv
from visioncube.operators import Add, AdjustColorLevels

image_path = ''
mask_path = ''
heatmap_path = ''

image = cv.imread(image_path, cv.IMREAD_COLOR)
image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

doc = {
    'image': image,                           # Required
    'bboxes': [], # [[x1, y1, x2, y2, label]] # Optional
    'mask': cv.imread(mask_path, 0),          # Optional
    'heatmap': cv.imread(heatmap_path),       # Optional
    'keypoints': [], # [[x1, y1], [x2, y2]]   # Optional
}

doc = Add(value=100)(doc)
doc = AdjustColorLevels(in_black=50, in_white=200)(doc)
image = doc['image']
```

#### CUDA Operators
```python
import cv2 as cv
from visioncube.operators_cuda import Add, AdjustColorLevels

image_path = ''
mask_path = ''
heatmap_path = ''

image = cv.imread(image_path, cv.IMREAD_COLOR)
image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

doc = {
    'image': image,                           # Required
    'bboxes': [], # [[x1, y1, x2, y2, label]] # Optional
    'mask': cv.imread(mask_path, 0),          # Optional
    'heatmap': cv.imread(heatmap_path),       # Optional
    'keypoints': [], # [[x1, y1], [x2, y2]]   # Optional
}

doc = Add(value=100)(doc)
doc = AdjustColorLevels(in_black=50, in_white=200)(doc)
image = doc['image']
```

## Get Operators
```python
## get image processing operators
from visioncube import get_transforms
ops = get_transforms(device='cuda') # or cpu

## get measure operators
from visioncube import measure
from visioncube import format_operator_param
ops = format_operator_param(measure)

## get recognition operators
from visioncube import recognition
from visioncube import format_operator_param
ops = format_operator_param(recognition)
```

## Image pre-processing
The supported operators include
 - GPU: Tesla T4
 - Image: 1080\*1080\*3
 - Cost time: ms

![img.png](source/img.png)


## TODO
 - [x] measure: ColorMeasurement
 - [x] operators: PolarUnwrap