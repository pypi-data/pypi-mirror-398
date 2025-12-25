import numpy as np
import cv2 as cv

METHOD_LIST = [
    ''
]


def conv2d(x: np.ndarray, k: np.ndarray) -> np.ndarray:
    assert len(x.shape) == 2
    assert len(k.shape) == 2 or len(k.shape) == 3
    unfolded = np.lib.stride_tricks.as_strided(
        x,
        shape=(*k.shape[-2:], x.shape[-2] - k.shape[-2] + 1, x.shape[-1] - k.shape[-1] + 1),
        strides=(*x.strides, *x.strides)
    )
    if len(k.shape) == 2:
        return np.einsum('ij,ijkl->kl', k, unfolded)
    else:
        return np.einsum('nij,ijkl->nkl', k, unfolded)


def match_template(img, templ, method: str = None):
    image_proj = img - np.mean(img)
    template_proj = templ - np.mean(templ, axis=(0, 1))
    res = conv2d(image_proj, template_proj)
    max_templ = np.argmax(np.max(res.reshape(res.shape[0], -1), axis=1))
    max_pos = np.argmax(res[max_templ])
    x_index = max_pos // res.shape[2]
    y_index = max_pos % res.shape[2]
    return x_index, y_index


def main():
    import time
    import visioncube as cube

    template = cv.cvtColor(cv.imread('template.png'), cv.COLOR_BGR2GRAY)
    template = cv.resize(template, dsize=None, fx=0.1, fy=0.1)

    image = cv.cvtColor(cv.imread('ori_image.jpg'), cv.COLOR_BGR2GRAY)
    image = cv.resize(image, dsize=None, fx=0.1, fy=0.1)

    template_list = [cube.rotate(template, i * 360 / 20, cval=0) for i in range(20)]
    templates = np.array(template_list)

    t1 = time.time()
    for templ in templates:
        res = cv.matchTemplate(image, templ, cv.TM_CCOEFF_NORMED)
        _, max_value, _, max_loc = cv.minMaxLoc(res)
        x1, y1 = max_loc
    print(time.time() - t1)  # 0.069s

    t2 = time.time()
    x_index, y_index = match_template(image, templates)
    print(time.time() - t2)  # 7.129s
    cv.imwrite('a.png', image[y_index: y_index + template.shape[-2], x_index: x_index + template.shape[-1]])


if __name__ == '__main__':
    main()
