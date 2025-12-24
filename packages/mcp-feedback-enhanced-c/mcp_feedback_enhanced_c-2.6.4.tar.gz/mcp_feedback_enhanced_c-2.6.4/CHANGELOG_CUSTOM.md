# Changelog - mcp-feedback-enhanced-c

此文档记录 `mcp-feedback-enhanced-c` 包的定制版本变更历史。

## [2.6.4] - 2025-12-21

### 修复
- **WebSocket 监听器跨会话问题**: 修复了在切换会话页面时 WebSocket 监听器可能失效的问题
  - 添加 `webSocketListenerSetup` 标志，防止重复设置监听器
  - 将原始消息处理方法保存在实例变量中，避免重复替换导致的递归问题
  - 确保每个会话页面都能正确接收 WebSocket 消息并自动刷新

### 新增
- **页面可见性变化监听**: 当用户切换回之前的会话页面时自动刷新
  - 监听 `visibilitychange` 事件
  - 页面从后台切换到前台时自动刷新活动会话列表（200ms 防抖）
  - 确保用户切换标签页时能看到最新的会话状态

### 改进
- **资源清理**: 完善 cleanup 方法，清理新增的 `visibilityDebounceTimer`
  - 防止内存泄漏
  - 提升代码健壮性

## [2.6.3] - 2025-12-21

### 新增
- **顶部活动会话切换选择器**: 在页面顶部导航栏添加精美的活动会话切换下拉菜单
  - 实时显示当前活动会话数量和状态
  - 点击下拉菜单可快速切换不同会话
  - 包含会话状态指示器（彩色圆点 + 脉冲动画）
  - 当前会话高亮显示
  - 响应式设计，移动端自动隐藏
  - 支持多语言（简体中文、繁体中文、英文）

### 改进
- **会话管理自动刷新**: 优化会话管理页面的用户体验
  - 页面加载时自动获取活跃会话列表（无需手动点击"重新整理"）
  - WebSocket 动态监听会话变化，实时自动刷新
  - 智能防抖机制，避免频繁刷新（300ms 延迟）
  - 自动判断需要刷新的会话状态变化（创建、更新、完成、超时、过期、错误）

### 技术优化
- **前端性能优化**: 添加渲染防抖机制，减少不必要的 DOM 操作
- **代码结构改进**: 模块化设计，提升可维护性
- **国际化完善**: 添加活动会话相关翻译字符串

## [2.6.2] - 2025-12-21

### 修复
- **可执行文件名问题**: 修复了包名与可执行文件名不匹配的问题
  - 之前：包名为 `mcp-feedback-enhanced-c`，但可执行文件为 `mcp-feedback-enhanced` 和 `interactive-feedback-mcp`
  - 现在：简化为单一可执行文件 `mcp-feedback-enhanced-c`，与包名保持一致
  - 用户现在可以直接使用：`uvx mcp-feedback-enhanced-c` 而无需指定 `--from`

### 使用方式
```bash
# 安装
pip install mcp-feedback-enhanced-c

# 直接运行
uvx mcp-feedback-enhanced-c@latest version
uvx mcp-feedback-enhanced-c@latest test --web
uvx mcp-feedback-enhanced-c@latest test --desktop
```

## [2.6.1] - 2025-12-21

### 新增
- **定制版本首次发布**: Fork from [Minidoracat/mcp-feedback-enhanced](https://github.com/Minidoracat/mcp-feedback-enhanced)
- **包名更改**: 从 `mcp-feedback-enhanced` 改为 `mcp-feedback-enhanced-c`
- **作者信息更新**: 添加 Dwsy 作为共同作者
- **仓库链接更新**: 指向新的 GitHub 仓库 [Dwsy/mcp-feedback-enhanced](https://github.com/Dwsy/mcp-feedback-enhanced)
- **README 增强**: 在所有语言版本的 README 中添加原始项目和增强版本的链接

### 致谢
- **原始作者**: [Fábio Ferreira](https://x.com/fabiomlferreira) - [Original Project](https://github.com/noopstudios/interactive-feedback-mcp)
- **增强版本**: [Minidoracat](https://github.com/Minidoracat) - [Enhanced Project](https://github.com/Minidoracat/mcp-feedback-enhanced)
- **UI 设计参考**: [sanshao85/mcp-feedback-collector](https://github.com/sanshao85/mcp-feedback-collector)

---

**注意**: 此定制版本基于 v2.6.0 版本开发，保持与上游版本的功能兼容性。完整的功能变更历史请参考上游项目的 [CHANGELOG](RELEASE_NOTES/CHANGELOG.en.md)。
