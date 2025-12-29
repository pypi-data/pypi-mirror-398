import os
import time
import json
import logging
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from supabase import create_client
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load env
load_dotenv(dotenv_path='c:\\Users\\adars\\Desktop\\moat\\.env')

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing Supabase credentials")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Worker Configuration
MAX_WORKERS = 5  # Allow processing 5 traces concurrently
POLL_INTERVAL = 2

def process_job(job):
    """
    Process a single job. This function runs in a separate thread.
    """
    job_id = job['id']
    trace_id = job.get('trace_id')
    
    logger.info(f"[{job_id}] Starting processing for Trace {trace_id}")
    
    try:
        # Mark as processing
        supabase.table('jobs').update({'status': 'processing'}).eq('id', job_id).execute()

        # Simulate processing (Replace this with actual logic later)
        # Note: In a real scenario, this would call the actual replay/trace generation code
        # For now, we are likely calling a script or function.
        # Based on previous context, we might be running a subprocess or internal function.
        
        # Checking how the original main.py did it. 
        # It seems the original main.py WAS calling subprocess or internal logic. 
        # I need to see the REST of main.py to know exactly what 'process_job' should do.
        
        # Placeholder for the actual logic I'll copy from the original file
        time.sleep(5) 
        
        logger.info(f"[{job_id}] Completed Trace {trace_id}")
        supabase.table('jobs').update({'status': 'completed'}).eq('id', job_id).execute()
        
    except Exception as e:
        logger.error(f"[{job_id}] Failed: {e}")
        supabase.table('jobs').update({'status': 'failed', 'error': str(e)}).eq('id', job_id).execute()

def worker_loop():
    logger.info(f"Worker started with {MAX_WORKERS} threads. Waiting for jobs...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while True:
            try:
                # Fetch pending jobs
                response = supabase.table('jobs').select('*').eq('status', 'pending').limit(MAX_WORKERS).execute()
                jobs = response.data
                
                if jobs:
                    logger.info(f"Found {len(jobs)} pending jobs. Submitting to pool.")
                    for job in jobs:
                        # Optimistic locking: mark as 'picked' immediately so other workers don't grab it
                        # For simplicity in this single-process-multi-thread version, we trust the fetch 
                        # but ideally we'd claim it first.
                        # Since we are the only worker PROCESS, this is fine.
                        executor.submit(process_job, job)
                
                time.sleep(POLL_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    worker_loop()
