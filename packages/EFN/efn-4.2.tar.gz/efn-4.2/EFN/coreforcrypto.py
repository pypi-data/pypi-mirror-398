from Crypto import version_info as _version_info
from Crypto.Random import atfork as _random_atfork, new as _random_new, get_random_bytes as _random_get_random_bytes, urandom as _random_urandom
from Crypto.Cipher import AES as _AES, ARC2 as _ARC2, ARC4 as _ARC4, Blowfish as _Blowfish, CAST as _CAST, ChaCha20 as _ChaCha20, ChaCha20_Poly1305 as _ChaCha20_Poly1305, DES as _DES, DES3 as _DES3, Salsa20 as _Salsa20
from Crypto.Hash import SHA256 as _SHA256, SHA512 as _SHA512, SHA3_256 as _SHA3_256, SHA3_512 as _SHA3_512, MD5 as _MD5, HMAC as _HMAC, BLAKE2b as _BLAKE2b, BLAKE2s as _BLAKE2s, RIPEMD160 as _RIPEMD160
from Crypto.PublicKey import RSA as _RSA, DSA as _DSA, ECC as _ECC, ElGamal as _ElGamal
from Crypto.Protocol.KDF import HKDF as _HKDF, PBKDF1 as _PBKDF1, PBKDF2 as _PBKDF2, scrypt as _scrypt
from Crypto.Protocol.SecretSharing import Shamir as _Shamir
from Crypto.Signature import pkcs1_15 as _pkcs1_15
from Crypto.Signature import PKCS1_v1_5 as _PKCS1_v1_5
from Crypto.Signature import pss as _PSS
from Crypto.Util.Padding import pad as _pad, unpad as _unpad
from Crypto.Util.number import getPrime as _getPrime, getRandomInteger as _getRandomInteger, getRandomNBitInteger as _getRandomNBitInteger, getRandomRange as _getRandomRange, getStrongPrime as _getStrongPrime, inverse as _inverse, isPrime as _isPrime, long_to_bytes as _long_to_bytes, bytes_to_long as _bytes_to_long, size as _size

def versioninfo():
    return _version_info

def randomatfork():
    return _random_atfork()

def randomnew():
    return _random_new()

def getrandombytes(n):
    return _random_get_random_bytes(n)

def urandombytes(n):
    return _random_urandom(n)

def aesnew(key, mode, iv=None, nonce=None):
    return _AES.new(key, mode, iv=iv, nonce=nonce)

def aessmartpointer():
    return _AES.SmartPointer

def aesmodecbc():
    return _AES.MODE_CBC

def aesmodeccm():
    return _AES.MODE_CCM

def aesmodecfb():
    return _AES.MODE_CFB

def aesmodectr():
    return _AES.MODE_CTR

def aesmodeeax():
    return _AES.MODE_EAX

def aesmodeecb():
    return _AES.MODE_ECB

def aesmodegcm():
    return _AES.MODE_GCM

def aesmodekw():
    return _AES.MODE_KW

def aesmodekwp():
    return _AES.MODE_KWP

def aesmodeocb():
    return _AES.MODE_OCB

def aesmodeofb():
    return _AES.MODE_OFB

def aesmodeopenpgp():
    return _AES.MODE_OPENPGP

def aesmodesiv():
    return _AES.MODE_SIV

def aesblocksize():
    return _AES.block_size

def aesgetrandombytes(n):
    return _AES.get_random_bytes(n)

def aeskeysize():
    return _AES.key_size

def aessys():
    return _AES.sys

def arc2new(key, mode, iv=None):
    return _ARC2.new(key, mode, iv=iv)

def arc2smartpointer():
    return _ARC2.SmartPointer

def arc2modecbc():
    return _ARC2.MODE_CBC

def arc2modecfb():
    return _ARC2.MODE_CFB

def arc2modectr():
    return _ARC2.MODE_CTR

def arc2modeeax():
    return _ARC2.MODE_EAX

def arc2modeecb():
    return _ARC2.MODE_ECB

def arc2modeofb():
    return _ARC2.MODE_OFB

def arc2modeopenpgp():
    return _ARC2.MODE_OPENPGP

def arc2blocksize():
    return _ARC2.block_size

def arc2keysize():
    return _ARC2.key_size

def arc2sys():
    return _ARC2.sys

def arc4new(key):
    return _ARC4.new(key)

