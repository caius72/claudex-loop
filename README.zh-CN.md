# Claudex Loop

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

在 Claude Code 与 Codex 之间选择模型、交接任务、审查计划并验证实现。这份中文指南基于 [@tura-ai-agent 的翻译贡献](https://github.com/chaseai-yt/claudex-loop/pull/6)，已更新为当前工作流的简明说明。完整参数与实现细节见英文 README 及各技能的参考文档。

本分支将社区 PR 的有效改动整合进当前共享运行器。逐项处理记录见 [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)。

## 技能

| 技能 | 用途 | 依赖 |
|---|---|---|
| [`claudex-route`](skills/claudex-route/SKILL.md) | 推荐模型，或执行一次范围明确的任务交接 | 独立使用；仅在委派时需要所选 CLI |
| [`claudex-loop`](skills/claudex-loop/SKILL.md) | 需求、计划审查、实现和最终检查 | 两个 CLI，以及 Python 3.10+ |
| [`codex-review`](skills/codex-review/SKILL.md) | 明确指定 Codex 审查计划的兼容命令 | 共享的 `claudex-loop` 技能 |
| [`codex-build`](skills/codex-build/SKILL.md) | 明确指定 Codex 实现计划的兼容命令 | 共享的 `claudex-loop` 技能 |

`claudex-route` 与完整循环相互独立。它可以建议保留当前模型、获取第二意见、调查阻碍或委派一个任务。仅请求推荐并不会启动其他模型，也不授权编辑文件；一次交接不使用完整循环的审批绑定运行器。

## 双向工作流

| 起点 | 需求与计划 | 计划审查 | 默认实现者 | 最终检查 |
|---|---|---|---|---|
| Claude Code | 当前 Claude 会话 | Codex | Claude | 新的 Codex 会话 |
| Codex | 当前 Codex 会话 | Claude | Codex | 新的 Claude 会话 |

通过 `builder=claude` 或 `builder=codex` 选择实现者。检查者始终来自另一个提供商。协调者接手修改后，新改动需要重新接受独立检查；两方都写过代码时，应记录各自的贡献和审查范围。

模型可以配置。明确选择且账户可用时，可以使用 Claude Fable 5.1 或 GPT-6 Astra。Codex 的计划审查和最终检查忽略用户配置；若要使用特定模型和推理强度，必须明确指定，否则使用 CLI 内置默认值。实现及 Claude 调用保留正常配置。宿主界面选择的模型不会自动改变另一个 CLI。运行记录区分请求的模型和实际观测到的模型，不会在失败后悄悄换模型或提供商。

1. **调研：**查看代码、调用者、共享状态的写入者及相关文档，列出假设和来源。
2. **明确需求：**解决会影响结果的关键问题，将方案、验收标准和验证命令写入计划。
3. **独立审查：**另一个提供商检查计划及相关代码，给出有证据的发现。协调者判断哪些意见成立，修改计划，并在同一审查会话中复查，直到明确结论或轮次上限。
4. **实现与检查：**已有实现授权后执行计划。协调者亲自运行验证，再由另一个提供商在新会话中检查最终代码。

审查结论为 `APPROVED`、`REVISE` 或 `BLOCKED`。空输出、进程失败或格式错误不能算作批准。没有发现问题是有效结果，但不代表审查已经穷尽所有缺陷。对于共享资源，需要检查已发现的写入者并列出未打开的文件；代码注释声称的保证也必须与实现一致。

`PLAN.md` 记录要做什么；`PLAN-REVIEW-LOG.md` 记录发现、处置、模型、验证及剩余不确定性。两者路径均可配置。诊断文件放在目标检出目录之外的独立私有目录中。

用户控制授权。只要求审查不等于允许实现；已要求规划并实现时，无需再次索取相同授权。提交、推送和发布遵循已有用户指令。

## 安装

完整循环要求两个 CLI 已安装并通过身份验证，另需 Python **3.10+**。共享运行器只使用标准库，无需运行时 pip 依赖或额外 API 密钥。可检查 `codex --version`、`codex login status`、`claude --version` 和 `claude auth status`。参见 [运行时参考](skills/claudex-loop/references/runtime.md)。

Claude Code 插件安装本分支：

```text
/plugin marketplace add caius72/claudex-loop
/plugin install claudex-loop@claudex-loop
```

使用 `/claudex-loop:claudex-route` 或 `/claudex-loop:claudex-loop`；兼容命令也在同一命名空间下。

手动安装：克隆本仓库，然后从仓库目录复制所有技能。兼容命令不能只复制自身目录，因为它们依赖共享运行器。`claudex-route` 可以单独安装。

```bash
# macOS / Linux
mkdir -p ~/.agents/skills ~/.claude/skills
cp -R skills/. ~/.agents/skills/
cp -R skills/. ~/.claude/skills/
```

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills", "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse -Force skills\* "$env:USERPROFILE\.agents\skills\"
Copy-Item -Recurse -Force skills\* "$env:USERPROFILE\.claude\skills\"
```

开启新会话后，在 Codex 中使用 `$claudex-route` / `$claudex-loop`，在 Claude Code 中使用 `/claudex-route` / `/claudex-loop`。手动更新需要 `git pull` 后重新复制目录。仓库也提供 `.codex-plugin/plugin.json` 用于 Codex 插件打包。

```text
claudex this feature — plan and implement it
claudex this plan, mode=review, plan=docs/migration.md, rounds=3
claudex this feature, builder=codex, reviewer_model=gpt-6-astra
claudex this feature, builder=claude, reviewer_model=claude-fable-5-1
```

后两个示例分别从 Claude Code 和 Codex 开始。`codex_cli` / `claude_cli` 可指定经验证的可执行文件绝对路径，由运行器接收为 `--cli`。不会自动修改全局 PATH 或安装配置。空版本输出加 SIGKILL（`-9` / `137`）应先调查实际可执行文件，不应盲目重试或删除 `~/.codex/`。

## 参数

| 参数 | 默认值 | 含义 |
|---|---|---|
| `mode` | `full` | `review` 从已有计划开始 |
| `plan` / `PLAN_FILE` | `PLAN.md` | 所有阶段使用的计划路径 |
| `log` / `LOG_FILE` | `PLAN-REVIEW-LOG.md` | 只追加的决策记录 |
| `builder` | 当前宿主 | `claude` 或 `codex` |
| `reviewer_model` / `builder_model` / `inspector_model` | CLI 默认值，见上方模型说明 | 为各角色指定模型 |
| `reviewer_effort` / `builder_effort` / `inspector_effort` | CLI 默认值，见上方模型说明 | 指定支持的推理强度 |
| `rounds` / `MAX_ROUNDS` | `5` | 完成的计划审查轮次上限 |
| `MAX_FIX_ROUNDS` | `2` | 实现修复轮次上限 |
| `MAX_INSPECTION_ROUNDS` | `2` | 首次检查加一次复查 |
| `research` | 与任务相称 | `none`、`web` 或明确授权的 `deep` |
| `inspect` | `on` | `off` 必须明确选择并记录 |
| `PROOF_CMD` | 来自计划或仓库 | 验证交付物的命令 |

## 批准、边界与服务中断

批准绑定计划的绝对路径与 SHA256；修改计划会使批准失效。最终检查还绑定实现前的提交及完整变更指纹，包括暂存和未跟踪文件。检查期间或之后有新改动时，需要重新检查。暂存变更与工作树内容不一致时，检查会拒绝启动；应暂存预期版本或取消这些变更的暂存，不要为通过检查而暂存无关工作。普通未暂存编辑仍受支持。检查后再暂存也会改变指纹，需要重新检查。

Codex 的审查使用只读 shell 沙箱，并忽略用户 `config.toml`、禁用网页搜索；用户配置中的 MCP 工具不会传给审查者。非 Git 目录的计划审查仍受支持。Claude 审查仅开放文件读取和搜索工具，并禁用自定义项及 MCP。两者边界不同，详见运行时参考。委派实现使用受限权限，并要求干净的 Git 基线；工作树用于隔离差异，本身不是安全沙箱。

服务中断时，按 [备用审查协议](skills/claudex-loop/references/fallback.md) 保留已完成轮次，再由用户选择等待、切换或跳过。可选的标准库 API 适配器支持明确选择的环境配置和认证／付款失败链。它只接收计划及可选历史，没有仓库或工具访问权限；只有明确接受 `--allow-limited-review` 后，其批准才能用于实现，且不能替代最终代码检查。远程 API 可能单独计费；调用前必须授权要发送的内容和端点。429 本身不能证明额度耗尽。

本地 `codex_usage.py` 可读取缓存的额度与重置时间，不调用模型。过期、不完整或缺失的信息标为未知；缓存不能证明当前可用性。

## 开发与验证

```text
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python -m unittest discover -s tests -v
```

CI 配置覆盖 Windows、macOS 和 Linux。测试使用临时 Git 仓库、模拟 CLI 和本机 HTTP 服务，需要本地套接字权限，不消耗模型额度。测试涵盖角色路由、会话恢复、无效输出、批准失效、变更清单、备用响应和重定向拒绝。历史实测及其局限见 [VALIDATION.md](VALIDATION.md)；自动化测试不证明所有在线模型或端点都兼容，也不证明审查质量。

## 历史与致谢

仓库曾名为 `grill-me-codex` 和 `crucible`；旧技能保留在 [legacy/](legacy/)。

- 原始访谈技能：© [Matt Pocock](https://github.com/mattpocock/skills)，MIT；参见第三方声明。
- Codex 实现模式借鉴 [Peter Steinberger](https://github.com/steipete/agent-scripts)。
- Claudex Loop、跨模型审查和打包来自 [Chase AI](https://youtube.com/@chaseai)。
- 翻译原始贡献来自 [@tura-ai-agent](https://github.com/tura-ai-agent)；社区修复的具体贡献见 [致谢与整合记录](ACKNOWLEDGMENTS.md)。

[Claude Code Masterclass / Chase AI+](https://www.skool.com/chase-ai/about) · [MIT 许可证](LICENSE)
