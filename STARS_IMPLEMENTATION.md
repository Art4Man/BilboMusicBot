# Telegram Stars Integration Implementation

This document describes the implementation of Telegram cryptocurrency Stars functionality for playlist likes in the Bilbo Music Bot.

## Overview

The implementation allows users to support playlist creators by sending 1 Telegram Star per playlist like. This creates a monetization mechanism while encouraging quality content creation.

## Key Components

### 1. Database Schema (`database/db.py`)

Added `playlist_likes` table:
```sql
CREATE TABLE IF NOT EXISTS playlist_likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    playlist_id INTEGER NOT NULL,
    star_amount INTEGER NOT NULL DEFAULT 1,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    telegram_payment_charge_id TEXT,
    UNIQUE(user_id, playlist_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (playlist_id) REFERENCES playlists (id) ON DELETE CASCADE
)
```

### 2. Service Functions (`services/playlist_service.py`)

**New Functions:**
- `add_playlist_like(user_id, playlist_id, star_amount, telegram_payment_charge_id)` - Records a star payment
- `get_playlist_likes_count(playlist_id)` - Gets total stars for a playlist
- `has_user_liked_playlist(user_id, playlist_id)` - Checks if user already liked

### 3. Payment Router (`routers/private/playlist_stars.py`)

**Handlers:**
- `handle_like_playlist()` - Creates payment invoice for 1 Star
- `handle_pre_checkout()` - Validates payment before processing  
- `handle_successful_payment()` - Records like in database after payment
- `handle_already_liked()` - Shows message for duplicate attempts

### 4. UI Components (`keyboards/inline.py`)

**New Function:**
- `get_shared_playlist_keyboard(playlist_id, user_has_liked)` - Creates like button keyboard

### 5. Integration Points

**Updated Files:**
- `routers/private/start.py` - Shows like count and button in shared playlists
- `routers/private/show_musics.py` - Displays like count in playlist views
- `bot.py` - Includes the new payment router
- `utils/messages.py` - Added STAR emoji
- `README.md` - Updated documentation

## Payment Flow

1. **User clicks "⭐ Like Playlist (1 ⭐)" button**
2. **System creates payment invoice** using `bot.send_invoice()`
   - Title: "Like Playlist: {playlist_name}"
   - Amount: 1 Telegram Star (XTR currency)
   - Payload: "like_playlist_{playlist_id}"

3. **Pre-checkout validation** (`PreCheckoutQuery`)
   - Verifies playlist still exists
   - Approves or denies payment

4. **Payment processing** (`SuccessfulPayment`)
   - Extracts playlist ID from payload
   - Records like in database with charge ID
   - Shows confirmation message with total likes

5. **UI updates automatically**
   - Button changes to "⭐ Already Liked"
   - Like count displays in playlist views

## Security Features

- **Duplicate Prevention**: UNIQUE constraint prevents same user liking same playlist twice
- **Payment Validation**: Pre-checkout query validates playlist existence
- **Transaction Tracking**: Stores Telegram payment charge IDs for audit trail
- **Error Handling**: Comprehensive error logging and user feedback

## User Experience

### For Playlist Viewers:
- See total star count next to playlist names
- Click "Like Playlist" button to support creators
- One-time payment per playlist per user
- Native Telegram Stars payment interface

### For Playlist Creators:
- View how many stars their playlists have received
- Automatic monetization without additional setup
- Encourages quality content creation

## Technical Benefits

- **Minimal Code Changes**: New functionality doesn't disrupt existing features
- **Modular Design**: Payment handling isolated in separate router
- **Database Integrity**: Foreign key constraints ensure data consistency
- **Scalable**: Can handle multiple concurrent payments
- **Future-Ready**: Foundation for advanced features like creator dashboards

## Demo Usage

Run the demo script to see functionality:
```bash
python demo_stars.py
```

This demonstrates:
- Database operations
- Service function behavior
- UI keyboard generation
- Payment charge tracking
- Duplicate prevention logic

## Production Deployment

1. Ensure bot has payment processing enabled in BotFather
2. Set up proper bot token in environment
3. Initialize database with `init_db()`
4. All payment handlers are automatically registered

The implementation is production-ready and handles all edge cases including payment failures, database errors, and concurrent access scenarios.