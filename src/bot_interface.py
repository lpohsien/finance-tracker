import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from src.config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS, START_KEY
from src.parser import TransactionParser
from src.storage import StorageManager
from src.analytics import AnalyticsEngine
from datetime import datetime

logger = logging.getLogger(__name__)

class FinanceBot:
    def __init__(self):
        self.parser = TransactionParser()
        self.storage = StorageManager()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Check if user is already authorized
        if user_id in ALLOWED_USER_IDS:
             await update.message.reply_text("Finance Tracker Bot Started. Send me your transaction messages!")
             return

        # Check for start key
        if START_KEY and context.args and context.args[0] == START_KEY:
            from src.utils import add_allowed_user
            if add_allowed_user(user_id):
                await update.message.reply_text("✅ Access Granted! You are now authorized to use this bot.")
                logger.info(f"User {user_id} authorized via start key.")
            else:
                await update.message.reply_text("You are already authorized.")
        else:
            await update.message.reply_text("⛔ Unauthorized access.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        message_text = update.message.text
        logger.info(f"Received message: {message_text} from user ID: {user_id}")

        parsed_data = self.parser.parse_message(message_text)
        
        if parsed_data:
            self.storage.save_transaction(parsed_data, user_id)
            
            # Check for budget alerts
            transactions = self.storage.get_transactions(user_id=user_id)
            analytics = AnalyticsEngine(transactions)
            now = datetime.now()
            month_txs = analytics.filter_transactions_by_month(now.year, now.month)
            alerts = analytics.check_budget_alerts(month_txs)
            
            response = (
                f"✅ Transaction Saved!\n"
                f"Type: {parsed_data['type']}\n"
                f"Time: {parsed_data['timestamp']}\n"
                f"Amount: SGD {parsed_data['amount']:.2f}\n"
                f"Category: {parsed_data['category']}\n"
                f"Description: {parsed_data['description']}\n"
            )
            
            if alerts:
                response += "\n" + "\n".join(alerts)
                
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("❌ Could not parse message. Ensure format is correct.")

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        transactions = self.storage.get_transactions(user_id=user_id)
        analytics = AnalyticsEngine(transactions)
        
        totals = analytics.get_total_income_expense()
        breakdown = analytics.get_category_breakdown()
        
        response = (
            f"📊 **All Time Stats**\n"
            f"Total Income: SGD {totals['income']:.2f}\n"
            f"Total Expense: SGD {totals['expense']:.2f}\n\n"
            f"📂 **Category Breakdown**\n"
        )
        
        for cat, amount in breakdown.items():
            response += f"- {cat}: SGD {amount:.2f}\n"
            
        await update.message.reply_text(response, parse_mode='Markdown')

    async def month_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        now = datetime.now()
        transactions = self.storage.get_transactions(user_id=user_id)
        analytics = AnalyticsEngine(transactions)
        month_txs = analytics.filter_transactions_by_month(now.year, now.month)
        
        month_analytics = AnalyticsEngine(month_txs)
        totals = month_analytics.get_total_income_expense()
        breakdown = month_analytics.get_category_breakdown()
        
        response = (
            f"📅 **{now.strftime('%B %Y')} Stats**\n"
            f"Total Income: SGD {totals['income']:.2f}\n"
            f"Total Expense: SGD {totals['expense']:.2f}\n\n"
            f"📂 **Category Breakdown**\n"
        )
        
        for cat, amount in breakdown.items():
            response += f"- {cat}: SGD {amount:.2f}\n"
            
        await update.message.reply_text(response, parse_mode='Markdown')

    def _is_authorized(self, update: Update) -> int:
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USER_IDS:
            logger.warning(f"Unauthorized access attempt from user ID: {user_id}")
            return 0
        return user_id

    def run(self):
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
            return

        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("stats", self.stats))
        application.add_handler(CommandHandler("month", self.month_stats))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))
        
        logger.info("Bot is polling...")
        application.run_polling()
