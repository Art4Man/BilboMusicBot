from aiogram import Router, F
from aiogram.types import Message,CallbackQuery
from aiogram.fsm.context import FSMContext
from collections import defaultdict
import time
from typing import Dict, Any
from utils.typing import (
    get_user_id,
    get_message_text_safe,
    get_audio_file_id,
    get_audio_title,
    get_callback_message,
    get_callback_text_safe,
    get_edit_text_message
)
from config import app_config
from services.playlist_service import (
    add_track,
    get_playlist_id_by_name,
    get_user_id as get_db_user_id
)
from utils.logging import get_logger
from utils.messages import is_text_starts_with_emoji
from utils.filters import IgnoreIfInPlaylistState
from states.user import PlaylistStates


logger = get_logger(__name__)

add_track_router = Router()
add_track_router.message.filter(IgnoreIfInPlaylistState(exclude_state="waiting_for_add_music"))

user_contexts: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
    "playlist_name": None, 
    "playlist_db_id": None,
    "timestamp": 0,
    "tracks_added": 0
})


@add_track_router.message(
    lambda message,state:
        message.text is not None 
        and not message.text.startswith('/') 
        and not is_text_starts_with_emoji(message.text)
)
async def store_playlist_name(message: Message,state: FSMContext):
    user_id = get_user_id(message)
    user_db_id = get_db_user_id(user_id)
    message_text = get_message_text_safe(message)

    playlist_name = message_text.strip()
    if not playlist_name:
        await message.answer("❌ Please provide a valid playlist name.")
        return

    playlist_db_id = get_playlist_id_by_name(user_db_id,playlist_name)
    if playlist_db_id == False:
        logger.warning(f"User {user_id} tried to add to non-existent playlist '{playlist_name}'")
        await message.answer(
            f"❌ Playlist with name `{playlist_name}` is not exist for this user."
        )
        return

    user_contexts[user_id] = {
        "playlist_name": playlist_name,
        "playlist_db_id": playlist_db_id,
        "timestamp": time.time(),
        "tracks_added": 0
    }
    
    await state.set_state(PlaylistStates.waiting_for_add_music)

    
    logger.info(f"User {user_id} started adding music to '{playlist_name}'")
    await message.answer(
        f"🎵 Ready to add tracks to playlist: **{playlist_name}**\n"
        f"⏰ Forward audio files within {app_config.ADD_TRACK_TIME_WINDOW} seconds\n"
    )


@add_track_router.message(PlaylistStates.waiting_for_add_music, F.audio)
async def handle_forwarded_audio(message: Message,state: FSMContext):
    user_id = get_user_id(message)
    user_db_id = get_db_user_id(user_id)
    context = user_contexts.get(user_id)

    if not context or not context.get("playlist_name"):
        await message.answer("❌ No active playlist session. Send playlist name first.")
        await state.clear()
        return
    
    # Check time window
    if time.time() - context['timestamp'] > app_config.ADD_TRACK_TIME_WINDOW:
        logger.info(f"Time window expired for user {user_id}")
        await message.answer(
            f"⏰ Time window expired ({app_config.ADD_TRACK_TIME_WINDOW}s)\n"
            f"📝 Send the playlist name again to continue adding tracks."
        )
        user_contexts[user_id] = {
            "playlist_name": None,
            "playlist_db_id": None,
            "timestamp": 0,
            "tracks_added": 0
        }
        return await state.clear()

    playlist_name = context["playlist_name"]

    audio_file_id = get_audio_file_id(message)
    audio_title = get_audio_title(message)

    track_added = add_track(playlist_name,user_db_id,audio_file_id)
    if track_added is None:
        logger.error(f"Failed to add '{audio_title}' to {playlist_name} for user '{user_id}'.",exc_info=True)
        await message.answer(
            f"❌ Failed to add '{audio_title}' to {playlist_name}."
        )
    elif track_added == False:
        await message.answer(
            f"❌ Track with title='{audio_title}' already exists in **{playlist_name}** playlist."
        )
    else:
        context["tracks_added"] += 1
        
        await message.answer(
            f"✅ Added: **{audio_title}**\n"
            f"📂 To playlist: '{playlist_name}'\n"
            f"🎵 Total added this session: {context['tracks_added']}"
        )
        
        logger.info(f"User {user_id} added '{audio_title}' with file_id '{audio_file_id}' to '{playlist_name}'")


@add_track_router.callback_query(F.data.startswith("add_music:"))
async def handle_add_track_inline(callback: CallbackQuery):
    callback_text = get_callback_text_safe(callback)
    callback_message = get_callback_message(callback)
    edit_text_message = get_edit_text_message(callback_message)

    playlist_name = callback_text.split(":")[1]
    
    await edit_text_message(
        f"To add track to `{playlist_name}` "
        f"just forward tracks and type `{playlist_name}` "
        "as message, no need to press any button."
    )

    return await callback.answer()

