from pathlib import Path
import pandas as pd
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
SCRAPED_DATA = BASE_DIR / "data" / "scraped_data.csv"
SAMPLE = BASE_DIR / "data" / "sample-websites-company-names.csv"
MERGED = BASE_DIR / "data" / "merged_companies.json"

# Extract domain from df1
def extract_domain(url):
    try:
        parsed = urlparse(url).netloc
        return parsed.replace('www.', '')
    except:
        return ''

if __name__ == "__main__":

    # Load both datasets
    df_scraped = pd.read_csv(SCRAPED_DATA)
    df_sample = pd.read_csv(SAMPLE)

    # Extract domain in df_scraped for merging
    df_scraped['domain'] = df_scraped['domain'].apply(extract_domain)

    # Select only necessary columns from each to avoid duplicates and control final structure
    df_scraped_reduced = df_scraped[['domain', 'phone_numbers', 'social_links', 'address']]
    df_sample_reduced = df_sample[['domain', 'company_commercial_name', 'company_legal_name', 'company_all_available_names']]

    # Merge with full outer join on 'domain'
    merged_df = pd.merge(df_scraped_reduced, df_sample_reduced, on='domain', how='outer')

    # Save for ElasticSearch ingestion
    merged_df.to_json(MERGED, orient="records", lines=True)

    print(f"✅ Merged data saved with {len(merged_df)} records.")
