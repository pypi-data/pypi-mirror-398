import os
from ....utils.pybind_utils import make

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

@make(
    this_folder=THIS_FOLDER,
    module_name="clustering_cpp_openmp_impl",
    package="wp21_train.physics.clustering.backends"
)
def cluster_cpp_openmp(clustering_cpp_openmp_impl, *args, **kwargs):
    return clustering_cpp_openmp_impl.cluster(*args, **kwargs)

