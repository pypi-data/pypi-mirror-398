import datetime
import time
import warnings
import pandas as pd
from .auth import get_gmail_service

def fetch_messages(query="", max_results=2000):
    """
    Fetches a list of messages based on the query.
    Returns a list of dicts: {'id': msg_id, 'threadId': thread_id}
    """
    service = get_gmail_service()
    messages = []
    
    try:
        # If query is empty, Gmail API match all.
        request = service.users().messages().list(userId='me', q=query, maxResults=500)
        
        while request is not None:
            response = request.execute()
            messages.extend(response.get('messages', []))
            request = service.users().messages().list_next(request, response)
            
            if max_results and len(messages) >= max_results:
                messages = messages[:max_results]
                break
    except Exception as e:
        print(f"Error fetching messages: {e}")
            
    return messages

def fetch_total_count(query=""):
    """
    Returns the estimated total number of messages matching the query.
    """
    service = get_gmail_service()
    try:
        response = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
        return response.get('resultSizeEstimate', 0)
    except Exception as e:
        print(f"Error getting total count: {e}")
        return 0

def get_yearly_counts():
    """
    Fetches email counts for each year from 2010 to present.
    Returns a DataFrame: {'Year': year, 'Count': count}
    """
    current_year = datetime.date.today().year
    years = range(2010, current_year + 1)
    results = []
    
    # We fetch these sequentially. It's fast (metadata only).
    for year in sorted(years, reverse=True):
        query = f"after:{year}/01/01 before:{year + 1}/01/01"
        count = fetch_total_count(query)
        if count > 0:
            results.append({'Year': str(year), 'Count': count})
            
    return pd.DataFrame(results)

def get_message_details(messages, progress_callback=None):
    """
    Fetches headers for ALL messages in the list to enable analytics.
    Uses batching to stay within API limits.
    """
    service = get_gmail_service()
    results = []
    
    # ---------------------------------------------------------
    # RATE LIMIT CONFIG
    # ---------------------------------------------------------
    # Limit: 250 quota units/sec. 'messages.get' = 5 units. Max 50 msgs/sec.
    # We use Safe Mode: 25 msgs (125 units) per batch.
    # Min time per batch = 0.5s. We sleep 0.5s + Latency -> ~0.7s/batch (~35 emails/s)
    chunk_size = 25 
    sleep_between_batches = 0.5
    # ---------------------------------------------------------
    
    total = len(messages)
    
    for i in range(0, total, chunk_size):
        chunk = messages[i:i + chunk_size]
        batch = service.new_batch_http_request()
        
        failed_in_batch = []
        
        def callback(request_id, response, exception):
            if exception:
                error_str = str(exception).lower()
                if 'ratelimit' in error_str or '429' in error_str or 'user' in error_str:
                    # Queue for individual retry
                    failed_in_batch.append(request_id)
                else:
                    print(f"Error fetching details for {request_id}: {exception}")
                    # Permanent error -> Placeholder
                    results.append({
                        'id': request_id, 
                        'Subject': '(Error loading details)', 
                        'From': '(Unknown)', 
                        'Date': ''
                    })
            else:
                headers = response.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown)')
                date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                results.append({
                    'id': request_id, 
                    'Subject': subject, 
                    'From': sender, 
                    'Date': date_str
                })

        for msg in chunk:
            batch.add(
                service.users().messages().get(
                    userId='me', 
                    id=msg['id'], 
                    format='metadata', 
                    metadataHeaders=['From', 'Subject', 'Date']
                ),
                callback=callback,
                request_id=msg['id']
            )
        
        # Execute Batch
        try:
            batch.execute()
        except Exception as e:
            print(f"Batch execution failed: {e}")
            # If batch fails entirely, mark all as failed
            for msg in chunk:
                if msg['id'] not in [r['id'] for r in results]: # Avoid dups if partial success
                    failed_in_batch.append(msg['id'])

        # Retry Logic for Rate Limited Items
        if failed_in_batch:
            print(f"⚠️ Retrying {len(failed_in_batch)} rate-limited items...")
            time.sleep(2.0) # Backoff for the retry
            
            for retry_id in failed_in_batch:
                try:
                    # Individual fetch for retry
                    msg_detail = service.users().messages().get(
                        userId='me', 
                        id=retry_id, 
                        format='metadata', 
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()
                    
                    headers = msg_detail.get('payload', {}).get('headers', [])
                    results.append({
                        'id': retry_id, 
                        'Subject': next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)'),
                        'From': next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown)'),
                        'Date': next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    })
                except Exception as e:
                    print(f"❌ Retry failed for {retry_id}: {e}")
                    results.append({
                        'id': retry_id, 
                        'Subject': '(Retry Failed)', 
                        'From': '(Unknown)', 
                        'Date': ''
                    })

        time.sleep(sleep_between_batches)
        
        if progress_callback:
            progress_callback(min(1.0, (i + len(chunk)) / total))

    df = pd.DataFrame(results)
    
    if not df.empty:
        # Robust Date Parsing
        try:
            # Try standard pandas parsing
            # Try standard pandas parsing
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=FutureWarning, message=".*Parsing 'GMT' as tzlocal.*")
                df['DateObj'] = pd.to_datetime(df['Date'], errors='coerce', utc=True)
            df['Year'] = df['DateObj'].dt.year
        except Exception as e:
            print(f"Pandas date parsing failed: {e}. Falling back to regex.")
            # Fallback: Extract year directly from string (e.g. "Tue, 20 Dec 2022")
            # Look for 4 digits that start with 20 (covering 2000-2099)
            df['Year'] = df['Date'].astype(str).str.extract(r'\b(20\d{2})\b').astype(float)
        
        # Fill NaN years with 'Unknown' (or 0 for now to keep int type if possible, but float allows NaN)
        # Actually app expects string or valid year.
        
        df['Email'] = df['From'].str.extract(r'<([^>]+)>')
        df['Email'] = df['Email'].fillna(df['From'])
    
    return df

def batch_delete_messages(message_ids):
    """
    Permanently deletes messages.
    """
    service = get_gmail_service()
    batch_size = 1000
    total_deleted = 0
    
    for i in range(0, len(message_ids), batch_size):
        batch = message_ids[i:i + batch_size]
        body = {'ids': batch}
        try:
            service.users().messages().batchDelete(userId='me', body=body).execute()
            total_deleted += len(batch)
            time.sleep(1) # Safety nap
        except Exception as e:
            print(f"Error deleting batch: {e}")
            raise e
            
    return total_deleted
