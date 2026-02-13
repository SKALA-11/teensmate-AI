"""
Data Module

데이터 크롤링 및 전처리 관련 모듈
"""

from data.crawlers.base import BaseCrawler
from data.crawlers.education import EducationCrawler
from data.crawlers.news import NewsCrawler
from data.crawlers.report import ReportCrawler
from data.crawlers.value_chain import ValueChainCrawler

__all__ = [
    "BaseCrawler",
    "EducationCrawler",
    "NewsCrawler",
    "ReportCrawler",
    "ValueChainCrawler",
]
