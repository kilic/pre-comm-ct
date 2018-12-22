#!/bin/bash
rm -rf db/*
mkdir -p tmp/keys/dev-chain && cp key.json tmp/keys/dev-chain/
parity --config config.toml --geth