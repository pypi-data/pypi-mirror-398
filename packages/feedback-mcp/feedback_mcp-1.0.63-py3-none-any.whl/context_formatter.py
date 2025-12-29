"""
上下文信息格式化模块
用于格式化工作空间、阶段、任务等上下文信息
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from workspace_manager import WorkspaceManager, get_session_title_for_session


def load_task_list(session_id: str, project_path: str = None) -> list:
    """加载任务列表

    Args:
        session_id: 会话ID
        project_path: 项目路径

    Returns:
        任务列表，每个任务包含 id, title, state
    """
    try:
        if not project_path:
            project_path = Path.cwd()
        else:
            project_path = Path(project_path)

        task_file = project_path / '.workspace' / 'tasks' / f'{session_id}.json'
        if not task_file.exists():
            return []

        with open(task_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('tasks', [])
    except Exception:
        return []


def format_for_stop_hook(session_id: str, project_path: str = None) -> str:
    """格式化上下文信息用于stop hook

    Args:
        session_id: 会话ID
        project_path: 项目路径

    Returns:
        格式化的上下文信息字符串
    """
    lines = []
    has_content = False

    # 获取会话标题
    session_title = get_session_title_for_session(session_id, project_path)

    # 获取阶段信息
    workspace_mgr = WorkspaceManager(project_path)
    stage_info = workspace_mgr.get_stage_info(session_id)

    # 获取任务列表
    tasks = load_task_list(session_id, project_path)

    # 只有在有阶段信息或任务列表时才显示
    if stage_info or tasks or session_title:
        lines.append("# 当前上下文相关信息：")
        lines.append("")
        has_content = True

    # 显示会话标题（仅当有值时）
    if session_title:
        # 检查是否为默认的新会话标题（包含"新会话"或以"New conversation"开头）
        if "新会话" in session_title or session_title.startswith("New conversation"):
            lines.append("## 当前会话标题：" + session_title)
            lines.append("⚠️ **提醒：请根据工作内容及时更新会话标题**")
            lines.append("")
        else:
            lines.append("## 当前会话标题：" + session_title)
            lines.append("")

    # 显示阶段信息（仅当有值时）
    if stage_info:
        current_stage = stage_info.get('current_stage', {})
        next_stage = stage_info.get('next_stage', {})

        if current_stage and current_stage.get('title'):
            lines.append(f"## 当前阶段：{current_stage.get('title')}")

        if next_stage and next_stage.get('title'):
            lines.append(f"## 下一个阶段：{next_stage.get('title')}")
        elif current_stage:  # 有当前阶段但没有下一阶段
            lines.append("## 下一个阶段：已完成所有阶段")

    # 显示任务列表（仅当有任务时）
    if tasks:
        lines.append("## 任务列表：")

        for task in tasks:
            state = task.get('state', 'pending')
            title = task.get('title', '未命名任务')
            task_id = task.get('id', '')

            # 简化标题显示
            if '(执行前请查看该步骤的详细规则)' in title:
                title = title.replace('(执行前请查看该步骤的详细规则)', '').strip()

            if state == 'completed':
                checkbox = '[x]'
            elif state == 'in_progress':
                checkbox = '[~]'
            else:
                checkbox = '[ ]'

            lines.append(f"- {checkbox} {task_id}. {title}")

        lines.append("")

    # 添加提示信息
    if has_content:
        lines.append(f"session_id:{session_id}")
        lines.append("请分析接下来的行动计划，是继续自动工作还是使用 feedback mcp 工具向用户反馈/请示")
        lines.append("请注意:只有通过 feedback mcp 用户才能收到你的信息，才能对你的消息进行反馈、确认")
        
    else:
        # 没有上下文信息时的简化提示
        lines.append(f"session_id:{session_id}")
        lines.append("请使用 feedback 工具向用户反馈/请示")

    return "\n".join(lines)


def format_context_info(session_id: str, project_path: str = None) -> Optional[str]:
    """格式化上下文信息（仅用于显示给用户）

    Args:
        session_id: 会话ID
        project_path: 项目路径

    Returns:
        格式化的上下文信息字符串，如果没有上下文信息则返回None
    """
    lines = []
    has_content = False

    # 获取阶段信息
    workspace_mgr = WorkspaceManager(project_path)
    stage_info = workspace_mgr.get_stage_info(session_id)

    # 获取任务列表
    tasks = load_task_list(session_id, project_path)

    # 只有在有阶段信息或任务列表时才添加内容
    if not stage_info and not tasks:
        return None

    lines.append("## 📋 当前上下文")
    lines.append("")

    # 显示阶段信息（仅当有值时）
    if stage_info:
        current_stage = stage_info.get('current_stage', {})
        next_stage = stage_info.get('next_stage', {})

        if current_stage and current_stage.get('title'):
            lines.append(f"**当前阶段**: {current_stage.get('title')}")
            has_content = True

        if next_stage and next_stage.get('title'):
            lines.append(f"**下一阶段**: {next_stage.get('title')}")
            has_content = True
        elif current_stage:  # 有当前阶段但没有下一阶段
            lines.append("**下一阶段**: 已完成所有阶段")
            has_content = True

        if has_content:
            lines.append("")

    # 显示任务列表（仅当有任务时）
    if tasks:
        # 找出当前任务和下一任务
        current_task = None
        next_task = None

        for i, task in enumerate(tasks):
            state = task.get('state', 'pending')
            if state == 'in_progress':
                current_task = task
                # 找下一个待处理的任务
                for j in range(i + 1, len(tasks)):
                    if tasks[j].get('state', 'pending') == 'pending':
                        next_task = tasks[j]
                        break
                break

        # 如果没有进行中的任务，找第一个待处理的任务
        if not current_task:
            for task in tasks:
                if task.get('state', 'pending') == 'pending':
                    current_task = task
                    # 找下一个
                    idx = tasks.index(task)
                    for j in range(idx + 1, len(tasks)):
                        if tasks[j].get('state', 'pending') == 'pending':
                            next_task = tasks[j]
                            break
                    break

        if current_task:
            title = current_task.get('title', '未命名任务')
            # 简化标题显示
            if '(执行前请查看该步骤的详细规则)' in title:
                title = title.replace('(执行前请查看该步骤的详细规则)', '').strip()
            lines.append(f"**当前任务**: {title}")
            has_content = True

        if next_task:
            title = next_task.get('title', '未命名任务')
            # 简化标题显示
            if '(执行前请查看该步骤的详细规则)' in title:
                title = title.replace('(执行前请查看该步骤的详细规则)', '').strip()
            lines.append(f"**下一任务**: {title}")
            has_content = True
        elif current_task and not next_task:
            lines.append("**下一任务**: 无（已是最后一个任务）")
            has_content = True

    if not has_content:
        return None

    return "\n".join(lines)


def format_for_feedback(session_id: str, project_path: str = None) -> Optional[str]:
    """格式化完整的feedback信息(AI规则+上下文),用于返回给AI

    Args:
        session_id: 会话ID
        project_path: 项目路径

    Returns:
        格式化的完整信息字符串，如果没有上下文信息则返回None
    """
    # 获取阶段信息
    workspace_mgr = WorkspaceManager(project_path)
    stage_info = workspace_mgr.get_stage_info(session_id)

    # 获取任务列表
    tasks = load_task_list(session_id, project_path)

    # 只有在有阶段信息或任务列表时才添加内容
    if not stage_info and not tasks:
        return None

    lines = []
    lines.append("## AI(你的)工作规则")
    lines.append("")
    lines.append("### 核心原则")
    lines.append("1. **严格遵循当前阶段**: 只能执行当前阶段的工作内容")
    lines.append("2. **严格遵循任务顺序**: 只能执行当前任务,完成后才能进入下一任务")
    lines.append("3. **禁止跨阶段**: feedback反馈选项只能针对『当前阶段』或『下一阶段』,禁止跨过下一阶段")
    lines.append("")
    lines.append("### Feedback使用规则(必须遵守)")
    lines.append("**禁止反馈以下内容:**")
    lines.append("- ❌ '好的,需求分析已确认'(没有实际工作)")
    lines.append("- ❌ '现在我将切换到下一阶段'(意图声明)")
    lines.append("- ❌ '让我开始XXX'(计划声明)")
    lines.append("- ❌ '我正在XXX'(进度声明)")
    lines.append("")
    lines.append("**只能反馈:**")
    lines.append("- ✓ 已完成的工作结果")
    lines.append("- ✓ 需要用户确认/选择的事项")
    lines.append("- ✓ 遇到的问题需要用户解决")
    lines.append("")
    lines.append("**正确流程:**")
    lines.append("用户要求切换阶段 → 先调用workspace_next_stage → 再开始工作 → 完成后再feedback")
    lines.append("")
    lines.append("### 反馈选项约束")
    lines.append("**允许的反馈选项:**")
    lines.append("- ✓ 当前阶段的操作 (如『继续当前工作』『修改当前成果』等)")
    lines.append("- ✓ 进入下一阶段 (如『确认,进入<下一阶段名称>』)")
    lines.append("")
    lines.append("**禁止的反馈选项:**")
    lines.append("- ❌ 跨过下一阶段的操作 (如当前=阶段1,下一=阶段2,禁止出现『直接进入阶段3』)")
    lines.append("- ❌ 跳过当前阶段的流程 (如当前阶段未完成就提供后续阶段的选项)")
    lines.append("")
    lines.append("### 操作检查清单")
    lines.append("在提供feedback选项前,必须检查:")
    lines.append("1. ✓ 当前阶段名称是什么?")
    lines.append("2. ✓ 下一阶段名称是什么?")
    lines.append("3. ✓ 我提供的选项是否只涉及『当前阶段』或『下一阶段』?")
    lines.append("4. ✓ 是否有跨过下一阶段的选项? (有则删除)")
    lines.append("")
    lines.append("### 示例说明")
    lines.append("假设: 当前阶段=A, 下一阶段=B, 再下一阶段=C")
    lines.append("- ✓ 正确: 反馈选项『继续A阶段工作』『完成A进入B阶段』")
    lines.append("- ❌ 错误: 反馈选项『继续A阶段工作』『直接进入C阶段』(跨过了B)")
    lines.append("")

    # 添加上下文信息
    context_info = format_context_info(session_id, project_path)
    if context_info:
        lines.append(context_info)

    return "\n".join(lines)
