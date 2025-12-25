#!/bin/bash
if [[ $# -eq 0 ]]; then
    echo -e "\033[31m you can edit the $(realpath $0) as you need \033[0m"
    echo "example: cmdxx build/update/reinstall"
    code $(realpath $0)
fi

echo "you can control compiling in docker image or not, which branch to use, debug or release build, cuda version, etc."
docker_images=""
branch=main
build_type=Debug
if [[ $build_type == Debug ]]; then
    dev_opts="--enable_nvtx_profile --enable_cuda_line_info"
fi
cuda=12.1

set -ex
# exit if $1 is not "build" or "update"
if [[ $1 != "build" && $1 != "update" && $1 != "reinstall" ]]; then
    echo -e "\033[31m you need to specify build / update / reinstall \033[0m"
    exit 1
fi

output_dir=/tmp/ort_build/$branch/$cuda/
ort_dir=/tmp/ort_src/$branch/$build_type
# in case you use "root" to build
sudo git config --system --add safe.directory "*"

if [[ ! -d $ort_dir ]]; then
    git clone https://github.com/microsoft/onnxruntime.git $ort_dir
    cd $ort_dir
    # checkout here, as user may edit src later, if checkout everytime then user changes will be reset
    git checkout $branch
fi

cd $ort_dir
current_branch=$(git branch | grep '*' | awk '{print $2}' -)
if [[ $branch != $current_branch ]]; then
    echo branch is wrong, we want $branch while it is $current_branch
    exit 666 # remove the exit if you want to continue to build
fi

if [[ $1 == "build" ]]; then
    build=1
    reinstall=1
    update=0
elif [[ $1 == "update" ]]; then
    build=0
    reinstall=0
    update=1
elif [[ $1 == "reinstall" ]]; then
    build=0
    reinstall=1
    update=0
fi

(
    if [[ -n $USER ]]; then
        path=$(pip show onnxruntime-training | grep Location | awk '{print $2}')/onnxruntime
        sudo chown -R $USER $path
        echo zhijiang, chown done
    fi
) &

if [[ $build -eq 1 ]]; then
    echo -e "\033[32m start building \033[0m"
    sudo rm -rf $output_dir/$build_type/dist/*.whl
    cmd=" git config --global --add safe.directory '*' && \
        cd $(pwd) && \
        bash ./build.sh \
            --build_dir=$output_dir \
            --cuda_home /usr/local/cuda-$cuda --cudnn_home /usr/lib/x86_64-linux-gnu/ \
            --cuda_version=$cuda \
            --use_cuda --config $build_type --update --build \
            --build_wheel \
            --parallel \
            --enable_training --skip_tests \
            --cmake_extra_defines ONNXRUNTIME_VERSION=$(cat ./VERSION_NUMBER) CMAKE_CUDA_ARCHITECTURES='70;75' onnxruntime_BUILD_UNIT_TESTS=OFF \
            --use_mpi=false $dev_opts --allow_running_as_root"

    if [[ -n $docker_images ]]; then
        sudo docker run -it --rm \
            -v /tmp:/tmp \
            $docker_images bash -xc "$cmd"
    else
        bash -xc "$cmd"
    fi
fi

if [[ $reinstall -eq 1 ]]; then
    sudo env "PATH=$PATH" pip uninstall -y onnxruntime-training
    sudo env "PATH=$PATH" pip uninstall -y onnxruntime
    sudo env "PATH=$PATH" pip install $output_dir/$build_type/dist/*.whl
    # avoid torch_ort find wrong cuda version
    cd /tmp
    sudo env "PATH=$PATH" pip install torch_ort
    export PATH=/usr/local/cuda-$cuda/bin:$PATH
    sudo env "PATH=$PATH" TORCH_CUDA_ARCH_LIST="7.0+PTX" python -m torch_ort.configure
    echo -e "\033[0;31m build and install ORT from scratch done\033[0m"
fi

if [[ $update -eq 1 ]]; then
    echo -e "\033[0;31m update ort package \033[0m"
    build_path=$(realpath -s $output_dir/$build_type)
    cd $build_path
    # VERBOSE=1
    make -j40 onnxruntime_pybind11_state
    cd /tmp
    wheel_path=$(pip show onnxruntime-training | grep -i location | cut -d" " -f2)
    cd $wheel_path/onnxruntime/capi
    so_files=$(ls *.so)
    sudo rm -rf $so_files
    for i in $so_files; do
        sudo ln -s $build_path/$i $i
    done
    echo -e "\033[0;31m update ORT by softlink done \033[0m"
fi
