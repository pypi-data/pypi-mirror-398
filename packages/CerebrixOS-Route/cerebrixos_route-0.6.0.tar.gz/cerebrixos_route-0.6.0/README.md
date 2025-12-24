## To make changes 

### change version in setup.py 

```sh
pip3 install -e . 
```

```sh
python3 -m build 
```

```sh
python3 -m twine upload dist/* 
```

### To use this package 

```sh
pip3 install route-cerebrixos
```

### Example command to register a router

```sh
route-cerebrixos --jwt enroll.txt 
```