# novel-ai

一个**多阶段、人物驱动、可回滚、带长期记忆**的 AI 小说创作系统骨架实现。

## 架构

- **Interface Layer**: `novel_ai/core/interfaces.py`
- **Orchestrator Layer**: `novel_ai/core/orchestrator.py`
- **Stage Layer**: `novel_ai/stages/pipeline.py`
- **Character Layer**: `novel_ai/core/models.py`（Global + Volume + Runtime）
- **Memory Layer**: `StoryBible`（只读，显式传递）
- **Consistency Layer**: `novel_ai/layers/consistency.py`
- **Infrastructure Layer**: `novel_ai/infra/llm.py` + `novel_ai/infra/storage.py`

## 创作流程（Stage0-Stage7）

已实现以下独立 Stage（统一 `run(context) -> result`）：

1. Stage0：题材建模
2. Stage1：世界构建
3. Stage2：总纲生成（创建 Global Characters）
4. Stage3：卷建模（只确定名单，不创建 VolumeCharacter）
5. Stage4：章节规划（创建 Volume Characters + 章节映射 + 情绪曲线 + 转折点 + 成长路径）
6. Stage5：章节创作
7. Stage6：一致性审查（由一致性引擎执行）
8. Stage7：润色优化

## 一致性与回滚

`Orchestrator` 使用显式状态机：

```python
while stage <= 7:
    result = run_stage(stage)
    report = consistency_check()
    if report.failed:
        rollback_to(report.rollback_stage)
    else:
        stage += 1
```

## 模型配置 / API 接入 / API Key 管理

### 1) 支持提供商

`novel_ai/infra/config.py` 已内置：

- OpenAI
- Claude (Anthropic)
- DeepSeek
- Local（OpenAI-compatible 本地服务）

### 2) 环境变量（推荐）

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="sk-..."
```

### 3) 初始化方式

```python
from novel_ai.infra.config import ApiKeyBundle, ApiKeyManager, Provider, default_model_config
from novel_ai.infra.llm import GenericLLMClient

bundle = ApiKeyBundle.from_env()
keys = ApiKeyManager(bundle)
model_cfg = default_model_config(Provider.OPENAI)

llm = GenericLLMClient(config=model_cfg, key_manager=keys)
```

### 4) API Key 管理策略

- 统一通过 `ApiKeyManager` 获取密钥，避免 Stage 直接访问密钥。
- 支持 `override_api_key`（单次任务覆盖），优先级高于环境变量。
- 密钥只在 `infra` 层使用，Stage 层与密钥无耦合。

### 5) 接口请求路径

- OpenAI / DeepSeek / 本地兼容：`POST /chat/completions`
- Claude：`POST /messages`

## 文件持久化规范

通过 `NovelRepository` 统一写入：

- `novels/{novel_id}/story_bible.json`
- `novels/{novel_id}/characters/global_characters.json`
- `novels/{novel_id}/volumes/{volume_id}/outline.json`
- `novels/{novel_id}/volumes/{volume_id}/characters/volume_characters.json`
- `novels/{novel_id}/volumes/{volume_id}/chapters/{chapter_id}.json`

> Stage 不直接写文件。


## 示例测试用例（回滚恢复）

新增测试 `tests/test_rollback_flow.py`，覆盖以下关键行为：

- Stage5 首次一致性检查失败。
- `ConsistencyReport` 指定回滚到 Stage4。
- Orchestrator 回滚后重新执行并最终完成到 Stage7。

运行：

```bash
pytest -q tests/test_rollback_flow.py
```

## 测试

```bash
python -m pytest -q
```
