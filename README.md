<div align="center">

<img src="frontend/public/favicon.svg" alt="装闭 Logo" width="120" />

# 装闭 - RenoPit

专为装修消费者打造的 AI 避坑引擎

<em>An AI-powered consumer advocate that reviews renovation plans & contracts, exposing overpriced pitfalls</em>

[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/666ghj/MiroFish)

> RenoPit <sub><sup>/ˈriːnoʊ pɪt/</sup></sub> 取自 **Reno**vation（装修）+ **Pit**fall（陷阱）

</div>

---

## 项目概述

**装闭（RenoPit）** 是一款面向装修消费者的 AI 审查引擎。你只需上传房屋设计图（户型图、效果图等）和装修相关文档（合同、报价单等），系统便会利用多模态 AI 进行批判性分析——找出设计图中的卫生死角、揭露报价单中的过度装修、指出合同中的隐形陷阱等，并生成一份在线报告和可下载的 PDF。

> 你只需：上传设计图纸和相关文档，用自然语言描述房屋情况</br>
> 系统将返回：一份详尽的批判性分析报告和相应的建议

> 装闭系统**不是中立的设计审查工具**，而是**消费者的辩护人**。任何增加成本却降低生活品质的设计，都会被标记为"智商税"。

### 我们的愿景

装修行业信息极度不对称——装修公司利用专业知识优势，通过复杂装饰、模糊报价、隐蔽增项等方式抬高成本。我们致力于用 AI 打破这种信息壁垒：

- **对消费者**：上传图纸即可获得专业批判意见，无需花钱或少花钱请第三方监理，轻松识破套路
- **对行业**：通过持续积累的坑位数据，推动装修服务透明化，让"良心装修"成为竞争力

从设计图审查到合同报价分析，我们让每一次装修决策都有据可依。

## 在线体验

欢迎访问在线 Demo 演示环境，体验我们为你准备的一次装修图纸审查与合同避坑分析：[https://renopit.fthux.com](https://renopit.fthux.com/)

## 系统截图

### 前端

| 主页 | 创建项目 & 上传素材 |
|------|------|
| <img src="screenshots/frontend/主页.png" alt="主页" width="400" /> | <img src="screenshots/frontend/创建项目.png" alt="创建项目" width="400" /> |
| 项目列表 | 删除项目 |
| <img src="screenshots/frontend/项目列表.png" alt="项目列表" width="400" /> | <img src="screenshots/frontend/项目列表-删除.png" alt="删除项目" width="400" /> |
| 复制项目 | 分析报告 — 总体评价 |
| <img src="screenshots/frontend/项目列表-复制.png" alt="复制项目" width="400" /> | <img src="screenshots/frontend/项目报告-总体评价.png" alt="总体评价" width="400" /> |
| 分析报告 — 问题详情 | 分析报告 — 合同 / 报价单审查 |
| <img src="screenshots/frontend/项目报告-问题详情.png" alt="问题详情" width="400" /> | <img src="screenshots/frontend/项目报告-合同:报价单分析.png" alt="合同报价单分析" width="400" /> |
| 分析报告 — 增项预测 | 分析报告 — 跨文档交叉核查 |
| <img src="screenshots/frontend/项目报告-增项预测.png" alt="增项预测" width="400" /> | <img src="screenshots/frontend/项目报告-跨文档交叉核查.png" alt="跨文档交叉核查" width="400" /> |

### 后端

| API 文档 — Swagger UI | API 文档 — ReDoc | 健康检查接口 |
|------|------|------|
| <img src="screenshots/backend/docs.png" alt="Swagger 文档" width="300" /> | <img src="screenshots/backend/redoc.png" alt="ReDoc 文档" width="300" /> | <img src="screenshots/backend/health.png" alt="健康检查" width="300" /> |

## 工作流程

1. **上传素材**：上传多张设计图（JPG/PNG/WEBP）+ 装修文档（合同/报价单 TXT/MD/DOCX/PDF）+ 文字补充说明
2. **AI 分析**：多模态大模型识别图纸 + 本地知识库匹配核心坑位 + 联网搜索最新套路，输出结构化批判报告
3. **在线报告**：分析完成后自动渲染可视化报告——展示每个问题的批判详情、套路揭露和替代方案
4. **下载 PDF**：点击按钮一键生成 PDF 报告，随时随地查看，也可以分享给装修公司"对峙"

## 快速开始

### Docker 部署

#### 前提要求

- 安装 **Docker** 和 **Docker Compose**（在 `Windows` 和 `macOS` 上使用`Docker Desktop`，通常情况下，`Docker Desktop` 安装包会自动包含 `Docker Compose`）
- 准备一个 `LLM API Key`（OpenAI 或兼容接口）

#### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

**必须的环境变量：**
```env
# LLM API配置（支持 OpenAI SDK 格式的任意 LLM API）
# 如果需要分析图片，请配置支持多模态的 LLM API
LLM_API_KEY=your_api_key
LLM_BASE_URL=llm_base_url
LLM_MODEL_NAME=llm_model_name
```

#### 2. 一键启动

```bash
docker-compose up -d
```

#### 3. 访问系统

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| 后端 API 文档 (Swagger) | http://localhost:8000/docs |
| 后端 API 文档 (ReDoc) | http://localhost:8000/redoc |
| 健康检查 | http://localhost:8000/health |

## 致谢

本项目灵感来源于装修过程中踩过的坑。感谢所有在装修中分享避坑经验的消费者，你们的每一次分享都在推动行业透明化。

---

<div align="center">

**让 AI 替你审查每一张图纸、每一份合同，装修不再任人宰割。**

</div>