from src.scraper import scrape_hashtag
from src.saver import save_to_csv, save_to_json

if __name__ == "__main__":
    hashtag = input("Enter hashtag (without #): ")
    limit = int(input("Limit posts: "))
    results = scrape_hashtag(hashtag, limit)
    save_to_csv(results, hashtag)
    save_to_json(results, hashtag)
