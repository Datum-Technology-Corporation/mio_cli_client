#! /bin/bash
########################################################################################################################
# Copyright 2021-2023 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


export mio="python3 -m mio "
cd ../../src

$mio --dbg sim tb -t hello_world -s 1 -w -c -a mdc
#$mio --dbg regr tb sanity -a mdc
