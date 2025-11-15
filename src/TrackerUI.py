import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from io import BytesIO
import requests
from dotenv import load_dotenv
from scipy.stats import alpha

from LeagueTracker import get_player_stats, get_puuid, get_images
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import sys
import os
load_dotenv()
api_key = os.environ.get('riot_api_key')

# -------------------------------
# Image cache to avoid reloading
# -------------------------------
image_cache = {}
player_cache = {}


# Function to get the correct path for bundled files
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# -------------------------------
# Tooltip Class
# -------------------------------
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, _):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background="#2b2b2b",
            foreground="#ffffff",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=5,
            pady=3
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


# -------------------------------
# Load image from URL safely
# -------------------------------
def load_image_from_url(url, size=(40, 40)):
    """
    Loads an image from a URL safely. Returns a placeholder if the URL fails or is invalid.
    """
    # Check cache first
    cache_key = f"{url}_{size[0]}x{size[1]}"
    if cache_key in image_cache:
        return image_cache[cache_key]

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return placeholder_image(size)

        img = Image.open(BytesIO(response.content))
        img = img.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)

        # Cache the image
        image_cache[cache_key] = photo
        return photo
    except Exception as e:
        print(f"Failed to load image: {url} -> {e}")
        return placeholder_image(size)


# -------------------------------
# Placeholder gray image
# -------------------------------
def placeholder_image(size=(40, 40)):
    cache_key = f"placeholder_{size[0]}x{size[1]}"
    if cache_key in image_cache:
        return image_cache[cache_key]

    img = Image.new("RGBA", size, (60, 60, 60, 255))
    photo = ImageTk.PhotoImage(img)
    image_cache[cache_key] = photo
    return photo


# -------------------------------
# Get item name from ID
# -------------------------------
_item_name_cache = None


def get_item_name(item_id):
    """Returns the item name for a given item ID"""
    global _item_name_cache

    if _item_name_cache is None:
        items_url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json"
        try:
            items_data = requests.get(items_url, timeout=10).json()
            _item_name_cache = {int(item["id"]): item.get("name", "Unknown Item") for item in items_data}
        except Exception as e:
            print(f"Error fetching item names: {e}")
            _item_name_cache = {}

    return _item_name_cache.get(int(item_id), "Unknown Item")


# -------------------------------
# Preload data on startup
# -------------------------------
def preload_data():
    """Preloads item and character data in background"""

    def load():
        try:
            # This will populate the caches
            get_item_name(1001)  # Load item cache
            from LeagueTracker import _item_data_cache, _character_data_cache

            # Preload character data by making a dummy call
            import pandas as pd
            from LeagueTracker import make_it_pretty
            dummy_df = pd.DataFrame({'champion': [1]})
            make_it_pretty(dummy_df)

            print("Data preloaded successfully!")
        except Exception as e:
            print(f"Preload error: {e}")

    thread = threading.Thread(target=load, daemon=True)
    thread.start()


