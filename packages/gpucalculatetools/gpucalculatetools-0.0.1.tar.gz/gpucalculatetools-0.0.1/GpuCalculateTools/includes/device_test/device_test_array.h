#ifndef DEVICE_TEST_ARRAY_H
#define DEVICE_TEST_ARRAY_H
#define PY_SIZE_T_CLEAN
#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include <Python.h>
void device_add_array(float* arr, float* arr1, float* result,int length);
void device_minus_array(float* arr, float* arr1, float* result, int length);
void device_mul_array(float* arr, float* arr1, float* result, int length);
#endif