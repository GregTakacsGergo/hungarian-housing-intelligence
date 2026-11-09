"""Run locally: export both datasets to a publishable CSV snapshot.
Credentials are read from environment variables or your existing config.py.
Does not modify the source database.
"""
import argparse
import os
from pathlib import Path
import pandas as pd
import mysql.connector

OUT = Path(__file__).resolve().parent / 'data' / 'housing_prices.csv'
DEB = 'hajdu-bihar/debrecen'


def export(out: Path = OUT):
    password = os.getenv('MYSQL_PASSWORD')
    if password is None:
        try:
            from config import DB_PASSWORD
            password = DB_PASSWORD
        except ImportError as exc:
            raise RuntimeError('Set MYSQL_PASSWORD or place your existing config.py beside this script (do not upload it).') from exc
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=password,
        database='real_estate_47loc',
    )
    try:
        current = pd.read_sql('''
            SELECT snapshot_date, location, huf_per_sqm, sample_count,
                   '47loc' AS source
            FROM real_estate_47loc.`47loc_table`
            WHERE huf_per_sqm IS NOT NULL
            ORDER BY snapshot_date, location
        ''', conn)
        try:
            historical = pd.read_sql('''
                SELECT date AS snapshot_date, 'hajdu-bihar/debrecen' AS location,
                       universal_sqm_price_huf AS huf_per_sqm,
                       NULL AS sample_count, 'historical' AS source
                FROM real_db.real_estate_market_data
                WHERE universal_sqm_price_huf IS NOT NULL
                ORDER BY date
            ''', conn)
        except Exception as exc:
            print(f'WARNING: Historical Debrecen read failed: {exc}')
            historical = pd.DataFrame(columns=current.columns)
    finally:
        conn.close()

    deb_new = current.loc[current['location'] == DEB, 'snapshot_date']
    if not deb_new.empty:
        historical = historical.loc[pd.to_datetime(historical['snapshot_date']) < pd.to_datetime(deb_new).min()]
    df = pd.concat([historical, current], ignore_index=True)
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date'], errors='coerce')
    df['huf_per_sqm'] = pd.to_numeric(df['huf_per_sqm'], errors='coerce')
    df['sample_count'] = pd.to_numeric(df['sample_count'], errors='coerce')
    df = df.dropna(subset=['snapshot_date', 'location', 'huf_per_sqm'])
    df = df.drop_duplicates(subset=['snapshot_date', 'location'], keep='last')
    df = df.sort_values(['location', 'snapshot_date'])
    df['snapshot_date'] = df['snapshot_date'].dt.strftime('%Y-%m-%d')
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding='utf-8')
    print(f'Exported {len(df)} rows / {df.location.nunique()} locations to {out}')
    print('Check this file for sensitive information before publishing.')
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, default=OUT)
    export(p.parse_args().output)
