def get_gpu_model():
    import subprocess
    result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8').strip().split('\n')[0]


def tensorrt_version():
    import tensorrt as trt
    return f'{trt.__version__}'

if __name__ == '__main__':
    print(get_gpu_model())