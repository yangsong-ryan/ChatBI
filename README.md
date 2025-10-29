<p align="center"><img src="http://www.crud-boy.com/images/logo/chatbi-logo.png" alt="SQLBot" width="300" /></p>
<h3 align="center">基于大模型和 RAG 的智能问数系统</h3>

<p align="center">
  <img src="https://img.shields.io/badge/LangChain-FABE0A?style=for-the-badge&logo=LangChain&logoColor=black" alt="LangChain">
  <img src="https://img.shields.io/badge/RAG-检索增强生成-blue?style=for-the-badge" alt="RAG">
  <img src="https://img.shields.io/badge/PyMySQL-4479A1?style=for-the-badge&logo=MySQL&logoColor=white" alt="PyMySQL">
  <img src="https://img.shields.io/badge/ECharts-AA344D?style=for-the-badge&logo=Apache&logoColor=white" alt="ECharts">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white" alt="Streamlit">
</p>

---

ChatBI是一个基于LangChain的AI数据分析助手，集成了数据库查询、知识库检索和可视化图表生成三大核心功能。本项目专为LangChain学习者设计，帮助理解Agent执行流程和工作原理。

## ✨ 核心功能

1. **数据库智能查询**
   - 自动生成SQL语句并执行
   - 支持MySQL数据库连接配置
   - 数据字典自动解析

2. **知识库检索(RAG)**
   - 基于百川Embedding的向量检索
   - 支持多文档上传和文本分割
   - MMR(Maximal Marginal Relevance)检索策略

3. **可视化图表生成**
   - 📊 柱状图 - 数据对比分析
   - 📈 折线图 - 趋势变化展示 
   - 🥧 饼图 - 比例分布可视化

## 🚀 技术栈

| 组件       | 技术实现               |
| ---------- | ---------------------- |
| 前端框架   | Streamlit              |
| LLM框架    | LangChain              |
| 向量数据库 | Chroma                 |
| 嵌入模型   | BaichuanTextEmbeddings |
| 图表库     | PyEcharts              |
| 数据库驱动 | PyMySQL                |

## 👉 体验地址

`http://www.crud-boy.com/`

## 🖼️ 项目展示