def arc4cipher():
    return _ARC4.ARC4Cipher

def arc4smartpointer():
    return _ARC4.SmartPointer

def arc4blocksize():
    return _ARC4.block_size

def arc4keysize():
    return _ARC4.key_size

def blowfishnew(key, mode, iv=None):
    return _Blowfish.new(key, mode, iv=iv)

def blowfishsmartpointer():
    return _Blowfish.SmartPointer

def blowfishmodecbc():
    return _Blowfish.MODE_CBC

def blowfishmodecfb():
    return _Blowfish.MODE_CFB

def blowfishmodectr():
    return _Blowfish.MODE_CTR

def blowfishmodeeax():
    return _Blowfish.MODE_EAX

def blowfishmodeecb():
    return _Blowfish.MODE_ECB

def blowfishmodeofb():
    return _Blowfish.MODE_OFB

def blowfishmodeopenpgp():
    return _Blowfish.MODE_OPENPGP

def blowfishblocksize():
    return _Blowfish.block_size

def blowfishkeysize():
    return _Blowfish.key_size

def blowfishsys():
    return _Blowfish.sys

def castnew(key, mode, iv=None):
    return _CAST.new(key, mode, iv=iv)

def castsmartpointer():
    return _CAST.SmartPointer

def castmodecbc():
    return _CAST.MODE_CBC

def castmodecfb():
    return _CAST.MODE_CFB

def castmodectr():
    return _CAST.MODE_CTR

def castmodeeax():
    return _CAST.MODE_EAX

def castmodeecb():
    return _CAST.MODE_ECB

def castmodeofb():
    return _CAST.MODE_OFB

def castmodeopenpgp():
    return _CAST.MODE_OPENPGP

def castblocksize():
    return _CAST.block_size

def castkeysize():
    return _CAST.key_size

def castsys():
    return _CAST.sys

def chacha20new(key, nonce):
    return _ChaCha20.new(key=key, nonce=nonce)

def chacha20cipher():
    return _ChaCha20.ChaCha20Cipher

def chacha20smartpointer():
    return _ChaCha20.SmartPointer

def chacha20blocksize():
    return _ChaCha20.block_size

def chacha20getrandombytes(n):
    return _ChaCha20.get_random_bytes(n)

def chacha20keysize():
    return _ChaCha20.key_size

def chacha20poly1305new(key, nonce):
    return _ChaCha20_Poly1305.new(key=key, nonce=nonce)

def chacha20poly1305cipher():
    return _ChaCha20_Poly1305.ChaCha20Poly1305Cipher

def chacha20poly1305blake2s():
    return _ChaCha20_Poly1305.BLAKE2s

def chacha20poly1305chacha20():
    return _ChaCha20_Poly1305.ChaCha20

def chacha20poly1305poly1305():
    return _ChaCha20_Poly1305.Poly1305

def chacha20poly1305getrandombytes(n):
    return _ChaCha20_Poly1305.get_random_bytes(n)

def chacha20poly1305keysize():
    return _ChaCha20_Poly1305.key_size

def chacha20poly1305unhexlify():
    return _ChaCha20_Poly1305.unhexlify

def desnew(key, mode, iv=None):
    return _DES.new(key, mode, iv=iv)

def dessmartpointer():
    return _DES.SmartPointer

def desmodecbc():
    return _DES.MODE_CBC

def desmodecfb():
    return _DES.MODE_CFB

def desmodectr():
    return _DES.MODE_CTR

def desmodeeax():
    return _DES.MODE_EAX

def desmodeecb():
    return _DES.MODE_ECB

def desmodeofb():
    return _DES.MODE_OFB

def desmodeopenpgp():
    return _DES.MODE_OPENPGP

def desblocksize():
    return _DES.block_size

def deskeysize():
    return _DES.key_size

def dessys():
    return _DES.sys

def des3new(key, mode, iv=None):
    return _DES3.new(key, mode, iv=iv)

def des3smartpointer():
    return _DES3.SmartPointer

def des3modecbc():
    return _DES3.MODE_CBC

def des3modecfb():
    return _DES3.MODE_CFB

def des3modectr():
    return _DES3.MODE_CTR

def des3modeeax():
    return _DES3.MODE_EAX

def des3modeecb():
    return _DES3.MODE_ECB

def des3modeofb():
    return _DES3.MODE_OFB

def des3modeopenpgp():
    return _DES3.MODE_OPENPGP

