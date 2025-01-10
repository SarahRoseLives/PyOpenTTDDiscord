import discord
from discord.ext import commands
import threading
import asyncio
from pyopenttdadmin import Admin, AdminUpdateType, openttdpacket
import configparser
import os

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Get the parent directory of the current file
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.dirname(current_directory)

        config_path = os.path.join(parent_directory, "config.ini")

        # Load channel ID from config file
        config = configparser.ConfigParser()
        config.read(config_path)  # Ensure the config.ini is in the correct directory

        # Get the channel ID from the config file
        self.channel_id = int(config.get("BOT", "chat_channel_id"))

        # Set the IP address and port number for connection
        ip_address = "127.0.0.1"
        port_number = 3977

        # Create an admin instance to communicate with OpenTTD
        self.admin = Admin(ip=ip_address, port=port_number)
        self.admin.login("pyOpenTTDAdmin", "toor")

        # Start the thread to handle OpenTTD console messages
        self.admin_thread = threading.Thread(target=self.run_openttd_admin, daemon=True)
        self.admin_thread.start()

    def run_openttd_admin(self):
        # Subscribe to receive console updates
        self.admin.subscribe(AdminUpdateType.CONSOLE)

        # Filter and forward console packets
        @self.admin.add_handler(openttdpacket.ConsolePacket)
        def console_packet(admin: Admin, packet: openttdpacket.ConsolePacket):
            message = packet.message

            # Forward messages starting with "[All] " (normal chat)
            if "[All]" in message and "Discord: " not in message:
                cleaned_message = message.replace("[All] ", "").strip()
                channel = self.bot.get_channel(self.channel_id)
                if channel is not None:
                    asyncio.run_coroutine_threadsafe(channel.send(cleaned_message), self.bot.loop)

            # Forward messages starting with "***" (events)
            elif "the game" in message:
                embed = discord.Embed(
                    description=message.strip(),
                    color=discord.Color.blue()  # You can customize the embed color here
                )
                channel = self.bot.get_channel(self.channel_id)
                if channel is not None:
                    asyncio.run_coroutine_threadsafe(channel.send(embed=embed), self.bot.loop)

        # Run admin to keep connection active
        self.admin.run()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Forwards all messages from a specific Discord channel to OpenTTD"""
        # Check if the message is from the specific channel (loaded from config)
        if message.channel.id == self.channel_id and not message.author.bot:
            # Prefix the message with "Discord: " so it's recognizable
            formatted_message = f"Discord: {message.author.display_name}: {message.content}"

            # Send the prefixed message to OpenTTD as a console command
            self.admin.send_global(message=formatted_message)
            print(f"Forwarded Discord message to OpenTTD: {formatted_message}")


async def setup(bot):
    await bot.add_cog(ChatCog(bot))
    print('Chat Cog Loaded')
