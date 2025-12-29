# PixelArrayLib - PixelArray Python开发工具库

PixelArrayLib是一个功能丰富的Python开发工具库，包含阿里云服务、数据库工具、装饰器、监控等功能，同时提供便捷的命令行工具。

## 安装

### 基础安装

```bash
pip install pixelarraylib
```

**注意**: 基础安装不包含任何依赖，只安装核心包。使用功能模块前需要安装相应的依赖。

### 安装所有依赖

```bash
# 安装所有依赖（推荐，适合需要使用多个模块的场景）
pip install pixelarraylib[all]
```

### 可选依赖安装

如果你只需要使用特定模块的功能，可以按需安装特定模块的依赖（这样可以减少安装的依赖包数量）：

#### 基础模块依赖

```bash
# 只安装MySQL工具相关依赖
pip install pixelarraylib[mysql]

# 只安装Redis工具相关依赖
pip install pixelarraylib[redis]

# 只安装监控工具相关依赖
pip install pixelarraylib[monitor]

# 只安装网络工具相关依赖
pip install pixelarraylib[net]

# 只安装系统工具相关依赖
pip install pixelarraylib[system]

# 只安装GitLab工具相关依赖
pip install pixelarraylib[gitlab]

# 组合安装多个模块
pip install pixelarraylib[mysql,redis]
```

#### 阿里云服务依赖（细分）

```bash
# 只安装OSS对象存储相关依赖
pip install pixelarraylib[aliyun-oss]

# 只安装STS安全令牌服务相关依赖
pip install pixelarraylib[aliyun-sts]

# 只安装SMS短信服务相关依赖
pip install pixelarraylib[aliyun-sms]

# 只安装邮件服务相关依赖
pip install pixelarraylib[aliyun-email]

# 只安装内容安全扫描相关依赖
pip install pixelarraylib[aliyun-content-scanner]

# 只安装域名服务相关依赖
pip install pixelarraylib[aliyun-domain]

# 只安装容器镜像服务相关依赖
pip install pixelarraylib[aliyun-acr]

# 只安装账单服务相关依赖
pip install pixelarraylib[aliyun-billing]

# 只安装ECS弹性计算相关依赖
pip install pixelarraylib[aliyun-ecs]

# 只安装EIP弹性公网IP相关依赖
pip install pixelarraylib[aliyun-eip]

# 只安装ECI容器实例相关依赖
pip install pixelarraylib[aliyun-eci]

# 只安装FC函数计算相关依赖
pip install pixelarraylib[aliyun-fc]

# 安装所有阿里云服务相关依赖
pip install pixelarraylib[aliyun]

# 组合安装多个阿里云服务
pip install pixelarraylib[aliyun-oss,aliyun-sms]
```


**可选依赖说明：**

**基础模块：**
- `mysql`: MySQL数据库工具（pymysql、aiomysql）及相关依赖
- `redis`: Redis数据库工具及相关依赖
- `monitor`: 监控告警工具（飞书通知等）及相关依赖
- `net`: 网络请求工具（requests、aiohttp）及相关依赖
- `system`: 系统工具（加密、SSH等）及相关依赖
- `gitlab`: GitLab工具（PyPI包管理、代码分析等）及相关依赖

**阿里云服务（细分）：**
- `aliyun-oss`: OSS对象存储服务
- `aliyun-sts`: STS安全令牌服务（需要redis依赖）
- `aliyun-sms`: SMS短信服务
- `aliyun-email`: 邮件服务（DM）
- `aliyun-content-scanner`: 内容安全扫描服务（Green）
- `aliyun-domain`: 域名服务（DNS）
- `aliyun-acr`: 容器镜像服务
- `aliyun-billing`: 账单服务
- `aliyun-ecs`: ECS弹性计算服务
- `aliyun-eip`: EIP弹性公网IP服务
- `aliyun-eci`: ECI容器实例服务（需要eip依赖）
- `aliyun-fc`: FC函数计算服务（需要system依赖）
- `aliyun`: 所有阿里云服务依赖（完整版）

**完整安装：**
- `all`: 所有可选依赖

## 使用方法

### 1. Python程序中使用

```python
# 导入pixelarraylib模块
import pixelarraylib

# 使用各种功能模块
from pixelarraylib.aliyun import some_service
from pixelarraylib.db_utils import database_tools
from pixelarraylib.decorators import useful_decorators
```

### 2. 命令行工具使用

安装后，你可以在命令行中直接使用 `pixelarraylib` 命令：

#### 创建测试用例文件
```bash
# 一键创建所有测试用例文件
pixelarraylib create_test_case_files
```

## 功能特性

- **阿里云服务集成**: 包含CMS、Green、DM、FC、SMS、STS等服务
- **数据库工具**: MySQL、Redis等数据库操作工具
- **Web框架**: FastAPI集成
- **实用工具**: 二维码生成、加密解密、XML处理等
- **命令行工具**: 测试用例生成、代码统计等实用脚本

## 开发

### 本地开发安装

```bash
# 克隆仓库
git clone https://gitlab.com/pixelarrayai/general_pythondevutils_lib.git
cd general_pythondevutils_lib

# 安装开发依赖
pip install -e .

# 测试命令行工具
pixelarraylib --help
```

### 添加新的命令行工具

1. 在 `pixelarraylib/scripts/` 目录下创建新的脚本文件
2. 在 `pixelarraylib/__main__.py` 中添加新的命令选项
3. 更新 `pixelarraylib/scripts/__init__.py` 导出新功能

## 许可证

MIT License

## 作者

Lu qi (qi.lu@pixelarrayai.com) 