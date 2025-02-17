import discord
import re
import datetime
import google.generativeai as genai
from discord.ext import commands
from discord.ui import Button, View
from currency_converter import CurrencyConverter
import os
from dotenv import load_dotenv
import emoji  
from cogs import mod
from dbconnMOD import add_mod_log, get_warnings

load_dotenv()
API_KEY = os.getenv("API_KEY") 
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-pro")  
c = CurrencyConverter()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  

MOD_LOG_CHANNEL_ID = 1338401271119347743  
TARGET_CHANNEL_ID = [1338422604897456129, 1248315045000253530, 1244399296279740558, 1240456287473369170, 1246266893925482641, 1243567009564721243, 1244400051879546930]

class Budget(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    log_counter = 1  

    def get_next_log_number(self):
        log_number = self.log_counter
        self.log_counter += 1
        return log_number

    def clean_text(self, text):
        # Remove links
        text = re.sub(r"https?://\S+", "", text)
        
        # Ignore TAT, TURN AROUND TIME, and SLOTS
        text = re.sub(r"(?i)(TAT|TURN AROUND TIME|SLOTS)", "", text)
        
        # Remove emoji and other unwanted characters
        text = emoji.replace_emoji(text, replace="")
        text = re.sub(r"<a?:\w+:\d+>", "", text)
        
        return text

    def extract_prices(self, text):
        # Extract prices from the text
        price_patterns = re.finditer(
            r"(?P<currency>[$€£¥₹]|USD|EUR|GBP|JPY|INR)?\s*(?P<amount>\d+(?:\.\d+)?)\s*(?P<post_currency>[$€£¥₹]|USD|EUR|GBP|JPY|INR)?",
            text,
            re.IGNORECASE,
        )
        prices = []
        currency_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR"}
        
        for match in price_patterns:
            pre_currency = match.group("currency")  
            amount = match.group("amount")  
            post_currency = match.group("post_currency")  
            
            currency_code = currency_map.get(pre_currency, "USD")
            if post_currency:
                currency_code = currency_map.get(post_currency, "USD")
            
            if amount:
                prices.append((float(amount), currency_code.upper()))
        return prices

    def check_price(self, text):
        # Clean the text to remove unwanted keywords
        text = self.clean_text(text)
        
        # Ignore the price range "$100-$140"
        text = re.sub(r"\$100-\$140", "", text)
        
        # Extract prices from the text
        price_patterns = re.finditer(
            r"(?P<currency>[$€£¥₹]|USD|EUR|GBP|JPY|INR)?\s*(?P<amount>\d+(?:\.\d+)?)\s*(?P<post_currency>[$€£¥₹]|USD|EUR|GBP|JPY|INR)?",
            text,
            re.IGNORECASE,
        )
        prices = []
        currency_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR"}
        
        for match in price_patterns:
            pre_currency = match.group("currency")  
            amount = match.group("amount")  
            post_currency = match.group("post_currency")  
            
            currency_code = currency_map.get(pre_currency, "USD")
            if post_currency:
                currency_code = currency_map.get(post_currency, "USD")
            
            if amount:
                prices.append((float(amount), currency_code.upper()))
        
        # Check if any price is below $15
        for price, currency in prices:
            try:
                price_usd = c.convert(price, currency, "USD") if currency in c.currencies else price
                if price_usd < 15:
                    return True  # Flag this message as INVALID
            except (ValueError, KeyError):
                pass
        return False  # No price below $15, so the message is valid

    async def analyze_with_gemini(self, text):
        try:
            model = genai.GenerativeModel("gemini-pro")
            prompt = f"""
            You are a moderator assistant reviewing marketplace messages.
            **Only flag messages as "INVALID" if they contain a price below $15 USD.**
            **Ignore prices labeled as add-ons, fees, or commercial use fees.**
            **Bulk deals (e.g., "minimum", "bundle", "bulk", "at least") are valid.**
            **TAT (Turnaround Time) mentions make the message valid.**
            **User Message:**
            {text}
            """
            response = model.generate_content(prompt)
            return "INVALID" if "INVALID" in response.text else "VALID"
        except Exception:
            return "VALID"  

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id in TARGET_CHANNEL_ID:
            text_without_links = self.clean_text(message.content)
            regex_check = self.check_price(text_without_links)
            ai_check = await self.analyze_with_gemini(text_without_links)

            if regex_check or ai_check == "INVALID":
                mod_log_channel = self.bot.get_channel(MOD_LOG_CHANNEL_ID)
                embed = discord.Embed(title="🚨 Possible Rule Violation", color=discord.Color.red())
                embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
                embed.add_field(name="User ID", value=message.author.id, inline=True)
                embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                embed.add_field(name="Message Content", value=message.content[:1024], inline=False)
                embed.set_footer(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                await mod_log_channel.send(embed=embed, view=WarningButton(self.bot, message.author.id, message, self.get_next_log_number()))


class WarningButton(View):
    def __init__(self, bot, user_id, message, log_number):
        super().__init__(timeout=None)
        self.bot = bot  
        self.user_id = user_id
        self.message = message
        self.log_number = log_number  

    async def issue_warning(self, interaction, warning_type):
        user = await self.bot.fetch_user(self.user_id)
        
        # Fetch minor and major warnings
        minor_warnings, major_warnings = get_warnings(user.id)
        
        # Count the warnings
        if warning_type.lower() == "minor_warning":
            count = len(minor_warnings) + 1  # Add 1 for this warning
        else:
            count = len(major_warnings) + 1  # Add 1 for this warning

        # Log the warning
        log_message = f"{warning_type} for pricing rule violation. This is warning number {count}."
        add_mod_log(user.id, log_message, interaction.user.id, warning_type.lower())
        
        # Create the embed for warning message
        warning_embed = discord.Embed(
            title=f"⚠️ {warning_type} Issued", 
            description=f"Your message was deleted because at least one of your listed prices was below the $15 minimum budget requirement.\nThis is your {count} {warning_type.lower()} warning.", 
            color=discord.Color.red()
        )
        warning_embed.add_field(name="Your Message", value=f"`{self.message.content}`", inline=False)
        
        try:
            await user.send(embed=warning_embed)
        except discord.Forbidden:
            pass
        
        # Delete the original message and send response to the interaction
        await self.message.delete()
        await interaction.response.send_message(f"{warning_type} issued.", ephemeral=True)
        
        # Disable buttons after action and update interaction message
        self.disable_all_buttons()
        await interaction.message.edit(view=self)

        # Log the warning in mod log channel
        mod_log_channel = self.bot.get_channel(MOD_LOG_CHANNEL_ID)
        embed = discord.Embed(title=f"🚨 User Warned", color=discord.Color.orange())
        embed.set_author(name=user.name, icon_url=user.display_avatar.url)
        embed.add_field(name="User ID", value=user.id, inline=True)
        embed.add_field(name="Warning Type", value=warning_type, inline=True)
        embed.add_field(name="Total Warnings", value=count, inline=True)
        embed.add_field(name="Message Content", value=self.message.content[:1024], inline=False)
        embed.set_footer(text=f"Warning issued by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await mod_log_channel.send(embed=embed)

    def disable_all_buttons(self):
        """Disables all buttons after the warning is issued."""
        for child in self.children:
            child.disabled = True
        self.stop()

    @discord.ui.button(label="Minor Warning", style=discord.ButtonStyle.danger)
    async def minor_warning(self, interaction: discord.Interaction, button: Button):
        await self.issue_warning(interaction, "Minor Warning")

    @discord.ui.button(label="Major Warning", style=discord.ButtonStyle.blurple)
    async def major_warning(self, interaction: discord.Interaction, button: Button):
        await self.issue_warning(interaction, "Major Warning")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Alert remains in place.", ephemeral=True)
        self.disable_all_buttons()
        await interaction.message.edit(view=self)


async def setup(bot):
    await bot.add_cog(Budget(bot))
