from aiogram import Router, F
from aiogram.types import CallbackQuery, PreCheckoutQuery, SuccessfulPayment, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot
import services.playlist_service as ps
from utils.logging import get_logger
from utils.messages import EMOJIS
from utils.typing import (
    get_user_id,
    get_callback_text_safe,
    get_callback_message,
    get_edit_text_message
)

logger = get_logger(__name__)

like_playlist_router = Router()


@like_playlist_router.callback_query(F.data.startswith("like_playlist:"))
async def handle_like_playlist(callback: CallbackQuery, bot: Bot):
    """
    Handle the "Like with Stars" callback: present payment options to the user.
    
    Creates an invoice for the user to contribute stars to a playlist they find valuable.
    Offers different star amounts as options (1, 5, 10 stars).
    """
    callback_text = get_callback_text_safe(callback)
    callback_message = get_callback_message(callback)
    edit_text_message = get_edit_text_message(callback_message)
    
    user_id = get_user_id(callback)
    playlist_name = callback_text.split(":", 1)[1]
    
    user_db_id = ps.get_user_id(user_id)
    if user_db_id is None:
        logger.error(f"Cannot resolve DB user id for telegram_id={user_id}")
        await edit_text_message(f"{EMOJIS.FAIL.value} Internal error occurred. Please try again.")
        return await callback.answer()
    
    playlist_id = ps.get_playlist_id_by_name(user_db_id, playlist_name)
    if playlist_id is None:
        await edit_text_message(f"{EMOJIS.FAIL.value} Playlist not found.")
        return await callback.answer()
    
    # Check if user has already liked this playlist
    if ps.user_has_liked_playlist(user_db_id, playlist_id):
        current_likes = ps.get_playlist_likes_count(playlist_id)
        total_stars = ps.get_playlist_total_stars(playlist_id)
        await edit_text_message(
            f"{EMOJIS.STAR.value} You have already liked this playlist!\n\n"
            f"{EMOJIS.MUSIC.value} **{playlist_name}**\n"
            f"{EMOJIS.STAR.value} {current_likes} likes • {total_stars} total stars"
        )
        return await callback.answer()
    
    # Create payment options keyboard
    payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{EMOJIS.STAR.value} 1 Star", callback_data=f"pay_stars:1:{playlist_name}"),
            InlineKeyboardButton(text=f"{EMOJIS.STAR.value} 5 Stars", callback_data=f"pay_stars:5:{playlist_name}")
        ],
        [
            InlineKeyboardButton(text=f"{EMOJIS.STAR.value} 10 Stars", callback_data=f"pay_stars:10:{playlist_name}"),
            InlineKeyboardButton(text=f"{EMOJIS.FAIL.value} Cancel", callback_data="cancel_payment")
        ]
    ])
    
    current_likes = ps.get_playlist_likes_count(playlist_id)
    total_stars = ps.get_playlist_total_stars(playlist_id)
    
    await edit_text_message(
        f"{EMOJIS.STAR.value} **Like with Stars**\n\n"
        f"{EMOJIS.MUSIC.value} Playlist: **{playlist_name}**\n"
        f"{EMOJIS.STAR.value} Current: {current_likes} likes • {total_stars} stars\n\n"
        f"Choose how many stars to contribute:",
        reply_markup=payment_keyboard
    )
    
    await callback.answer()


