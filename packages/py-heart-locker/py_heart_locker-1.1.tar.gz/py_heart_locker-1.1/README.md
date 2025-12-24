# py-heart-locker

> python 进程锁定器，避免同一时间重复执行相同的脚本

------

## 运行环境

![](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)


## 使用说明

1. 安装: `python -m pip install py-heart-locker`
2. 在代码中使用：

```python
from lock import locker

def main() :
    if locker.islocked() :
        return
    locker.lock()

    core()


def core() :
    # 业务核心代码


if __name__ == '__main__' :
    main()
    
```
