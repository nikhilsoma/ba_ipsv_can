from enum import Enum
import itpii
itp = itpii.baseaccess()

import log_file_framework as var_log_fw
#import can_reg; reload(can_reg)
import can_reg
import sys

import sys
import ctypes
import random
import time
import math

import itpii
import pci2
import os
import threading 


#can0 = can_reg.regs()
#CAN =[can0]

global can0
global can1
global CAN
dev_bus = 0x03

#global txbuf
#txbuf = []

#global rxbuf
#rxbuf = []

'''
## =========== Python 3.6.8 New log file Test_log.txt ================== ##
import sys
sys.stdout = open('Test_log.txt',"w")
## ===================================================================== ##
'''
DID_LIST = {
   
    'PTL' : {'0':{'DID':0x67B5, 'DEV': 0x1D, 'FUNC':0},'1':{'DID':0x67B6, 'DEV': 0x1D, 'FUNC':1}},
    
}

can0 = can_reg.regs(dev_bus, DID_LIST['PTL']['0']['DEV'],DID_LIST['PTL']['0']['FUNC'])
can1 = can_reg.regs(dev_bus, DID_LIST['PTL']['1']['DEV'],DID_LIST['PTL']['1']['FUNC'])
CAN =[can0, can1]

class Define_Value(Enum):
    FUNCTIONAL_CLOCK = 10000000
    CAN_CTRLMODE_FD = 0X08
    CAN_CTRLMODE_FD_BRS = 0X10
    CAN_CTRLMODE_CLASSIC = 0X04
    CAN_CTRLMODE_LISTENONLY = 0X02
    CAN_CTRLMODE_LOOPBACK = 0X01
    XIDFC_LSE_OFF = 16
    SIDFC_LSS_OFF = 16
    TIMEOUT_LIMIT = 10000

def ReadMmio(m_bar, address, size=4):
    address_str = str(m_bar + address).replace('[32b]', '').replace('p', '')
    value = itp.threads[0].mem((address_str + "p"), size)
    #print("In Read Reg***" + hex(m_bar + address) + " data= " + str(hex(value)) + "***")
    return value

def WriteMmio(m_bar, address, data, size=4):
    print("In Write MMIO***" + str(hex(m_bar + address)) + " data= " + str(hex(data)) + "***")
    address_str = str(m_bar + address).replace('[32b]', '').replace('p', '')
    itp.threads[0].mem((address_str + "p"), size, data)
    print("**read after write**")
    #ReadMmio(m_bar , address)
    #print("After writing***" + address_str + " data= " + str(hex(data)) + "***")
    return True

def clearRAM(m_bar = 0):
    for i in range(4480):
        itp.threads[0].mem(str(m_bar + 0x800 + (i * 4)) + "p", 4, 0x0)
    #below function is for register dumps for CAN controllers
    can0.readall()
    print("**Done clearRAM**")


def can_setup(m_bar = 0, rxf0c_elements = 0, rxf1c = 0, rxf1c_elements = 0, rxbuff_elements = 0, tbds = 0, flssa = 0, lss = 0, lse = 0, flesa = 0, eidm = 0, f0sa = 0, f1sa = 0, rbsa = 0, f0ds = 0, f1ds = 0, rbds = 0, efsa = 0, efs = 0, efwm = 0,f0wm=0,f0om=0, tbsa = 0, ndtb = 0, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0, ntseg1 = 0, nbrp = 0, nsjw = 0, fsjw = 0, ftseg2 = 0, ftseg1 = 0, fbrp = 0, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0, anfe = 0, anfs = 0, tie = 0, cfie = 0, eint0 = 0, eint1 = 0, intrLine = 0):

    reg_val_32 = 0
    flssa_val = 0

    # Step: 1
    reg_val_32 = ReadMmio(m_bar, can0.CCCR.offset)
    reg_val_32 = ((reg_val_32 & 0xffffff7f) | (0x1 << 7))
    reg_val_32 = ((reg_val_32 & 0xFFFFBFFF) | (0x1 << 14)) #TXP_Pause
    
    WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)
    print(" CCCR reg_val_32 is :", reg_val_32)
    


    # Step: 2
    flssa_val = ((flssa + 0x0800) >> 0x2)
    reg_val_32 = ReadMmio(m_bar, can0.SIDFC.offset)
    reg_val_32 = ((reg_val_32 & 0xff00ffff) | (lss << 16))
    reg_val_32 = ((reg_val_32 & 0xffff0003) | (flssa_val << 2))
    WriteMmio(m_bar, can0.SIDFC.offset, reg_val_32)

    # Step: 3
    reg_val_32 = ReadMmio(m_bar, can0.XIDFC.offset)
    reg_val_32 = ((reg_val_32 & 0xffff0003) | (((flesa + 0x00800) >> 0x2) << 2))
    reg_val_32 = ((reg_val_32 & 0xff80ffff) | (lse << 16))
    WriteMmio(m_bar, can0.XIDFC.offset, reg_val_32)

    # Step: 4
    reg_val_32 = ReadMmio(m_bar, can0.XIDAM.offset)
    reg_val_32 = ((reg_val_32 & 0xe0000000) | eidm)
    WriteMmio(m_bar, can0.XIDAM.offset, reg_val_32)

    # Step: 5
    reg_val_32 = ReadMmio(m_bar, can0.RXF0C.offset)
    reg_val_32 = ((reg_val_32 & 0xffff0003) | (((f0sa + 0x00800) >> 0x2) << 2))
    reg_val_32 = ((reg_val_32 & 0xff80ffff) | (rxf0c_elements << 16)) #Harshini_Org: 0xff80ffff
    #To write RXF0C.F0WM Rx FIFO 0 Watermark   
    #reg_val_32 = ((reg_val_32 & 0x80FFFFFF) | (f0wm << 24))# f1wm = 2
    #reg_val_32 = ((reg_val_32 & 0x7FFFFFFF) | (f0om << 31))#f1om = 0
    WriteMmio(m_bar, can0.RXF0C.offset, reg_val_32)
    
   

    # Step: 6
    reg_val_32 = ReadMmio(m_bar, can0.RXF1C.offset)
    #reg_val_32 = ((reg_val_32 & 0xffff0003) | (((rxf1c + 0x00800) >> 0x2) << 2))
    reg_val_32 = ((reg_val_32 & 0xffff0003) | (((f1sa + 0x00800) >> 0x2) << 2))
    reg_val_32 = ((reg_val_32 & 0xff80ffff) | (rxf1c_elements << 16)) #Harshini_Org: 0xff80ffff
    
   #To write RXF1C.F0WM Rx FIFO 1 Watermark   
    reg_val_32 = ((reg_val_32 & 0x80FFFFFF) | (2 << 24))# f1wm = 2
    reg_val_32 = ((reg_val_32 & 0x7FFFFFFF) | (1 << 31))#f1om = 0: Blocking mode, 1 =overwrite mode
    WriteMmio(m_bar, can0.RXF1C.offset, reg_val_32)
    
    # Step: 7
    reg_val_32 = ReadMmio(m_bar, can0.RXBC.offset)
    reg_val_32 = ((reg_val_32 & 0xffff0003) | (((rbsa + 0x00800) >> 0x2) << 2))
    WriteMmio(m_bar, can0.RXBC.offset, reg_val_32)

    # Step: 8
    reg_val_32 = ReadMmio(m_bar, can0.RXESC.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffff8) | f0ds)
    reg_val_32 = ((reg_val_32 & 0xffffff8f) | (f1ds << 4))
    reg_val_32 = ((reg_val_32 & 0xfffff8ff) | (rbds << 8))
    WriteMmio(m_bar, can0.RXESC.offset, reg_val_32)

    # Step: 9
    reg_val_32 = ReadMmio(m_bar, can0.TXEFC.offset)
    reg_val_32 = ((reg_val_32 & 0xffff0003) | (((efsa + 0x00800) >> 0x2) << 2))
    reg_val_32 = ((reg_val_32 & 0xffc0ffff) | (efs << 16))
    reg_val_32 = ((reg_val_32 & 0xc0ffffff) | (efwm << 24))
    WriteMmio(m_bar, can0.TXEFC.offset, reg_val_32)

    # Step: 10
    reg_val_32 = ReadMmio(m_bar, can0.TXBC.offset)
    reg_val_32 = ((reg_val_32 & 0xffff0003) | (((tbsa + 0x00800) >> 0x2) << 2))
    reg_val_32 = ((reg_val_32 & 0xffc0ffff) | (ndtb << 16))
    reg_val_32 = ((reg_val_32 & 0xc0ffffff) | (tbqs << 24))
    reg_val_32 = ((reg_val_32 & 0xbfffffff) | (tbqm << 30))
    WriteMmio(m_bar, can0.TXBC.offset, reg_val_32)

    # Step: 11
    reg_val_32 = ReadMmio(m_bar, can0.TXESC.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffff8) | tbds)
    WriteMmio(m_bar, can0.TXESC.offset, reg_val_32)

    # Step: 12
    #clearRAM(m_bar)

    # Step: 13
    reg_val_32 = ReadMmio(m_bar, can0.CCCR.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffeff) | (fdoe << 8))
    reg_val_32 = ((reg_val_32 & 0xfffffdff) | (brse << 9))
    WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)

    # Step: 14
    reg_val_32 = ReadMmio(m_bar, can0.NBTP.offset)
    reg_val_32 = ((reg_val_32 & 0xffffff80) | ntseg2)
    reg_val_32 = ((reg_val_32 & 0xffff80ff) | (ntseg1 << 8))
    reg_val_32 = ((reg_val_32 & 0xfe00ffff) | (nbrp << 16))
    reg_val_32 = ((reg_val_32 & 0x01ffffff) | (nsjw << 25))
    WriteMmio(m_bar, can0.NBTP.offset, reg_val_32)

    # Step: 15
    reg_val_32 = ReadMmio(m_bar, can0.DBTP.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffff0) | fsjw)
    reg_val_32 = ((reg_val_32 & 0xffffff0f) | (ftseg2 << 4))
    reg_val_32 = ((reg_val_32 & 0xffffe0ff) | (ftseg1 << 8))
    reg_val_32 = ((reg_val_32 & 0xffe0ffff) | (fbrp << 16))
    reg_val_32 = ((reg_val_32 & 0xff7fffff) | (tdc << 23))
    WriteMmio(m_bar, can0.DBTP.offset, reg_val_32)

    # Step: 16
    reg_val_32 = ReadMmio(m_bar, can0.TDCR.offset)
    reg_val_32 = ((reg_val_32 & 0xffffff80) | tdcf)
    reg_val_32 = ((reg_val_32 & 0xffff80ff) | (tdco << 8))
    WriteMmio(m_bar, can0.TDCR.offset, reg_val_32)

    # Step: 17
    reg_val_32 = ReadMmio(m_bar, can0.GFC.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffe) | rrfe)
    reg_val_32 = ((reg_val_32 & 0xfffffffd) | (rrfs << 1))
    reg_val_32 = ((reg_val_32 & 0xfffffff3) | (anfe << 2))
    reg_val_32 = ((reg_val_32 & 0xffffffcf) | (anfs << 4))
    WriteMmio(m_bar, can0.GFC.offset, reg_val_32)

    # Step: 18
    reg_val_32 = ReadMmio(m_bar, can0.TXBTIE.offset)
    reg_val_32 = ((reg_val_32 & 0x00000000) | tie)
    WriteMmio(m_bar, can0.TXBTIE.offset, reg_val_32)

    # Step: 19
    reg_val_32 = ReadMmio(m_bar, can0.TXBCIE.offset)
    reg_val_32 = ((reg_val_32 & 0x00000000) | cfie)
    WriteMmio(m_bar, can0.TXBCIE.offset, reg_val_32)

    # Step: 20
    WriteMmio(m_bar, can0.IR.offset, 0xffffffff)

    # Step: 21
    WriteMmio(m_bar, can0.IE.offset, 0xffffffff)

    # Step: 22
    if ((intrLine == 0x00000000) or (intrLine == 0x00000001)):
        reg_val_32 = ReadMmio(m_bar, can0.ILE.offset)
        if (intrLine == 0x00000000):
            reg_val_32 = ((reg_val_32 & 0xfffffffe) | eint0)
        elif (intrLine == 0x00000001):
            reg_val_32 = ((reg_val_32 & 0xfffffffd) | (eint1 << 1))
        WriteMmio(m_bar, can0.ILE.offset, reg_val_32)
    #can0.readall()
    
    #Step:23 Parity enabled/disabled,to set one time and continuous error injection and its status
    reg_val_32 = ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#PARITY_EN = 0 to disable
    WriteMmio(m_bar, can0.PAR_CTL_STAT.offset, reg_val_32)
 

    
 
    
    print("done can setup")
    


