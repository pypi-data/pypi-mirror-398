import requests
from io import StringIO, BytesIO
import datetime, time
import warnings
warnings.filterwarnings('ignore')
import snowflake.connector as sf
from snowflake.connector.pandas_tools import write_pandas
import base64
import logging,json, pygsheets, pandas as pd
import chardet
from zipfile import BadZipFile
import re
import os.path
from google.cloud import storage

def get_googlesheets_data(name,sheet,service_account_path,skip_rows=0):
  global new_columns, old_columns,file
  gc = pygsheets.authorize(service_account_file = service_account_path)

  sh = gc.open(name)
  wks = sh.worksheet_by_title(sheet)
  
  if skip_rows > 0:
    # Get all values from the sheet
    all_values = wks.get_all_values()
    if len(all_values) > skip_rows:
      # Use row at skip_rows as the new header, rows after that as data
      header_row = all_values[skip_rows]
      data_rows = all_values[skip_rows+1:] if len(all_values) > skip_rows + 1 else []
      data = pd.DataFrame(data_rows, columns=header_row)
    else:
      # Fallback if skip_rows is beyond available rows
      data = wks.get_as_df()
  else:
    data = wks.get_as_df()

  try: 
    data = data.drop('',axis=1)
  except KeyError:
    pass

  new_columns = []
  old_columns = data.columns.tolist()

  for item in old_columns:
    if type(item) == str:
      new_item = re.sub(r'^order$','"order"',item.replace(" ($)","_").replace(" \+ ","_").replace(":","_").replace(" ","_").replace(".","").replace("(","").replace(")","").replace("/","_").replace(",","_").\
      replace("-","_").replace("%","per").replace('unnamed__',"").lstrip('0123456789').replace('unique','a_unique').lower().replace('#','').replace("+","").replace('&','_').replace('___','_').replace('__','_'))
      new_columns.append(new_item)
    elif type(item) == datetime.datetime:
      new_item = item.strftime("%b_%Y").lower()
      new_columns.append(new_item)

  for col in data.columns:
    try:
      data[col] = data[col].astype(str)
    except (ValueError,KeyError):
      continue

  for i in range(len(new_columns)):
    new_columns[i] = new_columns[i].lower()

  data.columns = new_columns

  drop_cols = ['',',','_']
  data = data.drop(drop_cols, axis=1, errors = 'ignore')
  data = data.loc[:,~data.columns.duplicated()]
  new_columns = data.columns.tolist()

  new_columns = data.columns

  sf_cols = []
  sf_tr = []

  for i in range(len(new_columns)):
    new_value = new_columns[i].lower() + ' ' + 'string'
    transform = 'nullif(' + new_columns[i].lower() + ',\'\') as ' + new_columns[i].lower()        # + ' ' + 'string'
    sf_cols.append(new_value)
    sf_tr.append(transform)

  sf_query = "\n,".join(sf_cols)
  sf_tr_query = "\n,".join(sf_tr)

  return data, sf_query, sf_tr_query

class sharepoint:
  def __init__(self,client_id,client_secret,tenant_id,site_id,library_name,drive_id):
    self.client_id = client_id
    self.client_secret = client_secret
    self.tenant_id = tenant_id

    # SharePoint Online site URL and library name

    self.site_id = site_id
    self.library_name = library_name
    self.drive_id = drive_id

    # Authenticate and get an access token
    auth_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    response = requests.post(auth_url, data=data)
    self.access_token = response.json()['access_token']

    self.headers = {
        'Authorization': f'Bearer {self.access_token}',
        'Content-Type': 'application/octet-stream',
    }

  def get_data(self,search_query,relative_path,date_col,sheet_name,skip_rows):
    api_url = f'https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/items/root:/{relative_path}:/children'
    response = requests.get(api_url, headers=self.headers)

    data = response.json()

    df = pd.DataFrame(data = data['value'].copy())
    cols = df.columns.to_list()
    df_filtered = df[df[cols]['name'].str.lower().str.contains(search_query.lower())].sort_values('lastModifiedDateTime',ascending=False).head(1).reset_index()

    file_name = df_filtered['name'].values[0]
    api_url_content = f'https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/items/root:/{relative_path}/{file_name}:/content'

    output = StringIO()
    file = requests.get(api_url_content,headers=self.headers)
    
    try:
      output = StringIO()
      data = pd.read_csv(StringIO(file.content.decode('utf-8')),skiprows=skip_rows)
    except (UnicodeDecodeError,BadZipFile) as err:
      print(err,'\nNow processing as excel file')
      output = BytesIO()
      dict = pd.read_excel(BytesIO(file.content),sheet_name=[sheet_name],engine='openpyxl',skiprows=skip_rows)
      data = dict[sheet_name]

    data['insertion_datetime'] = datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S')
  
    new_columns = []
    old_columns = data.columns.tolist()

    for item in old_columns:
      if type(item) == str:
        new_item = re.sub('^_|_$','',item.replace(" ($)","_").replace('\n','_').replace(" \+ ","_").replace(":","_").replace(" ","_").replace(".","")\
        .replace("(","").replace(")","").replace("/","_").replace(",","_").\
        replace("-","_").replace('__','_').replace('___','_').replace("%","per").replace('unnamed__',"").lstrip('0123456789')\
        .replace('unique','a_unique').lower().replace('#','').replace('?','').replace("+","").replace('^_','').replace('_$',''))
        new_columns.append(new_item)
      elif type(item) == datetime.datetime:
        new_item = item.strftime("%b_%Y").lower()
        new_columns.append(new_item)
        
    try: 
      data = data.drop('',axis=1)
    except KeyError:
      pass

    for col in data.columns:
      try:
        data[col] = data[col].astype(str)
      except (ValueError,KeyError):
        continue

    for i in range(len(new_columns)):
      new_columns[i] = new_columns[i].lower()

    data.columns = new_columns

    drop_cols = ['',',','_']
    data = data.drop(drop_cols, axis=1, errors = 'ignore')
    data = data.loc[:,~data.columns.duplicated()]
    new_columns = data.columns.tolist()

    sf_cols = []
    sf_tr = []

    for i in range(len(new_columns)):
      new_value = new_columns[i].lower() + ' ' + 'string'
      transform = 'nullif(' + new_columns[i].lower() + ',\'nan\') as ' + new_columns[i].lower()        # + ' ' + 'string'
      sf_cols.append(new_value)
      sf_tr.append(transform)

    sf_query = "\n,".join(sf_cols)
    sf_tr_query = "\n,".join(sf_tr)

    return data, sf_query, sf_tr_query, file, api_url_content

  def upload_file(self,upload_url,modified_data,content_type='application/octet-stream'):
    headers = {
        'Authorization': f'Bearer {self.access_token}',
        'Content-Type': content_type,
        'Content-Length': str(len(modified_data)),
    }
    upload_response = requests.put(upload_url, data=modified_data, headers=headers)
    if upload_response.status_code == 200:
      print("File uploaded successfully.")
    else:
      print(f"Failed to upload file. Status code: {upload_response.status_code}")
    upload_response.close()
    return headers
  

