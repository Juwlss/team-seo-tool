import time
import pandas as pd
import streamlit as st
from curl_cffi import requests

# Configure the visual webpage interface settings
st.set_page_config(page_title="Team SEO Bulk Metric Auditor", layout="centered")
st.title("📊 Team SEO Bulk Metric Auditor")
st.write("Upload a CSV file with your domains, and fetch Domain Authority (DA) instantly.")

def fetch_public_moz_metrics(domain):
    """Queries Moz's official public endpoint bypassing token restrictions."""
    api_url = f"https://moz.com{domain}"
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://moz.com",
        "Referer": "https://moz.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(api_url, headers=headers, impersonate="chrome", timeout=12)
        
        if response.status_code == 200:
            data = response.json()
            da = data.get("domain_authority", "N/A")
            links = data.get("linking_domains_count", "N/A")
            spam = data.get("spam_score", "N/A")
            
            spam_display = f"{spam}%" if isinstance(spam, int) else "0%"
            return da, links, spam_display, "Success"
            
        elif response.status_code == 429:
            return "Rate Limited", "N/A", "N/A", "Rate Limited"
        else:
            return "N/A", "N/A", "N/A", f"Server Error {response.status_code}"
            
    except Exception:
        return "N/A", "N/A", "N/A", "Connection Timeout"

# UI File Drop Area for the user
uploaded_file = st.file_uploader("Drag and drop your 'websites.csv' file here", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    
    if "Domain" not in df.columns or "URL" not in df.columns:
        st.error("❌ Error: The uploaded CSV must contain exact columns named 'Domain' and 'URL'.")
    else:
        st.success(f"✅ Loaded {len(df)} web targets successfully!")
        
        if st.button("🚀 Start Bulk DA Extraction Run"):
            results = []
            progress_bar = st.progress(0)
            status_message = st.empty()
            
            for index, row in df.iterrows():
                domain_name = str(row["Domain"]).strip()
                url_name = str(row["URL"]).strip()
                if not domain_name or domain_name.lower() == "nan": continue
                
                status_message.text(f"Auditing ({index + 1}/{len(df)}): {domain_name}")
                
                da, links, spam, status_text = fetch_public_moz_metrics(domain_name)
                
                results.append({
                    "Domain": domain_name, 
                    "URL": url_name, 
                    "DA": da,
                    "Linking Domains": links, 
                    "Spam Score": spam,
                    "Status": status_text
                })
                progress_bar.progress((index + 1) / len(df))
                time.sleep(2)
            
            status_message.success("🎉 Bulk extraction processing completed successfully!")
            output_df = pd.DataFrame(results)
            output_df = output_df[["Domain", "URL", "DA", "Linking Domains", "Spam Score", "Status"]]
            st.write("### 📋 Results Preview")
            st.dataframe(output_df.head(10))
            
            final_csv = output_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Download Finished CSV Sheet", data=final_csv, file_name="da_bulk_results.csv", mime="text/csv")
