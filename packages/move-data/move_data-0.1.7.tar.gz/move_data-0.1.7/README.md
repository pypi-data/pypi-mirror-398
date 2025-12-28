# move-data

A Python package for moving data between Google Sheets, SharePoint, Google Cloud Storage, and Snowflake.

## Features

- **Google Sheets Integration**: Extract data from Google Sheets with automatic column name normalization
- **SharePoint Integration**: Download and upload files from SharePoint Online
- **Google Cloud Storage**: Retrieve files from GCS buckets
- **Snowflake Integration**: Load data to and extract data from Snowflake databases

## Installation

```bash
pip install move-data
```

## Usage

### Google Sheets

```python
from move_data import get_googlesheets_data

data, sf_query, sf_tr_query = get_googlesheets_data(
    name="My Spreadsheet",
    sheet="Sheet1",
    service_account_path="/path/to/service_account.json",
    skip_rows=0  # Optional: skip first N rows
)
```

### SharePoint

```python
from move_data import sharepoint

sp = sharepoint(
    client_id="your_client_id",
    client_secret="your_client_secret",
    tenant_id="your_tenant_id",
    site_id="your_site_id",
    library_name="Documents",
    drive_id="your_drive_id"
)

data, sf_query, sf_tr_query, file, api_url = sp.get_data(
    search_query="filename",
    relative_path="folder/path",
    date_col="date_column",
    sheet_name="Sheet1",
    skip_rows=0
)
```

### Snowflake

```python
from move_data import snowflake

sf = snowflake(
    user="username",
    pw="password",
    database="database_name",
    schema="schema_name",
    role="role_name"
)

# Load data to Snowflake
sf.load_data(sf_query, sf_tr_query, "table_name", data, change_tracking=True)

# Get data from Snowflake
df = sf.get_data(sheet_name="Sheet1", search_query="SELECT * FROM table")
```

### Google Cloud Storage

```python
from move_data import googlestorage

gs = googlestorage(service_account="/path/to/service_account.json")

df = gs.get_data(
    bucket_name="my-bucket",
    path="folder/path",
    search_query="filename",
    sheet_name="Sheet1",
    skip_rows=0
)
```

## Requirements

- Python 3.7+
- See `pyproject.toml` for full dependency list

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

