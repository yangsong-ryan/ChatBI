from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from io import BytesIO
import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain.agents import create_react_agent, AgentExecutor
import pymysql
from decimal import Decimal
from langchain.agents import Tool
import json
from langchain.agents.output_parsers.react_json_single_input import ReActJsonSingleInputOutputParser
import tempfile
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import BaichuanTextEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from pyecharts.charts import Bar, Line, Pie
from pyecharts import options as opts
from typing import List, Union, Tuple
import time
import uuid
from pathlib import Path
import os
from dotenv import load_dotenv
import datetime
import chromadb
import warnings
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)


# 加载环境变量
load_dotenv()

# 设置Streamlit应用配置
st.set_page_config(page_title="Chat BI", layout="wide", page_icon="📊")
st.title("Chat BI")

# 数据库配置默认值
DEFAULT_DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "port": os.getenv("MYSQL_PORT"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "charset": os.getenv("MYSQL_CHARSET")
}


# 初始化数据库配置
if "db_config" not in st.session_state:
    st.session_state.db_config = DEFAULT_DB_CONFIG.copy()

def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        # print(f"文件夹 '{path}' 已创建")
    else:
        pass
        # print(f"文件夹 '{path}' 已存在")

BASE_DIR = Path(__file__).resolve().parent
BASE_URL_IMAGES = os.getenv("BASE_URL_IMAGES")

BASE_PATH_IMAGES = os.path.join(BASE_DIR, "images")
# 判断图片存储文件夹是否存在，不存在则创建
make_dir(BASE_PATH_IMAGES)

TMP_DIR = os.path.join(BASE_DIR, "tmp")
# 判断临时文件夹是否存在，不存在则创建
make_dir(TMP_DIR)

# 默认文件路径
DEFAULT_RAG_FILE_PATH = os.path.join(BASE_DIR, "参考知识库.txt")
# 默认数据字典文件路径
DEFAULT_DATA_DIC_FILE_PATH = os.path.join(BASE_DIR, "参考数据字典.txt")


def read_default_file(file_path: str):
    with open(file_path, "rb") as f:
        return f.read()

def test_database_connection(db_config):
    """测试数据库连接是否成功"""
    try:
        # 尝试建立数据库连接
        connection = pymysql.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
            port=int(db_config["port"]),
            charset=db_config["charset"]
        )

        # 如果连接成功，关闭连接并返回True
        connection.close()
        return True, "✅ 数据库连接成功！"
    except pymysql.MySQLError as e:
        # 连接失败，返回错误信息
        return False, f"❌ 数据库连接失败: {str(e)}"
    except Exception as e:
        # 其他异常
        return False, f"❌ 发生未知错误: {str(e)}"


