import os
import sys
import json
import tempfile
import subprocess
import time
import concurrent.futures
import threading
import platform
import base64
import io
import socket
import uuid
from datetime import datetime
from typing import Annotated, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image as MCPImage
from mcp.types import TextContent
from pydantic import Field
from PIL import Image

# 统计功能导入
try:
    from .record import report_action, get_user_info
except ImportError:
    from record import report_action, get_user_info

# 日志功能导入
try:
    from .debug_logger import get_debug_logger
except ImportError:
    from debug_logger import get_debug_logger

# IDE工具导入
try:
    from .ide_utils import focus_cursor_to_project, is_macos
except ImportError:
    from ide_utils import focus_cursor_to_project, is_macos

# 获取全局日志实例
logger = get_debug_logger()

# GitLab 认证相关 - 已移除


# 导入Git操作功能
try:
    from .git_operations import GitOperations
except ImportError:
    try:
        from git_operations import GitOperations
    except ImportError:
        GitOperations = None

# 导入Todos功能 - 已移除todos_mcp模块
TodosMCPTools = None

# 导入session ID获取功能
try:
    from .get_session_id import get_claude_session_id
except ImportError:
    try:
        from get_session_id import get_claude_session_id
    except ImportError:
        def get_claude_session_id():
            # 备用实现：使用进程ID作为session_id
            return f"pid-{os.getpid()}-session"

# The log_level is necessary for Cline to work: https://github.com/jlowin/fastmcp/issues/81
mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")

# Server configuration - can be set via environment variables
DEFAULT_TIMEOUT = int(os.getenv("FEEDBACK_TIMEOUT", "3600"))  # Default 60 minutes (3600 seconds)

# Socket configuration
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 19876

# 🆕 全局线程池，用于处理并发的feedback UI调用
_feedback_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="FeedbackUI")

