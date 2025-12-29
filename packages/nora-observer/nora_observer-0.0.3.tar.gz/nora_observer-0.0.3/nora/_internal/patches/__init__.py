"""자동 패치 모듈"""

from typing import List, Callable


def apply_all_patches() -> None:
    """사용 가능한 모든 AI 라이브러리를 자동으로 패치합니다."""
    from .openai_patch import patch_openai
    from .anthropic_patch import patch_anthropic
    from .gemini_patch import patch_gemini

    patches: List[tuple[str, Callable]] = [
        ("OpenAI", patch_openai),
        ("Anthropic", patch_anthropic),
        ("Gemini", patch_gemini),
    ]

    for name, patch_func in patches:
        try:
            patch_func()
        except Exception:
            # 패치 실패는 조용히 처리 (해당 라이브러리가 없을 수 있음)
            pass


__all__ = ["apply_all_patches"]
