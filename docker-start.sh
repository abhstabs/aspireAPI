#!/bin/bash

echo "Welcome to Aspire API"
echo "Input Admin Credentials. Please enter Email and Password"
read -p "Enter admin email address: " EMAIL

# Prompt the user for a password (and hide the input)
read -s -p "Enter admin password: " PASSWORD


sed -i "s/{\$1}/$PASSWORD/g" docker-compose.yml
sed -i "s/{\$2}/$EMAIL/g" docker-compose.yml

echo "\n"

docker-compose up