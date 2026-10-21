# Frida Runner 与 Native 探针

## 依赖与适用范围

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install '.[runtime]'
```

Frida 为可选依赖：不安装也能执行离线命令及生成脚本。Python API 懒加载，不启动 MCP 服务。用户自己提供有权限的目标进程和匹配的 Frida 服务；工具不部署 daemon，不创建/删除 ADB 转发，不改 SELinux、代理、Root 或全局 Agent 配置。

macOS 本地注入受系统权限与 Frida 版本影响。Android Java 探针还需要 Java bridge；Frida 17 API 模式并不自动提供它。生成器不负责下载或编译 bridge。没有 Android 真机实测前，不能把本机/CI结果泛化为手机兼容性。

## 生成探针

Java 精确重载的命令保持不变。Native 探针必须选择模块和一个导出符号或模块内偏移：

```bash
mrat generate-native-hook --module libexample.so --symbol example_add \
  --arg-count 3 --buffer-arg 2 --buffer-size 4 --backtrace \
  --max-calls 100 --out /tmp/native-probe.js
```

也可以用 `--offset 0x1234` 替代 `--symbol`。先校验目标版本再填写偏移；探针会检查地址属于所选模块且具有执行权限，但没有计算模块代码哈希，事件明确标为 `build_hash=not_verified`。

- 参数仅记录前 0–8 个通用 ABI 参数槽的原始指针表示，不自动解码浮点、结构体或所有 ABI。
- 返回值记录原始表示及低 32 位有符号解释，后者不代表函数实际返回类型。
- 可选缓冲区读取入口和返回时同一参数地址的固定字节数，上限 4096；读取失败单独发事件，不伪造为空数据。
- 可选回溯是有限的原始地址，不能声称完整调用图。
- 使用模块 observer 捕获晚加载模块；不支持该 API 且模块未加载时明确报错。
- 达到调用数上限会发 `probe_limit`，后续调用省略；Runner 标为 partial，不作为完整记录。

## 执行与目标选择

必须选择一个传输以及 PID 或 spawn，不自动选第一台设备。

```bash
# 已连接的明确设备，只 attach 指定 PID
mrat run --device-id SERIAL --pid PID --script /tmp/native-probe.js \
  --duration 10 --require-ready --out /tmp/capture-unique.jsonl

# 已由操作者配置好的 remote endpoint
mrat run --remote HOST:PORT --spawn com.example.training \
  --script /tmp/native-probe.js --duration 10 --require-ready \
  --out /tmp/spawn-unique.jsonl
```

`SERIAL/PID/HOST/PORT` 要替换为自己的目标值。Runner 不会验证 PID 对应某个包名，操作者必须预先确认；进程重用、任意异步因果和子进程追踪不是本版本保证。

`--local --pid PID` 或 `--local --spawn /absolute/path/to/fixture ARG` 用于本机合成实验。spawn 的参数若以 `--` 开头，建议使用小型启动脚本消除 argparse 歧义。

## 生命周期与失败

spawn → attach → 绑定 message/detached → load → resume → 有限采集 → unload → detach → 终止本次 spawn 的进程。attach 的外部进程只 detach，绝不 kill/resume。spawn 模式结束时会终止目标，这是明确的副作用，不适合希望保持运行的外部 APP；这种场景选择 attach。

脚本仍可以执行任意用户代码；unload 不保证回滚任意脚本副作用。启动超时默认 15 秒，采集时长默认 10 秒。cleanup 操作各有独立超时；清理失败会记录 action 与错误，不能承诺故障时一定不存在悬挂进程。

SIGINT/SIGTERM 请求停止并执行清理；API 初始化期间可能等到当前操作或 setup deadline 返回。强杀进程、宿主崩溃和掉电不保证清理。CLI 可被外部进程超时监督，但外部强杀的清理责任必须单独考虑。

`--require-ready` 要求脚本发出 `probe_ready`，防止“脚本加载成功但没有 hook 到目标”被误记成功。自定义脚本可以不使用此开关；这种情况下成功仅表示采集窗口正常结束，不能证明 hook 已安装。

## 输出与完整性

每行有 schema_version、session_id、PID、主机单调时钟和事件。Frida 原始消息保存在 `data.message`；二进制保存为内联 Base64，包含原长度、保留长度、原始 SHA-256 和截断标记。

默认最多 10000 条消息、每条 JSON 256 KiB、每条二进制保留 64 KiB。输出文件使用独占创建，不覆盖已有证据。`runner_complete` 记录收到/省略消息、脚本错误、缓冲区错误、probe_ready 数量、截断与清理失败。生产端未送达的事件数量仍是 unknown；没有事件不证明函数未执行。

采集退出码 0 表示窗口正常结束或目标自然退出，1 表示采集失败/受限/取消，2 表示输入、依赖或文件错误。完整性看 coverage 和计数，而不是只看退出码。

## 可复现的原生样例

```bash
PYTHONPATH=src python examples/native/verify_real.py
```

该脚本只编译仓库内的合成 C 文件，创建临时目录，不连接手机。用真实 Frida 验证 spawn 与 attach，比较函数参数、返回 42 和包含 NUL/非 UTF-8 的 4 字节缓冲区，并读取 C 程序独立输出对账；确认 owned spawn 已退出，attach 和脚本错误均不终止外部进程。

验证脚本要求 macOS/Linux、C 编译器及可用 Frida 权限，失败不会降级为假数据。成功报告在临时目录中；不要上传私人目标日志。本版本结果见 verification.md。