def clearRAM_control(m_bar = 0, clearRAM_enable = 0):

    # Step: t0
    if (clearRAM_enable == 0x1):
        clearRAM(m_bar)


def loopback_control(m_bar = 0, internal_loopback = 0, loopback_enable = 0):

    reg_val_32 = 0

    # Step: _default
    if ((loopback_enable == 0x0) or (loopback_enable == 0x1)):
        reg_val_32 = ReadMmio(m_bar, can0.TEST.offset)
        if (loopback_enable == 0x0):
            reg_val_32 = ((reg_val_32 & 0xffffffef) | (0x0 << 4))
        elif (loopback_enable == 0x1):
            reg_val_32 = ((reg_val_32 & 0xffffffef) | (0x1 << 4))
        WriteMmio(m_bar, can0.TEST.offset, reg_val_32)
        if ((loopback_enable == 0x1) and ((internal_loopback == 0x0) or (internal_loopback == 0x1))):
            reg_val_32 = ReadMmio(m_bar, can0.CCCR.offset)
            if (internal_loopback == 0x0):
                reg_val_32 = ((reg_val_32 & 0xffffffdf) | (0x0 << 5))
            elif (internal_loopback == 0x1):
                reg_val_32 = ((reg_val_32 & 0xffffffdf) | (0x1 << 5))
            WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)
            
    print("**Done loopback**")


def retransmission_control(m_bar = 0, retransmission_disable = 0):

    reg_val_32 = 0

    # Step: _default
    if ((retransmission_disable == 0x0) or (retransmission_disable == 0x1)):
        reg_val_32 = ReadMmio(m_bar, can0.CCCR.offset)
        if (retransmission_disable == 0x0):
            reg_val_32 = ((reg_val_32 & 0xffffffbf) | (0x0 << 6))
        elif (retransmission_disable == 0x1):
            reg_val_32 = ((reg_val_32 & 0xffffffbf) | (0x1 << 6))
        WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)
        
    print("**Done retransmission_control**")

def getNumBytes(dlc = 0):

    ret = 0

    # Step: _default
    if (dlc <= 0x8):
        return dlc
    elif dlc<13:
        ret = (((dlc - 0x08) * 0x04) + 0x08) #9=12B, 10=16B, 11=20B, 12=24B, 13=32B, 14=48B, 15=64B
        print("the dlc is:",ret)
    #ret = (((dlc - 0x08) * 0x08) + 0x08) #9=12B, 10=16B, 11=20B, 12=24B, 13=32B, 14=48B, 15=64B
    elif dlc == 13:
        ret = 32
    elif dlc == 14:
        ret = 48
    elif dlc == 15:
        ret = 64
    else :
        print("Not a valid dlc")
    #not correct formula as per requirement #9=12B, 10=16B, 11=20B, 12=24B, 13=32B, 14=48B, 15=64B
    #ret = (((dlc - 0x09) * 0x04) + 0x08)
    return ret


def createTxPacket(can_id = 0, rtr = 0, xtd = 0, esi = 0, mm = 0, dlc = 0, brs = 0, fdf = 0, tsce = 0, efc = 0, txbuf = 0, tx_data = 0, pos = 0):

    can_id1 = 0
    t0 = 0
    t1 = 0
    num_bytes = 0
    txbuf = []
    #if pos >= 1:
        #txbuf = []

    # Step: 1
    if ((fdf == 0x0) and (xtd == 0x0)):
        can_id1 = (can_id << 0x12)    
    elif ((fdf == 0x0) and (xtd == 0x1)):
        can_id1 = can_id
    elif ((fdf == 0x1) and (xtd == 0x0)):
        can_id1 = (can_id << 0x12)
    elif ((fdf == 0x1) and (xtd == 0x1)):
        can_id1 = can_id   
    print("can_id1", can_id1)
    
    t0 = ((((esi << 0x1f) | (xtd << 0x1e)) | (rtr << 0x1d)) | can_id1)
    #t1 = ((((((((mm & 0xff) << 0x18) | (efc << 0x17)) | (tsce << 0x16)) | (fdf << 0x15)) | (brs << 0x14)) | (dlc << 0x10)) | 0x00000000)
    t1 = ((mm & 0xFF) <<24) | (efc<<23) | (tsce<<22) | (fdf<<21) | (brs<<20) | (dlc << 16) | ((mm>>8 & 0xFF)<<8)
    num_bytes = getNumBytes(dlc)
    print("num_bytes",num_bytes)
######################################################
    #append tx
    num_dword = num_bytes//4
    num_remain = num_bytes%4
    
    txbuf.append(t0)
    txbuf.append(t1)

    for idx in range(num_dword):
        offset = idx * 4
        #data =tx_data[offset+3] << 12 | tx_data[offset+2] << 8 | tx_data[offset+1] << 4 | tx_data[offset]
        data =tx_data[offset+3] << 24 | tx_data[offset+2] << 16 | tx_data[offset+1] << 8 | tx_data[offset]
        print("in for loop",data)
        txbuf.append(data)
    data = 0
    offset = num_dword*4
    print("this is offset",offset)
    if num_remain:
        for idx in range(num_remain):
            #offset = num_bytes
            #data = (data << 4) | tx_data[idx + offset]
            data = data | (tx_data[idx + offset])<<(idx*8)
        txbuf.append(data)
######################################################
    # Step: 2
    
    for idx in range(len(txbuf)):
        print("createTxPacket: index "+ str(idx) + ": " + hex(txbuf[idx]))
    print("createTxPacket() - end")
    return txbuf


def create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0):

    ret = 0

    # Step: _default
    ret = (((((sft << 0x1e) | (sfec << 0x1b)) | (sfid1 << 0x10)) | (ssync << 0xf)) | sfid2)
    return ret


def create29bitFilter(eft = 0, efec = 0, efid1 = 0, esync = 0, efid2 = 0):

    f0 = 0
    f1 = 0
    filt_val = []

    # Step: _default
    f0 = ((efec << 0x1d) | efid1)
    f1 = (((eft << 0x1e) | (esync << 0x1d)) | efid2)
    # ret = (f1 << 0x20) + f0
    #Harsnini
    filt_val.append(f0)
    filt_val.append(f1)
        
    for idx in range(len(filt_val)):
        print("create29bitFilter: index "+ str(idx) + ": " + hex(filt_val[idx]))
    print("create29bitFilter() - end")
    
    
    return filt_val

