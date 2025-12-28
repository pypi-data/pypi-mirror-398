# wxhelper-async 系统文档

## 核心概念

### 1. 命名空间 (name_space)

**定义**：命名空间是逻辑上具有同一分类名称的一组功能函数的集合。它通过加载其个性化"插件"返回了个性化的LLM提示词(prompt)和附加的语料信息，实现个性化的问答。

**作用**：
- **分类管理**：将不同的业务功能（如二手车、招聘、旅游等）组织到独立的命名空间中
- **个性化问答**：每个命名空间可以加载特定的插件，提供定制化的prompt和语料库
- **资源隔离**：确保不同业务类型的历史记录、配置和数据处理相互独立

**示例**：
- `car_client` - 二手车服务命名空间
- `qzzp` - 求职招聘命名空间
- `lvyou` - 旅游服务命名空间

### 2. 来源ID (source_id)

**定义**：source_id是一个先进的提议，当user_id与group_id不同时，source_id就是group_id，反之就是user_id。它实现了私聊、群聊环境的隔离。

**作用**：
- **环境隔离**：统一处理私聊和群聊场景，自动识别对话环境
- **历史记录管理**：基于source_id存储和检索历史记录，确保不同环境的记录独立
- **权限控制**：支持基于source_id的权限和访问控制

**工作逻辑**：
```
如果 (user_id ≠ group_id):
    source_id = group_id  # 群聊环境
否则:
    source_id = user_id   # 私聊环境
```

### 3. 命名空间历史记录 (name_space 命名空间历史记录)

**定义**：命名空间历史记录是打通私聊、群聊、跨bot的桥梁，记录了特定命名空间下的所有交互历史。

**作用**：
- **跨环境同步**：在私聊、群聊和不同机器人之间共享同一命名空间的历史记录
- **上下文保持**：为用户提供连续、一致的对话体验
- **公平访问**：通过公平算法确保多用户环境下的均衡记录访问

## 系统配置与公平算法

### 1. 环境变量配置 (.env)

系统通过环境变量进行灵活配置，支持不同部署环境的需求。以下为通用配置示例：

```env
# Redis连接配置（必需）
REDIS_HOST=192.168.66.24        # Redis服务器地址
REDIS_PORT=6379                # Redis端口
REDIS_DB=0                     # Redis数据库编号
REDIS_PASSWORD=                # Redis密码（如有）

# 历史记录大小约束（核心配置）
MAX_SINGLE_CHAR=9000           # 单条消息最大字符数（防止超长消息）
MAX_USER_RECORD_COUNT=50       # 每个用户/命名空间最大存储记录数
MAX_HISTORY_CONTENT_CHAR=10000 # 检索时历史记录总字符数限制
CLEAR_CYCLE=7                  # 自动清理周期（天）

# 机器人身份配置
BOT_ID=wxid_a2qwn1yzj30722     # 当前机器人微信号
DEFAULT_NAME_SPACE=聊天        # 默认命名空间名称

# 可选功能配置
ENABLE_VOICE_SERVICE=true      # 启用语音服务
ENABLE_FRIEND_CIRCLE=true      # 启用朋友圈服务
ENABLE_PLUGIN_SYSTEM=true      # 启用插件系统
```

### 2. 历史记录大小约束机制

系统采用分层约束机制，从存储层到检索层全方位控制历史记录的大小和性能：

#### 2.1 存储层约束（Redis层面）
- **FIFO队列管理**：每个用户/命名空间的历史记录使用Redis列表(LPUSH/RPOP)存储，严格遵循先进先出原则
- **最大记录数硬限制**：当列表长度达到`MAX_USER_RECORD_COUNT`时，系统自动删除最旧的记录
- **单条消息字符限制**：写入Redis前检查消息长度，超过`MAX_SINGLE_CHAR`的消息会被截断或拒绝
- **自动过期清理**：超过`CLEAR_CYCLE`天的记录会被定期清理任务自动删除

#### 2.2 检索层约束（应用层面）
- **总字符数软限制**：检索历史记录时，系统会动态计算已取记录的总字符数，确保不超过`MAX_HISTORY_CONTENT_CHAR`
- **分页检索支持**：对于大量历史记录，支持分页检索避免一次性加载过多数据
- **按需加载机制**：只有在需要显示时才从Redis加载历史记录，减少内存占用