# 侧边栏分成3个区块
with st.sidebar:
    # 区块1: 文档上传区
    with st.expander("📁 知识库文档上传", expanded=False):
        # 检索文档部分
        uploaded_files = st.file_uploader(
            label="上传知识库文档", type=["txt"], accept_multiple_files=True
        )

        # 如果没有上传文件，则使用默认文件
        if not uploaded_files:
            default_file_content = read_default_file(DEFAULT_RAG_FILE_PATH)
            default_file = BytesIO(default_file_content)
            default_file.name = "参考知识库.txt"
            uploaded_files = [default_file]
            # print("未上传文件：")
            # print(default_file)
            # 如果没有上传文件，需要强制清除一下缓存
            # 因为当用户先上传文件，再取消之后，streamlit不会自动清除缓存，会出bug
            # 用户初次访问，会执行 configure_retriever，用户上传文件之后，会执行 configure_retriever
            # 但是此时用户再删除文件，便不会重新执行 configure_retriever，按理来说应该要执行的，因为函数参数已经更新了，但实际上并没有执行
            # 这就导致 configure_retriever用的还是之前缓存的那个，而不是变更之后的，就会报错
            # 所以我们手动清除缓存
            st.cache_resource.clear()  # 清除所有 @st.cache_resource 缓存
            # st.rerun()  # 重新运行应用
            st.info("当前未上传检索文档，使用默认文档：参考知识库.txt")
            if st.button("🔍 预览默认检索文档"):
                with st.expander("📄 默认检索文档内容", expanded=True):
                    st.code(default_file_content.decode('utf8'), language="text")
    # 区域2：数据字典文档上传
    with st.expander("📖 数据字典文档上传", expanded=False):
        # 数据字典部分
        data_uploaded_files = st.file_uploader(
            label="上传数据字典文档", type=["txt"], accept_multiple_files=True
        )

        # 如果没有上传文件，则使用默认文件
        if not data_uploaded_files:
            default_file_content = read_default_file(DEFAULT_DATA_DIC_FILE_PATH)
            default_file = BytesIO(default_file_content)
            default_file.name = "参考数据字典.txt"
            data_uploaded_files = [default_file]
            st.cache_resource.clear()  # 清除所有 @st.cache_resource 缓存
            st.info("当前未上传数据字典文档，使用默认文档：参考数据字典.txt")
            if st.button("📊 预览默认数据字典"):
                with st.expander("📝 默认数据字典内容", expanded=True):
                    st.code(default_file_content.decode('utf8'), language="text")

    # 区块3: 数据库配置区
    with st.expander("🗄 数据库配置", expanded=False):
        if st.button("⚙️ 配置数据库连接"):
            st.session_state.show_db_config = True

        if st.session_state.get("show_db_config", False):
            st.write("请填写数据库连接信息:")

            col1, col2 = st.columns(2)
            with col1:
                st.session_state.db_config["host"] = st.text_input(
                    "主机地址",
                    value=st.session_state.db_config["host"],
                    help="数据库服务器地址"
                )
                st.session_state.db_config["port"] = st.text_input(
                    "端口",
                    value=st.session_state.db_config["port"],
                    help="数据库端口号"
                )
                st.session_state.db_config["user"] = st.text_input(
                    "用户名",
                    value=st.session_state.db_config["user"],
                    help="数据库用户名"
                )

            with col2:
                st.session_state.db_config["password"] = st.text_input(
                    "密码",
                    value=st.session_state.db_config["password"],
                    type="password",
                    help="数据库密码"
                )
                st.session_state.db_config["database"] = st.text_input(
                    "数据库名",
                    value=st.session_state.db_config["database"],
                    help="要连接的数据库名称"
                )
                st.session_state.db_config["charset"] = st.text_input(
                    "字符集",
                    value=st.session_state.db_config["charset"],
                    help="数据库字符集"
                )

            test_col1, test_col2 = st.columns([1, 3])
            with test_col1:
                if st.button("🔍 测试连接"):
                    success, message = test_database_connection(st.session_state.db_config)
                    test_col2.write(message)
                    st.session_state.db_connection_success = success

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ 保存配置", disabled=not st.session_state.get("db_connection_success", False)):
                    st.session_state.show_db_config = False
                    st.rerun()
            with col2:
                if st.button("🔄 重置默认"):
                    st.session_state.db_config = DEFAULT_DB_CONFIG.copy()
                    st.session_state.db_connection_success = False
                    st.rerun()
            with col3:
                if st.button("❌ 取消"):
                    st.session_state.show_db_config = False
                    st.rerun()

            if not st.session_state.get("db_connection_success", False):
                st.warning("请先测试数据库连接，成功后才能保存配置")

    # 区块4: 帮助说明区
    with st.expander("❓ 图表使用说明", expanded=True):
        st.markdown("""
        **支持自动生成的图表类型：**
        - 📊 柱状图 - 数据对比
        - 📈 折线图 - 趋势分析  
        - 🥧 饼图 - 比例分布

        **示例问题：**
        - 北极星计划和天宫项目是什么，还有他们的预算分别是多少，画一个饼图
        - 各项目的占比分布
        """)


