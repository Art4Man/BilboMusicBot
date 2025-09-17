from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, 
    PreCheckoutQuery, 
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice
)
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

playlist_stars_router = Router()

STAR_PRICE = 1  # 1 Telegram Star per like


@playlist_stars_router.callback_query(F.data.startswith("like_playlist:"))
async def handle_like_playlist(callback: CallbackQuery, bot: Bot):
    """
    Handle playlist like request by creating a star payment invoice.
    
    Parses playlist ID from callback data, validates the playlist exists,
    and creates a payment invoice for 1 Telegram Star to like the playlist.
    
    Parameters:
        callback (CallbackQuery): Callback from "like_playlist:<playlist_id>" button.
        bot (Bot): Telegram Bot instance for creating invoice.
    """
    callback_text = get_callback_text_safe(callback)
    user_id = get_user_id(callback)
    callback_message = get_callback_message(callback)
    edit_text_message = get_edit_text_message(callback_message)
    
    try:
        playlist_id = int(callback_text.split(":", 1)[1])
    except (ValueError, IndexError):
        logger.warning(f"Invalid playlist ID in like callback: {callback_text}")
        await edit_text_message(f"{EMOJIS.FAIL.value} Invalid playlist.")
        return await callback.answer()
    
    # Check if playlist exists
    playlist_name = ps.get_playlist_name_by_id(playlist_id)
    if not playlist_name:
        await edit_text_message(f"{EMOJIS.FAIL.value} Playlist not found.")
        return await callback.answer()
    
    # Check if user already liked this playlist
    db_user_id = ps.get_user_id(user_id)
    if db_user_id and ps.has_user_liked_playlist(db_user_id, playlist_id):
        await edit_text_message(f"{EMOJIS.STAR.value} You already liked this playlist!")
        return await callback.answer()
    
    # Create payment invoice for 1 star
    try:
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Like Playlist: {playlist_name}",
            description=f"Support this playlist with 1 Telegram Star",
            payload=f"like_playlist_{playlist_id}",
            currency="XTR",  # Telegram Stars currency
            prices=[LabeledPrice(label="Like Playlist", amount=STAR_PRICE)],
            start_parameter=f"like_{playlist_id}"
        )
        logger.info(f"Created star payment invoice for user {user_id} to like playlist {playlist_id}")
        await callback.answer("Payment invoice sent!")
        
    except Exception as e:
        logger.error(f"Failed to create payment invoice: {e}", exc_info=True)
        await edit_text_message(f"{EMOJIS.FAIL.value} Failed to create payment. Please try again.")
        await callback.answer()


@playlist_stars_router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """
    Handle pre-checkout validation for star payments.
    
    Validates the payment request before processing and answers the pre-checkout query.
    """
    payload = pre_checkout_query.invoice_payload
    
    if payload.startswith("like_playlist_"):
        try:
            playlist_id = int(payload.split("_", 2)[2])
            # Validate playlist still exists
            playlist_name = ps.get_playlist_name_by_id(playlist_id)
            if playlist_name:
                logger.info(f"Pre-checkout approved for playlist {playlist_id}")
                await pre_checkout_query.answer(ok=True)
            else:
                logger.warning(f"Pre-checkout denied - playlist {playlist_id} not found")
                await pre_checkout_query.answer(ok=False, error_message="Playlist no longer exists")
        except (ValueError, IndexError):
            logger.warning(f"Invalid payload in pre-checkout: {payload}")
            await pre_checkout_query.answer(ok=False, error_message="Invalid payment data")
    else:
        logger.warning(f"Unknown payload in pre-checkout: {payload}")
        await pre_checkout_query.answer(ok=False, error_message="Unknown payment type")


@playlist_stars_router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    """
    Handle successful star payment and record the playlist like.
    
    Processes the successful payment, extracts playlist ID from payload,
    and records the like in the database.
    """
    payment = message.successful_payment
    payload = payment.invoice_payload
    user_id = get_user_id(message)
    
    if payload.startswith("like_playlist_"):
        try:
            playlist_id = int(payload.split("_", 2)[2])
            db_user_id = ps.get_user_id(user_id)
            
            if not db_user_id:
                logger.error(f"Could not find database user for telegram user {user_id}")
                await message.answer(f"{EMOJIS.FAIL.value} Payment processed but could not record like.")
                return
            
            # Record the like
            success = ps.add_playlist_like(
                user_id=db_user_id,
                playlist_id=playlist_id,
                star_amount=payment.total_amount,
                telegram_payment_charge_id=payment.telegram_payment_charge_id
            )
            
            if success:
                playlist_name = ps.get_playlist_name_by_id(playlist_id)
                likes_count = ps.get_playlist_likes_count(playlist_id)
                
                await message.answer(
                    f"{EMOJIS.STAR.value} Thank you for supporting **{playlist_name}**!\n"
                    f"This playlist now has **{likes_count}** stars total."
                )
                logger.info(f"Successfully recorded like for playlist {playlist_id} from user {user_id}")
            else:
                await message.answer(f"{EMOJIS.FAIL.value} Payment processed but could not record like.")
                
        except (ValueError, IndexError):
            logger.warning(f"Invalid payload in successful payment: {payload}")
            await message.answer(f"{EMOJIS.FAIL.value} Payment processed but invalid data.")
    else:
        logger.warning(f"Unknown payload in successful payment: {payload}")


@playlist_stars_router.callback_query(F.data.startswith("already_liked:"))
async def handle_already_liked(callback: CallbackQuery):
    """
    Handle callback when user clicks on "Already Liked" button.
    
    Shows a message that the user has already liked this playlist.
    """
    await callback.answer("You have already liked this playlist! ⭐")