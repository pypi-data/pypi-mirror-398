# bo-atk-common

This package contains atk enforcement common entities and components

# Build procedure

Delete the files in the `dist` folder

Increment the version number in the `setup.py` file

Build the new wheel file:
```shell
python setup.py sdist bdist_wheel
```

Upload the new wheel file:
```shell
python -m twine upload dist/*
```