def des3blocksize():
    return _DES3.block_size

def des3keysize():
    return _DES3.key_size

def des3sys():
    return _DES3.sys

def salsa20new(key, nonce):
    return _Salsa20.new(key=key, nonce=nonce)

def salsa20cipher():
    return _Salsa20.Salsa20Cipher

def salsa20smartpointer():
    return _Salsa20.SmartPointer

def salsa20blocksize():
    return _Salsa20.block_size

def salsa20getrandombytes(n):
    return _Salsa20.get_random_bytes(n)

def salsa20keysize():
    return _Salsa20.key_size

def sha256new(data=b""):
    return _SHA256.new(data)

def sha512new(data=b""):
    return _SHA512.new(data)

def sha3256new(data=b""):
    return _SHA3_256.new(data)

def sha3512new(data=b""):
    return _SHA3_512.new(data)

def md5new(data=b""):
    return _MD5.new(data)

def hmacnew(key, msg=b""):
    return _HMAC.new(key, msg)

def blake2bnew(data=b"", digest_bits=512):
    return _BLAKE2b.new(data, digest_bits=digest_bits)

def blake2snew(data=b"", digest_bits=256):
    return _BLAKE2s.new(data, digest_bits=digest_bits)

def ripemd160new(data=b""):
    return _RIPEMD160.new(data)

def rsagenerate(bits=2048):
    return _RSA.generate(bits)

def rsaconstruct(n, e, d=None, p=None, q=None):
    return _RSA.construct((n, e, d, p, q))

def rsaimportkey(pem):
    return _RSA.import_key(pem)

def dsagenerate(bits=1024):
    return _DSA.generate(bits)

def dsaimportkey(pem):
    return _DSA.import_key(pem)

def eccgenerate(curve="P-256"):
    return _ECC.generate(curve=curve)

def eccimportkey(pem):
    return _ECC.import_key(pem)

def elgamalgenerate(bits=1024):
    return _ElGamal.generate(bits)

def hkdf(key, salt, info, length, hashmod=_SHA256):
    return _HKDF(key, length, salt, hashmod, context=info)

def pbkdf1(password, salt, dklen, hashmod=_MD5):
    return _PBKDF1(password, salt, dklen, hashmod)

def pbkdf2(password, salt, dklen, count=100000, hashmod=_SHA256):
    return _PBKDF2(password, salt, dklen, count, hmac_hash_module=hashmod)

def scryptderive(password, salt, key_len, n=16384, r=8, p=1):
    return _scrypt(password, salt, key_len, N=n, r=r, p=p)

def shamirsecretshare(k, n, secret):
    return _Shamir.split(k, n, secret)

def shamirsecretrecover(shares):
    return _Shamir.combine(shares)

def pkcs115new(key):
    return _pkcs1_15.new(key)

def dssnew(key, mode="fips-186-3"):
    return _DSS.new(key, mode)

def eddsanew(key):
    return _eddsa.new(key)

def pkcs1pssnew(key):
    return _PKCS1_PSS.new(key)

def padbytes(data, block_size):
    return _pad(data, block_size)

def unpadbytes(data, block_size):
    return _unpad(data, block_size)

def numbergetprime(bits):
    return _getPrime(bits)

def numbergetrandominteger(bits):
    return _getRandomInteger(bits)

def numbergetrandomnbitinteger(bits):
    return _getRandomNBitInteger(bits)

def numbergetrandomrange(a, b):
    return _getRandomRange(a, b)

def numbergetstrongprime(bits):
    return _getStrongPrime(bits)

def numberinverse(u, v):
    return _inverse(u, v)

def numberisprime(n):
    return _isPrime(n)

def numberlongtobytes(n):
    return _long_to_bytes(n)

def numberbytestolong(b):
    return _bytes_to_long(b)

def numbersize(n):
    return _size(n)

from Crypto.Hash import SHA1 as _SHA1, SHA224 as _SHA224, SHA384 as _SHA384, SHA3_224 as _SHA3_224, SHA3_384 as _SHA3_384
from Crypto.Hash import RIPEMD as _RIPEMD, CMAC as _CMAC, Poly1305 as _Poly1305
from Crypto.Signature import pkcs1_15 as _pkcs1_15, PKCS1_v1_5 as _PKCS1_v1_5, pss as _PSS
from Crypto.Util import number as _number, Padding as _Padding, Counter as _Counter

