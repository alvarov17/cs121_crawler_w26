import os
import pickle
import json
import heapq
from contextlib import ExitStack

# CRITICAL: Pickle needs to know what a "Posting" object is to load the files!
# Replace 'build_index' with whatever the actual name of your indexer python file is.
from posting import Posting 

PICKLE_DIR = "index_pickle"
TEXT_DIR = "index_text"

def convert_pickles_to_sorted_text():
    """
    Step 1: Converts memory-heavy pickles into sorted text streams.
    """
    print("Step 1: Converting pickles to sorted text files...")
    if not os.path.exists(TEXT_DIR):
        os.makedirs(TEXT_DIR)

    pickle_files = [f for f in os.listdir(PICKLE_DIR) if f.endswith('.pickle')]
    
    for p_file in pickle_files:
        pickle_path = os.path.join(PICKLE_DIR, p_file)
        txt_name = p_file.replace('.pickle', '.txt')
        txt_path = os.path.join(TEXT_DIR, txt_name)
        
        # Load one pickle into RAM
        with open(pickle_path, 'rb') as f:
            partial_index = pickle.load(f)
            
        # Sort alphabetically and write line-by-line
        with open(txt_path, 'w', encoding='utf-8') as f:
            for term in sorted(partial_index.keys()):
                
                # THIS IS THE NEW LINE: 
                # Convert the custom Posting objects into a simple list of [docid, freq]
                # so json.dumps() can actually write it to a text file.
                postings_list = [[p.docid, p.tfidf] for p in partial_index[term]]
                
                postings_str = json.dumps(postings_list)
                f.write(f"{term}\t{postings_str}\n")
                
        print(f"Converted {p_file} -> {txt_name}")
        
        # Clear RAM immediately
        del partial_index

def merge_sorted_text_files(output_file="master_index.txt"):
    """
    Step 2: Uses a Priority Queue (Min-Heap) to merge all text files 
    line-by-line without loading them entirely into memory.
    """
    print("\nStep 2: Starting N-Way Merge...")
    txt_files = [os.path.join(TEXT_DIR, f) for f in os.listdir(TEXT_DIR) if f.endswith('.txt')]
    
    with ExitStack() as stack:
        # Open all text files simultaneously
        files = [stack.enter_context(open(f, 'r', encoding='utf-8')) for f in txt_files]
        
        heap = []
        for i, f in enumerate(files):
            line = f.readline()
            if line:
                term, postings_str = line.strip().split('\t', 1)
                postings = json.loads(postings_str)
                heapq.heappush(heap, (term, postings, i))
                
        with open(output_file, 'w', encoding='utf-8') as out_f:
            current_term = None
            current_postings = []
            
            while heap:
                term, postings, file_idx = heapq.heappop(heap)
                
                if current_term == term:
                    # Merge postings for the same word
                    current_postings.extend(postings)
                else:
                    # New word found! Write the previous word's data to disk
                    if current_term is not None:
                        # Sort the merged postings by docID to keep search results organized
                        current_postings.sort(key=lambda x: x[0]) 
                        merged_str = json.dumps(current_postings)
                        out_f.write(f"{current_term}\t{merged_str}\n")
                        
                    current_term = term
                    current_postings = postings
                    
                # Pull the next word from the file we just processed
                next_line = files[file_idx].readline()
                if next_line:
                    next_term, next_postings_str = next_line.strip().split('\t', 1)
                    next_postings = json.loads(next_postings_str)
                    heapq.heappush(heap, (next_term, next_postings, file_idx))
            
            # Write the final lingering word
            if current_term is not None:
                current_postings.sort(key=lambda x: x[0])
                merged_str = json.dumps(current_postings)
                out_f.write(f"{current_term}\t{merged_str}\n")

    print(f"\nMerge Complete! Final master index saved to {output_file}")

if __name__ == "__main__":
    convert_pickles_to_sorted_text()
    merge_sorted_text_files()