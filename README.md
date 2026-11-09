# Hungarian Housing Intelligence — Streamlit portfolio dashboard

Read-only public UI, based on the **actual source data** of the uploaded 47-location Jófogás project. No made-up/sample data is included.

## 1. Export the real data on your Windows PC

Copy `export_mysql_snapshot.py` into the folder where your existing `config.py` lives, or set `MYSQL_PASSWORD` in the environment. The MySQL user must be able to read **both** `real_estate_47loc` and `real_db` databases.

PowerShell:

```powershell
py -m pip install -r requirements.txt
$env:MYSQL_PASSWORD = "YOUR_LOCAL_MYSQL_PASSWORD"
py export_mysql_snapshot.py
```

If you copied the exporter outside this dashboard folder, specify the output path:

```powershell
py export_mysql_snapshot.py --output "C:\path\to\real_estate_streamlit\data\housing_prices.csv"
```

`data/housing_prices.csv` is deliberately absent until you export your real data. Verify the CSV's contents before making the repository public.

## 2. Run locally

```powershell
py -m streamlit run web_app.py
```

## 3. Publish

Create a GitHub repository containing the dashboard files, `data/housing_prices.csv`, and `requirements.txt`. **Do not upload** `config.py`, DB credentials, AWS credentials, `.env`, private CSVs, or the original entire backend. In https://share.streamlit.io/ choose New app / Create app, select the repository and `web_app.py` as entrypoint, then Deploy.

The dashboard uses an exported snapshot, so it does **not** update until you export and commit a new CSV. No cloud-to-localhost connection is needed.

## Notes

* Debrecen: old historical observations before the earliest new Debrecen date, then the 47loc series.
* Others: 47loc dataset only.
* Prices are **asking-price-derived indices**, not completed sale prices.
* Weekly OHLC candles reflect weekly index observations, not trading prices.
* The export script uses the same tables/columns as your `database_gateway_0702.py`. It does not modify your MySQL tables.
* If the historical DB read fails, the exporter warns and uses only the 47loc dataset; check its console output.
