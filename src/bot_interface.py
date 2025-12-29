import logging
import csv
import tempfile
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from src.config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS, START_KEY
from src.parser import TransactionParser
from src.storage import StorageManager, FIELDNAMES
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
             self.storage.initialize_user_config(user_id)
             await update.message.reply_text("Finance Tracker Bot Started. Send me your transaction messages!")
             return

        # Check for start key
        if START_KEY and context.args and context.args[0] == START_KEY:
            from src.utils import add_allowed_user
            if add_allowed_user(user_id):
                self.storage.initialize_user_config(user_id)
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

        user_categories = self.storage.get_user_categories(user_id)
        parsed_data = self.parser.parse_message(message_text, user_categories)
        
        if parsed_data:
            self.storage.save_transaction(parsed_data, user_id)
            
            # Check for budget alerts
            transactions = self.storage.get_transactions(user_id=user_id)
            analytics = AnalyticsEngine(transactions)
            now = datetime.now()
            month_txs = analytics.filter_transactions_by_month(now.year, now.month)
            
            user_config = self.storage.get_user_config(user_id)
            budgets = user_config.get("budgets", {})
            big_ticket_threshold = user_config["big_ticket_threshold"]

            alerts = analytics.check_budget_alerts(month_txs, budgets)
            
            if parsed_data['type'] != 'Income' and abs(parsed_data['amount']) >= big_ticket_threshold:
                 alerts.append(f"🔥 Big Ticket Alert: SGD {abs(parsed_data['amount']):.2f} >= SGD {big_ticket_threshold:.2f}")
            
            response = (
                f"✅ Transaction Saved!\n"
                f"<b>ID</b>: <code>{parsed_data['id']}</code>\n"
                f"<b>Type</b>: {parsed_data['type']}\n"
                f"<b>Time</b>: {datetime.fromisoformat(parsed_data['timestamp']).strftime('%y/%m/%d %H:%M')}\n"
                f"<b>Amount</b>: SGD {parsed_data['amount']:.2f}\n"
                f"<b>Category</b>: {parsed_data['category']}\n"
                f"<b>Description</b>: <blockquote expandable>{parsed_data['description']}</blockquote>\n"
            )
            
            if alerts:
                response += "\n" + "\n".join(alerts)
                
            await update.message.reply_text(response, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Could not parse message. Ensure format is correct.")
            await update.message.reply_text("Correct format is __bank_message__(paynow/card),__timestamp__,__remarks__")

    async def set_budget_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        if not context.args or len(context.args) != 2:
            await update.message.reply_text("❌ Usage: /set_budget <category>/'threshold' <amount>")
            return
        
        category = str(context.args[0]).capitalize()

        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please provide a number.")
            return

        if category.lower() == 'threshold':
            self.storage.update_user_budget(user_id, "big_ticket", amount)
            await update.message.reply_text(f"✅ Big ticket threshold set to SGD {amount:.2f}")
        else:
            category = category.capitalize()
            user_categories = self.storage.get_user_categories(user_id)
            if category not in user_categories and category != "Total":
                await update.message.reply_text(f"❌ Category '{category}' not found in your category list. Use /add_cat to add it first.")
                return
            
            self.storage.update_user_budget(user_id, category, amount)
            await update.message.reply_text(f"✅ Budget for '{category}' set to SGD {amount:.2f}")

    async def add_category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /add_cat <category1>, <category2>, ...")
            return

        categories_str = " ".join(context.args)
        categories = [c.strip().capitalize() for c in categories_str.split(",") if c.strip()]
        
        if not categories:
            await update.message.reply_text("❌ No valid categories provided.")
            return

        self.storage.add_user_categories(user_id, categories)
        await update.message.reply_text(f"✅ Added categories: {', '.join(categories)}")

    async def delete_category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /delete_cat <category1>, <category2>, ...")
            return

        categories_str = " ".join(context.args)
        categories = [c.strip().capitalize() for c in categories_str.split(",") if c.strip()]
        
        if not categories:
            await update.message.reply_text("❌ No valid categories provided.")
            return

        self.storage.delete_user_categories(user_id, categories)
        await update.message.reply_text(f"✅ Deleted categories: {', '.join(categories)}")

    async def reset_category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        self.storage.reset_user_categories(user_id)
        await update.message.reply_text("✅ Categories reset to default.")

    async def view_category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        categories = self.storage.get_user_categories(user_id)
        if not categories:
             await update.message.reply_text("No categories found.")
             return

        response = "📂 **Current Categories**\n"
        for cat in categories:
            response += f"- {cat}\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def reset_budget_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        self.storage.reset_user_budget(user_id)
        await update.message.reply_text("✅ Budget reset to default values.")

    async def view_budget_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        config = self.storage.get_user_config(user_id)
        budgets = config.get("budgets", {})
        
        response = "📊 **Current Budgets**\n"
        if budgets:
            for category, amount in budgets.items():
                response += f"- {category}: SGD {amount:.2f}\n"
        else:
            response += "No budgets configured.\n"
            
        response += f"\n🔥 **Big Ticket Threshold**: SGD {config['big_ticket_threshold']:.2f}"
            
        await update.message.reply_text(response, parse_mode='Markdown')

    async def total_stats_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            f"Total Expense: SGD {totals['expense']:.2f}\n"
            f"Total Transactions: {len(transactions)}\n\n"
            f"📂 **Category Breakdown**\n"
        )
        
        for cat, amount in breakdown.items():
            response += f"- {cat}: SGD {amount:.2f}\n"
            
        await update.message.reply_text(response, parse_mode='Markdown')

    async def month_stats_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        if context.args and len(context.args) >= 2:
            try:
                year = int(context.args[0])
                month = int(context.args[1])
                year_month_str = f"{datetime(year, month, 1).strftime('%B %Y')}"
            except ValueError:
                await update.message.reply_text("❌ Invalid year or month. Use /month <year> <month>.")
                return
        elif not context.args or len(context.args) == 0:
            now = datetime.now()
            year = now.year
            month = now.month
            year_month_str = now.strftime("%B %Y")
        else:
            await update.message.reply_text("❌ Invalid command format. Use /month <year> <month> or /month for current month.")
            return

        transactions = self.storage.get_transactions(user_id=user_id)
        analytics = AnalyticsEngine(transactions)
        month_txs = analytics.filter_transactions_by_month(year, month)
        
        month_analytics = AnalyticsEngine(month_txs)
        totals = month_analytics.get_total_income_expense()
        breakdown = month_analytics.get_category_breakdown()
        
        response = (
            f"📅 **{year_month_str} Stats**\n"
            f"Total Income: SGD {totals['income']:.2f}\n"
            f"Total Expense: SGD {totals['expense']:.2f}\n"
            f"Total Transactions: {len(month_txs)}\n\n"
            f"📂 **Category Breakdown**\n"
        )
        
        for cat, amount in breakdown.items():
            response += f"- {cat}: SGD {amount:.2f}\n"
            
        await update.message.reply_text(response, parse_mode='Markdown')

    async def delete_transaction_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return
        
        if not context.args or len(context.args) != 1:
            await update.message.reply_text("❌ Usage: /delete <transaction_id>")
            return
            
        transaction_id = context.args[0]
        if self.storage.delete_transaction(transaction_id, user_id):
            await update.message.reply_text(f"✅ Transaction {transaction_id} deleted.")
        else:
            await update.message.reply_text(f"❌ Transaction {transaction_id} not found.")

    async def delete_all_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return
            
        if self.storage.delete_all_transactions(user_id):
            await update.message.reply_text("✅ All transactions deleted.")
        else:
            await update.message.reply_text("❌ Failed to delete transactions or no transactions found.")

    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self._is_authorized(update)
        if not user_id:
            return

        # Parse arguments for month/year
        year, month = None, None
        if context.args and len(context.args) >= 2:
            try:
                year = int(context.args[0])
                month = int(context.args[1])
            except ValueError:
                await update.message.reply_text("❌ Invalid year or month. Use /export <year> <month>.")
                return
        elif not context.args:
            now = datetime.now()
            year = now.year
            month = now.month
        else:
             await update.message.reply_text("❌ Usage: /export <year> <month> or /export for current month.")
             return

        transactions = self.storage.get_transactions(user_id)
        analytics = AnalyticsEngine(transactions)
        month_txs = analytics.filter_transactions_by_month(year, month)
        
        if not month_txs:
            await update.message.reply_text(f"No transactions found for {month}/{year}.")
            return

        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(month_txs)
            temp_path = f.name
            
        try:
            await update.message.reply_document(document=open(temp_path, 'rb'), filename=f"transactions_{year}_{month}.csv")
        except Exception as e:
            logger.error(f"Failed to send export: {e}")
            await update.message.reply_text("❌ Failed to send export file.")
        finally:
            os.unlink(temp_path)

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
        
        '''
        Available Commands:
            start - /start <key> initialize the bot and authorize user
            stats - View all-time financial statistics
            month - /month <year> <month> get the monthly expenses stats, defaults to current
            export - /month <year> <month> exports monthly transactions as csv, defaults to current
            delete - /delete <id> permanently removes a transaction by ID
            clear - Permanently delete all transactions
            set_budget - /set_budget <category> <amount> set budget for a category
            reset_budget - reset all budgets to default values
            view_budget - view all current budgets
            add_cat - /add_cat <cat1>, <cat2> add new categories
            delete_cat - /delete_cat <cat1>, <cat2> delete categories
            reset_cat - reset categories to default
            view_cat - view all current categories
            <message> - Send a bank transaction message to log it
        '''
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("stats", self.total_stats_commands))
        application.add_handler(CommandHandler("month", self.month_stats_commands))
        application.add_handler(CommandHandler("delete", self.delete_transaction_command))
        application.add_handler(CommandHandler("clear", self.delete_all_command))
        application.add_handler(CommandHandler("export", self.export_command))
        application.add_handler(CommandHandler("set_budget", self.set_budget_command))
        application.add_handler(CommandHandler("reset_budget", self.reset_budget_command))
        application.add_handler(CommandHandler("view_budget", self.view_budget_command))
        application.add_handler(CommandHandler("add_cat", self.add_category_command))
        application.add_handler(CommandHandler("delete_cat", self.delete_category_command))
        application.add_handler(CommandHandler("reset_cat", self.reset_category_command))
        application.add_handler(CommandHandler("view_cat", self.view_category_command))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))

        logger.info("Bot is polling...")
        application.run_polling()
