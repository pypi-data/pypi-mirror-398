#!/usr/bin/python3
# coding=utf-8
##################################################################
#              ____     _     _ __  __                 
#             / __/__  (_)___(_) /_/ /  ___  ___  ___ _
#            _\ \/ _ \/ / __/ / __/ /__/ _ \/ _ \/ _ `/
#           /___/ .__/_/_/ /_/\__/____/\___/_//_/\_, / 
#              /_/                              /___/  
# 
# Copyright (c) 2025 Chongqing Spiritlong Technology Co., Ltd.
# All rights reserved.
# @author	arthuryang
# @brief	SSH工具
##################################################################

# session名称格式：用户名@HOSTNAME。符合此格式的才进行处理

import	os
import	base64

# 仅在windows下可用
if os.name=='nt':
	import	winreg

import	hmac
import	hashlib
import	paramiko
import	SpiritLong_utility
import	SpiritLong_excel
from	nacl.signing	import	SigningKey	# pip install pynacl
from	nacl.encoding	import	Base64Encoder	as nacl_Base64Encoder
from	nacl.encoding	import	RawEncoder	as nacl_RawEncoder

# PuTTY注册表sessions路径
PUTTY_REGISTRY_PATH	= r"SOFTWARE\SimonTatham\PuTTY\Sessions"

# SSH路径：用户/OneDrive/文档/SSH
# 仅在windows下可用
if os.name=='nt':
	USER_SSH_BASE	= os.path.join(os.getenv('USERPROFILE'), 'OneDrive', '文档', 'SSH')
else:
	USER_SSH_BASE	= os.getenv('HOME')

# 需要读取/保存的设置
PUTTY_CONFIG	= [
	"HostName",		# 主机地址
	"PortNumber",		# 端口
	"UserName",		# 用户名
	"PublicKeyFile",	# 密钥文件（ppk文件）位置
]

