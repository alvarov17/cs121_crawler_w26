import json
import math

docMetaData = "doc_metadata.json"
linkGraph = "link_graph.json"
prFile = "pagerank.json"

dFac = 0.85
maxIter = 100
converge = 1e-6

#Computes the PageRank for all URLs that appear in url_to_docid.
def compute_pagerank(link_graph: dict, url_to_docid: dict) -> dict:
    urls = list(url_to_docid.keys())
    N = len(urls)
    if N == 0:
        return {}

    url_index = {url: i for i, url in enumerate(urls)}

    in_links = [[] for _ in range(N)]
    out_degree = [0] * N

    for src_url, dest_urls in link_graph.items():
        if src_url not in url_index:
            continue
        src_i = url_index[src_url]

        seen_dest = set()
        for dest_url in dest_urls:
            if dest_url in url_index and dest_url not in seen_dest:
                dest_i = url_index[dest_url]
                in_links[dest_i].append(src_i)
                seen_dest.add(dest_url)

        out_degree[src_i] = len(seen_dest)
    #Page Rank Formula given by: PR(A) = (1-d) + d Sigma (PR(ti)/C(ti))
    pr = [1.0] * N

    for iteration in range(maxIter):
        new_pr = [0.0] * N
        for i in range(N):
            new_pr[i] = (1.0 - dFac) + dFac * sum(pr[j] / out_degree[j] for j in in_links[i] if out_degree[j] > 0)

        delta = sum(abs(new_pr[i] - pr[i]) for i in range(N))
        pr = new_pr

        if delta < converge:
            print(f"PageRank converged after {iteration + 1} iterations")
            break
    else:
        print(f"PageRank reached max iterations ({maxIter}) without converging")

    #normalize the score
    scores = {}
    for url, docid in url_to_docid.items():
        idx = url_index.get(url)
        if idx is not None:
            scores[str(docid)] = math.log(1.0 + pr[idx])

    return scores


def main():
    print("Loading document metadata")
    with open(docMetaData, "r") as f:
        doc_meta = json.load(f)

    #get docid from url
    url_to_docid = {}
    for docid_str, meta in doc_meta.items():
        url = meta.get("url", "")
        if url:
            url_to_docid[url] = int(docid_str)

    print(f"  {len(url_to_docid)} URLs in index.")

    print("Loading link graph")
    with open(linkGraph, "r") as f:
        link_graph = json.load(f)
    print(f"  {len(link_graph)} pages have recorded outgoing links.")

    print("Computing PageRank")
    scores = compute_pagerank(link_graph, url_to_docid)

    print(f"Saving PageRank scores for {len(scores)} documents -> {prFile}")
    with open(prFile, "w") as f:
        json.dump(scores, f)

    #page rank report
    if scores:
        sorted_scores = sorted(scores.values(), reverse=True)
        print(f"  Max PR score : {sorted_scores[0]:.4f}")
        print(f"  Median PR score: {sorted_scores[len(sorted_scores)//2]:.4f}")
        print(f"  Min PR score : {sorted_scores[-1]:.4f}")
    print("Completed PR Report")


if __name__ == "__main__":
    main()