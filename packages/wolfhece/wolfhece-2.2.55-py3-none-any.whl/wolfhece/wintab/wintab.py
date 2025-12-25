import logging

WT_PACKET = 0x7FF0

# Information categories
WTI_INTERFACE = 1
WTI_STATUS = 2
WTI_DEFCONTEXT = 3
WTI_DEFSYSCTX = 4
WTI_DDCTXS = 400
WTI_DSCTXS = 500
WTI_DEVICES = 100
WTI_CURSORS = 200
WTI_EXTENSIONS = 300

# Hardware capabilities
HWC_INTEGRATED = 0x0001
HWC_TOUCH = 0x0002
HWC_HARDPROX = 0x0004
HWC_PHYSID_CURSORS = 0x0008

# Unit specifiers
TU_NONE = 0
TU_INCHES = 1
TU_CENTIMETERS = 2
TU_CIRCLE = 3

# Cursor capabilities
CRC_MULTIMODE = 0x0001
CRC_AGGREGATE = 0x0002
CRC_INVERT = 0x0004

# System button assignment values
SBN_NONE = 0x00
SBN_LCLICK = 0x01
SBN_LDBLCLICK = 0x02
SBN_LDRAG = 0x03
SBN_RCLICK = 0x04
SBN_RDBLCLICK = 0x05
SBN_RDRAG = 0x06
SBN_MCLICK = 0x07
SBN_MDBLCLICK = 0x08
SBN_MDRAG = 0x09
# for Pen Windows
SBN_PTCLICK = 0x10
SBN_PTDBLCLICK = 0x20
SBN_PTDRAG = 0x30
SBN_PNCLICK = 0x40
SBN_PNDBLCLICK = 0x50
SBN_PNDRAG = 0x60
SBN_P1CLICK = 0x70
SBN_P1DBLCLICK = 0x80
SBN_P1DRAG = 0x90
SBN_P2CLICK = 0xA0
SBN_P2DBLCLICK = 0xB0
SBN_P2DRAG = 0xC0
SBN_P3CLICK = 0xD0
SBN_P3DBLCLICK = 0xE0
SBN_P3DRAG = 0xF0

# Context option values
CXO_SYSTEM = 0x0001
CXO_PEN = 0x0002
CXO_MESSAGES = 0x0004
CXO_MARGIN = 0x8000
CXO_MGNINSIDE = 0x4000
CXO_CSRMESSAGES = 0x0008

# Context status values
CXS_DISABLED = 0x0001
CXS_OBSCURED = 0x0002
CXS_ONTOP = 0x0004

# Context lock values
CXL_INSIZE = 0x0001
CXL_INASPECT = 0x0002
CXL_SENSITIVITY = 0x0004
CXL_MARGIN = 0x0008
CXL_SYSOUT = 0x0010

# WTPKT bits
PK_CONTEXT = 0x0001          # reporting context
PK_STATUS = 0x0002           # status bits
PK_TIME = 0x0004             # time stamp
PK_CHANGED = 0x0008          # change bit vector
PK_SERIAL_NUMBER = 0x0010    # packet serial number
PK_CURSOR = 0x0020           # reporting cursor
PK_BUTTONS = 0x0040          # button information
PK_X = 0x0080                # x axis
PK_Y = 0x0100                # y axis
PK_Z = 0x0200                # z axis
PK_NORMAL_PRESSURE = 0x0400  # normal or tip pressure
PK_TANGENT_PRESSURE = 0x0800 # tangential or barrel pressure
PK_ORIENTATION = 0x1000      # orientation info: tilts */
PK_ROTATION = 0x2000         # rotation info; 1.1

# Packet status values
TPS_PROXIMITY =	0x0001
TPS_QUEUE_ERR =	0x0002
TPS_MARGIN = 0x0004
TPS_GRAB = 0x0008
TPS_INVERT = 0x0010

# Relative buttons
TBN_NONE = 0
TBN_UP = 1
TBN_DOWN = 2