# PuTTY注册表中的全部配置
PUTTY_CONFIG_DEFAULT	= {
	'HostName'			: '',
	'PortNumber'			: 22,
	'UserName'			: 'root',
	'PublicKeyFile'			: '',			# ppk文件位置
	
	# 字体
	'Font'				: 'Fixedsys',
	'FontHeight'			: 10,
	'FontIsBold'			: 0,			# 字体样式：是否加粗
	'FontQuality'			: 3,			# 字体质量 3->ClearType
	'FontCharSet'			: 134,			# 字体编码

	# Alt+Enter全屏
	'FullScreenOnAltEnter'		: 1,

	# 初始分辨率，单位为字符
	'TermWidth'			: 132,
	'TermHeight'			: 80,

	'WinTitle'			: 'arthuryang@PROGRAM',
	'Protocol'			: 'ssh',
	'BlinkCur'			: 1,
		
	# 行缓存数量	
	'ScrollbackLines'		: 999999,
	# X11转发使能才可以使用图形界面
	'X11Forward'			: 1,

	# TCP选项
	'PingInterval'			: 0,	# 发送TCPKeepalives的间隔：分钟数部分
	'PingIntervalSecs'		: 30,	# 发送TCPKeepalives的间隔：秒数部分
	'TCPNoDelay'			: 1,	# TCP_NODELAY
	'TCPKeepalives'			: 1,	# SO_KEEPALIVE

	'NoApplicationKeys'		: 1,	# 禁止应用程序小键盘，这可以在vi中正常使用小键盘
	'NoRemoteWinTitle'		: 1,	# 禁止远程修改标题

	# 以下是PuTTY默认设置
	'Present'			: 1,
	'LogFileName'			: 'putty.log',
	'LogType'			: 0,
	'LogFileClash'			: 4294967295,
	'LogFlush'			: 1,
	'LogHeader'			: 1,
	'SSHLogOmitPasswords'		: 1,
	'SSHLogOmitData'		: 0,
	'CloseOnExit'			: 1,
	'WarnOnClose'			: 1,	
	'TerminalType'			: 'xterm',
	'TerminalSpeed'			: '38400,38400',
	'TerminalModes'			: 'CS7=A,CS8=A,DISCARD=A,DSUSP=A,ECHO=A,ECHOCTL=A,ECHOE=A,ECHOK=A,ECHOKE=A,ECHONL=A,EOF=A,EOL=A,EOL2=A,ERASE=A,FLUSH=A,ICANON=A,ICRNL=A,IEXTEN=A,IGNCR=A,IGNPAR=A,IMAXBEL=A,INLCR=A,INPCK=A,INTR=A,ISIG=A,ISTRIP=A,IUCLC=A,IUTF8=A,IXANY=A,IXOFF=A,IXON=A,KILL=A,LNEXT=A,NOFLSH=A,OCRNL=A,OLCUC=A,ONLCR=A,ONLRET=A,ONOCR=A,OPOST=A,PARENB=A,PARMRK=A,PARODD=A,PENDIN=A,QUIT=A,REPRINT=A,START=A,STATUS=A,STOP=A,SUSP=A,SWTCH=A,TOSTOP=A,WERASE=A,XCASE=A',
	'AddressFamily'			: 0,
	'ProxyExcludeList'		: '',
	'ProxyDNS'			: 1,
	'ProxyLocalhost'		: 0,
	'ProxyMethod'			: 0,
	'ProxyHost'			: 'proxy',
	'ProxyPort'			: 80,
	'ProxyUsername'			: '',
	'ProxyPassword'			: '',
	'ProxyTelnetCommand'		: 'connect %host %port\n',
	'ProxyLogToTerm'		: 1,
	'Environment'			: '',
	'UserNameFromEnvironment	'	: 0,
	'LocalUserName'			: '',
	'NoPTY'				: 0,
	'Compression'			: 0,
	'TryAgent'			: 1,
	'AgentFwd'			: 0,
	'GssapiFwd'			: 0,
	'ChangeUsername'		: 0,
	'Cipher'			: 'aes,chacha20,3des,WARN,des,blowfish,arcfour',
	'KEX'				: 'ecdh,dh-gex-sha1,dh-group14-sha1,rsa,WARN,dh-group1-sha1',
	'HostKey'			: 'ed448,ed25519,ecdsa,rsa,dsa,WARN',
	'PreferKnownHostKeys'		: 1,
	'RekeyTime'			: 60,
	'GssapiRekey'			: 2,
	'RekeyBytes'			: '1G',
	'SshNoAuth'			: 0,
	'SshNoTrivialAuth'		: 0,
	'SshBanner'			: 1,
	'AuthTIS'			: 0,
	'AuthKI'			: 1,
	'AuthGSSAPI'			: 1,
	'AuthGSSAPIKEX'			: 1,
	'GSSLibs'			: 'gssapi32,sspi,custom',
	'GSSCustom'			: '',
	'SshNoShell'			: 0,
	'SshProt'			: 3,
	'LogHost'			: '',
	'SSH2DES'			: 0,
	'RemoteCommand'			: '',
	'RFCEnviron'			: 0,
	'PassiveTelnet'			: 0,
	'BackspaceIsDelete'		: 1,
	'RXVTHomeEnd'			: 0,
	'LinuxFunctionKeys'		: 0,
	'NoApplicationCursors'		: 0,
	'NoMouseReporting'		: 0,
	'NoRemoteResize'		: 0,
	'NoAltScreen'			: 0,
	'NoRemoteClearScroll'		: 0,
	'RemoteQTitleAction'		: 1,
	'NoDBackspace'			: 0,
	'NoRemoteCharset'		: 0,
	'ApplicationCursorKeys'		: 0,
	'ApplicationKeypad'		: 1,
	'NetHackKeypad'			: 0,
	'AltF4'				: 1,
	'AltSpace'			: 0,
	'AltOnly'			: 0,
	'ComposeKey'			: 0,
	'CtrlAltKeys'			: 1,
	'TelnetKey'			: 0,
	'TelnetRet'			: 1,
	'LocalEcho'			: 2,
	'LocalEdit'			: 2,
	'Answerback'			: 'PuTTY',
	'AlwaysOnTop'			: 0,
	'HideMousePtr'			: 0,
	'SunkenEdge'			: 0,
	'WindowBorder'			: 1,
	'CurType'			: 0,
	'Beep'				: 1,
	'BeepInd'			: 0,
	'BellWaveFile'			: '',
	'BellOverload'			: 1,
	'BellOverloadN'			: 5,
	'BellOverloadT'			: 2000,
	'BellOverloadS'			: 5000,
	'DECOriginMode'			: 0,
	'AutoWrapMode'			: 1,
	'LFImpliesCR'			: 0,
	'CRImpliesLF'			: 0,
	'DisableArabicShaping'		: 0,
	'DisableBidi'			: 0,
	'WinNameAlways'			: 1,
	'FontVTMode'			: 4,
	'UseSystemColours'		: 0,
	'TryPalette'			: 0,
	'ANSIColour'			: 1,
	'Xterm256Colour'		: 1,
	'TrueColour'			: 1,
	'BoldAsColour'			: 1,
	'Colour0'			: '187,187,187',
	'Colour1'			: '255,255,255',
	'Colour2'			: '0,0,0',
	'Colour3'			: '85,85,85',
	'Colour4'			: '0,0,0',
	'Colour5'			: '0,255,0',
	'Colour6'			: '0,0,0',
	'Colour7'			: '85,85,85',
	'Colour8'			: '187,0,0',
	'Colour9'			: '255,85,85',
	'Colour10'			: '0,187,0',
	'Colour11'			: '85,255,85',
	'Colour12'			: '187,187,0',
	'Colour13'			: '255,255,85',
	'Colour14'			: '0,0,187',
	'Colour15'			: '85,85,255',
	'Colour16'			: '187,0,187',
	'Colour17'			: '255,85,255',
	'Colour18'			: '0,187,187',
	'Colour19'			: '85,255,255',
	'Colour20'			: '187,187,187',
	'Colour21'			: '255,255,255',
	'RawCNP'			: 0,
	'UTF8linedraw'			: 0,
	'PasteRTF'			: 0,
	'MouseIsXterm'			: 0,
	'RectSelect'			: 0,
	'PasteControls'			: 0,
	'MouseOverride'			: 1,
	'Wordness0'			: '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0',
	'Wordness32'			: '0,1,2,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1',
	'Wordness64'			: '1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,2',
	'Wordness96'			: '1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1',
	'Wordness128'			: '1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
	'Wordness160'			: '1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
	'Wordness192'			: '2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2',
	'Wordness224'			: '2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2',
	'MouseAutocopy'			: 1,
	'MousePaste'			: 'explicit',
	'CtrlShiftIns'			: 'explicit',
	'CtrlShiftCV'			: 'none',
	'LineCodePage'			: '',
	'CJKAmbigWide'			: 0,
	'UTF8Override'			: 1,
	'Printer'			: '',
	'CapsLockCyr'			: 0,
	'ScrollBar'			: 1,
	'ScrollBarFullScreen'		: 0,
	'ScrollOnKey'			: 0,
	'ScrollOnDisp'			: 1,
	'EraseToScrollback'		: 1,
	'LockSize'			: 0,
	'BCE'				: 1,
	'BlinkText'			: 0,
	'X11Display'			: '',
	'X11AuthType'			: 1,
	'X11AuthFile'			: '',
	'LocalPortAcceptAll'		: 0,
	'RemotePortAcceptAll'		: 0,
	'PortForwardings'		: '',
	'BugIgnore1'			: 0,
	'BugPlainPW1'			: 0,
	'BugRSA1'			: 0,
	'BugIgnore2'			: 0,
	'BugHMAC2'			: 0,
	'BugDeriveKey2'			: 0,
	'BugRSAPad2'			: 0,
	'BugPKSessID2'			: 0,
	'BugRekey2'			: 0,
	'BugMaxPkt2'			: 0,
	'BugOldGex2'			: 0,
	'BugWinadj'			: 0,
	'BugChanReq'			: 0,
	'StampUtmp'			: 1,
	'LoginShell'			: 1,
	'ScrollbarOnLeft'		: 0,
	'BoldFont'			: '',
	'BoldFontIsBold'		: 0,
	'BoldFontCharSet'		: 0,
	'BoldFontHeight'		: 0,
	'WideFont'			: '',
	'WideFontIsBold'		: 0,
	'WideFontCharSet'		: 0,
	'WideFontHeight'		: 0,
	'WideBoldFont'			: '',
	'WideBoldFontIsBold'		: 0,
	'WideBoldFontCharSet'		: 0,
	'WideBoldFontHeight'		: 0,
	'ShadowBold'			: 0,
	'ShadowBoldOffset'		: 1,
	'SerialLine'			: 'COM1',
	'SerialSpeed'			: 115200,
	'SerialDataBits'		: 8,
	'SerialStopHalfbits'		: 2,
	'SerialParity'			: 0,
	'SerialFlowControl'		: 1,
	'WindowClass'			: '',
	'ConnectionSharing'		: 0,
	'ConnectionSharingUpstream'	: 1,
	'ConnectionSharingDownstream'	: 1,
	'SSHManualHostKeys'		: '',
	'SUPDUPLocation'		: 'The Internet',
	'SUPDUPCharset'			: 0,
	'SUPDUPMoreProcessing'		: 0,
	'SUPDUPScrolling'		: 0,
}

