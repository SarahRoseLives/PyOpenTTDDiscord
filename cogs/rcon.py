import discord
from discord.ext import commands
import threading
import asyncio
from pyopenttdadmin import Admin, AdminUpdateType, openttdpacket
import configparser
import os
import re


class RconCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Get the parent directory of the current file
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.dirname(current_directory)

        config_path = os.path.join(parent_directory, "config.ini")

        # Load channel ID from config file
        config = configparser.ConfigParser()
        config.read(config_path)  # Ensure the config.ini is in the correct directory

        self.admin_role_id = config.get("BOT", "admin_role_id")
        self.bot_name = config.get("BOT", "bot_name")


        # Get the welcome message from the config file
        self.welcome_message = config.get("OPENTTD", "welcome_message")
        self.ip_address = config.get("OPENTTD", "ip_address")
        self.port_number = int(config.get("OPENTTD", "port_number"))
        self.password = config.get("OPENTTD", "password")

        # Create an admin instance to communicate with OpenTTD
        self.admin = Admin(ip=self.ip_address, port=self.port_number)
        self.admin.login(self.bot_name, self.password)

        # Start the thread to handle OpenTTD console messages
        self.admin_thread = threading.Thread(target=self.run_openttd_admin, daemon=True)
        self.admin_thread.start()

        # To store all RCON responses
        self.rcon_responses = []

    def run_openttd_admin(self):
        # Subscribe to receive console updates
        @self.admin.add_handler(openttdpacket.RconPacket)
        def RconPacket(admin: Admin, packet: openttdpacket.RconPacket):
            # Append each RconPacket's message to the list
            self.rcon_responses.append(packet.response)

        # Run admin to keep connection active
        self.admin.run()

    @commands.command()
    async def rcon(self, ctx, *, command: str):
        """Send an RCON command to OpenTTD and respond with the output."""
        # Check if the user has the admin role
        if not any(role.id == int(self.admin_role_id) for role in ctx.author.roles):
            await ctx.send("You do not have permission to use this command.")
            return

        # Clear the previous responses before sending a new command
        self.rcon_responses.clear()

        # Send the RCON command to OpenTTD
        self.admin.send_rcon(command)

        # Wait for the response (you may need to adjust the sleep duration for your use case)
        await asyncio.sleep(2)  # Increase this if you expect multiple packets and need more time

        # Send all RCON responses back to the Discord channel
        if self.rcon_responses:
            for response in self.rcon_responses:
                await ctx.send(f"RCON Response: {response}")
        else:
            await ctx.send("No response received from the server.")


async def setup(bot):
    await bot.add_cog(RconCog(bot))
    print("Rcon Cog Loaded")