class Wintab():

    def __init__(self, hwnd):
        import ctypes
        from ctypes import wintypes, c_char, c_int, POINTER
        from ctypes.wintypes import HWND, UINT, DWORD, LONG, HANDLE, BOOL, LPVOID

        HCTX = HANDLE
        WTPKT = DWORD
        FIX32 = DWORD
        class LOGCONTEXTA(ctypes.Structure):
            _fields_ = [
                ('lcName', 40*c_char),
                ('lcOptions', UINT),
                ('lcStatus', UINT),
                ('lcLocks', UINT),
                ('lcMsgBase', UINT),
                ('lcDevice', UINT),
                ('lcPktRate', UINT),
                ('lcPktData', WTPKT),
                ('lcPktMode', WTPKT),
                ('lcMoveMask', WTPKT),
                ('lcBtnDnMask', DWORD),
                ('lcBtnUpMask', DWORD),
                ('lcInOrgX', LONG),
                ('lcInOrgY', LONG),
                ('lcInOrgZ', LONG),
                ('lcInExtX', LONG),
                ('lcInExtY', LONG),
                ('lcInExtZ', LONG),
                ('lcOutOrgX', LONG),
                ('lcOutOrgY', LONG),
                ('lcOutOrgZ', LONG),
                ('lcOutExtX', LONG),
                ('lcOutExtY', LONG),
                ('lcOutExtZ', LONG),
                ('lcSensX', FIX32),
                ('lcSensY', FIX32),
                ('lcSensZ', FIX32),
                ('lcSysMode', BOOL),
                ('lcSysOrgX', c_int),
                ('lcSysOrgY', c_int),
                ('lcSysExtX', c_int),
                ('lcSysExtY', c_int),
                ('lcSysSensX', FIX32),
                ('lcSysSensY', FIX32)
            ]

        # PK_CONTEXT = 		0x0001	# reporting context */
        # PK_STATUS = 			0x0002	# status bits */
        # PK_TIME = 			0x0004	# time stamp */
        # PK_CHANGED = 		0x0008	# change bit vector */
        # PK_SERIAL_NUMBER = 0x0010	# packet serial number */
        # PK_CURSOR = 			0x0020	# reporting cursor */
        # PK_BUTTONS = 		0x0040	# button information */
        # PK_X = 				0x0080	# x axis */
        # PK_Y = 				0x0100	# y axis */
        # PK_Z = 				0x0200	# z axis */
        # PK_NORMAL_PRESSURE = 0x0400	# normal or tip pressure */
        # PK_TANGENT_PRESSURE = 0x0800	# tangential or barrel pressure */
        # PK_ORIENTATION = 	0x1000	# orientation info: tilts */
        # PK_ROTATION = 		0x2000	# rotation info; 1.1 */

        lcPktData = (PK_CHANGED | PK_CURSOR | PK_BUTTONS | PK_X | PK_Y | PK_NORMAL_PRESSURE)
        lcPktMode = 0

        class PACKET(ctypes.Structure):
            _fields_ = [
                ('pkChanged', WTPKT),
                ('pkCursor', UINT),
                ('pkButtons', DWORD),
                ('pkX', LONG),
                ('pkY', LONG),
                ('pkNormalPressure', UINT)
            ]

        # WTI_DEFCONTEXT = 3

        # CXO_SYSTEM = 0x0001
        # CXO_PEN = 0x0002
        # CXO_MESSAGES = 0x0004
        # CXO_MARGIN = 0x8000

        try:
            self.dll = ctypes.WinDLL("wintab32.dll")
            self._wintab = True

            self.dll.WTInfoA.argtypes = [UINT, UINT, POINTER(LOGCONTEXTA)]
            self.dll.WTInfoA.restype = UINT

            self.dll.WTOpenA.argtypes = [HWND, POINTER(LOGCONTEXTA), BOOL]
            self.dll.WTOpenA.restype = HCTX

            self.dll.WTClose.argtypes = [HCTX]
            self.dll.WTClose.restype = BOOL

            self.dll.WTPacketsGet.argtypes = [HCTX, c_int, POINTER(PACKET)]
            self.dll.WTPacketsGet.restype = c_int

            self.dll.WTPacket.argtypes = [HCTX, UINT, POINTER(PACKET)]
            self.dll.WTPacket.restype = BOOL

            self.lc = LOGCONTEXTA()
            rslt = self.dll.WTInfoA(WTI_DEFCONTEXT, 0, self.lc)

            # logging.info(self.lc.lcOptions)
            self.lc.lcPktData = lcPktData
            self.lc.lcPktMode = lcPktMode
            self.lc.lcOptions = (CXO_SYSTEM | CXO_MESSAGES)
            # logging.info(self.lc.lcOptions)
            self.hctx = self.dll.WTOpenA(HWND(hwnd), self.lc, 1)

            self.buf = (1*PACKET)()
        except:
            self._wintab = False


    def get_xypressure(self):

        if self._wintab:
            n = self.dll.WTPacketsGet(self.hctx, 1, self.buf)
            if n > 0:
                return self.buf[0].pkX, self.buf[0].pkY, self.buf[0].pkNormalPressure
            else:
                return None, None, None
        else:
            return None, None, None


if __name__ == "__main__":

    loc = Wintab()

    while True:
        x, y, p = loc.get_xypressure()
        if x is not None:
            print(x, y, p)
        # else:
        #     print("No data")