## 在数据前面增加4字节长度，注意长度是大端
def big_Endian_bytes(data):
	if isinstance(data, str):
		# 字符串需要先转换到bytes
		data	= data.encode('ascii')
	return len(data).to_bytes(4, 'big')+data

## 生成随机密钥
def generate_random_key(algorithm='ssh-ed25519'):
	# 生成ed25519密钥
	key	= SigningKey.generate()
	verify	= key.verify_key

	# 生成密钥bytes
	private_key	= key.encode(nacl_RawEncoder)
	public_key	= verify.encode(nacl_RawEncoder)

	return {
		# 原始密钥
		'private'	: private_key,
		'public'	: public_key,

		# 密钥base64编码
		'private_string'	: base64.b64encode(big_Endian_bytes(private_key)).decode('ascii'),
		# 算法名称+密钥，然后base64编码
		'public_string'		: base64.b64encode(big_Endian_bytes(algorithm)+big_Endian_bytes(public_key)).decode('ascii'),
	}
	
## 从putty的ppk文件提取出密钥各部分信息
def _get_ppk_items(ppk_file_path):
	items	= {}
	with open(ppk_file_path, 'r', encoding='utf-8') as f:
		lines	= f.readlines()
		i	= 0
		while i<len(lines):
			n	= 1
			try:
				title, value	= lines[i].split(':', maxsplit=1)
				value	= value.strip()
				if title.startswith('PuTTY-User-Key-File'):
					# key的算法类型
					title	= 'key_type'
				if title=='Public-Lines':
					title	= 'public'
					n	= int(value)+1
					key_value_lines	= [v.strip() for v in lines[(i+1):(i+n)]]
					value	= ''.join(key_value_lines)
				elif title=='Private-Lines':
					title	= 'private'
					n	= int(value)+1
					key_value_lines	= [v.strip() for v in lines[(i+1):(i+n)]]
					value	= ''.join(key_value_lines)
				elif title=='Comment':
					title	= 'comment'
					value	= value.strip()
				items[title]	= value
			except:
				title	= None
				value	= None
			i	+= n;			
	return items


