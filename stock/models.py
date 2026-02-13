"""
Stock Model

주식 데이터 모델
"""

from typing import List


DEFAULT_INITIAL_PRICE = 0


class Stock:
    """
    주식 모델
    
    실시간 주가 및 가격 히스토리를 관리합니다.
    """
    
    def __init__(
        self,
        name: str,
        code: str,
        initial_price: int = DEFAULT_INITIAL_PRICE
    ):
        """
        Args:
            name: 주식 이름 (예: 삼성전자)
            code: 종목 코드 (예: 005930)
            initial_price: 초기 가격
        """
        self._name = name
        self._code = code
        self._price = initial_price
        self._price_history: List[int] = [self._price]
    
    @property
    def name(self) -> str:
        """주식 이름"""
        return self._name
    
    @property
    def code(self) -> str:
        """종목 코드"""
        return self._code
    
    @property
    def price(self) -> int:
        """현재 가격"""
        return self._price
    
    @property
    def price_history(self) -> List[int]:
        """가격 히스토리 (복사본)"""
        return self._price_history.copy()
    
    def update_price(self, new_price: int):
        """
        가격 업데이트
        
        Args:
            new_price: 새로운 가격
        """
        # 초기 가격이 0이면 첫 실제 가격으로 대체
        if self._price_history[0] == DEFAULT_INITIAL_PRICE:
            self._price_history[0] = new_price
        
        self._price = new_price
        self._price_history.append(self._price)
    
    def __repr__(self) -> str:
        return f"Stock(name='{self._name}', code='{self._code}', price={self._price})"
