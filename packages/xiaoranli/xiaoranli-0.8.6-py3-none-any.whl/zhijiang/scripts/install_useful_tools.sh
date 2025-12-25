# python or pip may not exists, so we need to ln for them
[ -z $(which python) ] && sudo ln -s /usr/bin/python3 /usr/bin/python
[ -z $(which pip) ] && sudo ln -s /usr/bin/pip3 /usr/bin/pip
# disable apt prompt
export DEBIAN_FRONTEND=noninteractive

python_pkg_path=$(cat ~/.zhijiang/python_pkg_path)
zhijiang_pkg_path=$python_pkg_path/zhijiang
zhijiang_version=$(python -c "import zhijiang; print(zhijiang.__version__)" | tail -1)
# import zhijiang may fail, if so then exit

file_flag=~/.zhijiang/useful_tools_installed.$zhijiang_version
if [[ -e $file_flag ]]; then
    echo -e "\\033[0;31m useful tools already installed\\033[0m"
    echo "if you want reinstall, please delete $file_flag"
    exit 0
fi

function setup_python_env() {
    sudo env "PATH=$PATH" pip install --upgrade py-spy viztracer debugpy \
        cmake netron termcolor stackprinter watchpoints plantweb \
        nvtx pre-commit pylint tldr \
        torchview graphviz code2flow
    tldr --update_cache
}

function setup_bash_env() {
    # vim with +clipboard, so vim can use os's clipboard
    sudo apt install -y vim \
        tmux htop \
        gdb cgdb peco bat ripgrep \
        strace ltrace sysstat tree bc \
        graphviz iftop git \
        silversearcher-ag autoconf libtool net-tools lsb-release curl wget \
        plocate \
        ccache distcc
    sudo updatedb &
    wget -q "https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb"
    sudo dpkg -i packages-microsoft-prod.deb
    sudo apt-get update
    #sudo apt-get install -y powershell

    [[ -n $(which batcat) && -n $(which bat) ]] && sudo ln -sf $(which batcat) $(which bat)

    if [[ ! -e ~/.config/peco/config.json ]]; then
        mkdir -p ~/.config/peco
        cat >~/.config/peco/config.json <<EOF
    {
        "InitialFilter": "IgnoreCase",
        "Keymap": {
            "C-a": "peco.SelectAll",
            "C-r": "peco.RotateFilter",
            "C-s": "peco.RotateFilter",
            "C-Space": "peco.ToggleSelectionAndSelectNext"
        }
    }
EOF
    fi

    if [[ -n $(which nvidia-smi) ]]; then
        # only install cuda tool if nvidia-smi exists
        gpu_arch=$(nvidia-smi --id=0 --query-gpu=compute_cap --format=csv | tail -1)
        gpu_arch_more_than_v100=$(echo "$gpu_arch >= 8.0" | bc -l)
        if [ -z $(which ncu) ]; then
            wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.1-1_all.deb
            sudo dpkg -i cuda-keyring_1.1-1_all.deb
            sudo apt update
            if [[ $gpu_arch_more_than_v100 -eq 1 ]]; then
                sudo apt install -y nsight-compute-2023.2.1
                sudo ln -sf /opt/nvidia/nsight-compute/2023.2.1/ncu /usr/local/bin
            else
                sudo apt install -y nsight-compute-2021.3.1
                sudo ln -sf /opt/nvidia/nsight-compute/2021.3.1/ncu /usr/local/bin
            fi
        fi
        if [ -z $(which nsys) ]; then
            wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.1-1_all.deb
            sudo dpkg -i cuda-keyring_1.1-1_all.deb
            sudo apt update
            if [[ $gpu_arch_more_than_v100 -eq 1 ]]; then
                sudo apt install -y nsight-systems-2023.2.3
            else
                sudo apt install -y nsight-systems-2021.2.4
            fi
        fi
    fi
    #2 flame graph
    if [[ -z $(which flamegraph.pl) ]]; then
        sudo wget --output-document=/usr/local/bin/stackcollapse-perf.pl https://raw.githubusercontent.com/brendangregg/FlameGraph/master/stackcollapse-perf.pl
        sudo wget --output-document=/usr/local/bin/flamegraph.pl https://raw.githubusercontent.com/brendangregg/FlameGraph/master/flamegraph.pl
        sudo chmod 777 /usr/local/bin/stackcollapse-perf.pl /usr/local/bin/flamegraph.pl
    fi

}

# install tool to output c++ call graph, class graph
function build_cpptree() {
    if [[ -z $(which cpptree) ]]; then
        sudo wget --output-document=/usr/local/bin/calltree https://raw.githubusercontent.com/satanson/cpp_etudes/master/calltree.pl
        sudo wget --output-document=/usr/local/bin/cpptree https://raw.githubusercontent.com/satanson/cpp_etudes/master/cpptree.pl
        sudo chmod 777 /usr/local/bin/calltree /usr/local/bin/cpptree
    fi
}

#------for profiling------
#1 install gpertools
function build_tcmalloc() {
    if [[ ! -e /usr/local/lib/libtcmalloc.so ]]; then
        tmp=$(mktemp -d)
        cd $tmp
        git clone https://github.com/gperftools/gperftools
        cd gperftools
        ./autogen.sh
        ./configure
        make -j$(nproc --all)
        sudo make install
        # ls -l /usr/local/lib/libtcmalloc* /usr/local/lib/libprofiler*
    fi
}

function build_libleak() {
    if [[ ! -e /usr/local/lib/libleak.so ]]; then
        tmp=$(mktemp -d)
        cd $tmp
        git clone --recursive https://github.com/WuBingzheng/libleak.git
        cd libleak
        make
        sudo mv libleak.so /usr/local/lib/
    fi
}

function setup_fzf() {
    if [[ ! -e ~/.fzf/install ]]; then
        git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
        ~/.fzf/install --all
    fi
}

# make cmd for project executable
cd "$zhijiang_pkg_path/scripts/projects"
# Iterate over directory entries safely; skip directories like __pycache__
for f in *; do
    # skip if not a regular file (e.g. directory, symlink)
    if [[ ! -f "$f" ]]; then
        continue
    fi
    # optional: skip backup/temp files
    if [[ "$f" =~ (~|\.swp|\.tmp)$ ]]; then
        continue
    fi
    dst="/usr/local/bin/zhijiang-prj-${f%.*}"
    sudo install -m 0777 "$f" "$dst"
done

sudo cp $zhijiang_pkg_path/scripts/self-bin/* /usr/bin
# apt install can't be paralleled!
# in case apt prompt, no bg process here
setup_bash_env
bash ~/.bashrc & # trigger the first time setup conda tab completion
setup_python_env &
build_cpptree &
# build_tcmalloc &
# build_libleak &
setup_fzf &

echo wait for all background setup jobs to finish
wait
# create file flag to indicate this script has been executed and thus avoid re-execution
bash $zhijiang_pkg_path/scripts/xr_install_useful_tools.sh
touch $file_flag