## 获取session在PUTTY_CONFIG中的配置
def get_session_config(session_name):
	# 仅在windows下可用
	if os.name!='nt':
		print("windows only")
		return

	config	= {}
	try:
		session_key		= winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"{PUTTY_REGISTRY_PATH}\\{session_name}")
	
		for c in PUTTY_CONFIG:
			config[c], value_type	= winreg.QueryValueEx(session_key, c)
		winreg.CloseKey(session_key)
	except Exception as e:
		print(e)
	return config

## 从注册表读取PuTTY配置，写入到excel
def export_PuTTY_config(filename):
	# 仅在windows下可用
	if os.name!='nt':
		print("windows only")
		return

	sessions	= []
	try:
		# 读取putty的所有ses///sion的注册表
		session_root_key	= winreg.OpenKey(winreg.HKEY_CURRENT_USER, PUTTY_REGISTRY_PATH)
		subkeys_n, _, _	= winreg.QueryInfoKey(session_root_key)
		for i in range(subkeys_n):
			# 每个subkey是一个session，只取关键的配置
			session_name	= winreg.EnumKey(session_root_key, i)
			session		= get_session_config(session_name)

			# 校验session名的格式：user@HOSTNAME；若session名称里面包含了"."，则不是HOSTNAME，而是session名称，仍然放在HOSTNAME字段
			parts	= session_name.split('@')
			if len(parts)>1:
				# 包含@则必须是username@HOSTNAME的样式
				session['HOSTNAME']	= parts[1]
				if parts[0]!=session['UserName']:
					# 用户名得对得上才行
					session	= None
			elif '.' not in parts[0]:
				# 若不包含@，则应该是一个域名，必须包含"."，否则无效
				session	= None
			else:
				# 不包含@但包含"."的将session名称放在HOSTNAME
				session['HOSTNAME']	= parts[0]

			if session:
				sessions.append(session)
		winreg.CloseKey(session_root_key)
	except Exception as e:
		print(f"读取注册表失败: {e}")
	
	# 生成excel数据
	records	= []
	for s in sessions:
		r	= {
			'主机'		: s['HostName'],
			'HOSTNAME'	: s['HOSTNAME'],
			'端口'		: s['PortNumber'],
			'用户'	: s['UserName'],
		}
		
		generate	= True
		try:
			v	= _get_ppk_items(s['PublicKeyFile'])
			if v['key_type']=='ssh-ed25519':
				generate	= False
			r['私钥']	= v['private']
			r['公钥']	= v['public']
		except:
			pass

		if generate:
			# 生成密钥
			k	= generate_random_key()
			r['私钥']	= k['private_string']
			r['公钥']	= k['public_string']
		records.append(r)

	# 写入到excel
	SpiritLong_excel.records_to_excel(filename, {
		'主机'	: {
			# 确保按此顺序放置各列
			'titles'	: ['用户', 'HOSTNAME', '主机', '端口', '公钥', '私钥'],
			'records'	: records,
		}
	})