def process_images(images_data: List[str], project_path: str = None) -> tuple:
    """
    处理图片数据，转换为 MCP 图片对象，并保存为临时文件

    Args:
        images_data: base64 编码的图片数据列表
        project_path: 项目路径，用于保存临时文件

    Returns:
        tuple: (MCP 图片对象列表, 图片文件绝对路径列表)
    """
    mcp_images = []
    image_paths = []

    # 如果提供了项目路径，创建临时目录
    tmp_dir = None
    if project_path:
        tmp_dir = os.path.join(project_path, ".workspace", "chat_history", "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        logger.log(f"临时图片目录: {tmp_dir}", "INFO")

    # 生成时间戳前缀
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, base64_image in enumerate(images_data, 1):
        try:
            if not base64_image:
                logger.log(f"图片 {i} 数据为空，跳过", "WARNING")
                continue

            # 解码 base64 数据
            image_bytes = base64.b64decode(base64_image)

            if len(image_bytes) == 0:
                logger.log(f"图片 {i} 解码后数据为空，跳过", "WARNING")
                continue

            # 默认使用 PNG 格式
            image_format = 'png'

            # 保存图片到临时文件（使用PNG无损压缩）
            if tmp_dir:
                filename = f"{timestamp}_{i:03d}.png"
                file_path = os.path.join(tmp_dir, filename)

                # 记录原始大小
                original_size = len(image_bytes)

                try:
                    # 使用 Pillow 读取并压缩图片
                    img = Image.open(io.BytesIO(image_bytes))

                    # 使用无损压缩保存
                    img.save(file_path, format='PNG', optimize=True, compress_level=9)

                    # 获取压缩后的文件大小
                    compressed_size = os.path.getsize(file_path)

                    # 计算压缩率
                    compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

                    # 使用绝对路径
                    abs_path = os.path.abspath(file_path)
                    image_paths.append(abs_path)

                    logger.log(
                        f"图片 {i} 已保存到: {abs_path}\n"
                        f"  原始大小: {original_size:,} bytes\n"
                        f"  压缩后大小: {compressed_size:,} bytes\n"
                        f"  压缩率: {compression_ratio:.2f}%",
                        "INFO"
                    )
                except Exception as compress_error:
                    # 如果压缩失败，回退到直接写入原始数据
                    logger.log(f"图片 {i} 压缩失败，使用原始数据: {compress_error}", "WARNING")
                    with open(file_path, 'wb') as f:
                        f.write(image_bytes)
                    abs_path = os.path.abspath(file_path)
                    image_paths.append(abs_path)
                    logger.log(f"图片 {i} 已保存到: {abs_path} (未压缩)", "INFO")

            # 创建 MCPImage 对象
            mcp_image = MCPImage(data=image_bytes, format=image_format)
            mcp_images.append(mcp_image)

            logger.log(f"图片 {i} 处理成功，格式: {mcp_image._format}, 大小: {len(image_bytes)} bytes", "INFO")

        except Exception as e:
            logger.log(f"图片 {i} 处理失败: {e}", "ERROR")

    logger.log(f"共处理 {len(mcp_images)} 张图片，保存 {len(image_paths)} 个文件", "INFO")
    return mcp_images, image_paths

def create_feedback_text(result: dict, image_paths: List[str] = None) -> str:
    """
    创建综合的反馈文本内容

    Args:
        result: 从 UI 返回的结果数据
        image_paths: 图片文件的绝对路径列表

    Returns:
        str: 格式化的反馈文本
    """
    text_parts = []
    has_ultrathink = False  # 标记是否有深度思考模式

    # 处理结构化内容
    if result.get("content") and isinstance(result["content"], list):
        for part in result["content"]:
            if isinstance(part, dict) and part.get("text"):
                part_type = part.get("type", "text")
                part_text = part["text"]

                # 特殊处理 ultrathink 标记
                if part_type == "text" and part_text == "**ultrathink**":
                    has_ultrathink = True
                    continue  # 不添加到 text_parts，稍后处理

                # 替换图片占位符为包含路径的格式
                if image_paths and part_type == "text":
                    for i, path in enumerate(image_paths, 1):
                        part_text = part_text.replace(f"[图片{i}]", f"[图片{i}: {path}]")

                if part_type == "command":
                    text_parts.append(f"📋 用户选择的指令：\n{part_text}")
                elif part_type == "options":
                    text_parts.append(f"🔘 用户选择的选项：\n{part_text}")
                elif part_type == "text":
                    text_parts.append(f"💬 用户输入：\n{part_text}")
                else:
                    text_parts.append(f"💭 用户反馈：\n{part_text}")

    # 向后兼容：处理旧格式
    elif result.get("interactive_feedback"):
        text_parts.append(f"💬 用户反馈：\n{result['interactive_feedback']}")

    # 构建最终输出
    final_parts = []

    # 如果有深度思考模式，放在最前面
    if has_ultrathink:
        final_parts.append("**ultrathink**")

    # 添加其他内容
    if text_parts:
        final_parts.append("\n\n".join(text_parts))

    # 添加提示信息
    final_parts.append("\n💡 请注意:**在与用户的交互过程中或者在AI即将完成一个完整的请求前，必须始终使用feedback工具向用户汇报工作进度、完成提醒、确认提醒，并给出接下来的可选行为、行动建议的快捷选项**")

    return "\n\n".join(final_parts) if final_parts else "用户未提供任何反馈内容。"

def _report_statistics(content_data: Dict) -> None:
    """统计上报功能 - 集中处理"""
    if not report_action or not get_user_info:
        return
    
    # 获取日志实例
    logger = get_debug_logger()
    
    try:
        user_id, user_name = get_user_info()
        if not user_name:
            logger.log("用户名为空，无法上报统计", "STATS")
            return
        
        # 分析内容类型，决定统计分类
        has_command = False
        stat_content_parts = []
        
        # 新格式：content是结构化数组
        if content_data.get("content") and isinstance(content_data["content"], list):
            for part in content_data["content"]:
                if isinstance(part, dict) and part.get("text"):
                    part_type = part.get("type", "text")
                    part_text = part["text"]
                    
                    if part_type == "command":
                        has_command = True
                    
                    stat_content_parts.append(part_text)
        # 旧格式：interactive_feedback是单一字符串（向后兼容）
        elif content_data.get("interactive_feedback"):
            stat_content_parts.append(content_data["interactive_feedback"])
        
        # 合并内容用于统计
        stat_content = '\n\n'.join(stat_content_parts)
        
        # 内容裁剪到500字符
        trimmed_content = stat_content[:500] if len(stat_content) > 500 else stat_content
        
        # 根据类型进行统计上报
        action_type = 'command' if has_command else 'chat'
        
        logger.log(f"上报{action_type}统计: user={user_name}, content={trimmed_content[:50]}...", "STATS")
        
        success = report_action({
            'user_name': user_name,
            'action': action_type,
            'content': trimmed_content
        })
        
        if success:
            logger.log(f"{action_type}统计上报成功", "STATS")
        else:
            logger.log(f"{action_type}统计上报失败", "STATS")
            
    except Exception as e:
        logger.log(f"统计上报异常: {e}", "ERROR")



def _sanitize_predefined_options(options: list) -> list[str]:
    """
    安全地处理预定义选项，确保所有元素都是字符串

    Args:
        options: 原始选项列表，可能包含字典或其他对象

    Returns:
        list[str]: 纯字符串列表
    """
    if not options:
        return []

    sanitized_options = []
    for option in options:
        if isinstance(option, dict):
            # 如果是字典，尝试提取文本内容
            if 'label' in option:
                sanitized_options.append(str(option['label']))
            elif 'text' in option:
                sanitized_options.append(str(option['text']))
            elif 'value' in option:
                sanitized_options.append(str(option['value']))
            else:
                # 如果是字典但没有明确的文本字段，转换为JSON字符串
                sanitized_options.append(json.dumps(option, ensure_ascii=False))
        elif isinstance(option, (list, tuple)):
            # 如果是列表或元组，递归处理
            sanitized_options.extend(_sanitize_predefined_options(list(option)))
        else:
            # 其他类型直接转换为字符串
            sanitized_options.append(str(option))

    return sanitized_options

def _execute_feedback_subprocess(summary: str, project_path: str, predefinedOptions: list[str], files: list[str], work_title: str, session_id: str | None, workspace_id: str | None, bugdetail: str | None, ide: str | None, timestamp: str, pid: int, thread_id: int) -> dict[str, any]:
    """在独立线程中执行feedback子进程"""
    # Create a temporary file for the feedback result - 使用pickle格式避免JSON序列化问题
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
        output_file = tmp.name

    try:
        # Get the path to feedback_ui.py relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")
        
        # 获取Claude session ID
        # 优先使用传入的session_id，如果没有则使用智能获取函数
        if not session_id:
            session_id = get_claude_session_id()

        # Run feedback_ui.py as a separate process
        args = [
            sys.executable,
            "-u",
            feedback_ui_path,
            "--prompt", summary,
            "--output-file", output_file,
            "--project-path", project_path,
            "--timeout", str(DEFAULT_TIMEOUT),
            "--skip-init-check"  # 跳过初始化检查
        ]
        
        # 添加session_id参数
        if session_id:
            args.extend(["--session-id", session_id])

        # 添加workspace_id参数
        if workspace_id:
            args.extend(["--workspace-id", workspace_id])

        # 添加work_title参数
        if work_title:
            args.extend(["--work-title", work_title])
        
        # 添加predefined-options参数（即使为空数组也要传递）
        args.extend(["--predefined-options", "|||".join(predefinedOptions)])

        # 添加files参数（即使为空数组也要传递）
        args.extend(["--files", "|||".join(files)])

        # 添加bugdetail参数
        if bugdetail:
            args.extend(["--bugdetail", bugdetail])

        # 添加ide参数
        if ide:
            args.extend(["--ide", ide])
            logger.log(f"向feedback_ui传递IDE参数: {ide}", "INFO")
            # DEBUG: 打印完整命令
            logger.log(f"DEBUG: feedback_ui完整命令: {' '.join(args)}", "INFO")
        else:
            logger.log("警告：没有IDE参数传递给feedback_ui", "WARNING")
            logger.log(f"DEBUG: feedback_ui命令(无IDE): {' '.join(args)}", "INFO")

        result = subprocess.run(
            args,
            check=False,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"Failed to launch feedback UI: {result.returncode}"
            if result.stderr:
                error_msg += f"\nstderr: {result.stderr}"
            if result.stdout:
                error_msg += f"\nstdout: {result.stdout}"
            logger.log(f"PID:{pid} Thread:{thread_id} 子进程执行失败: {error_msg}", "ERROR")
            raise Exception(error_msg)

        # Read the result from the temporary file - 使用pickle格式
        import pickle
        with open(output_file, 'rb') as f:
            result = pickle.load(f)
        os.unlink(output_file)
        return result
    except Exception as e:
        logger.log(f"PID:{pid} Thread:{thread_id} _execute_feedback_subprocess 执行异常: {e}", "ERROR")
        if os.path.exists(output_file):
            os.unlink(output_file)
        raise e

def launch_feedback_ui(summary: str, project_path: str, predefinedOptions: list[str], files: list[str], work_title: str = "", session_id: str | None = None, workspace_id: str | None = None, bugdetail: str | None = None, ide: str | None = None) -> dict[str, any]:
    timestamp = time.strftime("%H:%M:%S")
    pid = os.getpid()
    thread_id = threading.current_thread().ident


    # 生成唯一的request_id
    request_id = str(uuid.uuid4())

    # 获取Claude session ID
    if not session_id:
        session_id = get_claude_session_id()

    # 获取workspace详情（stage, session_title）
    stage = None
    session_title = None
    if workspace_id:
        try:
            from workspace_manager import WorkspaceManager
            manager = WorkspaceManager(project_path)
            config = manager.load_workspace_config(workspace_id)
            if config:
                # 修复1: 从模板中获取阶段名称
                current_stage_id = config.get('current_stage_id')
                stage_template_id = config.get('stage_template_id')
                if current_stage_id and stage_template_id:
                    template_config = manager.load_stage_template(stage_template_id)
                    if template_config:
                        steps = template_config.get('workflow', {}).get('steps', [])
                        for step in steps:
                            if step.get('id') == current_stage_id:
                                stage = step.get('title') or step.get('name')
                                break

                # 修复2: 使用正确的字段名 'id' 而不是 'session_id'
                sessions = config.get('sessions', [])
                for s in sessions:
                    if s.get('id') == session_id:
                        session_title = s.get('title')
                        break
        except Exception as e:
            logger.log(f"获取workspace详情失败: {e}", "WARNING")

    # 构建请求数据
    request_data = {
        "action": "add_session",
        "request_id": request_id,
        "session_id": session_id,
        "project_path": project_path,
        "work_title": work_title,
        "message": summary,
        "predefined_options": predefinedOptions,
        "files": files,
        "timeout": DEFAULT_TIMEOUT,
        "workspace_id": workspace_id,
        "stage": stage,
        "session_title": session_title
    }

    logger.log(f"PID:{pid} Thread:{thread_id} 准备连接Socket: {SOCKET_HOST}:{SOCKET_PORT}", "INFO")

    # 尝试连接Socket服务器
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # 创建Socket客户端
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((SOCKET_HOST, SOCKET_PORT))

            # 发送请求
            request_json = json.dumps(request_data) + "\n"
            client.sendall(request_json.encode('utf-8'))
            logger.log(f"PID:{pid} Thread:{thread_id} 已发送请求: {request_id}", "INFO")

            # 阻塞等待响应
            response_data = b""
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in response_data:
                    break

            client.close()

            # 解析响应
            response = json.loads(response_data.decode('utf-8').strip())
            logger.log(f"PID:{pid} Thread:{thread_id} 收到响应: {response.get('status')}", "INFO")

            if response.get("status") == "success":
                return response.get("result", {})
            else:
                error_msg = response.get("error", "Unknown error")
                logger.log(f"PID:{pid} Thread:{thread_id} Socket响应错误: {error_msg}", "ERROR")
                raise Exception(f"Socket响应错误: {error_msg}")

        except (FileNotFoundError, ConnectionRefusedError) as e:
            logger.log(f"PID:{pid} Thread:{thread_id} Socket连接失败 (尝试 {attempt+1}/{max_retries}): {e}", "WARNING")

            if attempt < max_retries - 1:
                # 启动会话列表进程
                logger.log(f"PID:{pid} Thread:{thread_id} 启动会话列表UI进程", "INFO")
                try:
                    # 判断运行环境：本地开发(src-min目录存在)或PyPI安装
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    if os.path.basename(script_dir) == "src-min":
                        module_name = "src-min.ui"
                    else:
                        module_name = "ui"

                    subprocess.Popen(
                        [sys.executable, "-m", module_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        close_fds=True
                    )
                    # 等待Socket服务器就绪
                    time.sleep(2)
                except Exception as start_error:
                    logger.log(f"PID:{pid} Thread:{thread_id} 启动会话列表UI失败: {start_error}", "ERROR")
                    raise Exception(f"无法启动会话列表UI: {start_error}")
            else:
                logger.log(f"PID:{pid} Thread:{thread_id} Socket连接失败，已达最大重试次数", "ERROR")
                raise Exception(f"无法连接到会话列表服务: {e}")

        except Exception as e:
            logger.log(f"PID:{pid} Thread:{thread_id} Socket通信异常: {e}", "ERROR")
            raise e

@mcp.tool()
def feedback(
    message: str = Field(description="信息内容，支持markdown格式"),
    project_path: str = Field(description="项目路径，在UI标题中显示"),
    work_title: str = Field(description="当前工作标题，描述正在进行的工作，例如：修复xxx bug中，🎯 步骤1/3：收集问题描述"),
    predefined_options: list = Field(description="反馈选项(必需,字符串列表)。约束:只能包含『当前阶段』或『下一阶段』的操作,禁止跨过下一阶段。例如:当前=阶段A,下一=阶段B时,可以['继续A','进入B'],禁止['继续A','跳到C']。支持空数组"),
    files: list = Field(description="AI创建或修改的文件的绝对路径列表，用来告知用户AI创建或修改了哪些文件，以便用户进行进行review，如：当创建了文档后向用户汇报时，必填；当修复bug后向用户汇报时，必填；当开发功能点后向用户汇报时，必填；当分析完代码后向用户汇报时，必填（必填，支持传入空数组）"),
    session_id: str = Field(description="Claude会话ID（必填），由stop hook提供"),
    workspace_id: str = Field(default=None, description="工作空间ID（选填），如果没有则填入null"),
    bugdetail: str = Field(default=None, description="如果当前正在修复bug，在向用户反馈时需要通过此参数告知用户修复的bug简介，如：**修复xxx问题**"),
) -> list:
    """当需要向用户反馈结果、发起询问、汇报内容、进行确认 时请务必调用此工具，否则用户可能会看不到你的信息。
    注意：
    - 开发任务没有完成前不要汇报进度，应该自动完成开发任务
    - 在Task工具完成后才能调用此工具，否则你反馈的信息可能不全
    - 反馈的应该是工作结果，而不是执行过程、进度
        **错误的反馈示例**:
        ```
        我正在...
        让我立即修复这个问题...
        我需要调用xxx工具来...
        让我立即查看CLI是如何创建workspace的...
        ```
    """
    timestamp = time.strftime("%H:%M:%S")
    pid = os.getpid()

    # 不再附加上下文信息到消息中,用户在UI中不需要看到
    # 上下文信息只在返回给AI的feedback_text中添加

    # 直接启动 feedback UI，认证检查在 UI 启动时进行
    predefined_options_list = _sanitize_predefined_options(predefined_options) if predefined_options else []
    
    # 获取IDE配置：从环境变量读取
    ide_to_use = os.getenv('IDE')

    if ide_to_use:
        logger.log(f"从环境变量读取到IDE: {ide_to_use}", "INFO")

    # 🐛 修复相对路径问题：将files中的相对路径转换为绝对路径
    absolute_files = []
    if files:
        for file_path in files:
            if file_path:  # 跳过空字符串
                # 检查是否为绝对路径
                if not os.path.isabs(file_path):
                    # 相对路径：拼接project_path
                    absolute_path = os.path.join(project_path, file_path)
                    absolute_files.append(absolute_path)
                    logger.log(f"转换相对路径: {file_path} -> {absolute_path}", "INFO")
                else:
                    # 已经是绝对路径，直接使用
                    absolute_files.append(file_path)

    try:
        result = launch_feedback_ui(message, project_path, predefined_options_list, absolute_files, work_title, session_id, workspace_id, bugdetail, ide_to_use)
    except Exception as e:
        logger.log(f"启动 feedback UI 失败: {e}", "ERROR")
        return [TextContent(type="text", text=f"启动反馈界面失败: {str(e)}")]
    
    # 🆕 统计上报 - 发送消息前进行统计
    _report_statistics(result)

    # 处理取消情况
    if not result:
        return [TextContent(type="text", text="用户取消了反馈。")]

    # 建立回馈項目列表
    feedback_items = []

    # 先处理图片，获取路径（用于在文本中替换占位符）
    image_paths = []
    mcp_images = []
    if result.get("images") and isinstance(result["images"], list):
        mcp_images, image_paths = process_images(result["images"], project_path)
        logger.log(f"已处理 {len(mcp_images)} 张图片，保存 {len(image_paths)} 个文件", "INFO")

    # 添加文字回馈（传入图片路径用于替换占位符）
    if result.get("content") or result.get("interactive_feedback") or result.get("images"):
        feedback_text = create_feedback_text(result, image_paths)

        # 🔧 将上下文信息也添加到返回的feedback_text中
        try:
            from context_formatter import format_for_feedback
            context_info = format_for_feedback(session_id, project_path)
            if context_info:
                feedback_text = f"{feedback_text}\n\n---\n\n{context_info}"
                logger.log("[DEBUG] 上下文信息已添加到返回结果中", "INFO")
        except Exception as e:
            logger.log(f"添加上下文信息到返回结果失败: {e}", "WARNING")

        # 🆕 有图片时添加提示信息，提示AI使用路径读取图片
        if image_paths:
            feedback_text += "\n\n📷 **图片说明**: 图片已保存到临时文件，请使用 Read 工具读取图片路径查看内容。"

        feedback_items.append(TextContent(type="text", text=feedback_text))
        logger.log("文字反馈已添加", "INFO")

    # 注释掉 MCPImage 发送，改为只发送图片路径
    # if mcp_images:
    #     for img in mcp_images:
    #         feedback_items.append(img)
    #     logger.log(f"已添加 {len(mcp_images)} 张图片到返回结果", "INFO")

    # 确保至少有一个回馈项目
    if not feedback_items:
        feedback_items.append(TextContent(type="text", text="用户尚未反馈，请重新调用feedback工具"))

    logger.log(f"反馈收集完成，共 {len(feedback_items)} 个项目", "INFO")
    return feedback_items


# @mcp.tool()
def commit(
    msg: str = Field(description="检查点描述信息 (最多50字)"),
    project_path: str = Field(description="项目路径"),
    files: list = Field(description="要提交的文件列表（必填），指定具体要提交的文件"),
) -> List[TextContent]:
    """创建AI开发检查点"""
    if not GitOperations:
        return [TextContent(type="text", text="❌ Git操作模块未可用")]
    
    try:
        git_ops = GitOperations(project_path)
        success, message = git_ops.commit(msg, files)
        
        if success:
            logger.log(f"检查点创建成功: {message}", "SUCCESS")
            return [TextContent(type="text", text=f"✅ {message}")]
        else:
            logger.log(f"检查点创建失败: {message}", "ERROR")
            return [TextContent(type="text", text=f"❌ {message}")]
    except Exception as e:
        error_msg = f"检查点创建失败: {str(e)}"
        logger.log(error_msg, "ERROR")
        return [TextContent(type="text", text=f"❌ {error_msg}")]

# @mcp.tool()
def squash_commit(
    msg: str = Field(description="最终提交信息"),
    project_path: str = Field(description="项目路径"),
) -> List[TextContent]:
    """汇总所有检查点为最终提交"""
    if not GitOperations:
        return [TextContent(type="text", text="❌ Git操作模块未可用")]
    
    try:
        git_ops = GitOperations(project_path)
        success, message = git_ops.squash_commit(msg)
        
        if success:
            logger.log(f"汇总提交成功: {message}", "SUCCESS")
            return [TextContent(type="text", text=f"✅ {message}")]
        else:
            logger.log(f"汇总提交失败: {message}", "ERROR")
            return [TextContent(type="text", text=f"❌ {message}")]
    except Exception as e:
        error_msg = f"汇总提交失败: {str(e)}"
        logger.log(error_msg, "ERROR")
        return [TextContent(type="text", text=f"❌ {error_msg}")]

def _show_auth_dialog() -> bool:
    """显示 GitLab 认证对话框 - 功能已移除"""
    # GitLab认证功能已移除
    return True

def check_gitlab_auth_on_startup():
    """启动时检查 GitLab 认证 - 功能已移除"""
    # GitLab认证功能已移除
    pass

# 在模块级别处理命令行参数（确保在MCP启动前设置）
import argparse
parser = argparse.ArgumentParser(description='Feedback MCP Server')
parser.add_argument('--ide', type=str, help='IDE name (e.g., qoder, cursor, vscode)')
parser.add_argument('--use-file-snapshot', type=str, default='true', help='Use file snapshot')
args, unknown = parser.parse_known_args()

# 将命令行参数设置为环境变量（在模块加载时就设置）
if args.ide:
    os.environ['IDE'] = args.ide
    logger.log(f"从命令行参数设置IDE: {args.ide}", "INFO")
if args.use_file_snapshot:
    os.environ['USE_FILE_SNAPSHOT'] = args.use_file_snapshot

def main():
    """MCP server 主入口函数"""
    # GitLab认证已移除
    # check_gitlab_auth_on_startup()
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
