function zhijiang-utils-add-rw-right() {
    if [[ -z $1 || $1 == --help || $1 == --h ]]; then
        echo "add_rw_right <path|file|python_pkg_name>"
        echo "if 'path|file' not exists then try to find it as python pkg and add rw right"
        echo "pkg name can be partial"
        return
    fi
    if [[ -d $1 ]]; then
        echo adding rw right to $1
        sudo chmod -R a+rw $1
    elif [[ -f $1 ]]; then
        echo adding rw right to $(dirname $1)
        sudo chmod a+rw $(dirname $1)
    else
        tmp=$(pip list | grep -i $1 | awk '{print $1}')
        read -ra pkgs <<<${tmp[@]}
        if [[ ${#pkgs[@]} -gt 1 ]]; then
            _colored_output more than 1 pkg found, then treat args1 as exact name
            pkgs=($1)
        fi

        pkg=${pkgs[0]}
        # pkg name is not always equal to import name, so try them both
        pkg_path=$(python -c "import $pkg; print($pkg.__path__[0])" 2>/dev/null)
        if [[ -z $pkg_path ]]; then
            pkg_path=$(python -c "import $1; print($1.__path__[0])" 2>/dev/null)
        fi

        if [[ -z $pkg_path ]]; then
            pkg=$(echo $pkg | tr - _)
            python_site_path=$(pip show $pkg | grep Location | awk '{print $2}' -)
            pkg_top_level_file=$python_site_path/$pkg*.dist-info/top_level.txt
            pkg_import_name=$(cat $pkg_top_level_file | awk '{print $1}')
            pkg_path=$(python -c "import $pkg_import_name; print($pkg_import_name.__path__[0])" 2>/dev/null)
        fi

        if [[ -z $pkg_path ]]; then
            _colored_output "can not find pkg path for $1 or $pkg"
            return
        fi
        echo adding rw right to $pkg_path
        sudo chmod -R a+rw $pkg_path
    fi
}
