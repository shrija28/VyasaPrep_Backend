"""
Script to migrate local FAISS indexes and PDF textbooks to Supabase Storage.
This reduces the local repository folder size by ~767 MB.
"""

import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

def get_supabase_config():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    # Infer SUPABASE_URL from DATABASE_URL if missing
    if not url:
        db_url = os.getenv("DATABASE_URL", "")
        match = re.search(r"postgres\.([a-z0-9]+)@", db_url)
        if match:
            project_id = match.group(1)
            url = f"https://{project_id}.supabase.co"
            print(f"[*] Inferred SUPABASE_URL from DATABASE_URL: {url}")
            
    return url, key


def main():
    url, key = get_supabase_config()
    
    if not url:
        print("[!] Error: SUPABASE_URL is missing in .env")
        print("Please add SUPABASE_URL=https://<your-project-id>.supabase.co to .env")
        sys.exit(1)
        
    if not key:
        print("[!] Error: SUPABASE_SERVICE_ROLE_KEY is missing in .env\n")
        print("==========================================================================")
        print("ACTION REQUIRED: Please add your Supabase Service Role Key to .env")
        print("==========================================================================")
        print("1. Open Supabase Dashboard: https://supabase.com/dashboard")
        print("2. Go to Project Settings -> API")
        print("3. Copy the 'service_role' secret key (under Project API keys)")
        print("4. Edit .env and paste it: SUPABASE_SERVICE_ROLE_KEY=your_key_here")
        print("==========================================================================\n")
        sys.exit(1)
        
    try:
        from supabase import create_client
    except ImportError:
        print("[!] Error: 'supabase' package is not installed. Run: pip install supabase")
        sys.exit(1)
        
    print("[*] Connecting to Supabase Storage...")
    try:
        supabase = create_client(url, key)
    except Exception as e:
        print(f"[!] Failed to connect to Supabase: {e}")
        sys.exit(1)
        
    faiss_bucket_name = os.getenv("SUPABASE_FAISS_BUCKET", "vyasaprep-faiss")
    textbooks_bucket_name = os.getenv("SUPABASE_TEXTBOOKS_BUCKET", "vyasaprep-textbooks")
    
    # Helper to ensure bucket exists
    def ensure_bucket(bucket_name):
        try:
            buckets = supabase.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            if bucket_name not in bucket_names:
                print(f"[*] Creating bucket '{bucket_name}'...")
                supabase.storage.create_bucket(bucket_name, options={"public": True})
            else:
                print(f"[+] Bucket '{bucket_name}' ready.")
        except Exception as e:
            print(f"[!] Warning listing/creating bucket '{bucket_name}': {e}")
            print(f"[*] Assuming bucket '{bucket_name}' exists...")

    ensure_bucket(faiss_bucket_name)
    ensure_bucket(textbooks_bucket_name)

    # 1. Upload FAISS files
    faiss_dir = Path("data/faiss")
    if faiss_dir.exists():
        faiss_bucket = supabase.storage.from_(faiss_bucket_name)
        files = [f for f in faiss_dir.glob("*") if f.is_file()]
        print(f"\n[*] Found {len(files)} FAISS files to upload in {faiss_dir}...")
        for f in files:
            file_size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  -> Uploading {f.name} ({file_size_mb:.2f} MB)...", end="", flush=True)
            try:
                with open(f, "rb") as file_data:
                    faiss_bucket.upload(
                        path=f.name,
                        file=file_data.read(),
                        file_options={"upsert": "true"}
                    )
                print(" [DONE]")
            except Exception as e:
                print(f" [FAILED: {e}]")
    else:
        print(f"[*] Directory {faiss_dir} not found. Skipping FAISS upload.")

    # 2. Upload Textbook PDFs
    textbooks_dir = Path("data/textbooks")
    if textbooks_dir.exists():
        tb_bucket = supabase.storage.from_(textbooks_bucket_name)
        files = [f for f in textbooks_dir.glob("*.pdf") if f.is_file()]
        print(f"\n[*] Found {len(files)} Textbook PDFs to upload in {textbooks_dir}...")
        for f in files:
            file_size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  -> Uploading {f.name} ({file_size_mb:.2f} MB)...", end="", flush=True)
            try:
                with open(f, "rb") as file_data:
                    tb_bucket.upload(
                        path=f.name,
                        file=file_data.read(),
                        file_options={"upsert": "true"}
                    )
                print(" [DONE]")
            except Exception as e:
                print(f" [FAILED: {e}]")
    else:
        print(f"[*] Directory {textbooks_dir} not found. Skipping Textbooks upload.")

    print("\n[+] All files processed!")
    print("\nNext step: Once verified, you can delete local files in data/ to reclaim ~767 MB.")

if __name__ == "__main__":
    main()
