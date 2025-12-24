import paramiko

class AgentClass(paramiko.Agent):
    def __init__(self):
        super().__init__()

class AgentKeyClass(paramiko.AgentKey):
    def __init__(self, key):
        super().__init__(key)

class AuthFailureClass(paramiko.AuthFailure):
    def __init__(self, message):
        super().__init__(message)

class AuthHandlerClass(paramiko.AuthHandler):
    def __init__(self, transport):
        super().__init__(transport)

class AuthResultClass(paramiko.AuthResult):
    def __init__(self, success, reason=None):
        super().__init__(success, reason)

class AuthSourceClass(paramiko.AuthSource):
    def __init__(self, source):
        super().__init__(source)

class AuthStrategyClass(paramiko.AuthStrategy):
    def __init__(self, strategy):
        super().__init__(strategy)

class AuthenticationExceptionClass(paramiko.AuthenticationException):
    def __init__(self, message):
        super().__init__(message)

class AutoAddPolicyClass(paramiko.AutoAddPolicy):
    def __init__(self):
        super().__init__()

class BadAuthenticationTypeClass(paramiko.BadAuthenticationType):
    def __init__(self, message):
        super().__init__(message)

class BadHostKeyExceptionClass(paramiko.BadHostKeyException):
    def __init__(self, hostname, key):
        super().__init__(hostname, key)

class BaseSFTPClass(paramiko.BaseSFTP):
    def __init__(self, transport):
        super().__init__(transport)

class BufferedFileClass(paramiko.BufferedFile):
    def __init__(self, fileobj, mode):
        super().__init__(fileobj, mode)

class ChannelClass(paramiko.Channel):
    def __init__(self, transport, windowSize=None, maxPacketSize=None):
        super().__init__(transport, window_size=windowSize, max_packet_size=maxPacketSize)

class ChannelExceptionClass(paramiko.ChannelException):
    def __init__(self, message):
        super().__init__(message)

class ChannelFileClass(paramiko.ChannelFile):
    def __init__(self, channel, mode):
        super().__init__(channel, mode)

class ChannelStderrFileClass(paramiko.ChannelStderrFile):
    def __init__(self, channel):
        super().__init__(channel)

class ChannelStdinFileClass(paramiko.ChannelStdinFile):
    def __init__(self, channel):
        super().__init__(channel)

class ConfigParseErrorClass(paramiko.ConfigParseError):
    def __init__(self, message):
        super().__init__(message)

class CouldNotCanonicalizeClass(paramiko.CouldNotCanonicalize):
    def __init__(self, path):
        super().__init__(path)

class DSSKeyClass(paramiko.DSSKey):
    def __init__(self, filename=None, password=None):
        super().__init__(filename, password)

class ECDSAKeyClass(paramiko.ECDSAKey):
    def __init__(self, filename=None, password=None):
        super().__init__(filename, password)

class Ed25519KeyClass(paramiko.Ed25519Key):
    def __init__(self, filename=None, password=None):
        super().__init__(filename, password)

def GSSAuth(transport, username, gssdelegcreds=True):
    return paramiko.GSSAuth(transport, username, gss_deleg_creds=gssdelegcreds)

class HostKeysClass(paramiko.HostKeys):
    def __init__(self):
        super().__init__()

class InMemoryPrivateKeyClass(paramiko.InMemoryPrivateKey):
    def __init__(self, keydata):
        super().__init__(keydata)

class IncompatiblePeerClass(paramiko.IncompatiblePeer):
    def __init__(self, message):
        super().__init__(message)

class InteractiveQueryClass(paramiko.InteractiveQuery):
    def __init__(self, prompt):
        super().__init__(prompt)

class MessageClass(paramiko.Message):
    def __init__(self, data=None):
        super().__init__(data)

class MessageOrderErrorClass(paramiko.MessageOrderError):
    def __init__(self, message):
        super().__init__(message)

class MissingHostKeyPolicyClass(paramiko.MissingHostKeyPolicy):
    def __init__(self):
        super().__init__()

class NoneAuthClass(paramiko.NoneAuth):
    def __init__(self):
        super().__init__()

class OnDiskPrivateKeyClass(paramiko.OnDiskPrivateKey):
    def __init__(self, filename):
        super().__init__(filename)

class PKeyClass(paramiko.PKey):
    def __init__(self):
        super().__init__()

class PacketizerClass(paramiko.Packetizer):
    def __init__(self, transport):
        super().__init__(transport)

class PasswordClass(paramiko.Password):
    def __init__(self, password):
        super().__init__(password)

class PasswordRequiredExceptionClass(paramiko.PasswordRequiredException):
    def __init__(self, message):
        super().__init__(message)

class PrivateKeyClass(paramiko.PrivateKey):
    def __init__(self, data):
        super().__init__(data)

class ProxyCommandClass(paramiko.ProxyCommand):
    def __init__(self, command):
        super().__init__(command)

class ProxyCommandFailureClass(paramiko.ProxyCommandFailure):
    def __init__(self, message):
        super().__init__(message)

class PublicBlobClass(paramiko.PublicBlob):
    def __init__(self, blob):
        super().__init__(blob)

class RSAKeyClass(paramiko.RSAKey):
    def __init__(self, filename=None, password=None):
        super().__init__(filename, password)

class RejectPolicyClass(paramiko.RejectPolicy):
    def __init__(self):
        super().__init__()

class SFTPClass(paramiko.SFTP):
    def __init__(self, transport):
        super().__init__(transport)

class SFTPAttributesClass(paramiko.SFTPAttributes):
    def __init__(self):
        super().__init__()

class SFTPClientClass(paramiko.SFTPClient):
    def __init__(self, sock):
        super().__init__(sock)

