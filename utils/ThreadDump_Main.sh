# !/bin/sh

SERVER_NAME=$1
echo $SERVER_NAME
STACK_NAME=$2
STACK=${STACK_NAME:0:3}
MACH_1="m1"
MACH_2="m2"
DOMAIN_1="d1"
DOMAIN_2="d2"

echo ${SERVER_NAME:5:2}

checkDomainName(){
if [ "${SERVER_NAME:5:2}" == $DOMAIN_1 ]; then
DOMAIN_NAME=uicpo
elif [ "${SERVER_NAME:5:2}"  ==  $DOMAIN_2 ]; then
DOMAIN_NAME=blwscpo
else
        echo "check input string"
        return 1
fi
}


checkMachineName(){
checkDomainName

if [[ "${SERVER_NAME:10:2}" == $MACH_1 && ${DOMAIN_NAME} == uicpo ]]; then
MACH_NAME=c
elif [[ "${SERVER_NAME:10:2}"  ==  $MACH_2 && ${DOMAIN_NAME} == uicpo ]]; then 
MACH_NAME=d
elif [[ "${SERVER_NAME:10:2}" == $MACH_1 && ${DOMAIN_NAME} == blwscpo ]]; then
MACH_NAME=a
elif [[ "${SERVER_NAME:10:2}"  ==  $MACH_2 && ${DOMAIN_NAME} == blwscpo ]]; then
MACH_NAME=b
else
 	echo "check input string"	
        return 1
fi
}

checkLogFile(){

cd /tmp  
rm ThreadDumpLogs_*.txt
}



checkMachineName
checkLogFile
FULL_NAME=$STACK-$MACH_NAME-$DOMAIN_NAME

ssh -v $STACK_NAME@$FULL_NAME-mgnt.cpggpc.ca "/cpg/3rdParty/scripts/cpg/threadDump.sh $SERVER_NAME" 2>&1 | tee /tmp/ThreadDumpLogs_$(date "+%Y-%m-%d")_$STACK_NAME.txt

#scp dev10@s-03059-c5f-mgnt.cpggpc.ca:/tmp/jstack* ./

#chmod 755 /TEST/jstack*
