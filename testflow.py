from enum import Enum
import itpii
itp = itpii.baseaccess()

#import can_reg; reload(can_reg)
import sys

import sys
import ctypes
import random
import time
import math

import pci2
import os
import threading
global can0

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
    value = itp.threads[0].mem((str(m_bar + address) + "p"), size)
    return value

def WriteMmio(m_bar, address, data, size=4):
    itp.threads[0].mem((str(m_bar + address) + "p"), size, data)
    return True

def clearRAM(m_bar = 0):
    for i in range(4480):
        itp.threads[0].mem(str(m_bar + 0x800 + (i * 4)) + "p", 4, 0x0)


def can_setup(m_bar = 0, rxf0c_elements = 0, rxf1c = 0, rxf1c_elements = 0, rxbuff_elements = 0, tbds = 0, flssa = 0, lss = 0, lse = 0, flesa = 0, eidm = 0, f0sa = 0, f1sa = 0, rbsa = 0, f0ds = 0, f1ds = 0, rbds = 0, efsa = 0, efs = 0, efwm = 0, tbsa = 0, ndtb = 0, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0, ntseg1 = 0, nbrp = 0, nsjw = 0, fsjw = 0, ftseg2 = 0, ftseg1 = 0, fbrp = 0, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0, anfe = 0, anfs = 0, tie = 0, cfie = 0, eint0 = 0, eint1 = 0, intrLine = 0):

    reg_val_32 = 0
    flssa_val = 0

    # Step: 1
    reg_val_32 = ReadMmio(m_bar, can0.CCCR.offset)
    reg_val_32 = ((reg_val_32 & 0xffffff7f) | (0x1 << 7))
    WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)

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
    reg_val_32 = ((reg_val_32 & 0xff80ffff) | (rxf0c_elements << 16))
    WriteMmio(m_bar, can0.RXF0C.offset, reg_val_32)

    # Step: 6
    reg_val_32 = ReadMmio(m_bar, can0.RXF1C.offset)
    reg_val_32 = ((reg_val_32 & 0xffff0003) | (((rxf1c + 0x00800) >> 0x2) << 2))
    reg_val_32 = ((reg_val_32 & 0xff80ffff) | (rxf1c_elements << 16))
    WriteMmio(m_bar, can0.RXF1C.offset, reg_val_32)

    # Step: 7
    reg_val_32 = ReadMmio(m_bar, can0.RXBC.offset)
    reg_val_32 = ((reg_val_32 & 0xffff0003) | ((rbsa >> 0x2) << 2))
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
    reg_val_32 = ReadMmio(m_bar, can0.CCCR.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffeff) | (fdoe << 8))
    reg_val_32 = ((reg_val_32 & 0xfffffdff) | (brse << 9))
    WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)

    # Step: 13
    reg_val_32 = ReadMmio(m_bar, can0.NBTP.offset)
    reg_val_32 = ((reg_val_32 & 0xffffff80) | ntseg2)
    reg_val_32 = ((reg_val_32 & 0xffff80ff) | (ntseg1 << 8))
    reg_val_32 = ((reg_val_32 & 0xfe00ffff) | (nbrp << 16))
    reg_val_32 = ((reg_val_32 & 0x01ffffff) | (nsjw << 25))
    WriteMmio(m_bar, can0.NBTP.offset, reg_val_32)

    # Step: 14
    reg_val_32 = ReadMmio(m_bar, can0.DBTP.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffff0) | fsjw)
    reg_val_32 = ((reg_val_32 & 0xffffff0f) | (ftseg2 << 4))
    reg_val_32 = ((reg_val_32 & 0xffffe0ff) | (ftseg1 << 8))
    reg_val_32 = ((reg_val_32 & 0xffe0ffff) | (fbrp << 16))
    reg_val_32 = ((reg_val_32 & 0xff7fffff) | (tdc << 23))
    WriteMmio(m_bar, can0.DBTP.offset, reg_val_32)

    # Step: 15
    reg_val_32 = ReadMmio(m_bar, can0.TDCR.offset)
    reg_val_32 = ((reg_val_32 & 0xffffff80) | tdcf)
    reg_val_32 = ((reg_val_32 & 0xffff80ff) | (tdco << 8))
    WriteMmio(m_bar, can0.TDCR.offset, reg_val_32)

    # Step: 16
    reg_val_32 = ReadMmio(m_bar, can0.GFC.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffe) | rrfe)
    reg_val_32 = ((reg_val_32 & 0xfffffffd) | (rrfs << 1))
    reg_val_32 = ((reg_val_32 & 0xfffffff3) | (anfe << 2))
    reg_val_32 = ((reg_val_32 & 0xffffffcf) | (anfs << 4))
    WriteMmio(m_bar, can0.GFC.offset, reg_val_32)

    # Step: 17
    reg_val_32 = ReadMmio(m_bar, can0.TXBTIE.offset)
    reg_val_32 = ((reg_val_32 & 0x00000000) | tie)
    WriteMmio(m_bar, can0.TXBTIE.offset, reg_val_32)

    # Step: 18
    reg_val_32 = ReadMmio(m_bar, can0.TXBCIE.offset)
    reg_val_32 = ((reg_val_32 & 0x00000000) | cfie)
    WriteMmio(m_bar, can0.TXBCIE.offset, reg_val_32)

    # Step: 19
    WriteMmio(m_bar, can0.IR.offset, 0xffffffff)

    # Step: 20
    WriteMmio(m_bar, can0.IE.offset, 0xffffffff)

    # Step: 21
    if ((intrLine == 0x00000000) or (intrLine == 0x00000001)):
        reg_val_32 = ReadMmio(m_bar, can0.ILE.offset)
        if (intrLine == 0x00000000):
            reg_val_32 = ((reg_val_32 & 0xfffffffe) | eint0)
        elif (intrLine == 0x00000001):
            reg_val_32 = ((reg_val_32 & 0xfffffffd) | (eint1 << 1))
        WriteMmio(m_bar, can0.ILE.offset, reg_val_32)


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