## 根据公钥和私钥生成ppk文件
#	filename	ppk文件名，含路径
#	public_key	公钥，带有长度的base64字符串（含算法名称）
#	private_key	私钥，带有长度的base64字符串
def generate_ppk_file(filename, public_key, private_key, comment):
	# 将字符串换成字节数组
	public_key	= public_key.encode('ascii')
	private_key	= private_key.encode('ascii')

	# 公钥分行
	public_lines	= [public_key[i:i+64].decode('ascii')+'\n' for i in range(0, len(public_key), 64)]

	# 私钥分行
	private_lines	= [private_key[i:i+64].decode('ascii')+'\n' for i in range(0, len(private_key), 64)]

	# 计算MAC，注意私钥和公钥要base64解码
	data	= big_Endian_bytes('ssh-ed25519')			+\
		  big_Endian_bytes('none')				+\
		  big_Endian_bytes(comment)				+\
		  big_Endian_bytes(base64.b64decode(public_key))	+\
		  big_Endian_bytes(base64.b64decode(private_key))
	MAC	= hmac.new(b'', data, hashlib.sha256).hexdigest()

	with open(filename, 'w', encoding='utf-8') as f:
		f.write("PuTTY-User-Key-File-3: ssh-ed25519\n")
		f.write("Encryption: none\n")
		f.write(f"Comment: {comment}\n")
		f.write(f"Public-Lines: {len(public_lines)}\n")
		f.writelines(public_lines)
		f.write(f"Private-Lines: {len(private_lines)}\n")
		f.writelines(private_lines)
		f.write(f"Private-MAC: {MAC}\n")

