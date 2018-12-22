#!/bin/bash
export GANACHEDB=$PWD/tmp
rm -rf $GANACHEDB
mkdir $GANACHEDB
ganache-cli -i 101 --db $GANACHEDB --noVMErrorsOnRPCResponse -l 50000000 -p 8545 -d