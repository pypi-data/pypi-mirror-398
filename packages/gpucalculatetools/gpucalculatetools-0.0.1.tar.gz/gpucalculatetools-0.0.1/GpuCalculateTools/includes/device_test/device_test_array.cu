#include "device_test_array.h"
__global__ void test_add_kernal(float* arr, float* arr1, float* result) {
    int i = threadIdx.x;
    result[i] = arr[i] + arr1[i];
}
__global__ void test_minus_kernal(float* arr, float* arr1, float* result) {
    int i = threadIdx.x;
    result[i] = arr[i] - arr1[i];
}
__global__ void test_mul_kernal(float* arr, float* arr1, float* result) {
    int i = threadIdx.x;
    result[i] = arr[i] * arr1[i];
}
void device_add_array(float* arr, float* arr1, float* result, int length) {
    float* d_arr;
    float* d_arr1;
    float* d_result;
    size_t N_SIZE = length * sizeof(float);
    cudaError_t error = cudaMalloc((void**)&d_arr, N_SIZE);
    if (error != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error), cudaGetErrorString(error));
    }
    cudaError_t error1 = cudaMalloc((void**)&d_arr1, N_SIZE);
    if (error1 != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error1), cudaGetErrorString(error1));
    }
    cudaError_t error2 = cudaMalloc((void**)&d_result, N_SIZE);
    if (error != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error2), cudaGetErrorString(error2));
    }
    cudaMemcpy(d_arr, arr, N_SIZE, cudaMemcpyHostToDevice);
    cudaMemcpy(d_arr1, arr1, N_SIZE, cudaMemcpyHostToDevice);
    cudaMemcpy(d_result, result, N_SIZE, cudaMemcpyHostToDevice);
    void* args[] = { &d_arr,&d_arr1, &d_result };
    cudaLaunchKernel(test_add_kernal, 1, length, args, 0, cudaStreamDefault);
    cudaMemcpy(result, d_result, N_SIZE, cudaMemcpyDeviceToHost);
    cudaFree(d_arr);
    cudaFree(d_arr1);
    cudaFree(d_result);
}
void device_minus_array(float* arr, float* arr1, float* result, int length) {
    float* d_arr;
    float* d_arr1;
    float* d_result;
    size_t N_SIZE = length * sizeof(float);
    cudaError_t error = cudaMalloc((void**)&d_arr, N_SIZE);
    if (error != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error), cudaGetErrorString(error));
    }
    cudaError_t error1 = cudaMalloc((void**)&d_arr1, N_SIZE);
    if (error1 != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error1), cudaGetErrorString(error1));
    }
    cudaError_t error2 = cudaMalloc((void**)&d_result, N_SIZE);
    if (error != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error2), cudaGetErrorString(error2));
    }
    cudaMemcpy(d_arr, arr, N_SIZE, cudaMemcpyHostToDevice);
    cudaMemcpy(d_arr1, arr1, N_SIZE, cudaMemcpyHostToDevice);
    cudaMemcpy(d_result, result, N_SIZE, cudaMemcpyHostToDevice);
    void* args[] = { &d_arr,&d_arr1, &d_result };
    cudaLaunchKernel(test_minus_kernal, 1, length, args, 0, cudaStreamDefault);
    cudaMemcpy(result, d_result, N_SIZE, cudaMemcpyDeviceToHost);
    cudaFree(d_arr);
    cudaFree(d_arr1);
    cudaFree(d_result);
}
void device_mul_array(float* arr, float* arr1, float* result, int length) {
    float* d_arr;
    float* d_arr1;
    float* d_result;
    size_t N_SIZE = length * sizeof(float);
    cudaError_t error = cudaMalloc((void**)&d_arr, N_SIZE);
    if (error != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error), cudaGetErrorString(error));
    }
    cudaError_t error1 = cudaMalloc((void**)&d_arr1, N_SIZE);
    if (error1 != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error1), cudaGetErrorString(error1));
    }
    cudaError_t error2 = cudaMalloc((void**)&d_result, N_SIZE);
    if (error != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error2), cudaGetErrorString(error2));
    }
    cudaMemcpy(d_arr, arr, N_SIZE, cudaMemcpyHostToDevice);
    cudaMemcpy(d_arr1, arr1, N_SIZE, cudaMemcpyHostToDevice);
    cudaMemcpy(d_result, result, N_SIZE, cudaMemcpyHostToDevice);
    void* args[] = { &d_arr,&d_arr1, &d_result };
    cudaLaunchKernel(test_mul_kernal, 1, length, args, 0, cudaStreamDefault);
    cudaMemcpy(result, d_result, N_SIZE, cudaMemcpyDeviceToHost);
    cudaFree(d_arr);
    cudaFree(d_arr1);
    cudaFree(d_result);
}
static PyObject* test_add(PyObject* self, PyObject* args) {
    PyObject* arr;
    PyObject* arr1;
    if (!PyArg_ParseTuple(args, "OO", &arr, &arr1))
    {
        Py_RETURN_NONE;
    }
    int length = PyObject_Length(arr);
    int length1 = PyObject_Length(arr1);
    if (length != length1)
    {
        Py_RETURN_NONE;
    }
    size_t N_SIZE = length * sizeof(float);
    float* h_arr = (float*)malloc(N_SIZE);
    float* h_arr1 = (float*)malloc(N_SIZE);
    float* h_result = (float*)malloc(N_SIZE);
    Py_INCREF(arr);
    Py_INCREF(arr1);
    for (size_t i = 0; i < length; i++)
    {
        PyObject* item = PyList_GetItem(arr, i);
        PyObject* item1 = PyList_GetItem(arr1, i);
        Py_INCREF(item);
        Py_INCREF(item1);
        PyArg_Parse(item, "f", &h_arr[i]);
        PyArg_Parse(item1, "f", &h_arr1[i]);
        Py_DECREF(item);
        Py_DECREF(item);
    }
    device_add_array(h_arr, h_arr1, h_result, length);
    PyObject* result = PyList_New(length);
    for (size_t i = 0; i < length; i++)
    {
        PyObject* ADD_ITEM = Py_BuildValue("f", h_result[i]);
        Py_INCREF(ADD_ITEM);
        PyList_SetItem(result, i, ADD_ITEM);
    }
    free(h_arr);
    free(h_arr1);
    free(h_result);
    Py_INCREF(result);
    return result;
}
static PyObject* test_minus(PyObject* self, PyObject* args) {
    PyObject* arr;
    PyObject* arr1;
    if (!PyArg_ParseTuple(args, "OO", &arr, &arr1))
    {
        Py_RETURN_NONE;
    }
    int length = PyObject_Length(arr);
    int length1 = PyObject_Length(arr1);
    if (length != length1)
    {
        Py_RETURN_NONE;
    }
    size_t N_SIZE = length * sizeof(float);
    float* h_arr = (float*)malloc(N_SIZE);
    float* h_arr1 = (float*)malloc(N_SIZE);
    float* h_result = (float*)malloc(N_SIZE);
    Py_INCREF(arr);
    Py_INCREF(arr1);
    for (size_t i = 0; i < length; i++)
    {
        PyObject* item = PyList_GetItem(arr, i);
        PyObject* item1 = PyList_GetItem(arr1, i);
        Py_INCREF(item);
        Py_INCREF(item1);
        PyArg_Parse(item, "f", &h_arr[i]);
        PyArg_Parse(item1, "f", &h_arr1[i]);
        Py_DECREF(item);
        Py_DECREF(item);
    }
    device_minus_array(h_arr, h_arr1, h_result, length);
    PyObject* result = PyList_New(length);
    for (size_t i = 0; i < length; i++)
    {
        PyObject* ADD_ITEM = Py_BuildValue("f", h_result[i]);
        Py_INCREF(ADD_ITEM);
        PyList_SetItem(result, i, ADD_ITEM);
    }
    free(h_arr);
    free(h_arr1);
    free(h_result);
    Py_INCREF(result);
    return result;
}
static PyObject* test_mul(PyObject* self, PyObject* args) {
    PyObject* arr;
    PyObject* arr1;
    if (!PyArg_ParseTuple(args, "OO", &arr, &arr1))
    {
        Py_RETURN_NONE;
    }
    int length = PyObject_Length(arr);
    int length1 = PyObject_Length(arr1);
    if (length != length1)
    {
        Py_RETURN_NONE;
    }
    size_t N_SIZE = length * sizeof(float);
    float* h_arr = (float*)malloc(N_SIZE);
    float* h_arr1 = (float*)malloc(N_SIZE);
    float* h_result = (float*)malloc(N_SIZE);
    Py_INCREF(arr);
    Py_INCREF(arr1);
    for (size_t i = 0; i < length; i++)
    {
        PyObject* item = PyList_GetItem(arr, i);
        PyObject* item1 = PyList_GetItem(arr1, i);
        Py_INCREF(item);
        Py_INCREF(item1);
        PyArg_Parse(item, "f", &h_arr[i]);
        PyArg_Parse(item1, "f", &h_arr1[i]);
        Py_DECREF(item);
        Py_DECREF(item);
    }
    device_mul_array(h_arr, h_arr1, h_result, length);
    PyObject* result = PyList_New(length);
    for (size_t i = 0; i < length; i++)
    {
        PyObject* ADD_ITEM = Py_BuildValue("f", h_result[i]);
        Py_INCREF(ADD_ITEM);
        PyList_SetItem(result, i, ADD_ITEM);
    }
    free(h_arr);
    free(h_arr1);
    free(h_result);
    Py_INCREF(result);
    return result;
}
static PyMethodDef methods[] = {
    {"add_array",test_add,METH_VARARGS,"To test array add function!"},
    {"minus_array",test_minus,METH_VARARGS,"To test array minus function!"},
    {"mul_array",test_mul,METH_VARARGS,"To test array mul function!"},
    {NULL,NULL,0,NULL}
};
static PyModuleDef GPU_DEVICE_TEST_MODULE = {
    PyModuleDef_HEAD_INIT,
    "_GPUDeviceTest",
    NULL,
    -1,
    methods
};
PyMODINIT_FUNC PyInit__GPUDeviceTest() {
    return PyModule_Create(&GPU_DEVICE_TEST_MODULE);
}