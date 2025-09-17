# 🎵 Bilbo Music Bot

A Telegram bot that allows users to create, manage, and share music playlists made from Telegram audio files. Built with long-term goals of playlist NFTs on TON blockchain.

---

## ✨ Features

### Button-Based Interface

- **🎧 My Playlists** – View and manage your playlists with interactive buttons
- **➕ New Playlist** – Create a new playlist with guided prompts
- **Interactive Actions** – Add music, show tracks, delete, rename, set cover, and share playlists via inline buttons
- **Time-Windowed Adding** – Add multiple tracks to a playlist within a configurable time window
- **Confirmation Dialogs** – Safe playlist deletion with confirmation prompts
- **Cover Images** – Set custom cover images for your playlists
- **Playlist Sharing** – Generate shareable links that preview playlists to others
- **⭐ Telegram Stars Support** – Users can like playlists with Telegram Stars cryptocurrency payments

### Technical Features

- **FSM (Finite State Machine)** – Robust state management for multi-step interactions
- **Router-Based Architecture** – Modular, maintainable code structure
- **Concurrent Operations** – Works seamlessly with multiple users
- **SQLite Database** – Reliable local storage with automatic initialization

---

## 🧠 Vision

This bot is the first phase in a project that will:

- Allow users to mint their playlists as NFTs on the TON blockchain
- Create a music NFT ecosystem native to Telegram and TON

---

## 🏁 Setup

### 1. Install Requirements

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file with your bot token (get one from @BotFather):

```bash
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_NAME=playlist.db
ADD_TRACK_TIME_WINDOW=60
LOG_LEVEL=INFO
```

### 3. Run the Bot

```bash
python bot.py
```

---

## 🎮 How to Use

1. **Start the bot** – Send `/start` to begin
2. **Create a playlist** – Tap "➕ New Playlist" and enter a name
3. **Add music** – Select "Add Music" from playlist actions, then forward audio files
4. **Manage playlists** – Use "🎧 My Playlists" to view and manage your collections
5. **Share playlists** – Generate shareable links that others can preview
6. **Like playlists** – Support creators by sending 1 Telegram Star per playlist like

---

## 🗃 Database Schema (SQLite)

* `users`: `id` (PRIMARY KEY), `telegram_id` (UNIQUE)
* `playlists`: `id` (PRIMARY KEY), `user_id`, `name`, `cover_file_id`, UNIQUE(user_id, name)
* `tracks`: `id` (PRIMARY KEY), `playlist_id`, `file_id`, UNIQUE(playlist_id, file_id)
* `playlist_likes`: `id` (PRIMARY KEY), `user_id`, `playlist_id`, `star_amount`, `transaction_date`, `telegram_payment_charge_id`, UNIQUE(user_id, playlist_id)

---

## 📂 Project Structure

```
AnvaaliMusicBot/
├── bot.py                      # Main bot entry point
├── config.py                   # Configuration and environment variables
├── database/
│   └── db.py                   # Database initialization and schema
├── services/
│   └── playlist_service.py     # Playlist CRUD operations
├── routers/
│   └── private/                # Private chat handlers
│       ├── start.py            # /start command and deep linking
│       ├── add_playlist.py     # New playlist creation
│       ├── add_track.py        # Track addition with time windows
│       ├── show_playlists.py   # Playlist listing and selection
│       ├── show_musics.py      # Track display with media groups
│       ├── rename_playlist.py  # Playlist renaming flow
│       ├── set_cover.py        # Cover image setting
│       ├── share_playlist.py   # Playlist sharing links
│       ├── remove_track.py     # Track removal by index
│       ├── remove_playlist.py  # Playlist deletion with confirmation
│       └── playlist_stars.py   # Telegram Stars payment handling
├── keyboards/
│   ├── inline.py               # Inline keyboard builders
│   └── reply.py                # Reply keyboard builders
├── states/
│   └── user.py                 # FSM state definitions
├── utils/
│   ├── filters.py              # Custom aiogram filters
│   ├── messages.py             # Message utility functions
│   ├── typing.py               # Type-safe accessor functions
│   └── logging.py              # Logging configuration
└── requirements.txt
```

---

## 🔧 Technical Details

- **Framework**: aiogram v3 with Router-based architecture
- **State Management**: FSM (Finite State Machine) for multi-step interactions
- **Database**: SQLite with context-managed connections
- **Keyboards**: Inline and reply keyboards for intuitive UX
- **Error Handling**: Comprehensive logging and user feedback
- **Modularity**: Separate routers for each feature area
- **Payments**: Telegram Stars integration for playlist monetization

---

## 📬 Contributing

Feel free to fork, extend, or raise PRs. Ideas welcome for the future TON blockchain integration!
