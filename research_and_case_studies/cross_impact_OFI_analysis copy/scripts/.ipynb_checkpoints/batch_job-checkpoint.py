import databento as db
import pandas as pd

def submit_batch_job(api_key, tickers, start_date, end_date, dataset="XNAS.ITCH", schema="mbp-10"):
    # Initialize the Databento Historical Client
    client = db.Historical(api_key)
    
    # Correct method for submitting a batch job using Databento
    batch_job = client.timeseries.submit_job(
        dataset=dataset,
        symbols=','.join(tickers),
        schema=schema,
        start=start_date,
        end=end_date,
        encoding="csv"
    )
    
    print(f"Batch job submitted successfully! Job ID: {batch_job['job_id']}")
    return batch_job['job_id']

def batch_job_to_dataframe(api_key, tickers, start_date, end_date, dataset="XNAS.ITCH", schema="mbp-10"):
    # Submit the batch job and download the data once complete
    job_id = submit_batch_job(api_key, tickers, start_date, end_date, dataset, schema)
    client = db.Historical(api_key)
    
    # Wait for job completion
    client.wait_for_job(job_id)
    
    # Download the completed batch job and load into a Pandas DataFrame
    data_path = client.download_job(job_id)
    df = pd.read_csv(data_path)
    print("Data successfully loaded into a Pandas DataFrame.")
    return df