# -------------------------------
# Create K/D Graph
# -------------------------------
def create_kd_graph(df, parent_frame):
    """Creates a K/D ratio graph for all matches"""
    # Clear any existing graph
    for widget in parent_frame.winfo_children():
        widget.destroy()

    # Calculate K/D ratio for each match (handle division by zero)
    kd_ratios = []
    win_status = []
    for _, row in df.iterrows():
        deaths = row['deaths'] if row['deaths'] > 0 else 1  # Avoid division by zero
        kd = row['kills'] / deaths
        kd_ratios.append(kd)
        win_status.append(row['win'])
    win_status.reverse()
    kd_ratios.reverse()

    # Create figure with dark theme
    fig = Figure(figsize=(5, 6), facecolor='#1c1c1c')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#2b2b2b')

    scatter_points = []

    # Plot the K/D ratios
    game_numbers = list(range(1, len(kd_ratios) + 1))
    for i, (game_num, kd, win) in enumerate(zip(game_numbers, kd_ratios, win_status)):
        color = '#6fff6f' if win else '#ff6f6f'

        # Plot the point
        scatter = ax.scatter(game_num, kd, s=100, c=color,
                             edgecolors='#ffffff', linewidths=1.5, zorder=5)
        scatter_points.append((game_num, kd, win))

        # Draw line to next point if not the last point
        if i < len(game_numbers) - 1:
            next_color = '#6fff6f' if win_status[i + 1] else '#ff6f6f'
            # Use gradient-like color (average of current and next)
            ax.plot([game_num, game_numbers[i + 1]], [kd, kd_ratios[i + 1]],
                    color=color, linewidth=2, alpha=0.6)
    # Add a horizontal line at K/D = 1.0
    ax.axhline(y=1.0, color='#ff6f6f', linestyle='--', linewidth=1, alpha=0.5)

    highlight = ax.scatter([], [], s=200, c='yellow', alpha=0.5, zorder=10)

    annot = ax.annotate("", xy=(0,0), xytext=(10,10),
                        textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.5", fc="#3c3c3c", ec="#ffffff", alpha=0.9),
                        color='#ffffff', fontsize=9, zorder=11)
    annot.set_visible(False)
    # Styling
    ax.set_xlabel('Game Number\n(Oldest → Most Recent)', color='#f8f8f8', fontsize=9)
    ax.set_ylabel('K/D Ratio', color='#f8f8f8', fontsize=10)
    ax.set_title('K/D Performance', color='#f8f8f8', fontsize=11, fontweight='bold')
    ax.tick_params(colors='#d0d0d0', labelsize=8)
    ax.grid(True, alpha=0.2, color='#ffffff')
    ax.set_xticks(game_numbers)

    # Style the spines
    for spine in ax.spines.values():
        spine.set_edgecolor('#3c3c3c')

    fig.tight_layout()

    def on_hover(event):
        if event.inaxes == ax:
            # Find closest point
            closest_dist = float('inf')
            closest_point = None

            for game_num, kd, win in scatter_points:
                # Convert data coordinates to display coordinates
                point_x, point_y = ax.transData.transform((game_num, kd))
                mouse_x, mouse_y = event.x, event.y

                dist = ((point_x - mouse_x) ** 2 + (point_y - mouse_y) ** 2) ** 0.5

                if dist < 20 and dist < closest_dist:  # 20 pixel threshold
                    closest_dist = dist
                    closest_point = (game_num, kd, win)

            if closest_point:
                game_num, kd, win = closest_point
                highlight.set_offsets([[game_num, kd]])
                highlight.set_visible(True)

                result = "Win" if win else "Loss"
                annot.xy = (game_num, kd)
                annot.set_text(f"Game {game_num}\nK/D: {kd:.2f}\n{result}")

                if game_num > len(scatter_points) * 0.7:
                    annot.set_position((-40,10))
                else:
                    annot.set_position((10,10))

                annot.set_visible(True)
            else:
                highlight.set_visible(False)
                annot.set_visible(False)

            fig.canvas.draw_idle()

    # Embed in tkinter
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.mpl_connect('motion_notify_event', on_hover)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# -------------------------------
# Damage Graph
# -------------------------------
def create_damage_graph(df, parent_frame):
    """Creates a damage dealt graph for all matches"""
    # Clear any existing graph
    for widget in parent_frame.winfo_children():
        widget.destroy()

    # Get damage data
    damage_data = []
    win_status = []
    for _, row in df.iterrows():
        damage_data.append(row['total_damage_dealt'])
        win_status.append(row['win'])

    damage_data.reverse()
    win_status.reverse()

    # Create figure with dark theme
    fig = Figure(figsize=(5, 6), facecolor='#1c1c1c')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#2b2b2b')

    scatter_points = []
    # Plot the damage with colors based on win/loss
    game_numbers = list(range(1, len(damage_data) + 1))

    # Plot each point with appropriate color
    for i, (game_num, damage, win) in enumerate(zip(game_numbers, damage_data, win_status)):
        color = '#6fff6f' if win else '#ff6f6f'

        # Plot the point
        scatter = ax.plot(game_num, damage, marker='o', markersize=8,
                color=color, markerfacecolor=color, markeredgecolor='#ffffff',
                markeredgewidth=1.5)
        scatter_points.append((game_num, damage, win))
        # Draw line to next point if not the last point
        if i < len(game_numbers) - 1:
            ax.plot([game_num, game_numbers[i + 1]], [damage, damage_data[i + 1]],
                    color=color, linewidth=2, alpha=0.6)

    highlight = ax.scatter([], [], s=200, c='yellow', alpha=0.5, zorder=10)

    annot = ax.annotate("", xy=(0, 0), xytext=(10, 10),
                        textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.5", fc="#3c3c3c", ec="#ffffff", alpha=0.9),
                        color='#ffffff', fontsize=9, zorder=11)
    annot.set_visible(False)

    # Styling
    ax.set_xlabel('Game Number\n(Oldest → Most Recent)', color='#f8f8f8', fontsize=9)
    ax.set_ylabel('Damage to Champions', color='#f8f8f8', fontsize=10)
    ax.set_title('Damage Performance', color='#f8f8f8', fontsize=11, fontweight='bold')
    ax.tick_params(colors='#d0d0d0', labelsize=8)
    ax.grid(True, alpha=0.2, color='#ffffff')

    # Set x-axis to show integer game numbers
    ax.set_xticks(game_numbers)

    # Style the spines
    for spine in ax.spines.values():
        spine.set_edgecolor('#3c3c3c')

    fig.tight_layout()

    def on_hover(event):
        if event.inaxes == ax:
            # Find closest point
            closest_dist = float('inf')
            closest_point = None

            for game_num, kd, win in scatter_points:
                # Convert data coordinates to display coordinates
                point_x, point_y = ax.transData.transform((game_num, kd))
                mouse_x, mouse_y = event.x, event.y

                dist = ((point_x - mouse_x) ** 2 + (point_y - mouse_y) ** 2) ** 0.5

                if dist < 20 and dist < closest_dist:  # 20 pixel threshold
                    closest_dist = dist
                    closest_point = (game_num, kd, win)

            if closest_point:
                game_num, kd, win = closest_point
                highlight.set_offsets([[game_num, kd]])
                highlight.set_visible(True)

                result = "Win" if win else "Loss"
                annot.xy = (game_num, kd)
                annot.set_text(f"Game {game_num}\nDMG: {kd:.2f}\n{result}")

                if game_num > len(scatter_points) * 0.7:
                    annot.set_position((-40,10))
                else:
                    annot.set_position((10,10))

                annot.set_visible(True)
            else:
                highlight.set_visible(False)
                annot.set_visible(False)

            fig.canvas.draw_idle()
    # Embed in tkinter
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.mpl_connect('motion_notify_event', on_hover)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