def getNumBytes(dlc = 0):

    ret = 0

    # Step: _default
    if (dlc <= 0x8):
        return dlc
    ret = (((dlc - 0x09) * 0x04) + 0x08)
    return ret


def createTxPacket(can_id = 0, rtr = 0, xtd = 0, esi = 0, mm = 0, dlc = 0, brs = 0, fdf = 0, tsce = 0, efc = 0, txbuf = 0, tx_data = 0):

    can_id1 = 0
    t0 = 0
    t1 = 0
    num_bytes = 0

    # Step: 1
    if ((fdf == 0x0) or (xtd == 0x0)):
        can_id1 = (can_id << 0x12)
    else:
        can_id1 = can_id
    t0 = ((((esi << 0x1f) | (xtd << 0x1e)) | (rtr << 0x1d)) | can_id1)
    t1 = (((((((((mm & 255) & 0xff) << 0x18) | (efc << 0x17)) | (tsce << 0x16)) | (fdf << 0x15)) | (brs << 0x14)) | (dlc << 0x10)) | ((((mm >> 0x8) & 255) & 0xff) << 0x8))
    num_bytes = getNumBytes(dlc)

    # Step: 2
    return txbuf


def create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0):

    ret = 0

    # Step: _default
    ret = (((((sft << 0x1e) | (sfec << 0x1b)) | (sfid1 << 0x10)) | (ssync << 0xf)) | sfid2)
    return ret


def create29bitFilter(eft = 0, efec = 0, efid1 = 0, esync = 0, efid2 = 0):

    f0 = 0
    f1 = 0

    # Step: _default
    f0 = ((efec << 0x1c) | efid1)
    f1 = (((eft << 0x1d) | (esync << 0x1c)) | efid2)


def pushTxPacketRam(m_bar = 0, pos = 0, txbuf = 0):

    reg_val_32 = 0
    tbsa = 0
    tbds = 0
    tx_size = 0
    address = 0

    # Step: 1
    reg_val_32 = ReadMmio(m_bar, can0.TXBC.offset)
    tbsa = ((reg_val_32 & 0x0000fffc) >> 2)
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
    address = ((tbsa << 0x2) + (pos * tx_size))


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
    buffer_element_enable = (txbar | (0x1 << pos))
    reg_val_32 = ((reg_val_32 & 0x00000000) | buffer_element_enable)
    WriteMmio(m_bar, can0.TXBAR.offset, reg_val_32)

    # Step: 2
    count = 0x1e
    while True:
        _tmp = ReadMmio(m_bar, can0.IR.offset)
        _pvar = ((_tmp & 0x00000200) >> 9)
        _PollCount += 1
        if (_PollCount >= 30):  # check max count
            print " ERROR | Hit Maximum count:30 (IR == BitVector<1>)"
            break
        if (_pvar == 0x1):
            break
    reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
    transmission_completed = ((reg_val_32 & 0x00000200) >> 9)
    if (transmission_completed == 0x1):
        reg_val_32 = ((reg_val_32 & 0xfffffdff) | (0x1 << 9))
        WriteMmio(m_bar, can0.IR.offset, reg_val_32)


