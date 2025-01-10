import discord
from discord.ext import commands
import threading
import asyncio
from pyopenttdadmin import Admin, AdminUpdateType, openttdpacket
import configparser
import os
import re

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Get the parent directory of the current file
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.dirname(current_directory)

        config_path = os.path.join(parent_directory, "config.ini")

        # Load channel ID from config file
        config = configparser.ConfigParser()
        config.read(config_path)  # Ensure the config.ini is in the correct directory

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

    def run_openttd_admin(self):
        # Subscribe to receive console updates
        self.admin.subscribe(AdminUpdateType.CONSOLE)

        # Filter and forward console packets
        @self.admin.add_handler(openttdpacket.ConsolePacket)
        def console_packet(admin: Admin, packet: openttdpacket.ConsolePacket):
            message = packet.message

            # Listen for new clients and send them a private message on join
            if '[server] Client' in packet.message:
                if 'joined' in packet.message:
                    # print(packet.message)

                    match = re.search(r"Client #(\d+)", packet.message)

                    if match:
                        client_id = match.group(1)
                        # print(client_id)
                        admin.send_private(self.welcome_message, int(client_id))

        # Run admin to keep connection active
        self.admin.run()

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
    print("Welcome Cog Loaded")