@like_playlist_router.callback_query(F.data.startswith("like_shared_playlist:"))
async def handle_like_shared_playlist(callback: CallbackQuery, bot: Bot):
    """
    Handle the "Like this Playlist" callback from shared playlists.
    """
    callback_text = get_callback_text_safe(callback)
    callback_message = get_callback_message(callback)
    edit_text_message = get_edit_text_message(callback_message)
    
    user_id = get_user_id(callback)
    playlist_id = int(callback_text.split(":", 1)[1])
    
    user_db_id = ps.get_user_id(user_id)
    if user_db_id is None:
        logger.error(f"Cannot resolve DB user id for telegram_id={user_id}")
        await edit_text_message(f"{EMOJIS.FAIL.value} Internal error occurred. Please try again.")
        return await callback.answer()
    
    # Check if user has already liked this playlist
    if ps.user_has_liked_playlist(user_db_id, playlist_id):
        playlist_name = ps.get_playlist_name_by_id(playlist_id)
        current_likes = ps.get_playlist_likes_count(playlist_id)
        total_stars = ps.get_playlist_total_stars(playlist_id)
        await edit_text_message(
            f"{EMOJIS.STAR.value} You have already liked this playlist!\n\n"
            f"{EMOJIS.MUSIC.value} **{playlist_name}**\n"
            f"{EMOJIS.STAR.value} {current_likes} likes • {total_stars} total stars"
        )
        return await callback.answer()
    
    playlist_name = ps.get_playlist_name_by_id(playlist_id)
    if playlist_name is None:
        await edit_text_message(f"{EMOJIS.FAIL.value} Playlist not found.")
        return await callback.answer()
    
    # Create payment options keyboard
    payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{EMOJIS.STAR.value} 1 Star", callback_data=f"pay_stars_shared:1:{playlist_id}"),
            InlineKeyboardButton(text=f"{EMOJIS.STAR.value} 5 Stars", callback_data=f"pay_stars_shared:5:{playlist_id}")
        ],
        [
            InlineKeyboardButton(text=f"{EMOJIS.STAR.value} 10 Stars", callback_data=f"pay_stars_shared:10:{playlist_id}"),
            InlineKeyboardButton(text=f"{EMOJIS.FAIL.value} Cancel", callback_data="cancel_payment")
        ]
    ])
    
    current_likes = ps.get_playlist_likes_count(playlist_id)
    total_stars = ps.get_playlist_total_stars(playlist_id)
    
    await edit_text_message(
        f"{EMOJIS.STAR.value} **Like with Stars**\n\n"
        f"{EMOJIS.MUSIC.value} Playlist: **{playlist_name}**\n"
        f"{EMOJIS.STAR.value} Current: {current_likes} likes • {total_stars} stars\n\n"
        f"Choose how many stars to contribute:",
        reply_markup=payment_keyboard
    )
    
    await callback.answer()


@like_playlist_router.callback_query(F.data.startswith("pay_stars_shared:"))
async def handle_pay_stars_shared(callback: CallbackQuery, bot: Bot):
    """
    Handle star payment selection for shared playlists.
    """
    callback_text = get_callback_text_safe(callback)
    callback_message = get_callback_message(callback)
    edit_text_message = get_edit_text_message(callback_message)
    
    # Parse callback data: pay_stars_shared:amount:playlist_id
    parts = callback_text.split(":", 2)
    if len(parts) != 3:
        await edit_text_message(f"{EMOJIS.FAIL.value} Invalid payment request.")
        return await callback.answer()
    
    star_amount = int(parts[1])
    playlist_id = int(parts[2])
    
    playlist_name = ps.get_playlist_name_by_id(playlist_id)
    if playlist_name is None:
        await edit_text_message(f"{EMOJIS.FAIL.value} Playlist not found.")
        return await callback.answer()
    
    # Create payment button
    payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{EMOJIS.STAR.value} Pay {star_amount} Stars", pay=True)],
        [InlineKeyboardButton(text=f"{EMOJIS.FAIL.value} Cancel", callback_data="cancel_payment")]
    ])
    
    # Send invoice
    try:
        await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title=f"Like Playlist: {playlist_name}",
            description=f"Show your appreciation by contributing {star_amount} stars to this playlist!",
            payload=f"like_playlist:{playlist_id}:{star_amount}",
            currency="XTR",  # XTR is the currency code for Telegram Stars
            prices=[{"label": f"{star_amount} Stars", "amount": star_amount}],
            reply_markup=payment_keyboard
        )
        
        await edit_text_message(f"{EMOJIS.STAR.value} Payment invoice sent below! Complete the payment to like the playlist.")
        
    except Exception as e:
        logger.error(f"Failed to send invoice: {e}", exc_info=True)
        await edit_text_message(f"{EMOJIS.FAIL.value} Failed to create payment. Please try again.")
    
    await callback.answer()