## 生成OPEN_SSH私钥文件（仅支持ed25519)
#	filename	ppk文件名，含路径
#	public_key	公钥，带有长度的base64字符串（含算法名称）
#	private_key	私钥，带有长度的base64字符串
def generate_OPENSSH_file(filename, public_key, private_key, comment=''): 
	# OpenSSH密钥格式 ed25519 private v1密钥格式，参考：https://sshref.dev/
	# 0.0 "openssh-key-v1" string plus terminating nullbyte (15 bytes)
	# 1.0 uint32 allocator for 1.0.0 (4 bytes)
	#     1.0.0 cipher name string (ASCII bytes)
	# 2.0 uint32 allocator for 2.0.0 (4 bytes)
	#     2.0.0 KDF name string (ASCII bytes)
	# 3.0 uint32 allocator for KDF options (3.0.0 to 3.0.1) (4 bytes) (ALWAYS 0 for unencrypted keys, so no following substructure)
	# 4.0 uint32 counter for # of keys (4 bytes)
	#     4.0.0 uint32 allocator for public key #n (4.0.0.0 to 4.0.0.1) (4 bytes)
	#         4.0.0.0 uint32 allocator for 4.0.0.0.0 (4 bytes)
	#             4.0.0.0.0 public key #n keytype string (ASCII bytes)
	#         4.0.0.1 uint32 allocator for 4.0.0.1.0 (4 bytes)
	#             4.0.0.1.0 public key #n payload (bytes)
	#     4.0.1 uint32 allocator for private key structure #n (4.0.1.0 to 4.0.1.5) (4 bytes)
	#         4.0.1.0 uint32 decryption "checksum" #1 (should match 4.0.1.1) (4 bytes)
	#         4.0.1.1 uint32 decryption "checksum" #2 (should match 4.0.1.0) (4 bytes)
	#         4.0.1.2 Copy of 4.0.0.0; allocator for 4.0.1.2.0 (4 bytes)
	#             4.0.1.2.0 Copy of 4.0.0.0.0 (ASCII bytes)
	#         4.0.1.3 Copy of 4.0.0.1; allocator for 4.0.1.3.0 (4 bytes)
	#             4.0.1.3.0 Copy of 4.0.0.1.0 (bytes)
	#         4.0.1.4 uint32 allocator for 4.0.1.4.0 (4 bytes)
	#             4.0.1.4.0 Private key #n (bytes)
	#         4.0.1.5 uint32 allocator for 4.0.1.5.0 (4 bytes)
	#             4.0.1.5.0 comment for key #n string (ASCII bytes)
	#         4.0.1.6 sequential padding

	key_n		= 1				# 密钥数量 (4.0 uint32 counter for # of keys)
	
	# 解算base64到bytes，注意公钥是类型+公钥
	public_bytes		= base64.b64decode(public_key)
	public_key_bytes	= public_bytes[(int.from_bytes(public_bytes[:4], 'big')+4+4):]

	# 解算base64到bytes
	private_bytes	= base64.b64decode(private_key)

	# 校验和1：未使用 (4.0.1.0 uint32 decryption "checksum" #1)
	# 校验和2：未使用 (4.0.1.1 uint32 decryption "checksum" #2)
	private_key_bytes	= big_Endian_bytes('')+big_Endian_bytes('')
	# 算法名（ssh-ed25519）(4.0.1.2.0 Copy of 4.0.0.0.0)
	# 公钥内容32字节 (4.0.1.3.0 Copy of 4.0.0.1.0)
	private_key_bytes	+=  public_bytes
	# 私钥内容64字节 (4.0.1.4.0 Private key #n (bytes))
	private_key_bytes	+=   big_Endian_bytes(private_bytes[4:]+public_key_bytes)
	# 私钥注释 (4.0.1.5.0 comment for key #n string)
	private_key_bytes	+=  big_Endian_bytes(comment)
	# sequential padding填充，私钥数据长度必须是8的倍数 (4.0.1.6 sequential padding)
	padding_length	= 8 - (len(private_key_bytes) % 8)
	if padding_length<8:
		private_key_bytes	+= bytes(range(1, 1+padding_length))	# 填充1,2,3...padding_length
	
	key_bytes	=  b'openssh-key-v1\0'			# OpenSSH密钥标识 (0.0 "openssh-key-v1" string plus terminating nullbyte)
	key_bytes	+= big_Endian_bytes('none')		# 加密算法：无 (1.0 uint32 allocator for 1.0.0 cipher name string)
	key_bytes	+= big_Endian_bytes('none')		# KDF算法：无 (2.0 uint32 allocator for 2.0.0 KDF name string)
	key_bytes	+= big_Endian_bytes('')			# KDF选项 (3.0 uint32 allocator for KDF options, ALWAYS 0 for unencrypted keys)
	key_bytes	+= key_n.to_bytes(4, 'big')		# 密钥数量
	key_bytes	+= big_Endian_bytes(public_bytes)	# 公钥
	key_bytes	+= big_Endian_bytes(private_key_bytes)	# 私钥

	# 编码成base64字符串
	key_string	= base64.b64encode(key_bytes).decode('ascii')

	# 写入文件
	with open(filename, 'w', encoding='utf-8') as f:
		f.write("-----BEGIN OPENSSH PRIVATE KEY-----\n")
		f.write('\n'.join(key_string[i:i+70] for i in range(0, len(key_string), 70)))
		f.write("\n-----END OPENSSH PRIVATE KEY-----\n")

