# AI Project OS · MCP v0.1 工程规范

## Engineering-Grade Model Context Protocol

### 定位一句话版：
这是一个把「AI 自动编程」约束进「真实软件工程流程」的 MCP 实现规范。

---

## 1️⃣ MCP 的设计目标（非口号）

### 本 MCP 解决什么问题
- ❌ AI 跳阶段直接写代码
- ❌ AI 擅自改架构、打补丁、脏改
- ❌ 无法审计 AI 为什么这样写
- ❌ 人不懂代码，无法判断 AI 是否「越权」

### 本 MCP 强制实现什么
- ✅ AI 只能在当前冻结阶段行动
- ✅ 所有工程决策 必须显式冻结
- ✅ 所有代码变更 必须可审计、可追责
- ✅ 不懂代码的人 也能主导完整项目

---

## 2️⃣ MCP 的核心哲学（这是灵魂）

### ❗ 三个不可动摇的原则
- **State > Prompt**
  - 项目真实状态来自 state.json
  - Prompt 只是解释，不是事实

- **Freeze > Generate**
  - 冻结是决策
  - 生成只是执行

- **Audit > Output**
  - 没有审计 = 没有交付
  - 输出本身不构成完成

---

## 3️⃣ MCP 的系统边界（非常重要）

### MCP 能做的
- 查询当前阶段
- 执行冻结
- 生成被冻结任务
- 写代码（仅 S5）
- 提交审计证据

### MCP 绝对不能做的
- ❌ 跳过冻结
- ❌ 修改 S3 架构
- ❌ 绕过 Guard 写代码
- ❌ 隐式变更、不留痕迹

**一切违规 → MCP 必须拒绝执行**

---

## 4️⃣ MCP 统一状态模型（Single Source of Truth）

### state.json （强制）
```json
{
  "stage": "S1 | S2 | S3 | S4 | S5",
  "frozen": true,
  "locked": false,
  "last_updated": "ISO-8601",
  "version": "v0.1"
}
```

### MCP 规则
- MCP 只能读取 / 通过工具写入
- AI 不得假设状态
- 所有 Tool 执行前必须读取 state

---

## 5️⃣ MCP 生命周期 = 5S 生命周期

| MCP Phase | 工程含义 | AI 权限 |
|-----------|----------|---------|
| S1 | Scope 定义 | ❌ 禁止代码 |
| S2 | Spec 固化 | ❌ 禁止代码 |
| S3 | 架构冻结 | ❌ 禁止代码 |
| S4 | 任务分解 | ❌ 禁止代码 |
| S5 | 实现 + 审计 | ✅ 受控代码 |

---

## 6️⃣ MCP Tool 规范（这是执行层）

### 必选 Tool（v0.1）
1. **get_stage**
   - 功能：读取当前阶段
   - 所有行为前必须调用

2. **freeze_stage**
   - 功能：冻结到下一个阶段
   - 必须人工确认
   - 禁止跳级

3. **guard_src**
   - 功能：校验是否允许写 src/
   - 失败 → MCP 立刻拒绝生成

4. **submit_audit**
   - 功能：提交 S5 审计记录
   - 未通过 → 不允许完成任务

---

## 7️⃣ MCP 强制行为铁律（System Contract）

这是 MCP Server 的 系统级约束，不是 Prompt 建议

```
You are an AI Project OS MCP Agent.

You MUST:
- Always query get_stage before acting
- Refuse code generation unless stage == S5
- Require Context Refresh for any src change
- Abort immediately on architecture violation
- Require audit submission for every S5 task

Violation = hard refusal.
```

---

## 8️⃣ S5 专属子协议（你这套的杀手锏）

### 🔒 Context Refresh（强制）
```
[Context Refresh]
Sub-task ID:
Layer:
Forbidden Constraints:
```

**缺失 → MCP 拒绝执行**

### 🔥 Change Fuse（熔断）

**触发条件：**
需求无法在 S3 架构内实现

**MCP 行为：**
- ❌ 禁止 workaround
- ❌ 禁止 Dirty Hack
- ✅ 返回： ARCHITECTURE BREAK – REQUIRE S3 REFREEZE

### 🧪 Pseudo-TDD（认知对齐）

代码前必须声明「什么是对的」
可为注释，但不可省略

---

## 9️⃣ 人类在 MCP 中的角色（你非常关键）

| 行为 | AI | 人 |
|------|----|----|
| 定义目标 | ❌ | ✅ |
| 冻结阶段 | ❌ | ✅ |
| 写代码 | ✅ | ❌ |
| 判断是否继续 | ❌ | ✅ |

👉 人永远是「裁决者」，AI 永远是「执行者」

---

## 🔟 MCP v0.1 的完成判定

一个 MCP 实现 只要满足以下 5 条，就合规 ：
1. 有真实状态源（非 Prompt）
2. 有冻结点（不可跳）
3. 有 Guard（物理拦截）
4. 有 Audit（可追责）
5. AI 无法绕过以上四点

---

## 最后一句（很重要）

这不是「AI 编程工具」，
这是「AI 工程执行操作系统」。