# DBAutoOps - 数据库自动化运维平台

<div align="center">

一个功能强大的数据库自动化运维管理平台，提供数据备份、数据血缘分析、作业模板管理等核心功能。

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

</div>

---

## 📖 项目简介

**DBAutoOps** 是一个基于 Flask 的数据库自动化运维平台，旨在简化数据库日常运维工作，提高运维效率。系统集成了以下核心功能：

- 🔐 **用户认证系统**：安全的用户注册、登录、会话管理
- 💾 **智能数据备份**：支持增量备份、自动锁表机制、进程监控、远程同步
- 🔍 **数据血缘分析**：可视化展示数据表的上下游依赖关系
- 📝 **作业模板管理**：自动提取和管理 Flink 作业配置模板
- 📧 **邮件告警**：备份异常时自动发送邮件通知
- 📊 **可视化仪表盘**：直观的 Web 界面操作

---

## 🏗️ 系统架构

### 目录结构

```
DBAutoOps/
├── app.py                      # Flask 应用主入口
├── auth.py                     # 用户认证模块（注册/登录/登出）
├── config.py                   # 配置文件（数据库连接、邮箱配置等）
├── utils.py                    # 工具函数（数据库连接、页面路由）
├── create.sql                  # 用户表创建 SQL
├── requirements.txt            # Python 依赖清单
│
├── backUp_module/              # 数据备份模块
│   ├── back_up.py             # 备份核心逻辑（pt-archiver、锁表、校验）
│   ├── alert.py               # 邮件告警功能
│   └── create.sql             # 锁表创建 SQL
│
├── dlm_module/                 # 数据血缘管理模块（Data Lineage Management）
│   ├── sql_extract_to_db.py   # GitLab SQL 扫描入库
│   ├── draw.py                # 血缘关系图生成（基于 NetworkX 和 Pyvis）
│   ├── clone.py               # Git 仓库克隆工具
│   ├── sql_extract.py         # SQL 解析提取
│   ├── to_db.py               # 血缘数据写入数据库
│   └── create.sql             # 血缘表创建 SQL
│
├── alioth_module/              # Alioth 作业模板管理模块
│   ├── alioth.py              # 作业模板分析与生成
│   ├── generate.py            # JSON 文法生成器
│   ├── extract.py             # 作业配置提取
│   └── create.sql             # 作业模板表创建 SQL
│
├── templates/                  # Flask HTML 模板
│   ├── login.html             # 登录页面
│   ├── register.html          # 注册页面
│   ├── dashboard.html         # 仪表盘
│   ├── back_up.html           # 数据备份页面
│   ├── data_lineage.html      # 数据血缘页面
│   └── alioth_example.html    # 作业模板查看页面
│
├── static/                     # 静态资源
│   ├── css/                   # 样式文件
│   ├── images/                # 图片资源
│   └── lineage_graphs/        # 生成的血缘图 HTML 文件
│
└── lib/                        # 前端 JavaScript 库
    ├── vis-9.1.2/             # Vis.js 网络可视化库
    └── tom-select/            # Tom-select 下拉选择库
```

---

## 🎯 主要模块介绍

### 1️⃣ 用户认证模块（`auth.py`）

- **注册功能**：密码复杂度验证（至少 8 位，包含大小写字母和数字）
- **登录功能**：会话管理，防止未授权访问
- **登出功能**：清除会话数据
- **仪表盘**：用户主界面，跳转到各功能模块

### 2️⃣ 数据备份模块（`backUp_module/`）

**核心功能**：
- 基于 `pt-archiver` 工具进行高效数据归档
- 支持三种模式：
  - `save`：仅备份不删除
  - `delete`：备份并删除源数据
  - `default`：仅备份不删除（同 save）
- 智能锁表机制：防止重复备份
- 进程监控：自动检测僵尸进程并清理锁
- 数据校验：备份前后记录数对比
- 远程同步：通过 rsync 自动上传备份文件
- 邮件告警：备份失败时发送邮件通知

**主要接口**：
- `/query_table`：查询表信息（记录数、字段数、容量）
- `/backup_table_route`：执行备份任务
- `/get_table_fields`：获取表字段列表

### 3️⃣ 数据血缘模块（`dlm_module/`）

