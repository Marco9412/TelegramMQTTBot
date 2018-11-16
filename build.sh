#!/bin/bash

EXECUTABLENAME="TelegramMQTTBot"

mkdir -p out

echo "Cleaning old files"
rm -f "out/$EXECUTABLENAME" "out/$EXECUTABLENAME.zip"

echo "Building"
cd app
zip -r "../out/$EXECUTABLENAME.zip" *
cd ..
echo '#!/usr/bin/env python3' | cat - "out/$EXECUTABLENAME.zip" > "out/$EXECUTABLENAME"
chmod +x "out/$EXECUTABLENAME"
rm "out/$EXECUTABLENAME.zip"
