import os
import sys
import subprocess

try:
    from zhijiang.scripts.zhijiang_useful_func import *
except Exception as e:
    print(f"# zhijiang, import zhijiang error, error msg is \n {e}")


__version__ = "0.7.52"


def main():
    from termcolor import cprint
    import fire
    import zhijiang as pkg

    pkg_installed_path = pkg.__path__[0]

    def _unzip_if_necessary():
        try:
            subprocess.run("which sudo".split(), check=True, capture_output=True)
        except:
            # if user is root, then "sudo" may not exist
            os.system("apt update > /dev/null")
            os.system("apt install -y sudo")
        zip_file = os.path.join(pkg_installed_path, "zhijiang.7z")
        if not os.path.exists(zip_file):
            return

        if os.path.exists(os.path.expanduser("~/.zhijiang")):
            cprint("~/.zhijiang exists, skip apt update", "red")
        else:
            # apt update here once.
            print(
                "-----------------in apt update, this may take times-------------------",
                flush=True,
            )
            # in docker container, may have not sudo command
            os.system("if [ -z `which sudo` ]; then apt install -y sudo; fi")
            os.system("sudo apt update > /dev/null")

        # clean ~/.zhijiang
        os.system("sudo rm -rf ~/.zhijiang && mkdir -p ~/.zhijiang")
        python_pkg_path = os.path.dirname(pkg_installed_path)
        os.system(f"echo {python_pkg_path} > ~/.zhijiang/python_pkg_path")
        cprint("--------------unzip zhijiang.7z at the first time-------------", "red")

        os.system("sudo apt install -y p7zip-full > /dev/null")
        try:
            dirname = os.path.dirname(pkg_installed_path)
            cmd = f"sudo 7z x {zip_file} -aoa ".split() + [f"-o{dirname}"]
            subprocess.run(cmd, check=True)
            os.system(f"sudo rm -rf {zip_file}")
        except Exception as e:
            cprint("zip file exist, you need to unzip it first", "red")
            print(e)
            sys.exit(1)

    _unzip_if_necessary()
    if not os.path.exists("~/.zhijiang"):
        os.system("mkdir -p ~/.zhijiang")
        python_pkg_path = os.path.dirname(pkg_installed_path)
        os.system(f"echo {python_pkg_path} > ~/.zhijiang/python_pkg_path")

    def setup_rc_files(dry_run=True, restore_rc=False):
        def replace_file(rc_file, dst, restore_rc, dry_run):
            # 1. backup the file if backup file is not existed
            backup = f"{dst}.bk"
            if not os.path.exists(os.path.expanduser(backup)):
                # when user is root, then the rc file is not existed
                if not os.path.exists(os.path.expanduser(dst)):
                    os.system(f"mkdir -p `dirname {dst}` && touch {dst}")
                os.system(f"cp {dst} {backup}")
            # 2. replace it.
            if restore_rc:
                cmd = f"cp {backup} {dst}"
            else:
                if "bashrc" in rc_file:
                    # echo here is to add a new line
                    cmd = f"cp {backup} {dst} && echo >> {dst} && cat {rc_file} >> {dst}"
                else:
                    cmd = f"cp {rc_file} {dst}"
            print(cmd)
            if not dry_run:
                os.system(cmd)

        assert isinstance(
            dry_run, bool
        ), "dry_run should be a boolean, so its value can only by True or False"
        if dry_run:
            cprint(
                "you are in dry run mode, use '--dry_run=False' to disable dry run",
                "red",
            )

        bashrc_related_files = ["bashrc", "alias", "alias2"]
        rc_files_path = os.path.join(pkg_installed_path, "data/rc_files")
        for root, _, files in os.walk(rc_files_path):
            for f in files:
                rc_file = os.path.join(root, f)
                if f not in bashrc_related_files:
                    if f != "htoprc":
                        dst = f"~/.{f}"
                    else:
                        dst = "~/.config/htop/htoprc"
                    replace_file(rc_file, dst, restore_rc, dry_run)
                elif f == "bashrc":
                    # command to source alias and alias2 has being added to bashrc file already
                    dst = "~/.bashrc"
                    replace_file(rc_file, dst, restore_rc, dry_run)

    def install_useful_tools():
        """
        install useful shell commands and python pkg, e.g. profiling tools, debugging tools;
        """
        script_path = os.path.join(
            pkg_installed_path, "scripts/install_useful_tools.sh"
        )
        subprocess.run(f"bash -e {script_path}".split(), check=True)

    def enhance_python():
        """
        add useful functions to python site.py, so you can call them like built-in functions, they are prefixed with zhijxu
        """
        script_path = os.path.join(pkg_installed_path, "scripts/enhance_python.sh")
        subprocess.run(f"bash {script_path}".split(), check=True)

    def info():
        """
        print help info;
        """
        cprint(f"version is {__version__}, dir is {pkg_installed_path}", "red")
        cprint(
            "python function or bash command are all prefixed with zhijiang- ", "red"
        )

    def all():
        """
        run all subcommands
        """
        setup_rc_files(dry_run=False)
        install_useful_tools()
        enhance_python()
        cprint("remember to source ~/.bashrc to make the changes take effect", "red")

    try:
        prefix = "pyfunc"
        # py_func_dict = {
        #     f"{prefix}_onnx_to_pbtxt": _zhijiang_onnx_to_pbtxt,
        # }
        py_func_dict = {}
    except Exception as e:
        cprint(f"#export py funcs failed, it's ok for the first time", "red")
        print(f"the error is {e}")
        py_func_dict = {}

    pkg_commands = {
        "info": info,
        "all": all,
        "setup_rc_files": setup_rc_files,
        "install_useful_tools": install_useful_tools,
        "enhance_python": enhance_python,
    }
    fire.Fire( {**pkg_commands, **py_func_dict})


if __name__ == "__main__":
    main()