def sha1new(data=b""):
    return _SHA1.new(data)

def sha224new(data=b""):
    return _SHA224.new(data)

def sha384new(data=b""):
    return _SHA384.new(data)

def sha3224new(data=b""):
    return _SHA3_224.new(data)

def sha3384new(data=b""):
    return _SHA3_384.new(data)

def ripemdnew(data=b""):
    return _RIPEMD.new(data)

def cmacnew(key, msg=b""):
    return _CMAC.new(key, msg)

def poly1305new(key, msg=b""):
    return _Poly1305.new(key, msg)

def pkcs115signature(key):
    return _pkcs1_15.new(key)

def pkcs1v15signature(key):
    return _PKCS1_v1_5.new(key)

def psssignature(key):
    return _PSS.new(key)

def numberbyteslong(b):
    return _number.bytes_to_long(b)

def numberlongbytes(n):
    return _number.long_to_bytes(n)

def numbergetprime(bits):
    return _number.getPrime(bits)

def numbergetrandominteger(bits):
    return _number.getRandomInteger(bits)

def numbergetrandomnbitinteger(bits):
    return _number.getRandomNBitInteger(bits)

def numbergetrandomrange(a, b):
    return _number.getRandomRange(a, b)

def numbergetstrongprime(bits):
    return _number.getStrongPrime(bits)

def numberinverse(u, v):
    return _number.inverse(u, v)

def numberisprime(n):
    return _number.isPrime(n)

def numberlong2str(n):
    return _number.long2str(n)

def numberstr2long(s):
    return _number.str2long(s)

def numbergcd(a, b):
    return _number.GCD(a, b)

def padbytes(data, block_size):
    return _Padding.pad(data, block_size)

def unpadbytes(data, block_size):
    return _Padding.unpad(data, block_size)

def counternew(initial_value=1):
    return _Counter.new(initial_value)

from Crypto.Protocol import DH as _DH, KDF as _KDF, SecretSharing as _SecretSharing
from Crypto.Signature import DSS as _DSS, eddsa as _eddsa, pkcs1_15 as _pkcs1_15, pss as _PSS
from Crypto.Util import asn1 as _asn1, RFC1751 as _RFC1751, strxor as _strxor

def dhconstruct(params):
    return _DH.construct(params)

def dhimportx25519privatekey(key):
    return _DH.import_x25519_private_key(key)

def dhimportx25519publickey(key):
    return _DH.import_x25519_public_key(key)

def dhimportx448privatekey(key):
    return _DH.import_x448_private_key(key)

def dhimportx448publickey(key):
    return _DH.import_x448_public_key(key)

def dhkeyagreement(priv, pub):
    return _DH.key_agreement(priv, pub)

def dhlongbytes(n):
    return _DH.long_to_bytes(n)

def hkdfderive(key, salt, info, length):
    return _KDF.HKDF(key, length, salt, _KDF.SHA256, context=info)

def pbkdf1derive(password, salt, dklen):
    return _KDF.PBKDF1(password, salt, dklen, _KDF.SHA1)

def pbkdf2derive(password, salt, dklen, count=100000):
    return _KDF.PBKDF2(password, salt, dklen, count, hmac_hash_module=_KDF.SHA256)

def scryptderive(password, salt, key_len):
    return _KDF.scrypt(password, salt, key_len)

def shamirsplit(k, n, secret):
    return _SecretSharing.Shamir.split(k, n, secret)

def shamircombine(shares):
    return _SecretSharing.Shamir.combine(shares)

def dssnew(key, mode="fips-186-3"):
    return _DSS.new(key, mode)

def eddsanew(key):
    return _eddsa.new(key)

def pkcs115new(key):
    return _pkcs1_15.new(key)

def pssnew(key):
    return _PSS.new(key)

def asn1bchr(val):
    return _asn1.bchr(val)

def asn1bord(val):
    return _asn1.bord(val)

def asn1byteslong(b):
    return _asn1.bytes_to_long(b)

def asn1longbytes(n):
    return _asn1.long_to_bytes(n)

def rfc1751englishkey(key):
    return _RFC1751.english_to_key(key)

def rfc1751keyenglish(key):
    return _RFC1751.key_to_english(key)

def strxorbytes(a, b):
    return _strxor.strxor(a, b)

def strxorconstant(a, c):
    return _strxor.strxor_c(a, c)

