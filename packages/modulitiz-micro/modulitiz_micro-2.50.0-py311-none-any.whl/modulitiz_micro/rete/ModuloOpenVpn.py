from modulitiz_nano.sistema.ModuloSystem import ModuloSystem


class ModuloOpenVpn(object):
	def __init__(self,percorsoOpenVpn:str):
		self.__percorsoOpenVpn=percorsoOpenVpn
	
	def startVpn(self,isOpenVpnAlreadyRunning:bool,filenameOvpn:str):
		"""
		Send a command to start vpn to a new or already running instance of the GUI.
		https://community.openvpn.net/openvpn/wiki/OpenVPN-GUI-New#gui-help
		"""
		subCmd="--command connect" if isOpenVpnAlreadyRunning else "--connect"
		cmd=r'start "" "{}" {} {}.ovpn'.format(self.__percorsoOpenVpn,subCmd,filenameOvpn)
		ModuloSystem.systemCallWaitAndClose(cmd,False)
