from pypn5180.pypn5180 import PN5180
import collections
"""
Implementation of ISO-IEC-15693 norm for PN5180 chipset
"""
class iso_iec_15693(object):

    CMD_CODE= {
        'INVENTORY':0x01,
        'STAY_QUIET':0x02,
        'READ_SINGLE_BLOCK':0x20,
        'WRITE_SINGLE_BLOCK':0x21,
        'LOCK_BLOCK':0x22,
        'READ_MULTIPLE_BLOCK':0x23,
        'WRITE_MULTIPLE_BLOCK':0x24,
        'SELECT':0x25,
        'RESET_READY':0x26,
        'WRITE_AFI':0x27,
        'LOCK_AFI':0x28,
        'WRITE_DSFID':0x29,
        'LOCK_DSFID':0x2A,
        'GET_SYSTEM_INFORMATION':0x2B,
        'GET_MULTIPLE_BLOCK_SECURITY_STATUS':0x2C,
        'CUSTOM_READ_SINGLE':0xC0,
        'CUSTOM_WRITE_SINGLE':0xC1,
        'CUSTOM_LOCK_BLOCK':0xC2,
        'CUSTOM_READ_MULTIPLE':0xC3,
        'CUSTOM_WRITE_MULTIPLE':0xC4,
    }

    ERROR_CODE = {
        0x00:'ERROR CODE ZERO',
        0x01:'The command is not supported, i.e. the request code is not recognised.',
        0x02:'The command is not recognised, for example: a format error occurred.',
        0x03:'The option is not supported.',
        0x0F:'Unknown error.',
        0x10:'The specified block is not available (doesn t exist).',
        0x11:'The specified block is already -locked and thus cannot be locked again',
        0x12:'The specified block is locked and its content cannot be changed.',
        0x13:'The specified block was not successfully programmed.',
        0x14:'The specified block was not successfully locked',
        0xA7:'CUSTOM ERROR 0xA7'
    }
    ERROR_CODE = collections.defaultdict(lambda:0,ERROR_CODE)

    def __init__(self, ftdi_port = "PORT_A", logs = False):
        self.pn5180 = PN5180(debug="PN5180", ftdi_port = ftdi_port)
        if logs: 
            print("Connecting to PN5180 device...")
            print("PN5180 Self test:")
            self.pn5180.selfTest()
            print("\nConfiguring device for ISO IEC 15693")
        self.pn5180.configureIsoIec15693Mode()
        self.flags = 0x02

    def configureFlags(self, flags):
        self.flags = flags


    def getError(self, flags, data):
        if flags == 0xFF:
            return "Transaction ERROR: No Answer from tag"
        elif flags != 0:
            return "Transaction ERROR: %s" %self.ERROR_CODE[data[0]]
        return "Transaction OK"


    def readSingleBlockCmd(self, blockNumber, uid=[]):
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['READ_SINGLE_BLOCK'])
        if uid is not []:
            frame.extend(uid)
        frame.append(blockNumber)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error

    def writeSingleBlockCmd(self, blockNumber, data, uid=[]):
        #'21'
        if len(data) != 8:
            print("WARNING, data block length must be 8 bytes")
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['WRITE_SINGLE_BLOCK'])
        if uid is not []:
            frame.extend(uid)
        frame.append(blockNumber)
        frame.extend(data)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error
