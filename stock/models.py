"""
Stock & User Models

주식 데이터 모델과 사용자 잔고/포트폴리오 관리
"""

from typing import List, Dict, Tuple
from datetime import datetime

DEFAULT_INITIAL_PRICE = 0
DEFAULT_INITIAL_BALANCE = 10_000_000  # 1000만원


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
        self._price_history: List[int] = []
        self._timestamps: List[datetime] = []

    @property
    def name(self) -> str:
        """주식 이름"""
        return self._name

    @property
    def code(self) -> str:
        """종목 코드"""
        return self._code

    # KIS WebSocket 원본 코드와 호환성을 위한 별칭
    @property
    def id(self) -> str:
        """종목 코드 별칭 (KIS WebSocket 호환)"""
        return self._code

    @property
    def price(self) -> int:
        """현재 가격"""
        return self._price

    @property
    def price_history(self) -> List[int]:
        """가격 히스토리 (복사본)"""
        return self._price_history.copy()

    @property
    def timestamps(self) -> List[datetime]:
        """타임스탬프 히스토리 (복사본)"""
        return self._timestamps.copy()

    @property
    def price_with_times(self) -> List[Tuple[datetime, int]]:
        """(타임스탬프, 가격) 쌍 리스트"""
        return list(zip(self._timestamps, self._price_history))

    def update_price(self, new_price: int):
        """
        가격 업데이트

        Args:
            new_price: 새로운 가격
        """
        self._price = new_price
        self._price_history.append(new_price)
        self._timestamps.append(datetime.now())

    def __repr__(self) -> str:
        return f"Stock(name='{self._name}', code='{self._code}', price={self._price})"


class User:
    """
    사용자 모델

    잔고와 포트폴리오(보유 주식)를 관리합니다.
    """

    def __init__(self, initial_balance: int = DEFAULT_INITIAL_BALANCE):
        """
        Args:
            initial_balance: 초기 잔고 (기본값: 1000만원)
        """
        self._balance = initial_balance
        self._portfolio: Dict[str, int] = {}  # {종목명: 보유수량}

    @property
    def balance(self) -> int:
        """현재 잔고"""
        return self._balance

    @property
    def portfolio(self) -> Dict[str, int]:
        """포트폴리오 (복사본)"""
        return self._portfolio.copy()

    def buy_stock(self, stock_name: str, stock_price: int, quantity: int) -> bool:
        """
        주식 매수

        Args:
            stock_name: 종목명
            stock_price: 현재가
            quantity: 매수 수량

        Returns:
            성공 여부
        """
        if stock_price == 0:
            return False
        if quantity <= 0:
            return False
        total_cost = stock_price * quantity
        if total_cost <= self._balance:
            self._balance -= total_cost
            self._portfolio[stock_name] = self._portfolio.get(stock_name, 0) + quantity
            return True
        return False

    def sell_stock(self, stock_name: str, stock_price: int, quantity: int) -> bool:
        """
        주식 매도

        Args:
            stock_name: 종목명
            stock_price: 현재가
            quantity: 매도 수량

        Returns:
            성공 여부
        """
        if quantity <= 0:
            return False
        if stock_name in self._portfolio and self._portfolio[stock_name] >= quantity:
            self._balance += stock_price * quantity
            self._portfolio[stock_name] -= quantity
            if self._portfolio[stock_name] == 0:
                del self._portfolio[stock_name]
            return True
        return False

    def __repr__(self) -> str:
        return f"User(balance={self._balance:,}, portfolio={self._portfolio})"
