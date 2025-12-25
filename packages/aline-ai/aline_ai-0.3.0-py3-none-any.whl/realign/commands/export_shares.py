#!/usr/bin/env python3
"""
Export shares command - Export selected commits' chat history to JSON files.

This allows users to select specific commits and extract their chat history changes
into standalone JSON files for sharing.
"""

import json
import os
import subprocess
import sys
import secrets
import hashlib
import base64
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from .review import get_unpushed_commits, UnpushedCommit
from .hide import parse_commit_indices
from ..logging_config import setup_logger

logger = setup_logger('realign.commands.export_shares', 'export_shares.log')

# Try to import cryptography
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography package not available, interactive mode disabled")

# Try to import httpx
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx package not available, interactive mode disabled")


def get_line_timestamp(line_json: dict) -> datetime:
    """
    从 JSON 对象中提取时间戳。

    Args:
        line_json: JSON 对象

    Returns:
        datetime 对象，如果没有 timestamp 则返回 datetime.min
    """
    if 'timestamp' in line_json:
        ts_str = line_json['timestamp']
        # 处理 ISO 格式: "2025-12-07T17:54:42.618Z"
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    return datetime.min  # 没有时间戳的放在最前面


def get_session_id(line_json: dict) -> Optional[str]:
    """
    从 JSON 对象中提取 session ID。

    Args:
        line_json: JSON 对象

    Returns:
        session ID 字符串，如果没有则返回 None
    """
    return line_json.get('sessionId')


