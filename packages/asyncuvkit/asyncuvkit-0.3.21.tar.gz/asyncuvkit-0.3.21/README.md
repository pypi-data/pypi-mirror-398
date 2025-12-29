# SecretPkg555

简单的计算包，核心逻辑已编译为二进制保护源码。

## 安装

```bash
pip install secretpkg555
```

## 快速开始

```python
from secretpkg555 import calculate

# 计算两数之和
sum_result = calculate(10, 20)
print(sum_result)  # 30
```

## 技术说明

本包使用 [Nuitka](https://nuitka.net/) 将核心逻辑编译为二进制文件（.pyd/.so），实现源码保护。用户可以正常使用所有功能，但无法查看核心算法的实现细节。

## 许可证

MIT License

## 作者

None555