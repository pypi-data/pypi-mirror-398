# Description
    ..........................
    

# Todo:
 - update build config to pyproject.toml 
 - Add Merge command in DictObj

# Build on Windows in Pycharm
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass 
```

```
python setup.py sdist
rm .\dist\* 
python -m build
twine upload dist/*
```


# Notes
 - .\tools\build.ps1 
 - pip install --upgrade ROTools



