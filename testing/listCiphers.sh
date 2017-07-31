#!/usr/bin/env bash

# OpenSSL requires the port number.
SERVER=${1:-localhost:443}
DELAY=1

echo Obtaining cipher list from $(openssl version).
ciphers=$(openssl ciphers -tls1 'ALL:eNULL' | sed -e 's/:/ /g')

for cipher in ${ciphers[@]}; do
	echo -n Testing $cipher...
	result=$(echo -n | openssl s_client -cipher "$cipher" -connect $SERVER 2>&1)
	if [[ "$result" =~ ":error:" ]] ; then
		error=$(echo -n $result | cut -d':' -f6)
		echo NO \($error\)
	else
		if [[ "$result" =~ "Cipher is ${cipher}" || "$result" =~ "Cipher    :" ]] ; then
			echo YES
		else
			echo UNKNOWN RESPONSE
			echo $result
		fi
	fi
	sleep $DELAY
done

# EOF