def GetTxBufferOffset(m_bar = 0, pos = 0):

    reg_val_32 = 0
    tbsa = 0
    tbds = 0
    tx_size = 0
    address = 0
    txbar = 0
    buffer_element_enable = 0
    count = 0
    _PollCount = 0
    _pvar = 0

    # Step: 1
    reg_val_32 = ReadMmio(m_bar, can0.TXBC.offset)
    tbsa = ((reg_val_32 & 0x0000fffc) >> 2)
    #tbsa = 10c0
    reg_val_32 = ReadMmio(m_bar, can0.TXESC.offset)
    tbds = (reg_val_32 & 0x00000007)
    if (tbds <= 0x4):
        tx_size = (0x08 + (0x04 * tbds))
    if (tbds == 0x5):
        tx_size = 0x20
    elif (tbds == 0x6):
        tx_size = 0x30
    elif (tbds == 0x7):
        tx_size = 0x40
    #address = ((tbsa << 0x2) + (pos * tx_size))
    address = ((tbsa << 0x2) + (pos * (8+tx_size))) #4310 #4348
    print("address",address)
    
        
######################################################
    #for i in range(len(txbuf)):
    #    WriteMmio(m_bar, address+(i*4),txbuf[i])
    return address
######################################################


def pushTxPacketRam(m_bar = 0, pos = 0, txbuf = 0):

    reg_val_32 = 0
    tbsa = 0
    tbds = 0
    tx_size = 0
    address = 0
    txbar = 0
    buffer_element_enable = 0
    count = 0
    _PollCount = 0
    _pvar = 0

    # Step: 1
    reg_val_32 = ReadMmio(m_bar, can0.TXBC.offset)
    tbsa = ((reg_val_32 & 0x0000fffc) >> 2)
    #tbsa = 10c0
    reg_val_32 = ReadMmio(m_bar, can0.TXESC.offset)
    tbds = (reg_val_32 & 0x00000007)
    if (tbds <= 0x4):
        tx_size = (0x08 + (0x04 * tbds))
    if (tbds == 0x5):
        tx_size = 0x20
    elif (tbds == 0x6):
        tx_size = 0x30
    elif (tbds == 0x7):
        tx_size = 0x40
    #address = ((tbsa << 0x2) + (pos * tx_size))
    address = ((tbsa << 0x2) + (pos * (8+tx_size))) #4310 #4348
    print("address",address)
    
        
######################################################
    for i in range(len(txbuf)):
        WriteMmio(m_bar, address+(i*4),txbuf[i])
######################################################

def pushTxPacketTxbar(m_bar = 0, pos = 0):

    reg_val_32 = 0
    txbar = 0
    buffer_element_enable = 0
    count = 0
    _PollCount = 0
    _pvar = 0
    transmission_completed = 0

    # Step: 1
    
    reg_val_32 = ReadMmio(m_bar, can0.TXBAR.offset)
    txbar = (reg_val_32 & 0xffffffff)
    buffer_element_enable = (txbar | (0x1 << pos)) #Harshini_Org: 0x1
    reg_val_32 = ((reg_val_32 & 0x00000000) | buffer_element_enable)
    WriteMmio(m_bar, can0.TXBAR.offset, reg_val_32)
    
    
    reg_val_32 = ReadMmio(m_bar, can0.TXBAR.offset)
    
    '''
    reg_val_32 = ReadMmio(m_bar, can0.TXBAR.offset)
    reg_val_32 = ((reg_val_32 & 0xffffffe) | 1) #txbuf0,1 bit
    WriteMmio(m_bar, can0.TXBAR.offset, reg_val_32)
    reg_val_32 = ReadMmio(m_bar, can0.TXBAR.offset)
    '''
    # Step: 2
    count = 0x1e
    can1_bar = 0x50418000
    while True:
        _tmp = ReadMmio(m_bar, can0.IR.offset)
        _pvar = ((_tmp & 0x00000200) >> 9)
        _PollCount += 1
        if (_PollCount >= 30):  # check max count
            print ("ERROR | Hit Maximum count:30 (IR == BitVector<1>")
            break
        if (_pvar == 0x1):
            break
    reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
    transmission_completed = ((reg_val_32 & 0x00000200) >> 9)
    '''
    if (transmission_completed == 0x1):
        //handcoded reg_val_32 = 0
        reg_val_32 = 0
        reg_val_32 = ((reg_val_32 & 0xfffffdff) | (0x1 << 9))
        WriteMmio(m_bar, can0.IR.offset, reg_val_32)
    '''


def push11BitFilter(m_bar = 0, pos = 0, filt = 0):

    reg_val_32 = 0
    flssa = 0
    address = 0
    can1_bar = 0x50418000

    # Step: _default
    reg_val_32 = ReadMmio(m_bar, can0.SIDFC.offset)
    print("reg_val_32",reg_val_32)
    flssa = ((reg_val_32 & 0x0000fffc) >> 2)
    print("flssa",flssa)
    address = ((flssa << 0x2) + (pos * 0x000000004))
    print("address",address)
    WriteMmio(m_bar, address, filt)



def get11BitFilter(m_bar = 0, pos = 0):

    reg_val_32 = 0
    flssa = 0
    address = 0
    can1_bar = 0x50418000

    # Step: _default
    reg_val_32 = ReadMmio(m_bar, can0.SIDFC.offset)
    print("reg_val_32",reg_val_32)
    flssa = ((reg_val_32 & 0x0000fffc) >> 2)
    print("flssa",flssa)
    address = ((flssa << 0x2) + (pos * 0x000000004))
    print("address",address)
    data = ReadMmio(m_bar, address)
    print("data",data)
    return data



def push29BitFilter(m_bar = 0, pos = 0, filt = 0):

    reg_val_32 = 0
    flesa = 0
    address = 0

    # Step: _default
    reg_val_32 = ReadMmio(m_bar, can0.XIDFC.offset)
    flesa = ((reg_val_32 & 0x0000fffc) >> 2)
    #address = ((flesa << 0x2) + (pos * 0x000000004))
    address = ((flesa << 0x2) + (pos * (0x000000008)))
    print("address",address)
    #Harshini
    #WriteMmio(m_bar, address, filt)
    for i in range(len(filt)):
        WriteMmio(m_bar, address+(i*4),filt[i])
    
    print("completed 29 bit filter")
"""    
def PollIR(m_bar=0,IR_bit_pos = 0):

    reg_val_32 = 0
    PollCount=0
    tmp=0
    pvar=0
	


    while True:
        tmp = ReadMmio(m_bar, can0.IR.offset)
        pvar = ((tmp & (0x1 << IR_bit_pos)) >> IR_bit_pos)
        PollCount += 1
        if (PollCount >= 30):
            print ("ERROR | Hit Maximum count:30 (IR == BitVector<1>")
            break
        if (pvar == 0x1):
		    break
    reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
    print ("PollIR: IR reg_val_32", reg_val_32)
    IR_value = ((reg_val_32 & (0x1 << IR_bit_pos)) >> IR_bit_pos)
    print ("PollIR: IR_value", IR_value)
    #return IR_value
    

"""
def can_end_communication(m_bar = 0):

    reg_val_32 = 0

    # Step: 1
    reg_val_32 = ReadMmio(m_bar, can0.CCCR.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffe) | 0x1)
    WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)

    # Step: 2
    reg_val_32 = ReadMmio(m_bar, can0.CCCR.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffd) | (0x1 << 1))
    WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)


def can_start_communication(m_bar = 0):

    reg_val_32 = 0

    # Step: _default
    reg_val_32 = ReadMmio(m_bar, can0.CCCR.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffe) | 0x0)
    reg_val_32 = ((reg_val_32 & 0xfffffffd) | (0x0 << 1))
    WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)


