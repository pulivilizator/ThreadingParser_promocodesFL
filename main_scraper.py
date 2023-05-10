from engine import DataScraper
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    scraper = DataScraper(headless=True, processes=7)
    scraper.create_driver()
    scraper.scrape_shops()
    scraper.reformat()
    scraper.main()