**核心功能**：
- GitLab 仓库扫描：自动克隆并解析 SQL 脚本
- SQL 解析：提取 source/target 表依赖关系
- 血缘图生成：
  - 基于 NetworkX 构建有向图
  - 使用 Pyvis 生成交互式 HTML 可视化
  - 红色节点：目标表
  - 蓝色节点：上游表
  - 绿色节点：下游表
- 递归追溯：自动追溯完整的上下游链路

**主要接口**：
- `/run_gitlab_scanner`：扫描 GitLab 仓库并入库
- `/generate_lineage_graph_route`：生成血缘关系图

### 4️⃣ 作业模板管理模块（`alioth_module/`）

**核心功能**：
- Flink 作业配置分析：自动提取 sources/sinks/udfs 组合模式
- 文法生成：基于出现频率生成通用模板
- 模板存储：将典型配置存储到数据库
- 模板查看：Web 界面查看和选择已生成的模板

**主要接口**：
- `/analyze_table`：分析作业表并生成模板
- `/show_templates_page`：展示所有模板列表
- `/view_specific_template`：查看特定模板详情

---

## 🚀 安装与运行步骤

### 前置要求

- **Python**: 3.7+
- **MySQL**: 5.7+ 或 8.0+
- **pt-archiver**: Percona Toolkit 工具（用于数据备份）
- **Git**: 用于克隆 GitLab 仓库
- **rsync**: 用于远程文件同步

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd DBAutoOps
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置数据库

#### 创建数据库

```sql
CREATE DATABASE ops CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 创建用户表

执行主目录下的 `create.sql`：

```bash
mysql -u your_user -p ops < create.sql
```

#### 创建锁表

```bash
mysql -u your_user -p ops < backUp_module/create.sql
```

#### 创建数据血缘表

```bash
mysql -u your_user -p ops < dlm_module/create.sql
```

#### 创建 Alioth 作业模板表

```bash
mysql -u your_user -p ops < alioth_module/create.sql
```

### 4. 修改配置文件

编辑 `config.py`，修改以下配置：

```python
# 用户登录数据库配置
class Config_users:
    MYSQL_HOST = 'localhost'
    MYSQL_DATABASE = 'ops'
    MYSQL_USER = 'your_username'          # 修改为实际用户名
    MYSQL_PASSWORD = 'your_password'      # 修改为实际密码

# 备份锁表数据库配置
class Config_lock:
    MYSQL_HOST = 'localhost'
    MYSQL_DATABASE = 'ops'
    MYSQL_USER = 'your_username'
    MYSQL_PASSWORD = 'your_password'
    MYSQL_PORT = 3306
    
    # 邮箱告警配置
    EMAIL_PORT = 587
    EMAIL_HOST = 'smtp.example.com'       # 修改为你的 SMTP 服务器
    EMAIL_USER = 'your@email.com'         # 修改为你的邮箱
    EMAIL_PASS = 'your_app_password'      # 修改为邮箱授权码
    ALERT_EMAIL = 'alert@example.com'     # 修改为接收告警的邮箱

# 数据血缘数据库配置
class Config_DLM:
    host = 'localhost'
    user = 'your_username'
    password = 'your_password'
    port = 3306
    database = 'ops'

# Alioth 作业配置
class Config_alioth:
    # 线上作业数据库配置
    host = 'localhost'
    user = 'your_username'
    password = 'your_password'
    port = 3306
    database = 'ops'
    table_name = 'flink_jobs_2'
    
    # 模板存储数据库配置
    user_for_online = 'your_username'
    password_for_online = 'your_password'
    host_for_online = 'localhost'
    port_for_online = 3306
    database_for_online = 'ops'
```

### 5. 安装 pt-archiver（仅备份功能需要）

**CentOS/RHEL**:
```bash
yum install percona-toolkit
```

**Ubuntu/Debian**:
```bash
apt-get install percona-toolkit
```

**验证安装**:
```bash
pt-archiver --version
```

### 6. 启动应用

```bash
python app.py
```

应用将运行在 `http://localhost:5001`

### 7. 访问系统

浏览器打开：`http://localhost:5001`

- 首次使用需要注册账号
- 注册成功后登录进入仪表盘

---

