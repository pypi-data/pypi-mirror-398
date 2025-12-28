### 百炼自定义 MCP 服务配置

- 编写 MCP 服务脚本：src/linzt_cfrna_test_1/server.py；
- 使用 `uv build` 打包项目，并用 `uv publish` 发布到 PYPI 仓库；
- 打开百炼页面：https://bailian.console.aliyun.com/?tab=app#/mcp-manage/custom；
- 创建 MCP 服务；
- 使用脚本部署 ---> 部署服务；
- 安装方法：`uvx`；
- 地域：`深圳`；
- 填写 MCP 配置，其中 `linzt-cfrna-test-1` 为 `pyproject.toml` 文件中标注的项目名称：

```{json}
{
  "mcpServers": {
    "linzt-cfrna-test-1": {
      "command": "uvx",
      "args": [
        "linzt-cfrna-test-1"
      ]
    }
  }
}
```
