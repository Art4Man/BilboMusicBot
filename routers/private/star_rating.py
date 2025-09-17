from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
import services.playlist_service as ps
from utils.logging import get_logger
from utils.messages import EMOJIS
from utils.typing import (
    get_user_id,
    get_callback_text_safe,
    get_callback_message,
    get_edit_text_message,
    get_edit_markup_message
)
from keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton

logger = get_logger(__name__)

star_rating_router = Router()


def get_star_amount_keyboard(playlist_identifier: str):
    """Create keyboard with different star amounts to give."""
    inline_keyboard = [
        [
            InlineKeyboardButton(text="1 ⭐", callback_data=f"rate_stars:1:{playlist_identifier}"),
            InlineKeyboardButton(text="3 ⭐", callback_data=f"rate_stars:3:{playlist_identifier}"),
            InlineKeyboardButton(text="5 ⭐", callback_data=f"rate_stars:5:{playlist_identifier}")
        ],
        [
            InlineKeyboardButton(text="10 ⭐", callback_data=f"rate_stars:10:{playlist_identifier}"),
            InlineKeyboardButton(text="25 ⭐", callback_data=f"rate_stars:25:{playlist_identifier}"),
            InlineKeyboardButton(text="50 ⭐", callback_data=f"rate_stars:50:{playlist_identifier}")
        ],
        [
            InlineKeyboardButton(text="🔙 Back", callback_data=f"back_to_playlist:{playlist_identifier}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


@star_rating_router.callback_query(F.data.startswith("give_stars:"))
async def handle_give_stars(callback: CallbackQuery):
    """
    Handle the 'Give Stars' button press, showing star amount options.
    """
    callback_text = get_callback_text_safe(callback)
    callback_message = get_callback_message(callback)
    user_id = get_user_id(callback)
    
    playlist_identifier = callback_text.split(":", 1)[1]
    
    # Get playlist info for rating stats
    user_db_id = ps.get_user_id(user_id)
    if user_db_id is None:
        logger.error(f"Cannot resolve DB user id for telegram_id={user_id}")
        await callback.answer("Internal error. Please try /start and retry.", show_alert=True)
        return
    
    # Determine if we have a playlist ID or name
    if playlist_identifier.startswith("id:"):
        playlist_id = int(playlist_identifier[3:])
        playlist_name = ps.get_playlist_name_by_id(playlist_id)
        if playlist_name is None:
            await callback.answer("Playlist not found.", show_alert=True)
            return
    else:
        playlist_name = playlist_identifier
        playlist_id = ps.get_playlist_id_by_name(user_db_id, playlist_name)
        if playlist_id is None:
            await callback.answer("Playlist not found.", show_alert=True)
            return
    
    # Check if user owns this playlist
    playlist_owner_id = ps.get_playlist_owner_id(playlist_id)
    if playlist_owner_id == user_db_id:
        await callback.answer("You cannot rate your own playlist!", show_alert=True)
        return
    
    # Get rating stats
    rating_stats = ps.get_playlist_rating_stats(playlist_id)
    user_rating = ps.get_user_playlist_rating(user_db_id, playlist_id)
    
    edit_text_message = get_edit_text_message(callback_message)
    edit_markup_message = get_edit_markup_message(callback_message)
    
    stats_text = ""
    if rating_stats and rating_stats['total_ratings'] > 0:
        stats_text = f"\n\n💫 Current rating: {rating_stats['average_stars']}⭐ ({rating_stats['total_ratings']} ratings, {rating_stats['total_stars']} total stars)"
    
    user_rating_text = ""
    if user_rating:
        user_rating_text = f"\n\n🌟 You already gave {user_rating} stars to this playlist!"
    
    await edit_text_message(f"{EMOJIS.STAR.value} Give stars to playlist '{playlist_name}'\n\nSelect how many stars you want to give:{stats_text}{user_rating_text}")
    await edit_markup_message(reply_markup=get_star_amount_keyboard(playlist_identifier))
    
    await callback.answer()


@star_rating_router.callback_query(F.data.startswith("rate_stars:"))
async def handle_rate_stars(callback: CallbackQuery, bot: Bot):
    """
    Handle star rating selection and create Telegram Stars payment.
    """
    callback_text = get_callback_text_safe(callback)
    callback_message = get_callback_message(callback)
    user_id = get_user_id(callback)
    
    # Parse callback data: rate_stars:<stars>:<playlist_identifier>
    parts = callback_text.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Invalid rating data.", show_alert=True)
        return
    
    stars_amount = int(parts[1])
    playlist_identifier = parts[2]
    
    # Get playlist info
    user_db_id = ps.get_user_id(user_id)
    if user_db_id is None:
        await callback.answer("Internal error. Please try /start and retry.", show_alert=True)
        return
    
    # Determine if we have a playlist ID or name
    if playlist_identifier.startswith("id:"):
        playlist_id = int(playlist_identifier[3:])
        playlist_name = ps.get_playlist_name_by_id(playlist_id)
        if playlist_name is None:
            await callback.answer("Playlist not found.", show_alert=True)
            return
    else:
        playlist_name = playlist_identifier
        playlist_id = ps.get_playlist_id_by_name(user_db_id, playlist_name)
        if playlist_id is None:
            await callback.answer("Playlist not found.", show_alert=True)
            return
    
    try:
        # Create Telegram Stars payment invoice
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Rate Playlist: {playlist_name}",
            description=f"Give {stars_amount} stars to the playlist '{playlist_name}'",
            payload=f"rate_playlist_{playlist_id}_{stars_amount}",
            provider_token="",  # Empty for Telegram Stars
            currency="XTR",  # Telegram Stars currency
            prices=[LabeledPrice(label=f"{stars_amount} ⭐", amount=stars_amount)],
            start_parameter=f"rate_{playlist_id}_{stars_amount}"
        )
        
        await callback.answer("Payment invoice sent! Complete the payment to give stars.", show_alert=True)
        
    except TelegramBadRequest as e:
        logger.error(f"Failed to create payment invoice: {e}")
        await callback.answer("Failed to create payment. Stars might not be supported in this chat.", show_alert=True)
    except Exception as e:
        logger.error(f"Error creating payment invoice: {e}", exc_info=True)
        await callback.answer("An error occurred while creating the payment.", show_alert=True)


@star_rating_router.callback_query(F.data.startswith("back_to_playlist:"))
async def handle_back_to_playlist(callback: CallbackQuery):
    """
    Handle going back to playlist actions from star rating.
    """
    callback_text = get_callback_text_safe(callback)
    callback_message = get_callback_message(callback)
    
    playlist_identifier = callback_text.split(":", 1)[1]
    
    # Determine if we have a playlist ID or name
    if playlist_identifier.startswith("id:"):
        playlist_id = int(playlist_identifier[3:])
        playlist_name = ps.get_playlist_name_by_id(playlist_id)
        if playlist_name is None:
            await callback.answer("Playlist not found.", show_alert=True)
            return
        # For shared playlists, just show the rating message without full actions
        edit_text_message = get_edit_text_message(callback_message)
        await edit_text_message(f"{EMOJIS.STAR.value} Rate this playlist:")
        await callback.answer()
        return
    else:
        playlist_name = playlist_identifier
    
    edit_text_message = get_edit_text_message(callback_message)
    edit_markup_message = get_edit_markup_message(callback_message)
    
    from keyboards.inline import get_playlist_actions_keyboard
    
    await edit_text_message(f"{EMOJIS.PEN.value} Select action for playlist '{playlist_name}':")
    await edit_markup_message(reply_markup=get_playlist_actions_keyboard(playlist_name))
    
    await callback.answer()


@star_rating_router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """
    Handle pre-checkout query for Telegram Stars payments.
    """
    # Always approve Telegram Stars payments
    await pre_checkout_query.answer(ok=True)


@star_rating_router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    """
    Handle successful Telegram Stars payment and record the rating.
    """
    payment = message.successful_payment
    user_id = get_user_id(message)
    
    # Parse payload: rate_playlist_<playlist_id>_<stars_amount>
    payload_parts = payment.invoice_payload.split("_")
    if len(payload_parts) != 4 or payload_parts[0] != "rate" or payload_parts[1] != "playlist":
        logger.error(f"Invalid payment payload: {payment.invoice_payload}")
        await message.answer(f"{EMOJIS.FAIL.value} Payment processing error.")
        return
    
    try:
        playlist_id = int(payload_parts[2])
        stars_amount = int(payload_parts[3])
    except ValueError:
        logger.error(f"Invalid playlist_id or stars_amount in payload: {payment.invoice_payload}")
        await message.answer(f"{EMOJIS.FAIL.value} Payment processing error.")
        return
    
    # Get user DB ID
    user_db_id = ps.get_user_id(user_id)
    if user_db_id is None:
        logger.error(f"Cannot resolve DB user id for telegram_id={user_id}")
        await message.answer(f"{EMOJIS.FAIL.value} Internal error.")
        return
    
    # Record the rating
    result = ps.add_playlist_rating(
        user_db_id, 
        playlist_id, 
        stars_amount, 
        payment.telegram_payment_charge_id
    )
    
    if result:
        playlist_name = ps.get_playlist_name_by_id(playlist_id)
        rating_stats = ps.get_playlist_rating_stats(playlist_id)
        
        stats_text = ""
        if rating_stats:
            stats_text = f"\n\n💫 New rating: {rating_stats['average_stars']}⭐ ({rating_stats['total_ratings']} ratings total)"
        
        await message.answer(
            f"{EMOJIS.CHECK_MARK.value} Thank you! You gave {stars_amount} stars to playlist '{playlist_name}'{stats_text}"
        )
        logger.info(f"User {user_id} gave {stars_amount} stars to playlist_id={playlist_id}")
    else:
        await message.answer(f"{EMOJIS.FAIL.value} Failed to record your rating. Please try again.")
        logger.error(f"Failed to record rating for user {user_id}, playlist {playlist_id}")