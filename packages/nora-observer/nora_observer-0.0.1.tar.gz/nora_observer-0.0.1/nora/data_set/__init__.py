"""
Nora DATASET API
DATASET 생성 및 관리 API
"""

from typing import Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import NoraClient


class Dataset_item_list:
    score: Optional[Union[float, str]]
    input: dict
    output: dict


class DataSetAPI:
    """
    DATASET 관리를 위한 API 클래스
    
    사용법:
        import nora
        
        # nora.init()으로 설정 (api_url을 DATASET API URL로도 사용)
        nora.init(
            api_key="YOUR_KEY",
            api_url="https://api.example.com/v1"
        )
        client = nora.Client()
        
        # 데이터셋 생성
        dataset = client.dataset.create(
            dataset_name="my_dataset",
            dataset_item_list=[
                {"input": {"question": "What is AI?"}, "output": {"answer": "AI is..."}, "score": 0.95},
                {"input": {"question": "What is ML?"}, "output": {"answer": "ML is..."}, "score": 0.88}
            ],
            description="QA dataset for training"
        )
        
        # 데이터셋 목록 조회
        datasets = client.dataset.list()
        
        # 특정 데이터셋 조회
        dataset_info = client.dataset.get(dataset_name="my_dataset")
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

    def _get_headers(self) -> dict:
        """
        공통 헤더 생성
        """
        headers = {
            "Content-Type": "application/json",
            "X_API_KEY": f"{self._client.api_key}",
        }
        return headers
    

    def create(
        self,
        name: str,
        dataset_items: List[Dataset_item_list],
        description: Optional[str] = None,
    ) -> dict:
        """
        새로운 DATASET을 생성합니다.
        
        Args:
            name: DATASET 이름
            dataset_itme_list: DATASET 아이템 리스트
            description: DATASET 설명 (옵션)
        
        Returns:
            생성된 DATASET 정보
        """
        import requests
        if not self._api_url:
            raise ValueError(
                "DATASET API URL이 설정되지 않았습니다. "
                "nora.init(api_key='...', api_url='...')을 먼저 호출하세요."
            )
        
        url = f"{self._api_url}/dataset-sdk/"
        payload = {
            "dataset_name": name,
            "dataset_item_list": dataset_items,
            "description": description,
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    

    def list(self) -> dict:
        """
        모든 DATASET 목록을 가져옵니다.
        
        Returns:
            DATASET 목록
        """
        import requests
        if not self._api_url:
            raise ValueError(
                "DATASET API URL이 설정되지 않았습니다. "
                "nora.init(api_key='...', api_url='...')을 먼저 호출하세요."
            )
        
        url = f"{self._api_url}/dataset-sdk/"
        
        response = requests.get(
            url,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get(self, name: str) -> dict:
        """
        DATASET ID로 특정 DATASET 정보를 가져옵니다.
        
        Args:
            dataset_id: DATASET ID
        
        Returns:
            DATASET 정보
        """
        import requests
        if not self._api_url:
            raise ValueError(
                "DATASET API URL이 설정되지 않았습니다. "
                "nora.init(api_key='...', api_url='...')을 먼저 호출하세요."
            )
        
        url = f"{self._api_url}/dataset-sdk/{name}"
        
        response = requests.get(
            url,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()