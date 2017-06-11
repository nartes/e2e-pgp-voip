#!/usr/bin/sh

BASE_NAME=$1

echo "\nAvailable keys\n" || exit

openssl ciphers -tls1_2 -s -V -v || exit

echo "\nKey private generation with a passphrase\n"
openssl genpkey -aes256 -algorithm EC -out build/$BASE_NAME \
	-pkeyopt ec_paramgen_curve:secp521r1 \
	-pkeyopt ec_param_enc:named_curve || exit

echo "\nPrint a plaintext of the key\n" || exit

openssl pkey -text -in build/$BASE_NAME || exit

echo "\nGenerate a public key of the key\n" || exit

openssl pkey -in build/$BASE_NAME -pubout -out build/$BASE_NAME.pub || exit

echo "\nVerify the public key\n" || exit

openssl pkey -pubin -text -in build/$BASE_NAME.pub || exit

echo "\nGenerate a self-signed certificate\n"

openssl req -new -x509 -days 1 -key build/$BASE_NAME \
	-out build/$BASE_NAME.crt \
	-subj "/C=AU/L=Abudabi/O=Masson/CN=localhost"

echo "\nPrint the content of build\n" || exit

ls -allh build/ || exit
