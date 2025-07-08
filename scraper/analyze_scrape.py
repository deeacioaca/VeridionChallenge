import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRAPED_CSV = BASE_DIR / "data" / "scraped_data.csv"
INPUT_CSV = BASE_DIR / "data" / "sample-websites.csv"

def compute_metrics():
    df_scraped = pd.read_csv(SCRAPED_CSV)
    df_input = pd.read_csv(INPUT_CSV)

    total_domains = len(df_input)
    scraped_domains = len(df_scraped)

    coverage = scraped_domains / total_domains * 100

    phone_fill = df_scraped['phone_numbers'].apply(lambda x: isinstance(x, str) and x.strip() != "").sum()
    phone_fill_rate = phone_fill / scraped_domains * 100 if scraped_domains else 0

    social_fill = df_scraped['social_links'].apply(lambda x: isinstance(x, str) and x.strip() != "").sum()
    social_fill_rate = social_fill / scraped_domains * 100 if scraped_domains else 0

    address_fill = df_scraped['address'].apply(lambda x: isinstance(x, str) and x.strip() != "").sum()
    address_fill_rate = address_fill / scraped_domains * 100 if scraped_domains else 0

    print("\n📊 Scrape Analysis:")
    print(f"Total domains:       {total_domains}")
    print(f"Successfully scraped: {scraped_domains} ({coverage:.2f}% coverage)")
    print(f"Phone fill rate:     {phone_fill} / {scraped_domains} ({phone_fill_rate:.2f}%)")
    print(f"Social link rate:    {social_fill} / {scraped_domains} ({social_fill_rate:.2f}%)")
    print(f"Address fill rate:    {address_fill} / {scraped_domains} ({address_fill_rate:.2f}%)")

if __name__ == "__main__":
    compute_metrics()
