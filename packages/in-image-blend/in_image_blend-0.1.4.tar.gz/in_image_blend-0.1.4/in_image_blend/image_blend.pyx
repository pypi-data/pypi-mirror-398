# in_image_blend/image_blend.pyx
# cython: boundscheck=False, wraparound=False, nonecheck=False, cdivision=True
import numpy as np
cimport numpy as cnp
# NumPy 2.x 兼容性：必须调用 import_array
cnp.import_array()

ctypedef cnp.uint8_t UINT8
ctypedef cnp.int32_t INT32

cpdef blend_images(
    const UINT8[:, :, :] img1, 
    const UINT8[:, :, :] img2, 
    const UINT8[:, :] mask
):
    cdef Py_ssize_t h = img1.shape[0]
    cdef Py_ssize_t w = img1.shape[1]
    cdef Py_ssize_t c = img1.shape[2]
    cdef Py_ssize_t i, j, k
    cdef float mask_value
    
    cdef cnp.ndarray result_arr = np.empty((h, w, c), dtype=np.uint8)
    cdef UINT8[:, :, :] result = result_arr
    
    for i in range(h):
        for j in range(w):
            mask_value = mask[i, j] / 255.0
            for k in range(c):
                result[i, j, k] = <UINT8>(img1[i, j, k] * (1.0 - mask_value) + img2[i, j, k] * mask_value + 0.5)

    return result_arr