def verify_rx_tranceiver_canX_to_canY(Tx_can_bar = 0, Rx_can_bar=0, sfec = 0, pkt_cnt = 0, txbuf = 0, pos = 0):

    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    reg_val_32 = 0
    tbsa = 0
    tbds = 0
    tx_size = 0
    tbsa_val = 0
    efsa = 0
    effl = 0
    efpi = 0
    efgi = 0
    f0sa = 0
    f0ds = 0
    reg_cached = 0
    f0fl = 0
    f0gi = 0
    f0pi = 0
    ir_rf0n = 0
    fx_size = 0
    address = 0
    f1sa = 0
    f1ds = 0
    f1fl = 0
    f1gi = 0
    f1pi = 0
    ir_rf1n = 0
    rbsa = 0
    ndat1 = 0
    ndat2 = 0
    rbds = 0
    rx_size = 0
    
    print("verify rx start")
    # Step: 1
    reg_val_32 = ReadMmio(Tx_can_bar, can0.TXBC.offset)
    tbsa = ((reg_val_32 & 0x0000fffc) >> 2)
    print("tbsa :",tbsa)
    # Step: 2
    reg_val_32 = ReadMmio(Tx_can_bar, can0.TXESC.offset)
    tbds = (reg_val_32 & 0x00000007)
    if (tbds <= 0x4):
        tx_size = 0x08
    if (tbds == 0x5):
        tx_size = 0x20
    elif (tbds == 0x6):
        tx_size = 0x30
    elif (tbds == 0x7):
        tx_size = 0x40
    tbsa_val = (tbsa + (pos * 0x010))
    print("start address of tx buffer",tbsa_val)

    # Step: 3
    reg_val_32 = ReadMmio(Tx_can_bar, can0.TXEFC.offset)
    efsa = ((reg_val_32 & 0x0000fffc) >> 2)
    print("start address of tx event",efsa)
    reg_val_32 = ReadMmio(Tx_can_bar, can0.TXEFS.offset)
    effl = (reg_val_32 & 0x0000003f)
    print("Number of elements in tx event fifo",efsa)
    efpi = ((reg_val_32 & 0x001f0000) >> 16)
    print("Get index in tx event fifo",efpi)
    efgi = ((reg_val_32 & 0x00001f00) >> 8)
    print("Get index in tx event fifo",efgi)
    # Step: 4
    reg_val_32 = ReadMmio(Tx_can_bar, can0.TXEFA.offset)
    reg_val_32 = ((reg_val_32 & 0xffffffe0) | efgi)
    WriteMmio(Tx_can_bar, can0.TXEFA.offset, reg_val_32)

    # Step: 5
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF0C.offset)
        f0sa = ((reg_val_32 & 0x0000fffc) >> 2)
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXESC.offset)
        f0ds = (reg_val_32 & 0x00000007)
    reg_cached = 0x0
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF0S.offset)
        reg_cached = 0x1
        f0fl = (reg_val_32 & 0x0000007f)
        print("f0fl: ",f0fl)
        if (not reg_cached):
            reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF0S.offset)
            reg_cached = 0x1
        f0gi = ((reg_val_32 & 0x00003f00) >> 8)
        print("f0gi: ",f0gi)
        if (not reg_cached):
            reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF0S.offset)
        f0pi = ((reg_val_32 & 0x003f0000) >> 16)
        print("f0pi: ",f0pi)
    
    reg_val_32 = 0
    # Step: 6
    if (f0gi == 0x00 & sfec == 1):
        reg_val_32 = ReadMmio(Rx_can_bar, can1.IR.offset)
        ir_rf0n = (reg_val_32 & 0x00000001)
        print("IR TC bit status",ir_rf0n)
        if (ir_rf0n != 0x1):
            print("No new message in fifo '0'")
            return -0x1

    # Step: 7
    if (sfec == 0x00000001):
        if (f0ds <= 0x4):
            fx_size = 0x08
        if (f0ds == 0x5):
            fx_size = 0x20
        elif (f0ds == 0x6):
            fx_size = 0x30
        elif (f0ds == 0x7):
            fx_size = 0x40
        address = (f0sa + (f0gi * 0x010))
        print("address of fifo 0 is :",address)

    # Step: 8
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF1C.offset)
        f1sa = ((reg_val_32 & 0x0000fffc) >> 2)
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXESC.offset)
        f1ds = ((reg_val_32 & 0x00000070) >> 4)
    reg_cached = 0x0
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF1S.offset)
        reg_cached = 0x1
        f1fl = (reg_val_32 & 0x0000007f)
        print("f1fl : ",f1fl)
        if (not reg_cached):
            reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF1S.offset)
            reg_cached = 0x1
        f1gi = ((reg_val_32 & 0x00003f00) >> 8)
        print("f1gi : ",f1gi)
        if (not reg_cached):
            reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF1S.offset)
        f1pi = ((reg_val_32 & 0x003f0000) >> 16)
        print("f1pi : ",f1pi)

    # Step: 9
    if (f1gi == 0x00 & sfec == 2):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.IR.offset)
        ir_rf1n = ((reg_val_32 & 0x00000010) >> 4)
        print("IR TC bit status",ir_rf1n)
        if (ir_rf1n != 0x1):
            print("No new message in fifo '1'")
            return -0x1

    # Step: 10
    if (sfec == 0x00000002):
        if (f1ds <= 0x4):
            fx_size = 0x08
        if (f1ds == 0x5):
            fx_size = 0x20
        elif (f1ds == 0x6):
            fx_size = 0x30
        elif (f1ds == 0x7):
            fx_size = 0x40
        address = (f1sa + (f1gi * 0x010))
        print("address of fifo 1 : ",address)

    # Step: 11
    if ((sfec == 0x00000001) and (f0fl < pkt_cnt)):
        return -0x1

    # Step: 12
    if ((sfec == 0x00000002) and (f1fl < pkt_cnt)):
        return -0x1

    # Step: 13
    if (sfec == 0x00000007):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXBC.offset)
        rbsa = ((reg_val_32 & 0x0000fffc) >> 2)
        reg_val_32 = ReadMmio(Rx_can_bar, can0.NDAT1.offset)
        ndat1 = (reg_val_32 & 0xffffffff)
        print("ndat1 : ",ndat1)
        reg_val_32 = ReadMmio(Rx_can_bar, can0.NDAT2.offset)
        ndat2 = (reg_val_32 & 0xffffffff)
        print("ndat2 : ",ndat2)
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXESC.offset)
        rbds = ((reg_val_32 & 0x00000700) >> 8)

    # Step: 14
    if (sfec == 0x00000007):
        if (rbds <= 0x4):
            rx_size = 0x08
        if (rbds <= 0x5):
            rx_size = 0x20
        if (rbds <= 0x6):
            rx_size = 0x30
        if (rbds <= 0x7):
            rx_size = 0x40
        address = ((rbsa << 0x2) + (pos * 0x010))
        print("address of fifo 1 : ",address)

    # Step: 15
    if (ndat1 >= 0x00000001):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.NDAT1.offset)
        reg_val_32 = ((reg_val_32 & 0x00000000) | 0x00000001)
        WriteMmio(Rx_can_bar, can0.NDAT1.offset, reg_val_32)

    # Step: 16
    if (ndat2 >= 0x00000001):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.NDAT2.offset)
        reg_val_32 = ((reg_val_32 & 0x00000000) | 0x00000001)
        WriteMmio(Rx_can_bar, can0.NDAT2.offset, reg_val_32)

    # Step: 17
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF0A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f0gi)
        WriteMmio(Rx_can_bar, can0.RXF0A.offset, reg_val_32)

    # Step: 18
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF1A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f1gi)
        WriteMmio(Rx_can_bar, can0.RXF1A.offset, reg_val_32)

    # Step: 19
    if (ir_rf0n == 0x1):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.IR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffe) | 0x1)
        WriteMmio(Rx_can_bar, can0.IR.offset, reg_val_32)

    # Step: 20
    if (ir_rf1n == 0x1):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.IR.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffef) | (0x1 << 4))
        WriteMmio(Rx_can_bar, can0.IR.offset, reg_val_32)
        
    ######################################################
    #append to rxbuf
    rxbuf = []
    print("RxBuffer:")
    for idx in range(len(txbuf)):
        rxVal = ReadMmio(Tx_can_bar, address)
        txVal = ReadMmio(Tx_can_bar, tbsa + (idx * 4))
        print(str(idx) + ": Tx(" + hex(txVal) + ") Rx("+ str(rxVal) + ")")
        rxbuf.append(ReadMmio(Rx_can_bar, address))
        address = address + 4
    
    	# Step: 6
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF0A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f0gi)
        WriteMmio(Rx_can_bar, can0.RXF0A.offset, reg_val_32)
    
    # Step: 7
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(Rx_can_bar, can0.RXF1A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f1gi)
        WriteMmio(Rx_can_bar, can0.RXF1A.offset, reg_val_32)
    
    
    
    #compare txbuf to rxbuf
    
    if len(txbuf) != len(rxbuf):
        print("ERROR: TxBuf num dwords (" + str(len(txbuf)) + ") does not match RxBuf num dwords (" + str(len(rxbuf)) + ")")
        #return -1
        
    if len(txbuf) == 0:
        print("ERROR: Tx/Rx buffer size is zero")
        #return -1
    #if it is 11 bit identifier ignore 0-17 bits
    mask = 0xFFFFF0000
    mask_buff_1 = 0x1F0000
    #mask = 0xFFFFF0000
    
    # Iterate over both buffers and compare the pattern in each element
    for i in range(len(txbuf)):
        if txbuf[i] != rxbuf[i]:
            if i == 0 : 
                if (txbuf[i] & mask) != (rxbuf[i] & mask):
                    print("Pattern mismatch at index %d: TX=0x%08X, RX=0x%08X" % (i, txbuf[i], rxbuf[i]))
                    #return -1
                else:
                    print("Pattern match at index %d: TX=0x%08X, RX=0x%08X" % (i, (txbuf[i] & mask), (rxbuf[i] & mask)))
            elif i == 1:
              if (txbuf[i] & mask_buff_1) != (rxbuf[i] & mask_buff_1):
                  print("Pattern mismatch at index %d: TX=0x%08X, RX=0x%08X" % (i, txbuf[i], rxbuf[i]))
                  #return -1
              else:
                  print("Pattern match at index %d: TX=0x%08X, RX=0x%08X" % (i, (txbuf[i] & mask_buff_1), (rxbuf[i] & mask_buff_1)))
        else:
            print("Pattern match at index %d: TX=0x%08X, RX=0x%08X" % (i, txbuf[i], rxbuf[i]))
    
    '''
    for idx in range(len(txbuf)):
        if idx == 0 :
            
        if txbuf[idx] != rxbuf[idx]:
            print(" ERROR | Data Mismatch")
            return -1
    print("Data Match")
    return 1
    '''
        
    ######################################################
    

