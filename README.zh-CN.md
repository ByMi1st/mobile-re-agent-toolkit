# Mobile RE Agent Toolkit

[![Tests](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | 简体中文

一个面向授权 Android 逆向分析的轻量终端工具包。它不是 Agent 框架、反编译器，也不是需要常驻加载的大型 MCP 工具集合。

## 命令

| 命令 | 功能 |
|---|---|
| `fingerprint` | 流式计算文件 SHA-256 和大小 |
| `search-exports` | 有限长度文本检索，附文件和行号；不是语义引用 |
| `summarize-events` | JSONL 基本事件校验与计数 |
| `locate-dex` | 查找定义或提及某个类或字符串的根 DEX | 调用图或运行时使用 |
| `scope-apk` | 生成只含所选根 DEX 的分析用 APK | 可安装或完整的 APK |
| `generate-java-hook` | 生成精确 Java 重载的探针源码 |
| `generate-native-hook` | 生成模块/符号或偏移探针，记录原始参数、返回值和有限二进制快照 |
| `run` | 明确指定传输与目标的 Frida spawn/attach、消息采集及清理 |

离线命令只需要 Python，运行时依赖可选安装。仓库不包含私有样本、生产流量或凭据。

## 安装与试用

需要 Python 3.10 或更高版本。在仓库目录中执行：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
mrat --help
mrat fingerprint examples/exports/0x1000.c
mrat search-exports examples/exports memcpy --limit 10
mrat summarize-events examples/events.jsonl
mrat generate-java-hook \
  --class 'example.Target' --method run \
  --overload java.lang.String --out /tmp/example-hook.js
```

运行时采集另安装 `python -m pip install ".[runtime]"`。
[动态使用说明](docs/runtime.zh-CN.md)包含执行方式、副作用、限制与端到端合成样例。尚未发布到 PyPI。[安装说明](docs/setup.md)包含获取仓库、免安装运行、退出码和手动执行探针的依赖条件。

## 探针记录什么

Java 调用事件包含 PID/TID、调用编号、方法与重载、参数、返回值、异常、堆栈，以及可选的业务场景／请求标签。

场景和请求标签由调用者提供，不代表工具自动确认了因果关系。值以有限长度的文本预览保存，不是无损 Java 对象或二进制序列化。耗时使用墙钟毫秒，不适合精确性能测试。

日志发送失败不会替换原方法的返回值或异常。但插桩本身仍可能影响时序和行为，观察标签不代表进程未受干预。脚本需要可用的 Frida Java bridge；目前尚未验证真实 Android 设备兼容性。

## 项目范围

JADX、IDA、Unicorn 和语义引用工具仍作为外部分析工具使用，本仓库不整体迁入或重新封装它们。不包含证书绕过、内核探针、刷机包、公司工具、RPC 服务或目标专用算法。

v0.2.0 已实现通用 Runner 和 Native 探针生成；实际兼容范围以[真实验证记录](docs/verification.md)为准，Android 真机仍未验证。

相关文档：[实现状态](docs/status.md) · [架构与验证约束](docs/architecture.md) · [后续计划](docs/roadmap.md) · [实际工作流](docs/workflow.zh-CN.md)。部分文档目前仅提供英文。

## 开发与测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Node.js 用于可选的合成 JavaScript 执行测试；未安装时该项会明确跳过。Python 或合成测试通过，不代表真机兼容性验证通过。

## 许可证

Copyright 2026 Meb1us (GitHub: ByMi1st)。使用 [Apache-2.0](LICENSE) 许可证。标准许可证附录中的占位符是应用示例，项目版权声明位于许可证顶部。
