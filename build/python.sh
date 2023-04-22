#!/bin/bash
while getopts ":p:a:" opt; do
  # shellcheck disable=SC2213
  case $opt in
    p) pathRepo="$OPTARG" ;;
    a) pathAction="$OPTARG" ;;
    \?) echo "Invalid option -$OPTARG" >&2
    exit 1
    ;;
  esac

  case $OPTARG in
    -*) echo "Option $opt needs a valid argument"
    exit 1
    ;;
  esac
done
printf "Argument path is %s\n" "$pathRepo"
printf "Argument path is %s\n" "$pathAction"

cd "$pathRepo"
zip -r $pathAction *