def verify_rx_tranceiver(m_bar = 0, sfec = 0, pkt_cnt = 0, txbuf = 0,pos = 0):

    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    reg_val_32 = 0
    tbsa = 0
    tbds = 0
    tx_size = 0
    tbsa_val = 0
    efsa = 0
    effl = 0
    efpi = 0
    efgi = 0
    f0sa = 0
    f0ds = 0
    reg_cached = 0
    f0fl = 0
    f0gi = 0
    f0pi = 0
    ir_rf0n = 0
    fx_size = 0
    address = 0
    f1sa = 0
    f1ds = 0
    f1fl = 0
    f1gi = 0
    f1pi = 0
    ir_rf1n = 0
    rbsa = 0
    ndat1 = 0
    ndat2 = 0
    rbds = 0
    rx_size = 0
    
    print("verify rx start")
    # Step: 1
    reg_val_32 = ReadMmio(can0_bar, can0.TXBC.offset)
    tbsa = ((reg_val_32 & 0x0000fffc) >> 2)
    print("tbsa :",tbsa)
    # Step: 2
    reg_val_32 = ReadMmio(can0_bar, can0.TXESC.offset)
    tbds = (reg_val_32 & 0x00000007)
    if (tbds <= 0x4):
        tx_size = 0x08
    if (tbds == 0x5):
        tx_size = 0x20
    elif (tbds == 0x6):
        tx_size = 0x30
    elif (tbds == 0x7):
        tx_size = 0x40
    tbsa_val = (tbsa + (pos * 0x010))
    print("start address of tx buffer",tbsa_val)

    # Step: 3
    reg_val_32 = ReadMmio(can1_bar, can0.TXEFC.offset)
    efsa = ((reg_val_32 & 0x0000fffc) >> 2)
    print("start address of tx event",efsa)
    reg_val_32 = ReadMmio(can1_bar, can0.TXEFS.offset)
    effl = (reg_val_32 & 0x0000003f)
    print("Number of elements in tx event fifo",efsa)
    efpi = ((reg_val_32 & 0x001f0000) >> 16)
    print("Get index in tx event fifo",efpi)
    efgi = ((reg_val_32 & 0x00001f00) >> 8)
    print("Get index in tx event fifo",efgi)
    # Step: 4
    reg_val_32 = ReadMmio(m_bar, can0.TXEFA.offset)
    reg_val_32 = ((reg_val_32 & 0xffffffe0) | efgi)
    WriteMmio(m_bar, can0.TXEFA.offset, reg_val_32)

    # Step: 5
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0C.offset)
        f0sa = ((reg_val_32 & 0x0000fffc) >> 2)
        reg_val_32 = ReadMmio(m_bar, can0.RXESC.offset)
        f0ds = (reg_val_32 & 0x00000007)
    reg_cached = 0x0
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0S.offset)
        reg_cached = 0x1
        f0fl = (reg_val_32 & 0x0000007f)
        print("f0fl: ",f0fl)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF0S.offset)
            reg_cached = 0x1
        f0gi = ((reg_val_32 & 0x00003f00) >> 8)
        print("f0gi: ",f0gi)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF0S.offset)
        f0pi = ((reg_val_32 & 0x003f0000) >> 16)
        print("f0pi: ",f0pi)
    
    reg_val_32 = 0
    # Step: 6
    if (f0gi == 0x00 & sfec == 1):
        reg_val_32 = ReadMmio(m_bar, can1.IR.offset)
        ir_rf0n = (reg_val_32 & 0x00000001)
        print("IR TC bit status",ir_rf0n)
        if (ir_rf0n != 0x1):
            print("No new message in fifo '0'")
            return -0x1

    # Step: 7
    if (sfec == 0x00000001):
        if (f0ds <= 0x4):
            fx_size = 0x08
        if (f0ds == 0x5):
            fx_size = 0x20
        elif (f0ds == 0x6):
            fx_size = 0x30
        elif (f0ds == 0x7):
            fx_size = 0x40
        address = (f0sa + (f0gi * 0x010))
        print("address of fifo 0 is :",address)

    # Step: 8
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1C.offset)
        f1sa = ((reg_val_32 & 0x0000fffc) >> 2)
        reg_val_32 = ReadMmio(m_bar, can0.RXESC.offset)
        f1ds = ((reg_val_32 & 0x00000070) >> 4)
    reg_cached = 0x0
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1S.offset)
        reg_cached = 0x1
        f1fl = (reg_val_32 & 0x0000007f)
        print("f1fl : ",f1fl)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF1S.offset)
            reg_cached = 0x1
        f1gi = ((reg_val_32 & 0x00003f00) >> 8)
        print("f1gi : ",f1gi)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF1S.offset)
        f1pi = ((reg_val_32 & 0x003f0000) >> 16)
        print("f1pi : ",f1pi)

    # Step: 9
    if (f1gi == 0x00 & sfec == 2):
        reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        ir_rf1n = ((reg_val_32 & 0x00000010) >> 4)
        print("IR TC bit status",ir_rf1n)
        if (ir_rf1n != 0x1):
            print("No new message in fifo '1'")
            return -0x1

    # Step: 10
    if (sfec == 0x00000002):
        if (f1ds <= 0x4):
            fx_size = 0x08
        if (f1ds == 0x5):
            fx_size = 0x20
        elif (f1ds == 0x6):
            fx_size = 0x30
        elif (f1ds == 0x7):
            fx_size = 0x40
        address = (f1sa + (f1gi * 0x010))
        print("address of fifo 1 : ",address)

    # Step: 11
    if ((sfec == 0x00000001) and (f0fl < pkt_cnt)):
        return -0x1

    # Step: 12
    if ((sfec == 0x00000002) and (f1fl < pkt_cnt)):
        return -0x1

    # Step: 13
    if (sfec == 0x00000007):
        reg_val_32 = ReadMmio(m_bar, can0.RXBC.offset)
        rbsa = ((reg_val_32 & 0x0000fffc) >> 2)
        reg_val_32 = ReadMmio(m_bar, can0.NDAT1.offset)
        ndat1 = (reg_val_32 & 0xffffffff)
        print("ndat1 : ",ndat1)
        reg_val_32 = ReadMmio(m_bar, can0.NDAT2.offset)
        ndat2 = (reg_val_32 & 0xffffffff)
        print("ndat2 : ",ndat2)
        reg_val_32 = ReadMmio(m_bar, can0.RXESC.offset)
        rbds = ((reg_val_32 & 0x00000700) >> 8)

    # Step: 14
    if (sfec == 0x00000007):
        if (rbds <= 0x4):
            rx_size = 0x08
        if (rbds <= 0x5):
            rx_size = 0x20
        if (rbds <= 0x6):
            rx_size = 0x30
        if (rbds <= 0x7):
            rx_size = 0x40
        address = ((rbsa << 0x2) + (pos * 0x010))
        print("address of fifo 1 : ",address)

    # Step: 15
    if (ndat1 >= 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.NDAT1.offset)
        reg_val_32 = ((reg_val_32 & 0x00000000) | 0x00000001)
        WriteMmio(m_bar, can0.NDAT1.offset, reg_val_32)

    # Step: 16
    if (ndat2 >= 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.NDAT2.offset)
        reg_val_32 = ((reg_val_32 & 0x00000000) | 0x00000001)
        WriteMmio(m_bar, can0.NDAT2.offset, reg_val_32)

    # Step: 17
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f0gi)
        WriteMmio(m_bar, can0.RXF0A.offset, reg_val_32)

    # Step: 18
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f1gi)
        WriteMmio(m_bar, can0.RXF1A.offset, reg_val_32)

    # Step: 19
    if (ir_rf0n == 0x1):
        reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffe) | 0x1)
        WriteMmio(m_bar, can0.IR.offset, reg_val_32)

    # Step: 20
    if (ir_rf1n == 0x1):
        reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffef) | (0x1 << 4))
        WriteMmio(m_bar, can0.IR.offset, reg_val_32)
        
    ######################################################
    #append to rxbuf
    rxbuf = []
    print("RxBuffer:")
    for idx in range(len(txbuf)):
        rxVal = ReadMmio(m_bar, address)
        txVal = ReadMmio(can0_bar, tbsa + (idx * 4))
        print(str(idx) + ": Tx(" + hex(txVal) + ") Rx("+ str(rxVal) + ")")
        rxbuf.append(ReadMmio(m_bar, address))
        address = address + 4
    
    	# Step: 6
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f0gi)
        WriteMmio(m_bar, can0.RXF0A.offset, reg_val_32)
    
    # Step: 7
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f1gi)
        WriteMmio(m_bar, can0.RXF1A.offset, reg_val_32)
    
    
    
    #compare txbuf to rxbuf
    
    if len(txbuf) != len(rxbuf):
        print("ERROR: TxBuf num dwords (" + str(len(txbuf)) + ") does not match RxBuf num dwords (" + str(len(rxbuf)) + ")")
        #return -1
        
    if len(txbuf) == 0:
        print("ERROR: Tx/Rx buffer size is zero")
        #return -1
    #if it is 11 bit identifier ignore 0-17 bits
    mask = 0xFFFFF0000
    mask_buff_1 = 0x1F0000
    #mask = 0xFFFFF0000
    
    # Iterate over both buffers and compare the pattern in each element
    for i in range(len(txbuf)):
        if txbuf[i] != rxbuf[i]:
            if i == 0 : 
                if (txbuf[i] & mask) != (rxbuf[i] & mask):
                    print("Pattern mismatch at index %d: TX=0x%08X, RX=0x%08X" % (i, txbuf[i], rxbuf[i]))
                    #return -1
                else:
                    print("Pattern match at index %d: TX=0x%08X, RX=0x%08X" % (i, (txbuf[i] & mask), (rxbuf[i] & mask)))
            elif i == 1:
              if (txbuf[i] & mask_buff_1) != (rxbuf[i] & mask_buff_1):
                  print("Pattern mismatch at index %d: TX=0x%08X, RX=0x%08X" % (i, txbuf[i], rxbuf[i]))
                  #return -1
              else:
                  print("Pattern match at index %d: TX=0x%08X, RX=0x%08X" % (i, (txbuf[i] & mask_buff_1), (rxbuf[i] & mask_buff_1)))
        else:
            print("Pattern match at index %d: TX=0x%08X, RX=0x%08X" % (i, txbuf[i], rxbuf[i]))
    
    '''
    for idx in range(len(txbuf)):
        if idx == 0 :
            
        if txbuf[idx] != rxbuf[idx]:
            print(" ERROR | Data Mismatch")
            return -1
    print("Data Match")
    return 1
    '''
        
    ######################################################
    
    

