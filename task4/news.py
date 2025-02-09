import requests
import sqlite3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from newspaper import Article
from bs4 import BeautifulSoup
import nltk

nltk.download("punkt")  # Needed for text processing in newspaper3k

# News sources
NEWS_SOURCES = {
    "Technology": ["https://www.theverge.com", "https://techcrunch.com"],
    "Business": ["https://www.bbc.com/news/business", "https://www.cnn.com/business"],
    "Sports": ["https://www.espn.com", "https://www.bbc.com/sport"],
    "Entertainment": ["https://www.billboard.com", "https://variety.com"]
}

# Keywords for recommendations
USER_PREFERENCES = {
    "Technology": ["AI", "Machine Learning", "Cybersecurity", "Blockchain"],
    "Business": ["Stock Market", "Economy", "Investing", "Startups"],
    "Sports": ["Football", "Cricket", "Tennis", "Olympics"],
    "Entertainment": ["Movies", "Music", "Celebrities", "Hollywood"]
}

# Database setup
DB_NAME = "news.db"

def setup_database():
    """Create the news table if it doesn't exist"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            published_date TEXT,
            content TEXT,
            source TEXT,
            category TEXT
        )
    """)
    conn.commit()
    conn.close()

def scrape_news():
    """Scrape news and store them in the database"""
    setup_database()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for category, urls in NEWS_SOURCES.items():
        for url in urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                for link in soup.find_all("a", href=True):
                    article_url = link["href"]
                    if article_url.startswith("http"):
                        try:
                            article = Article(article_url)
                            article.download()
                            article.parse()

                            cursor.execute("INSERT INTO news (title, author, published_date, content, source, category) VALUES (?, ?, ?, ?, ?, ?)",
                                           (article.title, ", ".join(article.authors), str(article.publish_date), article.text, url, category))
                            conn.commit()

                        except Exception as e:
                            print(f"Skipping {article_url} - {e}")

            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch {url}: {e}")

    conn.close()
    load_news()
    messagebox.showinfo("Success", "News Scraping Completed ✅")

def load_news():
    """Load news from database into the GUI"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category FROM news ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()

    news_listbox.delete(*news_listbox.get_children())  # Clear previous data
    for row in rows:
        news_listbox.insert("", "end", values=row)

def show_full_article(event):
    """Display full news article when a title is clicked"""
    selected_item = news_listbox.selection()
    if selected_item:
        item = news_listbox.item(selected_item)
        news_id = item["values"][0]

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT title, author, published_date, content FROM news WHERE id=?", (news_id,))
        article = cursor.fetchone()
        conn.close()

        if article:
            title, author, date, content = article
            article_text.delete("1.0", tk.END)  # Clear previous content
            article_text.insert(tk.END, f"Title: {title}\n")
            article_text.insert(tk.END, f"Author: {author}\n")
            article_text.insert(tk.END, f"Published Date: {date}\n\n")
            article_text.insert(tk.END, content)

def recommend_news():
    """Recommend news articles based on selected category"""
    selected_category = category_var.get()
    if not selected_category:
        messagebox.showwarning("Warning", "Please select a category!")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM news WHERE category=?", (selected_category,))
    articles = cursor.fetchall()
    conn.close()

    recommended_articles = []
    for title, content in articles:
        for keyword in USER_PREFERENCES[selected_category]:
            if keyword.lower() in content.lower():
                recommended_articles.append(title)
                break  # Stop checking after the first match

    recommendations_listbox.delete(*recommendations_listbox.get_children())  # Clear previous recommendations
    for title in recommended_articles:
        recommendations_listbox.insert("", "end", values=[title])

# Tkinter GUI
root = tk.Tk()
root.title("Personalized News Recommender")
root.geometry("1000x600")

# Scrape Button
scrape_button = tk.Button(root, text="Scrape News", command=scrape_news, font=("Arial", 12), bg="lightblue")
scrape_button.pack(pady=10)

# News Table
columns = ("ID", "Title", "Category")
news_listbox = ttk.Treeview(root, columns=columns, show="headings")

news_listbox.heading("ID", text="ID")
news_listbox.column("ID", width=50)
news_listbox.heading("Title", text="Title")
news_listbox.column("Title", width=500)
news_listbox.heading("Category", text="Category")
news_listbox.column("Category", width=150)

news_listbox.pack(fill="both", expand=True)
news_listbox.bind("<Double-1>", show_full_article)  # Double-click to view article

# Full Article View
article_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10)
article_text.pack(fill="both", expand=True, padx=10, pady=10)

# Recommendations Section
frame = tk.Frame(root)
frame.pack(fill="both", expand=True, padx=10, pady=10)

category_var = tk.StringVar()
category_label = tk.Label(frame, text="Select Category:", font=("Arial", 12))
category_label.grid(row=0, column=0, padx=5, pady=5)

category_dropdown = ttk.Combobox(frame, textvariable=category_var, values=list(NEWS_SOURCES.keys()), font=("Arial", 12))
category_dropdown.grid(row=0, column=1, padx=5, pady=5)

recommend_button = tk.Button(frame, text="Get Recommendations", command=recommend_news, font=("Arial", 12), bg="lightgreen")
recommend_button.grid(row=0, column=2, padx=5, pady=5)

# Recommended News Table
recommendations_listbox = ttk.Treeview(root, columns=["Recommended Articles"], show="headings")
recommendations_listbox.heading("Recommended Articles", text="Recommended Articles")
recommendations_listbox.column("Recommended Articles", width=800)
recommendations_listbox.pack(fill="both", expand=True, padx=10, pady=10)

# Load News on Start
setup_database()
load_news()

root.mainloop()