# -------------------------------
# Create Creep Score Graph
# -------------------------------
def create_creep_graph(df, parent_frame):
    for widget in parent_frame.winfo_children():
        widget.destroy()

    # Get damage data
    minion_data = []
    win_status = []
    for _, row in df.iterrows():
        minion_data.append(row['minions'])
        win_status.append(row['win'])
    minion_data.reverse()
    win_status.reverse()

    fig = Figure(figsize=(5, 6), facecolor='#1c1c1c')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#2b2b2b')
    scatter_points = []
    # Plot the CS with colors based on win/loss
    game_numbers = list(range(1, len(minion_data) + 1))

    # Plot each point with appropriate color
    for i, (game_num, damage, win) in enumerate(zip(game_numbers, minion_data, win_status)):
        color = '#6fff6f' if win else '#ff6f6f'

        # Plot the point
        scatter = ax.plot(game_num, damage, marker='o', markersize=8,
                color=color, markerfacecolor=color, markeredgecolor='#ffffff',
                markeredgewidth=1.5)
        scatter_points.append((game_num, damage, win))
        # Draw line to next point if not the last point
        if i < len(game_numbers) - 1:
            ax.plot([game_num, game_numbers[i + 1]], [damage, minion_data[i + 1]],
                    color=color, linewidth=2, alpha=0.6)
    highlight = ax.scatter([], [], s=200, c='yellow', alpha=0.5, zorder=10)

    annot = ax.annotate("", xy=(0, 0), xytext=(10, 10),
                        textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.5", fc="#3c3c3c", ec="#ffffff", alpha=0.9),
                        color='#ffffff', fontsize=9, zorder=11)
    annot.set_visible(False)
    # Styling
    ax.set_xlabel('Game Number\n(Oldest → Most Recent)', color='#f8f8f8', fontsize=9)
    ax.set_ylabel('Creep Score', color='#f8f8f8', fontsize=10)
    ax.set_title('CS per Game', color='#f8f8f8', fontsize=11, fontweight='bold')
    ax.tick_params(colors='#d0d0d0', labelsize=8)
    ax.grid(True, alpha=0.2, color='#ffffff')

    # Set x-axis to show integer game numbers
    ax.set_xticks(game_numbers)

    # Style the spines
    for spine in ax.spines.values():
        spine.set_edgecolor('#3c3c3c')

    fig.tight_layout()

    def on_hover(event):
        if event.inaxes == ax:
            # Find closest point
            closest_dist = float('inf')
            closest_point = None

            for game_num, kd, win in scatter_points:
                # Convert data coordinates to display coordinates
                point_x, point_y = ax.transData.transform((game_num, kd))
                mouse_x, mouse_y = event.x, event.y

                dist = ((point_x - mouse_x) ** 2 + (point_y - mouse_y) ** 2) ** 0.5

                if dist < 20 and dist < closest_dist:  # 20 pixel threshold
                    closest_dist = dist
                    closest_point = (game_num, kd, win)

            if closest_point:
                game_num, kd, win = closest_point
                highlight.set_offsets([[game_num, kd]])
                highlight.set_visible(True)

                result = "Win" if win else "Loss"
                annot.xy = (game_num, kd)
                annot.set_text(f"Game {game_num}\nCS: {kd:.2f}\n{result}")

                if game_num > len(scatter_points) * 0.7:
                    annot.set_position((-40, 10))
                else:
                    annot.set_position((10, 10))

                annot.set_visible(True)
            else:
                highlight.set_visible(False)
                annot.set_visible(False)

            fig.canvas.draw_idle()

    # Embed in tkinter
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.mpl_connect('motion_notify_event', on_hover)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# -------------------------------
# Fetch Player Stats and Build UI
# -------------------------------
def fetch_data():
    name = name_entry.get().strip()
    tag = tag_entry.get().strip()
    matches = match_entry.get().strip() or 5

    if not name or not tag:
        messagebox.showwarning("Missing Info", "Enter both name and tag.")
        return

    def start_fetch():
        # Disable fetch button during load
        fetch_btn.config(state="disabled")

        def fetch_thread():
            try:
                # Check cache first
                cache_key = f"{name}#{tag}_{matches}"
                if cache_key in player_cache:
                    df = player_cache[cache_key]
                    print(f"Loaded from cache: {cache_key}")
                else:
                    puuid = get_puuid(gameName=name, tagLine=tag, api_key=api_key)
                    if not puuid:
                        root.after(0, lambda: messagebox.showerror("Error", "Player not found"))
                        root.after(0, lambda: fetch_btn.config(state="normal"))
                        return

                    df = get_player_stats(puuid, match_count=int(matches))

                    # Cache the result
                    player_cache[cache_key] = df

                if df.empty:
                    root.after(0, lambda: messagebox.showinfo("No Data", "No matches found."))
                    root.after(0, lambda: fetch_btn.config(state="normal"))
                    return

                # Update UI in main thread
                root.after(0, lambda: display_results(df, name, tag))

            except Exception as e:
                root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                root.after(0, lambda: fetch_btn.config(state="normal"))

        # Run fetch in separate thread
        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()

    # Use after() to ensure UI updates before starting thread
    root.after(10, start_fetch)


