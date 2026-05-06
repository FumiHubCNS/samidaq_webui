#!/usr/bin/env bash
set -euo pipefail

########################################
### dump command
########################################
echo "TRIGGER_TYPE :  $SETTING1"
echo "Directory    :  $SETTING2"
echo "FILE NAME    :  $SETTING3"
echo "POLARITY     :  $SETTING4"
echo "GAIN         :  $SETTING5"
echo "NUM_SAMPLE   :  $SETTING6"
echo "PRE_SAMPLE   :  $SETTING7"
echo "CLOCK_TYPE   :  $SETTING8"
echo "TRIGGER_VALUE:  $SETTING9"
echo "COMMENT      :  $SETTING10"

########################################
### write setting
########################################
echo "$RUN_NUMBER" > ../data/run_number.dat
echo "$RUN_NAME" > ../data/run_name.dat
echo "$SETTING1" > ../data/trig_type.dat
echo "$SETTING2" > ../data/output_dir.dat
echo "$SETTING3" > ../data/file_name.dat
echo "$SETTING4" > ../data/polarity.dat
echo "$SETTING5" > ../data/gain.dat
echo "$SETTING6" > ../data/num_sample.dat
echo "$SETTING7" > ../data/pre_sample.dat
echo "$SETTING8" > ../data/clock_type.dat
echo "$SETTING9" > ../data/trig_value.dat
echo "$SETTING10" > ../data/comment.dat
