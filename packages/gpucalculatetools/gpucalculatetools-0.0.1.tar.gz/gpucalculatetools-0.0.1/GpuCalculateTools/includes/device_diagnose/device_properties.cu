#include "device_properties.h"
int set_device(int no) {
    cudaError_t error = cudaSetDevice(no);
    if (error != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error), cudaGetErrorString(error));
        return -1;
    }
    else
    {
        return 0;
    }
}
void get_device_prop(int no) {
    cudaDeviceProp prop;
    cudaError_t error = cudaGetDeviceProperties(&prop, no);
    if (error != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error), cudaGetErrorString(error));
    }
    else
    {
        printf("name:%s\n", prop.name);
        printf("totalGlobalMem:%dMByte\n", prop.totalGlobalMem / 1024 / 1024);
        printf("sharedMemPerBlock:%dKByte\n", prop.sharedMemPerBlock / 1024);
        printf("regsPerBlock:%d\n", prop.regsPerBlock);
        printf("warpSize:%d\n", prop.warpSize);
        printf("maxThreadsPerBlock:%d\n", prop.maxThreadsPerBlock);
        printf("maxThreadsDim:(%d,%d,%d)\n", prop.maxThreadsDim[0], prop.maxThreadsDim[1], prop.maxThreadsDim[2]);
        printf("maxGridSize:(%d,%d,%d)\n", prop.maxGridSize[0], prop.maxGridSize[1], prop.maxGridSize[2]);
        printf("totalConstMem:%dKByte\n", prop.totalConstMem / 1024);
        printf("major:%d\n", prop.major);
        printf("minor:%d\n", prop.minor);
        printf("textureAlignment:%dByte\n", prop.textureAlignment);
        printf("texturePitchAlignment:%dByte\n", prop.texturePitchAlignment);
        printf("multiProcessorCount:%d\n", prop.multiProcessorCount);
        printf("integrated:%d\n", prop.integrated);
        printf("canMapHostMemory:%s\n", prop.canMapHostMemory == 1 ? "true" : "false");
        printf("maxTexture1D:%d\n", prop.maxTexture1D);
        printf("maxTexture1DMipmap:%d\n", prop.maxTexture1DMipmap);
        printf("maxTexture2D:(%d,%d)\n", prop.maxTexture2D[0], prop.maxTexture2D[1]);
        printf("maxTexture2DMipmap:(%d,%d)\n", prop.maxTexture2DMipmap[0], prop.maxTexture2DMipmap[1]);
        printf("maxTexture2DLinear:(%d,%d,%d)\n", prop.maxTexture2DLinear[0], prop.maxTexture2DLinear[1], prop.maxTexture2DLinear[2]);
        printf("maxTexture2DGather:(%d,%d)\n", prop.maxTexture2DGather[0], prop.maxTexture2DGather[1]);
        printf("maxTexture3D:(%d,%d,%d)\n", prop.maxTexture3D[0], prop.maxTexture3D[1], prop.maxTexture3D[2]);
    }
}
int get_device_count() {
    int result = 0;
    cudaError_t error = cudaGetDeviceCount(&result);
    if (error != cudaSuccess)
    {
        printf("%s:%s\n", cudaGetErrorName(error), cudaGetErrorString(error));
        return -1;
    }
    else
    {
        return result;
    }
}

static PyObject* set_device_host(PyObject* self, PyObject* args) {
	int dev_no = 0;
	if (!PyArg_ParseTuple(args, "i", &dev_no))
	{
		Py_RETURN_NONE;
	}
	int result = set_device(dev_no);
	PyObject* res = Py_BuildValue("i", result);
	Py_INCREF(res);
	return res;
}
static PyObject* get_device_prop_host(PyObject* self, PyObject* args) {
	int dev_no = 0;
	if (!PyArg_ParseTuple(args, "i", &dev_no))
	{
		Py_RETURN_NONE;
	}
	get_device_prop(dev_no);
	Py_RETURN_NONE;
}
static PyObject* get_device_count_host(PyObject* self, PyObject* args) {
	int result = get_device_count();
	PyObject* RES = Py_BuildValue("I", result);
	Py_INCREF(RES);
	return RES;
}
static PyMethodDef methods[] = {
	{"set_device",set_device_host,METH_VARARGS,"To set running device!"},
	{"get_device_prop",get_device_prop_host,METH_VARARGS,"To get GPU properties precisely!"},
	{"get_device_count",get_device_count_host,METH_VARARGS,"To get GPU numbers in this desktop!"},
	{NULL,NULL,0,NULL}
};
static PyModuleDef GPU_DEVICE_DIAGNOSE_MODULE = {
	PyModuleDef_HEAD_INIT,
	"_GPUDeviceDiagnose",
	NULL,
	-1,
	methods
};
PyMODINIT_FUNC PyInit__GPUDeviceDiagnose() {
	return PyModule_Create(&GPU_DEVICE_DIAGNOSE_MODULE);
}