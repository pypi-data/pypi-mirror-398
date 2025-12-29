# SCIV

> SCIV: Unveiling the pivotal cell types involved in variant function regulation at a single-cell resolution

> SCIV: 以单细胞分辨率揭示参与突变功能调节的关键细胞类型

## 1. 介绍

## 2. 上传

> upload

> test

```shell
py -m build
twine check dist/*
twine upload --repository testpypi dist/*
```

> production

```shell
py -m build
twine check dist/*
twine upload dist/*
```

## 3. 使用

```shell
vim ~/.bashrc
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
source ~/.bashrc

```

> test

```shell
pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
pip install sciv -i https://test.pypi.org/simple/
```

> production

```shell
pip install sciv

```