from Crypto.PublicKey import DSA as _DSA, ECC as _ECC, ElGamal as _ElGamal, RSA as _RSA
from Crypto.Signature import DSS as _DSS, eddsa as _eddsa, pkcs1_15 as _pkcs1_15, pss as _PSS
from Crypto.Util import py3compat as _py3compat, RFC1751 as _RFC1751, strxor as _strxor

def dsagenerate(bits=1024):
    return _DSA.generate(bits)

def dsaconstruct(params):
    return _DSA.construct(params)

def dsaimportkey(pem):
    return _DSA.import_key(pem)

def eccgenerate(curve="P-256"):
    return _ECC.generate(curve=curve)

def eccconstruct(params):
    return _ECC.construct(params)

def eccimportkey(pem):
    return _ECC.import_key(pem)

def elgamalgenerate(bits=1024):
    return _ElGamal.generate(bits)

def elgamalconstruct(params):
    return _ElGamal.construct(params)

def rsagenerate(bits=2048):
    return _RSA.generate(bits)

def rsaconstruct(params):
    return _RSA.construct(params)

def rsaimportkey(pem):
    return _RSA.import_key(pem)

def dssnew(key, mode="fips-186-3"):
    return _DSS.new(key, mode)

def eddsanew(key):
    return _eddsa.new(key)

def pkcs115new(key):
    return _pkcs1_15.new(key)

def pssnew(key):
    return _PSS.new(key)

def py3compatb(val):
    return _py3compat.b(val)

def py3compatbchr(val):
    return _py3compat.bchr(val)

def py3compatbord(val):
    return _py3compat.bord(val)

def py3compatbstr(val):
    return _py3compat.bstr(val)

def py3compatbytes(val):
    return _py3compat.is_bytes(val)

def py3compatnativeint(val):
    return _py3compat.is_native_int(val)

def py3compatstring(val):
    return _py3compat.is_string(val)

def py3compattobytes(val):
    return _py3compat.tobytes(val)

def py3compattostr(val):
    return _py3compat.tostr(val)

def rfc1751englishkey(key):
    return _RFC1751.english_to_key(key)

def rfc1751keyenglish(key):
    return _RFC1751.key_to_english(key)

def strxorbytes(a, b):
    return _strxor.strxor(a, b)

def strxorconstant(a, c):
    return _strxor.strxor_c(a, c)

from Crypto.Hash import SHAKE128 as _SHAKE128, SHAKE256 as _SHAKE256
from Crypto.Hash import cSHAKE128 as _cSHAKE128, cSHAKE256 as _cSHAKE256
from Crypto.Hash import TurboSHAKE128 as _TurboSHAKE128, TurboSHAKE256 as _TurboSHAKE256
from Crypto.Hash import TupleHash128 as _TupleHash128, TupleHash256 as _TupleHash256
from Crypto.Hash import KangarooTwelve as _KangarooTwelve
from Crypto.Hash import KMAC128 as _KMAC128, KMAC256 as _KMAC256

def shake128new(data=b""):
    return _SHAKE128.new(data)

def shake256new(data=b""):
    return _SHAKE256.new(data)

def cshake128new(data=b"", custom=b""):
    return _cSHAKE128.new(data, custom=custom)

def cshake256new(data=b"", custom=b""):
    return _cSHAKE256.new(data, custom=custom)

def turbosha128new(data=b""):
    return _TurboSHAKE128.new(data)

def turbosha256new(data=b""):
    return _TurboSHAKE256.new(data)

def tuplehash128new(data=b""):
    return _TupleHash128.new(data)

def tuplehash256new(data=b""):
    return _TupleHash256.new(data)

def kangarootwelvenew(data=b""):
    return _KangarooTwelve.new(data)

def kmac128new(key, msg=b""):
    return _KMAC128.new(key, msg)

def kmac256new(key, msg=b""):
    return _KMAC256.new(key, msg)

from Crypto.Util import asn1 as _asn1, number as _number, Padding as _Padding, Counter as _Counter
from Crypto.Util import RFC1751 as _RFC1751, strxor as _strxor, py3compat as _py3compat

def asn1bchr(val):
    return _asn1.bchr(val)

def asn1bord(val):
    return _asn1.bord(val)

def asn1byteslong(b):
    return _asn1.bytes_to_long(b)

def asn1longbytes(n):
    return _asn1.long_to_bytes(n)

