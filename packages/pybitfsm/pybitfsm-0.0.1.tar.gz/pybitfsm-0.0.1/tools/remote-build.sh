#!/bin/sh

set -eu

host="$1"
shift
rsync -avz --exclude 'build*' --exclude '.git' --exclude 'env' . "$host":src/bitfsm
ssh "$host" "/bin/bash -l -c 'cd src/bitfsm && $@'"
