# add usefule python function to builtins, so they can be call directly
# these functions will be prefixed with zhijxu to avoid name conflict
sitepy_path=$(python -c "import site; print(site.__file__)" | tail -1)
backup=$(dirname $sitepy_path)/site.py_bk
if [ -f $backup ]; then
  ## restore site.py
  sudo cp $backup $sitepy_path
else
  ## site.py is unchanged, so backup it
  sudo cp $sitepy_path $backup
fi

sudo chmod 777 $sitepy_path

cat >>$sitepy_path <<EOF
#
# add useful function to builtins, so they can be called directly without import
try:
  import builtins
  import inspect
  import zhijiang
  setattr(builtins, "zhijiang", zhijiang)
  from zhijiang.scripts import zhijiang_useful_func
  func_set = {
      name: obj
      for name, obj in inspect.getmembers(zhijiang_useful_func) if name.startswith("zhijiang_")
  }
  for name, obj in func_set.items():
      setattr(builtins, name, obj)
except Exception as e:
  print(f"# init fail at {__file__}")
  print(f"# error: {e}")
  pass

EOF