## ⚙️ 配置文件说明

### `Config_users`

用于用户认证系统的数据库连接配置。

| 参数 | 说明 | 示例 |
|------|------|------|
| `MYSQL_HOST` | 数据库主机地址 | `localhost` |
| `MYSQL_DATABASE` | 数据库名称 | `ops` |
| `MYSQL_USER` | 数据库用户名 | `root` |
| `MYSQL_PASSWORD` | 数据库密码 | `your_password` |

### `Config_lock`

用于备份锁表和邮件告警配置。

| 参数 | 说明 | 示例 |
|------|------|------|
| `MYSQL_HOST` | 锁表数据库主机 | `localhost` |
| `MYSQL_DATABASE` | 锁表所在数据库 | `ops` |
| `MYSQL_USER` | 数据库用户名 | `root` |
| `MYSQL_PASSWORD` | 数据库密码 | `your_password` |
| `MYSQL_PORT` | 数据库端口 | `3306` |
| `EMAIL_HOST` | SMTP 服务器地址 | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP 端口 | `587` |
| `EMAIL_USER` | 发件邮箱 | `your@email.com` |
| `EMAIL_PASS` | 邮箱授权码 | `app_password` |
| `ALERT_EMAIL` | 告警接收邮箱 | `alert@email.com` |

### `Config_DLM`

用于数据血缘模块的数据库配置。

| 参数 | 说明 | 示例 |
|------|------|------|
| `host` | 数据库主机 | `localhost` |
| `user` | 数据库用户名 | `root` |
| `password` | 数据库密码 | `your_password` |
| `port` | 数据库端口 | `3306` |
| `database` | 数据库名称 | `ops` |
| `config_fn` | 配置文件名列表 | `['config.py', 'conf.py']` |

### `Config_alioth`

用于 Alioth 作业模板管理配置。

| 参数 | 说明 |
|------|------|
| `host` | 线上作业数据库主机 |
| `user` | 数据库用户名 |
| `password` | 数据库密码 |
| `database` | 数据库名称 |
| `table_name` | 作业表名 |
| `field1` | 启动参数字段名 |
| `field2` | 流标识符字段名 |
| `times_for_grammer` | 第一次筛选阈值 |
| `times_for_grammer_2` | 第二次筛选阈值 |

---

## 🎨 主要功能演示

### 1. 数据备份

1. 登录后进入仪表盘，点击"数据备份"
2. 输入备份参数：
   - **主机名**：数据库实例地址
   - **数据库名**：目标数据库
   - **表名**：目标表
3. 点击"查询表信息"查看表详情
4. 选择备份字段和时间范围
5. 选择备份模式（save/delete）
6. 输入 rsync 目标地址
7. 点击"开始备份"

**特性**：
- 自动锁表防止重复备份
- 实时进度显示（每 10000 条记录）
- 备份完成后自动校验
- 自动上传到远程服务器
- 失败时邮件告警

### 2. 数据血缘分析

1. 点击"数据血缘"进入血缘分析页面
2. 输入 GitLab 仓库 URL（包含 SQL 脚本）
3. 点击"扫描 GitLab"，系统将：
   - 克隆仓库到本地
   - 解析 SQL 脚本
   - 提取表依赖关系
   - 存储到数据库
4. 输入目标表信息（实例、库、表）
5. 点击"生成血缘图"
6. 查看交互式血缘关系图

**血缘图说明**：
- 节点颜色：红色（目标表）、蓝色（上游）、绿色（下游）
- 鼠标悬停查看详细信息
- 边上显示相关 SQL 脚本名称

### 3. 作业模板管理

1. 点击"作业模板"进入模板管理页面
2. 输入作业表信息（实例、库、表）
3. 点击"分析表"，系统将：
   - 提取所有作业配置
   - 统计 source/sink/udf 组合模式
   - 生成通用模板
   - 存储到模板库
4. 在模板列表中选择模板
5. 点击"查看"查看模板详情

---

## 📊 接口列表

### 认证相关

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 重定向到登录页 |
| `/register` | GET, POST | 用户注册 |
| `/login` | GET, POST | 用户登录 |
| `/logout` | GET | 用户登出 |
| `/dashboard` | GET | 仪表盘 |

### 数据备份

