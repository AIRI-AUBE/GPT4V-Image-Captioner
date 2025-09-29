# GPT4V-Image-Captioner 使用说明（简体中文）

一个基于 Gradio 的图像打标与数据集工具，支持多种视觉大模型服务：
- OpenAI GPT-4o（视觉）
- Google Vertex AI（基于 Vertex 的 Gemini）
- Google Gemini（google-generativeai SDK）
- 阿里巴巴通义千问 Qwen-VL（DashScope）
- 可选本地后端（Moondream、CogVLM、MiniCPM）

功能包含：单图打标、批量打标（同名 .txt 旁车文件）、可选图像预处理、水印检测、基于规则的图片分类、标签分析与清洗（词云、共现网络）、简单图片分割等。

## Windows 一键启动

- 直接双击 `start.ps1`（若策略限制脚本执行，可先在 PowerShell 执行下两行）：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\start.ps1
```

脚本将会：
- 创建虚拟环境 `.venv`
- 从 `requirements.txt` 安装最小依赖
- 启动 Gradio 界面（默认 http://127.0.0.1:8848 ）

需要安装全部可选功能（标签可视化、本地模型工具、各云厂商 SDK）可使用：

```powershell
.\start.ps1 -Full
```

可选参数：
- `-Port 8848` 指定端口
- `-Listen` 监听 0.0.0.0（允许局域网访问）
- `-Share` 启用 Gradio share 临时外网链接
- `-NoBrowser` 不自动打开浏览器

示例：
```powershell
.\start.ps1 -Full -Port 9000 -Listen -NoBrowser
```

## 工作流程（步骤）

1) 界面与设置
- UI 在 `gpt-caption.py` 中定义。
- 首次使用某个服务后，API 设置会保存到 `api_settings.json`。

2) 各服务与凭据填写位置
- OpenAI（GPT-4o）
  - API Key：你的 OpenAI Key
  - API URL：保持默认 `https://api.openai.com/v1/chat/completions`
  - Model：如 `gpt-4o` 或 `gpt-4o-mini`
- Anthropic Claude（可选）
  - API Key：你的 Claude Key
  - API URL：`https://api.anthropic.com/v1/messages`
  - Model：如 `claude-3.5-sonnet`
- Google Gemini（非 Vertex）
  - API Key：你的 Gemini API Key
  - API URL：包含 `gemini` 的任意字符串（自动识别）
  - Model：如 `gemini-1.5-pro`、`gemini-1.5-flash-latest`
- 阿里通义千问 Qwen-VL
  - API Key：你的 DashScope Key
  - API URL：`https://dashscope.aliyuncs.com/v1/services/aigc/multimodal-generation/generation`
  - Model：在下拉菜单选择（`qwen-vl-plus`、`qwen-vl-max` 等）
- Google Vertex AI（基于 Vertex 的 Gemini）
  - API Key 字段：填写本地服务账号 JSON 文件路径
  - API URL 字段：填写你的 Google Cloud Project ID（如 `my-project-123456`）
  - Model：默认 `gemini-2.0-flash-exp`（可在 UI 或代码中修改）
  - 也可在 UI 的“Vertex AI Configuration”折叠面板中保存配置
  - 提示：将仓库根目录的 `service_account.json.templete` 复制为 `service_account.json` 并填入真实值。真实凭据文件已被 git 忽略。`start.ps1` 会自动设置 `GOOGLE_APPLICATION_CREDENTIALS` 并尝试从该文件读取 `project_id`。

3) 运行时选择后端
- 使用“Choose API / 选择API”下拉框并点击“Switch / 切换”。
- 云端服务：直接向其 HTTP API 请求（无需额外本地服务）。
- 本地模型（Moondream / CogVLM / MiniCPM）：会启动内部 FastAPI（`openai_api.py`，`http://127.0.0.1:8000`），UI 请求会转到此服务。

4) 打标流程
- 单图：上传图片，点击“Caption Single Image”。
- 批量：填写目录路径。程序会在每张图片旁写入同名 `.txt`，并支持覆盖/前置/追加/跳过策略。
- Prompt 可包含 `{path\\to\\captions\\}`，会自动读取与图片同名的 .txt 并注入到提示词中。
- 质量选项会影响部分服务的图片缩放。

5) 其他工具
- Image Zip：预处理图片，加速标注。
- 水印检测：将疑似含水印图片移动/复制到目标文件夹。
- 图片筛选：基于规则将图片归类到不同文件夹。
- 图片分割：将图片按网格分割保存。
- 标签处理：统计、可视化、翻译与批量清洗（需要可选依赖）。

## 手动安装

若不使用 `start.ps1`：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
# 可选功能
pip install -r requirements-optional.txt

# 运行
python gpt-caption.py --port 8848
```

可选/本地模型说明：
- PyTorch 请根据你的 CUDA/CPU 环境在 https://pytorch.org/get-started/locally/ 选择合适版本安装；再安装 `requirements-optional.txt` 其余依赖。
- Hugging Face 模型体积较大（20–40GB+），请确保磁盘与显存充足（详见 UI 本地模型说明）。

## 部署建议

- 局域网访问：
  - 使用 `--listen` 绑定 `0.0.0.0`，并在防火墙放行端口。
  - 例如：`python gpt-caption.py --listen --port 8848 --no-browser`
- 快速外网演示：
  - 使用 `--share` 获取临时公网链接（不建议用于生产）。
- 长期稳定访问（推荐）：
  - 使用 Nginx/Caddy/IIS/Traefik 作为反向代理，转发到 `http://127.0.0.1:8848`；
  - 建议在代理层开启 HTTPS 与基础认证。

## 常见问题

- PowerShell 无法执行脚本
  - 执行：`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force`
- `google.genai` 或 `google.generativeai` 导入失败
  - 安装可选依赖：`pip install -r requirements-optional.txt` 或 `pip install google-genai google-generativeai`
- Qwen（DashScope）导入失败
  - 安装：`pip install dashscope`
- 标签可视化报错（matplotlib/networkx/wordcloud 等）
  - 安装可选依赖：`pip install -r requirements-optional.txt`
- Torch/CUDA 报错
  - 按照 pytorch.org 指南安装与你环境匹配的 PyTorch，然后再安装可选依赖。
- 大模型下载缓慢
  - 在 UI 的下载功能中选择 `CN` 加速，或确保网络稳定。

## 目录与入口
- `gpt-caption.py` – 主 Gradio 应用
- `lib/Api_Utils.py` – 各服务路由、重试与设置持久化
- `openai_api.py` – 本地后端的 FastAPI 包装
- `vertex_api.py` – Vertex AI 接入
- `lib/*` – 图像处理、提示词、标签处理与工具库

## 许可
本项目包含的第三方模型与库分别遵循其各自的许可证，请在商用前确认相应条款。
