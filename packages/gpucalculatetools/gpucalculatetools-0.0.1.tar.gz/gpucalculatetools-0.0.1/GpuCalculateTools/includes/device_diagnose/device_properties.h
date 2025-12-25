#ifndef DEVICE_PROPERTIES_H
#define DEVICE_PROPERTIES_H
#define PY_SIZE_T_CLEAN
#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include <Python.h>
int set_device(int no);
void get_device_prop(int no);
int get_device_count();

#endif