![chatbi-1](http://www.crud-boy.com/images/logo/chatbi_1.png)

![chatbi-2](http://www.crud-boy.com/images/logo/chatbi_2.png)

---

## 📦 安装指南

### 前置要求
- Python 3.11+

  - 建议使用conda搭建python环境

  - ```sh
    # 安装 Miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
    
    # 将 conda 临时添加到 PATH（仅当前会话有效）
    export PATH="$HOME/miniconda/bin:$PATH"
    
    # 初始化 conda（永久生效）
    conda init
    conda config --set auto_activate_base false
    
    # 创建新环境（现在 conda 已可用）
    conda create -n chatbi python=3.11 -y
    # 激活新环境
    conda activate chatbi
    ```

- Chrome浏览器(用于图表渲染)

  - ```sh
    ##########################################安装 google-chrome##########################################
    
    # 1. 安装必要的依赖包
    sudo dnf install -y dnf-plugins-core wget
    
    # 2. 创建Google Chrome官方仓库配置文件
    sudo tee /etc/yum.repos.d/google-chrome.repo <<'EOL'
    [google-chrome]
    name=google-chrome
    baseurl=https://dl.google.com/linux/chrome/rpm/stable/$basearch
    enabled=1
    gpgcheck=1
    gpgkey=https://dl.google.com/linux/linux_signing_key.pub
    EOL
    
    # 3. 导入Google的GPG公钥
    # 用于验证软件包签名，确保下载的包未被篡改
    sudo rpm --import https://dl.google.com/linux/linux_signing_key.pub
    
    # 4. 安装Google Chrome稳定版
    sudo dnf install -y google-chrome-stable
    
    # 5. 验证安装
    # 显示已安装版本并检查可执行文件
    google-chrome --version
    
    ###############################安装 google-chrome版本对应的 chromedriver################################
    
    # 这里去下载对应版本的 chromedriver
    # https://developer.chrome.com/docs/chromedriver/downloads?hl=zh-cn
    
    # 1.下载
    # 找到对应版本下载链接后，替换以下链接
    wget "https://storage.googleapis.com/chrome-for-testing-public/141.0.7390.122/linux64/chromedriver-linux64.zip"
    
    # 2.解压
    unzip chromedriver-linux64.zip
    
    # 3.创建软链接
    sudo ln -s $(pwd)/chromedriver-linux64/chromedriver /usr/bin/chromedriver
    
    # 4.添加执行权限
    # 拿到配置文件里的 CHROMEDRIVER_PATH路径：/usr/bin/chromedriver
    sudo chmod +x /usr/bin/chromedriver
    
    # 5.验证是否安装成功
    chromedriver --version
    ```

- Nginx(用于托管图片，反向代理)

  - ```sh
    # 安装nginx（如果没有）
    yum install nginx
    
    # 修改配置文件
    vim /etc/nginx/nginx.conf
    
    # 启动
    systemctl start nginx
    # 查看状态
    systemctl status nginx
    # 重启
    systemctl restart nginx
    # 停止
    systemctl stop nginx
    ```

  - 参考nginx配置

    ```sh
        server {
            listen       80;
            listen       [::]:80;
            server_name  _;
            
            # 用于提供图片
            # 如果项目地址在 /data/ChatBI
            location /images/ {
                alias /data/ChatBI/images/;  
                expires 30d;  # 缓存30天
                access_log off;
            }
            # 反向代理配置   默认转发至 8501 即项目的streamlit
            location / {
                    proxy_pass http://localhost:8501;
                    
                    # 基础代理设置
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                    proxy_set_header X-Forwarded-Proto $scheme;
                    
                    # WebSocket和长连接支持
                    proxy_http_version 1.1;
                    proxy_set_header Upgrade $http_upgrade;
                    proxy_set_header Connection "upgrade";
                    
                    # 其他推荐设置
                    proxy_read_timeout 300s;
                    proxy_buffering off;
            }
    
            # Load configuration files for the default server block.
            include /etc/nginx/default.d/*.conf;
    
            error_page 404 /404.html;
            location = /404.html {
            }
    
            error_page 500 502 503 504 /50x.html;
            location = /50x.html {
            }
        }
    
    ```

- MySQL数据库(可选)

### 安装步骤
1. 克隆仓库：
   ```sh
   git clone https://github.com/yourusername/chatbi.git
   cd chatbi

1. 安装依赖：

   ```sh
   # 激活项目环境
   conda activate chatbi
   
   # 安装项目依赖
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. 配置环境变量： 复制`.env.example`文件为`.env`并填写您的配置：

## 🖥 使用说明

1. 启动应用：

   ```sh
   # 启动nginx
   systemctl start nginx
   
   # 激活项目环境
   conda activate chatbi
   
   # 启动项目，也可后台启动，或将其配置到linux service
   streamlit run chatbi.py
   ```

2. 访问方式：

   * 直接访问streamlit：浏览器中打开`http://<你的服务器IP>:8501/`
   * 也可直接访问`http://<你的服务器IP>`

3. 界面功能介绍：

   - 左侧边栏：
     - 📁 知识库文档上传区
     - 📖 数据字典文档上传区
     - 🗄 数据库配置区
     - ❓ 帮助说明区

4. 典型使用流程：

   ```
   1. 上传知识库文档(或使用默认文档)
   2. 配置数据库连接(可选)
   3. 上传数据字典文档(或使用默认文档)
   4. 在聊天框输入问题，例如：
      - "北极星计划和天宫项目是什么？预算分别是多少？画一个饼图"
   ```

## 🧠 LangChain学习重点

本项目特别适合学习LangChain的以下概念：

- Agent执行流程(思考→动作→观察循环)
- 多工具协同工作
- 自定义Tool实现
- Memory管理
- RAG集成
- 结构化输出解析

主要代码文件：`chatbi.py` 中包含完整的：

- 工具定义(Tool/StructuredTool)
- Agent创建(create_react_agent)
- 记忆管理(ConversationBufferMemory)
- 提示工程(PromptTemplate)

## 📂 项目结构

```
chatbi/
├── .gitignore               # Git忽略规则文件
├── LICENSE                  # 项目许可证文件
├── README.md                # 项目说明文档
├── DDL.sql                  # 测试数据库DDL（基于参考数据字典）
├── chatbi.py                # 主程序文件
├── requirements.txt         # Python依赖文件
├── .env.example             # 环境变量示例文件
├── 参考数据字典.txt           # 默认数据字典
├── 参考知识库.txt             # 默认知识库文档
├── images/                  # 生成的图表存储目录
└── tmp/                     # 临时文件目录
```

## 🤝 贡献指南

欢迎提交Pull Request！建议改进方向：

- 支持更多图表类型
- 优化数据库查询逻辑
- 添加测试用例
- 改进RAG检索效果

## 📞 联系我们

有问题或想了解更多？欢迎添加微信：`mxjx_1997`

## 📄 许可证

[MIT License](LICENSE)

------

🛠️ *本项目专为LangChain学习者设计，通过实际项目掌握Agent工作原理！*