async def handle_pay_stars(callback: CallbackQuery, bot: Bot):
    """
    Handle star payment selection: create and send an invoice.
    """
    callback_text = get_callback_text_safe(callback)
    callback_message = get_callback_message(callback)
    edit_text_message = get_edit_text_message(callback_message)
    
    # Parse callback data: pay_stars:amount:playlist_name
    parts = callback_text.split(":", 2)
    if len(parts) != 3:
        await edit_text_message(f"{EMOJIS.FAIL.value} Invalid payment request.")
        return await callback.answer()
    
    star_amount = int(parts[1])
    playlist_name = parts[2]
    
    user_id = get_user_id(callback)
    user_db_id = ps.get_user_id(user_id)
    playlist_id = ps.get_playlist_id_by_name(user_db_id, playlist_name)
    
    if playlist_id is None:
        await edit_text_message(f"{EMOJIS.FAIL.value} Playlist not found.")
        return await callback.answer()
    
    # Create payment button
    payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{EMOJIS.STAR.value} Pay {star_amount} Stars", pay=True)],
        [InlineKeyboardButton(text=f"{EMOJIS.FAIL.value} Cancel", callback_data="cancel_payment")]
    ])
    
    # Send invoice
    try:
        await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title=f"Like Playlist: {playlist_name}",
            description=f"Show your appreciation by contributing {star_amount} stars to this playlist!",
            payload=f"like_playlist:{playlist_id}:{star_amount}",
            currency="XTR",  # XTR is the currency code for Telegram Stars
            prices=[{"label": f"{star_amount} Stars", "amount": star_amount}],
            reply_markup=payment_keyboard
        )
        
        await edit_text_message(f"{EMOJIS.STAR.value} Payment invoice sent below! Complete the payment to like the playlist.")
        
    except Exception as e:
        logger.error(f"Failed to send invoice: {e}", exc_info=True)
        await edit_text_message(f"{EMOJIS.FAIL.value} Failed to create payment. Please try again.")
    
    await callback.answer()


@like_playlist_router.callback_query(F.data == "cancel_payment")
async def handle_cancel_payment(callback: CallbackQuery):
    """
    Handle payment cancellation.
    """
    callback_message = get_callback_message(callback)
    edit_text_message = get_edit_text_message(callback_message)
    
    await edit_text_message(f"{EMOJIS.FAIL.value} Payment cancelled.")
    await callback.answer()


@like_playlist_router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """
    Handle pre-checkout validation for star payments.
    """
    # Parse payload to validate the payment
    payload = pre_checkout_query.invoice_payload
    if not payload.startswith("like_playlist:"):
        logger.warning(f"Invalid payment payload: {payload}")
        await pre_checkout_query.answer(ok=False, error_message="Invalid payment request.")
        return
    
    try:
        # Validate payload format: like_playlist:playlist_id:star_amount
        parts = payload.split(":", 2)
        playlist_id = int(parts[1])
        star_amount = int(parts[2])
        
        # Basic validation
        if star_amount <= 0 or star_amount > 100:  # Reasonable limits
            await pre_checkout_query.answer(ok=False, error_message="Invalid star amount.")
            return
            
        # Could add more validation here (e.g., check if playlist still exists)
        
        await pre_checkout_query.answer(ok=True)
        
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse payment payload: {payload}, error: {e}")
        await pre_checkout_query.answer(ok=False, error_message="Invalid payment data.")


@like_playlist_router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    """
    Handle successful star payment: record the like in the database.
    """
    payment: SuccessfulPayment = message.successful_payment
    payload = payment.invoice_payload
    
    if not payload.startswith("like_playlist:"):
        logger.warning(f"Unexpected successful payment payload: {payload}")
        return
    
    try:
        # Parse payload: like_playlist:playlist_id:star_amount
        parts = payload.split(":", 2)
        playlist_id = int(parts[1])
        star_amount = int(parts[2])
        
        user_id = get_user_id(message)
        user_db_id = ps.get_user_id(user_id)
        
        if user_db_id is None:
            logger.error(f"Cannot resolve DB user id for telegram_id={user_id}")
            await message.answer(f"{EMOJIS.FAIL.value} Internal error occurred.")
            return
        
        # Record the like in the database
        transaction_id = payment.telegram_payment_charge_id
        success = ps.add_playlist_like(user_db_id, playlist_id, star_amount, transaction_id)
        
        if success:
            playlist_name = ps.get_playlist_name_by_id(playlist_id)
            current_likes = ps.get_playlist_likes_count(playlist_id)
            total_stars = ps.get_playlist_total_stars(playlist_id)
            
            await message.answer(
                f"{EMOJIS.CHECK_MARK.value} **Thank you for your contribution!**\n\n"
                f"{EMOJIS.MUSIC.value} Playlist: **{playlist_name}**\n"
                f"{EMOJIS.STAR.value} You contributed: {star_amount} stars\n"
                f"{EMOJIS.STAR.value} Total: {current_likes} likes • {total_stars} stars\n\n"
                f"Your support helps recognize valuable playlists in the community!"
            )
            
            logger.info(f"User {user_id} successfully liked playlist {playlist_id} with {star_amount} stars")
        else:
            await message.answer(f"{EMOJIS.FAIL.value} Failed to record your like. Please contact support.")
            logger.error(f"Failed to record like for user {user_id}, playlist {playlist_id}")
            
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to process successful payment: {payload}, error: {e}")
        await message.answer(f"{EMOJIS.FAIL.value} Payment processing error. Please contact support.")