def generate_img_filename(type: str):
    # 生成随机的UUID（去掉连字符）
    random_uuid = str(uuid.uuid4()).replace('-', '')

    # 获取当前时间戳（精确到毫秒）
    timestamp = int(time.time() * 1000)

    # 组合成文件名
    html_filename = f"{type}_{random_uuid}_{timestamp}.html"
    png_filename = f"{type}_{random_uuid}_{timestamp}.png"
    html_path = os.path.join(BASE_PATH_IMAGES,html_filename)
    png_path = os.path.join(BASE_PATH_IMAGES,png_filename)
    png_url = f"{BASE_URL_IMAGES}/{png_filename}"

    return html_path,png_path,png_url
def delete_file_if_is_file(filename):
    """用于删除生成图表所用到的html文件。如果是文件且存在，则删除"""
    if os.path.exists(filename) and os.path.isfile(filename):
        os.remove(filename)
        print(f"文件 {filename} 已删除")
    else:
        print(f"{filename} 不是文件或不存在")

CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")

def get_chromedriver_service(chromedriver_path=CHROMEDRIVER_PATH):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Chrome 112+新版无头模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--force-device-scale-factor=1.5")  # 高清缩放
    
    # 关键：启用软件渲染backend
    chrome_options.add_argument("--use-gl=angle")
    chrome_options.add_argument("--use-angle=swiftshader")
    
    # 显式设置虚拟显示大小
    chrome_options.add_argument("--window-size=1920,1080")

    # 关键：强制指定字体
    chrome_options.add_argument("--font-render-hinting=full")
    chrome_options.add_argument("--force-font-fallback=")  # 禁用回退字体
    chrome_options.add_argument("--disable-features=FontSrcLocalMatching")
    
    # 确保字体目录被加载
    chrome_options.add_argument("--lang=zh-CN")
    
    # 打印可用字体（调试用）
    chrome_options.add_argument("--enable-logging=stderr")
    chrome_options.add_argument("--v=1")
    
    # 使用本地 ChromeDriver
    service = Service(chromedriver_path)
    # 创建无头浏览器实例
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


# 开始生成工具
# 工具一：sql查询
def get_sql_result(sql_query: str):
    """数据库查询函数 - 保持不变"""
    db_config = st.session_state.db_config
    connection = pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        port=int(db_config["port"]),
        charset=db_config["charset"]
    )
    print("sql_query:", sql_query)
    try:
        with connection.cursor() as cursor:
            sql = sql_query
            cursor.execute(sql)
            results = cursor.fetchall()

            # 自定义序列化函数
            def default_serializer(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, (datetime.date, datetime.datetime)):
                    return obj.isoformat()
                elif isinstance(obj, bytes):
                    return obj.decode('utf-8')
                raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

            # 处理结果
            processed_results = []
            for row in results:
                processed_row = []
                for item in row:
                    try:
                        # 尝试直接序列化
                        json.dumps(item, default=default_serializer)
                        processed_row.append(item)
                    except (TypeError, ValueError):
                        # 无法序列化的值使用自定义函数处理
                        processed_row.append(default_serializer(item))
                processed_results.append(tuple(processed_row))

            # 使用自定义序列化器
            return json.dumps(processed_results, default=default_serializer)
    except Exception as e:
        # 捕获其他异常
        error_info = {
            "status": "error",
            "error_message": str(e)
        }
        return json.dumps(error_info)
    finally:
        connection.close()


sqlTool = Tool(
    name="查询数据库",
    description="数据库sql查询函数",
    func=get_sql_result,
)


