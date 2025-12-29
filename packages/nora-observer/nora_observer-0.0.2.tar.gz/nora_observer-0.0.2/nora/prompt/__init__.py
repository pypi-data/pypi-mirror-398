"""
Nora Prompt API
프롬프트 생성 및 관리 API
"""

from typing import Optional, Dict, Any, List, Union

try:
    import requests
except ImportError:
    requests = None


class PromptAPI:
    """
    프롬프트 관리를 위한 API 클래스
    
    사용법:
        import nora
        
        # nora.init()으로 설정 (api_url을 프롬프트 API URL로도 사용)
        nora.init(
            api_key="YOUR_KEY",
            api_url="https://api.example.com/v1"
        )
        client = nora.Client()
        
        # 새 프롬프트 그룹 생성
        prompt = client.prompt.create(
            group_name="greeting_prompts",
            system_prompt="You are a helpful assistant. Greet users warmly.",
            group_description="Greeting prompt templates",
            variables={"language": "en", "tone": "friendly"},
            message_prompt=[
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi {name}! How can I help you today?"}
            ]
        )
        
        # 프롬프트 버전 업데이트
        updated = client.prompt.update(
            group_name="greeting_prompts",
            system_prompt="You are a professional assistant.",
            is_default=True,
            variables={"language": "en", "tone": "professional"}
        )
        
        # 프롬프트 조회 (기본 버전)
        prompt = client.prompt.get(name="greeting_prompts")
        
        # 프롬프트 조회 (특정 버전)
        prompt = client.prompt.get(name="greeting_prompts", version=2)
        
        # 프롬프트 목록 조회
        prompts = client.prompt.list()
    """
    
    def __init__(self, client: "NoraClient"):
        """
        Args:
            client: NoraClient 인스턴스
        """
        self._client = client
        
        # 전역 설정에서 api_url 가져오기
        from .. import _global_config
        api_url = _global_config.get("api_url")
        
        if api_url:
            self._api_url = api_url.rstrip("/")
        else:
            self._api_url = None
        
    
    def _ensure_configured(self) -> None:
        """API URL이 설정되었는지 확인"""
        if not self._api_url:
            raise ValueError(
                "Prompt API URL이 설정되지 않았습니다. "
                "nora.init(api_key='...', api_url='...')을 먼저 호출하세요."
            )
        if not requests:
            raise ImportError(
                "requests 라이브러리가 필요합니다. 'pip install requests'로 설치하세요."
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        return {
            "Content-Type": "application/json",
            "X-API-KEY": f"{self._client.api_key}",
        }
    

    def create(
        self,
        group_name: str,        
        system_prompt: str,
        group_description: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        message_prompt: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        새로운 프롬프트를 생성합니다.
        Args:
            group_name: 프롬프트 그룹 이름
            system_prompt: 시스템 프롬프트 내용
            group_description: 프롬프트 그룹 설명 (옵션)
            variables: 변수 객체 (옵션)
            message_prompt: 메시지 프롬프트 배열 (옵션)
        Returns:
            생성된 프롬프트 정보
        Raises:
            ValueError: API URL이 설정되지 않은 경우
            requests.HTTPError: API 요청 실패 시
        """
        self._ensure_configured()
        
        payload = {
            "group_name": group_name,
            "system_prompt": system_prompt,
        }
        
        if group_description is not None:
            payload["group_description"] = group_description
        if variables is not None:
            payload["variables"] = variables
        if message_prompt is not None:
            payload["message_prompt"] = message_prompt
        
        create_api_url = f"{self._api_url}/prompt-sdk/save-by-new-group"

        response = requests.post(
            create_api_url,
            json=payload,
            headers=self._get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


    def update(
        self,
        group_name: str,
        system_prompt: str,
        is_default: bool,
        variables: Optional[Dict[str, Any]] = None,
        message_prompt: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        프롬프트 버전을 업데이트합니다.
        
        Args:
            group_name: 프롬프트 그룹 이름
            system_prompt: 시스템 프롬프트 내용
            is_default: 기본 버전으로 설정 여부
            variables: 변수 객체 (옵션)
            message_prompt: 메시지 프롬프트 배열 (옵션)
            **kwargs: 기타 API 파라미터
            
        Returns:
            업데이트된 프롬프트 정보
            
        Raises:
            ValueError: API URL이 설정되지 않은 경우
            requests.HTTPError: API 요청 실패 시
        """
        self._ensure_configured()
        
        payload = {
            "group_name": group_name,
            "system_prompt": system_prompt,
            "is_default": is_default,
        }
        
        if variables is not None:
            payload["variables"] = variables
        if message_prompt is not None:
            payload["message_prompt"] = message_prompt
        
        create_api_url = f"{self._api_url}/prompt-sdk/version-update"

        response = requests.post(
            create_api_url,
            json=payload,
            headers=self._get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    
    def get(self, name: str, version: Union[str, int] = "default") -> Dict[str, Any]:
        """
        특정 프롬프트를 조회합니다.

        Nora Prompt API 사양에 따라 POST로 조회하며,
        이름과 버전으로 프롬프트를 선택합니다.

        Args:
            name: 프롬프트 이름
            version: 프롬프트 버전 ("default" 또는 숫자)

        Returns:
            프롬프트 정보

        Raises:
            ValueError: API URL이 설정되지 않은 경우
            requests.HTTPError: API 요청 실패 시
        """
        self._ensure_configured()

        get_api_url = f"{self._api_url}/prompt-sdk/"

        params = {
            "name": name,
            "version": version,
        }

        response = requests.get(
            get_api_url,
            params=params,
            headers=self._get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    
    def list(
        self,
    ) -> List[Dict[str, Any]]:
        """
        프롬프트 목록을 조회합니다.
        
        Args:
            limit: 최대 조회 개수 (옵션)
            offset: 조회 시작 위치 (옵션)
            tags: 필터링할 태그 목록 (옵션)
            **kwargs: 기타 쿼리 파라미터
            
        Returns:
            프롬프트 목록
            
        Raises:
            ValueError: API URL이 설정되지 않은 경우
            requests.HTTPError: API 요청 실패 시
        """
        self._ensure_configured()
        
        list_api_url = f"{self._api_url}/prompt-sdk/groups"
        response = requests.get(
            list_api_url,
            headers=self._get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


__all__ = ["PromptAPI"]