class SFTPErrorClass(paramiko.SFTPError):
    def __init__(self, message):
        super().__init__(message)

class SFTPFileClass(paramiko.SFTPFile):
    def __init__(self, fileobj):
        super().__init__(fileobj)

class SFTPHandleClass(paramiko.SFTPHandle):
    def __init__(self, flags=0):
        super().__init__(flags)

class SFTPServerClass(paramiko.SFTPServer):
    def __init__(self, transport):
        super().__init__(transport)

class SFTPServerInterfaceClass(paramiko.SFTPServerInterface):
    def __init__(self):
        super().__init__()

class SSHClientClass(paramiko.SSHClient):
    def __init__(self):
        super().__init__()

class SSHConfigClass(paramiko.SSHConfig):
    def __init__(self):
        super().__init__()

class SSHConfigDictClass(paramiko.SSHConfigDict):
    def __init__(self):
        super().__init__()

class SSHExceptionClass(paramiko.SSHException):
    def __init__(self, message):
        super().__init__(message)

class SecurityOptionsClass(paramiko.SecurityOptions):
    def __init__(self, transport):
        super().__init__(transport)

class ServerInterfaceClass(paramiko.ServerInterface):
    def __init__(self):
        super().__init__()

class ServiceRequestingTransportClass(paramiko.ServiceRequestingTransport):
    def __init__(self, sock):
        super().__init__(sock)

class SourceResultClass(paramiko.SourceResult):
    def __init__(self, result):
        super().__init__(result)

class SubsystemHandlerClass(paramiko.SubsystemHandler):
    def __init__(self, name):
        super().__init__(name)

class TransportClass(paramiko.Transport):
    def __init__(self, sock):
        super().__init__(sock)

class UnknownKeyTypeClass(paramiko.UnknownKeyType):
    def __init__(self, message):
        super().__init__(message)

class WarningPolicyClass(paramiko.WarningPolicy):
    def __init__(self):
        super().__init__()

authFailedConst = paramiko.AUTH_FAILED
authPartiallySuccessfulConst = paramiko.AUTH_PARTIALLY_SUCCESSFUL
authSuccessfulConst = paramiko.AUTH_SUCCESSFUL
gssAuthAvailableConst = paramiko.GSS_AUTH_AVAILABLE
gssExceptionsConst = paramiko.GSS_EXCEPTIONS
openFailedAdministrativelyProhibitedConst = paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
openFailedConnectFailedConst = paramiko.OPEN_FAILED_CONNECT_FAILED
openFailedResourceShortageConst = paramiko.OPEN_FAILED_RESOURCE_SHORTAGE
openFailedUnknownChannelTypeConst = paramiko.OPEN_FAILED_UNKNOWN_CHANNEL_TYPE
openSucceededConst = paramiko.OPEN_SUCCEEDED
sftpBadMessageConst = paramiko.SFTP_BAD_MESSAGE
sftpConnectionLostConst = paramiko.SFTP_CONNECTION_LOST
sftpEofConst = paramiko.SFTP_EOF
sftpFailureConst = paramiko.SFTP_FAILURE
sftpNoConnectionConst = paramiko.SFTP_NO_CONNECTION
sftpNoSuchFileConst = paramiko.SFTP_NO_SUCH_FILE
sftpOkConst = paramiko.SFTP_OK
sftpOpUnsupportedConst = paramiko.SFTP_OP_UNSUPPORTED
sftpPermissionDeniedConst = paramiko.SFTP_PERMISSION_DENIED
versionConst = paramiko._version
agentModuleConst = paramiko.agent
authHandlerModuleConst = paramiko.auth_handler
authStrategyModuleConst = paramiko.auth_strategy
berModuleConst = paramiko.ber
bufferedPipeConst = paramiko.buffered_pipe
channelModuleConst = paramiko.channel
clientModuleConst = paramiko.client
commonModuleConst = paramiko.common
compressModuleConst = paramiko.compress
configModuleConst = paramiko.config
dssKeyModuleConst = paramiko.dsskey
ecdsaKeyModuleConst = paramiko.ecdsakey
ed25519KeyModuleConst = paramiko.ed25519key
fileModuleConst = paramiko.file
hostKeysModuleConst = paramiko.hostkeys
ioSleepConst = paramiko.io_sleep
kexCurve25519Const = paramiko.kex_curve25519
kexEcdhNistConst = paramiko.kex_ecdh_nist
kexGexConst = paramiko.kex_gex
kexGroup1Const = paramiko.kex_group1
kexGroup14Const = paramiko.kex_group14
kexGroup16Const = paramiko.kex_group16
kexGssConst = paramiko.kex_gss
keyClassesConst = paramiko.key_classes
messageModuleConst = paramiko.message
packetModuleConst = paramiko.packet
pipeModuleConst = paramiko.pipe
pkeyModuleConst = paramiko.pkey
primesModuleConst = paramiko.primes
proxyModuleConst = paramiko.proxy
rsaKeyModuleConst = paramiko.rsakey
serverModuleConst = paramiko.server
sftpModuleConst = paramiko.sftp
sftpAttrModuleConst = paramiko.sftp_attr
sftpClientModuleConst = paramiko.sftp_client
sftpFileModuleConst = paramiko.sftp_file
sftpHandleModuleConst = paramiko.sftp_handle
sftpServerModuleConst = paramiko.sftp_server
sftpSiModuleConst = paramiko.sftp_si
sshExceptionModuleConst = paramiko.ssh_exception
sshGssModuleConst = paramiko.ssh_gss
sysModuleConst = paramiko.sys
transportModuleConst = paramiko.transport
utilModuleConst = paramiko.util
