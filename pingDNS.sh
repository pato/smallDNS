#!/bin/bash
touch ~/oldIP;

ip=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1 -d'/');
oldip=$(cat ~/oldIP);
hostname=$(hostname)

if [ "$ip" == "$oldip" ]; then
  echo "no ip change";
else
  echo "ip changed to $ip";
  wget -qO- "http://localhost:7979/$ip~$hostname";
  echo "$ip" > ~/oldIP;
fi
