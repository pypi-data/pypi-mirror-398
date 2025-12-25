import os


# Restrict NumPy-based BLAS libraries to single-threaded execution
def set_scikit_n_threads(n_threads: int | str):
    n_threads = str(n_threads)
    os.environ["OMP_NUM_THREADS"] = n_threads  # Limits OpenMP
    os.environ["MKL_NUM_THREADS"] = n_threads  # Limits Intel MKL
    os.environ["OPENBLAS_NUM_THREADS"] = n_threads  # Limits OpenBLAS
    os.environ["NUMBA_NUM_THREADS"] = n_threads  # If using Numba
