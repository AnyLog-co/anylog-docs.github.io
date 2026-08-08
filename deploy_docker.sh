#!/usr/bin/env bash

CMD=${1:-up}
LOCAL_SCRIPTS=${2:-.}

# if LOCAL_SCRIPTS directory DNE && is not equal to "."
if [[ -z ${LOCAL_SCRIPTS} ]] && [[ ! ${LOCAL_SCRIPTS} == "." ]] && [[ ! -d ${LOCAL_SCRITPS} ]] ; then
  echo "Failed to locate Docker directory: ${LOCAL_SCRIPTS}"
  exit 1
fi

if [[ "${CMD}" -eq "up" ]] ; then
  LOCAL_DOCS=${LOCAL_SCRIPTS} docker compose -f ./docker-compose.yml up -d
elif [[ "${CMD}" -eq "logs" ]] ; then
  docker logs -f anylog-docs
elif [[ "${CMD}" -eq "down" ]] ; then
  LOCAL_DOCS=${LOCAL_SCRIPTS} docker compose -f ./docker-compose.yml down
elif [[ "${CMD}" -eq "clean" ]] ; then
  LOCAL_DOCS=${LOCAL_SCRIPTS} docker compose -f ./docker-compose.yml down -v --rmi all
else
  echo "Invalid option: ${CMD}"
fi