def push11BitFilter(m_bar = 0, pos = 0, filt = 0):

    reg_val_32 = 0
    flssa = 0
    address = 0

    # Step: _default
    reg_val_32 = ReadMmio(m_bar, can0.SIDFC.offset)
    flssa = ((reg_val_32 & 0x0000fffc) >> 2)
    address = ((flssa << 0x2) + (pos * 0x000000004))
    WriteMmio(m_bar, address, filt)


def push29BitFilter(m_bar = 0, pos = 0, filt = 0):

    reg_val_32 = 0
    flesa = 0
    address = 0

    # Step: _default
    reg_val_32 = ReadMmio(m_bar, can0.XIDFC.offset)
    flesa = ((reg_val_32 & 0x0000fffc) >> 2)
    address = ((flesa << 0x2) + (pos * 0x000000004))
    WriteMmio(m_bar, address, filt)


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


def verify_rx(m_bar = 0, sfec = 0, pkt_cnt = 0, txbuf = 0):

    reg_val_32 = 0
    f0sa = 0
    address = 0
    f1sa = 0
    timeout = 0
    _PollCount = 0
    _pvar = 0
    reg_cached = 0
    rf0n = 0
    rf1n = 0
    f0fl = 0
    f0gi = 0
    f1fl = 0
    f1gi = 0

    # Step: 1
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0C.offset)
        f0sa = ((reg_val_32 & 0x0000fffc) >> 2)
        address = (f0sa << 0x2)

    # Step: 2
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1C.offset)
        f1sa = ((reg_val_32 & 0x0000fffc) >> 2)
        address = (f1sa << 0x2)

    # Step: 3
    timeout = 0x1e
    while True:
        _tmp = ReadMmio(m_bar, can0.IR.offset)
        _pvar = (_tmp & 0x00000001)
        _PollCount += 1
        if (_PollCount >= 30):  # check max count
            print " ERROR | Hit Maximum count:30 (IR == BitVector<1>)"
            break
        if (_pvar == 0x1):
            break
    reg_cached = 0x0
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        reg_cached = 0x1
        rf0n = (reg_val_32 & 0x00000001)
    if ((not reg_cached) and ((rf0n == 0x1) or ((sfec == 0x00000002) and (not (sfec == 0x00000001))))):
        reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        reg_cached = 0x1
    if (sfec == 0x00000002):
        rf1n = ((reg_val_32 & 0x00000010) >> 4)
    if (rf0n == 0x1):
        reg_val_32 = ((reg_val_32 & 0xfffffffe) | 0x1)
    if (rf1n == 0x1):
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.IR.offset)
        reg_val_32 = ((reg_val_32 & 0xffffffef) | (0x1 << 4))
    if ((rf1n == 0x1) or (rf0n == 0x1)):
        WriteMmio(m_bar, can0.IR.offset, reg_val_32)
    reg_cached = 0x0
    if (sfec == 0x00000001):
        reg_val_32 = ReadMmio(m_bar, can0.RXF0S.offset)
        reg_cached = 0x1
        f0fl = (reg_val_32 & 0x0000007f)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF0S.offset)
        f0gi = ((reg_val_32 & 0x00003f00) >> 8)
    reg_cached = 0x0
    if (sfec == 0x00000002):
        reg_val_32 = ReadMmio(m_bar, can0.RXF1S.offset)
        reg_cached = 0x1
        f1fl = (reg_val_32 & 0x0000007f)
        if (not reg_cached):
            reg_val_32 = ReadMmio(m_bar, can0.RXF1S.offset)
        f1gi = ((reg_val_32 & 0x00003f00) >> 8)

    # Step: 4
    if ((sfec == 0x00000001) and (f0fl < pkt_cnt)):
        return -0x1

    # Step: 5
    if ((sfec == 0x00000002) and (f1fl < pkt_cnt)):
        return -0x1

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
