import json
import os
from datetime import datetime
from Bio import Entrez

#NCBI requires an email address to track API usage
Entrez.email = "qureshiabdulraffay@gmail.com"

#Define our target research areas form the pipeline secifications
SEARCH_QUERIES = [
    "Computational drug discovery",
    "Machine learning in drug discovery",
    "Deep learning in drug discovery",
    "molecular docking",
    "immunoinformatics",
    "genomics transcriptomics"
]
TRACKING_FILE = "seen_pmids.json"


# 1st Function to search PubMed for papers based on a query ✅
def search_pubmed(query, max_results=5):
    print(f"Searching PubMed for: {query}...")

    # E-utilities search execution
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)  # Core API call to search PubMed database #retmax = to limit the results

    # Parse the XML response into Python dictionary
    record = Entrez.read(handle)        #NCBI server sends data back in a messy XML format
    handle.close()

    # Return the list of PubMed IDs (PMIDs)
    return record["IdList"]


# 2nd Function to fetch paper details given a list of PMIDs ✅
def fetch_paper_details(pmid_list):
    if not pmid_list:
        return []

    print(f"Fetching details for {len(pmid_list)} papers...")

    # E-utilities fetch execution
    handle = Entrez.efetch(db="pubmed", id=pmid_list, retmode="xml")  # Core API call to fetch paper details
    records = Entrez.read(handle)  # Parse the XML response into Python dictionary
    handle.close()

    papers_data = []

    # Safely parse the messy XML dictionary
    for pubmed_article in records.get('PubmedArticle', []):
        medline_citation = pubmed_article.get('MedlineCitation', {})
        article = medline_citation.get('Article', {})

        pmid = str(medline_citation.get('PMID', 'Unknown'))
        title = article.get('ArticleTitle', 'No Title Available')

    # Safely extract the abstract if it exists
    abstract = "No abstract available."
    if 'Abstract' in article and 'AbstractText' in article['Abstract']:
        # Sometimes abstracts are split into multiple sections, we just grab the first one
        abstract = str(article['Abstract']['AbstractText'][0])

    papers_data.append({
        "pmid": pmid,
        "title": title,
        "abstract": abstract
    })

    return papers_data

# Deduplication Functions ✅
def load_seen_pmids():                  # load_seen_pmids() acts as the gatekeeper. Before we process any papers, it opens seen_pmids.json and loads all the old IDs into memory.
    """Loads previously processed PMIDs from the JSON tracking file."""
    # Check if the tracking file actually exsists first to prevent FileNotFoundError
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'r') as f:
            # We convert the JSON list onto a Python Set for instant lookups
            return set (json.load(f))

    # If this is the first time running the pipeline, return an empty Set
    return set()
    

def save_seen_pmids(pmids):            # save_seen_pmids() runs at the very end of our pipeline to write the new, updated list of IDs back to the hard drive so the next X-hour run remembers them.
    """Saves the updated Set of PMIDs back to the JSON file."""
    with open(TRACKING_FILE, 'w') as f:
        # JSON can't natively save Sets, so we convert it back to a list
        json.dump(list(pmids), f, indent=4)

# Function for markdown append ✅
def append_to_markdown(paper_data):
    """Formats and appends new papers to the Markdown digest."""
    if not paper_data:
        return
    
    filename = "RESEARCH_DIGEST.md"
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Open the file in "a" (append) mode so we don't overwrite history
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\n## PubMed Update: {today}\n\n")

        for paper in paper_data:
            # Create a clickable link directly to the PubMed article
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/"

            f.write(f"### {paper['title']}\n")
            f.write(f"**PMID:** [{paper['pmid']}]({pubmed_url})\n\n")
            f.write(f"**Abstract:** {paper['abstract']}\n\n")
            f.write("---\n")


if __name__ == "__main__":
    print("Starting PubMed Literature Tracker Pipeline...")

    # 1. Load historical state
    seen_pmids = load_seen_pmids()
    print(f"Loaded {len(seen_pmids)} previously procesed PMIDs.")

    #Variables to hold our new discoveries
    all_new_pmids = set()
    all_new_paper_details = []

    # 2. Iterate through all our search qureies
    for query in SEARCH_QUERIES:
        found_pmids = search_pubmed(query, max_results=3)

        # 3. Deduplication Logic: Keep only PMIDs NOT in our seen_pmids set
        new_pmids = [pmid for pmid in found_pmids if pmid not in seen_pmids]

        if new_pmids:
            print(f"Found {len(new_pmids)} new papers for '{query}'")
            # Fetch details for the ONLY new papers
            paper_details = fetch_paper_details(new_pmids)
            all_new_paper_details.extend(paper_details)

            # Add these new PMIDs to our tracker variable
            all_new_pmids.update(new_pmids)
        else:
            print(f"No new papers found for '{query}'")

# 4. Save state if we found anything new
if all_new_paper_details:
    print(f"\n--- PIPELINE SUMMARY ---")
    print(f"Total new papers processed: {len(all_new_paper_details)}")

    # Update our main state tracker and save it to the hard drive
    seen_pmids.update(all_new_pmids)
    save_seen_pmids(seen_pmids)
    print("State successfully saved to seen_pmids.json")

    # Add this new Markdown generator!
    append_to_markdown(all_new_paper_details)
    print("Successfully appended discoveries to RESEARCH_DIGEST.md")
else:
    print("\nPipeline completed. No new papers to process.")