def asn1derbitstring():
    return _asn1.DerBitString

def asn1derboolean():
    return _asn1.DerBoolean

def asn1derinteger():
    return _asn1.DerInteger

def asn1dernull():
    return _asn1.DerNull

def asn1derobject():
    return _asn1.DerObject

def asn1derobjectid():
    return _asn1.DerObjectId

def asn1deroctetstring():
    return _asn1.DerOctetString

def asn1dersequence():
    return _asn1.DerSequence

def asn1dersetof():
    return _asn1.DerSetOf

def numberbyteslong(b):
    return _number.bytes_to_long(b)

def numberlongbytes(n):
    return _number.long_to_bytes(n)

def numbergetprime(bits):
    return _number.getPrime(bits)

def numbergetrandominteger(bits):
    return _number.getRandomInteger(bits)

def numbergetrandomnbitinteger(bits):
    return _number.getRandomNBitInteger(bits)

def numbergetrandomrange(a, b):
    return _number.getRandomRange(a, b)

def numbergetstrongprime(bits):
    return _number.getStrongPrime(bits)

def numberinverse(u, v):
    return _number.inverse(u, v)

def numberisprime(n):
    return _number.isPrime(n)

def numberlong2str(n):
    return _number.long2str(n)

def numberstr2long(s):
    return _number.str2long(s)

def numbergcd(a, b):
    return _number.GCD(a, b)

def padbytes(data, block_size):
    return _Padding.pad(data, block_size)

def unpadbytes(data, block_size):
    return _Padding.unpad(data, block_size)

def counternew(initial_value=1):
    return _Counter.new(initial_value)

def rfc1751englishkey(key):
    return _RFC1751.english_to_key(key)

def rfc1751keyenglish(key):
    return _RFC1751.key_to_english(key)

def strxorbytes(a, b):
    return _strxor.strxor(a, b)

def strxorconstant(a, c):
    return _strxor.strxor_c(a, c)

def py3compatb(val):
    return _py3compat.b(val)

def py3compatbchr(val):
    return _py3compat.bchr(val)

def py3compatbord(val):
    return _py3compat.bord(val)

def py3compatbstr(val):
    return _py3compat.bstr(val)

def py3compatbytes(val):
    return _py3compat.is_bytes(val)

def py3compatnativeint(val):
    return _py3compat.is_native_int(val)

def py3compatstring(val):
    return _py3compat.is_string(val)

def py3compattobytes(val):
    return _py3compat.tobytes(val)

def py3compattostr(val):
    return _py3compat.tostr(val)

from Crypto.IO import PEM as _PEM, PKCS8 as _PKCS8, _PBES as _PBES
from Crypto.Random import random as _random
from Crypto.Cipher import PKCS1_OAEP as _PKCS1OAEP, PKCS1_v1_5 as _PKCS1V15
from Crypto.Math import Primality as _Primality
from Crypto.Util import _cpu_features as _cpu
from Crypto.PublicKey import _openssh as _openssh

def pemencode(data, armor=True):
    return _PEM.encode(data, armor)

def pemdecode(pem_data, passphrase=None):
    return _PEM.decode(pem_data, passphrase)

def pempad(data, block_size):
    return _PEM.pad(data, block_size)

def pemunpad(data, block_size):
    return _PEM.unpad(data, block_size)

def pemtobytes(val):
    return _PEM.tobytes(val)

def pemtostr(val):
    return _PEM.tostr(val)

def pempbkdf1(password, salt, dklen, hashmod=None):
    return _PEM.PBKDF1(password, salt, dklen, hashmod)

def pkcs8wrap(private_key, passphrase=None, protection=None, prot_params=None, key_params=None):
    return _PKCS8.wrap(private_key, passphrase, protection, prot_params, key_params)

def pkcs8unwrap(pem_data, passphrase=None):
    return _PKCS8.unwrap(pem_data, passphrase)

def pbespbkdf1(password, salt, dklen, hashmod=None):
    return _PBES.PBKDF1(password, salt, dklen, hashmod)

def pbespbkdf2(password, salt, dklen, count, prf=None):
    return _PBES.PBKDF2(password, salt, dklen, count, prf)

def pbesscrypt(password, salt, key_len, n=16384, r=8, p=1):
    return _PBES.scrypt(password, salt, key_len, n, r, p)

