#!/bin/bash

cd ..

# Generate service description

echo -e "[Unit]
Description=TelegramMQTTBot instance
After=network.target

[Service]
User=$(whoami)
Group=$(whoami)
WorkingDirectory=$(pwd)
Environment=\"PATH=/usr/bin\"
ExecStart=/usr/bin/python3 out/TelegramMQTTBot resources/settings.json

[Install]
WantedBy=multi-user.target
" > systemd/TelegramMQTTBot.service

# Enable and start service
sudo cp systemd/TelegramMQTTBot.service /etc/systemd/system/
sudo systemctl start TelegramMQTTBot
sudo systemctl enable TelegramMQTTBot