def extract_messages_from_commit(
    commit: UnpushedCommit,
    repo_root: Path
) -> Dict[str, List[Tuple[datetime, dict]]]:
    """
    从单个 commit 提取所有新增消息，按 session ID 分组。

    Args:
        commit: UnpushedCommit 对象
        repo_root: shadow git 仓库路径

    Returns:
        字典: {session_id: [(timestamp, json_object), ...]}
    """
    logger.info(f"Extracting messages from commit {commit.hash}")
    session_messages = defaultdict(list)

    for session_file, line_ranges in commit.session_additions.items():
        logger.debug(f"Processing session file: {session_file}")

        # 获取文件内容
        result = subprocess.run(
            ["git", "show", f"{commit.full_hash}:{session_file}"],
            cwd=repo_root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.warning(f"Failed to get content for {session_file}")
            continue

        lines = result.stdout.split('\n')

        # 提取新增行
        for start, end in line_ranges:
            for line_num in range(start, end + 1):
                if line_num <= len(lines):
                    line = lines[line_num - 1].strip()

                    if not line or "[REDACTED]" in line:
                        continue

                    try:
                        json_obj = json.loads(line)

                        # 跳过已被标记为 redacted 的内容
                        if json_obj.get("redacted"):
                            continue

                        session_id = get_session_id(json_obj)
                        if session_id:
                            timestamp = get_line_timestamp(json_obj)
                            session_messages[session_id].append((timestamp, json_obj))
                            logger.debug(f"Extracted message from session {session_id}")

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON at line {line_num}: {e}")
                        continue

    logger.info(f"Extracted {sum(len(msgs) for msgs in session_messages.values())} messages from {len(session_messages)} sessions")
    return session_messages


def merge_messages_from_commits(
    selected_commits: List[UnpushedCommit],
    repo_root: Path
) -> Dict[str, List[dict]]:
    """
    合并所有选中 commits 的消息，按 session ID 分组并排序。

    Args:
        selected_commits: 选中的 commits 列表
        repo_root: shadow git 仓库路径

    Returns:
        字典: {session_id: [sorted_json_objects]}
    """
    logger.info(f"Merging messages from {len(selected_commits)} commits")
    all_session_messages = defaultdict(list)

    # 按时间顺序处理 commits（从旧到新）
    for commit in reversed(selected_commits):
        commit_messages = extract_messages_from_commit(commit, repo_root)

        for session_id, messages in commit_messages.items():
            all_session_messages[session_id].extend(messages)

    # 排序和去重
    result = {}
    for session_id, messages_with_ts in all_session_messages.items():
        # 按时间戳排序
        sorted_messages = sorted(messages_with_ts, key=lambda x: x[0])

        # 去重（基于 JSON 字符串）
        seen = set()
        unique_messages = []
        for ts, msg in sorted_messages:
            msg_str = json.dumps(msg, sort_keys=True, ensure_ascii=False)
            if msg_str not in seen:
                seen.add(msg_str)
                unique_messages.append(msg)

        result[session_id] = unique_messages
        logger.info(f"Session {session_id}: {len(unique_messages)} unique messages")

    return result


def save_export_file(
    session_messages: Dict[str, List[dict]],
    output_dir: Path,
    username: str
) -> Path:
    """
    保存导出文件。

    Args:
        session_messages: {session_id: [messages]}
        output_dir: 输出目录
        username: 用户名

    Returns:
        导出文件路径
    """
    logger.info(f"Saving export file to {output_dir}")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名: username_timestamp.json
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{username}_{timestamp}.json"
    output_path = output_dir / filename

    # 构建导出数据
    export_data = {
        "username": username,
        "time": datetime.now().isoformat(),
        "sessions": [
            {
                "session_id": session_id,
                "messages": messages
            }
            for session_id, messages in session_messages.items()
        ]
    }

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Export file saved to {output_path}")
    return output_path


def display_commits_for_selection(commits: List[UnpushedCommit]) -> None:
    """
    显示 commits 供用户选择。

    Args:
        commits: UnpushedCommit 列表
    """
    print(f"\n📋 Available commits ({len(commits)}):\n")

    for commit in commits:
        # Display format: [index] hash - message
        print(f"  [{commit.index}] {commit.hash} - {commit.message}")

        # Show user request if available
        if commit.user_request:
            request_preview = commit.user_request[:60]
            if len(commit.user_request) > 60:
                request_preview += "..."
            print(f"      └─ {request_preview}")

    print()


def export_shares_command(
    indices: Optional[str] = None,
    username: Optional[str] = None,
    repo_root: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> int:
    """
    Main entry point for export shares command.

    Allows users to select commits and export their chat history to JSON files.

    Args:
        indices: Commit indices to export (e.g., "1,3,5-7"). If None, prompts user.
        username: Username for the export. If None, uses system username.
        repo_root: Path to user's project root (auto-detected if None)
        output_dir: Custom output directory. If None, uses ~/.aline/{project}/share/

    Returns:
        0 on success, 1 on error
    """
    logger.info("======== Export shares command started ========")

    # Auto-detect user project root if not provided
    if repo_root is None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            repo_root = Path(result.stdout.strip())
            logger.debug(f"Detected user project root: {repo_root}")
        except subprocess.CalledProcessError:
            print("Error: Not in a git repository", file=sys.stderr)
            logger.error("Not in a git repository")
            return 1

    # Get shadow git repository path
    from .. import get_realign_dir
    shadow_dir = get_realign_dir(repo_root)
    shadow_git = shadow_dir

    # Verify shadow git exists
    if not shadow_git.exists():
        print(f"Error: ReAlign repository not found at {shadow_git}", file=sys.stderr)
        print("Run 'aline init' first to initialize the repository.", file=sys.stderr)
        logger.error(f"Shadow git not found at {shadow_git}")
        return 1

    # Check if it's a git repository
    git_dir = shadow_git / '.git'
    if not git_dir.exists():
        print(f"Error: {shadow_git} is not a git repository", file=sys.stderr)
        print("Run 'aline init' first to initialize the repository.", file=sys.stderr)
        logger.error(f"No .git found in {shadow_git}")
        return 1

    logger.info(f"Using shadow git repository: {shadow_git}")

    # Get username
    if username is None:
        username = os.environ.get('USER') or os.environ.get('USERNAME') or 'user'

    logger.debug(f"Using username: {username}")

    # Set output directory
    if output_dir is None:
        output_dir = shadow_dir / "share"

    logger.debug(f"Output directory: {output_dir}")

    # Get all unpushed commits from shadow git
    try:
        all_commits = get_unpushed_commits(shadow_git)
    except Exception as e:
        print(f"Error: Failed to get commits: {e}", file=sys.stderr)
        logger.error(f"Failed to get commits: {e}", exc_info=True)
        return 1

    if not all_commits:
        print("No unpushed commits found. Nothing to export.", file=sys.stderr)
        logger.info("No unpushed commits found")
        return 1

    # Get commit selection
    if indices is None:
        # Interactive mode: display commits and prompt user
        display_commits_for_selection(all_commits)

        print("Enter commit indices to export (e.g., '1,3,5-7' or 'all'):")
        indices_input = input("Indices: ").strip()

        if not indices_input:
            print("No commits selected. Exiting.")
            logger.info("No commits selected by user")
            return 0
    else:
        indices_input = indices

    # Parse indices
    try:
        if indices_input.lower() == "all":
            indices_list = [c.index for c in all_commits]
        else:
            indices_list = parse_commit_indices(indices_input)
    except ValueError as e:
        print(f"Error: Invalid indices format: {e}", file=sys.stderr)
        logger.error(f"Invalid indices format: {e}")
        return 1

    # Validate indices
    max_index = len(all_commits)
    invalid_indices = [i for i in indices_list if i < 1 or i > max_index]
    if invalid_indices:
        print(f"Error: Invalid indices (out of range 1-{max_index}): {invalid_indices}", file=sys.stderr)
        logger.error(f"Invalid indices: {invalid_indices}")
        return 1

    # Get selected commits
    selected_commits = [c for c in all_commits if c.index in indices_list]

    logger.info(f"Selected {len(selected_commits)} commit(s) to export")

    # Merge messages from commits
    print(f"\n🔄 Extracting chat history from {len(selected_commits)} commit(s)...")
    try:
        session_messages = merge_messages_from_commits(selected_commits, shadow_git)
    except Exception as e:
        print(f"\nError: Failed to extract messages: {e}", file=sys.stderr)
        logger.error(f"Failed to extract messages: {e}", exc_info=True)
        return 1

    if not session_messages:
        print("\nWarning: No chat history found in selected commits.", file=sys.stderr)
        logger.warning("No chat history found in selected commits")
        return 1

    # Save export file
    try:
        output_path = save_export_file(session_messages, output_dir, username)
    except Exception as e:
        print(f"\nError: Failed to save export file: {e}", file=sys.stderr)
        logger.error(f"Failed to save export file: {e}", exc_info=True)
        return 1

    # Success message
    total_messages = sum(len(msgs) for msgs in session_messages.values())
    print(f"\n✅ Successfully exported {len(session_messages)} session(s)")
    print(f"📁 Export file: {output_path}")
    print(f"📊 Total messages: {total_messages}")
    print()

    logger.info(f"======== Export shares command completed: {output_path} ========")
    return 0


def encrypt_conversation_data(data: dict, password: str) -> dict:
    """
    使用 AES-256-GCM 加密对话数据

    Args:
        data: 要加密的数据字典
        password: 加密密码

    Returns:
        包含加密数据的字典: {encrypted_data, salt, nonce, password_hash}
    """
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography package not installed. Run: pip install cryptography")

    # 生成盐值和随机数
    salt = os.urandom(32)
    nonce = os.urandom(12)

    # 密钥派生
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=1000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())

    # 加密数据
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()

    json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    ciphertext = encryptor.update(json_data) + encryptor.finalize()

    # 添加认证标签
    ciphertext_with_tag = ciphertext + encryptor.tag

    # 计算密码 hash
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    return {
        "encrypted_data": base64.b64encode(ciphertext_with_tag).decode('ascii'),
        "salt": base64.b64encode(salt).decode('ascii'),
        "nonce": base64.b64encode(nonce).decode('ascii'),
        "password_hash": password_hash
    }


def upload_to_backend(
    encrypted_payload: dict,
    metadata: dict,
    backend_url: str
) -> dict:
    """
    上传加密数据到后端服务器

    Args:
        encrypted_payload: 加密后的数据
        metadata: 元数据
        backend_url: 后端 URL

    Returns:
        包含 share_id 和 share_url 的字典
    """
    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx package not installed. Run: pip install httpx")

    try:
        response = httpx.post(
            f"{backend_url}/api/share/create",
            json={
                "encrypted_payload": encrypted_payload,
                "metadata": metadata
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Upload failed: {e}")
        raise RuntimeError(f"Failed to upload to server: {e}")


def clean_text_for_prompt(text: str) -> str:
    """
    清理文本中的控制字符，使其适合在 LLM prompt 中使用

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    # 替换控制字符为空格或删除
    import re
    # 保留换行符和制表符，删除其他控制字符
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # 将多个连续空格合并为一个
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def generate_ui_metadata_with_llm(
    conversation_data: dict,
    selected_commits: List,
    provider: str = "auto",
    preset_id: str = "default"
) -> Tuple[Optional[dict], Optional[dict]]:
    """
    使用 LLM 根据对话内容生成个性化的 UI 元数据

    Args:
        conversation_data: 对话数据字典 {username, time, sessions}
        selected_commits: 选中的 UnpushedCommit 列表
        provider: LLM provider ("auto", "claude", "openai")
        preset_id: Prompt preset ID，用于调整生成风格

    Returns:
        Tuple[ui_metadata, debug_info]
        - ui_metadata: UI 元数据字典，包含 title, welcome, description, preset_questions
        - debug_info: {system_prompt, user_prompt, response_text, provider} 或 None
        如果生成失败则都返回 None
    """
    logger.info(f"Generating UI metadata with LLM (preset: {preset_id})")

    # 构建对话内容摘要
    sessions = conversation_data.get("sessions", [])
    total_messages = sum(len(s.get("messages", [])) for s in sessions)

    # 提取 commit 中的 LLM summary 和 user request
    commit_summaries = []
    user_requests = []

    for commit in selected_commits:
        if commit.llm_summary and commit.llm_summary.strip():
            # 清理控制字符
            cleaned_summary = clean_text_for_prompt(commit.llm_summary)
            commit_summaries.append(cleaned_summary)
        if commit.user_request and commit.user_request.strip():
            # 清理控制字符并截取前300字符
            cleaned_request = clean_text_for_prompt(commit.user_request[:300])
            user_requests.append(cleaned_request)

    # 如果没有 commit summary，回退到提取消息样本
    if not commit_summaries:
        logger.warning("No commit summaries found, falling back to message samples")
        user_messages = []
        assistant_messages = []

        for session in sessions[:5]:  # 只看前5个session
            for msg in session.get("messages", [])[:10]:  # 每个session前10条消息
                content = msg.get("content", "")
                if isinstance(content, str) and content.strip():
                    # 清理控制字符并截取
                    cleaned_content = clean_text_for_prompt(content[:200])
                    if msg.get("role") == "user":
                        user_messages.append(cleaned_content)
                    elif msg.get("role") == "assistant":
                        assistant_messages.append(cleaned_content)

    # 根据 preset_id 定制 system_prompt
    preset_configs = {
        "default": {
            "role_description": "a general-purpose conversation assistant",
            "title_style": "a neutral, descriptive summary of the topic",
            "welcome_tone": "friendly and informative, with a brief overview of the conversation",
            "description_focus": "what information can be found and how the assistant can help",
            "question_angles": [
                "high-level summary",
                "technical or implementation details",
                "decision-making or reasoning",
                "results, impact, or follow-up"
            ]
        },
        "work-report": {
            "role_description": "a professional work report agent representing the user to colleagues/managers",
            "title_style": "a professional, achievement-oriented summary (e.g., 'Progress on Project X', 'Completed Tasks for Week Y')",
            "welcome_tone": "professional and confident, highlighting accomplishments and progress",
            "description_focus": "what work was done, what value was created, and how the assistant represents the user's contributions",
            "question_angles": [
                "overall progress and achievements",
                "technical solutions implemented",
                "challenges overcome and decisions made",
                "next steps and impact on project goals"
            ]
        },
        "knowledge-agent": {
            "role_description": "a knowledge-sharing agent representing the user's deep thinking as founder/architect/author",
            "title_style": "a thought-provoking, conceptual title (e.g., 'Design Philosophy of Feature X', 'Architectural Decisions for System Y')",
            "welcome_tone": "insightful and educational, emphasizing the thinking process and context behind decisions",
            "description_focus": "the knowledge and insights shared, the reasoning behind decisions, and how the assistant helps others understand the user's thought process",
            "question_angles": [
                "core concepts and philosophy",
                "design rationale and trade-offs",
                "key insights and learning",
                "practical implications and applications"
            ]
        },
        "personality-analyzer": {
            "role_description": "a personality analysis assistant that understands the user's characteristics based on conversation",
            "title_style": "an analytical, personality-focused title (e.g., 'Minhao's Working Style Analysis', 'Communication Pattern Insights')",
            "welcome_tone": "analytical yet friendly, introducing what aspects of personality can be explored",
            "description_focus": "what personality traits, working styles, and communication patterns can be discovered from the conversation",
            "question_angles": [
                "overall personality traits and characteristics",
                "working style and approach to problem-solving",
                "communication patterns and preferences",
                "strengths, growth areas, and unique qualities"
            ]
        }
    }

    # 获取 preset 配置，如果没有则使用默认
    preset_config = preset_configs.get(preset_id, preset_configs["default"])

    # 构建 LLM prompt
    system_prompt = f"""You are a conversation interface copy generator for {preset_config['role_description']}.

Your task is to analyze a given conversation history and generate
personalized UI copy for a chat-based assistant that helps users
understand and explore that conversation.

Return the result strictly in JSON format:

{{
  "title": "A highly abstract and concise title (30–50 characters) that is {preset_config['title_style']}.",

  "welcome": "A welcome message (60-120 characters) that is {preset_config['welcome_tone']}.
              The message should provide context about what this conversation contains and set the right tone.",

  "description": "A clear description (30-80 characters) that explains {preset_config['description_focus']}.",

  "preset_questions": [
    "Question 1: About {preset_config['question_angles'][0]} (15–30 characters)",
    "Question 2: About {preset_config['question_angles'][1]} (15–30 characters)",
    "Question 3: About {preset_config['question_angles'][2]} (15–30 characters)",
    "Question 4: About {preset_config['question_angles'][3]} (15–30 characters)"
  ]
}}

Requirements:
1. The title must align with the preset's purpose and tone.
2. The welcome message should match the preset's role and create appropriate expectations.
3. The description should clearly explain the assistant's specific purpose for this preset.
4. Preset questions must be based on the actual conversation content, concrete, and useful from the specified angles.
5. All text must be in English or Chinese, depending on the conversation language.
6. Output JSON only. Do not include any additional explanation or text."""

    # 构建 user prompt - 优先使用 commit summaries
    if commit_summaries:
        user_prompt = f"""Analyze the following conversation history and generate UI copy:

Number of sessions: {len(sessions)}
Total messages: {total_messages}
Number of commits included: {len(commit_summaries)}

LLM summaries from each commit:
{chr(10).join(f"{i+1}. {summary}" for i, summary in enumerate(commit_summaries))}

User's main requests:
{chr(10).join(f"- {req}" for req in user_requests[:10]) if user_requests else "None"}

Return the UI copy in JSON format."""
    else:
        # 回退到使用消息样本
        user_prompt = f"""Analyze the following conversation history and generate UI copy:

Number of sessions: {len(sessions)}
Total messages: {total_messages}

User message samples:
{chr(10).join(user_messages[:10])}

Assistant reply samples:
{chr(10).join(assistant_messages[:10])}

Return the UI copy in JSON format."""

    # 尝试调用 LLM
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    try_claude = provider in ("auto", "claude")
    try_openai = provider in ("auto", "openai")

    # 尝试 Claude
    if try_claude and anthropic_key:
        print("   → Generating UI metadata with Anthropic Claude...", file=sys.stderr)
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)

            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            response_text = response.content[0].text.strip()
            logger.debug(f"Claude response: {response_text}")

            # 解析 JSON
            json_str = response_text
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    json_str = response_text[json_start:json_end].strip()

            # 清理控制字符，避免 JSON 解析错误
            import re
            # 移除非法的控制字符，但保留合法的空白字符（空格、制表符、换行）
            json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)

            ui_metadata = json.loads(json_str)
            print("   ✅ UI metadata generated successfully with Claude", file=sys.stderr)

            # Return with debug info
            debug_info = {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_text": response_text,
                "provider": "claude"
            }
            return ui_metadata, debug_info

        except ImportError:
            if provider == "claude":
                print("   ❌ Anthropic package not installed", file=sys.stderr)
                return None, None
            print("   ⚠️  Anthropic package not installed, trying OpenAI...", file=sys.stderr)
        except Exception as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            if provider == "claude":
                print(f"   ❌ Claude API error: {e}", file=sys.stderr)
                return None, None
            print(f"   ⚠️  Claude failed, trying OpenAI...", file=sys.stderr)

    # 尝试 OpenAI
    if try_openai and openai_key:
        print("   → Generating UI metadata with OpenAI...", file=sys.stderr)
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            response_text = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI response: {response_text}")

            # 解析 JSON
            json_str = response_text
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    json_str = response_text[json_start:json_end].strip()

            # 清理控制字符，避免 JSON 解析错误
            import re
            # 移除非法的控制字符，但保留合法的空白字符（空格、制表符、换行）
            json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)

            ui_metadata = json.loads(json_str)
            print("   ✅ UI metadata generated successfully with OpenAI", file=sys.stderr)

            # Return with debug info
            debug_info = {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_text": response_text,
                "provider": "openai"
            }
            return ui_metadata, debug_info

        except ImportError:
            print("   ❌ OpenAI package not installed", file=sys.stderr)
            return None, None
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            print(f"   ❌ OpenAI API error: {e}", file=sys.stderr)
            return None, None

    # 没有可用的 API
    logger.warning("No LLM API keys available for UI metadata generation")
    print("   ⚠️  No LLM API keys configured, using default UI text", file=sys.stderr)
    return None, None


def save_export_log(
    conversation_data: dict,
    llm_prompts: Optional[dict],
    llm_response: Optional[str],
    username: str,
    shadow_dir: Path
) -> Path:
    """
    保存导出日志

    Args:
        conversation_data: 分享的对话数据
        llm_prompts: LLM prompts字典 {system_prompt, user_prompt}
        llm_response: LLM的原始回答
        username: 用户名
        shadow_dir: ReAlign目录 (~/.aline/{project}/)

    Returns:
        保存的日志文件路径
    """
    # 创建日志目录
    log_dir = shadow_dir / "share" / "export_logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"{username}_{timestamp}.log.json"

    # 构建日志内容
    log_content = {
        "export_time": datetime.now().isoformat(),
        "username": username,
        "conversation_data": conversation_data,
        "llm_generation": {
            "prompts": llm_prompts,
            "response": llm_response
        } if llm_prompts else None
    }

    # 保存
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_content, f, indent=2, ensure_ascii=False)

    return log_file


def display_selection_statistics(
    selected_commits: List[UnpushedCommit],
    session_messages: Dict[str, List[dict]]
) -> None:
    """
    显示选择的统计信息

    Args:
        selected_commits: 选中的commits
        session_messages: 合并后的session消息
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
    except ImportError:
        # Fallback to plain text if rich is not available
        print(f"\n📊 Selection Summary:")
        print(f"  Commits: {len(selected_commits)}")
        print(f"  Sessions: {len(session_messages)}")
        total_messages = sum(len(msgs) for msgs in session_messages.values())
        print(f"  Messages: {total_messages}")
        return

    console = Console()

    # 计算统计信息
    total_sessions = len(session_messages)
    total_messages = sum(len(msgs) for msgs in session_messages.values())

    # 消息角色分布
    user_messages = 0
    assistant_messages = 0
    other_messages = 0

    for messages in session_messages.values():
        for msg in messages:
            role = msg.get('role', 'unknown')
            if role == 'user':
                user_messages += 1
            elif role == 'assistant':
                assistant_messages += 1
            else:
                other_messages += 1

    # 时间范围
    all_timestamps = []
    for messages in session_messages.values():
        for msg in messages:
            if 'timestamp' in msg:
                ts_str = msg['timestamp']
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    all_timestamps.append(ts)
                except:
                    pass

    time_info = ""
    if all_timestamps:
        earliest = min(all_timestamps)
        latest = max(all_timestamps)
        duration = latest - earliest

        time_info = f"""
[bold]Time Range:[/bold]
  {earliest.strftime('%Y-%m-%d %H:%M')} → {latest.strftime('%Y-%m-%d %H:%M')}
  Duration: {duration.days}d {duration.seconds//3600}h {(duration.seconds%3600)//60}m
"""

    # 构建统计文本
    stats_text = f"""[bold cyan]Commits Selected:[/bold cyan] {len(selected_commits)}

[bold green]Sessions:[/bold green] {total_sessions}

[bold yellow]Messages:[/bold yellow] {total_messages}
  ├─ User:      {user_messages}
  ├─ Assistant: {assistant_messages}"""

    if other_messages > 0:
        stats_text += f"\n  └─ Other:     {other_messages}"

    if time_info:
        stats_text += "\n" + time_info

    panel = Panel(
        stats_text,
        title="[bold]📊 Selection Summary[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)


def display_session_preview(
    session_messages: Dict[str, List[dict]],
    max_sessions: int = 10
) -> None:
    """
    显示session预览

    Args:
        session_messages: {session_id: [messages]}
        max_sessions: 最多显示的session数量
    """
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        # Fallback to plain text
        print(f"\n📝 Sessions to be shared ({len(session_messages)} total):")
        for i, (session_id, messages) in enumerate(list(session_messages.items())[:max_sessions], 1):
            print(f"  {i}. {session_id[-25:] if len(session_id) > 25 else session_id} ({len(messages)} messages)")
        if len(session_messages) > max_sessions:
            print(f"  ... and {len(session_messages) - max_sessions} more sessions")
        return

    console = Console()

    total_sessions = len(session_messages)
    showing = min(total_sessions, max_sessions)

    table = Table(
        title=f"📝 Session Preview (showing {showing} of {total_sessions})"
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Session ID", style="cyan", width=25)
    table.add_column("Msgs", justify="right", width=6)
    table.add_column("First User Message", style="dim", no_wrap=False)

    for i, (session_id, messages) in enumerate(
        list(session_messages.items())[:max_sessions], 1
    ):
        # 获取第一条用户消息
        first_msg_preview = "[No user messages]"
        for msg in messages[:10]:
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                if isinstance(content, str) and content.strip():
                    first_msg_preview = content[:60]
                    if len(content) > 60:
                        first_msg_preview += "..."
                    break

        # 截断session ID用于显示
        session_display = session_id[-25:] if len(session_id) > 25 else session_id

        table.add_row(
            str(i),
            session_display,
            str(len(messages)),
            first_msg_preview
        )

    if total_sessions > max_sessions:
        table.add_row(
            "...",
            f"[{total_sessions - max_sessions} more sessions]",
            "...",
            "..."
        )

    console.print(table)


def save_preview_json(
    conversation_data: dict,
    username: str
) -> Path:
    """
    保存预览JSON到临时位置

    Args:
        conversation_data: 完整的对话数据
        username: 用户名(用于文件名)

    Returns:
        Path: 保存的预览文件路径
    """
    import tempfile

    # 创建临时目录
    temp_dir = Path(tempfile.gettempdir()) / "aline_previews"
    temp_dir.mkdir(exist_ok=True, parents=True)

    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    preview_path = temp_dir / f"{username}_preview_{timestamp}.json"

    # 保存并格式化
    with open(preview_path, 'w', encoding='utf-8') as f:
        json.dump(conversation_data, f, indent=2, ensure_ascii=False)

    return preview_path


def display_ui_metadata_preview(ui_metadata: dict) -> None:
    """
    显示UI metadata预览

    Args:
        ui_metadata: UI metadata字典
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
    except ImportError:
        # Fallback to plain text
        print("\n🎨 Generated UI Content:")
        print(f"  Title: {ui_metadata.get('title', '[Not generated]')}")
        print(f"  Welcome: {ui_metadata.get('welcome', '[Not generated]')}")
        print(f"  Description: {ui_metadata.get('description', '[Not generated]')}")
        questions = ui_metadata.get('preset_questions', [])
        if questions:
            print("  Preset Questions:")
            for i, q in enumerate(questions, 1):
                print(f"    {i}. {q}")
        return

    console = Console()

    console.print("\n[bold cyan]🎨 Generated UI Content[/bold cyan]\n")

    # Title
    console.print(Panel(
        ui_metadata.get('title', '[Not generated]'),
        title="[bold]Title[/bold]",
        border_style="green",
        padding=(1, 2)
    ))

    # Welcome message
    console.print(Panel(
        ui_metadata.get('welcome', '[Not generated]'),
        title="[bold]Welcome Message[/bold]",
        border_style="blue",
        padding=(1, 2)
    ))

    # Description
    console.print(Panel(
        ui_metadata.get('description', '[Not generated]'),
        title="[bold]Description[/bold]",
        border_style="yellow",
        padding=(1, 2)
    ))

    # Preset questions
    questions = ui_metadata.get('preset_questions', [])
    if questions:
        questions_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
    else:
        questions_text = "[No questions generated]"

    console.print(Panel(
        questions_text,
        title="[bold]Preset Questions[/bold]",
        border_style="magenta",
        padding=(1, 2)
    ))


def prompt_ui_metadata_editing(ui_metadata: dict) -> dict:
    """
    提示用户确认或编辑UI metadata

    Args:
        ui_metadata: 生成的metadata

    Returns:
        dict: 更新后的metadata
    """
    try:
        from rich.console import Console
        from rich.prompt import Prompt, Confirm
    except ImportError:
        # Fallback: just return original if rich is not available
        print("\n💡 Rich library not available for interactive editing. Using generated content.")
        return ui_metadata

    console = Console()

    # 询问是否要编辑
    console.print()
    if not Confirm.ask(
        "[yellow]Would you like to review and edit this content?[/yellow]",
        default=False
    ):
        console.print("[green]✓ Using generated content as-is[/green]")
        return ui_metadata

    console.print("\n[dim]Press Enter to keep current value, or type new value:[/dim]\n")

    edited = {}

    # Title
    console.print(f"[bold cyan]Title:[/bold cyan]")
    console.print(f"  Current: {ui_metadata.get('title', '')}")
    new_title = Prompt.ask("  New value", default="")
    edited['title'] = new_title if new_title else ui_metadata.get('title', '')

    # Welcome
    console.print(f"\n[bold cyan]Welcome Message:[/bold cyan]")
    console.print(f"  Current: {ui_metadata.get('welcome', '')}")
    new_welcome = Prompt.ask("  New value", default="")
    edited['welcome'] = new_welcome if new_welcome else ui_metadata.get('welcome', '')

    # Description
    console.print(f"\n[bold cyan]Description:[/bold cyan]")
    console.print(f"  Current: {ui_metadata.get('description', '')}")
    new_desc = Prompt.ask("  New value", default="")
    edited['description'] = new_desc if new_desc else ui_metadata.get('description', '')

    # Questions
    questions = ui_metadata.get('preset_questions', [])
    edited['preset_questions'] = []

    console.print(f"\n[bold cyan]Preset Questions:[/bold cyan]")
    for i, q in enumerate(questions, 1):
        console.print(f"  Question {i}: {q}")
        new_q = Prompt.ask(f"  New value", default="")
        edited['preset_questions'].append(new_q if new_q else q)

    console.print("\n[green]✓ Content updated[/green]")
    return edited


def display_share_result(
    share_url: str,
    password: str,
    expiry_days: int,
    max_views: int,
    admin_token: Optional[str] = None
) -> None:
    """
    显示分享创建结果

    Args:
        share_url: 分享URL
        password: 加密密码
        expiry_days: 过期天数
        max_views: 最大浏览次数
        admin_token: 管理员token(可选)
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
    except ImportError:
        # Fallback to plain text
        print("\n╭────────────────────────────────────────╮")
        print("│  ✅ Share Created Successfully!        │")
        print("╰────────────────────────────────────────╯\n")
        print(f"🔗 Share URL: {share_url}")
        print(f"🔑 Password: {password}")
        print(f"📅 Expires: {expiry_days} days")
        print(f"👁️  Max views: {max_views}")
        if admin_token:
            print(f"\n📊 Admin token: {admin_token}")
            print(f"   View stats at: {share_url}/stats?token={admin_token}")
        print("\n💡 Share this URL and password with your team!")
        return

    console = Console()

    # 成功标题
    console.print("\n")
    success_text = Text("✅ Share Created Successfully!", style="bold green")
    success_panel = Panel(
        success_text,
        border_style="green",
        padding=(1, 4)
    )
    console.print(success_panel)

    # 分享详情
    share_info = f"""[bold cyan]🔗 Share URL:[/bold cyan]
{share_url}

[bold yellow]🔑 Password:[/bold yellow]
{password}

[bold blue]📅 Expires:[/bold blue] {expiry_days} days from now
[bold magenta]👁️  Max Views:[/bold magenta] {max_views} views"""

    info_panel = Panel(
        share_info,
        title="[bold white]Share Details[/bold white]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(info_panel)

    # Admin token (如果有)
    if admin_token:
        admin_info = f"""[bold]Admin Token:[/bold]
{admin_token}

[bold]Stats URL:[/bold]
{share_url}/stats?token={admin_token}

[dim]Use this to view access statistics and manage the share[/dim]"""

        admin_panel = Panel(
            admin_info,
            title="[bold yellow]Admin Access[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print(admin_panel)

    # 使用说明
    instructions = """[bold green]How to Share:[/bold green]

1. Copy the URL and password above
2. Send them to your team (separately for security)
3. Recipients can access the interactive chatbot
4. They'll need the password to decrypt

[dim]💡 Tip: Send URL via Slack, password via DM[/dim]"""

    instructions_panel = Panel(
        instructions,
        title="[bold white]Next Steps[/bold white]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(instructions_panel)
    console.print()


def export_shares_interactive_command(
    indices: Optional[str] = None,
    password: Optional[str] = None,
    expiry_days: int = 7,
    max_views: int = 100,
    enable_preview: bool = True,
    backend_url: Optional[str] = None,
    repo_root: Optional[Path] = None,
    preset: Optional[str] = None,
    enable_mcp: bool = True
) -> int:
    """
    交互式导出对话历史并生成分享链接

    Args:
        indices: Commit indices to export
        password: 加密密码 (如果为 None 则自动生成)
        expiry_days: 过期天数
        max_views: 最大访问次数
        enable_preview: 是否启用UI预览和编辑 (默认: True)
        backend_url: 后端服务器 URL
        repo_root: 项目根目录
        preset: Prompt preset ID (如果为 None 则交互式选择)
        enable_mcp: 是否启用MCP agent-to-agent通信 (默认: True)

    Returns:
        0 on success, 1 on error
    """
    logger.info("======== Interactive export shares command started ========")

    # Check dependencies
    if not CRYPTO_AVAILABLE:
        print("❌ Error: cryptography package not installed", file=sys.stderr)
        print("Install it with: pip install cryptography", file=sys.stderr)
        return 1

    if not HTTPX_AVAILABLE:
        print("❌ Error: httpx package not installed", file=sys.stderr)
        print("Install it with: pip install httpx", file=sys.stderr)
        return 1

    # Get backend URL
    if backend_url is None:
        # Try to load from config
        from ..config import ReAlignConfig
        if repo_root is None:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                repo_root = Path(result.stdout.strip())
            except subprocess.CalledProcessError:
                repo_root = Path.cwd()

        config = ReAlignConfig.load()
        backend_url = config.share_backend_url

    print("\n╭────────────────────────────────────────╮")
    print("│  ReAlign Interactive Share Export      │")
    print("╰────────────────────────────────────────╯\n")

    # Step 1: Select commits (reuse existing logic)
    if repo_root is None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            repo_root = Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            print("Error: Not in a git repository", file=sys.stderr)
            return 1

    from .. import get_realign_dir
    shadow_dir = get_realign_dir(repo_root)
    shadow_git = shadow_dir

    if not shadow_git.exists() or not (shadow_git / '.git').exists():
        print(f"Error: ReAlign not initialized. Run 'aline init' first.", file=sys.stderr)
        return 1

    # Get commits
    try:
        all_commits = get_unpushed_commits(shadow_git)
    except Exception as e:
        print(f"Error: Failed to get commits: {e}", file=sys.stderr)
        return 1

    if not all_commits:
        print("No unpushed commits found. Nothing to export.", file=sys.stderr)
        return 1

    # Display and select commits
    if indices is None:
        display_commits_for_selection(all_commits)
        print("Enter commit indices to export (e.g., '1,3,5-7' or 'all'):")
        indices = input("Indices: ").strip()

        if not indices:
            print("No commits selected. Exiting.")
            return 0

    # Parse indices
    try:
        if indices.lower() == "all":
            indices_list = [c.index for c in all_commits]
        else:
            indices_list = parse_commit_indices(indices)
    except ValueError as e:
        print(f"Error: Invalid indices format: {e}", file=sys.stderr)
        return 1

    # Get selected commits
    selected_commits = [c for c in all_commits if c.index in indices_list]

    # Step 2: Extract messages
    print(f"\n🔄 Extracting chat history from {len(selected_commits)} commit(s)...")
    try:
        session_messages = merge_messages_from_commits(selected_commits, shadow_git)
    except Exception as e:
        print(f"\nError: Failed to extract messages: {e}", file=sys.stderr)
        return 1

    if not session_messages:
        print("\nWarning: No chat history found in selected commits.", file=sys.stderr)
        return 1

    # Build conversation data
    username = os.environ.get('USER') or os.environ.get('USERNAME') or 'anonymous'
    conversation_data = {
        "username": username,
        "time": datetime.now().isoformat(),
        "sessions": [
            {
                "session_id": session_id,
                "messages": messages
            }
            for session_id, messages in session_messages.items()
        ]
    }

    total_messages = sum(len(msgs) for msgs in session_messages.values())
    print(f"✅ Extracted {len(session_messages)} session(s) with {total_messages} messages")

    # NEW: Display selection statistics
    print()
    display_selection_statistics(selected_commits, session_messages)

    # NEW: Display session preview
    print()
    display_session_preview(session_messages)

    # NEW: Save preview JSON
    try:
        preview_path = save_preview_json(conversation_data, username)
        try:
            from rich.console import Console
            console = Console()
            console.print(f"\n💾 Preview saved: [cyan]{preview_path}[/cyan]")
            console.print("   You can inspect the full data before encryption.\n")
        except ImportError:
            print(f"\n💾 Preview saved: {preview_path}")
            print("   You can inspect the full data before encryption.\n")
    except Exception as e:
        logger.warning(f"Failed to save preview JSON: {e}")
        # Don't fail the export if preview save fails

    # Step 3: Select prompt preset
    from ..prompts import get_all_presets, get_preset_by_id, display_preset_menu, prompt_for_custom_instructions

    selected_preset = None
    custom_instructions = ""

    if preset:
        # Use preset specified via command line
        selected_preset = get_preset_by_id(preset)
        if not selected_preset:
            print(f"\n❌ Error: Preset '{preset}' not found", file=sys.stderr)
            print("Available presets:", file=sys.stderr)
            all_presets = get_all_presets()
            for p in all_presets:
                print(f"  - {p.id}: {p.name}", file=sys.stderr)
            return 1
        print(f"\n✓ Using preset: {selected_preset.name} ({selected_preset.id})")
    else:
        # Interactive preset selection
        all_presets = get_all_presets()
        print(display_preset_menu(all_presets))

        while True:
            try:
                selection = input("Enter preset number or ID [1]: ").strip()
                if not selection:
                    selection = "1"

                # Try parsing as index first
                try:
                    idx = int(selection)
                    from ..prompts import get_preset_by_index
                    selected_preset = get_preset_by_index(idx)
                    if not selected_preset:
                        print(f"Invalid index. Please enter 1-{len(all_presets)}")
                        continue
                except ValueError:
                    # Not a number, try as ID
                    selected_preset = get_preset_by_id(selection)
                    if not selected_preset:
                        print(f"Invalid preset ID: {selection}")
                        continue

                print(f"\n✓ Selected: {selected_preset.name}")
                break

            except KeyboardInterrupt:
                print("\n\nExport cancelled.")
                return 0

    # Collect custom instructions if allowed
    if selected_preset.allow_custom_instructions:
        custom_instructions = prompt_for_custom_instructions(selected_preset)

    # Step 4: Generate UI metadata with LLM
    print("\n🤖 Generating personalized UI content...")
    from ..config import ReAlignConfig
    config = ReAlignConfig.load()
    ui_metadata, llm_debug_info = generate_ui_metadata_with_llm(
        conversation_data,
        selected_commits,
        provider=config.llm_provider,
        preset_id=selected_preset.id
    )

    # NEW: Display and optionally edit UI metadata
    if ui_metadata:
        display_ui_metadata_preview(ui_metadata)

        # Only prompt for editing if enable_preview is True
        if enable_preview:
            try:
                ui_metadata = prompt_ui_metadata_editing(ui_metadata)

                # Show final version
                try:
                    from rich.console import Console
                    console = Console()
                    console.print("\n[bold green]✅ Final UI Content:[/bold green]")
                except ImportError:
                    print("\n✅ Final UI Content:")
                display_ui_metadata_preview(ui_metadata)
            except KeyboardInterrupt:
                # User cancelled during editing
                try:
                    from rich.prompt import Confirm
                    print("\n")
                    if Confirm.ask("[yellow]Cancel export?[/yellow]", default=False):
                        print("Export cancelled.")
                        return 0
                    else:
                        print("Continuing with generated content...")
                except ImportError:
                    print("\nContinuing with generated content...")

        # Add UI metadata with preset information
        if ui_metadata is None:
            ui_metadata = {}
        ui_metadata["prompt_preset"] = {
            "id": selected_preset.id,
            "name": selected_preset.name,
            "custom_instructions": custom_instructions
        }
        conversation_data["ui_metadata"] = ui_metadata

        # Debug logging
        logger.info(f"Added preset to ui_metadata: id={selected_preset.id}, custom_instructions={custom_instructions[:100] if custom_instructions else 'None'}")
        print(f"\n🔍 Debug: Preset info added - ID: {selected_preset.id}, Custom instructions: '{custom_instructions[:50]}{'...' if len(custom_instructions) > 50 else ''}'", file=sys.stderr)
    else:
        # Use default UI metadata if LLM generation failed
        try:
            from rich.console import Console
            console = Console()
            console.print("[yellow]⚠️  Using default UI content[/yellow]")
        except ImportError:
            print("⚠️  Using default UI content")
        # Still add preset information
        conversation_data["ui_metadata"] = {
            "prompt_preset": {
                "id": selected_preset.id,
                "name": selected_preset.name,
                "custom_instructions": custom_instructions
            }
        }

    # Add MCP instructions if enabled
    if enable_mcp:
        conversation_data["ui_metadata"]["mcp_instructions"] = {
            "tool_name": "ask_shared_conversation",
            "usage": "Local AI agents can install the aline MCP server and use the 'ask_shared_conversation' tool to query this conversation programmatically.",
            "installation": {
                "step1": "Install aline: pip install aline",
                "step2": "Add to claude_desktop_config.json:",
                "config": {
                    "mcpServers": {
                        "aline": {
                            "command": "aline-mcp"
                        }
                    }
                },
                "step3": "Restart Claude Desktop"
            },
            "example_usage": "Ask your local Claude agent: 'Use the ask_shared_conversation tool to query this URL with question: ...'"
        }
        logger.info("MCP instructions added to ui_metadata")

    # NEW: Save export log
    try:
        log_file = save_export_log(
            conversation_data=conversation_data,
            llm_prompts={
                "system_prompt": llm_debug_info["system_prompt"],
                "user_prompt": llm_debug_info["user_prompt"]
            } if llm_debug_info else None,
            llm_response=llm_debug_info["response_text"] if llm_debug_info else None,
            username=username,
            shadow_dir=shadow_git
        )
        logger.info(f"Export log saved to: {log_file}")
        try:
            from rich.console import Console
            console = Console()
            console.print(f"\n📝 Export log saved: [cyan]{log_file}[/cyan]\n")
        except ImportError:
            print(f"\n📝 Export log saved: {log_file}\n")
    except Exception as e:
        logger.warning(f"Failed to save export log: {e}")
        # Don't fail the export if log save fails

    # Step 4: Ask if user wants password protection
    use_password = True  # Default
    if password is None:
        try:
            from rich.prompt import Confirm
            print()
            use_password = Confirm.ask(
                "[yellow]🔐 Would you like to protect this share with a password?[/yellow]",
                default=False
            )
        except ImportError:
            # Fallback: ask with plain input
            print("\n🔐 Would you like to protect this share with a password? (y/N): ", end='')
            response = input().strip().lower()
            use_password = (response == 'y' or response == 'yes')

    # Step 5: Generate password or skip encryption
    encrypted_payload = None
    if use_password:
        if password is None:
            # Generate a random password
            password = secrets.token_urlsafe(16)
            print(f"\n🔐 Generated password: {password}")
            print("⚠️  Save this password - you'll need it to access the share!")

        # Encrypt data
        print("\n🔒 Encrypting conversation data...")
        try:
            encrypted_payload = encrypt_conversation_data(conversation_data, password)
        except Exception as e:
            print(f"\nError: Failed to encrypt data: {e}", file=sys.stderr)
            logger.error(f"Encryption failed: {e}", exc_info=True)
            return 1

        print("✅ Encryption complete")
    else:
        print("\n📂 No password protection - data will be accessible to anyone with the link")
        password = None

    # Step 6: Upload to backend
    print(f"\n📤 Uploading to {backend_url}...")

    metadata = {
        "username": username,
        "expiry_days": expiry_days,
        "max_views": max_views
    }

    try:
        # Prepare payload based on whether encryption was used
        if encrypted_payload:
            payload = {"encrypted_payload": encrypted_payload, "metadata": metadata}
        else:
            # No encryption - send conversation data directly
            payload = {"conversation_data": conversation_data, "metadata": metadata}

        response = httpx.post(
            f"{backend_url}/api/share/create",
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        print(f"\n❌ Upload failed: {e}", file=sys.stderr)
        logger.error(f"Upload failed: {e}", exc_info=True)
        return 1

    # Step 7: Display success with beautiful formatting
    display_share_result(
        share_url=result['share_url'],
        password=password,
        expiry_days=expiry_days,
        max_views=max_views,
        admin_token=result.get('admin_token')
    )

    # Display MCP setup instructions if enabled
    if enable_mcp:
        try:
            from rich.console import Console
            from rich.panel import Panel
            console = Console()

            mcp_instructions = f"""[bold green]🤖 MCP Access Enabled![/bold green]

This share can be queried by AI agents using the Model Context Protocol.

[bold]Installation:[/bold]

1. Install aline (if not already installed):
   [cyan]pip install aline[/cyan]

2. Add to Claude Desktop config:
   [dim]~/.config/Claude/claude_desktop_config.json (Linux/Mac)
   or %APPDATA%/Claude/claude_desktop_config.json (Windows)[/dim]

   {{
     "mcpServers": {{
       "aline": {{
         "command": "aline-mcp"
       }}
     }}
   }}

3. Restart Claude Desktop

[bold]Usage Example:[/bold]

In Claude Desktop, say:
[cyan]"Use the ask_shared_conversation tool to query this URL:
{result['share_url']}

Question: What were the main topics discussed?"[/cyan]

{f'[yellow]Password: {password}[/yellow]' if password else '[dim](No password required)[/dim]'}

[dim]💡 Tip: Agents can now directly query this conversation without human intervention![/dim]"""

            mcp_panel = Panel(
                mcp_instructions,
                title="[bold magenta]Agent-to-Agent Communication[/bold magenta]",
                border_style="magenta",
                padding=(1, 2)
            )
            console.print()
            console.print(mcp_panel)
            console.print()

        except ImportError:
            # Fallback to plain text
            print("\n" + "="*60)
            print("🤖 MCP ACCESS ENABLED")
            print("="*60)
            print("\nThis share can be queried by AI agents programmatically.")
            print("\nSetup:")
            print("1. pip install aline")
            print("2. Add to claude_desktop_config.json:")
            print('   {"mcpServers": {"aline": {"command": "aline-mcp"}}}')
            print("3. Restart Claude Desktop")
            print(f"\nShare URL: {result['share_url']}")
            if password:
                print(f"Password: {password}")
            print("\n" + "="*60 + "\n")

    logger.info(f"======== Interactive export completed: {result['share_url']} ========")
    return 0