def display_results(df, name, tag):
    """Display the fetched results"""
    # Clear old results
    for widget in results_frame.winfo_children():
        widget.destroy()

    ttk.Label(results_frame, text=f"Stats for {name}#{tag}", style="Header.TLabel").pack(pady=5)

    # Create K/D graph
    create_kd_graph(df, kd_tab)
    create_damage_graph(df, damage_tab)
    create_creep_graph(df, cs_tab)

    # Display each match card
    for _, row in df.iterrows():
        create_match_card(row)


# -------------------------------
# Create Match Card
# -------------------------------
def create_match_card(row):
    card = ttk.Frame(results_frame, style="Card.TFrame", padding=10)
    card.pack(fill="x", pady=5)

    # Header row
    header = ttk.Frame(card, style="Card.TFrame")
    header.pack(fill="x", pady=3)

    ttk.Label(header, text=f"{row['role']} | {row['champion']}", style="Bold.TLabel").pack(side="left")

    kda = f"{row['kills']}/{row['deaths']}/{row['assists']}"
    ttk.Label(header, text=f"K/D/A: {kda}", style="TLabel").pack(side="left", padx=10)

    result_text = "✅ Win" if row["win"] else "❌ Loss"
    ttk.Label(header, text=result_text, style="Win.TLabel" if row["win"] else "Loss.TLabel").pack(side="right")

    # --- Items row ---
    try:
        item_urls = get_images(row)
    except Exception as e:
        print(f"Error getting item images: {e}")
        item_urls = []

    item_frame = ttk.Frame(card, style="Card.TFrame")
    item_frame.pack(pady=5)

    if not item_urls:
        ttk.Label(item_frame, text="No items built.", style="TLabel").pack(side="left", padx=5)
    else:
        # Store images in a list attached to the frame to prevent garbage collection
        if not hasattr(item_frame, 'item_images'):
            item_frame.item_images = []

        # Get all non-zero item IDs in order
        item_ids = []
        for j in range(7):
            try:
                item_val = int(row[f"item{j}"])
                if item_val != 0:
                    item_ids.append(item_val)
            except (KeyError, ValueError, TypeError):
                continue

        # Now match URLs to item IDs
        for i, url in enumerate(item_urls):
            if not url:
                continue

            # Get the corresponding item ID
            item_id = item_ids[i] if i < len(item_ids) else None

            img = load_image_from_url(url, size=(40, 40))
            lbl = ttk.Label(item_frame, image=img)
            lbl.pack(side="left", padx=3)

            # Add tooltip with item name
            if item_id:
                item_name = get_item_name(item_id)
                ToolTip(lbl, item_name)

            # Keep a reference to prevent garbage collection
            item_frame.item_images.append(img)


