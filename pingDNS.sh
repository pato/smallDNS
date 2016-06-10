#!/bin/bash
touch .oldIP;

server='nixons-head.csres.utexas.edu'

ip=12341234
oldip=$(cat .oldIP);
hostname=$(hostname)

if [ "$ip" == "$oldip" ]; then
  echo "$(date): no ip change";
else
  wget -qO- "http://$server:7978/$ip~$hostname" > /dev/null;
  if [ $? -ne 0 ]; then
    echo "$(date): server is down";
  else
    echo "$(date): ip changed to $ip";
    echo "$ip" > .oldIP;
  fi
fi
