from .._GPUDeviceDiagnose import *
def set_gpu_device(no):
    set_device(no)
def get_gpu_device_prop(no):
    get_device_prop(no)
def get_gpu_device_count():
    return get_device_count()