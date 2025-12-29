#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

def main():
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)

        # Only process Task tool calls
        if input_data.get("tool_name") != "Task":
            return

        session_id = input_data.get("session_id")
        if not session_id:
            return

        # Get project root directory from cwd field
        cwd = input_data.get("cwd", ".")
        project_root = Path(cwd)

        tool_input = input_data.get("tool_input", {})
        tool_response = input_data.get("tool_response", {})

        # Extract content text
        content_list = tool_response.get("content", [])
        content_text = ""
        for item in content_list:
            if item.get("type") == "text":
                content_text = item.get("text", "")
                break

        # Construct agent record
        agent_record = {
            "role": "agent",
            "subagent_type": tool_input.get("subagent_type", ""),
            "description": tool_input.get("description", ""),
            "agent_id": tool_response.get("agentId", ""),
            "content": content_text,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": tool_response.get("status", ""),
            "duration_ms": tool_response.get("totalDurationMs", 0),
            "tokens": tool_response.get("totalTokens", 0),
            "tool_calls": tool_response.get("totalToolUseCount", 0)
        }

        # Ensure directory exists using absolute path
        history_dir = project_root / ".workspace/chat_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        # Read existing history or create new
        history_file = history_dir / f"{session_id}.json"
        if history_file.exists():
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Detect format
            if isinstance(data, dict) and "dialogues" in data:
                # New format
                data["dialogues"].append(agent_record)
            else:
                # Old format (list)
                data = {"dialogues": data + [agent_record], "control": {}}
        else:
            # Create new format
            data = {"dialogues": [agent_record], "control": {}}

        # Write back
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        # Silent fail to avoid breaking the hook chain
        pass

if __name__ == "__main__":
    main()
