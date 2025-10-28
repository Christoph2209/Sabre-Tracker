"""
    This is the main code for the Sabre Tracker UI
    This will start with a log in screen, a refresh button
        NEEDS:
            Main Tab
                -
            League Tab
            Valorant Tab
"""
import tkinter as tk
from tkinter import ttk, messagebox
from LeagueTracker import get_player_stats, get_puuid
from PIL import Image, ImageTk
from dotenv import load_dotenv
import os


load_dotenv()

api_key = os.environ.get('riot_api_key')


def fetch_data():
    name = name_entry.get().strip()
    tag = tag_entry.get().strip()
    matches = match_entry.get().strip()
    puuid = get_puuid(gameName=name,tagLine=tag,api_key=api_key)
    if not name or not tag:
        messagebox.showwarning("Missing Info", "Enter both name and tag.")
        return

    try:
        df = get_player_stats(puuid, match_count=matches)
        if df.empty:
            output_box.insert(tk.END, "No matches found.\n")
            return

        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, f"Stats for {name}#{tag}\n\n")
        for _, row in df.iterrows():
            result = "✅ Win" if row["win"] else "❌ Loss"
            output_box.insert(
                tk.END,
                f"{row['role']} ({row['game_duration']}m) — {row['champion']}: "
                f"{row['kills']}/{row['deaths']}/{row['assists']} — {result}\n"
                f"Items:\n\t{row['item0']}, {row['item1']}, {row['item2']}, {row['item3']}, {row['item4']}, {row['item5']}, {row['item6']} \n\n"
            )
    except Exception as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Sabre Tracker")
root.geometry("800x400")

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="Summoner Name:").grid(row=0, column=0)
name_entry = ttk.Entry(frame, width=10)
name_entry.grid(row=0, column=1, padx=5)

ttk.Label(frame, text="Tagline:").grid(row=0, column=2)
tag_entry = ttk.Entry(frame, width=10)
tag_entry.grid(row=0, column=3, padx=5)

ttk.Label(frame, text="Matches:").grid(row=0, column=4)
match_entry = ttk.Entry(frame, width=5)
match_entry.grid(row=0, column=6, padx=5)

fetch_btn = ttk.Button(frame, text="Fetch Stats", command=fetch_data)
fetch_btn.grid(row=0, column=8, padx=10)

output_box = tk.Text(frame, wrap="word", width=70, height=20)
output_box.grid(row=1, column=0, columnspan=10, pady=10)

root.mainloop()
