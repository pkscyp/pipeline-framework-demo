#!/bin/bash



while [[ $# -gt 0 ]]; do
case $1 in
        -s|--servers)
          WATCH_SERVER_LIST=$2
          shift
          shift
          ;;
        *)
          shift
          ;;
esac
done


if [ "${WATCH_SERVER_LIST:-}" == ""  ]; then
   echo " MONITOR_HOST_PORTS Not defined .."
   exit 0
fi
CLNS=(${WATCH_SERVER_LIST//,/ })

allup=1

while [ $allup -ne 0 ]
do
  for server in ${CLNS[@]}
    do
        echo $allup
        s=(${server//:/ })
        host=${s[0]}
        port=${s[1]:-5000}
        timeout 5 nc -zv $host $port
        allup=$?
        if [ $allup -ne 0 ]
        then
         break
        fi
    done
  sleep 5
done

echo " All ${MONITOR_HOST_PORTS} alive "

exit 0
