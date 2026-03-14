import tkinter as tk
from tkinter import ttk, messagebox
import search as se
import time

INDEX_FILE = "master_index.txt"  # merge.py output file
METADATA_FILE = "metadata.json"


def show_error():
    messagebox.showerror("Empty Query", "No query inputted, try again!")


class SearchEngine(tk.Tk):
    def __init__(self):
        super().__init__()

        # main window
        self.se = se.Searcher(INDEX_FILE)
        self.title("CS 121 Search Engine")
        self.geometry("1200x500")  # set the window size

        # Label Title
        self.window_label = ttk.Label(self, text="CS 121 Search Engine")
        self.window_label.config(font=("Helvetica", 24, "bold"))
        self.window_label.pack(pady=20)

        # Create and place widgets
        self.label = ttk.Label(self, text="What do we want to search for today?")
        self.label.pack(pady=20)  # Add some vertical padding

        self.text_box = tk.Entry(self, width=40)
        self.text_box.pack()

        self.query_button = ttk.Button(self, text="Submit Query", command=self.on_button_click)
        self.query_button.pack(pady=10)

        self.result_label = ttk.Label(self, text="")
        self.label_pack = False

        self.columns = ("Title", "docID", "Score", "URL")
        self.results_view = ttk.Treeview(self, columns=self.columns, show='headings')
        self.results_view.heading("Title", text="Title")
        self.results_view.heading("docID", text="docID")
        self.results_view.heading("Score", text="Score")
        self.results_view.heading("URL", text="URL")
        self.results_view.column("Title", width=500, minwidth=200, stretch=True)
        self.results_view.column("docID", width=70)
        self.results_view.column("Score", width=65)
        self.results_view.column("URL", width=750, minwidth=200, stretch=True)
        self.results_view_show = False

        self.response_time = ttk.Label(self, text="")


    def on_button_click(self):
        """Action performed when the button is clicked."""
        raw_query = self.text_box.get()
        if not raw_query:
            show_error()
            return
        self.text_box.delete(0, tk.END)
        self.present_results(raw_query)

    def get_results(self, query: str):
        return self.se.search(query)

    def present_results(self, query):
        # clear window to prevent double widgets

        start_time = time.perf_counter() # start processing timeer
        results = self.get_results(query)
        end_time = time.perf_counter()  # end processing timer
        last_response_time = (end_time - start_time) * 1000 # converts to ms

        for item in self.results_view.get_children(): # clears results widget
            self.results_view.delete(item)

        if results:
            self.result_label.config(text=f"Here are the top 5 results for: {query}")
            self.response_time.config(text=f"Response Time: {last_response_time:.2f} ms")

            # get first 5 tuples
            # result structure is (doc_id, {'score': ..., 'url': ...})
            for doc_id, data in results[:5]:
                self.results_view.insert("", "end", values=(
                    data.get('title'),  # title column
                    doc_id,  # doc id column
                    f"{data.get('score'):.2f}",  # score column
                    data.get('url')  # url column
                ))
        else:
            self.result_label.config(text=f"No results found for: {query}")
            self.response_time.config(text=f"Response Time: {last_response_time:.2f} ms")

        # making sure everything appears in the window
        if not self.label_pack:
            self.result_label.pack()
            self.results_view.pack()
            self.response_time.pack()
            self.label_pack = True

if __name__ == "__main__":
    app = SearchEngine()
    app.mainloop()
