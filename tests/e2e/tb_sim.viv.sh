#! /bin/bash
########################################################################################################################
# Copyright Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


export mio="mio "

$mio --dbg sim  tb -t hello_world -s 1 -w -c -a viv
$mio --dbg regr tb sanity -a viv
