# 前置条件
1. Python 3.12.3
2. pip

# 快速入门指南
## 获取 BLADE
1. 点击 "Clone or download"，然后选择 "Download Zip"。
2. 将仓库解压到任意位置。
3. 导航到包含 `setup.py` 的文件夹，使用 `pip install .` 安装仓库。每次修改项目文件夹中的文件后，需要重新使用 `pip install .` 安装包。或者，使用 `pip install -e .` 以可编辑模式安装包。这样修改代码后无需重复安装。
4. [gymnasium](https://gymnasium.farama.org/) 是希望将 BLADE 用作 Gym 环境的用户的依赖项。这种情况下，使用 `pip install .[gym]` 或 `pip install -e .[gym]` 进行安装。

## 运行演示
1. 运行 `scripts/simple_demo/demo.py` 中提供的演示脚本。
2. 演示将输出一个想定文件，可使用前端 GUI 查看。
