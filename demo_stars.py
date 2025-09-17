#!/usr/bin/env python3
"""
Demo script showing Telegram Stars functionality for playlist likes.

This script demonstrates the database operations and service functions
for the Telegram Stars integration without requiring a bot token.
"""

import os
import sqlite3

# Set a dummy bot token to avoid config errors
os.environ['BOT_TOKEN'] = 'demo_token'

from database.db import init_db, sqlite_db_path
import services.playlist_service as ps
from keyboards.inline import get_shared_playlist_keyboard


def demo_stars_functionality():
    """Demonstrate the complete Stars functionality."""
    
    print("🎵 Bilbo Music Bot - Telegram Stars Demo")
    print("=" * 50)
    
    # Initialize database
    print("1. Initializing database...")
    init_db()
    print("   ✓ Database initialized successfully")
    
    # Create demo users
    print("\n2. Creating demo users...")
    ps.add_user(12345)  # Creator
    ps.add_user(67890)  # Fan 1
    ps.add_user(11111)  # Fan 2
    
    creator_id = ps.get_user_id(12345)
    fan1_id = ps.get_user_id(67890)
    fan2_id = ps.get_user_id(11111)
    
    print(f"   ✓ Creator user created (DB ID: {creator_id})")
    print(f"   ✓ Fan 1 user created (DB ID: {fan1_id})")
    print(f"   ✓ Fan 2 user created (DB ID: {fan2_id})")
    
    # Create demo playlist
    print("\n3. Creating demo playlist...")
    ps.create_playlist(creator_id, "Awesome Mix Vol. 1")
    playlist_id = ps.get_playlist_id_by_name(creator_id, "Awesome Mix Vol. 1")
    print(f"   ✓ Created playlist 'Awesome Mix Vol. 1' (ID: {playlist_id})")
    
    # Check initial state
    print("\n4. Initial playlist state...")
    likes_count = ps.get_playlist_likes_count(playlist_id)
    print(f"   ✓ Initial likes count: {likes_count}")
    
    # Simulate first fan liking the playlist
    print("\n5. Fan 1 likes the playlist...")
    has_liked_before = ps.has_user_liked_playlist(fan1_id, playlist_id)
    print(f"   • Fan 1 has liked before: {has_liked_before}")
    
    like_result = ps.add_playlist_like(fan1_id, playlist_id, 1, "star_charge_123")
    print(f"   ✓ Like recorded: {like_result}")
    
    likes_after_1 = ps.get_playlist_likes_count(playlist_id)
    has_liked_after = ps.has_user_liked_playlist(fan1_id, playlist_id)
    print(f"   ✓ Likes count after Fan 1: {likes_after_1}")
    print(f"   ✓ Fan 1 has liked now: {has_liked_after}")
    
    # Simulate second fan liking the playlist
    print("\n6. Fan 2 likes the playlist...")
    ps.add_playlist_like(fan2_id, playlist_id, 1, "star_charge_456")
    likes_after_2 = ps.get_playlist_likes_count(playlist_id)
    print(f"   ✓ Likes count after Fan 2: {likes_after_2}")
    
    # Try duplicate like (should replace)
    print("\n7. Fan 1 tries to like again...")
    ps.add_playlist_like(fan1_id, playlist_id, 1, "star_charge_789")
    likes_final = ps.get_playlist_likes_count(playlist_id)
    print(f"   ✓ Final likes count (should be same): {likes_final}")
    
    # Show keyboard examples
    print("\n8. UI Keyboard examples...")
    kb_not_liked = get_shared_playlist_keyboard(playlist_id, False)
    kb_already_liked = get_shared_playlist_keyboard(playlist_id, True)
    
    print("   ✓ Keyboard for user who hasn't liked:")
    print(f"     Button text: {kb_not_liked.inline_keyboard[0][0].text}")
    print(f"     Callback data: {kb_not_liked.inline_keyboard[0][0].callback_data}")
    
    print("   ✓ Keyboard for user who already liked:")
    print(f"     Button text: {kb_already_liked.inline_keyboard[0][0].text}")
    print(f"     Callback data: {kb_already_liked.inline_keyboard[0][0].callback_data}")
    
    # Show database contents
    print("\n9. Database contents...")
    with sqlite3.connect(sqlite_db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT pl.user_id, u.telegram_id, pl.playlist_id, pl.star_amount, 
                   pl.transaction_date, pl.telegram_payment_charge_id 
            FROM playlist_likes pl 
            JOIN users u ON pl.user_id = u.id
        """)
        likes = cur.fetchall()
        
        print("   Playlist likes in database:")
        for like in likes:
            user_id, telegram_id, playlist_id, stars, date, charge = like
            print(f"     • User {telegram_id}: {stars} ⭐ for playlist {playlist_id} (charge: {charge})")
    
    print("\n" + "=" * 50)
    print("🌟 Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("• ✓ Database schema with playlist_likes table")
    print("• ✓ Service functions for adding/counting likes")
    print("• ✓ Duplicate prevention (same user can't like twice)")
    print("• ✓ UI keyboard generation based on like status")
    print("• ✓ Payment charge ID tracking")
    print("\nReady for production with real Telegram bot! 🚀")


if __name__ == "__main__":
    demo_stars_functionality()