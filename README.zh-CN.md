# Mobile RE Agent Toolkit

[![Tests](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | 简体中文

Mobile RE Agent Toolkit（`mrat`）是一套面向 Android 逆向、由 agent 驱动的命令行工具链。每个命令都输出 JSON，记录输入文件的哈希，并说明它的结果不能证明什么。

它不替代 jadx、IDA 或 Frida，而是把它们包装起来，让每次调用都可以复现，每个结果都保存为文件，供 agent 或审阅者逐项核对。

## 用途

对一个已获授权的样本，典型工作流如下：

1. `fingerprint` 记录样本的 SHA-256，之后的结果都引用这个哈希。
2. `locate-dex` 找出定义某个类或包含某个字符串的 DEX 文件。
3. `scope-apk` 只保留你选中的 DEX，生成更小的分析用 APK。
4. `decompile-class` 调用 jadx CLI 得到单个类的可读源码。
5. `xref-method` 或 `xref-serve` 列出静态调用方，所用的 xref 工具可以由本仓库构建，也可以自备。
6. `generate-java-hook` 或 `generate-native-hook` 生成探针，`run` 在你明确指定的目标上观察。

每一步都把输出写入磁盘。结果会列出自己的局限，因此 agent 可以从文件继续，审阅者也能逐条核对。

## 命令

### 样本与基线

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `fingerprint` | 计算文件的 SHA-256 和大小。 | 文件从哪里来 |
| `diff-binary` | 按哈希比较两个二进制；ELF 文件额外按节区比较。 | 变化做了什么 |

### DEX 与 Java

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `locate-dex` | 找出定义或提及某个类或字符串的根 `classes*.dex`。 | 代码在运行时是否被使用 |
| `scope-apk` | 生成只包含所选 DEX 的分析用 APK。 | 被排除的 DEX 里有什么 |
| `decompile-class` | 调用你指定的 jadx CLI 反编译一个类，使用 `--show-bad-code`。 | 输出是否正确 |
| `xref-method` | 用 xref jar 列出一个方法的静态引用。 | 反射、动态分派或运行时调用 |
| `xref-serve` | 为一个 APK 常驻一个 xref 进程，从标准输入逐行接收 JSON 请求。 | 同 `xref-method` |
| `search-exports` | 在 jadx 或 IDA 的文本导出中搜索，返回文件和行号。 | 语义上的引用关系 |

### Native

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `ida-run` | 运行 IDA 无头批处理脚本，记录运行前后的日志和数据库哈希。 | 脚本的结果 |

### 动态（Frida）

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `generate-java-hook` | 为一个精确的 Java 重载生成探针。 | 探针是否在设备上运行过 |
| `generate-native-hook` | 为导出符号或偏移生成探针，记录原始参数、返回值和有限长度的缓冲区快照。 | 参数的真实类型，或构建是否一致 |
| `run` | 在你指定的目标（本机、设备或远程；按 PID 附加或 spawn）上运行脚本，收集消息并清理。 | 采集窗口之外发生了什么 |

### 证据

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `summarize-events` | 检查 JSONL 事件文件的基本结构并统计事件数。 | 采集是否完整或准确 |

离线命令只需要 Python。运行时与 Java 相关的工具是可选的。

## 快速开始

需要 Python 3.10 或更高版本。

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
mrat --help
```

试用仓库自带的合成样例：

```bash
mrat fingerprint examples/exports/0x1000.c
mrat search-exports examples/exports memcpy --limit 10
mrat summarize-events examples/events.jsonl
mrat generate-java-hook --class 'example.Target' --method run \
  --overload java.lang.String --out /tmp/example-hook.js
```

运行时采集需要可选依赖：`python -m pip install ".[runtime]"`。各运行时命令的副作用见 [docs/guides/runtime.zh-CN.md](docs/guides/runtime.zh-CN.md)，退出码见 [docs/guides/setup.md](docs/guides/setup.md)。

## 自备的工具

仓库不附带 jadx、IDA、Frida 或任何应用样本。你需要自己安装这些工具，并负责它们的许可证和版本。通过 `--jadx`、`--idat`、`--java`、`--jar` 显式指定路径；如果省略，命令会去 `PATH` 中查找，找不到时明确报错。

### xref 工具

`tools/xref` 是 `xref-method` 和 `xref-serve` 所用的 xref 命令行工具源码。用 Maven 构建（需要 JDK 11 或更高版本）：

```bash
mvn -f tools/xref/pom.xml package
export MRAT_XREF_JAR="$PWD/tools/xref/target/jadx-xrefs-cli.jar"
```

构建固定使用 jadx 1.5.3。默认按需加载以保证速度；设置 `XREF_FULL_INDEX=1` 会先反编译所有类，较慢但索引最完整。`inspect-class` 始终使用完整索引。

## 证据与局限

- 静态结果在其他证据支持之前只是候选。[工作流文档](docs/guides/workflow.zh-CN.md)说明了证据等级（`confirmed_static`、`candidate`、`contradicted`）。
- 生成的 Java 探针以文本预览的形式记录参数和返回值。日志失败不会改变原方法的结果，但插桩本身仍可能改变时序和行为。
- Native 探针只在源码构建的合成样例上验证过，Android 真机尚未测试。
- 静态链路在一个公开的 CTF 训练 APK 上完整运行过一次，具体运行内容见[验证记录](docs/reference/verification.md)。

## 设计原则

- 输入显式：设备、进程、工具路径和输出文件都必须明确指定。
- 没有隐式副作用：工具不安装守护进程，不修改 ADB 转发，不改变设备或系统设置。
- 默认不覆盖输出。
- 每个结果都说明自己的局限。
- 贡献内容保持与具体目标无关，并使用合成样例，见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 仓库结构

```text
src/mrat/
  cli.py          命令行入口
  core/           数据模型与离线工具：哈希、检索、JSONL 检查
  static/         DEX 定位、反编译、交叉引用、IDA 运行、二进制 diff
  runtime/        探针生成与 Frida runner
tools/xref/       xref 工具源码（Maven）
docs/guides/      使用指南：工作流、运行时、安装
docs/reference/   状态、架构、路线图、验证记录、发布清单
examples/         仅包含合成样例
scripts/          真实环境验证脚本
tests/            单元测试与合成测试
```

## 状态

[docs/reference/status.md](docs/reference/status.md) 说明了已实现的内容、仅用桩或合成数据验证过的内容，以及尚未实现的内容。Java 运行时发现和 native 构建身份校验尚未实现。

## 开发

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Node.js 是可选的；未安装时合成 JavaScript 测试会跳过。Python 测试通过并不代表设备兼容。

## 适用范围

只用于你拥有或获得授权评估的软件。本项目不包含证书绕过、内核探针、刷机包、公司内部工具、RPC 服务或针对特定目标的算法。

## 文档

- [工作流（中文）](docs/guides/workflow.zh-CN.md)：静态分析的完整步骤。
- [动态使用（中文）](docs/guides/runtime.zh-CN.md)：采集、native 探针、清理与限制。
- [安装](docs/guides/setup.md)：安装、退出码与手动执行脚本。
- [状态](docs/reference/status.md)、[架构](docs/reference/architecture.md)、[路线图](docs/reference/roadmap.md)。

## 许可证

Copyright 2026 Meb1us (GitHub: ByMi1st)。使用 [Apache-2.0](LICENSE) 许可证。