| 路由 | 方法 | 说明 |
|------|------|------|
| `/to_back_up` | GET, POST | 跳转到备份页面 |
| `/query_table` | GET, POST | 查询表信息 |
| `/backup_table_route` | GET, POST | 执行备份 |
| `/get_table_fields` | GET, POST | 获取表字段 |

### 数据血缘

| 路由 | 方法 | 说明 |
|------|------|------|
| `/to_data_lineage` | GET, POST | 跳转到血缘页面 |
| `/run_gitlab_scanner` | GET, POST | 扫描 GitLab 仓库 |
| `/generate_lineage_graph_route` | GET, POST | 生成血缘图 |

### 作业模板

| 路由 | 方法 | 说明 |
|------|------|------|
| `/analyze_table` | GET, POST | 分析作业表 |
| `/show_templates_page` | GET, POST | 显示模板列表 |
| `/view_specific_template` | GET | 查看特定模板 |

---

## 📝 日志与错误处理机制

### 日志系统

项目使用 Python `logging` 模块进行日志记录：

```python
import logging

# 记录信息日志
logging.info("表备份成功")

# 记录错误日志
logging.error(f"备份失败: {error_message}")
```

日志级别：
- `INFO`：正常操作信息
- `ERROR`：错误信息
- `WARNING`：警告信息

### 错误处理机制

1. **数据库连接错误**：
   - 捕获 `mysql.connector.Error` 异常
   - 记录错误日志
   - 返回 `None` 或友好错误信息

2. **备份错误**：
   - 捕获 `CalledProcessError`（命令执行失败）
   - 捕获 `OSError`（文件操作错误）
   - 发送邮件告警
   - 自动解锁表

3. **血缘图生成错误**：
   - 捕获 `NetworkXError`（图构建错误）
   - 捕获数据库查询异常
   - 返回错误提示

4. **表单验证**：
   - Flask `flash` 消息提示
   - 前端输入验证
   - 密码复杂度检查

### 邮件告警

备份失败时自动发送邮件：

```python
from alert import send_alert

send_alert(
    subject="备份失败告警",
    body=f"表 {host}.{db}.{table} 备份失败：{error_message}"
)
```

---

## 🔮 未来改进方向

### 安全性增强

- [ ] 密码加密存储（使用 bcrypt 或 argon2）
- [ ] JWT Token 认证机制
- [ ] API 接口权限控制
- [ ] SQL 注入防护增强
- [ ] HTTPS 支持

### 功能扩展

- [ ] 支持更多数据库类型（PostgreSQL、Oracle、MongoDB）
- [ ] 定时备份任务调度（Celery + Redis）
- [ ] 备份文件压缩和加密
- [ ] 数据恢复功能
- [ ] 备份历史记录查询
- [ ] 数据血缘自动更新机制
- [ ] 更丰富的血缘图可视化选项
- [ ] 作业模板自动推荐

### 性能优化

- [ ] 数据库连接池（SQLAlchemy）
- [ ] 异步任务处理（Celery）
- [ ] 大表备份分片处理
- [ ] 血缘图缓存机制
- [ ] 前端懒加载和分页

### 用户体验

- [ ] 前端框架升级（Vue.js/React）
- [ ] 响应式设计优化
- [ ] 实时进度显示（WebSocket）
- [ ] 更友好的错误提示
- [ ] 操作日志审计
- [ ] 多语言支持

### 运维监控

- [ ] Prometheus 指标暴露
- [ ] Grafana 仪表盘集成
- [ ] 备份成功率统计
- [ ] 系统健康检查接口
- [ ] 性能指标监控

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 邮件：1070058272@qq.com

---

## 🙏 致谢

本项目使用了以下优秀的开源项目：

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [MySQL Connector](https://dev.mysql.com/doc/connector-python/en/) - MySQL 数据库驱动
- [NetworkX](https://networkx.org/) - 图数据结构库
- [Pyvis](https://pyvis.readthedocs.io/) - 网络可视化库
- [Percona Toolkit](https://www.percona.com/software/database-tools/percona-toolkit) - MySQL 运维工具
- [Vis.js](https://visjs.org/) - 前端可视化库

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个 Star！⭐**

Made with ❤️ by DBAutoOps Team

</div>
