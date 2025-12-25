# Path: usekit.help.use_help.py
# -----------------------------------------------------------------------------------------------
#  MOSA Help System - Memory-Oriented Software Architecture Documentation
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from typing import Optional, Literal
import textwrap

from usekit.help.index.topic.help_part1 import (
    HELP_TOPICS,
    HELP_OVERVIEW,
    HELP_ALIAS,
    HELP_ACTION,
)

from usekit.help.index.topic.help_part2 import (
    HELP_PATTERN,
    HELP_WALK,
    HELP_KEYDATA,
)

from usekit.help.index.topic.help_part3 import (    
    HELP_EXAMPLES,
    HELP_QUICK,
)

# ===============================================================================
# Help Display Function
# ===============================================================================

def show_help(topic: Optional[str] = None) -> None:
    """
    MOSA 도움말 표시
    
    Args:
        topic: 도움말 주제 (없으면 전체 개요)
    """
    # ----------------------------------------
    # 1) topic 없으면 전체 개요 출력
    # ----------------------------------------
    if topic is None:
        print(HELP_OVERVIEW)
        print("\n📚 사용 가능한 도움말 주제:")
        print("━" * 74)

        # 정렬된 출력 (일관성 ↑)
        for key, desc in sorted(HELP_TOPICS.items()):
            print(f"  u.help('{key:12s}')  # {desc}")
        return

    # ----------------------------------------
    # 2) topic 존재하는 경우
    # ----------------------------------------
    topic = topic.lower().strip()

    help_map = {
        "overview": HELP_OVERVIEW,
        "alias": HELP_ALIAS,
        "action": HELP_ACTION,
        "pattern": HELP_PATTERN,
        "walk": HELP_WALK,
        "keydata": HELP_KEYDATA,
        "examples": HELP_EXAMPLES,
        "quick": HELP_QUICK,
    }

    if topic in help_map:
        print(help_map[topic])
    else:
        print(f"❌ '{topic}' 주제를 찾을 수 없습니다.\n")
        print("📚 사용 가능한 주제:")
        for key, desc in sorted(HELP_TOPICS.items()):
            print(f"  • {key:12s} - {desc}")

# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "show_help",
]