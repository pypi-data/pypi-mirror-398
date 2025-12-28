"""
FastAPI + SQLModel + aiosqlite + Casbin ACL 示例应用

这个示例展示了如何使用 fastapi-casbin-acl 构建一个带有权限控制的 Web 应用。
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_casbin_acl.enforcer import acl
from fastapi_casbin_acl.config import ACLConfig
from fastapi_casbin_acl.adapter import SQLModelAdapter
from fastapi_casbin_acl.exceptions import Unauthorized, Forbidden

try:
    # 作为模块导入时使用相对导入
    from .database import init_db, close_db, AsyncSessionLocal
    from .routes import router
except ImportError:
    # 直接运行时使用绝对导入
    from database import init_db, close_db, AsyncSessionLocal
    from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时初始化
    # 1. 初始化数据库
    await init_db()

    # 2. 初始化 Casbin ACL
    # 使用 SQLModelAdapter 连接数据库
    adapter = SQLModelAdapter(AsyncSessionLocal)
    # 使用 ABAC 模型，owner 提取通过 owner_getter 或模型的 get_owner_sub 方法
    config = ACLConfig(default_model="abac")
    await acl.init(adapter=adapter, config=config)

    # 3. 初始化示例用户数据
    await init_users()

    # 4. 初始化权限策略（示例数据）
    await init_policies()

    yield

    # 关闭时清理
    await close_db()


# 创建 FastAPI 应用
app = FastAPI(
    title="FastAPI Casbin ACL 示例",
    description="一个使用 FastAPI、SQLModel、aiosqlite 和 Casbin ACL 的完整示例",
    version="1.0.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(router, prefix="/api")


# ==================== 用户数据初始化 ====================


async def init_users():
    """
    初始化示例用户数据
    """
    try:
        from examples.models import User
        from examples.database import AsyncSessionLocal
    except ImportError:
        from models import User
        from database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # 检查用户是否已存在
        from sqlmodel import select as sqlmodel_select

        users_to_create = [
            {"username": "alice", "email": "alice@example.com"},
            {"username": "bob", "email": "bob@example.com"},
            {"username": "charlie", "email": "charlie@example.com"},
        ]

        for user_data in users_to_create:
            statement = sqlmodel_select(User).where(
                User.username == user_data["username"]
            )
            result = await session.execute(statement)
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                user = User(**user_data)
                session.add(user)

        await session.commit()
        print("✅ 示例用户初始化完成")


# ==================== 权限策略初始化 ====================


async def init_policies():
    """
    初始化权限策略
    在实际应用中，这些策略应该从配置文件或管理界面加载

    注意：策略中使用用户 ID（字符串）而非 username，原因如下：
    1. get_subject_from_user 返回的是 str(user.id)（字符串）
    2. 为了在 ABAC 权限检查时正确匹配，owner 也必须返回用户 ID
    3. 因此策略中的 subject 和 owner 都使用用户 ID 格式（字符串）
    """
    try:
        from examples.models import User
        from examples.database import AsyncSessionLocal
    except ImportError:
        from models import User
        from database import AsyncSessionLocal

    # 获取 ABAC 模型的 enforcer
    enforcer = acl.get_enforcer("abac")

    # 首先查询用户获取 ID
    async with AsyncSessionLocal() as session:
        from sqlmodel import select as sqlmodel_select

        # 查询用户并获取 ID
        alice_stmt = sqlmodel_select(User).where(User.username == "alice")
        bob_stmt = sqlmodel_select(User).where(User.username == "bob")
        charlie_stmt = sqlmodel_select(User).where(User.username == "charlie")

        alice_result = await session.execute(alice_stmt)
        bob_result = await session.execute(bob_stmt)
        charlie_result = await session.execute(charlie_stmt)

        alice = alice_result.scalar_one_or_none()
        bob = bob_result.scalar_one_or_none()
        charlie = charlie_result.scalar_one_or_none()

        if not alice or not bob or not charlie:
            print("⚠️  警告：部分用户未找到，请先运行 init_users()")
            return

        # 定义角色（使用用户 ID）
        # g, 1, admin  -> 用户 ID 1 是 admin 角色
        # g, 2, user   -> 用户 ID 2 是 user 角色
        await enforcer.add_grouping_policy(str(alice.id), "admin")
        await enforcer.add_grouping_policy(str(bob.id), "user")
        await enforcer.add_grouping_policy(str(charlie.id), "user")

    # 定义策略（RBAC）
    # 注意：使用通配符 /* 来匹配带路径参数的路由
    # 例如：/api/orders/* 可以匹配 /api/orders 和 /api/orders/{id}
    # p, admin, /api/users, read    -> admin 可以读取用户
    # p, admin, /api/users, write   -> admin 可以创建/更新用户
    # p, admin, /api/orders/*, read   -> admin 可以读取订单（包括列表和详情）
    # p, admin, /api/orders/*, write  -> admin 可以创建/更新订单
    # p, admin, /api/orders/*, delete -> admin 可以删除订单
    # p, user, /api/orders/*, read    -> user 可以读取订单（包括列表和详情）
    # p, user, /api/orders/*, write    -> user 可以创建/更新订单
    # p, user, /api/orders/*, delete  -> user 可以删除订单
    await enforcer.add_policy("admin", "/api/users/*", "read")
    await enforcer.add_policy("admin", "/api/users/*", "write")
    # 使用通配符匹配所有 /api/orders 下的路径（包括 /api/orders 和 /api/orders/{id}）
    await enforcer.add_policy("admin", "/api/orders/*", "read")
    await enforcer.add_policy("admin", "/api/orders/*", "write")
    await enforcer.add_policy("admin", "/api/orders/*", "delete")
    await enforcer.add_policy("user", "/api/orders/*", "read")
    await enforcer.add_policy("user", "/api/orders/*", "write")
    await enforcer.add_policy("user", "/api/orders/*", "delete")

    # 保存策略到数据库
    await acl.save_policy()

    print("✅ 权限策略初始化完成")
    print(f"   - 用户 ID {alice.id} ({alice.username}, admin): 可以访问所有用户和订单")
    print(f"   - 用户 ID {bob.id} ({bob.username}, user): 只能访问自己的订单")
    print(f"   - 用户 ID {charlie.id} ({charlie.username}, user): 只能访问自己的订单")


# ==================== 异常处理 ====================


@app.exception_handler(Unauthorized)
async def unauthorized_handler(request: Request, exc: Unauthorized):
    """
    处理未授权异常
    """
    return JSONResponse(
        status_code=401,
        content={"message": "未授权：请提供有效的用户 ID (X-User-ID 请求头)"},
    )


@app.exception_handler(Forbidden)
async def forbidden_handler(request: Request, exc: Forbidden):
    """
    处理禁止访问异常
    """
    return JSONResponse(
        status_code=403, content={"message": "禁止访问：您没有执行此操作的权限"}
    )


# ==================== 前端页面 ====================


@app.get("/", response_class=HTMLResponse)
async def index():
    """
    返回前端 HTML 页面
    """
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FastAPI Casbin ACL 示例</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            line-height: 1.6;
        }
        
        .user-selector {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        .user-selector label {
            display: block;
            margin-bottom: 10px;
            font-weight: bold;
            color: #333;
        }
        
        .user-selector select {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .section h2 {
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
        }
        
        .btn-success {
            background: #48bb78;
            color: white;
        }
        
        .btn-success:hover {
            background: #38a169;
        }
        
        .btn-danger {
            background: #f56565;
            color: white;
        }
        
        .btn-danger:hover {
            background: #e53e3e;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 80px;
        }
        
        .result {
            margin-top: 20px;
            padding: 15px;
            background: #f7fafc;
            border-radius: 5px;
            border-left: 4px solid #667eea;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .result pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 12px;
            color: #333;
        }
        
        .error {
            border-left-color: #f56565;
            background: #fed7d7;
        }
        
        .success {
            border-left-color: #48bb78;
            background: #c6f6d5;
        }
        
        @media (max-width: 768px) {
            .content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 FastAPI Casbin ACL 示例</h1>
            <p>这是一个完整的示例应用，展示了如何使用 FastAPI、SQLModel、aiosqlite 和 Casbin ACL 构建带权限控制的 Web 应用。</p>
            <p><strong>提示：</strong>切换用户查看不同的权限效果。用户 ID 1 通常是管理员，其他用户是普通用户。权限策略使用用户 ID 进行匹配。</p>
        </div>
        
        <div class="user-selector">
            <label for="userId">当前用户 ID：</label>
            <select id="userId" onchange="updateUserId()">
                <option value="">请选择用户...</option>
            </select>
            <p style="margin-top: 10px; font-size: 12px; color: #666;">
                提示：用户 ID 在用户创建后自动分配。首次使用请先创建用户或等待初始化完成。
            </p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>👥 用户管理</h2>
                <div class="button-group">
                    <button class="btn-primary" onclick="listUsers()">获取用户列表</button>
                    <button class="btn-primary" onclick="showGetUserForm()">获取用户详情</button>
                    <button class="btn-success" onclick="showCreateUserForm()">创建用户</button>
                </div>
                <div id="getUserForm" style="display: none;">
                    <div class="form-group">
                        <label>用户 ID：</label>
                        <input type="number" id="getUserId" placeholder="输入用户 ID">
                    </div>
                    <button class="btn-primary" onclick="getUser()">查询</button>
                    <button onclick="hideGetUserForm()">取消</button>
                </div>
                <div id="createUserForm" style="display: none;">
                    <div class="form-group">
                        <label>用户名：</label>
                        <input type="text" id="newUsername" placeholder="输入用户名">
                    </div>
                    <div class="form-group">
                        <label>邮箱：</label>
                        <input type="email" id="newEmail" placeholder="输入邮箱">
                    </div>
                    <button class="btn-success" onclick="createUser()">创建</button>
                    <button onclick="hideCreateUserForm()">取消</button>
                </div>
                <div id="usersResult" class="result" style="display: none;"></div>
            </div>
            
            <div class="section">
                <h2>📦 订单管理</h2>
                <div class="button-group">
                    <button class="btn-primary" onclick="listOrders()">获取订单列表</button>
                    <button class="btn-primary" onclick="showGetOrderForm()">获取订单详情 (ABAC)</button>
                    <button class="btn-success" onclick="showCreateOrderForm()">创建订单</button>
                    <button class="btn-success" onclick="showUpdateOrderForm()">更新订单 (ABAC)</button>
                    <button class="btn-danger" onclick="showDeleteOrderForm()">删除订单 (ABAC)</button>
                </div>
                <div id="getOrderForm" style="display: none;">
                    <div class="form-group">
                        <label>订单 ID：</label>
                        <input type="number" id="getOrderId" placeholder="输入订单 ID">
                    </div>
                    <button class="btn-primary" onclick="getOrder()">查询</button>
                    <button onclick="hideGetOrderForm()">取消</button>
                </div>
                <div id="createOrderForm" style="display: none;">
                    <div class="form-group">
                        <label>订单标题：</label>
                        <input type="text" id="orderTitle" placeholder="输入订单标题">
                    </div>
                    <div class="form-group">
                        <label>描述：</label>
                        <textarea id="orderDesc" placeholder="输入订单描述"></textarea>
                    </div>
                    <div class="form-group">
                        <label>金额：</label>
                        <input type="number" id="orderAmount" placeholder="输入金额" step="0.01">
                    </div>
                    <button class="btn-success" onclick="createOrder()">创建</button>
                    <button onclick="hideCreateOrderForm()">取消</button>
                </div>
                <div id="updateOrderForm" style="display: none;">
                    <div class="form-group">
                        <label>订单 ID：</label>
                        <input type="number" id="updateOrderId" placeholder="输入订单 ID">
                    </div>
                    <div class="form-group">
                        <label>订单标题：</label>
                        <input type="text" id="updateOrderTitle" placeholder="输入新标题（可选）">
                    </div>
                    <div class="form-group">
                        <label>描述：</label>
                        <textarea id="updateOrderDesc" placeholder="输入新描述（可选）"></textarea>
                    </div>
                    <div class="form-group">
                        <label>金额：</label>
                        <input type="number" id="updateOrderAmount" placeholder="输入新金额（可选）" step="0.01">
                    </div>
                    <div class="form-group">
                        <label>状态：</label>
                        <select id="updateOrderStatus">
                            <option value="">不修改</option>
                            <option value="pending">pending</option>
                            <option value="completed">completed</option>
                            <option value="cancelled">cancelled</option>
                        </select>
                    </div>
                    <button class="btn-success" onclick="updateOrder()">更新</button>
                    <button onclick="hideUpdateOrderForm()">取消</button>
                </div>
                <div id="deleteOrderForm" style="display: none;">
                    <div class="form-group">
                        <label>订单 ID：</label>
                        <input type="number" id="deleteOrderId" placeholder="输入订单 ID">
                    </div>
                    <button class="btn-danger" onclick="deleteOrder()">删除</button>
                    <button onclick="hideDeleteOrderForm()">取消</button>
                </div>
                <div id="ordersResult" class="result" style="display: none;"></div>
            </div>
        </div>
    </div>
    
    <script>
        let currentUserId = '';
        
        // 页面加载时获取用户列表并填充选择器
        async function loadUsers() {
            try {
                // 使用一个临时用户来获取用户列表（这里简化处理，实际应该有一个公开的接口）
                // 或者我们可以硬编码初始用户 ID（1, 2, 3）
                // 为了演示，我们先尝试获取用户列表
                const response = await fetch('/api/users', {
                    headers: {
                        'X-User-ID': '1',  // 使用管理员 ID 获取列表
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const users = await response.json();
                    const select = document.getElementById('userId');
                    select.innerHTML = '<option value="">请选择用户...</option>';
                    
                    users.forEach(user => {
                        const option = document.createElement('option');
                        option.value = user.id.toString();
                        option.textContent = `${user.username} (ID: ${user.id})${user.id === 1 ? ' - 管理员' : ' - 普通用户'}`;
                        select.appendChild(option);
                    });
                    
                    // 默认选择第一个用户
                    if (users.length > 0) {
                        select.value = users[0].id.toString();
                        currentUserId = users[0].id.toString();
                    }
                } else {
                    // 如果获取失败，使用硬编码的初始用户 ID
                    const select = document.getElementById('userId');
                    select.innerHTML = `
                        <option value="">请选择用户...</option>
                        <option value="1">Alice (ID: 1) - 管理员</option>
                        <option value="2">Bob (ID: 2) - 普通用户</option>
                        <option value="3">Charlie (ID: 3) - 普通用户</option>
                    `;
                }
            } catch (error) {
                // 如果出错，使用硬编码的初始用户 ID
                const select = document.getElementById('userId');
                select.innerHTML = `
                    <option value="">请选择用户...</option>
                    <option value="1">Alice (ID: 1) - 管理员</option>
                    <option value="2">Bob (ID: 2) - 普通用户</option>
                    <option value="3">Charlie (ID: 3) - 普通用户</option>
                `;
            }
        }
        
        function updateUserId() {
            currentUserId = document.getElementById('userId').value;
            console.log('当前用户 ID:', currentUserId);
        }
        
        // 页面加载时初始化
        window.addEventListener('DOMContentLoaded', () => {
            loadUsers();
        });
        
        function getHeaders() {
            return {
                'X-User-ID': currentUserId,
                'Content-Type': 'application/json'
            };
        }
        
        function showResult(elementId, data, isError = false) {
            const element = document.getElementById(elementId);
            element.style.display = 'block';
            element.className = 'result ' + (isError ? 'error' : 'success');
            element.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }
        
        // 用户管理
        async function listUsers() {
            try {
                const response = await fetch('/api/users', {
                    headers: getHeaders()
                });
                const data = await response.json();
                if (response.ok) {
                    showResult('usersResult', data);
                } else {
                    showResult('usersResult', data, true);
                }
            } catch (error) {
                showResult('usersResult', {error: error.message}, true);
            }
        }
        
        function showGetUserForm() {
            document.getElementById('getUserForm').style.display = 'block';
            document.getElementById('createUserForm').style.display = 'none';
        }
        
        function hideGetUserForm() {
            document.getElementById('getUserForm').style.display = 'none';
        }
        
        async function getUser() {
            const userId = document.getElementById('getUserId').value;
            
            if (!userId) {
                alert('请输入用户 ID');
                return;
            }
            
            try {
                const response = await fetch(`/api/users/${userId}`, {
                    headers: getHeaders()
                });
                const data = await response.json();
                if (response.ok) {
                    showResult('usersResult', data);
                    hideGetUserForm();
                    document.getElementById('getUserId').value = '';
                } else {
                    showResult('usersResult', data, true);
                }
            } catch (error) {
                showResult('usersResult', {error: error.message}, true);
            }
        }
        
        function showCreateUserForm() {
            document.getElementById('createUserForm').style.display = 'block';
            document.getElementById('getUserForm').style.display = 'none';
        }
        
        function hideCreateUserForm() {
            document.getElementById('createUserForm').style.display = 'none';
        }
        
        async function createUser() {
            const username = document.getElementById('newUsername').value;
            const email = document.getElementById('newEmail').value;
            
            if (!username || !email) {
                alert('请填写所有字段');
                return;
            }
            
            try {
                const response = await fetch('/api/users', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({username, email})
                });
                const data = await response.json();
                if (response.ok) {
                    showResult('usersResult', data);
                    hideCreateUserForm();
                    document.getElementById('newUsername').value = '';
                    document.getElementById('newEmail').value = '';
                } else {
                    showResult('usersResult', data, true);
                }
            } catch (error) {
                showResult('usersResult', {error: error.message}, true);
            }
        }
        
        // 订单管理
        async function listOrders() {
            try {
                const response = await fetch('/api/orders', {
                    headers: getHeaders()
                });
                const data = await response.json();
                if (response.ok) {
                    showResult('ordersResult', data);
                } else {
                    showResult('ordersResult', data, true);
                }
            } catch (error) {
                showResult('ordersResult', {error: error.message}, true);
            }
        }
        
        function showGetOrderForm() {
            document.getElementById('getOrderForm').style.display = 'block';
            document.getElementById('createOrderForm').style.display = 'none';
            document.getElementById('updateOrderForm').style.display = 'none';
            document.getElementById('deleteOrderForm').style.display = 'none';
        }
        
        function hideGetOrderForm() {
            document.getElementById('getOrderForm').style.display = 'none';
        }
        
        async function getOrder() {
            const orderId = document.getElementById('getOrderId').value;
            
            if (!orderId) {
                alert('请输入订单 ID');
                return;
            }
            
            try {
                const response = await fetch(`/api/orders/${orderId}`, {
                    headers: getHeaders()
                });
                const data = await response.json();
                if (response.ok) {
                    showResult('ordersResult', data);
                    hideGetOrderForm();
                    document.getElementById('getOrderId').value = '';
                } else {
                    showResult('ordersResult', data, true);
                }
            } catch (error) {
                showResult('ordersResult', {error: error.message}, true);
            }
        }
        
        function showCreateOrderForm() {
            document.getElementById('createOrderForm').style.display = 'block';
            document.getElementById('getOrderForm').style.display = 'none';
            document.getElementById('updateOrderForm').style.display = 'none';
            document.getElementById('deleteOrderForm').style.display = 'none';
        }
        
        function hideCreateOrderForm() {
            document.getElementById('createOrderForm').style.display = 'none';
        }
        
        async function createOrder() {
            const title = document.getElementById('orderTitle').value;
            const description = document.getElementById('orderDesc').value;
            const amount = parseFloat(document.getElementById('orderAmount').value);
            
            if (!title || !amount) {
                alert('请填写标题和金额');
                return;
            }
            
            try {
                const response = await fetch('/api/orders', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({title, description, amount})
                });
                const data = await response.json();
                if (response.ok) {
                    showResult('ordersResult', data);
                    hideCreateOrderForm();
                    document.getElementById('orderTitle').value = '';
                    document.getElementById('orderDesc').value = '';
                    document.getElementById('orderAmount').value = '';
                } else {
                    showResult('ordersResult', data, true);
                }
            } catch (error) {
                showResult('ordersResult', {error: error.message}, true);
            }
        }
        
        function showUpdateOrderForm() {
            document.getElementById('updateOrderForm').style.display = 'block';
            document.getElementById('getOrderForm').style.display = 'none';
            document.getElementById('createOrderForm').style.display = 'none';
            document.getElementById('deleteOrderForm').style.display = 'none';
        }
        
        function hideUpdateOrderForm() {
            document.getElementById('updateOrderForm').style.display = 'none';
        }
        
        async function updateOrder() {
            const orderId = document.getElementById('updateOrderId').value;
            const title = document.getElementById('updateOrderTitle').value;
            const description = document.getElementById('updateOrderDesc').value;
            const amount = document.getElementById('updateOrderAmount').value;
            const status = document.getElementById('updateOrderStatus').value;
            
            if (!orderId) {
                alert('请输入订单 ID');
                return;
            }
            
            const updateData = {};
            if (title) updateData.title = title;
            if (description) updateData.description = description;
            if (amount) updateData.amount = parseFloat(amount);
            if (status) updateData.status = status;
            
            if (Object.keys(updateData).length === 0) {
                alert('请至少填写一个要更新的字段');
                return;
            }
            
            try {
                const response = await fetch(`/api/orders/${orderId}`, {
                    method: 'PUT',
                    headers: getHeaders(),
                    body: JSON.stringify(updateData)
                });
                const data = await response.json();
                if (response.ok) {
                    showResult('ordersResult', data);
                    hideUpdateOrderForm();
                    document.getElementById('updateOrderId').value = '';
                    document.getElementById('updateOrderTitle').value = '';
                    document.getElementById('updateOrderDesc').value = '';
                    document.getElementById('updateOrderAmount').value = '';
                    document.getElementById('updateOrderStatus').value = '';
                } else {
                    showResult('ordersResult', data, true);
                }
            } catch (error) {
                showResult('ordersResult', {error: error.message}, true);
            }
        }
        
        function showDeleteOrderForm() {
            document.getElementById('deleteOrderForm').style.display = 'block';
            document.getElementById('getOrderForm').style.display = 'none';
            document.getElementById('createOrderForm').style.display = 'none';
            document.getElementById('updateOrderForm').style.display = 'none';
        }
        
        function hideDeleteOrderForm() {
            document.getElementById('deleteOrderForm').style.display = 'none';
        }
        
        async function deleteOrder() {
            const orderId = document.getElementById('deleteOrderId').value;
            
            if (!orderId) {
                alert('请输入订单 ID');
                return;
            }
            
            if (!confirm(`确定要删除订单 ${orderId} 吗？`)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/orders/${orderId}`, {
                    method: 'DELETE',
                    headers: getHeaders()
                });
                
                if (response.ok || response.status === 204) {
                    showResult('ordersResult', {message: `订单 ${orderId} 已成功删除`});
                    hideDeleteOrderForm();
                    document.getElementById('deleteOrderId').value = '';
                } else {
                    const data = await response.json();
                    showResult('ordersResult', data, true);
                }
            } catch (error) {
                showResult('ordersResult', {error: error.message}, true);
            }
        }
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