#### 2.3 资源隔离与分配
系统将历史记录分为三类，每类有独立的资源配额：

| 记录类型 | 配置键名 | 默认配额 | 存储键格式 | 用途说明 |
|----------|----------|----------|------------|----------|
| 常规聊天记录 | `chat_history_size_set` | 20% | `chat:history:{source_id}:{name_space}` | 普通对话历史 |
| 朋友圈记录 | `friend_circle_size_set` | 30% | `friend:history:{name_space}` | 朋友圈信息流 |
| 命名空间记录 | `name_space_history_size_set` | 40% | `namespace:history:{name_space}` | 业务功能记录 |
| 系统总容量 | `all_history_size_set` | 100% (90000字符) | - | 系统历史记录总限制 |

### 3. 公平分配算法详解

#### 3.1 算法核心思想
在多用户环境下，防止少数活跃用户垄断历史记录显示，确保所有参与者都能获得相对均衡的曝光机会。算法通过"按用户分组→计算公平配额→均衡选取"的三步流程实现这一目标。

#### 3.2 算法实现流程（命名空间历史记录为例）

```python
def get_fair_history_records_name_space(name_space: str, max_records: int = 100):
    """
    公平获取命名空间历史记录 - 核心算法实现
    
    算法流程：
    1. 数据收集：从Redis获取指定命名空间的所有历史记录
    2. 用户分组：按发送者用户ID分组，形成 {用户: [(时间, 内容), ...]} 结构
    3. 时间排序：每组内按时间降序排列（最新在前）
    4. 配额计算：根据总用户数和max_records计算每个用户的理论配额
    5. 公平选取：从每个用户的最新记录中选取配额数量的记录
    6. 合并排序：所有选取的记录按时间重新排序
    7. 返回结果：返回前max_records条记录
    
    公平性保障：
    - 即使用户数 > max_records，每个用户至少获得1条记录
    - 活跃用户不会完全挤占非活跃用户的展示机会
    - 最新消息优先原则保证时效性
    """
    # 1. 从Redis获取原始数据
    redis_key = f"namespace:history:{name_space}"
    all_records = await redis.lrange(redis_key, 0, -1)  # 获取全部记录
    
    # 2. 按用户分组（解析每条记录的JSON结构）
    user_records = defaultdict(list)
    for record_json in all_records:
        record = json.loads(record_json)
        user = record.get("user")
        content = record.get("content")
        time = record.get("timestamp")
        if user and content and time:
            user_records[user].append((time, content))
    
    # 3. 每组内按时间降序排序
    for user in user_records:
        user_records[user].sort(key=lambda x: x[0], reverse=True)
    
    # 4. 计算公平配额
    total_users = len(user_records)
    if total_users == 0:
        return []
    
    # 关键公式：per_user_limit = max(1, max_records // total_users)
    per_user_limit = max(1, max_records // total_users)
    
    # 5. 公平选取
    fair_records = []
    for user, records in user_records.items():
        # 取该用户前per_user_limit条记录
        selected_count = min(per_user_limit, len(records))
        for i in range(selected_count):
            time, content = records[i]
            fair_records.append({
                "user": user,
                "content": content,
                "timestamp": time,
                "source": "fair_algorithm"
            })
    
    # 6. 按时间重新排序（跨用户合并）
    fair_records.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # 7. 返回限定数量的结果
    return fair_records[:max_records]
```

#### 3.3 算法数学原理
设：
- N = 总用户数
- M = 最大返回记录数（max_records）
- Q = 每个用户的配额

则算法公式为：
```
Q = max(1, M ÷ N)  当 N ≤ M 时
Q = 1              当 N > M 时
```

**特性分析**：
- 当用户数较少时（N ≤ M）：每个用户可获得 M/N 条记录，充分利用展示空间
- 当用户数较多时（N > M）：每个用户至少获得1条记录，保证基本可见性
- 配额向下取整：确保总记录数不超过M，防止溢出

#### 3.4 算法优势与特点
1. **绝对公平性**：无论用户活跃度如何，算法保障每个用户都有基本的记录展示机会
2. **动态适应性**：根据实际用户数量动态调整配额，适应不同规模的群组
3. **时效性优先**：每组内优先选择最新记录，保证信息的及时性
4. **性能高效**：基于Redis的批量操作，时间复杂度为O(N)，适合大规模场景
5. **可配置性**：通过max_records参数灵活控制返回记录数量

