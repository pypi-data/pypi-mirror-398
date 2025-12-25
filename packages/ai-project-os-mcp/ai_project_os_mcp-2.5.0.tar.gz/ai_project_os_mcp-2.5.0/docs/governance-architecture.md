# v2.5 治理接口总览

## Architecture / Event / Policy / Action

这是给工程师 / 架构师 / MCP 平台看的技术文档。

### 1. 总体治理流（不可变）

```
AI Tool Call
    ↓
GovernanceEvent (with Actor)
    ↓
GovernanceEngine (Single Gate)
    ↓
TriggerEngine → Violations
    ↓
PolicyEngine → Actions
    ↓
State / Audit / Score
```

### 2. Event 模型（强制）

```python
class GovernanceEvent:
    event_type: EventType
    actor: Actor                # REQUIRED
    payload: dict
    timestamp: datetime
```

> **没有 actor → 行为非法**

### 3. Violation 是一等公民（First-Class Object）

```python
class GovernanceViolation:
    id
    level: CRITICAL | MAJOR | MINOR
    rule_id
    event_id
    actor_id
    timestamp
    resolved
```

> **Violation 不是日志**
> **Violation 是 治理事实**

### 4. Policy = 决策权，不是配置

```yaml
policies:
  - id: code_outside_s5
    match:
      event_type: CODE_GENERATION
      condition: stage != "S5"
    actions:
      - FREEZE_PROJECT
      - LOG_VIOLATION
```

- `system.policy.yaml`：不可修改
- `project.policy.yaml`：可配置
- **系统策略永远优先**

### 5. Action 是唯一能改变系统状态的东西

| Action | 影响 |
|--------|------|
| FREEZE_PROJECT | 写入 state.json |
| SCORE_PENALTY | 不可逆扣分 |
| REQUIRE_HUMAN_APPROVAL | 阻断执行 |
| LOG_AUDIT | 生成审计 |

> **没有 Action，系统状态不会改变**

### 6. MCP Tool 的地位（刻意降级）

MCP Tool 不允许：

- 判断对错
- 修改状态
- 决定后果

MCP Tool 只允许：

- 解析输入
- 构造 GovernanceEvent
- 调用 GovernanceEngine