# 工具二：柱状图工具
def generate_bar_chart(title: str, xaxis_name: str, xaxis_data: List[str], yaxis_name: str,
                       yaxis_data: List[Union[int, float]]):
    # 创建柱状图
    bar = (
        Bar(init_opts=opts.InitOpts(width="1600px", height="800px", bg_color="#ffffff"))
        .add_xaxis(xaxis_data)
        .add_yaxis(yaxis_name, yaxis_data,
                   itemstyle_opts=opts.ItemStyleOpts(color="#5470c6"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title,
                                      title_textstyle_opts=opts.TextStyleOpts(font_size=20)),
            toolbox_opts=opts.ToolboxOpts(),
            legend_opts=opts.LegendOpts(pos_left="right"),
            xaxis_opts=opts.AxisOpts(name=xaxis_name,
                                     name_textstyle_opts=opts.TextStyleOpts(font_size=14)),
            yaxis_opts=opts.AxisOpts(name=yaxis_name,
                                     name_textstyle_opts=opts.TextStyleOpts(font_size=14))
        )
    )

    html_path,png_path,png_url = generate_img_filename("bar")
    # 保存为HTML
    bar.render(html_path)
    driver = get_chromedriver_service()

    try:
        # 保存为高分辨率图片
        make_snapshot(snapshot, html_path, png_path,driver=driver, pixel_ratio=3)
        print(f"图表已成功保存为 {png_path}")
        return png_url
    finally:
        delete_file_if_is_file(html_path)
        # 关闭浏览器
        driver.quit()


# 多参数函数，需要用 StructuredTool
barChartTool = StructuredTool.from_function(
    func=generate_bar_chart,
    name="生成柱状图",
    description="生成可视化柱状图表，返回值为图表地址",
)


# 工具三：折线图工具
def generate_line_chart(title: str, xaxis_name: str, xaxis_data: List[str], yaxis_name: str,
                        yaxis_data: List[Union[int, float]]):
    # 创建折线图
    line = (
        Line(init_opts=opts.InitOpts(width="1600px", height="800px", bg_color="#ffffff"))
        .add_xaxis(xaxis_data)
        .add_yaxis(yaxis_name, yaxis_data,
                   is_smooth=True,
                   symbol_size=8)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, title_textstyle_opts=opts.TextStyleOpts(font_size=20)),
            toolbox_opts=opts.ToolboxOpts(),
            legend_opts=opts.LegendOpts(pos_left="right"),
            xaxis_opts=opts.AxisOpts(name=xaxis_name, name_textstyle_opts=opts.TextStyleOpts(font_size=14)),
            yaxis_opts=opts.AxisOpts(name=yaxis_name, name_textstyle_opts=opts.TextStyleOpts(font_size=14))
        )
    )

    html_path,png_path,png_url = generate_img_filename("line")
    # 保存为HTML
    line.render(html_path)
    driver = get_chromedriver_service()

    try:
        # 保存为高分辨率图片
        make_snapshot(snapshot, html_path, png_path,driver=driver, pixel_ratio=3)
        print(f"图表已成功保存为 {png_path}")
        return png_url
    finally:
        delete_file_if_is_file(html_path)
        # 关闭浏览器
        driver.quit()


# 多参数函数，需要用 StructuredTool
lineChartTool = StructuredTool.from_function(
    func=generate_line_chart,
    name="生成折线图",
    description="生成可视化折线图表，返回值为图表地址",
)


# 工具四：饼图
def generate_pie_chart(title: str, data_pair: List[Tuple[str, Union[int, float]]]):
    pie = (
        Pie(init_opts=opts.InitOpts(width="1600px", height="800px", bg_color="#ffffff"))
        .add(
            # 这个 series_name 是html里展示才能看出来，是鼠标悬浮会显示，这里不用
            series_name="",
            data_pair=data_pair,
            radius=["30%", "75%"],  # 内半径和外半径
            center=["50%", "50%"],  # 圆心位置
            rosetype=None,  # 设置为"radius"可创建南丁格尔玫瑰图
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                title_textstyle_opts=opts.TextStyleOpts(font_size=20)
            ),
            legend_opts=opts.LegendOpts(pos_left="right", orient="vertical")
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)")
        )
    )

    html_path,png_path,png_url = generate_img_filename("pie")
    # 保存为HTML
    pie.render(html_path)
    driver = get_chromedriver_service()

    try:
        # 保存为高分辨率图片
        make_snapshot(snapshot, html_path, png_path,driver=driver, pixel_ratio=3)
        print(f"图表已成功保存为 {png_path}")
        return png_url
    finally:
        delete_file_if_is_file(html_path)
        # 关闭浏览器
        driver.quit()


