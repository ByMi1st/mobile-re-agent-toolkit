# 终端优先的静态分析流程

本工具包不重写 jadx、IDA 或 Frida。它把确定性的步骤包装成可复现的命令，保留本地产物，并要求每个结论标明证据等级。

## 1. 样本登记与基线

```bash
mrat fingerprint app.apk
mrat diff-binary old/libexample.so new/libexample.so
```

- 每次分析先登记样本的 SHA-256，所有结论绑定到这份样本。
- 升级样本后先做二进制 diff。哈希相同时直接复用旧产物，不要重跑。
- `diff-binary` 只报告结构变化（哈希、ELF 节区），不解释行为差异。

## 2. Java 层定位

```bash
mrat locate-dex app.apk --class com.example.Target
mrat locate-dex app.apk --text "some literal"
mrat scope-apk app.apk --dex classes3.dex --out scoped/classes3.apk
```

- 大 APK 一次建立全量索引容易耗尽内存。先用 `locate-dex` 找到定义和引用的 DEX，再用 `scope-apk` 生成只含这些 DEX 的分析用 APK。
- `scope-apk` 的输出不可安装，也不能证明其他 DEX 中没有引用。范围缩小本身需要写入结论。

## 3. 反编译与交叉引用

```bash
mrat decompile-class scoped/classes3.apk com.example.Target --out out/Target.java \
  --jadx /path/to/jadx
mrat xref-method scoped/classes3.apk com.example.Target run --jar /path/to/your-xref.jar \
  --out out/run-xrefs.txt
```

- `decompile-class` 调用 jadx CLI，使用 `--no-res` 和 `--show-bad-code`。输出是反编译结果，不是原始源码，`--show-bad-code` 保留的错误代码需要人工检查。
- `xref-method` 调用你自备的交叉引用 jar。本工具包不捆绑该 jar。结果是静态引用，不是运行时调用。
- 如果交叉引用因为 DEX 规模或加载错误失败，可以重试一次。仍失败时，改用 jadx 导出该 DEX 的全部类，再在导出结果中精确检索调用点，并在结论中注明"工具降级"。

## 4. Native 层

```bash
mrat ida-run libexample.i64 --script batch.py --log out/batch.log --idat /path/to/idat
```

- IDA 以无头模式运行 IDAPython 批处理脚本。脚本决定写哪些产物，`ida-run` 只记录日志和数据库前后的哈希。
- IDA 许可证与版本兼容性由使用者负责。

## 5. 证据等级

每条结论只能使用以下之一：

| 等级 | 含义 |
|---|---|
| `confirmed_static` | 由工具输出直接支持，并能回溯到具体文件、行或地址 |
| `candidate` | 有线索但未确认，需要其他证据（例如动态验证或第二种独立数据流） |
| `contradicted` | 已有证据与之冲突 |

以下情况只能记为 `candidate`：字符串相似、同一常量值碰撞、名称相近、时间上接近、结构上相邻。把候选当作已确认结构之前，需要证明它真实存在（例如指令位置、处理函数表、独立状态对象）。

静态结论不能描述为"实际执行"或"实际发送"。这类断言需要运行时证据。

## 6. 产物管理

- 每轮分析建立独立目录，例如 `output/<样本>/<主题>_<YYYYMMDD>/`，产物全部落盘。
- 脚本输出路径应当显式指定。工具包的命令默认拒绝覆盖已有文件。
- 设备上拉取的样本必须与本地样本做哈希比对，哈希一致才能视为同一样本。

## 7. 常见问题

| 问题 | 处理 |
|---|---|
| 全 APK 建索引耗尽内存 | 先 `locate-dex` 与 `scope-apk`，再做交叉引用 |
| 交叉引用中出现 StackOverflow | 重试一次，仍失败则降级为全类导出检索 |
| 把候选结构当作真实结构 | 按第 5 节要求补证据 |
| 同值碰撞写成"共用来源" | 只记为 `candidate` |
| 重跑已有基线 | 先 `diff-binary`，哈希相同则复用 |

## 8. 边界

本工具包只提供通用工具与合成测试样本。公司材料、业务样本、设备画像、凭据、目标专用的分析脚本和绕过方法不属于本仓库。外部工具（jadx、IDA、交叉引用 jar）由使用者自行安装、授权并负责其版本。