#### 3.5 应用场景与效果
| 场景类型 | 用户规模 | 算法效果 | 实际应用 |
|----------|----------|----------|----------|
| 小型群聊 | 5-10人 | 每个用户获得10-20条记录，展示充分 | 家庭群、工作小组 |
| 中型社群 | 20-50人 | 每个用户获得2-5条记录，均衡展示 | 兴趣社群、班级群 |
| 大型社区 | 100+人 | 每个用户至少1条记录，防止刷屏 | 公开群组、社区论坛 |
| 朋友圈 | 动态变化 | 不同用户的内容均衡曝光 | 信息流展示 |

#### 3.6 扩展变体算法
系统还实现了以下公平算法变体，适应不同场景：
- **加权公平算法**：为VIP用户分配更高配额（基于用户等级）
- **时间衰减算法**：较旧的记录权重降低，突出近期内容
- **内容质量算法**：基于点赞/评论数调整展示优先级

#### 3.7 配置建议
```python
# 根据业务场景调整的参数建议
配置场景 = {
    "小型私密群组": {
        "max_records": 50,      # 返回较多记录
        "per_user_min": 5       # 每个用户最少5条
    },
    "中型兴趣社群": {
        "max_records": 30,      # 适中记录数
        "per_user_min": 2       # 每个用户最少2条
    },
    "大型公开群组": {
        "max_records": 20,      # 较少记录数
        "per_user_min": 1       # 保证基本可见性
    }
}
```

### 4. 数据库层面的公平保障

#### 4.1 表级记录限制
在数据库层面，系统通过触发器实现额外的公平保障：

```sql
-- 以history_now表为例的公平限制触发器
CREATE TRIGGER tr_history_now_fair_limit
AFTER INSERT ON history_now
FOR EACH ROW
BEGIN
    -- 每个用户最多保留10条最新记录
    DELETE FROM history_now 
    WHERE user_id = NEW.user_id 
    AND id NOT IN (
        SELECT id FROM history_now 
        WHERE user_id = NEW.user_id 
        ORDER BY create_time DESC 
        LIMIT 10
    );
END;
```

#### 4.2 定时清理任务
通过SQL Server代理任务，每天自动清理过期记录：
- 清理1个月前的所有历史记录
- 按用户均衡保留近期记录
- 防止数据库过度膨胀

#### 4.3 防崩溃机制
为防止清理时程序崩溃，系统采用缓存机制：
1. 收到请求时原始JSON存入cache表
2. 处理完成后更新what_json_base64字段
3. 回复完成后删除缓存记录
4. 程序重启时自动处理未完成请求

### 5. 算法性能与可扩展性

#### 5.1 性能指标
- **时间复杂度**：O(N + UlogR)，其中N为总记录数，U为用户数，R为单用户记录数
- **空间复杂度**：O(N)，主要消耗在内存中的分组数据结构
- **Redis操作**：1次LRANGE + U次内存排序，网络开销小

#### 5.2 扩展方向
1. **多维度公平**：结合用户活跃度、内容质量、时间衰减等多因素
2. **个性化配额**：根据用户角色（管理员/VIP/普通成员）差异化配额
3. **动态权重**：基于实时反馈（点赞、转发）动态调整展示优先级
4. **AI优化**：使用机器学习预测用户偏好，优化公平与个性化的平衡

## 系统架构优势

### 1. 灵活的插件系统
- 支持动态加载命名空间插件
- 每个插件可提供定制化的LLM prompt和语料库
- 插件间相互隔离，互不影响

### 2. 智能的环境识别
- 自动识别私聊和群聊环境
- 统一的历史记录管理接口
- 支持跨bot的数据同步

### 3. 高效的历史记录管理
- 多层次的大小约束机制
- 公平的资源分配算法
- 自动的清理和维护机制

### 4. 可扩展的架构设计
- 支持新的命名空间和插件扩展
- 可配置的资源分配策略
- 适应不同规模和类型的应用场景