def verify_rx_fifo_remote_frame(m_bar = 0, addr=0, num_packets=0):
    print("Execute verify_rx_fifo_remote_frame")
    for i in range(num_packets):
        addr1 = addr + (i*0x48) # Next packet is in +0x48 address.
        readval = itp.threads[0].mem(str(m_bar + addr1) + 'p', 4)
        print ("readval from addr1 is", addr1)
        print ("readval is", readval)
        can_id = (readval >> 18) & 0x000007FF
        rtr = (readval >> 29) & 0x00000001
    
        if (i!=0):
            if (can_id >= prev_packet_can_id ): #Next packet should have higher/same can_id
                print ("PASS")
            else:
                print ("FAIL")
                print ("FAIL: Next packet should have higher/same can_id - can_id and prev_can_id are:", can_id, prev_packet_can_id)
        if (i!=0 and rtr == 1): 
            if (prev_packet_can_id <= can_id ): #If current packet is remote packet, previous packet should have lesser/same can_id
                print ("PASS for remote packet")
            else:
                print ("FAIL") 
                print ("FAIL: If current packet is remote packet, previous packet should have lesser/same can_id - can_id and prev_can_id are:", can_id, prev_packet_can_id)
                
        prev_packet_can_id = can_id
        
    

def verify_rx_fifo_remote_frame_with_stuff(m_bar = 0, addr=0, num_packets=0, can_id_sent_array=[],xtd=0):
    print("Execute verify_rx_fifo_remote_frame")
    can_id_rcv_array=[]
    for i in range(num_packets):
        addr1 = addr + (i*0x48) # Next packet is in +0x48 address.
        readval = itp.threads[0].mem(str(m_bar + addr1) + 'p', 4)
        print ("readval from addr1 is", addr1)
        print ("readval is", readval)
        if (xtd==0):
            can_id = (readval >> 18) & 0x000007FF
        else: 
            can_id = (readval) & 0x1FFFFFFF
        
        rtr = (readval >> 29) & 0x00000001
    
        if (i!=0):
            if (can_id >= prev_packet_can_id ): #Next packet should have higher/same can_id
                print ("PASS")
            else:
                print ("FAIL")
                print ("FAIL: Next packet should have higher/same can_id - can_id and prev_can_id are:", can_id, prev_packet_can_id)
        if (i!=0 and rtr == 1): 
            if (prev_packet_can_id <= can_id ): #If current packet is remote packet, previous packet should have lesser/same can_id
                print ("PASS for remote packet")
            else:
                print ("FAIL") 
                print ("FAIL: If current packet is remote packet, previous packet should have lesser/same can_id - can_id and prev_can_id are:", can_id, prev_packet_can_id)
                
        prev_packet_can_id = can_id
        
        can_id_rcv_array.append(can_id) 
        
        if (can_id_sent_array == can_id_rcv_array):
            print ("PASS: Receive CAN IDs are in incremental order")
        else:
            print ("FAIL: Receive CAN IDs are NOT in incremental order")
        
        
        
                    
        


def ReadRAM(m_bar = 0, addr=0, dw_count=0):
    print("Reading message RAM from addr = 0x%x"%addr)
    global rxbuf
    rxbuf = []
    for i in range(dw_count):
        addr1 = addr + (i*4)
        readval = itp.threads[0].mem(str(m_bar + addr1) + 'p', 4)
        #readval = readreg(m_bar+addr)
        print("Read  MsgRAM[0x%x] = 0x%x"%(m_bar+addr1,readval))
        rxbuf.append(readval)
        
        
def MsgRAMTest(m_bar = 0):
    print("Writing MsgRAM...")
    for i in range(4480):
        wrval = i + 100 #1180-->can_1
        WriteMmio(m_bar, 0x800+(i*4), wrval)
        rdval =  ReadMmio(m_bar, 0x800+(i*4),1)
        if(wrval == rdval):
            print("Match at address 0x%x"%(0x800+(i*4)))
        else:
            print("MisMatch at address 0x%x"%(0x800+(i*4)))
            #return 0
    



def verify_rx(m_bar = 0, sfec = 0, pkt_cnt = 0, txbuf = 0, pos = 0):

    reg_val_32 = 0
    tbsa = 0
    tbds = 0
    tx_size = 0
    tbsa_val = 0
    efsa = 0
    effl = 0
    efpi = 0
    efgi = 0
    f0sa = 0
    f0ds = 0
    reg_cached = 0
    f0fl = 0
    f0gi = 0
    f0pi = 0
    ir_rf0n = 0
    fx_size = 0
    address = 0
    f1sa = 0
    f1ds = 0
    f1fl = 0
    f1gi = 0
    f1pi = 0
    ir_rf1n = 0
    rbsa = 0
    ndat1 = 0
    ndat2 = 0
    rbds = 0
    rx_size = 0
    
    print("verify rx start")
    # Step: 1
    reg_val_32 = ReadMmio(m_bar, can0.TXBC.offset)
    tbsa = ((reg_val_32 & 0x0000fffc) >> 2)
    print("tbsa :",tbsa)
    # Step: 2
    reg_val_32 = ReadMmio(m_bar, can0.TXESC.offset)
    tbds = (reg_val_32 & 0x00000007)
    if (tbds <= 0x4):
        tx_size = 0x08
    if (tbds == 0x5):
        tx_size = 0x20
    elif (tbds == 0x6):
        tx_size = 0x30
    elif (tbds == 0x7):
        tx_size = 0x40
    tbsa_val = (tbsa + (pos * 0x010))
    print("start address of tx buffer",tbsa_val)

    # Step: 3
    reg_val_32 = ReadMmio(m_bar, can0.TXEFC.offset)# for loop back read from mbar, for CAN0--->CAN1 read from CAN1 and from CAN1--->CAN0 read from CAN0
    efsa = ((reg_val_32 & 0x0000fffc) >> 2)
    print("start address of tx event",efsa)
    reg_val_32 = ReadMmio(m_bar, can0.TXEFS.offset)
    effl = (reg_val_32 & 0x0000003f)
    print("Number of elements in tx event fifo",effl)
    efpi = ((reg_val_32 & 0x001f0000) >> 16)
    print("Get index in tx event fifo",efpi)
    efgi = ((reg_val_32 & 0x00001f00) >> 8)
    print("Get index in tx event fifo",efgi)
    # Step: 4
    reg_val_32 = ReadMmio(m_bar, can0.TXEFA.offset)
    reg_val_32 = ((reg_val_32 & 0xffffffe0) | efgi)
    WriteMmio(m_bar, can0.TXEFA.offset, reg_val_32)

    # Step: 5
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0C.offset)
        f0sa = ((reg_val_32 & 0x0000fffc) >> 2)
        reg_val_32 = ReadMmio(m_bar, can0.RXESC.offset)
        f0ds = (reg_val_32 & 0x00000007)
    reg_cached = 0x0
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0S.offset)
        reg_cached = 0x1
        f0fl = (reg_val_32 & 0x0000007f)
        print("f0fl: ",f0fl)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF0S.offset)
            reg_cached = 0x1
        f0gi = ((reg_val_32 & 0x00003f00) >> 8)
        print("f0gi: ",f0gi)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF0S.offset)
        f0pi = ((reg_val_32 & 0x003f0000) >> 16)
        print("f0pi: ",f0pi)

    # Step: 6
    if (f0gi == 0x00):
        reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        ir_rf0n = (reg_val_32 & 0x00000001)
    if (ir_rf0n != 0x1):
        return -0x1

    # Step: 7
    if (sfec == 0x00000001):
        if (f0ds <= 0x4):
            fx_size = 0x08
        if (f0ds == 0x5):
            fx_size = 0x20
        elif (f0ds == 0x6):
            fx_size = 0x30
        elif (f0ds == 0x7):
            fx_size = 0x40
        address = (f0sa + (f0gi * 0x010))
        print("address of fifo 0 is :",address)

    # Step: 8
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1C.offset)
        f1sa = ((reg_val_32 & 0x0000fffc) >> 2)
        reg_val_32 = ReadMmio(m_bar, can0.RXESC.offset)
        f1ds = ((reg_val_32 & 0x00000070) >> 4)
    reg_cached = 0x0
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1S.offset)
        reg_cached = 0x1
        f1fl = (reg_val_32 & 0x0000007f)
        print("f1fl : ",f1fl)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF1S.offset)
            reg_cached = 0x1
        f1gi = ((reg_val_32 & 0x00003f00) >> 8)
        print("f1gi : ",f1gi)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF1S.offset)
        f1pi = ((reg_val_32 & 0x003f0000) >> 16)
        print("f1pi : ",f1pi)

    # Step: 9
    if (f1gi == 0x00):
        reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        ir_rf1n = ((reg_val_32 & 0x00000010) >> 4)
    if (ir_rf1n != 0x1):
        return -0x1

    # Step: 10
    if (sfec == 0x00000002):
        if (f1ds <= 0x4):
            fx_size = 0x08
        if (f1ds == 0x5):
            fx_size = 0x20
        elif (f1ds == 0x6):
            fx_size = 0x30
        elif (f1ds == 0x7):
            fx_size = 0x40
        address = (f1sa + (f1gi * 0x010))
        print("address of fifo 1 : ",address)

    # Step: 11
    if ((sfec == 0x00000001) and (f0fl < pkt_cnt)):
        return -0x1

    # Step: 12
    if ((sfec == 0x00000002) and (f1fl < pkt_cnt)):
        return -0x1

    # Step: 13
    if (sfec == 0x00000007):
        reg_val_32 = ReadMmio(m_bar, can0.RXBC.offset)
        rbsa = ((reg_val_32 & 0x0000fffc) >> 2)
        reg_val_32 = ReadMmio(m_bar, can0.NDAT1.offset)
        ndat1 = (reg_val_32 & 0xffffffff)
        print("ndat1 : ",ndat1)
        reg_val_32 = ReadMmio(m_bar, can0.NDAT2.offset)
        ndat2 = (reg_val_32 & 0xffffffff)
        print("ndat2 : ",ndat2)
        reg_val_32 = ReadMmio(m_bar, can0.RXESC.offset)
        rbds = ((reg_val_32 & 0x00000700) >> 8)

    # Step: 14
    if (sfec == 0x00000007):
        if (rbds <= 0x4):
            rx_size = 0x08
        if (rbds <= 0x5):
            rx_size = 0x20
        if (rbds <= 0x6):
            rx_size = 0x30
        if (rbds <= 0x7):
            rx_size = 0x40
        address = ((rbsa << 0x2) + (pos * 0x010))
        print("address of fifo 1 : ",address)

    # Step: 15
    if (ndat1 >= 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.NDAT1.offset)
        reg_val_32 = ((reg_val_32 & 0x00000000) | 0x00000001)
        WriteMmio(m_bar, can0.NDAT1.offset, reg_val_32)

    # Step: 16
    if (ndat2 >= 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.NDAT2.offset)
        reg_val_32 = ((reg_val_32 & 0x00000000) | 0x00000001)
        WriteMmio(m_bar, can0.NDAT2.offset, reg_val_32)

    # Step: 17
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f0gi)
        WriteMmio(m_bar, can0.RXF0A.offset, reg_val_32)

    # Step: 18
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f1gi)
        WriteMmio(m_bar, can0.RXF1A.offset, reg_val_32)

    # Step: 19
    if (ir_rf0n == 0x1):
        reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffe) | 0x1)
        WriteMmio(m_bar, can0.IR.offset, reg_val_32)

    # Step: 20
    if (ir_rf1n == 0x1):
        reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffef) | (0x1 << 4))
        WriteMmio(m_bar, can0.IR.offset, reg_val_32)
        
    ######################################################
    #append to rxbuf
    rxbuf = []
    print("RxBuffer:")
    for idx in range(len(txbuf)):
        rxVal = ReadMmio(m_bar, address)
        txVal = ReadMmio(m_bar, tbsa + (idx * 4))
        print(str(idx) + ": Tx(" + hex(txVal) + ") Rx("+ str(rxVal) + ")")
        rxbuf.append(ReadMmio(m_bar, address))
        address = address + 4
    
    	# Step: 6
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f0gi)
        WriteMmio(m_bar, can0.RXF0A.offset, reg_val_32)
    
    # Step: 7
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1A.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffc0) | f1gi)
        WriteMmio(m_bar, can0.RXF1A.offset, reg_val_32)
    
    
    
    #compare txbuf to rxbuf
    
    if len(txbuf) != len(rxbuf):
        print("ERROR: TxBuf num dwords (" + str(len(txbuf)) + ") does not match RxBuf num dwords (" + str(len(rxbuf)) + ")")
        #return -1
        
    if len(txbuf) == 0:
        print("ERROR: Tx/Rx buffer size is zero")
        #return -1
    #if it is 11 bit identifier ignore 0-17 bits
    mask = 0xFFFFF0000
    mask_buff_1 = 0x1F0000
    #mask = 0xFFFFF0000
    
    # Iterate over both buffers and compare the pattern in each element
    for i in range(len(txbuf)):
        if txbuf[i] != rxbuf[i]:
            if i == 0 : 
                if (txbuf[i] & mask) != (rxbuf[i] & mask):
                    print("Pattern mismatch at index %d: TX=0x%08X, RX=0x%08X" % (i, txbuf[i], rxbuf[i]))
                    #return -1
                else:
                    print("Pattern match at index %d: TX=0x%08X, RX=0x%08X" % (i, (txbuf[i] & mask), (rxbuf[i] & mask)))
            elif i == 1:
              if (txbuf[i] & mask_buff_1) != (rxbuf[i] & mask_buff_1):
                  print("Pattern mismatch at index %d: TX=0x%08X, RX=0x%08X" % (i, txbuf[i], rxbuf[i]))
                  #return -1
              else:
                  print("Pattern match at index %d: TX=0x%08X, RX=0x%08X" % (i, (txbuf[i] & mask_buff_1), (rxbuf[i] & mask_buff_1)))
        else:
            print("Pattern match at index %d: TX=0x%08X, RX=0x%08X" % (i, txbuf[i], rxbuf[i]))
    
    '''
    for idx in range(len(txbuf)):
        if idx == 0 :
            
        if txbuf[idx] != rxbuf[idx]:
            print(" ERROR | Data Mismatch")
            return -1
    print("Data Match")
    return 1
    '''
        
    ######################################################
    
    
