import multiprocessing

def available_gpus():
    def f(res):
        from numba import cuda
        gpu_list = cuda.gpus.lst
        for i, device in enumerate(gpu_list):
            res.append({
                "id": i,
                "model": device.name
            })
    result = multiprocessing.Manager().list()
    p = multiprocessing.Process(target=f, args=(result,))
    p.start()
    p.join()
    return list(result)