## 【系统更新】
### 2025-3-17
#### 清理数据表，减小表过大
- 在表触发器中，每个用保留在数据表（history_now、friend、name_space_history）中的记录只有10条，超出则删除最早的记录，防止用户重复发消息，更为公平。
- 在SQLSERVER代理自动任务中，每天定清理数据表（history_now、friend、name_space_history），凡是1个月之前的记录全部删除
#### 防止在清理数据库记录时，收到请求程序崩溃
- 在tcp_server.py中收到请求时，将原始JSON存入数据表cache
- 在格式化json后更新该记录的what_json_base64字段
- 在text.py中回复完毕即删除该条记录
- 在always_run.py中加载cache.py，确保每次程序自动重启时处理未回复消息
#### 增加推理模型为deepseek
### 2024-05-30
- 优化了prompt
- 更换了模型推理方式
- 固定了输出格式
### 2024-06-30
- 在fun.py中增加了检查消息中是否存在手机号的函数。
- 所有消息中如未包含有效手机号，将不会写入分类命名空间和朋友圈数据。
- 每个AI使用分类 = 系统预置分类 + 自己的自定义的分类
- 在朋友圈服务分类中如果没有分类，则自行增加，并发送通知给AI主人
- 增加删除分类命令，使用方式：/删除分类|<分类名称>
### 2024-08-28
- 在mssql_helper.py第533行增加了取消投放暗号功能

## 怎样使用

### 1. 安装微信特定版本
1. 安装最新版微信，使用专门手机、手机卡，在该手机专门登录手机微信、专门的电脑（可以是虚拟机，推荐Win10），一直登录到在手机确认上出现“自动登录该设备”
2. 卸载最新版微信，保留登录信息
3. 安装程序微信3.9.2.23版本，登录，在“通用设置”中去掉“有更新时自动升级微信”的勾选

### 2. Hook注入
运行程序目录中的“微信DLL注入器V1.0.3.exe”，它会自动加载程序目录中的“wxhelper-3.9.2.23-v9.dll”文件，点击“注入DLL”

### 3. 安装Miniconda
下载并安装Miniconda（推荐Python 3.12版本）

### 4. 创建虚拟环境
```bash
conda create -n wxhelper python=3.12
conda activate wxhelper
```

### 5. 安装Python依赖
在虚拟环境中执行：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 6. 运行程序
按顺序运行以下批处理文件：
1. `启动主程序.bat`
2. `启动朋友圈服务.bat`
3. `启动接口服务.bat`

## 通用公平算法类（FairHistoryManager）

系统核心的公平算法已抽象为独立的Python类 `FairHistoryManager`，可用于任何LLM聊天应用，支持Redis存储。

### 安装
```bash
pip install fair-history-manager
```

### 基本使用
```python
from fair_history_manager import FairHistoryManager
import redis

# 初始化Redis连接
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 创建公平历史管理器
history_manager = FairHistoryManager(
    redis_client=redis_client,
    namespace="chat_history",
    max_records_per_user=50,
    max_single_char=9000,
    max_total_chars=10000
)

# 添加历史记录
await history_manager.add_record(
    user_id="user123",
    content="Hello, how are you?",
    timestamp=1690200000
)

# 公平获取历史记录
fair_records = await history_manager.get_fair_records(max_records=100)
```

### 高级功能
```python
# 1. 加权公平算法（VIP用户更高配额）
weighted_manager = FairHistoryManager(
    redis_client=redis_client,
    namespace="vip_chat",
    user_weights={"vip_user": 3, "normal_user": 1}  # VIP用户3倍配额
)

# 2. 时间衰减算法
from fair_history_manager import TimeDecayFairAlgorithm
decay_manager = FairHistoryManager(
    redis_client=redis_client,
    algorithm=TimeDecayFairAlgorithm(decay_rate=0.1)  # 每天衰减10%
)

# 3. 多命名空间管理
multi_manager = FairHistoryManager(
    redis_client=redis_client,
    namespace="multi_env",
    sub_namespaces=["group_chat", "private_chat", "customer_service"]
)

# 4. 自定义存储格式
class CustomRecord:
    def __init__(self, user, message, metadata):
        self.user = user
        self.message = message
        self.metadata = metadata

custom_manager = FairHistoryManager(
    redis_client=redis_client,
    record_class=CustomRecord,
    serialize_func=lambda r: json.dumps(r.__dict__),
    deserialize_func=lambda s: CustomRecord(**json.loads(s))
)
```

### 配置选项
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `redis_client` | Redis | 必填 | Redis连接实例 |
| `namespace` | str | "default" | 命名空间前缀 |
| `max_records_per_user` | int | 50 | 每个用户最大记录数 |
| `max_single_char` | int | 9000 | 单条消息最大字符数 |
| `max_total_chars` | int | 10000 | 检索总字符数限制 |
| `cleanup_days` | int | 7 | 自动清理天数 |
| `algorithm` | FairAlgorithm | BasicFairAlgorithm | 公平算法实现 |
| `user_weights` | dict | {} | 用户权重映射 |