pieChartTool = StructuredTool.from_function(
    func=generate_pie_chart,
    name="生成饼图",
    description="生成可视化饼图表，返回值为图表地址",
)

# 百川向量模型Key
BAICHUAN_EMBEDDINGS_KEY = os.getenv("BAICHUAN_EMBEDDINGS_KEY")

# 这里是缓存retriever
# Streamlit 会在每次用户交互时重新运行整个脚本，为了避免重复计算昂贵的资源（如数据库连接、模型加载等），可以使用缓存装饰器
# 以下情况会重新执行该函数
# 1、TTL过期：代码设置了ttl="1h"，即从上次执行开始1小时后，缓存会失效，函数会重新执行。
# 2、输入参数变更：当函数参数 uploaded_files 发生变化时：用户上传了新文件等
@st.cache_resource(ttl="1h")
def configure_retriever(uploaded_files):
    # print("configure_retriever函数执行开始：")
    docs = []
    temp_dir = tempfile.TemporaryDirectory(dir=TMP_DIR)
    for file in uploaded_files:
        temp_filepath = os.path.join(temp_dir.name, file.name)
        with open(temp_filepath, "wb") as f:
            f.write(file.getvalue())
        loader = TextLoader(temp_filepath, encoding="utf-8")
        docs.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
    splits = text_splitter.split_documents(docs)

    key = BAICHUAN_EMBEDDINGS_KEY
    embeddings = BaichuanTextEmbeddings(api_key=key)

    # streamlit刷新一次，代码就会重新执行一次，就会把文件拿出来重新插入向量数据库，就会导致向量数据库的数据不断重复
    # 上面临时文件读取完毕之后，就会被删除，所有的数据都存在了这个向量数据库里
    # 而这个向量数据库如果不实体化，他是默认在内存中的
    # 我们多次创建文档，他默认是在内存里的同一个地方，所以我们如果多次执行，数据就会在同一个集合里不断叠加，造成重复
    # 这里没有指定 persist_directory
    # 但 Chroma 的默认行为是：
    # 在内存中创建一个临时集合（collection），但这个集合会被自动分配一个固定的默认名称（通常是 "langchain"）
    # 即使你重新执行 from_documents()，只要 Python 进程没有完全重启（比如在 Streamlit 的连续交互中）
    # Chroma 的客户端会继续连接到同一个内存数据库，并向同名集合追加数据
    # vectordb = Chroma.from_documents(splits, embeddings)

    # 每次执行先删除集合，否则多次执行会向同一个集合追加数据 造成重复
    client = chromadb.Client()
    try:
        # 这个是默认的集合名字
        client.delete_collection(Chroma._LANGCHAIN_DEFAULT_COLLECTION_NAME)  # 删除默认集合
    except Exception as e:
        print(f"删除集合出错（可能无害）: {e}")

    # 关键步骤2：创建新集合（无需指定名称，Chroma自动生成）
    vectordb = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        client=client
    )

    collection = vectordb._client.get_collection(vectordb._collection.name)
    records = collection.get()  # 获取所有数据
    print(f"向量数据库总存储数: {len(records['ids'])}")

    retriever = vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4, "fetch_k": 2}
    )
    return retriever


retriever = configure_retriever(uploaded_files)

retriever_tool = create_retriever_tool(
    retriever=retriever,
    name="知识库检索",
    description="用于检索用户提出的问题，并基于检索到的文档内容进行回复.",
)