def vector_to_can_send(fd = 0,nsjw=0,can_bitrate=0, fd_bitrate=0, is_extended=0, ntseg1=0, ntseg2=0, dsjw=0, dtseg1=0, dtseg2=0, brs=0,remote_frame=0, dlc=0,arbitration_id=1,channel=1 ):

    import argparse
    import contextlib

    # pylint: disable=deprecated-module
    import time

    import re
    import can
    from can.bus import BusState

    #from can.interfaces.vector import get_channel_configs
    '''
    if __name__ == "__main__":
        parser = argparse.ArgumentParser(
            description="Receive CAN frame",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument("--fd", action="store_true")
        parser.add_argument("--brs", action="store_true")
        parser.add_argument("--remote-frame", action="store_true")
        parser.add_argument("--is-extended", action="store_true")
        parser.add_argument(
            "-c", "--can_bitrate", default=125000, help="CAN bitrate [bps]", type=int
        )
        parser.add_argument("-d", "--fd_bitrate", default=250000, help="FD bitrate [bps]", type=int)
        parser.add_argument("--nsjw", help="Nominal sjw", type=int)
        parser.add_argument("--ntseg1", help="Nominal tseg 1", type=int)
        parser.add_argument("--ntseg2", help="Nominal tseg 2", type=int)
        parser.add_argument("--dsjw", help="Data sjw", type=int)
        parser.add_argument("--dtseg1", help="Data tseg 1", type=int)
        parser.add_argument("--dtseg2", help="Data tseg 2", type=int)

        parser.add_argument("-a", "--arbitration_id", default=123, help="arbitration id", type=int)
        parser.add_argument("-l", "--data_length", help="Data length", type=int)
        parser.add_argument("--data", default=None, help="Data in hex string")

        args = vars(parser.parse_args())
    '''
    if ( fd ==1 ):#args["fd"]
        if (nsjw==0):#args["nsjw"] is None:
            vector_bus = can.Bus(
                interface="vector",
                channel=channel,
                bitrate=can_bitrate,#args["can_bitrate"]
                fd=True,
                data_bitrate=fd_bitrate,#args["fd_bitrate"]
                is_extended_id=is_extended,#args["is_extended"]
            )
        else:
            vector_bus = can.Bus(
                interface="vector",
                channel=1,
                serial = 26680,
                #channel=channel,
                bitrate=can_bitrate,#args["can_bitrate"]
                fd=True,
                data_bitrate=fd_bitrate, #args["fd_bitrate"]
                sjw_abr=nsjw, #args["nsjw"]
                tseg1_abr=ntseg1, #args["ntseg1"]
                tseg2_abr=ntseg2, #args["ntseg2"]
                sjw_dbr=dsjw, #args["dsjw"]
                tseg1_dbr=dtseg1, #args["dtseg1"]
                tseg2_dbr=dtseg2, #args["dtseg2"]
                is_extended_id=is_extended, #args["is_extended"]
                app_name="CANalyzer",
            )
    else:
        vector_bus = can.Bus(interface="vector", channel=channel, bitrate=can_bitrate)

    with vector_bus as vector_can:
        '''
        for config in get_channel_configs():
            if "Virtual" not in config.name:
                with contextlib.suppress(AttributeError):
                    print(str(config.bus_params.canfd))
        '''
        with contextlib.suppress(NotImplementedError):
            vector_bus.state = BusState.PASSIVE

        print("VECTOR STATE:{vector_can.state}", vector_can.state)
        print("start")

        #arbitration_id = arbitration_id #args["arbitration_id"]

        data = (
            range(dlc) #args["data_length"]
            #if (data == 0) #args["data"] is None
            #else [int(x, 16) for x in re.findall("[A-Fa-f\\d]{2}",(data) #args["data"])]
        )

        #data_len = (
        #    data_length = len(data)) #(args["data_length"] if args["data_length"] else len(data))
        #    #if (fd)#args["fd"]
        #    #else ["data_length"] if ["data_length"] <= 8 else 8 #args["data_length"] if args["data_length"] <= 8 else 8
        #)
        #data_len = len(data)

        #print("Sending arbitration_id: arbitration_id  and data is", arbitration_id, data)

        vector_can.send(
            can.Message(
                arbitration_id=arbitration_id,
                data=data,
                dlc=dlc,
                is_fd= fd, #args["fd"],
                bitrate_switch=brs, #args["brs"],
                is_remote_frame=remote_frame, #args["remote_frame"],
                is_extended_id=is_extended, #args["is_extended"],
            )
        )

        time.sleep(1)
        print("STOP SENDING")



def createTxdata(can_id = 0, rtr = 0, xtd = 0, esi = 0, mm = 0, dlc = 0, brs = 0, fdf = 0, tsce = 0, efc = 0, txbuf = 0, tx_data = 0, pos = 0):


    num_bytes = getNumBytes(dlc)
    print("num_bytes",num_bytes)
