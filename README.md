# 🎨 AstrBot Plugin ComfyUI Pro

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/lumingya/astrbot_plugin_comfyui_pro)
[![AstrBot](https://img.shields.io/badge/AstrBot-Plugin-orange.svg)](https://github.com/Soulter/AstrBot)

一个功能强大的 AstrBot 插件，旨在将你本地的 **ComfyUI** 无缝集成到聊天机器人中。支持 LLM 智能绘图、多工作流热切换、自定义系统提示词及敏感词过滤。

---

## 📑 目录

- [特色功能](#-特色功能)
- [快速开始](#-快速开始)
- [导入自定义工作流](#-导入自定义工作流)
- [配置说明](#️-配置说明)
- [指令与用法](#-指令与用法)
- [常见问题](#-常见问题)
- [更新日志](#-更新日志)

---

## ✨ 特色功能

### 🤖 LLM 智能绘图
- **自然语言生图**：用户只需说"帮我画一个..."，LLM 即自动分析、优化并生成高质量英文提示词
- **高度可定制**：可随时修改 System Prompt，定制你的"AI 绘画助手"人设和回复风格

### 🔌 ComfyUI 深度集成
- **便捷工作流导入**：完美支持 ComfyUI 的 API 格式工作流
- **多工作流热切换**：在 AstrBot 后台或通过管理员指令，随时切换不同的模型和风格
- **智能参数注入**：自动将提示词注入到指定节点，并智能寻找种子节点以实现随机化

### 🛡️ 完善的风控与权限
- **分级违禁词过滤**：内置 `Lite` 和 `Full` 两级敏感词库，支持中英文过滤
- **白名单与全局锁定**：可设置仅在白名单群组生效，或一键开启全局锁定
- **管理员特权**：可配置"无视冷却"、"无视白名单"、"无视敏感词"等超级权限

---

## 🚀 快速开始

### 1. 安装插件
在 AstrBot 插件市场搜索 `astrbot_plugin_comfyui_pro` 并安装。

### 2. 配置 ComfyUI 地址
进入插件设置，填写你的 ComfyUI 运行地址（默认为 `127.0.0.1:8188`）。

### 3. 开始使用
确保 ComfyUI 已启动，然后向机器人发送：
- 自然语言：`帮我画一只猫，赛博朋克风格`
- 指令方式：`/画图 a cute cat, cyberpunk style`

---

## 📂 导入自定义工作流

> 💡 本插件最大的特点就是让你几乎无缝地使用你在 ComfyUI 中已经搭建好的工作流。

### 步骤一：导出工作流
在 ComfyUI 工作流界面，点击菜单的 **`Save (API Format)`** 按钮，将工作流导出为 `.json` 文件。

### 步骤二：找到关键节点 ID
开启开发者模式后，ID 会显示在每个节点的标题上方。记下：
- **输入节点 ID**：接收提示词的 `CLIP Text Encode` 节点 **（必需）**
- **输出节点 ID**：最终生成图像的 `Save Image` 或 `Preview Image` 节点 **（必需）**

### 步骤三：放置并配置
1. 将导出的 `.json` 文件放入数据目录：
   ```
   data/plugin_data/astrbot_plugin_comfyui_pro/workflow/
   ```
2. **重载插件** → **刷新浏览器 (F5)** → **再次重载插件**
3. 进入插件设置：
   - 选择你刚刚放入的工作流文件
   - 填入对应的节点 ID
4. **完成！** 现在你的机器人就可以使用这个专属工作流进行绘画了。

---

## ⚙️ 配置说明

在 AstrBot 仪表盘 → 插件 → `astrbot_plugin_comfyui_pro` 中点击设置：

### ComfyUI 连接
| 配置项 | 说明 |
|--------|------|
| `Server Address` | ComfyUI 运行地址，默认 `127.0.0.1:8188` |

### 工作流设置
| 配置项 | 说明 |
|--------|------|
| `JSON File` | 选择 `workflow` 文件夹中的工作流文件 |
| `Input Node ID` | 接收正向提示词的节点 ID |
| `Output Node ID` | 输出图片的节点 ID |

### LLM 设置
| 配置项 | 说明 |
|--------|------|
| `System Prompt` | 编辑给 LLM 的系统提示词，定义它如何响应用户的画图请求 |

> ⚠️ **重要**：插件通过 XML 标签 `<提示词>xxx</提示词>` 来识别 LLM 的绘图意图。无论如何修改 System Prompt，**必须**确保 LLM 回复中包含此格式，否则无法触发绘图！

### 访问控制
| 配置项 | 说明 |
|--------|------|
| 管理员列表 | 设置管理员 QQ 号 |
| 白名单群组 | 允许使用插件的群号 |
| 冷却时间 | 防止用户刷屏 |
| 违禁词策略 | 为私聊和群聊设置敏感词拦截等级 (none/lite/full) |

---

## 📖 指令与用法

### 方式一：自然语言对话（推荐）
直接与机器人对话，让它帮你画。

**你**：帮我画一只猫，赛博朋克风格，在下雨的东京街头

![llm演示](https://raw.githubusercontent.com/lumingya/astrbot_plugin_comfyui_pro/main/assets/llm.png)

### 方式二：指令绘图
| 指令 | 说明 |
|------|------|
| `/画图 <提示词>` | 以合并转发的方式发送图片 |
| `/画图no <提示词>` | 直接发送图片，更简洁 |

![指令演示](https://raw.githubusercontent.com/lumingya/astrbot_plugin_comfyui_pro/main/assets/draw.png)

### 方式三：管理指令（仅管理员）
| 指令 | 说明 |
|------|------|
| `/comfy帮助` | 查看所有可用指令 |
| `/comfy_ls` | 列出所有可用的工作流 |
| `/comfy_use <序号> [input_id] [output_id]` | 切换工作流（无需重载） |
| `/comfy_add <节点ID> <步数>` | 覆盖特定节点的步数设置 |
| `/违禁级别 <none/lite/full>` | 调整当前群的敏感词拦截等级 |

---

## ❓ 常见问题

<details>
<summary><b>Q: 为什么 LLM 回复了提示词，但没有出图？</b></summary>

请检查：
1. ComfyUI 服务是否已在本地成功启动
2. 插件设置中的 `Input Node ID` 和 `Output Node ID` 是否填写正确
3. LLM 回复是否包含 `<提示词>xxx</提示词>` 格式
4. 后台日志中是否有报错信息
</details>

<details>
<summary><b>Q: 新添加的工作流文件看不到？</b></summary>

这是 AstrBot 的缓存机制导致。请执行：
1. **重载插件**
2. **刷新浏览器 (F5)**
3. **再次重载插件**
</details>

<details>
<summary><b>Q: 生成的图片总是一样的？</b></summary>

插件会自动寻找并修改名为 `seed` 或 `noise_seed` 的参数。如果你的工作流使用了非常规的自定义种子节点，请尝试在设置中手动指定 `Seed Node ID`。
</details>

<details>
<summary><b>Q: 工作流文件应该放在哪里？</b></summary>

从 v2.0 开始，工作流文件应放在数据目录：
```
data/plugin_data/astrbot_plugin_comfyui_pro/workflow/
```
**不是**插件目录 `data/plugins/astrbot_plugin_comfyui_pro/workflow/`
</details>

---

## � 目录结构

```
data/plugin_data/astrbot_plugin_comfyui_pro/   # ✅ 持久化目录（更新不丢失）
├── workflow/                                   # 你的工作流文件
│   └── *.json
├── output/                                     # 生成的图片历史
│   └── *.png
└── sensitive_words.json                        # 敏感词配置（可自定义）
```

---

## 📋 更新日志

### v2.2.0
- 优化提示词识别逻辑
- 修复若干已知问题

### v2.0.0
#### ✨ 新功能
- **步数覆盖功能**：按节点ID精确控制步数，解决 ComfyUI 前端修改参数影响插件生成的问题
- **数据持久化**：工作流、图片、敏感词等数据存储在独立目录，更新插件不会丢失
- **首次安装自动初始化**：自动复制默认工作流和敏感词文件

#### 🔧 优化
- 统一使用 `pathlib.Path` 处理路径，提高跨平台兼容性
- `/comfy_ls` 显示工作流覆盖配置数量，高亮当前使用的工作流
- `/comfy帮助` 显示更多状态信息
- 敏感词提示最多显示 5 个，避免消息过长

#### 📝 日志改进
| 场景 | 旧版 | 新版 |
|------|------|------|
| 群不在白名单 | `禁止输入。` | `🚫 本群(123456)不在白名单中` |
| 全局锁定 | `全局锁定。` | `🔒 全局锁定中，仅管理员可用` |
| 冷却中 | `请求太频繁...` | `⏱️ 冷却中，请在 30 秒后重试` |

### 从 v1.x 升级
1. 备份 `plugins/astrbot_plugin_comfyui_pro/workflow/` 下的工作流文件
2. 更新插件
3. 将备份的文件放入 `data/plugin_data/astrbot_plugin_comfyui_pro/workflow/`
4. 重载插件（两次重载 + 刷新浏览器）

> 💡 配置（管理员ID、白名单群等）由框架管理，**不会丢失**。

---

## 📄 许可证

MIT License

---

## 🔗 相关链接

- [AstrBot](https://github.com/Soulter/AstrBot) - 一站式多平台机器人框架
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的 Stable Diffusion 界面