tools = [sqlTool, barChartTool, lineChartTool, pieChartTool, retriever_tool]

# 记忆和提示词配置
msgs = StreamlitChatMessageHistory()
# chat_memory就是具体存数据的地方   不指定默认存在内存，即InMemoryChatMessageHistory里
memory = ConversationBufferMemory(
    chat_memory=msgs, memory_key="chat_history", output_key="output"
)


@st.cache_resource(ttl="1h")
def read_data_dictionary(data_uploaded_files):
    docs = []
    for file in data_uploaded_files:
        docs.append(file.getvalue().decode("utf-8"))
    return '\n'.join(docs)


data_dictionary = "数据库表信息如下：\n" + read_data_dictionary(data_uploaded_files)

instructions = """
你是一个专业的问题解决助手，具备以下核心能力：
1、数据库查询 - 直接访问结构化数据 
2、RAG检索 - 从知识库获取最新信息
3、可视化生成 - 创建数据图表(仅支持柱状图、饼图、折线图，如果生成图表请使用Markdown格式展示 如：![img](url))

工作流程：
明确用户意图，智能判断最适合的工具组合：
需要背景知识/最新信息 → RAG检索
需要精确数据 → 数据库查询
需要数据呈现 → 图表生成
必要时进行多工具协同（如：先用RAG确认概念，再查询具体数据）
如果你从文档或者数据库查询结果中找不到任何信息用于回答问题，则只需返回“抱歉，这个问题我还不知道。”作为答案。
"""

# 基础提示模板（更新以包含图表工具）
base_prompt_template = """
{instructions}

{data_dictionary}

Answer the following questions as best you can. You have access to the following tools:

{tools}

The way you use the tools is by specifying a json blob.
Specifically, this json should have a `action` key (with the name of the tool to use) and a `action_input` key (with the input to the tool going here).

The only values that should be in the "action" field are: {tool_names}

The $JSON_BLOB should only contain a SINGLE action, do NOT return a list of multiple actions. Here is an example of a valid $JSON_BLOB:

```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```

请严格按照上述格式来生成，$JSON_BLOB前后都必须用 ``` 包裹，不要忘记! important

The $JSON_BLOB should contain a SINGLE action with properly named parameters, even for single-parameter tools. Always include the parameter names explicitly. Here are examples:
For multi-parameter tools

你必须严格遵守JSON格式规范生成$JSON_BLOB。特别注意：
- 必须包含完整的闭合括号

ALWAYS use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action:
```
$JSON_BLOB
```

Observation: the result of the action
... (this Thought/Action/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin! Reminder to always use the exact characters `Final Answer` when responding.

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}


"""

base_prompt = PromptTemplate.from_template(base_prompt_template)
prompt = base_prompt.partial(instructions=instructions, data_dictionary=data_dictionary)

# 创建llm
llm = ChatOpenAI(model=os.getenv("LLM_MODEL_NAME"), openai_api_key=os.getenv("LLM_API_KEY"),openai_api_base=os.getenv("LLM_BASE_URL"))

# 创建agent
agent = create_react_agent(llm, tools, prompt, output_parser=ReActJsonSingleInputOutputParser())
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True, handle_parsing_errors=True)

# 初始化消息状态
if "messages" not in st.session_state or st.sidebar.button("清空聊天记录"):
    st.session_state["messages"] = [
        {"role": "assistant", "content": "您好，我是ChatBI智能助手，我可以查询文档，查询数据库，并为您生成图表"}]
    # 重置内存
    if 'memory' in globals():
        memory.clear()

# 加载历史聊天记录
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 用户输入处理
user_query = st.chat_input(placeholder="请开始提问吧!")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container())
        config = {"callbacks": [st_cb]}
        response = agent_executor.invoke({"input": user_query}, config=config)
        # 显示响应文本
        st.write(response["output"])
        st.session_state.messages.append({"role": "assistant", "content": response["output"]})
