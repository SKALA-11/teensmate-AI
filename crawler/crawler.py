from News import News
from Report import Report
from Education import Education

# 데이터 크롤링 코드
def main():
    news_scraper = News()
    news_scraper.run_pipeline()

    report = Report()
    report.run_pipeline()

    education_processor = Education()
    education_processor.run_pipeline()

if __name__ == "__main__":
    main()