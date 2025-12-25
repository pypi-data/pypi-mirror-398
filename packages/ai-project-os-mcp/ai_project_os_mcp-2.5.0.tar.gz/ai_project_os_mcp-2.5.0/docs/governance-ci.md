# Governance-Aware CI 模板

这是「系统替你盯 AI」的关键一步。

## 1. GitHub Actions（最小强制版）

```yaml
name: Governance Check

on: [push, pull_request]

jobs:
  governance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: false

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install
        run: |
          pip install -e .

      - name: Governance self-check
        run: |
          python - << 'EOF'
          from ai_project_os_mcp import GovernanceEngine
          print("✅ GovernanceEngine loaded")

          try:
              from ai_project_os_mcp.core.trigger_engine import TriggerEngine
              raise RuntimeError("Bypass possible")
          except ImportError:
              print("✅ Single Gate enforced")
          EOF
```

## 2. S5 强制治理（示例）

```yaml
- name: Block code outside S5
  run: |
    python - << 'EOF'
    from ai_project_os_mcp import GovernanceEngine
    ge = GovernanceEngine(".")
    ge.assert_stage("S5")
    EOF
```

## 3. 企业版可扩展方向（v3.0）

- PR 自动生成 GovernanceEvent
- CI 失败自动生成 Violation
- Violation → Jira / Linear
- Score 影响发布权限