### 支持的算法
1. **BasicFairAlgorithm**：基础公平算法，每个用户均衡配额
2. **WeightedFairAlgorithm**：加权公平，支持用户权重
3. **TimeDecayFairAlgorithm**：时间衰减，旧记录权重降低
4. **QualityBasedAlgorithm**：基于内容质量（点赞/评论）的算法
5. **HybridAlgorithm**：混合多种因素的算法

### 性能特性
- **时间复杂度**：O(N + UlogR)，N为总记录数，U为用户数，R为用户记录数
- **空间复杂度**：O(N)，主要使用Redis存储
- **并发安全**：支持异步操作，线程安全
- **可扩展性**：易于添加新算法和存储后端

### 发布信息
该包已发布到PyPi，可通过以下方式安装使用：
```bash
pip install fair-history-manager
```

源码仓库：https://github.com/your-username/fair-history-manager

文档：https://fair-history-manager.readthedocs.io/

### 贡献指南
欢迎贡献代码、报告问题或提出改进建议。请遵循项目代码规范和测试标准。

### 许可证
MIT License

## 与LLM框架集成示例

### 1. 与LangChain集成
```python
from langchain.memory import ChatMessageHistory
from langchain.schema import HumanMessage, AIMessage
from fair_history_manager import FairHistoryManager
import redis.asyncio as aioredis

class FairAllocationChatMessageHistory(ChatMessageHistory):
    """使用公平算法的LangChain聊天历史"""
    
    def __init__(self, redis_url="redis://localhost:6379", namespace="langchain_chat"):
        self.redis_client = aioredis.from_url(redis_url)
        self.fair_manager = FairHistoryManager(
            redis_client=self.redis_client,
            namespace=namespace,
            max_records_per_user=100
        )
    
    async def add_user_message(self, message: str, user_id: str = "default_user"):
        """添加用户消息"""
        await self.fair_manager.add_record(
            user_id=user_id,
            content=message,
            metadata={"type": "human"}
        )
    
    async def add_ai_message(self, message: str, user_id: str = "default_user"):
        """添加AI回复"""
        await self.fair_manager.add_record(
            user_id=user_id,
            content=message,
            metadata={"type": "ai"}
        )
    
    async def get_fair_messages(self, max_records: int = 20):
        """获取公平分配的历史消息"""
        records = await self.fair_manager.get_fair_records(max_records=max_records)
        
        messages = []
        for record in records:
            if record.get("metadata", {}).get("type") == "human":
                messages.append(HumanMessage(content=record["content"]))
            else:
                messages.append(AIMessage(content=record["content"]))
        
        return messages
    
    async def clear(self):
        """清空历史"""
        await self.fair_manager.delete_namespace("chat")
```

### 2. 与FastAPI集成（Web API）
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fair_history_manager import FairHistoryManager
import redis.asyncio as aioredis

app = FastAPI()

# 初始化公平历史管理器
redis_client = aioredis.from_url("redis://localhost:6379")
fair_manager = FairHistoryManager(
    redis_client=redis_client,
    namespace="api_chat"
)

class ChatMessage(BaseModel):
    user_id: str
    content: str