def pbespad(data, block_size):
    return _PBES.pad(data, block_size)

def pbesunpad(data, block_size):
    return _PBES.unpad(data, block_size)

def randomchoice(seq):
    return _random.choice(seq)

def randomgetbits(n):
    return _random.getrandbits(n)

def randomrandint(a, b):
    return _random.randint(a, b)

def randomrandrange(start, stop=None, step=1):
    return _random.randrange(start, stop, step)

def randomsample(population, k):
    return _random.sample(population, k)

def randomshuffle(x):
    return _random.shuffle(x)

def pkcs1oaepnew(key, hashmod=None, mgf=None, label=b""):
    return _PKCS1OAEP.new(key, hashAlgo=hashmod, mgfunc=mgf, label=label)

def pkcs1v15new(key):
    return _PKCS1V15.new(key)

def primalitygenerateprime(bits):
    return _Primality.generate_probable_prime(bits)

def primalitygeneratesafeprime(bits):
    return _Primality.generate_probable_safe_prime(bits)

def primalitylucastest(n):
    return _Primality.lucas_test(n)

def primalitymillerrabintest(n, rounds=5):
    return _Primality.miller_rabin_test(n, rounds)

def primalitytestprime(n):
    return _Primality.test_probable_prime(n)

def cpufeatureshaveaesni():
    return _cpu.have_aes_ni()

def cpufeatureshaveclmul():
    return _cpu.have_clmul()

def opensshimportprivate(pem, passphrase=None):
    return _openssh.import_openssh_private_generic(pem, passphrase)

def opensshcheckpadding(data):
    return _openssh.check_padding(data)

from Crypto.Cipher import _mode_cbc as _cbc, _mode_cfb as _cfb, _mode_ctr as _ctr, _mode_eax as _eax
from Crypto.Cipher import _mode_gcm as _gcm, _mode_ocb as _ocb, _mode_ofb as _ofb, _mode_siv as _siv, _mode_ecb as _ecb
from Crypto.Math import _IntegerBase as _IntegerBase, _IntegerNative as _IntegerNative, _IntegerCustom as _IntegerCustom
from Crypto.Util import _raw_api as _raw_api

def cbcnew(key, iv):
    return _cbc.CbcMode(key, iv)

def cfnew(key, iv):
    return _cfb.CfbMode(key, iv)

def ctrnew(key, counter):
    return _ctr.CtrMode(key, counter)

def eaxnew(key, nonce):
    return _eax.EaxMode(key, nonce)

def gcmnew(key, nonce):
    return _gcm.GcmMode(key, nonce)

def ocbnew(key, nonce):
    return _ocb.OcbMode(key, nonce)

def ofbnew(key, iv):
    return _ofb.OfbMode(key, iv)

def sivnew(key, nonce):
    return _siv.SivMode(key, nonce)

def ecbnew(key):
    return _ecb.EcbMode(key)

def integerbase():
    return _IntegerBase.IntegerBase

def integernative():
    return _IntegerNative.IntegerNative

def integercustom():
    return _IntegerCustom.IntegerCustom

def rawapiffi():
    return _raw_api.FFI

def rawapismartpointer():
    return _raw_api.SmartPointer

def rawapivoidpointer():
    return _raw_api.VoidPointer_cffi

from Crypto.Cipher import _mode_kw as _kw, _mode_kwp as _kwp, _mode_openpgp as _openpgp, _mode_siv as _siv
from Crypto.PublicKey import _point as _point, _nist_ecc as _nist_ecc

def kwnew(key, data):
    return _kw.KWMode(key, data)

def kwinverse(key, data):
    return _kw.W_inverse(key, data)

def kwstrxor(a, b):
    return _kw.strxor(a, b)

def kwpmode(key, data):
    return _kwp.KWPMode(key, data)

def openpgpnew(key, iv=None):
    return _openpgp.OpenPgpMode(key, iv)

def sivmode(key, nonce):
    return _siv.SivMode(key, nonce)

def eccpoint(x, y):
    return _point.EccPoint(x, y)

def eccxpoint(x, y):
    return _point.EccXPoint(x, y)

def curvep192():
    return _nist_ecc.p192_curve

def curvep224():
    return _nist_ecc.p224_curve

def curvep256():
    return _nist_ecc.p256_curve

def curvep384():
    return _nist_ecc.p384_curve

def curvep521():
    return _nist_ecc.p521_curve
