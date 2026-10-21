# Mobile RE Agent Toolkit

[![Tests](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | 简体中文

一个面向授权 Android 逆向分析的轻量终端工具包。它不是 Agent 框架、反编译器，也不是需要常驻加载的大型 MCP 工具集合。

## v0.1.0：四个命令

| 命令 | 功能 | 不能据此证明什么 |
|---|---|---|
| `fingerprint` | 流式计算文件 SHA-256，记录文件大小 | 文件真实性或发布者身份 |
| `search-exports` | 检索本地文本导出，返回文件、行号和输出限制信息 | 语义交叉引用或真实运行时调用 |
| `summarize-events` | 校验 JSONL 基本事件格式，统计事件类型 | 采集内容真实或覆盖完整 |
| `generate-java-hook` | 为一个明确的 Java 方法重载生成 Frida 探针 | 真机兼容性或正在进行的采集 |

所有命令都在本地执行。生成探针不会连接手机；仓库不包含私有应用样本、生产流量或凭据。

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

尚未发布到 PyPI。[安装说明](docs/setup.md)包含获取仓库、免安装运行、退出码和手动执行探针的依赖条件。

## 探针记录什么

Java 调用事件包含 PID/TID、调用编号、方法与重载、参数、返回值、异常、堆栈，以及可选的业务场景／请求标签。

场景和请求标签由调用者提供，不代表工具自动确认了因果关系。值以有限长度的文本预览保存，不是无损 Java 对象或二进制序列化。耗时使用墙钟毫秒，不适合精确性能测试。

日志发送失败不会替换原方法的返回值或异常。但插桩本身仍可能影响时序和行为，观察标签不代表进程未受干预。脚本需要可用的 Frida Java bridge；目前尚未验证真实 Android 设备兼容性。

## 项目范围

JADX、IDA、Unicorn 和语义引用工具仍作为外部分析工具使用，本仓库不整体迁入或重新封装它们。不包含证书绕过、内核探针、刷机包、公司工具、RPC 服务或目标专用算法。

后续先做通用 Frida 会话 Runner，再做 Native 探针生成器；两者都不属于 v0.1.0 已实现功能。

相关文档：[实现状态](docs/status.md) · [架构与验证约束](docs/architecture.md) · [后续计划](docs/roadmap.md) · [实际工作流](docs/workflow.zh-CN.md)。部分文档目前仅提供英文。

## 开发与测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Node.js 用于可选的合成 JavaScript 执行测试；未安装时该项会明确跳过。Python 或合成测试通过，不代表真机兼容性验证通过。

## 许可证

Copyright 2026 Meb1us (GitHub: ByMi1st)。使用 [Apache-2.0](LICENSE) 许可证。标准许可证附录中的占位符是应用示例，项目版权声明位于许可证顶部。
