utest-manage 管理工具

概述
- 提供脚手架与工程管理能力：`init`、`new-case`、`build`、`clean`。
- 与核心包解耦，作为独立可安装的 CLI 分发。

新增能力
- `update-core`：从远程模板（失败回退本地模板）更新项目中的核心文件，可按需选择性更新单个或多个文件。

命令说明
- 查看帮助：
```bash
utest-manage --help
```

- 初始化仅脚本目录（依赖 utest-core，不复制 core 源码）：
```bash
utest-manage init .
utest-manage init ./my_tests --force
```

说明：`init` 默认从内置远程模板下载并直接解压到目标目录，若远程不可用则回退到本地 `manage/templates`。

- 新建示例用例：
```bash
utest-manage new-case my_login_test
```

- 构建与清理：
```bash
utest-manage build
utest-manage clean
```

### 更新核心文件：update-core

用于将「模板中的核心文件」同步到当前或指定目录。默认更新全部核心项，支持 `--files` 选择性更新，`--force` 覆盖。

核心项清单：
- uv.toml
- update_config.py
- start_test.py
- run.sh
- requirements.txt
- build.py
- test_cases/internal/ 目录

用法：
```bash
# 在当前目录更新全部核心项（若存在且不加 --force，将跳过）
utest-manage update-core

# 在指定目录更新全部核心项
utest-manage update-core /path/to/project

# 仅更新部分文件（可多次传入 --files，或用逗号分隔）
utest-manage update-core --files uv.toml --files start_test
utest-manage update-core --files "uv.toml,run.sh,internal"

# 强制覆盖目标文件/目录
utest-manage update-core --force
utest-manage update-core /path/to/project --files internal --force
```

`--files` 支持的别名：
- uv.toml｜uvtoml
- update_config（映射到 update_config.py）
- start_test（映射到 start_test.py）
- run.sh｜run_sh
- requirements｜requirements.txt
- build｜build.py
- internal（映射到 test_cases/internal）

行为说明：
- 源优先来自远程ZIP模板（内置下载链接），失败时自动回退到本地 `manage/templates`；
- 目录项（如 `internal`）在 `--force` 时会先删除再拷贝，确保与模板一致；
- 未加 `--force` 时，已存在的文件将被跳过（保护本地改动）。

## 编译

```shell
uv build
```

## 发布包

```shell
uv publish --publish-url https://mirrors.tencent.com/repository/pypi/tencent_pypi/simple
```

## 用户安装

```shell
uv tool install utest-auto-manage --index-url https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://mirrors.tencent.com/repository/pypi/tencent_pypi/simple
```