## 根据配置文件写入PuTTY注册表选项
#	filename	配置文件名（含路径）
#	PPK_path	密钥保存路径，ppk文件将放在path/PPK下，OPENSSH文件将放在path/OPENSSH下
#	who_as_root	当用户为root时，需要个表示实际人员的字符串，此字符串将出现在/root/.ssh/authorized_keys里面该密钥的后面注释，以区分是谁的公钥
#	flush		清除当前所有配置，重新写入。注意如果此选项为True，则需要管理员权限
def import_PuTTY_config(filename, who_as_root, SSH_path=f'{USER_SSH_BASE}', flush=False, font_name='Fixedsys'):
	# 仅在windows下可用
	if os.name!='nt':
		print("windows only")
		return

	records	= []
	try:
		book	= SpiritLong_excel.open_xlsx(filename)
		records	= SpiritLong_excel.get_records_with_title(book['主机'])
	except:
		print(f"无法读取配置文件{filename}")
		return
	
	# 清除当前所有Session
	if flush:
		# 由于无法直接删除带子键的键，因此需要遍历。注意，需要尝试创建PUTTY_REGISTRY_PATH，若已存在则会打开
		session_root_key	= winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, PUTTY_REGISTRY_PATH, access=winreg.KEY_ALL_ACCESS)
		subkeys_n, _, _	= winreg.QueryInfoKey(session_root_key)
		session_names	= []
		for i in range(subkeys_n):
			# Session键中应该没有子键
			session_names.append(winreg.EnumKey(session_root_key, i))
		for s in session_names:
			session_key	= winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"{PUTTY_REGISTRY_PATH}\\{s}")
			winreg.DeleteKeyEx(session_key, '')
		winreg.CloseKey(session_root_key)
	
	# PPK文件所在路径
	PPK_path	= os.path.join(SSH_path, 'PPK')
	if not os.path.exists(PPK_path):
		os.mkdir(PPK_path)

	# OPENSSH文件所在路径
	OPENSSH_path	= os.path.join(SSH_path, 'OPENSSH')
	if not os.path.exists(OPENSSH_path):
		os.mkdir(OPENSSH_path)
 
	for r in records:
		# session名称：用户名@HOSTNAME，但若HOSTNAME有.则直接使用HOSTNAME作为session名称
		session_name	= r['HOSTNAME'] if '.' in r['HOSTNAME'] else f"{r['用户']}@{r['HOSTNAME']}"
		# 创建记录
		session_key	= winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{PUTTY_REGISTRY_PATH}\\{session_name}")
		
		comment		= f"{who_as_root}@{r['HOSTNAME']}" if r['用户']=='root' else f"{r['用户']}"
		
		# 生成ppk
		ppk_file	= os.path.join(PPK_path, session_name+'.ppk')
		generate_ppk_file(ppk_file, r['公钥'], r['私钥'], comment)

		# 生成OPENSSH
		OPENSSH_file	= os.path.join(OPENSSH_path, session_name+'.key')
		generate_OPENSSH_file(OPENSSH_file, r['公钥'], r['私钥'], comment)
		
		# 写入默认的配置值
		for k in PUTTY_CONFIG_DEFAULT:
			# 不是字符串就只可能是DWORD了
			winreg.SetValueEx(session_key, k, 0, winreg.REG_SZ if isinstance(PUTTY_CONFIG_DEFAULT[k], str) else winreg.REG_DWORD, PUTTY_CONFIG_DEFAULT[k])

		# 写入/修改每个session的特有配置值
		winreg.SetValueEx(session_key, 'HostName',	0,	winreg.REG_SZ,		str(r['主机'])	)	# 主机地址
		winreg.SetValueEx(session_key, 'PortNumber',	0,	winreg.REG_DWORD,	r['端口']	)	# 端口
		winreg.SetValueEx(session_key, 'UserName',	0,	winreg.REG_SZ,		r['用户']	)	# 用户名
		winreg.SetValueEx(session_key, 'PublicKeyFile',	0,	winreg.REG_SZ,		ppk_file	)	# PPK文件位置
		winreg.SetValueEx(session_key, 'WinTitle',	0,	winreg.REG_SZ,		session_name	)	# 窗口标题
		winreg.SetValueEx(session_key, 'Font',		0,	winreg.REG_SZ,		font_name	)	# 字体名称
		
		winreg.CloseKey(session_key)

