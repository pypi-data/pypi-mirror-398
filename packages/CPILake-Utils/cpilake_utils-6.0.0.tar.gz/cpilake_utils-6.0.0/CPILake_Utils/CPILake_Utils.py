import re
import requests
from typing import Optional, List, Dict, Tuple, Union
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.conf import SparkConf
import json
from notebookutils import mssparkutils


## <<<<<<<<<<<<<<<<         hash_function 

def hash_function(s):
    """Hash function for alphanumeric strings"""
    if s is None:
        return None
    s = str(s).upper()
    s = re.sub(r'[^A-Z0-9]', '', s)
    base36_map = {ch: idx for idx, ch in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
    result = 0
    for i, ch in enumerate(reversed(s)):
        result += base36_map.get(ch, 0) * (36 ** i)
    result += len(s) * (36 ** (len(s) + 1))
    return result


## <<<<<<<<<<<<<<<<         send_email_via_http 

def send_email_via_http(params):
    """
    Sends an email using an HTTP endpoint (uses global endpoint_url & access_token set by init_mail()).

    Required:
      - to (str | list), subject (str), body (str)  # body will be replaced if df_in_body=True

    Optional:
      - cc, bcc, from_addr, headers (dict), attachments (list), timeout (int, default 15)
      - df            : Spark or Pandas DataFrame to render into the email body
      - df_limit      : limit rows if Spark DF (default 1000)
      - df_in_body    : if True (default), replace body with styled DF HTML (your format)
      - df_attach     : if True, also attach the same DF as HTML file (default False)
      - df_name       : attachment filename (default "data.html")
      - tz_name       : timezone string for timestamp header (default "America/Los_Angeles")
    """
    # Ensure init_mail() ran
    try:
        _ = endpoint_url
    except NameError:
        raise RuntimeError("endpoint_url not set. Call init_mail(...) once in this session before send_email_via_http().")
    try:
        _ = access_token
    except NameError:
        raise RuntimeError("access_token not set. Call init_mail(...) once in this session before send_email_via_http().")

    # Required checks
    required = ['to', 'subject', 'body']
    missing = [f for f in required if not params.get(f)]
    if missing:
        return None, f"Missing required fields: {', '.join(missing)}"

    # Base payload
    payload = {
        "to": ";".join(params["to"]) if isinstance(params["to"], list) else params["to"],
        "subject": params["subject"],
        "body": params["body"],
    }
    if params.get("cc"):
        payload["cc"] = params["cc"] if isinstance(params["cc"], list) else [params["cc"]]
    if params.get("bcc"):
        payload["bcc"] = params["bcc"] if isinstance(params["bcc"], list) else [params["bcc"]]
    if params.get("from_addr"):
        payload["from"] = params["from_addr"]
    if params.get("attachments"):
        payload["attachments"] = params["attachments"]

    # ---- DataFrame → HTML body (your existing style) ----
    df = params.get("df")
    if df is not None:
        df_limit = int(params.get("df_limit", 1000))
        tz_name  = params.get("tz_name", "America/Los_Angeles")
        df_in_body = params.get("df_in_body", True)
        df_attach  = params.get("df_attach", False)
        df_name    = params.get("df_name", "data.html")

        # Get pandas DataFrame
        pdf = None
        try:
            from pyspark.sql import DataFrame as SparkDF
            if isinstance(df, SparkDF):
                pdf = df.limit(df_limit).toPandas()
            else:
                pdf = df  # assume already pandas
        except Exception:
            pdf = df

        html_body = _df_to_html_table(pdf, tz_name=tz_name)

        if df_in_body:
            subject = str(params.get("subject", ""))
            if "QA Success" in subject:
                payload["body"] ='<html><body><h4>No data available to display.</h4></body></html>'
            else:
                payload["body"] = html_body
        else:
            # append to body if you prefer not to replace
            payload["body"] = f'{payload["body"]}{html_body}'

        if df_attach:
            content_b64 = base64.b64encode(html_body.encode("utf-8")).decode("utf-8")
            attach = {"name": df_name, "contentBytes": content_b64, "contentType": "text/html"}
            if "attachments" in payload and isinstance(payload["attachments"], list):
                payload["attachments"].append(attach)
            else:
                payload["attachments"] = [attach]

    # Auth header
    req_headers = {"Authorization": f"Bearer {access_token}"}
    if params.get("headers"):
        req_headers.update(params["headers"])

    timeout = params.get("timeout", 15)

    # Send
    try:
        response = requests.post(endpoint_url, json=payload, headers=req_headers, timeout=timeout)
        status_msg = "✅ Success" if response.status_code == 200 else f"❌ Failed ({response.status_code})"
        print(f"Email send: {status_msg}")
        return response.status_code, response.text, req_headers
    except requests.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        print(f"❌ {error_msg}")
        return None, error_msg
    

## <<<<<<<<<<<<<<<<         _df_to_html_table

def _df_to_html_table(pdf, tz_name="America/Los_Angeles"):
    """Render a pandas DataFrame to your styled HTML table."""
    # Empty DF → simple message
    if pdf is None or len(pdf.index) == 0:
        return '<html><body><h4>No data available to display.</h4></body></html>'

    # Header with PST time
    pst = pytz.timezone(tz_name)
    now_pst = datetime.now(pst).strftime("%Y-%m-%d %H:%M:%S")

    html_Table = []
    html_Table.append('<html><head><style>')
    html_Table.append('table {border-collapse: collapse; width: 100%} '
                      'table, td, th {border: 1px solid black; padding: 3px; font-size: 9pt;} '
                      'td, th {text-align: left;}')
    html_Table.append('</style></head><body>')
    html_Table.append(f'<h4>(Refresh Time: {now_pst})</h4><hr>')
    html_Table.append('<table style="width:100%; border-collapse: collapse;">')
    html_Table.append('<thead style="background-color:#000000; color:#ffffff;"><tr>')

    # Columns (skip FailureFlag in header, to match your code)
    cols = list(pdf.columns)
    visible_cols = [c for c in cols if c != "FailureFlag"]
    for c in visible_cols:
        html_Table.append(f'<th style="border: 1px solid black; padding: 5px;">{html.escape(str(c))}</th>')
    html_Table.append('</tr></thead><tbody>')

    # Rows (highlight red if FailureFlag == 'Yes', else light green default)
    ff_present = "FailureFlag" in cols
    for _, row in pdf.iterrows():
        row_bg_color = '#ccff66'  # default
        if ff_present:
            try:
                if str(row["FailureFlag"]).strip().lower() == "yes":
                    row_bg_color = '#ff8080'
            except Exception:
                pass
        html_Table.append(f'<tr style="background-color:{row_bg_color};">')
        for c in visible_cols:
            val = row[c]
            html_Table.append(f'<td>{html.escape("" if val is None else str(val))}</td>')
        html_Table.append('</tr>')

    html_Table.append('</tbody></table></body></html>')
    return "".join(html_Table)


## <<<<<<<<<<<<<<<<         send_email_no_attachment 

def send_email_no_attachment(p, endpoint_url=None, access_token=None):
    """
    Send email via POST API without attachment.

    Parameters:
        p (dict): {
            "to": str | list[str],
            "subject": str,
            "body": str,
            "headers": dict (optional),
            "timeout": int (optional)
        }
        endpoint_url (str): API endpoint for sending mail
        access_token (str): Bearer token

    Returns:
        (status_code, response_text) or (None, error_message)
    """
    if not endpoint_url:
        raise ValueError("endpoint_url is required")
    if not access_token:
        raise ValueError("access_token is required")

    missing = [k for k in ("to", "subject", "body") if not p.get(k)]
    if missing:
        return None, f"Missing required fields: {', '.join(missing)}"

    payload = {
        "to": ";".join(p["to"]) if isinstance(p["to"], list) else p["to"],
        "subject": p["subject"],
        "body": p["body"],
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        **p.get("headers", {})
    }

    try:
        resp = requests.post(
            endpoint_url,
            json=payload,
            headers=headers,
            timeout=p.get("timeout", 15)
        )
        success_codes = (200, 201, 202)
        return resp.status_code, resp.text
    except requests.RequestException as e:
        return None, str(e)


## <<<<<<<<<<<<<<<<         send_email_no_attachment_01 

def send_email_no_attachment_01(
    body        : Optional[str]             = None,
    endpoint_url: Optional[str]             = None,
    access_token: Optional[str]             = None,
    subject     : Optional[str]             = None,
    recipients  : Optional[List[str]]       = None,
    headers     : Optional[Dict[str, str]]  = None,
    timeout     : int                       = 15,
    tz_name     : str                       = "America/Los_Angeles"
) -> Tuple[Optional[int], str]:
    """
    Send email via POST API without attachments. All parameters are optional.
    If required information is missing, returns a descriptive message instead of sending.
    """
    # If endpoint or token not provided, skip sending
    if not endpoint_url or not access_token:
        return None, "Skipping send: endpoint_url or access_token not provided."

    # Determine recipients
    final_recipients = recipients
    if not final_recipients:
        return None, "Skipping send: no recipients provided."

    # Determine body content
    final_body = body
    if not final_body:
        return None, "Skipping send: no body content provided."

    payload = {
        "to": ";".join(final_recipients) if isinstance(final_recipients, list) else final_recipients,
        "subject": subject or "",
        "body": final_body
    }

    request_headers = {
        "Authorization": f"Bearer {access_token}",
        **(headers or {})
    }

    try:
        resp = requests.post(
            endpoint_url,
            json=payload,
            headers=request_headers,
            timeout=timeout
        )
        if resp.status_code in (200, 201, 202):
            return resp.status_code, resp.text
        else:
            return resp.status_code, f"Failed: {resp.text}"
    except requests.RequestException as e:
        return None, str(e)


## <<<<<<<<<<<<<<<<         QA_CheckUtil 

def QA_CheckUtil(
    source_df: DataFrame,
    qa_df: DataFrame
) -> DataFrame:

    spark = source_df.sparkSession
    qa_rows: List[tuple] = []

    def calc_diff(src: Optional[Union[int, float]], qa: Optional[Union[int, float]]) -> Optional[float]:
        if src is None or qa is None:
            return None
        return float(src) - float(qa)

    # Row count
    src_count = float(source_df.count())
    qa_count = float(qa_df.count())
    qa_rows.append((
        "ROW_COUNT",
        "row_count",
        None,
        src_count,
        qa_count,
        calc_diff(src_count, qa_count),
        src_count == qa_count
    ))

    # Null check
    common_cols = set(source_df.columns).intersection(set(qa_df.columns))
    for col in common_cols:
        src_nulls = float(source_df.filter(F.col(col).isNull()).count())
        qa_nulls = float(qa_df.filter(F.col(col).isNull()).count())
        qa_rows.append((
            "NULL_CHECK",
            "null_count",
            col,
            src_nulls,
            qa_nulls,
            calc_diff(src_nulls, qa_nulls),
            src_nulls == qa_nulls
        ))

    # Aggregation check (SUM for amount)
    if "amount" in source_df.columns and "amount" in qa_df.columns:
        src_sum = float(source_df.select(F.sum("amount")).collect()[0][0] or 0.0)
        qa_sum = float(qa_df.select(F.sum("amount")).collect()[0][0] or 0.0)
        qa_rows.append((
            "AGG_CHECK",
            "sum",
            "amount",
            src_sum,
            qa_sum,
            calc_diff(src_sum, qa_sum),
            src_sum == qa_sum
        ))

    # Duplicate check on id column
    if "id" in source_df.columns and "id" in qa_df.columns:
        src_dupes = float(source_df.count() - source_df.select("id").distinct().count())
        qa_dupes = float(qa_df.count() - qa_df.select("id").distinct().count())
        qa_rows.append((
            "DUPLICATE_CHECK",
            "duplicate_id",
            "id",
            src_dupes,
            qa_dupes,
            calc_diff(src_dupes, qa_dupes),
            src_dupes == qa_dupes
        ))

    # Create final QA DataFrame
    qa_df_result = spark.createDataFrame(
        qa_rows,
        [
            "check_type",
            "check_name",
            "column_name",
            "source_value",
            "qa_value",
            "diff",
            "match"
        ]
    )
    return qa_df_result


## <<<<<<<<<<<<<<<<         create_lakehouse_shortcuts 

def create_lakehouse_shortcuts(shortcut_configs, workspace_id, lakehouse_id, target_schema):
    access_token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com/.default")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    print("Access token starts with:", access_token[:20])

    for config in shortcut_configs:
        source_path = config["source_subpath"]
        target_shortcut_name = config["target_shortcut_name"]
        source_workspace_id = config["source_workspace_id"]
        source_lakehouse_id = config["source_lakehouse_id"]

        target_path = f"Tables/{target_schema or 'dbo'}/"

        payload = {
            "path": target_path,
            "name": target_shortcut_name,
            "target": {
                "type": "OneLake",
                "oneLake": {
                    "workspaceId": source_workspace_id,
                    "itemId": source_lakehouse_id,
                    "path": source_path
                }
            }
        }

        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts"
        print(f"Creating shortcut '{target_shortcut_name}' → {target_path}")
        print(json.dumps(payload, indent=2))

        # --- Send POST request ---
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            print(f"Shortcut '{target_shortcut_name}' created successfully.")
            print(response.json())
        else:
            print(f"Failed to create shortcut '{target_shortcut_name}'.")
            print("Status Code:", response.status_code)
            print("Response:", response.text)


## <<<<<<<<<<<<<<<<         create_lakehouse_shortcuts_01 

def create_lakehouse_shortcuts_01(shortcut_configs):
    access_token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com/.default")
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json" }
    print("Access token starts with:", access_token[:20])

    for config in shortcut_configs:
        source_path             =   config["source_subpath"]
        target_schema           =   config["target_schema"]
        workspace_name          =   config["workspace_name"]
        lakehouse_name          =   config["lakehouse_name"]
        target_shortcut_name    =   config["target_shortcut_name"]

        resp_ws         = requests.get("https://api.fabric.microsoft.com/v1/workspaces", headers=headers)
        resp_ws.raise_for_status()
        workspace_id = next(ws["id"] for ws in resp_ws.json()["value"] if ws["displayName"] == workspace_name)

        resp_lh = requests.get(f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/lakehouses", headers=headers)
        resp_lh.raise_for_status()
        lakehouse_id = next(lh["id"]  for lh in resp_lh.json()["value"]  if lh["displayName"] == lakehouse_name)

        target_path = f"Tables/{target_schema or 'dbo'}/"

        payload = {
            "path": target_path,
            "name": target_shortcut_name,
            "target": {
                "type": "OneLake",
                "oneLake": {
                    "workspaceId"   :   workspace_id,
                    "itemId"        :   lakehouse_id,
                    "path"          :   source_path,
                    "target_schema" :   config["target_schema"]
                }
            }
        }

        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts"
        print(f"Creating shortcut '{target_shortcut_name}' → {target_path}")
        print(json.dumps(payload, indent=2))

        # --- Send POST request ---
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            print(f"Shortcut '{target_shortcut_name}' created successfully.")
            print(response.json())
        else:
            print(f"Failed to create shortcut '{target_shortcut_name}'.")
            print("Status Code:", response.status_code)
            print("Response:", response.text)

"""
# How to call function
shortcut_configs = [  
    {
        "target_shortcut_name"  :   "DIM_Date",
        "workspace_name"        :   "FDnECostHubReporting_DEV",
        "lakehouse_name"        :   "Cost_Hub",
        "source_subpath"        :   "Tables/DIM_Date",
        "target_schema"         :   "CostHub",
    }
]
create_lakehouse_shortcuts_01(shortcut_configs)
"""

## <<<<<<<<<<<<<<<<         create_adls_shortcuts 

def create_adls_shortcuts(shortcut_configs, workspace_id, lakehouse_id, target_schema):
    access_token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com/.default")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    print("Access token starts with:", access_token[:20])

    target_path = f"Tables/{target_schema}/"
    
    for config in shortcut_configs:
        payload = {
            "name": config["name"],
            "path": target_path,
            "target": {
                "type": "AdlsGen2",
                "adlsGen2": {
                    "connectionId": config["connection_id"],
                    "location": config["location"],
                    "subpath": config["subpath"]
                }
            }
        }

        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts"
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            print(f"Shortcut '{config['name']}' created successfully.")
        else:
            print(f"Failed to create shortcut '{config['name']}'.")
            print("Status Code:", response.status_code)
            print("Response:", response.text)


## <<<<<<<<<<<<<<<<         create_adls_shortcuts_01 

def create_adls_shortcuts_01(shortcut_configs):
    access_token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com/.default")
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json" }
    print("Access token starts with:", access_token[:20])

    for config in shortcut_configs:
        target_schema       = config["target_schema"]
        workspace_name      = config["workspace_name"]
        lakehouse_name      = config["lakehouse_name"]
        connection_name     = config["connection_name"]
        target_path         = f"Tables/{target_schema}/"

        resp_ws         = requests.get("https://api.fabric.microsoft.com/v1/workspaces", headers=headers)
        resp_ws.raise_for_status()
        workspace_id = next(ws["id"] for ws in resp_ws.json()["value"] if ws["displayName"] == workspace_name)

        resp_lh = requests.get(f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/lakehouses", headers=headers)
        resp_lh.raise_for_status()
        lakehouse_id = next(lh["id"]  for lh in resp_lh.json()["value"]  if lh["displayName"] == lakehouse_name)

        resp_cn = requests.get(f"https://api.fabric.microsoft.com/v1/connections", headers=headers)
        resp_cn.raise_for_status()
        connection_id = next(conn["id"] for conn in resp_cn.json()["value"] if conn["displayName"] == connection_name)

        conn_loc = next(conn for conn in resp_cn.json()["value"] if conn["displayName"] == connection_name)
        location = conn_loc["connectionDetails"]["path"]

        payload = {
            "name": config["name"],
            "path": target_path,
            "target": {
                "type": "AdlsGen2",
                "adlsGen2": {
                    "connectionId"  :     connection_id,
                    "location"      :     location,
                    "subpath"       :     config["subpath"]                    
                }
            }
        }

        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts"
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            print(f"Shortcut '{config['name']}' created successfully.")
        else:
            print(f"Failed to create shortcut '{config['name']}'.")
            print("Status Code:", response.status_code)
            print("Response:", response.text)

"""
# How to call function

# Define shortcut configurations
shortcut_configs = [
    {
        "name"              :   "Bridge_ExecOrgSummary",
        "target_schema"     :   "CostHub",
        "workspace_name"    :   "FDnECostHubReporting_DEV",
        "lakehouse_name"    :   "Cost_Hub",
        "connection_name"   :   "CostHub_ADLS abibrahi",
        "subpath"           :   "/abidatamercury/MercuryDataProd/CostHub/Bridge_ExecOrgSummary"
    }]

# Call the function
create_adls_shortcuts_01(shortcut_configs)  
"""