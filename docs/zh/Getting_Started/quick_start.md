# 贡献者入门指南

## 贡献条款

通过为本项目做出贡献，您同意您的贡献将在 Apache License, Version 2.0 下获得许可。
您确认不会因您的贡献而获得付款或补偿。

## 前置条件

- Python 3.12.3
- pip

## 获取 BLADE

1. 点击"Clone or download"，然后点击"Download Zip"。
2. 将仓库解压到任意位置。
3. 导航到包含 `setup.py` 的文件夹，使用以下命令安装仓库：

   ```bash
   pip install .
   ```

   每当您对项目文件夹中的文件进行更改时，需要使用以下命令重新安装包：

   ```bash
   pip install .
   ```

   或者，使用：

   ```bash
   pip install -e .
   ```

   以可编辑模式安装包。这样做之后，您可以更改代码而无需继续安装。

4. `gymnasium` 是希望将 BLADE 用作 Gym 环境的用户的依赖项。在这种情况下，使用：

   ```bash
   pip install .[gym]
   ```

   或：

   ```bash
   pip install -e .[gym]
   ```

## 运行演示

1. 运行 `scripts/simple_demo/demo.py` 中提供的演示。
2. 演示将输出一个场景文件，可以使用前端 GUI 查看。

## 设置客户端

1. 点击"Clone or download"，然后点击"Download Zip"。
2. 将仓库解压到任意位置。
3. 导航到 `client` 文件夹，使用以下命令安装客户端：

   ```bash
   npm install
   ```

   要在没有服务器的情况下运行客户端：

   ```bash
   npm run standalone
   ```
