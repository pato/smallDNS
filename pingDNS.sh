#!/bin/bash
touch .oldIP;

server='localhost'

ip=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1 -d'/');
oldip=$(cat .oldIP);
hostname=$(hostname)

if [ "$ip" == "$oldip" ]; then
  echo "$(date): no ip change";
else
  wget -qO- "http://$server:7979/$ip~$hostname" > /dev/null;
  if [ $? -ne 0 ]; then
    echo "$(date): server is down";
  else
    echo "$(date): ip changed to $ip";
    echo "$ip" > .oldIP;
  fi
fi