@app.post("/chat")
async def add_chat_message(message: ChatMessage):
    """添加聊天消息"""
    success = await fair_manager.add_record(
        user_id=message.user_id,
        content=message.content
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add message")
    return {"status": "success", "message": "Message added"}

@app.get("/chat/fair")
async def get_fair_chat_history(max_records: int = 50):
    """获取公平分配的历史记录"""
    records = await fair_manager.get_fair_records(max_records=max_records)
    return {"status": "success", "records": records}

@app.get("/chat/statistics")
async def get_chat_statistics():
    """获取聊天统计信息"""
    stats = await fair_manager.get_statistics()
    return {"status": "success", "statistics": stats}
```

### 3. 与Discord/Telegram机器人集成
```python
import discord
from discord.ext import commands
from fair_history_manager import FairHistoryManager
import redis.asyncio as aioredis

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 初始化公平历史管理器
redis_client = aioredis.from_url("redis://localhost:6379")
fair_manager = FairHistoryManager(
    redis_client=redis_client,
    namespace="discord_bot"
)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    # 忽略机器人自己的消息
    if message.author == bot.user:
        return
    
    # 保存用户消息
    await fair_manager.add_record(
        user_id=str(message.author.id),
        content=message.content,
        metadata={
            "channel_id": str(message.channel.id),
            "guild_id": str(message.guild.id) if message.guild else None
        }
    )
    
    # 处理命令
    await bot.process_commands(message)

@bot.command(name="history")
async def get_fair_history(ctx, limit: int = 20):
    """获取公平分配的历史记录"""
    records = await fair_manager.get_fair_records(max_records=limit)
    
    if not records:
        await ctx.send("No history records found.")
        return
    
    response = "**Fair Chat History:**\n"
    for i, record in enumerate(records[:10], 1):
        response += f"{i}. User {record['user_id'][:8]}...: {record['content'][:50]}...\n"
    
    await ctx.send(response)

# 运行机器人
bot.run("YOUR_DISCORD_TOKEN")
```

## Windows兼容性说明

### 1. 命令语法
在Windows PowerShell中，推荐使用以下命令语法：

```powershell
# 创建虚拟环境（PowerShell）
conda create -n wxhelper python=3.12
conda activate wxhelper

# 安装依赖（PowerShell）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 运行测试（PowerShell）
cd fair_history_manager
python test_basic.py

# 或者使用单行命令（PowerShell 7+）
cd fair_history_manager; python test_basic.py
```

### 2. Redis安装与配置（Windows）
```powershell
# 方法1：使用Windows Subsystem for Linux (WSL)
wsl --install
wsl
sudo apt update
sudo apt install redis-server
sudo service redis-server start

# 方法2：使用Windows原生Redis
# 1. 下载Redis for Windows: https://github.com/microsoftarchive/redis/releases
# 2. 解压并运行redis-server.exe
# 3. 或在PowerShell中运行：
Invoke-WebRequest -Uri "https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.msi" -OutFile "redis.msi"
msiexec /i redis.msi /quiet
```

### 3. 批处理文件示例
创建`start_fair_manager.bat`：
```batch
@echo off
echo Starting Fair History Manager...
cd /d "%~dp0"
python -c "from fair_history_manager import FairHistoryManager; import redis.asyncio as aioredis; print('FairHistoryManager imported successfully')"
pause
```

## 故障排除

### 常见问题
1. **Redis连接失败**
   - 检查Redis服务是否运行：`redis-cli ping`
   - Windows: 在服务管理器中查看"Redis"服务状态

2. **异步函数调用错误**
   - 确保使用`asyncio.run()`或在异步上下文中调用
   - 示例：
     ```python
     import asyncio
     
     async def main():
         # 你的代码
         pass
     
     if __name__ == "__main__":
         asyncio.run(main())
     ```

3. **依赖安装失败**
   - 使用国内镜像源：`-i https://pypi.tuna.tsinghua.edu.cn/simple`
   - 或使用阿里云镜像：`-i https://mirrors.aliyun.com/pypi/simple/`

4. **Windows路径问题**
   - 使用原始字符串或双反斜杠：`r"C:\path\to\file"` 或 `"C:\\path\\to\\file"`
   - 避免使用Linux风格的路径：`/path/to/file`

### 性能优化建议
1. **Redis配置**
   ```conf
   # redis.conf
   maxmemory 100mb
   maxmemory-policy allkeys-lru
   save 900 1
   save 300 10
   save 60 10000
   ```

2. **批量操作**
   ```python
   # 批量添加记录
   async def add_batch_records(records):
       pipeline = redis_client.pipeline()
       for record in records:
           pipeline.lpush("key", json.dumps(record))
       await pipeline.execute()
   ```

3. **内存管理**
   - 设置合理的`max_records_per_user`（默认50）
   - 定期清理旧记录：`await manager.clear_old_records(days=7)`
   - 监控Redis内存使用：`redis-cli info memory`

## 更新日志

### v1.0.0 (2024-12-24)
- 初始版本发布
- 支持5种公平分配算法
- 完整的异步Redis支持
- Windows/Linux/macOS跨平台兼容
- 详细的文档和示例

### 未来计划
- 支持更多存储后端（SQLite, PostgreSQL, MongoDB）
- 实时公平性调整算法
- 机器学习优化的配额分配
- 图形化管理界面
- 更多LLM框架集成
