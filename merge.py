import os
import pickle
import json
import heapq
from contextlib import ExitStack
from posting import Posting 

PICKLE_DIR = "index_pickle"
TEXT_DIR = "index_text"

def convert_pickles_to_sorted_text():
    """
    Step 1: Converts pickles into sorted text streams.
    """
    print("Step 1: Converting pickles to sorted text files...")
    if not os.path.exists(TEXT_DIR):
        os.makedirs(TEXT_DIR)

    # gathers pickle file paths
    pickle_files = [f for f in os.listdir(PICKLE_DIR) if f.endswith('.pickle')]
    
    for p_file in pickle_files:
        pickle_path = os.path.join(PICKLE_DIR, p_file)
        txt_name = p_file.replace('.pickle', '.txt')
        txt_path = os.path.join(TEXT_DIR, txt_name)
        
        # loads one pickle into memory
        with open(pickle_path, 'rb') as f:
            partial_index = pickle.load(f)
            
        # alphabetically sorted and stores line by line
        with open(txt_path, 'w', encoding='utf-8') as f:
            for term in sorted(partial_index.keys()):
                # convert the custom Posting objects into a simple list of [docid, freq]
                # so json.dumps() can actually write it to a text file.
                postings_list = [[p.docid, p.tfidf, p.url] for p in partial_index[term]]
                
                postings_str = json.dumps(postings_list)
                f.write(f"{term}\t{postings_str}\n")
                
        print(f"Converted {p_file} -> {txt_name}")
        
        # immediately clear memory JIC
        del partial_index

def merge_sorted_text_files(output_file="master_index.txt"):
    """
    Step 2: Uses a priority queue to merge all text files 
    line-by-line without loading them entirely into memory.
    """
    print("\nStep 2: Starting Merge...")
    # gathers all .txt files
    txt_files = [os.path.join(TEXT_DIR, f) for f in os.listdir(TEXT_DIR) if f.endswith('.txt')]
    
    with ExitStack() as stack:
        # open all files
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
                    # merge postings for the same word
                    current_postings.extend(postings)
                else:
                    # new word found, writes the previous word's data to disk
                    if current_term is not None:
                        # sort by doc id
                        current_postings.sort(key=lambda x: x[0]) 
                        merged_str = json.dumps(current_postings)
                        out_f.write(f"{current_term}\t{merged_str}\n")
                        
                    current_term = term
                    current_postings = postings
                    
                # pulls next word from file just processed
                next_line = files[file_idx].readline()
                if next_line:
                    next_term, next_postings_str = next_line.strip().split('\t', 1)
                    next_postings = json.loads(next_postings_str)
                    heapq.heappush(heap, (next_term, next_postings, file_idx))
            
            # writes final word
            if current_term is not None:
                current_postings.sort(key=lambda x: x[0])
                merged_str = json.dumps(current_postings)
                out_f.write(f"{current_term}\t{merged_str}\n")

    print(f"\nMerge complete! Final master index saved to {output_file}")

if __name__ == "__main__":
    convert_pickles_to_sorted_text()
    merge_sorted_text_files()