# -------------------------------
# UI Setup
# -------------------------------
root = tk.Tk()
root.title("Sabre Tracker")
root.geometry("900x600")
icon_image = tk.PhotoImage(file="src/icon.png")
try:
    icon_image = tk.PhotoImage(file=resource_path("src/icon.png"))
    root.iconphoto(False, icon_image)
except:
    pass  # If icon fails, just continue without it
style = ttk.Style()
style.theme_use("clam")

# Custom ttk styles
style.configure("TFrame", background="#1c1c1c")
style.configure("Card.TFrame", background="#2b2b2b", relief="groove")
style.configure("Header.TLabel", background="#1c1c1c", foreground="#f8f8f8", font=("Segoe UI", 14, "bold"))
style.configure("Bold.TLabel", background="#2b2b2b", foreground="#e0e0e0", font=("Segoe UI", 11, "bold"))
style.configure("TLabel", background="#2b2b2b", foreground="#d0d0d0", font=("Segoe UI", 10))
style.configure("Win.TLabel", background="#2b2b2b", foreground="#6fff6f", font=("Segoe UI", 10, "bold"))
style.configure("Loss.TLabel", background="#2b2b2b", foreground="#ff6f6f", font=("Segoe UI", 10, "bold"))
style.configure("TButton", padding=6, relief="flat", background="#3c3c3c", foreground="#ffffff")

# Input area
input_frame = ttk.Frame(root, padding=10)
input_frame.pack(fill="x")

ttk.Label(input_frame, text="Summoner Name:").pack(side="left")
name_entry = ttk.Entry(input_frame, width=15)
name_entry.pack(side="left", padx=5)

ttk.Label(input_frame, text="Tagline:").pack(side="left")
tag_entry = ttk.Entry(input_frame, width=10)
tag_entry.pack(side="left", padx=5)

ttk.Label(input_frame, text="Matches:").pack(side="left")
match_entry = ttk.Entry(input_frame, width=5)
match_entry.pack(side="left", padx=5)

fetch_btn = ttk.Button(input_frame, text="Fetch Stats", command=fetch_data)
fetch_btn.pack(side="left", padx=10)

# Main content area - split between match cards (left) and graph (right)
content_frame = ttk.Frame(root)
content_frame.pack(fill="both", expand=True)

# Scrollable Results (Left side)
container = ttk.Frame(content_frame)
canvas = tk.Canvas(container, bg="#1c1c1c", highlightthickness=0)
scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
results_frame = ttk.Frame(canvas)

results_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=results_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

container.pack(side="left", fill="both", expand=True)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Graph frame with tabs (Right side)
graph_container = ttk.Frame(content_frame, style="TFrame")
graph_container.pack(side="right", fill="both", padx=10, pady=10)

# Create notebook (tabs) for different graphs
notebook = ttk.Notebook(graph_container)
notebook.pack(fill="both", expand=True)

# Create tabs
kd_tab = ttk.Frame(notebook, style="TFrame")
damage_tab = ttk.Frame(notebook, style="TFrame")
cs_tab = ttk.Frame(notebook, style="TFrame")
#vision_tab = ttk.Frame(notebook, style="TFrame")

# Add tabs to notebook
notebook.add(kd_tab, text="K/D")
notebook.add(damage_tab, text="Damage")
notebook.add(cs_tab, text="CS")
#notebook.add(vision_tab, text="Vision")

# Preload data when app starts
preload_data()

root.mainloop()