######################################################
    #append tx
    num_dword = num_bytes/4
    num_remain = num_bytes%4

    for idx in range(num_dword):
        offset = idx * 4
        #data =tx_data[offset+3] << 12 | tx_data[offset+2] << 8 | tx_data[offset+1] << 4 | tx_data[offset]
        data =tx_data[offset+3] << 24 | tx_data[offset+2] << 16 | tx_data[offset+1] << 8 | tx_data[offset]
        print("in for loop",data)
        txbuf.append(data)
    data = 0
    offset = num_dword*4
    print("this is offset",offset)
    if num_remain:
        for idx in range(num_remain):
            #offset = num_bytes
            #data = (data << 4) | tx_data[idx + offset]
            data = data | (tx_data[idx + offset])<<(idx*8)
        txbuf.append(data)
######################################################
    # Step: 2
    
    for idx in range(len(txbuf)):
        print("createTxPacket: index "+ str(idx) + ": " + hex(txbuf[idx]))
    print("createTxPacket() - end")
    return txbuf
    
    
    
def verify_rx_fifo_3nodes(m_bar = 0, addr=0, num_packets=0):

    count_can_id =  0
    print("Execute verify_rx_fifo_remote_frame")
    for i in range(num_packets):
        addr1 = addr + (i*0x48) # Next packet is in +0x48 address.
        readval = itp.threads[0].mem(str(m_bar + addr1) + 'p', 4)
        print ("readval from addr1 is", addr1)
        print ("readval is", readval)
        can_id = (readval >> 18) & 0x000007FF
        
    
        if (can_id!=0):
            count_can_id=count_can_id+1
            print ("count_can_id is", count_can_id)
    if  (count_can_id!=2): 
        print ("FAIL")
    else:
        print ("PASS")
        
        
        
    
def verify_rx_testcase_25(m_bar = 0, can1_bar=0, addr=0, can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=1, num_packets=1):
    count_can_id =  0
    print("Execute verify_rx_fifo_remote_frame")
    for i in range(num_packets):
        addr1 = addr + (i*0x48) # Next packet is in +0x48 address.
        readval = itp.threads[0].mem(str(m_bar + addr1) + 'p', 4)
        if (readval == 0):
            readval = itp.threads[0].mem(str(can1_bar + addr1) + 'p', 4)
        
        print ("addr1 is", addr1)
        print ("readval is", readval)
        can_id = (readval >> 18) & 0x000007FF
        print ("Receive can_id is", can_id)
        
    
        if ((sent_can_id > can0_sfid1) and (sent_can_id < can0_sfid2)):
            if ((can_id > can0_sfid1) and (can_id < can0_sfid2)):
                print ("PASS")
            else:
                print ("FAIL")
                
   
        if ((sent_can_id > can1_sfid1) and (sent_can_id < can1_sfid2)):
            if ((can_id > can1_sfid1) and (can_id < can1_sfid2)):
                print ("PASS")
            else:
                print ("FAIL")
        else:
            print ("FAIL")        
            print ("FAIL: Receive can_id did not match with any sent can id")
    

   
def verify_rx_testcase_26(m_bar = 0, can1_bar=0, addr=(0x800 + 0x400), can0_sfid1=0x1, can0_sfid2=0x1AA,can1_sfid1=0x1AB, can1_sfid2=0x7FF, sent_can_id_can0=1, sent_can_id_can1=1, sent_can_id_vector=1, num_packets=1):
    count_can_id =  0
    print("Execute verify_rx_fifo_remote_frame")
    for i in range(num_packets):
        addr1 = addr + (i*0x48) # Next packet is in +0x48 address.
        readval_can0 = itp.threads[0].mem(str(m_bar + addr1) + 'p', 4)
        readval_can0_next = itp.threads[0].mem(str(m_bar + addr1 + (i*0x48)) + 'p', 4)
        
        readval_can1 = itp.threads[0].mem(str(can1_bar + addr1) + 'p', 4)

        print ("addr1 is", addr1)
        can_id_can0 = (readval_can0 >> 18) & 0x000007FF
        can_id_can0_next = (readval_can0_next >> 18) & 0x000007FF
        
        can_id_can1 = (readval_can1 >> 18) & 0x000007FF
        
        print ("Receive can_id_can0 is", can_id_can0)
        print ("Receive can_id_can0_next is", can_id_can0_next)
        
        print ("Receive can_id_can1 is", can_id_can1)
            
        if (can_id_can0 !=0 and can_id_can0_next !=0):
            print ("PASS")
        else:
            print ("FAIL")
           
        if (can_id_can1 !=0):
            print ("PASS")
        else:
            print ("FAIL")
            
            
def can_vector_receive(fd = 0,nsjw=0,can_bitrate=0, fd_bitrate=0, is_extended=0, ntseg1=0, ntseg2=0, dsjw=0, dtseg1=0, dtseg2=0, brs=0,remote_frame=0, dlc=0,arbitration_id=1 ):
                    
    import argparse
    import contextlib

    import can
    from can.bus import BusState
    #from can.interfaces.vector import get_channel_configs

    '''

    def print_message(can_message):
        out = f"Arbitration_id: {hex(can_message.arbitration_id)}\n"
        out += "Remote frame\n" if can_message.is_remote_frame else ""
        out += "Extended arbitration id frame\n" if can_message.is_extended_id else ""
        out += "Error frame\n" if can_message.is_error_frame else ""
        out += "Bitrate Switch\n" if can_message.bitrate_switch else ""
        out += f"Data_length: {len(can_message.data)}\n"
        out += f"data: {[hex(byte) for byte in can_message.data]}\n"
        print(out)


    if __name__ == "__main__":
        parser = argparse.ArgumentParser(
            description="Receive CAN frame",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument("--fd", action="store_true")
        parser.add_argument(
            "-c", "--can_bitrate", default=125000, help="CAN bitrate [bps]", type=int
        )
        parser.add_argument("-d", "--fd_bitrate", default=250000, help="FD bitrate [bps]", type=int)
        parser.add_argument(
            "-t", "--frame-timeout", default=2, help="Receiving frame Timeout", type=int
        )
        parser.add_argument(
            "-n", "--frames-number", default=1, help="Number of expected frames", type=int
        )
        parser.add_argument("--nsjw", help="Nominal sjw", type=int)
        parser.add_argument("--ntseg1", help="Nominal tseg 1", type=int)
        parser.add_argument("--ntseg2", help="Nominal tseg 2", type=int)
        parser.add_argument("--dsjw", help="Data sjw", type=int)
        parser.add_argument("--dtseg1", help="Data tseg 1", type=int)
        parser.add_argument("--dtseg2", help="Data tseg 2", type=int)

        args = vars(parser.parse_args())
    '''
    if (fd==1):#args["fd"]:
            if (nsjw==0):#args["nsjw"] is None:
                vector_bus = can.Bus(
                    interface="vector",
                    channel=0,
                    bitrate= can_bitrate,#args["can_bitrate"],
                    fd=True,
                    data_bitrate=fd_bitrate,#args["fd_bitrate"],
                )
            else:
                vector_bus = can.Bus(
                    interface="vector",
                    channel=0,
                    bitrate=can_bitrate,#args["can_bitrate"],
                    fd=True,
                    data_bitrate=fd_bitrate,#args["fd_bitrate"],
                    sjw_abr=nsjw,#args["nsjw"],
                    tseg1_abr=ntseg1,#args["ntseg1"],
                    tseg2_abr=ntseg2,#args["ntseg2"],
                    sjw_dbr=dsjw,#args["dsjw"],
                    tseg1_dbr=dtseg1,#args["dtseg1"],
                    tseg2_dbr=dtseg2,#args["dtseg2"],
                )
    else:
        if (nsjw==0):#)args["nsjw"] is None:
                vector_bus = can.Bus(interface="vector", channel=0, bitrate=can_bitrate)#args["can_bitrate"])
        else:
            f_clock = 16_000_000
            tq_per_bit = ntseg1+ntseg2+1#args["ntseg1"] + args["ntseg2"] + 1
            brp = int(f_clock / (can_bitrate* tq_per_bit))#(args["can_bitrate"] * tq_per_bit))
            print(f"brp = {brp}")
            vector_bus = can.Bus(
                    interface="vector",
                    channel=0,
                    f_clock=f_clock,
                    brp=brp,
                    tseg1=ntseg1,#args["ntseg1"],
                    tseg2=ntseg2,#args["ntseg2"],
                    sjw=nsjw,#args["nsjw"],
                    nof_samples=1,            
            )
    return vector_bus
    '''
    with vector_bus as vector_can:
        
        
        for config in get_channel_configs():
            if "Virtual" not in config.name:
                with contextlib.suppress(AttributeError):
                    print(str(config.bus_params.canfd))
        
        with contextlib.suppress(NotImplementedError):
            vector_bus.state = BusState.PASSIVE

        print(f"VECTOR STATE:{vector_can.state}")
        print("start receiving")
        frame_count = 0
        for _ in range(frames_number):#args["frames_number"]):
            msg = vector_can.recv(frame_timeout)#args["frame_timeout"])
            if msg:
                frame_count += 1
                print("=" * 80)
                print(f"Message nr {frame_count} received")
                print_message(msg)
                tryout = 0
                while tryout <= 64 and msg and msg.is_error_frame:
                        tryout += 1
                        print("-" * 80)
                        print(f"Message tryout: {tryout}")
                        msg = vector_can.recv(frame_timeout)#args["frame_timeout"])
                        print_message(msg)

        print("STOP RECEIVING")                   

        '''  
                   

        