class snowflake:
  def __init__(self,user,pw,database,schema,role):

    self.database=database
    self.schema=schema
    self.role=role

    if 'airbyte' in role.lower():
      warehouse = 'airbyte_warehouse'
    else:
      warehouse = 'cart_dev_compute_wh'

    self.cnn = sf.connect(
            user= user,
            password = pw,
            account = 'og64234.us-central1.gcp',
            warehouse = warehouse,
            database = database,
            role = role,
            schema = schema)
    
  def load_data(self,sf_query,sf_tr_query,table_name,data,change_tracking=None):
    print('Table Name: {}'.format(self.database + '.' + self.schema + '.' + table_name))
    print('Start: load to Snowflake...')
    data.reset_index(drop=True, inplace=True)
    print('opening snowflake...')

    self.cnn.cursor().execute(
        "CREATE SCHEMA IF NOT EXISTS " + self.database + "." + self.schema
    ) 
    
    self.cnn.cursor().execute(
      "CREATE OR REPLACE TABLE " +
      table_name + "("  + sf_query + ")"
    )

    success, nchunks, nrows, _ = write_pandas(self.cnn, data, table_name, on_error = "CONTINUE",quote_identifiers=False)
    print(str(success) + ', ' + str(nchunks) + ', ' + str(nrows))

    self.cnn.cursor().execute(
      "CREATE OR REPLACE TABLE " + table_name + " as" + "\nselect\n" + sf_tr_query + '\nfrom\n' + table_name 
    )

    if change_tracking:
      self.cnn.cursor().execute("ALTER TABLE " + table_name + " set CHANGE_TRACKING=TRUE")
      print("Change Tracking Enabled")

    if self.database.casefold() != "maas_db":
      print(self.database)
      self.cnn.cursor().execute("EXECUTE TASK ENRICHMENT_DB.TASKS.SPROC5_TRIGGER")

    print('Started: Executed SPROC5...\n\n')

    self.cnn.close()
    print('Done: Load to Snowflake\n\n')

  def get_data(self,sheet_name,search_query):
    global df, sqlText, file_path
    print('Start: download from Snowflake for sheet {}'.format(sheet_name))

    print('opening snowflake...')

    sqlText = search_query
    print(sqlText)

    # Create a cursor object
    cur = self.cnn.cursor().execute(sqlText)

    # Fetch the result set from the cursor and deliver it as the Pandas DataFrame
    self.df = cur.fetch_pandas_all()

    # Process the DataFrame as needed for each sheet
    columns = self.df.columns.tolist()

    # Create a new dataframe with dynamic column names
    cumm_df = pd.DataFrame(columns=columns,data=self.df)
    # cumm_df = cumm_df.append(self.df, ignore_index=True)

    self.cnn.close()
    print('End: download from Snowflake for sheet {}'.format(sheet_name))

    # Return the new dataframe
    return cumm_df

class googlestorage:
  def __init__(self,service_account):
    self.client = storage.Client.from_service_account_json(service_account)

  def get_data(self,bucket_name,path,search_query,sheet_name,skip_rows):
    bucket = self.client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=f'{path}')
    max_modified_date = None

    for blob in blobs:
      if search_query.lower() in blob.name.lower():
        modified_time = blob.updated
        if max_modified_date is None or modified_time > max_modified_date:
          max_modified_date = modified_time
          fblob = blob
          print(f'Object Name: {fblob.name}, Modified: {fblob.updated}')

    try:
      csv_data = fblob.download_as_string()
      csv_string = csv_data.decode('utf-8')
      df = pd.read_csv(csv_string,skiprows=skip_rows)
    except UnicodeDecodeError:
      csv_data = fblob.download_as_bytes()
      df = pd.read_excel(csv_data,sheet_name=sheet_name,skiprows=skip_rows)

    return df
