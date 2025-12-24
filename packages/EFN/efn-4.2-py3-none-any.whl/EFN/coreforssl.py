import ssl

AlertDescriptionClass = ssl.AlertDescription
OptionsClass = ssl.Options
PurposeClass = ssl.Purpose
TFlags = ssl.Options
TLSVersionClass = ssl.TLSVersion
VerifyFlagsClass = ssl.VerifyFlags
VerifyModeClass = ssl.VerifyMode

CertificateErrorClass = ssl.CertificateError
SSLCertVerificationErrorClass = ssl.SSLCertVerificationError
SSLErrorClass = ssl.SSLError
SSLEOFErrorClass = ssl.SSLEOFError
SSLWantReadErrorClass = ssl.SSLWantReadError
SSLWantWriteErrorClass = ssl.SSLWantWriteError
SSLZeroReturnErrorClass = ssl.SSLZeroReturnError
SSLSyscallErrorClass = ssl.SSLSyscallError

SSLContextClass = ssl.SSLContext
SSLSocketClass = ssl.SSLSocket
SSLObjectClass = ssl.SSLObject
SSLSessionClass = ssl.SSLSession
MemoryBIOClass = ssl.MemoryBIO
DefaultVerifyPathsClass = ssl.DefaultVerifyPaths

def derCertToPemCert(derCert):
    return ssl.DER_cert_to_PEM_cert(derCert)

def pemCertToDerCert(pemCert):
    return ssl.PEM_cert_to_DER_cert(pemCert)

def createDefaultHttpsContext():
    return ssl._create_default_https_context()

def createStdlibContext():
    return ssl._create_stdlib_context()

def createUnverifiedContext():
    return ssl._create_unverified_context()

def createDefaultContext(purpose=ssl.Purpose.SERVER_AUTH):
    return ssl.create_default_context(purpose=purpose)

def createConnection(address, timeout=None, sourceAddress=None):
    return ssl.create_connection(address, timeout=timeout, source_address=sourceAddress)

def getDefaultVerifyPaths():
    return ssl.get_default_verify_paths()

def getProtocolName(protocol):
    return ssl.get_protocol_name(protocol)

def getServerCertificate(addr, sslVersion=None, caCerts=None):
    return ssl.get_server_certificate(addr, ssl_version=sslVersion, ca_certs=caCerts)

def matchHostname(cert, hostname):
    return ssl.match_hostname(cert, hostname)

AFInetConst = ssl.AF_INET

certNoneConst = ssl.CERT_NONE
certOptionalConst = ssl.CERT_OPTIONAL
certRequiredConst = ssl.CERT_REQUIRED

hasAlpnConst = ssl.HAS_ALPN
hasEcdhConst = ssl.HAS_ECDH
hasNpnConst = ssl.HAS_NPN
hasSniConst = ssl.HAS_SNI
hasNeverCheckCommonNameConst = ssl.HAS_NEVER_CHECK_COMMON_NAME

hasTlsv1Const = ssl.HAS_TLSv1
hasTlsv11Const = ssl.HAS_TLSv1_1
hasTlsv12Const = ssl.HAS_TLSv1_2
hasTlsv13Const = ssl.HAS_TLSv1_3

opensslVersionConst = ssl.OPENSSL_VERSION
opensslVersionInfoConst = ssl.OPENSSL_VERSION_INFO
opensslVersionNumberConst = ssl.OPENSSL_VERSION_NUMBER

protocolSslv23Const = ssl.PROTOCOL_SSLv23
protocolTlsConst = ssl.PROTOCOL_TLS
protocolTlsClientConst = ssl.PROTOCOL_TLS_CLIENT
protocolTlsServerConst = ssl.PROTOCOL_TLS_SERVER
protocolTlsv1Const = ssl.PROTOCOL_TLSv1
protocolTlsv11Const = ssl.PROTOCOL_TLSv1_1
protocolTlsv12Const = ssl.PROTOCOL_TLSv1_2

opAllConst = ssl.OP_ALL
opNoCompressionConst = ssl.OP_NO_COMPRESSION
opNoRenegotiationConst = ssl.OP_NO_RENEGOTIATION
opNoSslv2Const = ssl.OP_NO_SSLv2
opNoSslv3Const = ssl.OP_NO_SSLv3
opNoTlsv1Const = ssl.OP_NO_TLSv1
opNoTlsv11Const = ssl.OP_NO_TLSv1_1
opNoTlsv12Const = ssl.OP_NO_TLSv1_2
opNoTlsv13Const = ssl.OP_NO_TLSv1_3

verifyDefaultConst = ssl.VERIFY_DEFAULT
verifyX509StrictConst = ssl.VERIFY_X509_STRICT
verifyX509TrustedFirstConst = ssl.VERIFY_X509_TRUSTED_FIRST

channelBindingTypesConst = ssl.CHANNEL_BINDING_TYPES
