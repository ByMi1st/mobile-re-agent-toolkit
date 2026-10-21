# Mobile RE Agent Toolkit

[![Tests](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | 简体中文

Mobile RE Agent Toolkit（`mrat`）是一套给 agent 用的逆向工具链。它提供一小组终端命令，输出可预测：每个结果都是 JSON，每个输入文件都有哈希，每条结论都写明它能证明什么、不能证明什么。

它不替代 jadx、IDA 或 Frida，而是把它们包装起来，让 agent 每次都以同样的方式调用，证据也保留在磁盘上。

## agent 怎么用它

假设你让 agent 去做这件事："找到这个 App 构造签名头的地方，并列出谁调用了它。"典型流程是：

1. `fingerprint` 记录样本的 SHA-256，之后的所有结果都绑定到这份样本上。
2. `locate-dex` 找到定义该类的 DEX 文件。
3. `scope-apk` 生成一个只包含该 DEX 的较小 APK，避免 jadx 因内存不足失败。
4. `decompile-class` 产出该类的可读源码。
5. `xref-method` 用项目中的 xref.jar 列出静态调用方。
6. 对应的 `generate-*-hook` 生成探针，`run` 在你明确指定的设备上观察目标。

每一步都把输出写进文件，每个结果也都列出自己的局限。agent 可以从中断的地方继续，你也可以对照文件核对每一条结论。

## 命令

### 样本与基线

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `fingerprint` | 计算文件的 SHA-256 并记录大小。建议先跑它。 | 样本从哪里来 |
| `diff-binary` | 按哈希比较两个二进制；ELF 文件额外按节区比较。版本升级后、重跑之前用它判断变化范围。 | 某个变化做了什么 |

### Java / DEX

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `locate-dex` | 找出哪个根目录下的 `classes*.dex` 定义或提到了某个类或字符串。 | 代码在运行时是否被调用 |
| `scope-apk` | 生成只包含你所选 DEX 的分析用 APK。整体索引大 APK 容易耗尽内存，所以先缩小范围。 | 你没选中的 DEX 里有什么 |
| `decompile-class` | 调用你指定的 jadx CLI 反编译一个类。使用 `--show-bad-code`，错误的输出要先人工检查。 | 反编译结果是否正确 |
| `xref-method` | 用你通过 `--jar` 指定的 xref.jar 列出一个方法的静态引用。 | 反射、动态分派或运行时调用 |
| `search-exports` | 在 jadx 或 IDA 导出的文本里搜索，返回文件和行号。 | 语义上的引用关系 |

### Native

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `ida-run` | 在数据库上无头运行 IDA 批处理脚本，并记录日志以及运行前后的数据库哈希。 | 脚本的结果，或 IDA 本身做了什么 |

### 动态（Frida）

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `generate-java-hook` | 为一个精确的 Java 重载生成探针。 | 探针是否真的在设备上运行 |
| `generate-native-hook` | 为导出符号或偏移生成探针，记录原始参数、返回值和有限长度的缓冲区快照。 | 参数的真实类型，或构建是否一致 |
| `run` | 在你指定的目标（设备、远程地址或本机；按 PID 附加或 spawn）上运行脚本，收集消息并清理。 | 采集窗口之外目标做了什么 |

### 证据

| 命令 | 它做什么 | 它不能证明什么 |
|---|---|---|
| `summarize-events` | 检查 JSONL 事件文件的基本结构并统计事件数。 | 采集是否完整或真实 |

离线命令只需要 Python，运行时的依赖可选安装。

## 安装

需要 Python 3.10 或更高版本。在仓库目录中执行：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
mrat --help
```

用仓库自带的合成样例试一下：

```bash
mrat fingerprint examples/exports/0x1000.c
mrat search-exports examples/exports memcpy --limit 10
mrat summarize-events examples/events.jsonl
mrat generate-java-hook \
  --class 'example.Target' --method run \
  --overload java.lang.String --out /tmp/example-hook.js
```

需要运行时采集时，再执行 `python -m pip install ".[runtime]"`。[动态使用说明](docs/guides/runtime.zh-CN.md)列出了每个命令的实际副作用；[安装说明](docs/guides/setup.md)包含退出码，以及手动运行生成脚本所需的前提条件。

## 自备的工具

仓库不附带 jadx、IDA、Frida、xref.jar 或任何应用样本。你需要自己安装或获取它们，并负责它们的许可证和版本。通过 `--jadx`、`--jar`、`--idat`、`--java` 等参数显式指定路径；如果不传，命令会去 `PATH` 里找，找不到就明确报错。

## 能证明什么，不能证明什么

- 静态结果在被其他证据确认之前都只是候选。[工作流文档](docs/guides/workflow.zh-CN.md)说明了证据等级（`confirmed_static`、`candidate`、`contradicted`）以及如何使用。
- 生成的 Java 探针会把调用、参数和返回值以文本预览的形式记录下来。日志失败不会改变原方法的结果，但插桩本身仍可能改变时序和行为。
- 还没有在 Android 真机上测试。native 探针只在源码构建的合成样例上验证过；真实的 jadx 与 IDA 路径也没有在 CI 中运行。[验证记录](docs/reference/verification.md)列出了实际跑过的内容。

## 仓库结构

```text
src/mrat/
  cli.py          命令行入口
  core/           数据模型与离线工具：哈希、检索、JSONL 检查
  static/         DEX 定位、反编译、交叉引用、IDA 运行、二进制 diff
  runtime/        探针生成与 Frida runner
docs/guides/      使用指南：工作流、运行时、安装
docs/reference/   状态、架构、路线图、验证记录、发布清单
examples/         仅包含合成样例
scripts/          真实环境验证脚本
tests/            单元测试与合成测试
```

## 文档

- [工作流（中文）](docs/guides/workflow.zh-CN.md)：静态分析的完整步骤与常见问题。
- [动态使用（中文）](docs/guides/runtime.zh-CN.md)：采集、native 探针、清理与限制。
- [安装](docs/guides/setup.md)：安装、退出码与手动执行脚本。
- [状态](docs/reference/status.md)：已实现、仅用桩或合成数据测试、尚未完成的内容。
- [架构](docs/reference/architecture.md)与[路线图](docs/reference/roadmap.md)。

## 开发

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Node.js 是可选的。没有安装时，合成 JavaScript 测试会跳过。Python 测试通过并不代表设备兼容。贡献内容应保持与具体目标无关，见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 适用范围与责任

只用于你拥有或获得授权评估的软件。本项目不包含、也不会加入证书绕过、内核探针、刷机包、公司内部工具、RPC 服务或针对特定目标的算法。

## 许可证

Copyright 2026 Meb1us (GitHub: ByMi1st)。使用 [Apache-2.0](LICENSE) 许可证。许可证附录中的占位符只是标准示例，项目版权声明位于许可证顶部。
