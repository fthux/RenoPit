<div align="center">

<img src="frontend/public/favicon.svg" alt="装闭 Logo" width="120" />

# 🏠 装闭
### RenoPit <sub><sup>/ˈriːnoʊ pɪt/</sup></sub>

取自 **Reno**vation（装修）+ **Pit**fall（陷阱），专为装修消费者打造的 AI 避坑引擎

一个**完全站在消费者立场**的 AI 审查工具，上传装修设计图和合同文档，自动识别不合理设计、过度装修和卫生死角等"装修智商税"

<em>An AI-powered consumer advocate that reviews renovation plans & contracts, exposing overpriced pitfalls</em>

[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/666ghj/MiroFish)

</div>

---

## ⚡ 项目概述

**装闭（RenoPit）** 是一款面向装修消费者的 AI 审查引擎。你只需上传房屋设计图（户型图、效果图等）和装修相关文档（合同、报价单），系统便会利用多模态 AI 进行批判性分析——自动框出图纸上的卫生死角、揭露报价单中的过度装修、指出合同中的隐形陷阱，并生成一份**带图像标注的在线可视化报告**和可下载的 PDF。

> 你只需：上传设计图纸和相关文档，用自然语言描述房屋情况</br>
> 系统将返回：一份详尽的批判性分析报告，原图上叠加问题标注框，点击即可查看每个坑位的套路揭露和替代方案

> ⚠️ 系统**不是中立的设计审查工具**，而是**消费者的辩护人**。任何增加成本却降低生活品质的设计，都会被标记为"智商税"。

### 我们的愿景

装修行业信息极度不对称——装修公司利用专业知识优势，通过复杂装饰、模糊报价、隐蔽增项等方式抬高成本。我们致力于用 AI 打破这种信息壁垒：

- **对消费者**：上传图纸即可获得专业批判意见，无需花钱请第三方监理，轻松识破套路
- **对行业**：通过持续积累的坑位数据，推动装修服务透明化，让"良心装修"成为竞争力

从设计图审查到合同报价分析，我们让每一次装修决策都有据可依。

## 🌐 在线体验

欢迎访问在线 Demo 演示环境，体验我们为你准备的一次装修图纸审查与合同避坑分析：[https://renopit.fthux.com](https://renopit.fthux.com/)

## 📸 系统截图

### 前端

<details>
<summary>主页</summary>

![主页](screenshots/frontend/主页.png)
</details>

<details>
<summary>创建项目 & 上传素材</summary>

![创建项目](screenshots/frontend/创建项目.png)
</details>

<details>
<summary>项目列表</summary>

![项目列表](screenshots/frontend/项目列表.png)
</details>

<details>
<summary>删除项目</summary>

![项目列表-删除](screenshots/frontend/项目列表-删除.png)
</details>

<details>
<summary>复制项目</summary>

![项目列表-复制](screenshots/frontend/项目列表-复制.png)
</details>

<details>
<summary>分析报告 — 总体评价</summary>

![总体评价](screenshots/frontend/项目报告-总体评价.png)
</details>

<details>
<summary>分析报告 — 问题详情（含图像标注定位）</summary>

![问题详情](screenshots/frontend/项目报告-问题详情.png)
</details>

<details>
<summary>分析报告 — 合同 / 报价单审查</summary>

![合同报价单分析](screenshots/frontend/项目报告-合同:报价单分析.png)
</details>

<details>
<summary>分析报告 — 增项预测</summary>

![增项预测](screenshots/frontend/项目报告-增项预测.png)
</details>

<details>
<summary>分析报告 — 跨文档交叉核查</summary>

![跨文档交叉核查](screenshots/frontend/项目报告-跨文档交叉核查.png)
</details>

### 后端

<details>
<summary>API 文档 — Swagger UI</summary>

![Swagger 文档](screenshots/backend/docs.png)
</details>

<details>
<summary>API 文档 — ReDoc</summary>

![ReDoc 文档](screenshots/backend/redoc.png)
</details>

<details>
<summary>健康检查接口</summary>

![健康检查](screenshots/backend/health.png)
</details>

## 🔄 工作流程

1. **上传素材**：拖拽上传多张设计图（JPG/PNG/WEBP）+ 装修文档（合同/报价单 TXT/MD/DOCX/PDF）+ 文字补充说明（至少一项）
2. **AI 分析**：多模态大模型识别图纸 + 本地知识库匹配核心坑位 + 联网搜索最新套路，输出含 bbox 坐标的结构化批判报告
3. **在线报告**：分析完成后自动渲染可视化报告——原图上叠加红色标注框，点击即可查看每个问题的批判详情、套路揭露和替代方案
4. **下载 PDF**：点击按钮一键生成 PDF 报告（含中文），随时分享给装修公司"对峙"

## 🚀 快速开始

### 前提要求

- 安装 **Docker** 和 **Docker Compose**
- 准备一个 LLM API Key（OpenAI 或兼容接口）

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 2. 一键启动

```bash
docker-compose up -d
```

### 3. 访问系统

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| 后端 API 文档 | http://localhost:8000/docs |

## 📄 致谢

本项目灵感来源于装修过程中踩过的坑。感谢所有在装修中分享避坑经验的消费者，你们的每一次分享都在推动行业透明化。

---

<div align="center">

**让 AI 替你审查每一张图纸、每一份合同，装修不再任人宰割。**

</div>