## 连接到远程主机，返回连接对象
def _connect_session(session_name, base=USER_SSH_BASE):
	s		= get_session_config(session_name)
	OPENSSH_file	= os.path.join(base, 'OPENSSH', f'{session_name}.key')
	ssh		= paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
	key	= paramiko.Ed25519Key.from_private_key_file(OPENSSH_file)
	ssh.connect(
		hostname	= s['HostName'],
		username	= s['UserName'],
		pkey		= key,
		port		= s['PortNumber'],
	)

	return ssh

## 使用SFTP上传文件，使用session
def upload_on_session(session_name, local_file, remote_file, base=USER_SSH_BASE):
	ssh	= _connect_session(session_name, base)
	sftp	= ssh.open_sftp()
	sftp.put(local_file, remote_file)
	sftp.close()
	ssh.close()

## 使用SFTP下载文件，使用session
def download_on_session(session_name, remote_file, local_file, base=USER_SSH_BASE):
	ssh	= _connect_session(session_name, base)
	sftp	= ssh.open_sftp()
	sftp.get(remote_file, local_file)
	sftp.close()
	ssh.close()

## 远程连接执行非交互命令，使用session，返回stdout+stderr
def execute_on_session(session_name, command, base=USER_SSH_BASE):
	ssh	= _connect_session(session_name, base)
	stdin, stdout, stderr	= ssh.exec_command(command, False)
	
	stdout_content	= stdout.read().decode(encoding='utf-8')
	stderr_content	= stderr.read().decode(encoding='utf-8')

	ssh.close()
	return stdout_content+stderr_content

if __name__ == '__main__':
	
	# 构建OneDrive文档SSH目录路径
	#me		= 'arthuryang'
	#config_xlsx	= 'a.xlsx'
	# 导入
	#import_PuTTY_config(config_xlsx, base, me, flush=True, font_name='Maple Mono NF CN')

	# 导出	
	# export_PuTTY_config(config_xlsx)

	#session_name	= 'arthuryang@PROGRAM'
	# result	= execute_on_session(session_name, 'cat .bashrc')
	# print(result)

	# download_on_session(session_name, '.bashrc', 'bashrc')
	# upload_on_session(session_name, 'bashrc', 'bashrc')

	pass