#!/bin/bash

# List of cert aliases to be removed
certList="
	entrustrootcag2
    geotrustprimarycag3
    globalsignr3ca
    keynectisrootca
    secomscrootca2
	thawteprimaryrootcag3
    ttelesecglobalrootclass2ca
    ttelesecglobalrootclass3ca
	verisignuniversalrootca
"

# Make sure we are in the right directory
if [ ! -f cacerts ]; then
	cat <<EOF

	usage $0

	Removes known certificates with SHA@56withRSA signature algorithm
	These are not supported by the library we are using for SSL

	Run from \$JAVA_HOME/jre/lib/security of the version to be fixed.

EOF
	exit 1
fi

# Make a backup if needed and verify
if [ ! -f cacerts.bak ]; then
	cp cacerts cacerts.bak
fi
if [ ! -f cacerts.bak ]; then
	echo "FATAL: cannot create keystore backup"
	exit 1
fi

# Remove the certs
for CERT in ${certList}; do
	echo "Removing cert with alias ${CERT}"
	keytool --keystore cacerts --storepass changeit --delete --alias ${CERT}
done

# Verify results
keytool --keystore cacerts --storepass changeit --list -v | grep SHA256withRSA

# EOF
