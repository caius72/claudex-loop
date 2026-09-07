# Claudex Loop

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

Claude Code と Codex の間でモデルを選び、タスクを引き継ぎ、計画と実装を検証するスキル集です。この日本語ガイドは [@tura-ai-agent の翻訳提案](https://github.com/chaseai-yt/claudex-loop/pull/6) を基に、現在のワークフローの概要として更新しました。全パラメーターと実装の詳細は英語 README および各スキルの参照文書をご覧ください。

このフォークでは、コミュニティ PR の有効な変更を現在の共有ランナーへ統合しています。個別の扱いは [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) に記録しています。

## スキル

| スキル | 用途 | 依存関係 |
|---|---|---|
| [`claudex-route`](skills/claudex-route/SKILL.md) | モデルの推薦、または範囲を限定した一度の引き継ぎ | 単独利用可能。委任時のみ選択した CLI が必要 |
| [`claudex-loop`](skills/claudex-loop/SKILL.md) | 要件、計画レビュー、実装、最終検査 | 両方の CLI と Python 3.10+ |
| [`codex-review`](skills/codex-review/SKILL.md) | Codex による計画レビューを明示する互換コマンド | 共有の `claudex-loop` スキル |
| [`codex-build`](skills/codex-build/SKILL.md) | Codex による実装を明示する互換コマンド | 共有の `claudex-loop` スキル |

`claudex-route` は完全なループから独立しています。現在のモデルを使い続ける、別の意見を得る、障害を調べる、限定したタスクを委任する、といった選択を提案します。推薦を求めるだけでは他のモデルを起動せず、ファイル編集も許可しません。一度の引き継ぎでは、完全なループの承認を結び付けるランナーは使用しません。

## 双方向のワークフロー

| 開始場所 | 要件と計画 | 計画レビュー | 既定の実装担当 | 最終検査 |
|---|---|---|---|---|
| Claude Code | 現在の Claude セッション | Codex | Claude | 新しい Codex セッション |
| Codex | 現在の Codex セッション | Claude | Codex | 新しい Claude セッション |

`builder=claude` または `builder=codex` で実装担当を選べます。検査担当は実装担当と異なるプロバイダーです。調整役が修正を引き継いだ場合、その変更にも新たな独立検査が必要です。両者が実装した場合は、誰がどの部分を作成し、検査したかを記録します。

モデルは設定可能です。明示的に選択し、アカウントで利用できる場合は Claude Fable 5.1 や GPT-6 Astra を使えます。各 CLI の設定を維持することもできます。ホスト画面で選んだモデルが別の CLI に自動適用されるわけではありません。要求したモデルと観測できたモデルは別々に記録し、失敗時に黙って切り替えません。

1. **調査：**関連コード、呼び出し元、共有状態への書き込み元、文書を調べ、前提と出典を整理します。
2. **要件の確定：**結果を左右する判断を解決し、計画、受け入れ条件、検証コマンドを記述します。
3. **独立レビュー：**別のプロバイダーが計画と関連コードを読み、証拠付きの指摘を返します。調整役が指摘を判断し、必要な修正後に同じレビューセッションで再確認します。明示的な結論または回数上限で終了します。
4. **実装と検査：**実装が許可されていれば計画を実行します。調整役が検証を実行し、別のプロバイダーが新しいセッションで最終コードを検査します。

判定は `APPROVED`、`REVISE`、`BLOCKED` です。空の出力、プロセスの失敗、不正な形式は承認になりません。指摘がゼロでも有効ですが、欠陥をすべて調べ尽くした証拠にはなりません。共有リソースの書き込み元を確認し、未確認のファイルを明記します。コメントが保証を主張している場合は、実装が本当にその保証を提供するか確認します。

`PLAN.md` は実装内容、`PLAN-REVIEW-LOG.md` は指摘、対応、モデル、検証、残る不確実性を記録します。両方のパスを変更できます。診断ファイルは対象チェックアウトの外にある、実行ごとの私有ディレクトリへ保存します。

許可はユーザーが決めます。レビューの依頼だけでは実装を許可しません。計画と実装の両方が既に依頼されている場合、同じ許可を繰り返し求める必要はありません。コミット、プッシュ、公開は既存のユーザー指示に従います。

## インストール

完全なループでは、両方の CLI のインストールと認証、および Python **3.10+** が必要です。共有ランナーは標準ライブラリのみを使い、実行時の pip 依存関係や追加 API キーは不要です。`codex --version`、`codex login status`、`claude --version`、`claude auth status` で確認できます。[実行環境の参照文書](skills/claudex-loop/references/runtime.md)もご覧ください。

このフォークを Claude Code プラグインとしてインストールする場合：

```text
/plugin marketplace add caius72/claudex-loop
/plugin install claudex-loop@claudex-loop
```

`/claudex-loop:claudex-route` または `/claudex-loop:claudex-loop` を使用します。互換コマンドも同じ名前空間にあります。

手動インストールでは、このリポジトリをクローンし、そのディレクトリから全スキルをコピーします。互換コマンドは共有ランナーに依存するため、単独コピーでは動きません。`claudex-route` は単独でインストールできます。

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

新しいセッションを開き、Codex では `$claudex-route` / `$claudex-loop`、Claude Code では `/claudex-route` / `/claudex-loop` を呼び出します。手動更新は `git pull` 後に再コピーします。Codex のプラグイン用に `.codex-plugin/plugin.json` も提供しています。

```text
claudex this feature — plan and implement it
claudex this plan, mode=review, plan=docs/migration.md, rounds=3
claudex this feature, builder=codex, reviewer_model=gpt-6-astra
claudex this feature, builder=claude, reviewer_model=claude-fable-5-1
```

最後の2例はそれぞれ Claude Code、Codex から開始します。`codex_cli` / `claude_cli` で検証済みの実行ファイルの絶対パスを指定でき、ランナーの `--cli` に渡されます。グローバル PATH やインストールを自動変更しません。バージョン出力が空で SIGKILL（`-9` / `137`）になった場合は、再試行より先に実行ファイルを調べ、`~/.codex/` は削除しないでください。

## 設定項目

| 引数 | 既定値 | 意味 |
|---|---|---|
| `mode` | `full` | `review` は既存計画から開始 |
| `plan` / `PLAN_FILE` | `PLAN.md` | 全段階で使用する計画パス |
| `log` / `LOG_FILE` | `PLAN-REVIEW-LOG.md` | 追記式の判断記録 |
| `builder` | 現在のホスト | `claude` または `codex` |
| `reviewer_model` / `builder_model` / `inspector_model` | 各 CLI 設定 | 役割別モデル指定 |
| `reviewer_effort` / `builder_effort` / `inspector_effort` | 各 CLI 設定 | 対応する推論強度の指定 |
| `rounds` / `MAX_ROUNDS` | `5` | 完了した計画レビューの上限 |
| `MAX_FIX_ROUNDS` | `2` | 実装修正の上限 |
| `MAX_INSPECTION_ROUNDS` | `2` | 初回検査と1回の再検査 |
| `research` | タスクに応じる | `none`、`web`、明示許可された `deep` |
| `inspect` | `on` | `off` は明示的に選び記録 |
| `PROOF_CMD` | 計画またはリポジトリから取得 | 成果物を検証するコマンド |

## 承認、境界、サービス障害

承認は計画の絶対パスと SHA256 に結び付き、計画を変更すると無効になります。最終検査には実装前のコミットと、ステージ済み・未追跡ファイルを含む変更全体の指紋も記録します。検査中または検査後に変更があれば、再検査が必要です。

Codex のレビューは読み取り専用 shell サンドボックスを使い、Git リポジトリでないディレクトリの計画もレビューできます。ただし、既存 MCP 設定による外部書き込み能力は別途確認が必要です。Claude のレビューはファイルの読み取りと検索のみを許可し、カスタマイズと MCP を無効にします。両者の境界は異なります。委任実装は限定した権限とクリーンな Git 基準状態を使用します。worktree は差分を隔離する仕組みであり、それ自体がセキュリティサンドボックスではありません。

レビュー担当が利用できない場合は、[フォールバック手順](skills/claudex-loop/references/fallback.md) に従い、完了済みのラウンドを保存し、ユーザーが待機・切り替え・スキップを選びます。任意の標準ライブラリ API アダプターは、環境変数で設定したプロファイルと明示的な認証／支払い失敗時の切り替え順序をサポートします。受け取るのは計画と任意の履歴だけで、リポジトリやツールへアクセスできません。その限定的な承認を実装に使うには `--allow-limited-review` の明示的な受け入れが必要で、最終コード検査の代わりにはなりません。外部 API は別料金の可能性があるため、送信内容と接続先を事前に許可する必要があります。429 だけではクォータ枯渇と断定できません。

ローカルの `codex_usage.py` はモデルを呼び出さず、キャッシュされた利用枠とリセット時刻を読みます。古い、不完全、または存在しないデータは不明として扱い、現在の利用可能性を保証しません。

## 開発と検証

```text
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python -m unittest discover -s tests -v
```

CI は Windows、macOS、Linux 向けに設定されています。テストは一時 Git リポジトリ、模擬 CLI、ローカル HTTP サーバーを使用し、ローカルソケット権限が必要ですがモデル利用枠は消費しません。役割選択、セッション再開、不正出力、承認失効、変更一覧、フォールバック応答、リダイレクト拒否を検証します。過去の実測と限界は [VALIDATION.md](VALIDATION.md) に記載しています。自動テストは全オンラインモデルとの互換性やレビュー品質を保証しません。

## 履歴とクレジット

旧名称は `grill-me-codex` と `crucible` です。以前のスキルは [legacy/](legacy/) に保存されています。

- 元のインタビュースキル：© [Matt Pocock](https://github.com/mattpocock/skills)、MIT。第三者ライセンス表記を参照してください。
- Codex による実装パターンは [Peter Steinberger](https://github.com/steipete/agent-scripts) を参考にしています。
- Claudex Loop、モデル間レビュー、パッケージングは [Chase AI](https://youtube.com/@chaseai) によるものです。
- 翻訳の元の貢献は [@tura-ai-agent](https://github.com/tura-ai-agent)。コミュニティ修正の帰属は [統合記録](ACKNOWLEDGMENTS.md) にあります。

[Claude Code Masterclass / Chase AI+](https://www.skool.com/chase-ai/about) · [MIT ライセンス](LICENSE)
