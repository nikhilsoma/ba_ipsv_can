###Author: chia.kian.puan@intel.com  --- VICE LPSS SV
## PLEASE DO NOT EDIT ANY of the function. If u want to do so, please inform me. Thank you.
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import sys
import ctypes
import random
import time
import math

import itpii
import pci2
import os
import threading 
#from can_reg import *
itp = itpii.baseaccess()



#import my_lib;reload (my_lib)

import log_file_framework as var_log_fw
#import can_reg; reload(can_reg)
import importlib

import can_reg
#import can_vector_receive as can_vector_receive


importlib.reload(can_reg)

import CanDeviceLibrary as CanDeviceLibrary

'''
## =========== Python 3.6.8 New log file Test_log.txt ================== ##
import sys
sys.stdout = open('Test_log.txt',"w")
## ===================================================================== ##
'''

print("after CanDeviceLibrary")




var_log_ALL=4
var_log_INFORMATION=3
var_log_DEBUG=2
var_log_ERROR=1
var_log_CRITICAL=0

start_time = 0

#Default Assignment

var_log_level_SET=var_log_ALL
#Faster Execution, Restricted Log Level
#var_log_level_SET=var_log_DEBUG



def log_print(var_log_level=var_log_ALL, var_log_line=''):
    if var_log_level <= var_log_level_SET:
        var_log_fw.write_to_existing_file(var_log_line)

log_print(var_log_INFORMATION,str(sys.argv[0]) + " command line arguments : " + str(sys.argv))

# for current func name, specify 0 or no argument.
# for name of caller of current func, specify 1.
# for name of caller of caller of current func, specify 2. etc.
currentFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name

DID_LIST = {
   
    'PTL' : {'0':{'DID':0x67B5, 'DEV': 0x1D, 'FUNC':0},'1':{'DID':0x67B6, 'DEV': 0x1D, 'FUNC':1}},
    
    }

global prj 
prj = 'PTL'


global CAN
global can0
global can1


mem_src = 0x1000000
mem_dst = 0x2000000



bus=0x03
device=0x1D
func=0x0
func_can1=0x1



def dump_mem (base, length, size=4):
    # itp.threads[0].memdump(str(base)+'p' , str(length)+'p', size)
    itp.threads[0].memdump(str(base)+'p' , length, size)
    return
    

def readMem(address, size=4):
    value = itp.threads[0].mem((str(address) + 'p'), size)
    return value

def writeMem(address, data, size=4):
    itp.threads[0].mem((str(address) + 'p'), size, data)
    return True


def readCfg(bus,device,func,offset):
    arg = ((0x80000000) | (bus << 16) | (device << 11) | (func << 8) | (offset))
    itp.threads[0].dport(0xcf8, arg)
    value = itp.threads[0].dport(0xcfc)
    return value

def writeCfg(bus,device,func,offset, data):
    arg = ((0x80000000) | (bus << 16) | (device << 11) | (func << 8) | (offset))
    itp.threads[0].dport(0xcf8, arg)
    itp.threads[0].dport(0xcfc, data)
    return True


##############function to re-initiate project
def fpga_init(proj=prj,verbose= 0):

    global PROJECT

    found = False
 
    #loop to scan bus and identify where the TSN is located
    for i in range(2,23):
        #open PCI cfg space for TSN.
        if(verbose):
            log_print(var_log_INFORMATION, "Open PCI Cfg for B:D:F = %d,0x%x,0x%x\n" % (i,DID_LIST[proj]['0']['DEV'],DID_LIST[proj]['0']['FUNC']))
            
        pci2.OpenPciCfg(i,DID_LIST[proj]['0']['DEV'],DID_LIST[proj]['0']['FUNC'])
        #pci2.OpenPciCfg(i,DID_LIST[proj]['1']['DEV'],DID_LIST[proj]['1']['FUNC'])
        
        didread = pci2.ReadPciCfgBits(0x0,31,16)

        pci2.ClosePciCfg()

        if((didread & 0xffff) == DID_LIST[proj]['0']['DID']):  
            log_print(var_log_INFORMATION, "Detected CAN FPGA for %s with DID = 0x%x on bus number = 0x%x\n" %(proj,DID_LIST[proj]['0']['DID'],i))
            found = True
            dev_bus = i
            break
   
    if(not found):
        log_print(var_log_INFORMATION, "ERROR | Did not manage to find any CAN controller\n")
        return 1
        
    
    
    #print I3C
    global CAN
    global can0
    global can1

  
        

    can0 = can_reg.regs(dev_bus, DID_LIST[proj]['0']['DEV'],DID_LIST[proj]['0']['FUNC'])
    can1 = can_reg.regs(dev_bus, DID_LIST[proj]['1']['DEV'],DID_LIST[proj]['1']['FUNC'])
    CAN =[can0, can1]
    
    
    log_print(var_log_INFORMATION, "MSG_RAM_SIZE =0x%X" % (can0.MSG_RAM_SIZE.read()))
    #log_print(var_log_INFORMATION, "MAC_Version =0x%X" % (can0.MAC_Version.read()))
    #log_print(var_log_INFORMATION, "CSR =0x%X" % (tsn0.CSR.read()))
    
   

    
        
    
    log_print(var_log_INFORMATION, "SUCCESS | FPGA Initialization complete\n")
    
    return


def can_init():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 0, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 0, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    #CanDeviceLibrary.pushTxPacket(m_bar = m_bar, pos = 0, pkt_num = 1, can_id = 0x5A5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, data0 = 0x04030201, data1 = 0x08070605)
    #CanDeviceLibrary.createTxPacket(dw_num = 0, can_id = 0, rtr = 0, xtd = 0, esi = 0, mm = 0, dlc = 0, brs = 0, fdf = 0, tsce = 0, efc = 0, txbuf = [], tx_data = [])
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x5A5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    #txbuf = CanDeviceLibrary.createTxPacket(can_id=0x114, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 6, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data , pos = 1)
    #CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = 7, pkt_cnt = 0, txbuf = txbuf)
    #CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 1, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = 1, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    


def can_init_old():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 2, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
  
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 10, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    
        
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 10, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
       
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 10, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
               
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 10, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 3, txbuf = txbuf)
       
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 10, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 4)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 4, txbuf = txbuf)
    
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
    print("IR TxEventFIFO - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")    
    
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
    print("IR TxEventFIFO - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")      
    
    
    
    # val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1FFFF, esync = 0x0, efid2 = 0x1FFFFF)
    # CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 1, filt = val)
    
    # val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1FFFFFF, esync = 0x0, efid2 = 0x1FFFFFFF)
    # CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 2, filt = val)
    
    
    # txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FFE, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    # CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    # CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    # txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FFFFE, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    # CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    # CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    
    # txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FFFFFFE, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    # CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    # CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)
    
    # CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    # CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 1)
    # CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 2)
    
    
    print("Reading MsgRAM Extended filter data")
    addr = (0x800 + 0x200)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x2800), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 8)
    print("\n")
    
    
    
def can_init_extd_filter():
    
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    '''
    print("this is my first sequence")
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 3, rbds = 3, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 0, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x01, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    val = CanDeviceLibrary.create11bitFilter(sft = 1, sfec = 7, sfid1 = 0x01, ssync = 0, sfid2 = 0x0)
    CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    #CanDeviceLibrary.pushTxPacket(m_bar = m_bar, pos = 0, pkt_num = 1, can_id = 0x5A5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, data0 = 0x04030201, data1 = 0x08070605)
    #CanDeviceLibrary.createTxPacket(dw_num = 0, can_id = 0, rtr = 0, xtd = 0, esi = 0, mm = 0, dlc = 0, brs = 0, fdf = 0, tsce = 0, efc = 0, txbuf = [], tx_data = [])
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    #txbuf = CanDeviceLibrary.createTxPacket(can_id=0x114, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 6, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data , pos = 1)
    #CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = 7, pkt_cnt = 0, txbuf = txbuf)
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 7, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    '''
    print("this is my second sequence")
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1fffffff, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 3, rbds = 3, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    '''
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 0, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    '''
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    txbuf = CanDeviceLibrary.createTxPacket(can_id=15555555, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 6, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)

    #val = CanDeviceLibrary.create11bitFilter(sft = 1, sfec = 7, sfid1 = 0x3d, ssync = 0, sfid2 = 0x0)
    #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x02, efid1 = 0x1, esync = 0x0, efid2 = 0x1FFFFFFF)
    CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 0, filt = val)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 2, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x2800), dw_count = 20)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 8)
    print("\n")
    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    '''
        
    
    #CanDeviceLibrary.MsgRAMTest(m_bar = m_bar)
def can_init_old():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)

    #single Packet
    
    """
    val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1, esync = 0x0, efid2 = 0x1FFFFFFF)
    CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FFFFFFF, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    #CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0) 
    
    """
    
    # Multiple packet
    """
   
    val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1, esync = 0x0, efid2 = 0x1FFF)
    CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1FFFF, esync = 0x0, efid2 = 0x1FFFFF)
    CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 1, filt = val)
    
    val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1FFFFFF, esync = 0x0, efid2 = 0x1FFFFFFF)
    CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 2, filt = val)
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FFE, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FFFFE, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FFFFFFE, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)
    
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 1)
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 2)
    
    
   """
   
    #RX buffer
    
    val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x07, efid1 = 0x1, esync = 0x0, efid2 = 0)
    CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    # val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1FFFF, esync = 0x0, efid2 = 0x1FFFFF)
    # CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 1, filt = val)
    
    # val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1FFFFFF, esync = 0x0, efid2 = 0x1FFFFFFF)
    # CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 2, filt = val)
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    # txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FFFFE, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    # CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    # CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    
    # txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FFFFFFE, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    # CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    # CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)
    
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x07, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    # CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 1)
    # CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 2)
    
    
    print("Reading MsgRAM Extended filter data")
    addr = (0x800 + 0x200)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 100)
    print("\n")
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 200)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 40)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x2800), dw_count = 40)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 140)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 140)
    print("\n")
    
    
    CanDeviceLibrary.ReadFilterPriority(m_bar = m_bar)


    
    print("Reading MsgRAM Rx Filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x200), dw_count = 4)
    print("\n")
    
    



    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
def can_init_extd_filter():
    
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    '''
    print("this is my first sequence")
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 3, rbds = 3, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 0, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x01, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    val = CanDeviceLibrary.create11bitFilter(sft = 1, sfec = 7, sfid1 = 0x01, ssync = 0, sfid2 = 0x0)
    CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    #CanDeviceLibrary.pushTxPacket(m_bar = m_bar, pos = 0, pkt_num = 1, can_id = 0x5A5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, data0 = 0x04030201, data1 = 0x08070605)
    #CanDeviceLibrary.createTxPacket(dw_num = 0, can_id = 0, rtr = 0, xtd = 0, esi = 0, mm = 0, dlc = 0, brs = 0, fdf = 0, tsce = 0, efc = 0, txbuf = [], tx_data = [])
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    #txbuf = CanDeviceLibrary.createTxPacket(can_id=0x114, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 6, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data , pos = 1)
    #CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = 7, pkt_cnt = 0, txbuf = txbuf)
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 7, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    '''
    print("this is my second sequence")
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1fffffff, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 3, rbds = 3, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    '''
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 0, anfs = 0, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    '''
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    txbuf = CanDeviceLibrary.createTxPacket(can_id=15555555, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 6, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)

    #val = CanDeviceLibrary.create11bitFilter(sft = 1, sfec = 7, sfid1 = 0x3d, ssync = 0, sfid2 = 0x0)
    #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x02, efid1 = 0x1, esync = 0x0, efid2 = 0x1FFFFFFF)
    CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 0, filt = val)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 2, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x2800), dw_count = 20)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 8)
    print("\n")
    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    '''
        
    
    #CanDeviceLibrary.MsgRAMTest(m_bar = m_bar)
    
    

def Vector_to_CAN0():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 31
    ntseg2 = 8
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x20)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("send packet from Vector...")
    time.sleep(30)
    
    #txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    #CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x2800), dw_count = 80)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    '''

def Vector_to_CAN1():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    print("send packet from Vector...")
    time.sleep(30)
    
    #txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    #CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    '''
    
    
def Vector_to_CAN1_CAN0():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR values of CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR values of CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x2)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x3, ssync = 0, sfid2 = 0x4)
    CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR values of CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR values of CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    '''
    
    
    

    
def No_Receiver():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 127
    ntseg2 = 32
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
    #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
    #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    
    print("CAN0 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 4)
    print("\n")
    
    
    print("CAN1 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    '''
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)


    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    

def Test_Case_14():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 16
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    efec = 2
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x7;
    sfid1 = 0
    efid1 = 0
    ssync = 0
    sfid2 = 0
    efid2 = 0
    #filt = 0
    val = 0
    
    
    
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = efec, efid1 = 0, esync = 0x0, efid2 = 0x1FFF0000)
    CanDeviceLibrary.push29BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 10, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x3A00), dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 4)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 10)
    print("\n")
    

    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    '''   
    
    
    
    
def Test_Case_21():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    #sfec = random.choice(sfec_values)
    sfec = 2
    efec = 2
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    #can_id = 0x7;
    sfid1 = 0
    efid1 = 0
    ssync = 0
    sfid2 = 0
    efid2 = 0
    #filt = 0
    val = 0
    
    
    
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    #val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = efec, efid1 = 0, esync = 0x0, efid2 = 0x1FFF0000)
    #CanDeviceLibrary.push29BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
    
    #setwatermark
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    
        
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
       
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
               
    txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 3, txbuf = txbuf)
       
    txbuf = CanDeviceLibrary.createTxPacket(can_id=5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 4)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 4, txbuf = txbuf)
    
    for i in range(4):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
    
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
 
  
    
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")  
                   
   
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
    print("IR TxEventFIFO can0_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")  
                      
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
 
    
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR TxEventFIFO - After verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")  
                   
 
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 100)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x3A00), dw_count = 100)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 4)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 10)
    print("\n")  
    
    print("Reading TXEFS")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.TXEFS.offset)
    print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n") 
    
    print("Reading PSR")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
    print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n") 

def arbitration():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    
    '''
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    '''
    

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
 
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x50)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 1, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x50)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 2, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
   
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)  
    
    
    
    '''
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FE, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FD, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
    '''
    CanDeviceLibrary.WriteMmio(m_bar, can0.TXBAR.offset, 0x7)
    
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    

    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
    print("\n")

    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
 
   
    
def can_init_can1_to_can0_ackerror():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    #can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    #print("send packet from Vector...")
    #time.sleep(30)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
    
   
    txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 3, txbuf = txbuf)
    
                          
    txbuf = CanDeviceLibrary.createTxPacket(can_id=5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 4)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 4, txbuf = txbuf)
    
        
    
    for i in range(4):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    
     
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR TxEventFIFO can0_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")    
       
    
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR TxEventFIFO can1_bar - After verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")    
       
    print("Reading TXEFS")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.TXEFS.offset)
    print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n") 
    
    print("Reading PSR")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
    print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n") 
        
    CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    

    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x640), dw_count = 40)
    print("\n")
    
   
    
def Test_Case_21_can1_to_can0_watermark():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)

    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
       
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
    
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 2, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
  
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    
        
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
       
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
    '''     
    txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 3, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 4)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 4, txbuf = txbuf)
    '''
    print("Reading IR TxEventFIFO ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")    
    
    for i in range(3):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)
        
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 120)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 50)
    print("\n")
        
        
    print("Reading IR TxEventFIFO ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")  
    
    '''
    print("Reading IR TxEventFIFO ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR TxEventFIFO can0_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")    
    '''

       
    #CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    CanDeviceLibrary.verify_rx(m_bar = can1_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    
    
    print("Send packets after packets are drined")
    txbuf = CanDeviceLibrary.createTxPacket(can_id=10, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    
    #for i in range(4):
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    '''
    txbuf = CanDeviceLibrary.createTxPacket(can_id=11, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 6)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 6, txbuf = txbuf)
    
    #for i in range(4):
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 6)
    '''
    
    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR after packets are sent ", reg_val_32)
    print("\n")    

        
    
    
    
  
    '''
    print("Reading MsgRAM Extended filter data")
    addr = (0x800 + 0x200)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 8)
    print("\n")
    '''
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 120)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 50)
    print("\n")
    '''
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x2800), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 150)
    print("\n")
    
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR TxEventFIFO - After verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")
    
 
def TX_side_loop_back_watermark():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
  
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    
        
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
       
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
               
    txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 3, txbuf = txbuf)
       
    txbuf = CanDeviceLibrary.createTxPacket(can_id=5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 4)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 4, txbuf = txbuf)
    
    
    
    ##==============================================================================================##   
    ##==================Read TXBRP,TXBTO,TC=============================================## 
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
    print("TXBRP reg_val_32 is :", reg_val_32)

    print("\n")
    print("\n")
        
        
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
    print("TXBTO reg_val_32 is :", reg_val_32)

    print("\n")
    print("\n")
         
        
        
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TC=(reg_val_32 & 0x00000200)>>9
    print("TC  is :", TC)
    print("\n")
    print("\n")
        ##==============================================================================================##   
    
    for i in range(4):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
        
    ##==============================================================================================##   
    ##==================Read TXBRP,TXBTO,TC=============================================## 
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
    print("TXBRP reg_val_32 is :", reg_val_32)

    print("\n")
    print("\n")
        
        
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
    print("TXBTO reg_val_32 is :", reg_val_32)

    print("\n")
    print("\n")
         
        
        
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TC=(reg_val_32 & 0x00000200)>>9
    print("TC  is :", TC)
    print("\n")
    print("\n")
        ##==============================================================================================##   
    
    
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR TxEventFIFO - verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")    
    
    #CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
    #CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=10, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 5)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 5, txbuf = txbuf)
    
    #for i in range(4):
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 5)
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=11, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 6)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 6, txbuf = txbuf)
    
    #for i in range(4):
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 6)
    
    
  
    
    
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR TxEventFIFO - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")    

    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR TxEventFIFO - After verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")      
    
    
    
  
    
    print("Reading MsgRAM Extended filter data")
    addr = (0x800 + 0x200)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 120)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 50)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x2800), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 10)
    print("\n")
    
    print("Reading IR TxEventFIFO TEFL")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR TxEventFIFO - After verify_rx_transceiver. reg_val_32 is", reg_val_32)
    print("\n")
    
    
    

    
def can_init_can1_to_can0_Transceiver():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 5, efwm = 4, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 5, efwm = 4, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    for i in range(6):
        txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf)
    for i in range(6):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)

    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR can0_bar - reg_val_32 is", reg_val_32)
    print("\n")    
    
    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR can1_bar - reg_val_32 is", reg_val_32)
    print("\n")  
   
    print("Reading TXEFS ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXEFS.offset)
    print("TXEFS can1_bar - Before verify_rx_tranceiver reg_val_32 is", reg_val_32)
    print("\n")  
        
    CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf, pos=0)
    #CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf, pos=0)
  
    print("Reading TXEFS ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXEFS.offset)
    print("TXEFS can1_bar - After verify_rx_tranceiver reg_val_32 is", reg_val_32)
    print("\n")  
            
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 40)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x2800), dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 40)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x640), dw_count = 4)
    print("\n")    
    
    
    for i in range(1):
        txbuf = CanDeviceLibrary.createTxPacket(can_id=i+8, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf)
    for i in range(1):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)    

  
    print("Reading TXEFS ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXEFS.offset)
    print("TXEFS can1_bar - After verify_rx_tranceiver reg_val_32 is", reg_val_32)
    print("\n")  
            
    
    print("Reading MsgRAM Tx Buffer - After send some more packets")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 100)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 60)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x2800), dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 100)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x640), dw_count = 50)
    print("\n")    
    
    
    
def can_init_can0_to_can1_Transceiver():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 5, efwm = 4, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 5, efwm = 4, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    for i in range(6):
        txbuf = CanDeviceLibrary.createTxPacket(can_id=i+2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf)
    for i in range(6):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)

    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR can0_bar - reg_val_32 is", reg_val_32)
    print("\n")    
    
    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR can1_bar - reg_val_32 is", reg_val_32)
    print("\n")  
   
    print("Reading TXEFS ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXEFS.offset)
    print("TXEFS can1_bar - Before verify_rx_tranceiver reg_val_32 is", reg_val_32)
    print("\n")  
        
    CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf, pos=0)
    #CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf, pos=0)
  
    print("Reading TXEFS ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXEFS.offset)
    print("TXEFS can1_bar - After verify_rx_tranceiver reg_val_32 is", reg_val_32)
    print("\n")  
            
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 80)
    print("\n")
    
    '''
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 40)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x2800), dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 40)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x640), dw_count = 4)
    print("\n")    
    '''
    
    for i in range(1):
        txbuf = CanDeviceLibrary.createTxPacket(can_id=i+8, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf)
    for i in range(1):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)    

  
    print("Reading TXEFS ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXEFS.offset)
    print("TXEFS can1_bar - After verify_rx_tranceiver reg_val_32 is", reg_val_32)
    print("\n")  
            
    
    print("Reading MsgRAM Tx Buffer - After send some more packets")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 100)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 60)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x2800), dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 100)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x640), dw_count = 50)
    print("\n")    
    
    
    
       

    
def Test_case_22_can_init_can1_to_can0_Transceiver_at_Rx_side():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    '''
    ##============Venkat added to check inturrupt is working======#
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, 0x508)
    print("INTR_CTRL is :", reg_val_32)
    reg_val_32= 0x00000001
    CanDeviceLibrary.WriteMmio(m_bar, 0x508, reg_val_32)
    
    ##======================================================#
    '''
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 3, rxf1c = 0, rxf1c_elements = 3, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 32, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 3, rxf1c = 0, rxf1c_elements = 3, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 32, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    for i in range(5):
        txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf)
    for i in range(5):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)

    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR can0_bar - reg_val_32 is", reg_val_32)
    print("\n")    
    
    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR can1_bar - reg_val_32 is", reg_val_32)
    print("\n")  
   
    print("Reading RXF0S ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.RXF0S.offset)
    print("TXEFS can1_bar - Before verify_rx_tranceiver reg_val_32 is", reg_val_32)
    print("\n")  
        
    CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf, pos=0)
    #CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf, pos=0)
  
    print("Reading RXF0S ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.RXF0S.offset)
    print("TXEFS can1_bar - After verify_rx_tranceiver reg_val_32 is", reg_val_32)
    print("\n")
    
    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR can0_bar - reg_val_32 is", reg_val_32)
    print("\n")     
            
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 40)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x2800), dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")    
    
def Test_case_7_Parity_Check_messageram_with_clearing():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #Step 1: Verify Parity enabled/Disabled by default
    print("#Step 1: Verify Parity enabled/Disabled by default")
    print("Reading Paity PAR_CTL_STAT ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
    print("Reading PAR_CTL_STAT", reg_val_32)
    print("\n") 
    print("\n")

    #Step 2: Set Error injection enable and injection mode
    print("#Step 2: Set Error injection enable and injection mode")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
    reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #one-time error
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
    print("\n") 
    print("\n")     

    
    #Step 3: Set offset and Error injection data mask
    print("#Step 3: Set offset and Error injection data mask")    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    reg_val_32 = ((reg_val_32 & 0xFFFF0000) | 0x00000800)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    print("Reading PAR_EINJ_OFFSET value", reg_val_32)
    print("\n") 
    print("\n") 
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x10000000)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
    print("Read PAR_EINJ_DATA_MASK", reg_val_32)
    print("\n") 
    print("\n")     

    #Step 4: configure 11 bit filter
    print("#Step 4: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n")      
    
    #Step 5: Read one-time error occured
    print("#Step 5: Read one-time error occured")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
    print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
    print("\n") 
    
    #Step 6: Read stored offset value is correct
    print("#Step 6: Read stored offset value is correct")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
    print("Reading PAR_ERR_OFFSET to see in which offset error has occured", reg_val_32)
    print("\n")    
 
    #Step 7: Read PERR_OCCURED=1
    print("#Step 7: Read PERR_OCCURED=1 ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
    print("Read PERR_OCCURED=1", reg_val_32)
    print("\n")   
    
    #Step 8: Read EINJ_EN deasserts    
    print("#Step 8: Read EINJ_EN deasserts")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
    print("\n")

    #Step 9: set EINJ_EN=1 to clear one-time error
    print("#Step 9: set EINJ_EN=1 to clear one-time error")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
    reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #one-time error
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
    print("\n") 
    print("\n")     

    #Step 10: Repeat steps 3 and 4
    print("#Step 10: Repeat steps 3 and 4")
    print("Set offset and Error injection data mask")    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    reg_val_32 = ((reg_val_32 & 0xFFFF0000) | 0x00000800)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    print("Reading PAR_EINJ_OFFSET value", reg_val_32)
    print("\n") 
    print("\n") 
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x10000000)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
    print("Read PAR_EINJ_DATA_MASK", reg_val_32)
    print("\n") 
    print("\n")     

    #Step 11: configure 11 bit filter
    print("#Step 11: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n")      
    
    #Step 12: Read one-time error not occured
    print("#Step 12: Read one-time error not occured")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
    print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)#value=0
    print("\n") 
    
    #Step 13: Read stored offset value is stored
    print("#Step 13: Read stored offset value is stored")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
    print("Read stored offset value", reg_val_32)
    print("\n")    
 
    #Step 14: Read PERR_OCCURED not occured
    print("#Step 14: Read PERR_OCCURED not occured ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
    print("Read PERR_OCCURED not occured", reg_val_32)
    print("\n")   
    
    
def Test_case_7_one_time_error_injection():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    
    print("#By default PAR_EINJ_DATA_MASK- check values of PAR_EINJ_DATA_MASK =0  " )
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset) 
    print("Read PAR_EINJ_DATA_MASK", reg_val_32)
    print("\n") 
    print("\n")
    
    #Step 1: Verify Parity enabled/Disabled by default
    print("#Step 1: Verify Parity enabled/Disabled by default")
    print("Reading Paity PAR_CTL_STAT ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
    print("Reading PAR_CTL_STAT", reg_val_32)
    print("\n") 
    print("\n")
    
    #Step 2: configure 11 bit filter
    print("#Step 2: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n")     
    
    


    #Step 3: Set Error injection enable and injection mode
    print("#Step 3: Set Error injection enable and injection mode")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
    reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #one-time error
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
    print("\n") 
    print("\n")     

    
    #Step 4: Set offset and Error injection data mask
    print("#Step 4: Set offset and Error injection data mask")    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    reg_val_32 = ((reg_val_32 & 0xFFFF0000) | 0x00000800)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    print("Reading PAR_EINJ_OFFSET value", reg_val_32)
    print("\n") 
    print("\n")
    
    '''
    #Step 5: Dont configure PAR_EINJ_DATA_MASK
    print("#Step 5:Dont configure PAR_EINJ_DATA_MASK- check values of PAR_EINJ_DATA_MASK =0  " )
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset) 
    print("Read PAR_EINJ_DATA_MASK", reg_val_32)
    print("\n") 
    print("\n")
    '''
    #Step 5: configure PAR_EINJ_DATA_MASK
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x10000000)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
    print("Read PAR_EINJ_DATA_MASK", reg_val_32)
    print("\n") 
    print("\n")     
    

    #Step 6: configure 11 bit filter
    print("#Step 6: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n")      
    
    #Step 7: Read one-time error occured
    print("#Step 7: Read one-time error occured")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
    print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
    print("\n") 
    
    #Step 8: Read stored offset value is correct
    print("#Step87: Read stored offset value is correct")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
    print("Reading PAR_ERR_OFFSET to see in which offset error has occured", reg_val_32)
    print("\n")    
 
    #Step 9: Read PERR_OCCURED=1
    print("#Step 9: Read PERR_OCCURED=1 ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
    print("Read PERR_OCCURED=1", reg_val_32)
    print("\n") 

    '''
    #Step A: Read IR.BEU
    print("#Step 9: R.BEU ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset) >>2
    print("Read IR.BEU", reg_val_32)
    print("\n")    
    
    #Step B: Read CCCR.INIT
    print("#Step 9: CCCR.INIT ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset) >>2
    print("Read CCCR.INIT", reg_val_32)
    print("\n") 
    '''
    #Step 10: Read EINJ_EN deasserts    
    print("#Step 10: Read EINJ_EN deasserts")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
    print("\n")

   

    #Step 11: configure 11 bit filter
    print("#Step 11: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n") 


    #Step 12: configure 11 bit filter
    print("#Step 12: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n") 

    #Step 13: configure 11 bit filter
    print("#Step 13: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n") 

  
    
    #Step 13: Read one-time error not occured
    print("#Step 13: Read one-time error not occured")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
    print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
    print("\n") 
    
    #Step 13: Read stored offset value is stored
    print("#Step 13: Read stored offset value is stored")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
    print("Read stored offset value", reg_val_32)
    print("\n")    
 
    #Step 14: Read PERR_OCCURED not occured
    print("#Step 14: Read PERR_OCCURED not occured ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
    print("Read PERR_OCCURED not occured", reg_val_32)
    print("\n")  

def Test_case_7_continuous_error_injection():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #Step 1: Verify Parity enabled/Disabled by default
    print("#Step 1: Verify Parity enabled/Disabled by default")
    print("Reading Paity PAR_CTL_STAT ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
    print("Reading PAR_CTL_STAT", reg_val_32)
    print("\n") 
    print("\n")
    
    #Step 2: configure 11 bit filter
    print("#Step 2: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n")     
    
    


    #Step 3: Set Error injection enable and injection mode
    print("#Step 3: Set Error injection enable and injection mode")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
    reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #one-time error
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
    print("\n") 
    print("\n")     

    
    #Step 4: Set offset and Error injection data mask
    print("#Step 4: Set offset and Error injection data mask")    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    reg_val_32 = ((reg_val_32 & 0xFFFF0000) | 0x00000800)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    print("Reading PAR_EINJ_OFFSET value", reg_val_32)
    print("\n") 
    print("\n") 
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00000001)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
    print("Read PAR_EINJ_DATA_MASK", reg_val_32)
    print("\n") 
    print("\n")     

    #Step 5: configure 11 bit filter
    print("#Step 5: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n")      
    
    #Step 6: Read one-time error occured
    print("#Step 6: Read one-time error occured")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
    print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
    print("\n") 
    
    #Step 7: Read stored offset value is correct
    print("#Step 7: Read stored offset value is correct")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
    print("Reading PAR_ERR_OFFSET to see in which offset error has occured", reg_val_32)
    print("\n")    
 
    #Step 8: Read PERR_OCCURED=1
    print("#Step 8: Read PERR_OCCURED=1 ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
    print("Read PERR_OCCURED=1", reg_val_32)
    print("\n")   
    
   

    #Step 9: configure 11 bit filter
    print("#Step 9: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n") 


    #Step 10: configure 11 bit filter
    print("#Step 10: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n") 

    #Step 11: configure 11 bit filter
    print("#Step 11: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 0, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    print("Reading MsgRAM 11 bit filter")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
    print("\n") 

  

    #Step 12: Read stored offset value is stored
    print("#Step 12: Read stored offset value is stored")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
    print("Read stored offset value", reg_val_32)
    print("\n")    
 
    #Step 13: Read PERR_OCCURED not occured
    print("#Step 13: Read PERR_OCCURED not occured ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
    print("Read PERR_OCCURED not occured", reg_val_32)
    print("\n")    
 
def Test_case_33_continuous_error_injection_4300():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #Step 1: Verify Parity enabled/Disabled by default
    print("#Step 1: Verify Parity enabled/Disabled by default")
    print("Reading Paity PAR_CTL_STAT ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
    print("Reading PAR_CTL_STAT", reg_val_32)
    print("\n") 
    print("\n")
    
    #Step 2: configure 11 bit filter and create TX packet
    print("#Step 2: configure 11 bit filter")
    

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf) 
    for i in range(3):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        print("\n")
        print("\n")
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 20)
        print("\n")
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 20)
        print("\n")
        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 20)
        print("\n")
        print("\n")
        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")       



        #Step 3: Set Error injection enable and injection mode
        print("#Step 3: Set Error injection enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #one-time error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        print("\n") 
        print("\n")     

        
        #Step 4: Set offset and Error injection data mask
        print("#Step 4: Set offset and Error injection data mask")    
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | 0x00004300)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00000001)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     


        #Step 5: check packet is not received at FIFO 0
        print("#Step 5: check packet is not received at FIFO 0")
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
        #print("Reading MsgRAM 11 bit filter")
        #CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800), dw_count = 8)
        #print("\n") 
        txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)    
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        print("\n")
        print("\n")
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 20)
        print("\n")
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 20)
        print("\n")
        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 20)
        print("\n")
          
        '''
        #Step 6: Read one-time error occured
        print("#Step 6: Read one-time error occured")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
        print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
        print("\n") 
        '''
        #Step 7: Read stored offset value is correct
        print("#Step 7: Read stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
        print("Reading PAR_ERR_OFFSET to see in which offset error has occured", reg_val_32)
        print("\n")    
     
        #Step 8: Read PERR_OCCURED=1
        print("#Step 8: Read PERR_OCCURED=1 ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED=1", reg_val_32)
        print("\n")   
        
        #Step 9: Read EINJ_EN deasserts    
        print("#Step 9: Read EINJ_EN deasserts")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        print("\n")

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")       

def Test_case_33_continuous_error_injection_4308():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #Step 1: Verify Parity enabled/Disabled by default
    print("#Step 1: Verify Parity enabled/Disabled by default")
    print("Reading Paity PAR_CTL_STAT ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
    print("Reading PAR_CTL_STAT", reg_val_32)
    print("\n") 
    print("\n")
    
    #Step 2: configure 11 bit filter and create TX packet
    print("#Step 2: configure 11 bit filter")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 3, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 4, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 5, txbuf = txbuf)

    for i in range(5):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
     

    for i in range(5): 
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = i)
    print("\n")
    print("\n")
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    print("\n")
    print("Reading CCCR.INIT")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
    print("Reading CCCR.INIT", reg_val_32)
    print("\n")       



    #Step 3: Set Error injection enable and injection mode
    print("#Step 3: Set Error injection enable and injection mode")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
    reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #one-time error
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
    print("\n") 
    print("\n")     

    
    #Step 4: Set offset and Error injection data mask
    print("#Step 4: Set offset and Error injection data mask")    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    reg_val_32 = ((reg_val_32 & 0xFFFF0000) | 0x00004308)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
    print("Reading PAR_EINJ_OFFSET value", reg_val_32)
    print("\n") 
    print("\n") 
    
    
    CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00000001)
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
    print("Read PAR_EINJ_DATA_MASK", reg_val_32)
    print("\n") 
    print("\n")     


    #Step 5: check packet is not received at FIFO 0
    print("#Step 5: check packet is not received at FIFO 0")
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
 
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 3, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 4, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=5, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 5, txbuf = txbuf)

    for i in range(5):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
     

    for i in range(5): 
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = i)
        
    print("\n")
    print("\n")
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 20)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 20)
    print("\n")
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 20)
    print("\n")
      
    '''
    #Step 6: Read one-time error occured
    print("#Step 6: Read one-time error occured")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
    print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
    print("\n") 
    '''
    #Step 7: Read stored offset value is correct
    print("#Step 7: Read stored offset value is correct")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
    print("Reading PAR_ERR_OFFSET to see in which offset error has occured", reg_val_32)
    print("\n")    
 
    #Step 8: Read PERR_OCCURED=1
    print("#Step 8: Read PERR_OCCURED=1 ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
    print("Read PERR_OCCURED=1", reg_val_32)
    print("\n")   
    
    #Step 9: Read EINJ_EN deasserts    
    print("#Step 9: Read EINJ_EN deasserts")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
    print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
    print("\n")

    print("Reading CCCR.INIT")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
    print("Reading CCCR.INIT", reg_val_32)
    print("\n")       

def seed0_Test_case_7_CAN0_Continuous_error_injection_Randamization():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    
    from random import seed
    for i in range (1):
        seed_id = i
        seed(seed_id)
        addr_list = range(0x800,0x4781,0x4)
        addr_val = random.choice(addr_list)
        #addr_val = hex(addr_dec).split('x')[-1]
        data = random.randint(1,65535)
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        
        

        print("SEED_ID is",seed_id)
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        print("\n") 
        print("\n")
        

        
        


        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #continuous error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000003
        print("\n") 
        print("\n")     

        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask")    
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | addr_val)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00000001)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     


        
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)        
        print("Written data is ", data_hex, "for address", hex(addr_val))
        print("\n") 
 
        if (addr_val != 0x800):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val-4), data_previous)
            print("Written data at previous address is ", data_hex_previous, "for address", hex(addr_val-4))
            print("\n")
        if (addr_val != 0x4780):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val+4), data_next)
            print("Written data at Next address is ", (data_hex_next), "for address", hex(addr_val+4))
            print("\n")        
        
        '''
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different during 1st ERR Injection for addr_val. Written data is", data_hex, "Read data is", hex(Read_data) )
        else:
            print("PASS")
        print("\n")
        
        if (addr_val != 0x800):               
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val-4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val-4))
            if (data_hex_previous !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val-4. Written data is", data_hex_previous, "Read data is", hex(Read_data) )
            print("\n")
        else:
            print("PASS")        
            
        if (addr_val != 0x4780):
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val+4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val+4))        
            if (data_hex_next !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val+4. Written data is", data_hex_next, "Read data is", hex(Read_data))
            print("\n")       
        else:
            print("PASS")                  
 
        '''
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different during 1st ERR Injection for addr_val. Written data is", data_hex, "Read data is", hex(Read_data) )
        else:
            print("PASS")
        print("\n")
        
        if (addr_val != 0x800):               
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val-4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val-4))
            if (data_hex_previous ==hex(Read_data)):
                print("FAIL:written data and Read data are not different in adjacent addr_val-4. Written data is", data_hex_previous, "Read data is", hex(Read_data) )
            print("\n")
        else:
            print("PASS")        
            
        if (addr_val != 0x4780):
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val+4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val+4))        
            if (data_hex_next ==hex(Read_data)):
                print("FAIL:written data and Read data are not different in adjacent addr_val+4. Written data is", data_hex_next, "Read data is", hex(Read_data))
            print("\n")       
        else:
            print("PASS")   
        
        
        
        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        reg_val_32 = reg_val_32 & 0x00003FFF
        
        
        if (reg_val_32 != offset_Value):
            print("FAIL: Stored offset value != injected offset value")
        else:
            print("PASS")
           
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("PASS:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")         


                    

        

        
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different in 2nd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
       
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)  ):
            print("FAIL:written data and Read data are not different in 3rd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
        
def adjacent_check_Test_case_7_CAN0_Continuous_error_injection_Randamization():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    
    from random import seed
    for i in range (1):
        seed_id = i
        seed(seed_id)
        addr_list = range(0x800,0x4781,0x4)
        addr_val = random.choice(addr_list)
        #addr_val = hex(addr_dec).split('x')[-1]
        data = random.randint(1,65535)
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        
        

        print("SEED_ID is",seed_id)
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        print("\n") 
        print("\n")
        
        ##==================================Read adjacent offsets===========================================##
        

        ##==================================write adjacent offsets===========================================##
        if (addr_val != 0x800):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val-4), data_previous)
            print("Written data at previous address is ", data_hex_previous, "for address", hex(addr_val-4))
            print("\n")
        if (addr_val != 0x4780):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val+4), data_next)
            print("Written data at Next address is ", (data_hex_next), "for address", hex(addr_val+4))
            print("\n")        
        ##====================================================================================##
        


        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #continuous error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000003
        print("\n") 
        print("\n")     

        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask")    
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | addr_val)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00000001)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n") 
        

        ##=====================Write offset to which parity to be injected======================##
        
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)        
        print("Written data is ", data_hex, "for address", hex(addr_val))
        print("\n") 
        ##=======================================================================================##
        
        
        
        ##=============Read adjacent offsets===================================##
        
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different during 1st ERR Injection for addr_val. Written data is", data_hex, "Read data is", hex(Read_data) )
        else:
            print("PASS")
        print("\n")
        
        if (addr_val != 0x800):               
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val-4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val-4))
            if (data_hex_previous ==hex(Read_data)):
                print("FAIL:written data and Read data are not different in adjacent addr_val-4. Written data is", data_hex_previous, "Read data is", hex(Read_data) )
            print("\n")
        else:
            print("PASS")        
            
        if (addr_val != 0x4780):
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val+4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val+4))        
            if (data_hex_next ==hex(Read_data)):
                print("FAIL:written data and Read data are not different in adjacent addr_val+4. Written data is", data_hex_next, "Read data is", hex(Read_data))
            print("\n")       
        else:
            print("PASS")   
        
        
        
      ##=======================================================================================================##   
        
        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        reg_val_32 = reg_val_32 & 0x00003FFF
        
        '''
        if (reg_val_32 != offset_Value):
            print("FAIL: Stored offset value != injected offset value")
        else:
            print("PASS")
        '''
        
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("PASS:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")         


                    

        

        
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different in 2nd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
       
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)  ):
            print("FAIL:written data and Read data are not different in 3rd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##       
        


        
def Test_case_7_CAN0_one_time_error_injection_Randamization():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    
    from random import seed
    for i in range (0,1):
        seed_id = i
        seed(seed_id)
        addr_list = range(0x800,0x4781,0x4)
        addr_val = random.choice(addr_list)
        #addr_val = hex(addr_dec).split('x')[-1]
        data = random.randint(1,65535)
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        
        

        print("SEED_ID is",seed_id)
        '''
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffB) | 1)
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_CTL_STAT.offset, reg_val_32)
        CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("PAR_CTL_STAT is", reg_val_32)
        
        '''
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        print("\n") 
        print("\n")
       
        if (addr_val != 0x800):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val-4), data_previous)
            print("Written data at previous address is ", data_hex_previous, "for address", hex(addr_val-4))
            print("\n")
        if (addr_val != 0x4780):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val+4), data_next)
            print("Written data at Next address is ", (data_hex_next), "for address", hex(addr_val+4))
            print("\n")  
        
        


        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #one-time error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        print("\n") 
        print("\n")     

        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask")    
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | addr_val)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00000001)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     


        ##==============================Reading Adjacent memories=================================================##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)        
        print("Written data is ", data_hex, "for address", hex(addr_val))
        print("\n") 
 
      
        
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different during 1st ERR Injection for addr_val")
        else:
            print("PASS")
        print("\n")
        
        if (addr_val == 0x800):               
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val-4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val-4))
            if (data_hex_previous !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val-4", )
            print("\n")
        else:
            print("PASS")        
            
        if (addr_val == 0x4780):
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val+4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val+4))        
            if (data_hex_next !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val+4")
            print("\n")       
        else:
            print("PASS")                  
        
        #Step 4: Read one-time error occured
        print("#Step 4: Read one-time ERR_OCCURED")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
        print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT.EINJ_ONE_TIME_ERR_OCCURED!= 1")
        else:
            print("PASS")       
        
        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        reg_val_32 = reg_val_32 & 0x00003FFF
        
        '''
        if (reg_val_32 != offset_Value):
            print("FAIL: Stored offset value != injected offset value")
        else:
            print("PASS")
        '''  
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("PASS:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")         
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        print("\n")

                    
        print("\n")
        #Compare function
        
        print("\n")
        print("\n")
        
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not same in 2nd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
       
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)  ):
            print("FAIL:written data and Read data are not same in 3rd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffB) | 1)
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_CTL_STAT.offset, reg_val_32)
        CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("PAR_CTL_STAT is", reg_val_32)
        



               
def Test_case_7_CAN1_one_time_error_injection_Randamization():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can1_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    
    from random import seed
    for i in range (0,2):
        seed_id = i
        seed(seed_id)
        addr_list = range(0x800,0x4781,0x4)
        addr_val = random.choice(addr_list)
        #addr_val = hex(addr_dec).split('x')[-1]
        data = random.randint(1,65535)
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        
        

        
        print("SEED_ID is",seed_id)
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        print("\n") 
        print("\n")
        
        if (addr_val != 0x800):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val-4), data_previous)
            print("Written data at previous address is ", data_hex_previous, "for address", hex(addr_val-4))
            print("\n")
        if (addr_val != 0x4780):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val+4), data_next)
            print("Written data at Next address is ", (data_hex_next), "for address", hex(addr_val+4))
            print("\n")        
        
        


        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #one-time error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        print("\n") 
        print("\n")     

        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask")    
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | addr_val)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00000001)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     

  
        
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)        
        print("Written data is ", data_hex, "for address", hex(addr_val))
        print("\n") 
 
    
        
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different during 1st ERR Injection for addr_val")
        else:
            print("PASS")
        print("\n")
        
        if (addr_val != 0x800):               
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val-4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val-4))
            if (data_hex_previous !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val-4", )
            print("\n")
        else:
            print("PASS")        
            
        if (addr_val != 0x4780):
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val+4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val+4))        
            if (data_hex_next !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val+4")
            print("\n")       
        else:
            print("PASS")                  
        
        #Step 4: Read one-time error occured
        print("#Step 4: Read one-time ERR_OCCURED")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
        print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT.EINJ_ONE_TIME_ERR_OCCURED!= 1")
        else:
            print("PASS")       
        
        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        reg_val_32 = reg_val_32 & 0x00003FFF
        '''
        if (reg_val_32 != offset_Value):
            print("FAIL: Stored offset value != injected offset value")
        else:
            print("PASS")
        ''' 
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("PASS:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")   
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        print("\n")

                    
        print("\n")
        #Compare function
        
        print("\n")
        print("\n")
        
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex !=hex(Read_data)):
            print("FAIL:written data and Read data are not same in 2nd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
       
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex !=hex(Read_data)  ):
            print("FAIL:written data and Read data are not same in 3rd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
        
        
def Test_case_7_CAN0_Continuous_error_injection_Randamization():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    
    from random import seed
    for i in range (0,2):
        seed_id = i
        seed(seed_id)
        addr_list = range(0x800,0x4781,0x4)
        addr_val = random.choice(addr_list)
        #addr_val = hex(addr_dec).split('x')[-1]
        data = random.randint(1,65535)
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        
        

        print("SEED_ID is",seed_id)
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        print("\n") 
        print("\n")
        

        if (addr_val != 0x800):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val-4), data_previous)
            print("Written data at previous address is ", data_hex_previous, "for address", hex(addr_val-4))
            print("\n")
        if (addr_val != 0x4780):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val+4), data_next)
            print("Written data at Next address is ", (data_hex_next), "for address", hex(addr_val+4))
            print("\n")        
                
        


        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #continuous error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000003
        print("\n") 
        print("\n")     

        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask")    
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | addr_val)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00000001)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     


        
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)        
        print("Written data is ", data_hex, "for address", hex(addr_val))
        print("\n") 
        
         
 
        
        ##=============================================================##
        
        
        '''
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different during 1st ERR Injection for addr_val. Written data is", data_hex, "Read data is", hex(Read_data) )
        else:
            print("PASS")
        print("\n")
        
        if (addr_val != 0x800):               
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val-4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val-4))
            if (data_hex_previous !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val-4. Written data is", data_hex_previous, "Read data is", hex(Read_data) )
            print("\n")
        else:
            print("PASS")        
            
        if (addr_val != 0x4780):
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val+4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val+4))        
            if (data_hex_next !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val+4. Written data is", data_hex_next, "Read data is", hex(Read_data))
            print("\n")       
        else:
            print("PASS")                  
 
        '''
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different during 1st ERR Injection for addr_val. Written data is", data_hex, "Read data is", hex(Read_data) )
        else:
            print("PASS")
        print("\n")
        
        if (addr_val != 0x800):               
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val-4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val-4))
            if (data_hex_previous ==hex(Read_data)):
                print("FAIL:written data and Read data are not different in adjacent addr_val-4. Written data is", data_hex_previous, "Read data is", hex(Read_data) )
            print("\n")
        else:
            print("PASS")        
            
        if (addr_val != 0x4780):
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val+4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val+4))        
            if (data_hex_next ==hex(Read_data)):
                print("FAIL:written data and Read data are not different in adjacent addr_val+4. Written data is", data_hex_next, "Read data is", hex(Read_data))
            print("\n")       
        else:
            print("PASS")   
        
        
        
        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        reg_val_32 = reg_val_32 & 0x00003FFF
        
        '''
        if (reg_val_32 != offset_Value):
            print("FAIL: Stored offset value != injected offset value")
        else:
            print("PASS")
        '''   
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("PASS:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")         


                    

        

        
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different in 2nd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
       
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)  ):
            print("FAIL:written data and Read data are not different in 3rd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
        
        
        
def Test_case_7_CAN1_Continuous_error_injection_Randamization():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can1_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    
    from random import seed
    for i in range (0,2):
        seed_id = i
        seed(seed_id)
        addr_list = range(0x800,0x4781,0x4)
        addr_val = random.choice(addr_list)
        #addr_val = hex(addr_dec).split('x')[-1]
        data = random.randint(1,65535)
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        
        

        print("SEED_ID is",seed_id)
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        print("\n") 
        print("\n")
        

        
        


        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #continuous error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000003
        print("\n") 
        print("\n")     

        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask")    
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | addr_val)#EINJ_OFFSET = 0x800 for error injection enable ,EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00000001)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     


        
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)        
        print("Written data is ", data_hex, "for address", hex(addr_val))
        print("\n") 
 
        if (addr_val != 0x800):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val-4), data_previous)
            print("Written data at previous address is ", data_hex_previous, "for address", hex(addr_val-4))
            print("\n")
        if (addr_val != 0x4780):
            CanDeviceLibrary.WriteMmio(m_bar, (addr_val+4), data_next)
            print("Written data at Next address is ", (data_hex_next), "for address", hex(addr_val+4))
            print("\n")        
        
        '''
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different during 1st ERR Injection for addr_val. Written data is", data_hex, "Read data is", hex(Read_data) )
        else:
            print("PASS")
        print("\n")
        
        if (addr_val != 0x800):               
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val-4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val-4))
            if (data_hex_previous !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val-4. Written data is", data_hex_previous, "Read data is", hex(Read_data) )
            print("\n")
        else:
            print("PASS")        
            
        if (addr_val != 0x4780):
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val+4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val+4))        
            if (data_hex_next !=hex(Read_data)):
                print("FAIL:written data and Read data are not same during 1st ERR Injection in addr_val+4. Written data is", data_hex_next, "Read data is", hex(Read_data))
            print("\n")       
        else:
            print("PASS")                  
 
        '''
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different during 1st ERR Injection for addr_val. Written data is", data_hex, "Read data is", hex(Read_data) )
        else:
            print("PASS")
        print("\n")
        
        if (addr_val != 0x800):               
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val-4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val-4))
            if (data_hex_previous ==hex(Read_data)):
                print("FAIL:written data and Read data are not different in adjacent addr_val-4. Written data is", data_hex_previous, "Read data is", hex(Read_data) )
            print("\n")
        else:
            print("PASS")        
            
        if (addr_val != 0x4780):
            Read_data = CanDeviceLibrary.ReadMmio(m_bar, (addr_val+4))
            print("Read data is ", hex(Read_data), "for address", hex(addr_val+4))        
            if (data_hex_next ==hex(Read_data)):
                print("FAIL:written data and Read data are not different in adjacent addr_val+4. Written data is", data_hex_next, "Read data is", hex(Read_data))
            print("\n")       
        else:
            print("PASS")   
        
        
        
        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        reg_val_32 = reg_val_32 & 0x00003FFF
        '''
        if (reg_val_32 != offset_Value):
            print("FAIL: Stored offset value != injected offset value")
        else:
            print("PASS")
        '''   
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("PASS:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")         


                    

        

        
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)):
            print("FAIL:written data and Read data are not different in 2nd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
       
        ##=============================================== ##
        CanDeviceLibrary.WriteMmio(m_bar, addr_val, data)
        print("Written data is ", (data_hex), "for address", hex(addr_val))        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, addr_val)
        print("Read data is ", hex(Read_data), "for address", hex(addr_val))
        if (data_hex ==hex(Read_data)  ):
            print("FAIL:written data and Read data are not different in 3rd ERR Injection")
        else:
            print("PASS")            
        ##=============================================== ##
        




        
def Test_case_33_data_pkt_CAN0_continuous_error_injection_Randamization_loopback():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #TODO: create11bitFilter
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    #TODO: Push11bitFilter

    
    from random import seed
    for i in range (0,1):
        seed_id = i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
        
        '''
         ##===============adjacent offsets===============================##
        data = random.randint(1,65535)
        
       
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        ##===============================================================##
        '''

        
       
        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
      
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
		##=====================================Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf) 

        #for i in range (0,5):
        #    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
        #####==============Clear msg RAM================================#
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #####==============================================#
        
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #continuous error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x3):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")  
        
        #####==============================================#

        addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = m_bar, pos = 2)
        print("addr_val is", addr_val)
        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask") 
        reg_val_32 = 0
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (m_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00040000)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf) 
        for i in range (0,5):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
        '''
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset, txbuf = txbuf) 
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset)
            
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset)
        '''
  
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        
        ##======================================================================================##
         
         
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        ##==============Verify Packets are dropped from 3rd packets after parity ERR_ING==============##
        ##=====Verify at 0x90, 0x0D8,0x120 addresses as 1 packet takes 0x48 size(its based on RX FIFO elements size)====##
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x90))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        


        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0xD8))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x120))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        ##=============================================================================================##



        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")  

        
        ##========================Read IR=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)

        reg_val_32 = reg_val_32 & 0x0000FFFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        
       
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")

        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN will not deasserts-after 1st time EINJ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:EINJ_EN= 1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")      
        
        time.sleep(5)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFFFFFE) | (0x0))
        #reg_val_32 = ((reg_val_32 & 0xFFFFBFFF) | (0x1 << 14)) #TXP_Pause
    
        CanDeviceLibrary.WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print(" ******IMP*******CCCR reg_val_32 is :", reg_val_32)
        

    
        

        #===============Packets creating 2nd time to check the behaviour============== #

        print("Packets creating again for 2nd time to check one time behaviour working after EINJ deassertion" )
        print("\n")
                    
        print("\n")
        
        
        #for i in range (0,5):
        print("send 0x7FF-ID" )
        txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        
        
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf) 
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
            


        print("Reading MsgRAM Tx Buffer for 2nd time")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 300)
        print("\n")

        print("Reading MsgRAM RxFiFo0 for 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 300)
        print("\n")
        
        
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts- after msg read")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x01):
            print("FAIL:EINJ_EN= 1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")                                

                       
       
 
               
               
               
               
def Test_case_33_data_pkt_CAN0_one_time_error_injection_Randamization_loopback():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #TODO: create11bitFilter
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    #TODO: Push11bitFilter

    
    from random import seed
    for seed_i in range (0,1):
        seed_id = seed_i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
        
        '''
         ##===============adjacent offsets===============================##
        data = random.randint(1,65535)
        
       
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        ##===============================================================##
        '''

        
       
        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
      
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
		##=====================================Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf) 

        #for i in range (0,5):
        #    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
        #####==============Clear msg RAM================================#
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #####==============================================#
        
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #continuous error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")  
        
        #####==============================================#

        addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = m_bar, pos = 2)
        print("addr_val is", addr_val)
        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask") 
        reg_val_32 = 0
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (m_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00040000)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf) 
        for i in range (0,5):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
        '''
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset, txbuf = txbuf) 
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset)
            
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset)
        '''
  
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        
        ##======================================================================================##
         
         
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        '''
        ##==============Verify Packets are dropped from 3rd packets after parity ERR_ING==============##
        ##=====Verify at 0x90, 0x0D8,0x120 addresses as 1 packet takes 0x48 size(its based on RX FIFO elements size)====##
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x90))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        


        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0xD8))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x120))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        ##=============================================================================================##
        '''


        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
        ##========================Read IR=======================================##
        
        
        

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)

        reg_val_32 = reg_val_32 & 0x0000FFFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        
       
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")  


        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts-after EINJ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
        time.sleep(5)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))
        #reg_val_32 = ((reg_val_32 & 0xFFFFBFFF) | (0x1 << 14)) #TXP_Pause
    
        CanDeviceLibrary.WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print(" ******IMP*******CCCR reg_val_32 is :", reg_val_32)
         
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
            
        #====================================================================================== #
        #===============Packets creating 2nd time to check the behaviour============== #

        print("Packets creating again for 2nd time to check one time behaviour working after EINJ deassertion" )
        
        print("\n")
                    
        print("\n")
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
            


        print("Reading MsgRAM Tx Buffer for 2nd time")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 250)
        print("\n")

        print("Reading MsgRAM RxFiFo0 for 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 250)
        print("\n")
        
        
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts- after msg read")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
               
def For_cont_Test_case_33_data_pkt_CAN0_error_injection_Randamization_working_can1_can0():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

 
    ## ============================================================================== ##
    from random import seed
    for seed_i in range (0,501):
        seed_id = seed_i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
    ## ============================================================================== ##
    
      
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
      
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
        ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
        ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
            
       
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        
        #TODO: create11bitFilter
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        #TODO: Push11bitFilter
        

        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        
        '''
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        '''
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
      
        
        print("IR",reg_val_32)
        
        '''
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        '''
        
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
		##===============Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf) 
    


        #for i in range (0,5):
        #    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = (0x800 + 0x3B00), dw_count = 120)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 120)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
        #####==============Clear msg RAM================================#
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #####==============================================#
        
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #0<<1 ontime, 1<<1 continuous error
        CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x3):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")  
        
        #####==============================================#

        #addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = can1_bar, pos = 4)
        #print("addr_val is", addr_val)
        
        #Step 3: Set offset and Error injection data mask
        #print("#Step 3: Set offset and ERR_INJ data mask") 
        #reg_val_32 = 0
        #reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset)
        #reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (can1_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        #offset_Value = reg_val_32
        
        
        #CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset, reg_val_32)
        #reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset)
        #print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        #print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_DATA_MASK.offset, 0x100000) #20th bit is the mask. 4th bit ID
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf) 
    

        
        for i in range (0,7):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)
        
      
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = (0x800 + 0x3B00), dw_count = 120)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 120)
        print("\n")
        reg_val_RxFIFO = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400))
        reg_val_RxFIFO = (reg_val_RxFIFO  >> 18) & 0x000007FF
        if (reg_val_RxFIFO == 0):
            print("PASS")
        else:
            print("FAIL: RxFIFO is not 0 always in cont err inj")

        
        ##======================================================================================##
         
         
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
 


        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
        ##========================Read IR=======================================##
        
        
        

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_ERR_OFFSET.offset)

        reg_val_32 = reg_val_32 & 0x0000FFFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        
       
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")  


        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts-after EINJ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
        time.sleep(5)
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))        
        CanDeviceLibrary.WriteMmio(can1_bar, can1.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        '''
        print(" ******IMP*******CCCR CAN1 reg_val_32 is :", reg_val_32)         
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        '''


        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))        
        CanDeviceLibrary.WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print(" ******IMP*******CCCR CAN0 reg_val_32 is :", reg_val_32)         
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        
     

        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
            
        #====================================================================================== #
        #===============Packets creating 2nd time to check the behaviour============== #

        print("Packets creating again for 2nd time to check one time behaviour working after EINJ deassertion" )
        
        print("\n")
                    
        print("\n")
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)
            


        print("Reading MsgRAM Tx Buffer for 2nd time")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = (0x800 + 0x3B00), dw_count = 250)
        print("\n")

        print("Reading MsgRAM RxFiFo0 for 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 250)
        print("\n")
        
        
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts- after msg read")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
                                                            
def For_cont_Test_case_33_data_pkt_CAN0_error_injection_Randamization_working_can0_can1():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

 
    ## ============================================================================== ##
    from random import seed
    for seed_i in range (0,501):
        seed_id = seed_i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
    ## ============================================================================== ##
    
      
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
      
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
        ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
        ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
            
       
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        
        #TODO: create11bitFilter
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        #TODO: Push11bitFilter
        

        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        
        '''
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        '''
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
      
        
        print("IR",reg_val_32)
        
        '''
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        '''
        
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
		##===============Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can0_bar, pos = i, txbuf = txbuf) 
    


        #for i in range (0,5):
        #    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = (0x800 + 0x3B00), dw_count = 120)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 120)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
        #####==============Clear msg RAM================================#
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #####==============================================#
        
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #0<<1 ontime, 1<<1 continuous error
        CanDeviceLibrary.WriteMmio(can0_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x3):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")  
        
        #####==============================================#

        #addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = can1_bar, pos = 4)
        #print("addr_val is", addr_val)
        
        #Step 3: Set offset and Error injection data mask
        #print("#Step 3: Set offset and ERR_INJ data mask") 
        #reg_val_32 = 0
        #reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset)
        #reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (can1_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        #offset_Value = reg_val_32
        
        
        #CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset, reg_val_32)
        #reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset)
        #print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        #print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(can0_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x100000) #20th bit is the mask. 4th bit ID
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can0_bar, pos = i, txbuf = txbuf) 
    

        
        for i in range (0,7):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can0_bar, pos = i)
        
      
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = (0x800 + 0x3B00), dw_count = 120)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 120)
        print("\n")
        reg_val_RxFIFO = CanDeviceLibrary.ReadMmio(can1_bar, (0x800 + 0x400))
        reg_val_RxFIFO = (reg_val_RxFIFO  >> 18) & 0x000007FF
        if (reg_val_RxFIFO == 0):
            print("PASS")
        else:
            print("FAIL: RxFIFO is not 0 always in cont err inj")

        
        ##======================================================================================##
         
         
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
 


        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
        ##========================Read IR=======================================##
        
        
        

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_ERR_OFFSET.offset)

        reg_val_32 = reg_val_32 & 0x0000FFFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        
       
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")  


        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts-after EINJ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
        time.sleep(5)
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))        
        CanDeviceLibrary.WriteMmio(can0_bar, can0.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.CCCR.offset)
        '''
        print(" ******IMP*******CCCR CAN1 reg_val_32 is :", reg_val_32)         
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        '''


        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))        
        CanDeviceLibrary.WriteMmio(can1_bar, can1.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
             
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
     

        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
            
        #====================================================================================== #
        #===============Packets creating 2nd time to check the behaviour============== #

        print("Packets creating again for 2nd time to check one time behaviour working after EINJ deassertion" )
        
        print("\n")
                    
        print("\n")
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can0_bar, pos = i, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can0_bar, pos = i)
            


        print("Reading MsgRAM Tx Buffer for 2nd time")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = (0x800 + 0x3B00), dw_count = 250)
        print("\n")

        print("Reading MsgRAM RxFiFo0 for 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 250)
        print("\n")
        
            
               
def Test_case_33_data_pkt_CAN0_one_time_error_injection_Randamization_working_can1_can0():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

   

    ## ===================================================================================== ##
    from random import seed
    for seed_i in range (0,1):
        seed_id = seed_i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
    ## ===================================================================================== ##

        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
      
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
        ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
        ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
            
       
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        
        #TODO: create11bitFilter
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        #TODO: Push11bitFilter




        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        '''
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        '''
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
      
        
        print("IR",reg_val_32)
        '''
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        '''
        
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
		##===============Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf) 
    


        #for i in range (0,5):
        #    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = (0x800 + 0x3B00), dw_count = 50)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
        #####==============Clear msg RAM================================#
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #####==============================================#
        
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #0<<1 ontime, 1<<1 continuous error
        CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")  
        
        #####==============================================#

        addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = can1_bar, pos = 4)
        print("addr_val is", addr_val)
        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask") 
        reg_val_32 = 0
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (can1_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_DATA_MASK.offset, 0x100000) #20th bit is the mask. 4th bit ID
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf) 
    

        
        for i in range (0,7):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)
        
      
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = (0x800 + 0x3B00), dw_count = 50)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
        
        reg_val_RxFIFO = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400))
        reg_val_RxFIFO = (reg_val_RxFIFO  >> 18) & 0x000007FF
        if (reg_val_RxFIFO != 0):
            print("PASS")
        else:
            print("FAIL: RxFIFO is 0 in one time err inj")

        ##======================================================================================##
         
         
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
 


        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
        ##========================Read IR=======================================##
        
        
        

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        '''
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        '''    
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_ERR_OFFSET.offset)

        reg_val_32 = reg_val_32 & 0x0000FFFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        
       
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")  


        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts-after EINJ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
        time.sleep(5)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))        
        CanDeviceLibrary.WriteMmio(can1_bar, can0.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can0.CCCR.offset)
        print(" ******IMP*******CCCR reg_val_32 is :", reg_val_32)         
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
       
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))        
        CanDeviceLibrary.WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print(" ******IMP*******CCCR reg_val_32 is :", reg_val_32)         
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
   
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
            
        #====================================================================================== #
        #===============Packets creating 2nd time to check the behaviour============== #

        print("Packets creating again for 2nd time to check one time behaviour working after EINJ deassertion" )
        
        print("\n")
                    
        print("\n")
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)
            


        print("Reading MsgRAM Tx Buffer for 2nd time")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = (0x800 + 0x3B00), dw_count = 50)
        print("\n")

        print("Reading MsgRAM RxFiFo0 for 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
        
        
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts- after msg read")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
                                                            
def Test_case_33_data_pkt_CAN0_one_time_error_injection_Randamization_working_can0_can1():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

   

    ## ===================================================================================== ##
    from random import seed
    for seed_i in range (0,501):
        seed_id = seed_i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
    ## ===================================================================================== ##

        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
      
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
        ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
        ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
            
       
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        
        #TODO: create11bitFilter
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        #TODO: Push11bitFilter




        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        '''
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        '''
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
      
        
        print("IR",reg_val_32)
        '''
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        '''
        
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
		##===============Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can0_bar, pos = i, txbuf = txbuf) 
    


        #for i in range (0,5):
        #    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = (0x800 + 0x3B00), dw_count = 50)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
        #####==============Clear msg RAM================================#
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #####==============================================#
        
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #0<<1 ontime, 1<<1 continuous error
        CanDeviceLibrary.WriteMmio(can0_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")  
        
        #####==============================================#

        addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = can0_bar, pos = 4)
        print("addr_val is", addr_val)
        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask") 
        reg_val_32 = 0
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (can0_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(can0_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(can0_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x100000) #20th bit is the mask. 4th bit ID
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can0_bar, pos = i, txbuf = txbuf) 
    

        
        for i in range (0,7):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can0_bar, pos = i)
        
      
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = (0x800 + 0x3B00), dw_count = 50)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
        
        reg_val_RxFIFO = CanDeviceLibrary.ReadMmio(can1_bar, (0x800 + 0x400))
        reg_val_RxFIFO = (reg_val_RxFIFO  >> 18) & 0x000007FF
        if (reg_val_RxFIFO != 0):
            print("PASS")
        else:
            print("FAIL: RxFIFO is 0 in one time err inj")

        ##======================================================================================##
         
         
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
 


        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
        ##========================Read IR=======================================##
        
        
        

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        '''
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        '''    
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_ERR_OFFSET.offset)

        reg_val_32 = reg_val_32 & 0x0000FFFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        
       
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")  


        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts-after EINJ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
        time.sleep(5)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))        
        CanDeviceLibrary.WriteMmio(can1_bar, can1.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        print(" ******IMP*******CCCR reg_val_32 is :", reg_val_32)         
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
       
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))        
        CanDeviceLibrary.WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print(" ******IMP*******CCCR reg_val_32 is :", reg_val_32)         
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
   
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
            
        #====================================================================================== #
        #===============Packets creating 2nd time to check the behaviour============== #

        print("Packets creating again for 2nd time to check one time behaviour working after EINJ deassertion" )
        
        print("\n")
                    
        print("\n")
        for i in range (0,7):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can0_bar, pos = i, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can0_bar, pos = i)
            


        print("Reading MsgRAM Tx Buffer for 2nd time")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = (0x800 + 0x3B00), dw_count = 50)
        print("\n")

        print("Reading MsgRAM RxFiFo0 for 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
        
        
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts- after msg read")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
                                                            
                             
               
def For_cont_Test_case_33_data_pkt_CAN0_one_time_error_injection_Randamization_loopback():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #TODO: create11bitFilter
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    #TODO: Push11bitFilter

    
    from random import seed
    for i in range (0,1):
        seed_id = i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
        
        '''
         ##===============adjacent offsets===============================##
        data = random.randint(1,65535)
        
       
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        ##===============================================================##
        '''

        
       
        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        '''
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        '''
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
      
        
        print("IR",reg_val_32)
        
        '''
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        '''
        
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
		##=====================================Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf) 

        #for i in range (0,5):
        #    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
        #####==============Clear msg RAM================================#
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #####==============================================#
        
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (1<<1)) #continuous error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")  
        
        #####==============================================#

        #addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = m_bar, pos = 2)
        #print("addr_val is", addr_val)
        
        #Step 3: Set offset and Error injection data mask
        #print("#Step 3: Set offset and ERR_INJ data mask") 
        #reg_val_32 = 0
        #reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        #reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (m_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        #offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00040000)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf) 
        for i in range (0,5):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
        '''
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset, txbuf = txbuf) 
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset)
            
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset)
        '''
  
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        
        ##======================================================================================##
         
         
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        '''
        ##==============Verify Packets are dropped from 3rd packets after parity ERR_ING==============##
        ##=====Verify at 0x90, 0x0D8,0x120 addresses as 1 packet takes 0x48 size(its based on RX FIFO elements size)====##
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x90))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        


        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0xD8))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x120))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        ##=============================================================================================##
        '''


        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
        ##========================Read IR=======================================##
        
        
        

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)

        reg_val_32 = reg_val_32 & 0x0000FFFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        
       
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")  


        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts-after EINJ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
        time.sleep(5)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | (0x0))
        #reg_val_32 = ((reg_val_32 & 0xFFFFBFFF) | (0x1 << 14)) #TXP_Pause
    
        CanDeviceLibrary.WriteMmio(m_bar, can0.CCCR.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print(" ******IMP*******CCCR reg_val_32 is :", reg_val_32)
         
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
            
        #====================================================================================== #
        #===============Packets creating 2nd time to check the behaviour============== #

        print("Packets creating again for 2nd time to check one time behaviour working after EINJ deassertion" )
        
        print("\n")
                    
        print("\n")
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
            


        print("Reading MsgRAM Tx Buffer for 2nd time")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 250)
        print("\n")

        print("Reading MsgRAM RxFiFo0 for 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 250)
        print("\n")
        
        
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts- after msg read")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
                              
               
                              
               
               
def Test_case_33_data_pkt_CAN0_one_time_error_injection_Randamization_External_loopback_CAN0_CAN1():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)        
    
    #TODO: create11bitFilter
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    #TODO: Push11bitFilter

    
    from random import seed
    for i in range (0,1):
        seed_id = i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
        
        '''
         ##===============adjacent offsets===============================##
        data = random.randint(1,65535)
        
       
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        ##===============================================================##
        '''

        
       
        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
      
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
		##=====================================Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf) 

        #for i in range (0,5):
        #    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
        #####==============Clear msg RAM================================#
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #####==============================================#
        
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #continuous error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")  
        
        #####==============================================#

        addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = m_bar, pos = 2)
        print("addr_val is", addr_val)
        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask") 
        reg_val_32 = 0
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (m_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00040000)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf) 
        for i in range (0,5):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
        '''
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset, txbuf = txbuf) 
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset)
            
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset)
        '''
  
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        
        ##======================================================================================##
         
         
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        '''
        ##==============Verify Packets are dropped from 3rd packets after parity ERR_ING==============##
        ##=====Verify at 0x90, 0x0D8,0x120 addresses as 1 packet takes 0x48 size(its based on RX FIFO elements size)====##
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x90))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        


        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0xD8))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x120))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        ##=============================================================================================##
        '''


        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
        ##========================Read IR=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)

        reg_val_32 = reg_val_32 & 0x0000FFFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        
       
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")  


        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts-after EINJ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        

         
            
        #====================================================================================== #
        #===============Packets creating 2nd time to check the behaviour============== #

        print("Packets creating again for 2nd time to check one time behaviour working after EINJ deassertion" )
        
        print("\n")
                    
        print("\n")
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
            


        print("Reading MsgRAM Tx Buffer for 2nd time")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")

        print("Reading MsgRAM RxFiFo0 for 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        
        
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts- after msg read")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
                              
def Test_case_33_data_pkt_CAN0_one_time_error_injection_Randamization_External_loopback_CAN1_CAN0():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)        
    
    #TODO: create11bitFilter
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0x1, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    #TODO: Push11bitFilter

    
    from random import seed
    for i in range (0,1):
        seed_id = i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
        
        '''
         ##===============adjacent offsets===============================##
        data = random.randint(1,65535)
        
       
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        ##===============================================================##
        '''

        
       
        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
      
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
		##=====================================Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf) 

        #for i in range (0,5):
        #    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
        #####==============Clear msg RAM================================#
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #####==============================================#
        
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #continuous error
        CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")  
        
        #####==============================================#

        addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = can1_bar, pos = 2)
        print("addr_val is", addr_val)
        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask") 
        reg_val_32 = 0
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (can1_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(can1_bar, can1.PAR_EINJ_DATA_MASK.offset, 0x00040000)
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf) 
        for i in range (0,5):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)
        
        '''
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset, txbuf = txbuf) 
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset)
            
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset)
        '''
  
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        
        ##======================================================================================##
         
         
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        '''
        ##==============Verify Packets are dropped from 3rd packets after parity ERR_ING==============##
        ##=====Verify at 0x90, 0x0D8,0x120 addresses as 1 packet takes 0x48 size(its based on RX FIFO elements size)====##
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x90))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        


        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0xD8))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x120))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        ##=============================================================================================##
        '''


       # ============================ CAN1_CCCR=================================================== #
        print("Reading CAN1 CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
        ##========================Read IR=======================================##
        
        
        # ============================ CAN0_CCCR=================================================== #
        print("Reading CAN0 CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
        ##========================Read IR_CAN1=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##  


        ##========================Read IR CAN0=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
        ##===============================================================##           
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_ERR_OFFSET.offset)

        reg_val_32 = reg_val_32 & 0x0000FFFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        
       
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")  


        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts-after EINJ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        

         
            
        #====================================================================================== #
        #===============Packets creating 2nd time to check the behaviour============== #

        print("Packets creating again for 2nd time to check one time behaviour working after EINJ deassertion" )
        
        print("\n")
                    
        print("\n")
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)
            


        print("Reading MsgRAM Tx Buffer for 2nd time")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")

        print("Reading MsgRAM RxFiFo0 for 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        
        
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts- after msg read")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        
                              
                             
                       
        
def Debug_Test_case_33_data_pkt_CAN0_one_time_error_injection_Randamization():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = random.randint(5, 31)

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #TODO: create11bitFilter
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    #TODO: Push11bitFilter

    
    from random import seed
    for i in range (0,1):
        seed_id = i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        data = random.randint(1,65535)
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        
        

        print("SEED_ID is",seed_id)
        
       
        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
      
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
		##=====================================Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = m_bar, pos = TxBufferOffset)
            print("addr_val is", addr_val)

            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset+i-2, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset+i-2)
            CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset+i-2)

  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
               
        ##==============================================================================================##   
        ##===============================================================##  
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #one-time error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")     

        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask")    
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (m_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0x00040000)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset, txbuf = txbuf) 
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset)
            
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset)

  
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 600)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        
        ##======================================================================================##
        ''' 
        ##==============Verify Packets are dropped from 3rd packets after parity ERR_ING==============##
        ##==============Verify at 0x90, 0x0D8,0x120 addresses as 1 packet takes 0x48 size(its based on RX FIFO elements size)==============##
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x90))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        


        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0xD8))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x120))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        ##=============================================================================================##
        '''
        #Step 4: Read one-time error occured
        print("#Step 4: Read one-time ERR_OCCURED")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
        print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT.EINJ_ONE_TIME_ERR_OCCURED!= 1")
        else:
            print("PASS")       

        print("\n")         
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        

        #Compare function
        
        print("\n")
        print("\n")


        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
##========================Read IR=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
        
        
        reg_val_32 = reg_val_32 & 0x0000FFFF #before reg_val_32 = reg_val_32 & 0x00003FFF
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        '''
        if (reg_val_32 != offset_Value):
            print("FAIL: Stored offset value != injected offset value")
        else:
            print("PASS")
        '''  
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")         

         
           
       #====================================================================================== #
       #===============================Packets creating 2nd time to check continuous behaviour======================================================= #
 

        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset+i-2, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset+i-2)
            if (i<2): # i<2 packets should be received in RxFIFO and i= 2to4 should be dropped, since Parity error is injected in i=2
                CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset+i-2)

  
       
        print("Reading MsgRAM Tx Buffer")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
        
        
        

        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        '''
        #==============================================================================# 
        ##==============Verify Packets are NOT dropped from 3rd packet in one time err inj==============##
        ##==============Verify at 0x90, 0x0D8,0x120 addresses as 1 packet takes 0x48 size(its based on RX FIFO elements size)==============##
       
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x90))
        
        if (Read_data == 0):
            print("FAIL: Second time ERR_INJ: 1st packet after ERR_INJ Offest is dropped")
        else:
            print("PASS")
        


        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0xD8))
        if (Read_data == 0):
            print("FAIL: Second time ERR_INJ: 1st packet after ERR_INJ Offest is dropped")
        else:
            print("PASS")
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x120))
        if (Read_data == 0):
            print("FAIL: Second time ERR_INJ: 1st packet after ERR_INJ Offest is dropped")
        else:
            print("PASS")
        ##=============================================================================================##
        '''

def mask_18_to_32bits_Test_case_33_data_pkt_CAN0_one_time_error_injection_Randamization():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = random.randint(5, 31)

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 1 , loopback_enable  = 1)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #TODO: create11bitFilter
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    #TODO: Push11bitFilter

    
    from random import seed
    for i in range (0,1):
        seed_id = i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        data = random.randint(1,65535)
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        
        

        print("SEED_ID is",seed_id)
        
       
        #====================================Read CCCR.INIT============================================ #
    
        print("#Step 1: Verify CCCR.INIT =0")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        print("Reading CCCR.INIT", reg_val_32)
        print("\n")
        
         #====================================================================================== #

 
        
        #Step 1: Verify Parity enabled/Disabled by default
        print("#Step 1: Verify Parity enabled/Disabled by default")
        print("Reading Paity PAR_CTL_STAT ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset)
        print("Reading PAR_CTL_STAT", reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PARITY_EN!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")
        
       
       ##========================Read IR for 21st bit before=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
      
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x0):
            print("FAIL:Read IR.BEU!=0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
		##=====================================Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            addr_val = CanDeviceLibrary.GetTxBufferOffset(m_bar = m_bar, pos = TxBufferOffset)
            print("addr_val is", addr_val)

            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset+i-2, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset+i-2)
            CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset+i-2)

  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 500)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
               
        ##==============================================================================================##   
        ##===============================================================##  
        #Step 2: Set Error injection enable and injection mode
        print("#Step 2: Set ERR_INJ enable and injection mode")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = ((reg_val_32 & 0xfffffffE) | 1)#EINJ_EN = 1 for error injection enable ,EINJ_EN = 0 for error injection disable
        reg_val_32 = ((reg_val_32 & 0xfffffffD) | (0<<1)) #one-time error
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        
        print("Read PAR_EINJ_CTL_STAT", reg_val_32)#value=0x00000001
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT!= 1")
                     
        else:
            print("PASS")
        print("\n")
        print("\n")       
        print("\n") 
        print("\n")        
        print("\n") 
        print("\n")     

        
        #Step 3: Set offset and Error injection data mask
        print("#Step 3: Set offset and ERR_INJ data mask")    
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        reg_val_32 = ((reg_val_32 & 0xFFFF0000) | (m_bar + addr_val))#Eaddr_val= different offset value, EINJ_EN = 0 for error injection disable
        offset_Value = reg_val_32
        
        
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_OFFSET.offset, reg_val_32)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_OFFSET.offset)
        print("Reading PAR_EINJ_OFFSET value", reg_val_32)
        print("\n") 
        print("\n") 
        CanDeviceLibrary.WriteMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset, 0xFFFC0000)
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_DATA_MASK.offset)    
        print("Read PAR_EINJ_DATA_MASK", reg_val_32)
        print("\n") 
        print("\n")     
        #====================================================================================== #

        ##==================================ERR_INJ to 3rd packet====================================================##
        txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset, txbuf = txbuf) 
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset)
            
        CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset)

  
       
        print("Reading MsgRAM Tx Buffer-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 500)
        print("\n")
        
        

        print("Reading MsgRAM RxFiFo0-After ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        
        ##======================================================================================##
        ''' 
        ##==============Verify Packets are dropped from 3rd packets after parity ERR_ING==============##
        ##==============Verify at 0x90, 0x0D8,0x120 addresses as 1 packet takes 0x48 size(its based on RX FIFO elements size)==============##
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x90))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        


        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0xD8))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x120))
        if (Read_data != 0):
            print("FAIL: 1st packet after ERR_INJ Offest is not dropped")
        else:
            print("PASS")
        ##=============================================================================================##
        '''
        #Step 4: Read one-time error occured
        print("#Step 4: Read one-time ERR_OCCURED")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)>>2
        print("Reading Paity PAR_EINJ_CTL_STAT to verify EINJ_ONE_TIME_ERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_EINJ_CTL_STAT.EINJ_ONE_TIME_ERR_OCCURED!= 1")
        else:
            print("PASS")       

        print("\n")         
        #Step 7: Read EINJ_EN deasserts    
        print("#Step 7: Read EINJ_EN deasserts")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_EINJ_CTL_STAT.offset)
        reg_val_32 = reg_val_32 &0x00000001
        print("Reading Parity is deasserted EINJ_EN=0", reg_val_32)
        
        print("\n")
        if (reg_val_32 != 0x0):
            print("FAIL:EINJ_EN= 0")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")
        

        #Compare function
        
        print("\n")
        print("\n")


        # =============================================================================== #

        print("Reading CCCR.INIT")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.CCCR.offset)
        reg_val_32= reg_val_32 & 0x00000001
        print("Reading CCCR.INIT", reg_val_32)
        if (reg_val_32 != 0x1):
            print("FAIL:CCCR.INIT= 1")
                     
        else:
            print("PASS")
        
        
        print("\n")      
##========================Read IR=======================================##

       
        print("#Step 7: Read IR.BEU")

        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
        
        reg_val_32=reg_val_32 >>21
        
        print("IR",reg_val_32)
        
        if (reg_val_32 != 0x1):
            print("FAIL:Read IR.BEU=1")
                     
        else:
            print("PASS")
        print("\n")
                    
        print("\n")   
        
##===============================================================##        
        #Step 5: Check stored offset value is correct
        print("#Step 5: Check stored offset value is correct")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_ERR_OFFSET.offset)
        print("Read PAR_ERR_OFFSET ", reg_val_32)
        print("\n")
        reg_val_32 = reg_val_32 & 0x00003FFF
        
        '''
        if (reg_val_32 != offset_Value):
            print("FAIL: Stored offset value != injected offset value")
        else:
            print("PASS")
        '''  
        #Step 6: Read PERR_OCCURED=1
        print("#Step 6: Read PERR_OCCURED ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PAR_CTL_STAT.offset) >>2
        print("Read PERR_OCCURED", reg_val_32)
        print("\n")
        if (reg_val_32 != 0x1):
            print("FAIL:PAR_CTL_STAT.PERR_OCCURED!= 1")
                     
        else:
            print("PASS")
        print("\n")
        

        print("\n")         

         
           
       #====================================================================================== #
       #===============================Packets creating 2nd time to check continuous behaviour======================================================= #
 

        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = TxBufferOffset+i-2, txbuf = txbuf) 
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = TxBufferOffset+i-2)
            if (i<2): # i<2 packets should be received in RxFIFO and i= 2to4 should be dropped, since Parity error is injected in i=2
                CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = TxBufferOffset+i-2)

  
       
        print("Reading MsgRAM Tx Buffer")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 500)
        print("\n")
        
        
        

        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        '''
        #==============================================================================# 
        ##==============Verify Packets are NOT dropped from 3rd packet in one time err inj==============##
        ##==============Verify at 0x90, 0x0D8,0x120 addresses as 1 packet takes 0x48 size(its based on RX FIFO elements size)==============##
       
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x90))
        
        if (Read_data == 0):
            print("FAIL: Second time ERR_INJ: 1st packet after ERR_INJ Offest is dropped")
        else:
            print("PASS")
        


        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0xD8))
        if (Read_data == 0):
            print("FAIL: Second time ERR_INJ: 1st packet after ERR_INJ Offest is dropped")
        else:
            print("PASS")
        
        Read_data = CanDeviceLibrary.ReadMmio(m_bar, (0x800 + 0x400 + 0x120))
        if (Read_data == 0):
            print("FAIL: Second time ERR_INJ: 1st packet after ERR_INJ Offest is dropped")
        else:
            print("PASS")
        ##=============================================================================================##
        '''
        
        
def CAN0_CAN1_to_Vector():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]
    Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0, brs=0 )

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    
    '''
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    '''

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
 
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
    #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
    #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    msg=Vector_bus.recv(3)
    if msg:
        print("vector data",msg)
    else:
        print(" no vector data received")
    
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    '''
    print("CAN0 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 4)
    print("\n")
    
    
    print("CAN1 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 4)
    print("\n")
    '''
    
    print("Reading MsgRAM Tx Buffer CAN0")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Buffer CAN1")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    '''
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    '''
    '''
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
     
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    '''
    
  
    
def Vector_to_CAN1_CAN0():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    '''
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR values of CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR values of CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    '''
    
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x5)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x8, ssync = 0, sfid2 = 0x9)
    CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    print("send packet from Vector...")
    time.sleep(30)
    
    '''
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    '''
    '''
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    '''
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    '''
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR values of CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR values of CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    '''



def Vector_to_CAN1_CAN0_same_ID_in_two_Filters():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
    
    '''
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0x1, ssync = 0, sfid2 = 0x5)
    CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0x5, ssync = 0, sfid2 = 0x6)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    '''
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 2, sfid1 = 0x7, ssync = 0, sfid2 = 0x9)
    CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    

    
    print("send packet from Vector...")
    time.sleep(30)
    
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1 CAN0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1 CAN0")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x1E00), dw_count = 80)
    print("\n")
    
    

    
    
def can_init_can1_to_can0():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x2FF
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x2800), dw_count = 4)
    print("\n")
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x640), dw_count = 4)
    print("\n")
    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    '''
        
    
    #CanDeviceLibrary.MsgRAMTest(m_bar = m_bar)
    
    #CanDeviceLibrary.MsgRAMTest(m_bar = can0_bar)
    
def can_init_can0_to_can1():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0xFF
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    ##==============================================================================================##   
    ##==================Read TXBRP,TXBTO,TC=============================================## 
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
    print("TXBRP reg_val_32 is :", reg_val_32)

    print("\n")
    print("\n")
        
        
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
    print("TXBTO reg_val_32 is :", reg_val_32)

    print("\n")
    print("\n")
         
        
        
    reg_val_32_3 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TC=(reg_val_32 & 0x00000200)>>9
    print("TC  is :", TC)
    print("\n")
    print("\n")
            
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    #reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    ##==============================================================================================##   
    ##==================Read TXBRP,TXBTO,TC=============================================## 
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
    print("TXBRP reg_val_32 is :", reg_val_32)

    print("\n")
    print("\n")
        
        
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
    print("TXBTO reg_val_32 is :", reg_val_32)

    print("\n")
    print("\n")
         
        
        
    reg_val_32_3 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TC=(reg_val_32 & 0x00000200)>>9
    print("TC  is :", TC)
    print("\n")
    print("\n")
            
    
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x3A00), dw_count = 50)
    print("\n")

    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 4)
    print("\n")
    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    '''
    
    #CanDeviceLibrary.Readerror(m_bar = m_bar)
    
    #CanDeviceLibrary.MsgRAMTest(m_bar = m_bar)
    
    #CanDeviceLibrary.MsgRAMTest(m_bar = can0_bar)
    
    
def Testcase_23_CAN0_CAN1_to_Acute_For_CAN():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    
    '''
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    '''
    

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
 
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
    #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
    #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
  
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)  
    
    
    
    
    
    
    
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x17FF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x17FE, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x17FD, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
    
    CanDeviceLibrary.WriteMmio(m_bar, can0.TXBAR.offset, 0x7)
    CanDeviceLibrary.WriteMmio(can1_bar, can1.TXBAR.offset, 0x7)
    
    
    
    
    
    

    

    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    '''
    print("CAN0 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 4)
    print("\n")
    
    
    print("CAN1 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 4)
    print("\n")
    '''
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    '''
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    '''
    '''
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
     
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    '''
    
def Testcase_23_CAN0_CAN1_to_Acute_For_CAN_FD():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    
    '''
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    '''
    

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
 
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
    #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
    #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
  
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)  
    
    
    
    
    
    
    
    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FE, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FD, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
    
    CanDeviceLibrary.WriteMmio(m_bar, can0.TXBAR.offset, 0x7)
    CanDeviceLibrary.WriteMmio(can1_bar, can1.TXBAR.offset, 0x7)
    
    
    
    
    
    

    

    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    '''
    print("CAN0 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 4)
    print("\n")
    
    
    print("CAN1 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 4)
    print("\n")
    '''
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    '''
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    '''
    '''
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
     
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    ''' 
    
    
    
def Test_case_20_data_frame_over_remote_frame():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    
    '''
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    '''
    

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
 
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x50)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 1, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x50)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 2, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x50)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 3, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
   
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 1, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 3, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)  
    
    
    
    '''
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FE, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FD, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
    '''
    CanDeviceLibrary.WriteMmio(m_bar, can0.TXBAR.offset, 0xF)
    
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    

    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
    print("\n")

    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 100)
    print("\n")
    
   
def Test_case_20_data_frame_over_remote_frame_rand():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    

    
    from random import seed

    for i in range(0,501):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id)        
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)


        # Randomize variables    
        num_packets = random.randint(1, 31)
        print("num_packets:",num_packets)
       
        for i in range(1,num_packets):    
            val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7FF)
            CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = i, filt = val)
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x0, ssync = 0, sfid2 = 0x50)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 1, filt = val)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x0, ssync = 0, sfid2 = 0x50)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 2, filt = val)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x0, ssync = 0, sfid2 = 0x50)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 3, filt = val)
        '''
        prev_canID = 0x1    
        for i in range(0,num_packets): 
            can_id_rand = random.randint(min_can_id, max_can_id)    
            rand_remote_pkt = random.randint(0, 1)
            if (rand_remote_pkt ==1):
                #if (random.randint(0, 1)):
                canID = prev_canID  
                #else:
                #    canID = can_id_rand

            else:
                canID = can_id_rand
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=canID, rtr = rand_remote_pkt, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf)       
            prev_canID = can_id_rand;       
            
      
        
        
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FE, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
        #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 1)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FD, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
        '''
        reg_val_32=0x0
        for i in range(0,num_packets): 
            buffer_element_enable = (0x1 << i) 
            reg_val_32 = (reg_val_32 ) | buffer_element_enable
        CanDeviceLibrary.WriteMmio(m_bar, can0.TXBAR.offset, reg_val_32)
        print("TXBAR.offset - Number of buffer elements enabled are:", reg_val_32)
        
        '''
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")

        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
        '''
        
        CanDeviceLibrary.verify_rx_fifo_remote_frame(m_bar= can1_bar, addr = (0x800 + 0x400), num_packets = num_packets)
        
        
def Test_case_16_stuff_concept():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    
    '''
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    '''
    

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
 
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7FF)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x7FF)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 1, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x7FF)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 2, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x7FF)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 3, filt = val)
    
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7FF)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 4, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x7FF)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 5, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x7FF)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 6, filt = val)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x7FF)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 7, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
   
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1F, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x3F, rtr = 1, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 2, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7F, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 3, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)  
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x6, rtr = 1, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 4)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 4, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)    
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 5)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 5, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0xFF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 6)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 6, txbuf = txbuf)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x1FF, rtr = 1, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 7)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 7, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 2)   
    '''
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FE, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
    #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 1)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FD, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
    '''
    CanDeviceLibrary.WriteMmio(m_bar, can0.TXBAR.offset, 0xFF)
    
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    


 
def Test_case_16_stuff_concept_rand():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x1E  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1

    can_id_sent_array =[]
    

    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id)        
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 1, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)


        # Randomize variables    
        num_packets = random.randint(1, 31)
        xtd=0;

        print("num_packets:",num_packets)
       
        for i in range(1,num_packets):    
            val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7FF)
            CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = i, filt = val)
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x0, ssync = 0, sfid2 = 0x50)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 1, filt = val)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x0, ssync = 0, sfid2 = 0x50)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 2, filt = val)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x0, ssync = 0, sfid2 = 0x50)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 3, filt = val)
        '''
        prev_canID = 0x1    
        for i in range(0,num_packets): 
            #can_id_rand = random.randint(min_can_id, max_can_id) 
            
            #pcaket_type=0 - Normal data
            #pcaket_type=1 - Remote data    
            #pcaket_type=2 - Normal stuffed data
            #pcaket_type=3 - Remote stuffed data 
            
            packet_type = random.randint(0, 3)  
            
            if (packet_type == 0 or 1):
                can_id_rand = random.randint(0x01, 0x1E) 
                
            if (packet_type == 2 or 3):
                stuff_id_pos = random.randint(0, 23)
                can_id_rand =0x1F
                for i in range(0,stuff_id_pos): 
                    can_id_pos = (0x1 << i+5) 
                    can_id_rand = (can_id_rand ) | can_id_pos
                    if (xtd == 0):
                        can_id_rand = (can_id_rand<<18)
                    
                
            can_id_sent_array.append(can_id_rand)
                        
            rand_remote_pkt = random.randint(0, 1)
            if (rand_remote_pkt ==1):
                #if (random.randint(0, 1)):
                    canID = prev_canID  
                #else:
                #    canID = can_id_rand

            else:
                canID = can_id_rand
            print("CANID is ", canID)
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=canID, rtr = rand_remote_pkt, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf)       
            prev_canID = can_id_rand;       
            
      
        
        
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FE, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
        #CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 1)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=0x7FD, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 13, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
        '''
        reg_val_32=0x0
        for i in range(0,num_packets): 
            buffer_element_enable = (0x1 << i) 
            reg_val_32 = (reg_val_32 ) | buffer_element_enable
        CanDeviceLibrary.WriteMmio(m_bar, can0.TXBAR.offset, reg_val_32)
        print("TXBAR.offset - Number of buffer elements enabled are:", reg_val_32)
        
        

        
        can_id_sent_array.sort()
        print("Sorted CANID array is", can_id_sent_array)
        CanDeviceLibrary.verify_rx_fifo_remote_frame_with_stuff(m_bar= can1_bar, addr = (0x800 + 0x400), num_packets = num_packets, can_id_sent_array=can_id_sent_array)



   
def Test_case_32():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    

    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
    
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0xA)
    CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    '''
    print("send packet from Vector...")
    time.sleep(30)
    '''
    CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =0x4 )


    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    '''
       
def Test_case_32_rand_CAN_CAN_FD():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    can_id_vector = random.randint(0x01, 0x9)
    print ("can_id_vector is", can_id_vector)
    can_id_can0 = random.randint(0x0A, 0xB)
    print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        fd_rand = random.randint(0,1)
        
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        if (fd_rand == 1):
        
            CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
            lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
            efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
            ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
            anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
            
            
            CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
            lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
            efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
            ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
            anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
            
            CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
            CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
            CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
            CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
            CanDeviceLibrary.can_start_communication(m_bar = m_bar)
            CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

            val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7FF)
            CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_can0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
            '''
            print("send packet from Vector...")
            time.sleep(30)
            '''
            CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector )
            
        else:
        
            CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
            lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
            efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1, ntseg2 = ntseg2, 
            ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
            anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
            
            
            CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
            lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
            efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1, ntseg2 = ntseg2, 
            ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
            anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
            
            CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
            CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
            CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
            CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
            CanDeviceLibrary.can_start_communication(m_bar = m_bar)
            CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

            val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7FF)
            CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_can0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
            '''
            print("send packet from Vector...")
            time.sleep(30)
            '''
            CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector )



        '''
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 120)
        print("\n")
        
        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
 
        CanDeviceLibrary.verify_rx_fifo_3nodes(m_bar = can1_bar,  addr = (0x800 + 0x400), num_packets = 2)
        
        
def Test_case_32_rand_CAN():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    can_id_vector = random.randint(0x01, 0x9)
    print ("can_id_vector is", can_id_vector)
    can_id_can0 = random.randint(0x0A, 0xB)
    print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(120,130):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_can0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        '''
        print("send packet from Vector...")
        time.sleep(30)
        '''
        CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector )


        '''
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = addr, dw_count = 120)
        print("\n")
        
        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
 
        CanDeviceLibrary.verify_rx_fifo_3nodes(m_bar = can1_bar,  addr = (0x800 + 0x400), num_packets = 2)
       
def Test_case_25_Vector():
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    can_id_vector = random.randint(0x1, 0x7FF)
    print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        

        '''
        print("send packet from Vector...")
        time.sleep(30)
        '''
        CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector )




        
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        
        print("Reading MsgRAM RxFiFo0 CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
 

        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        
def Test_case_26_CAN():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    from random import seed

    for i in range(0,501):    
        seed_id = i
        seed(seed_id) 
        print ("seed_id", seed_id)        
        can_id_vector = random.randint(0x1, 0x7E)
        print ("can_id_vector is", can_id_vector)
        can_id_can0 = random.randint(0x1AB,0x7FF)
        print ("can_id_can0 is", can_id_can0)
        can_id_can1 = random.randint(0x7F, 0x1AA)
        print ("can_id_can1 is", can_id_can1)

        
        
        
       
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x1AB, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x1, ssync = 0, sfid2 = 0x1AA)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        '''
        print("send packet from Vector...")
        time.sleep(30)
        '''
        
        CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector )
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_can1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_can0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
        #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
        
        '''
        print("CAN0 Reading MsgRAM 11bit Filter Buffer")
        addr = (0x800)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 4)
        print("\n")
        
        
        print("CAN1 Reading MsgRAM 11bit Filter Buffer")
        addr = (0x800)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 4)
        print("\n")
        '''
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
        print("\n")
        
        '''
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
        print("\n")
        
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
        print("\n")
        '''
        '''
        print("Reading MsgRAM Rx Buffer")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
        print("\n")
        
        #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
        
        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
        print("\n")
        '''
        print("Reading MsgRAM Rx Fifo1 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1 CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        '''
        
        print("Reading MsgRAM Rx Fifo1")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
        print("\n")
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
        print("PSR reg_val_32 is :", reg_val_32)
        psr=(reg_val_32 & 0x00000007)
        print("LEC  is :", psr)

        print("ECR value at CAN0")
         
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TEC=(reg_val_32 & 0x000000FF)
        print("TEC  is :", TEC)
        
        REC=(reg_val_32 & 0x0000FF00)>>8
        print("REC  is :", REC)
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
        print("PSR reg_val_32 is :", reg_val_32)
        psr=(reg_val_32 & 0x00000007)
        print("LEC  is :", psr)
        
        print("ECR value at CAN1")
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TEC=(reg_val_32 & 0x000000FF)
        print("TEC  is :", TEC)
        
        REC=(reg_val_32 & 0x0000FF00)>>8
        print("REC  is :", REC)
        '''
        CanDeviceLibrary.verify_rx_testcase_26(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x640), can0_sfid1=0x1, can0_sfid2=0x1AA,can1_sfid1=0x1AB, can1_sfid2=0x7FF, sent_can_id_can0=can_id_can0, sent_can_id_can1=can_id_can1, sent_can_id_vector=can_id_vector, num_packets=1)      
        
def Test_case_26_CAN_FD():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 64
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id) 
        print ("seed_id", seed_id)
        can_id_vector = random.randint(0x1, 0x7E)
        print ("can_id_vector is", can_id_vector)
        can_id_can0 = random.randint(0x1AB,0x7FF)
        print ("can_id_can0 is", can_id_can0)
        can_id_can1 = random.randint(0x7F, 0x1AA)
        print ("can_id_can1 is", can_id_can1)

        
        
        
       
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x1AB, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x1, ssync = 0, sfid2 = 0x1AA)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        '''
        print("send packet from Vector...")
        time.sleep(30)
        '''
        
        CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector )
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_can1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 15, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_can0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 15, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
        #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
        
        '''
        print("CAN0 Reading MsgRAM 11bit Filter Buffer")
        addr = (0x800)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 4)
        print("\n")
        
        
        print("CAN1 Reading MsgRAM 11bit Filter Buffer")
        addr = (0x800)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 4)
        print("\n")
        '''
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
        print("\n")
        
        '''
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
        print("\n")
        
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
        print("\n")
        '''
        '''
        print("Reading MsgRAM Rx Buffer")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
        print("\n")
        
        #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
        
        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
        print("\n")
        '''
        print("Reading MsgRAM Rx Fifo1 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1 CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        '''
        
        print("Reading MsgRAM Rx Fifo1")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
        print("\n")
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
        print("PSR reg_val_32 is :", reg_val_32)
        psr=(reg_val_32 & 0x00000007)
        print("LEC  is :", psr)

        print("ECR value at CAN0")
         
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TEC=(reg_val_32 & 0x000000FF)
        print("TEC  is :", TEC)
        
        REC=(reg_val_32 & 0x0000FF00)>>8
        print("REC  is :", REC)
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
        print("PSR reg_val_32 is :", reg_val_32)
        psr=(reg_val_32 & 0x00000007)
        print("LEC  is :", psr)
        
        print("ECR value at CAN1")
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TEC=(reg_val_32 & 0x000000FF)
        print("TEC  is :", TEC)
        
        REC=(reg_val_32 & 0x0000FF00)>>8
        print("REC  is :", REC)
        '''
        CanDeviceLibrary.verify_rx_testcase_26(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x640), can0_sfid1=0x1, can0_sfid2=0x1AA,can1_sfid1=0x1AB, can1_sfid2=0x7FF, sent_can_id_can0=can_id_can0, sent_can_id_can1=can_id_can1, sent_can_id_vector=can_id_vector, num_packets=1)


def Test_Case_24_CAN0_CAN1_to_Vector():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]
    Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=1, brs=0 )

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    
 
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    
 
    
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
    ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
    #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
    #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
    #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
    
    #print("send packet from Vector...")
    #time.sleep(30)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
    for i in range(0,5):
    
        msg=Vector_bus.recv(10)
        if msg:
            print("vector data",msg)
        else:
            print(" no vector data received")
    
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    #CanDeviceLibrary.verify_rx_tranceiver(m_bar = m_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)
    
    '''
    print("CAN0 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 4)
    print("\n")
    
    
    print("CAN1 Reading MsgRAM 11bit Filter Buffer")
    addr = (0x800)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 4)
    print("\n")
    '''
    
    print("Reading MsgRAM Tx Buffer CAN0")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Buffer CAN1")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    '''
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x3A00), dw_count = 80)
    print("\n")
    '''
    '''
    print("Reading MsgRAM Rx Buffer")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x2800), dw_count = 80)
    print("\n")
    
    #CanDeviceLibrary.PollIR(m_bar= m_bar,IR_bit_pos=0)
    
    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
    print("\n")
    
    
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x800), dw_count = 4)
    print("\n")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)

    print("ECR value at CAN0")
     
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can1.PSR.offset)
    print("PSR reg_val_32 is :", reg_val_32)
    psr=(reg_val_32 & 0x00000007)
    print("LEC  is :", psr)
    
    print("ECR value at CAN1")
    
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
    print("ECR reg_val_32 is :", reg_val_32)
    TEC=(reg_val_32 & 0x000000FF)
    print("TEC  is :", TEC)
    
    REC=(reg_val_32 & 0x0000FF00)>>8
    print("REC  is :", REC)
    '''
       
       
def Test_Case_24_CAN0_CAN1_to_Vector_rand():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    can_id_vector_CAN0 = random.randint(0x1, 0xFE)
    can_id_vector_CAN1 = random.randint(0xFF, 0x7FF)
    
    print ("can_id_vector_CAN0 is", can_id_vector_CAN0)
    print ("can_id_vector_CAN1 is", can_id_vector_CAN1)
    Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0, brs=0 )

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed
    for i in range(0,5):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
        #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
        #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        for i in range(0,2):
        
            msg=Vector_bus.recv(10)
            if msg:
                print("vector data",msg)
                if (msg.arbitration_id != 0):
                    print ("PASS")
                else:
                    print ("FAIL")
                
            else:
                print("FAIL :No vector data received")
        

        

        print("Reading MsgRAM Tx Buffer CAN0")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Tx Buffer CAN1")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
        print("\n")
        
        
        
        
        
        

def Test_case_38_Bus_off():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)

    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x7FF
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 8)
    print("\n")
    

    

    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
 
    
    print("Date and Time before removing CAN-H and CAN-L:")
    now=datetime.datetime.now()
    print(now)
        
    print("Remove CAN-H")
    time.sleep(50)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 8)
    print("\n")
    

    

    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    
    
        
    print("Date and Time After removing CAN-H and CAN-L:")
    now=datetime.datetime.now()
    print(now)



    print("Connect CAN-H")
    time.sleep(50)
    
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
    CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
    CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
    CanDeviceLibrary.verify_rx_tranceiver(m_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf)
    
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 8)
    print("\n")
    

    

    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 8)
    print("\n")
    
    
    
        
    print("Date and Time After removing CAN-H and CAN-L:")
    now=datetime.datetime.now()
    print(now)


    

def Test_Case_21_rand_1():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1


    from random import seed

    for s in range(0,501):    
        seed_id = s
        seed(seed_id) 
        print ("seed_id", seed_id)        
        Num_packets = random.randint(4,30)    

        print("Num_packets",Num_packets)
        EFS = Num_packets-1
        EFWM = Num_packets-2
       
      
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
      
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)

        #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = EFS, efwm = EFWM, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = EFS, efwm = EFWM, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
           
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        
        
        for n in range(Num_packets):
        
            val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 2, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
            CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
          
            
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=1+n, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = n)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = n, txbuf = txbuf)
            
            '''   
            txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
               
            txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 3, txbuf = txbuf)
            '''
      
        
        for e in range(Num_packets):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = e)
            
        print("Reading IR ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
        print("\n")

        IR_TEFW = (0x00002000 & reg_val_32)>>13
        if (IR_TEFW == 1 ):
            print("PASS:Water mark is set")
        else:
            print("FAIL") 
        
        IR_TEFF = (0x00004000 & reg_val_32)>>14
        if (IR_TEFW == 1 ):
            print("PASS:Tx Event FIFO Full is set")
        else:
            print ("FAIL") 
        
        IR_TEFL = (0x00008000 & reg_val_32)>>15
        if (IR_TEFL == 1 ):
            print("PASS:Tx Event FIFO Element Lost is set")
        else:
            print("FAIL") 

        
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 120)
        print("\n")
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 50)
        print("\n")
            
            

        '''
        print("Reading IR TxEventFIFO ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
        print("IR TxEventFIFO can0_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
        print("\n")    
        '''
        #Packet_dropped = CanDeviceLibrary.ReadMmio(can1_bar, (4+(0x800 + 0x3A00)+(Num_packets*4)))
        Packet_dropped = CanDeviceLibrary.ReadMmio(can1_bar, ((0x800 + 0x3A00)+(Num_packets*8)))
        if (Packet_dropped == 0):
            print("PASS:Packet dropped after fill level")
            
        else:
             print("FAIL:Packet not dropped")
           
        #CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        CanDeviceLibrary.verify_rx(m_bar = can1_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        
        new_Packet_ID = 0x8
        
        print("Send packets after packets are drined")
        txbuf = CanDeviceLibrary.createTxPacket(can_id=new_Packet_ID, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        
        
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=11, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 6)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 6, txbuf = txbuf)
        
        #for i in range(4):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 6)
        '''
      

        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 120)
        print("\n")
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 50)
        print("\n")
        
        Packet_Filled = CanDeviceLibrary.ReadMmio(can1_bar, 0x800 + 0x3A00)
        
        if (Packet_Filled == 0x000200000):
            print("PASS:New packet is received",Packet_Filled)
            
        else:
             print("FAIL: new packet is not received")
        

        print("Reading MsgRAM Rx Fifo1")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 150)
        print("\n")
            
def Test_case_22_can_init_can1_to_can0_Transceiver_at_Rx_side():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    F1OM =0
    
    '''
    ##============Venkat added to check inturrupt is working======#
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, 0x508)
    print("INTR_CTRL is :", reg_val_32)
    reg_val_32= 0x00000001
    CanDeviceLibrary.WriteMmio(m_bar, 0x508, reg_val_32)
    
    ##======================================================#
    '''
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
    
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 32,f1wm=2,f1om=0,tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    
    CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64 , rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 32, efwm = 32,f1wm=2,f1om=0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
    ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
    CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
    CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    for i in range(5):
        txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf)
    for i in range(5):
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = i)

    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR can0_bar - reg_val_32 is", reg_val_32)
    print("\n")    
    
    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
    print("IR can1_bar - reg_val_32 is", reg_val_32)
    print("\n")  
   


    print("Reading RXF1S ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.RXF1S.offset)
    print("CAN0_RXF1S", reg_val_32)
    print("\n")     
        
    CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf, pos=0)
    #CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf, pos=0)
  
    print("Reading RXF0S ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.RXF0S.offset)
    print("CAN1_RXF1S", reg_val_32)
    print("\n")
    
    print("Reading IR ")
    reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
    print("IR can0_bar - reg_val_32 is", reg_val_32)
    print("\n")     
            
    
    print("Reading MsgRAM Tx Buffer")
    addr = (0x800 + 0x3B00)
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
    print("\n")
    
    print("Reading MsgRAM Tx Event Fifo")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 40)
    print("\n")
    

    print("Reading MsgRAM RxFiFo0")
    CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 4)
    print("\n")
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x1600), dw_count = 100)
    print("\n")    
    '''
    print("Reading MsgRAM Rx Fifo1")
    CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 100)
    print("\n")
    
def Test_Case_22_rand_Blocking():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1


    from random import seed

    for s in range(0,501):    
        seed_id = s
        seed(seed_id) 
        print ("seed_id", seed_id)        
        Num_packets = random.randint(4,18)    

        print("Num_packets",Num_packets)
        #EFS = Num_packets-1
        #print ("EFS", EFS)
        #EFWM = Num_packets-2
        #print ("EFWM", EFWM)
        rxf0c_elements = Num_packets-1
        print ("rxf0c_elements", rxf0c_elements)
        F0WM = Num_packets-2
        f0om = 0 # 0- Blocking 1- Overwrite
        print ("f0om", f0om)
      
      
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
      
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)

        #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = rxf0c_elements, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0,tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
                
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = rxf0c_elements, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0,f0wm=F0WM,f0om=f0om,tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
           
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        
        
        #for n in range(Num_packets):
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
          
            
        for n in range(Num_packets):
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=2+n, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = n)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = n, txbuf = txbuf)
            
            '''   
            txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
               
            txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 3, txbuf = txbuf)
            '''
      
        
        for e in range(Num_packets):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = e)
        
        '''        
        print("Reading IR ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
        print("\n")
        
        IR_TEFW = (0x00002000 & reg_val_32)>>13
        if (IR_TEFW == 1 ):
            print("PASS:Water mark is set")
        else:
            print("FAIL:Water mark is not set") 
        
        IR_TEFF = (0x00004000 & reg_val_32)>>14
        if (IR_TEFW == 1 ):
            print("PASS:Tx Event FIFO Full is set")
        else:
            print ("FAIL:Tx Event FIFO Full is not set") 
        
        IR_TEFL = (0x00008000 & reg_val_32)>>15
        if (IR_TEFL == 1 ):
            print("PASS:Tx Event FIFO Element Lost is set")
        else:
            print("FAIL") 
        
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 120)
        print("\n")
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 50)
        print("\n")
        '''
           
            

        #Packet_dropped = CanDeviceLibrary.ReadMmio(can1_bar, (4+(0x800 + 0x3A00)+(Num_packets*4)))
        Packet_dropped = CanDeviceLibrary.ReadMmio(can1_bar, ((0x800 + 0x400)+((Num_packets-1)*0x48))) #RXFIFO increments by 0x48
        if (Packet_dropped == 0):
            print("PASS:Packet dropped after fill level")
            
        else:
             print("FAIL:Packet not dropped")
           
        #CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        #CanDeviceLibrary.verify_rx(m_bar = can0_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 120)
        print("\n")
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 50)
        print("\n")
         
        print("Reading MsgRAM RxFiFo0 - 1st time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        

        new_Packet_ID = 0xF
        
        print("Send packets after packets are drined")
        txbuf = CanDeviceLibrary.createTxPacket(can_id=new_Packet_ID, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        
        
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
     

    
    
                 
        Packet_Filled = CanDeviceLibrary.ReadMmio(can0_bar, 0x800 + 0x400) #Reading MsgRAM RxFiFo0
        Packet_Filled_can_id= (Packet_Filled & 0x1FFC0000)>>18
        print("Packet_Filled_can_id is ",Packet_Filled_can_id)
        
        
        if (Packet_Filled_can_id == 2):
            print("PASS:New packet is received",Packet_Filled_can_id)
            
        else:
             print("FAIL: new packet is not received")
        
        print("Reading IR ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("IR. reg_val_32 is", reg_val_32)
        print("\n")

        IR_RF0W = (0x00000002 & reg_val_32)>>1
        if (IR_RF0W == 1 ):
            print("PASS:Water mark is set")
        else:
            print("FAIL:Water mark not set") 
        
        IR_RF0F = (0x00000004 & reg_val_32)>>2
        if (IR_RF0F == 1 ):
            print("PASS:RX FIFO Full is set")
        else:
            print ("FAIL:RX FIFO Full not set") 
        
        IR_RF0L = (0x00000008 & reg_val_32)>>3
        if (IR_RF0L == 1 ):
            print("PASS:RX FIFO Element Lost is set")
        else:
            print("FAIL:RX FIFO Element Lost is not set") 
            
        print("Reading MsgRAM RxFiFo0 - 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
    
            
            
            
            
            
def Test_Case_22_rand_overwrite():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1


    from random import seed

    for s in range(0,1):    
        seed_id = s
        seed(seed_id) 
        print ("seed_id", seed_id)        
        Num_packets = 3#random.randint(4,18)    

        print("Num_packets",Num_packets)
        #EFS = Num_packets-1
        #print ("EFS", EFS)
        #EFWM = Num_packets-2
        #print ("EFWM", EFWM)
        rxf0c_elements = Num_packets-1
        print ("rxf0c_elements", rxf0c_elements)
        F0WM = Num_packets-2
        f0om = 1 # 0- Blocking 1- Overwrite
        print ("f0om", f0om)
      
      
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
      
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)

        #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = rxf0c_elements, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0,tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
                
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = rxf0c_elements, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0,f0wm=F0WM,f0om=f0om,tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
           
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        
        
        #for n in range(Num_packets):
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
          
            
        for n in range(Num_packets):
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=1+n, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = n)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = n, txbuf = txbuf)
            
            '''   
            txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)
               
            txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 3, txbuf = txbuf)
            '''
      
        
        for e in range(Num_packets):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = e)
        
        '''        
        print("Reading IR ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("IR TxEventFIFO can1_bar - Before verify_rx_transceiver. reg_val_32 is", reg_val_32)
        print("\n")
        
        IR_TEFW = (0x00002000 & reg_val_32)>>13
        if (IR_TEFW == 1 ):
            print("PASS:Water mark is set")
        else:
            print("FAIL:Water mark is not set") 
        
        IR_TEFF = (0x00004000 & reg_val_32)>>14
        if (IR_TEFW == 1 ):
            print("PASS:Tx Event FIFO Full is set")
        else:
            print ("FAIL:Tx Event FIFO Full is not set") 
        
        IR_TEFL = (0x00008000 & reg_val_32)>>15
        if (IR_TEFL == 1 ):
            print("PASS:Tx Event FIFO Element Lost is set")
        else:
            print("FAIL") 
        
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 120)
        print("\n")
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 50)
        print("\n")
        '''
           
            

        #Packet_dropped = CanDeviceLibrary.ReadMmio(can1_bar, (4+(0x800 + 0x3A00)+(Num_packets*4)))
        Packet_dropped = CanDeviceLibrary.ReadMmio(can1_bar, ((0x800 + 0x400)+((Num_packets-1)*0x48))) #RXFIFO increments by 0x48
        if (Packet_dropped == 0):
            print("PASS:Packet dropped after fill level")
            
        else:
             print("FAIL:Packet not dropped")
           
        #CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        #CanDeviceLibrary.verify_rx(m_bar = can0_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 120)
        print("\n")
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 50)
        print("\n")
         
        print("Reading MsgRAM RxFiFo0 - 1st time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        

        new_Packet_ID = 0xF
        
        print("Send packets after packets are drined")
        txbuf = CanDeviceLibrary.createTxPacket(can_id=new_Packet_ID, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        
        
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
     

    
    
                 
        Packet_Filled = CanDeviceLibrary.ReadMmio(can0_bar, 0x800 + 0x400) #Reading MsgRAM RxFiFo0
        
        if (Packet_Filled == 0xbc004):
            print("PASS:New packet is received",Packet_Filled)
            
        else:
             print("FAIL: new packet is not received")
        
        print("Reading IR ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("IR. reg_val_32 is", reg_val_32)
        print("\n")

        IR_RF0W = (0x00000002 & reg_val_32)>>1
        if (IR_RF0W == 1 ):
            print("PASS:Water mark is set")
        else:
            print("FAIL:Water mark not set") 
        
        IR_RF0F = (0x00000004 & reg_val_32)>>2
        if (IR_RF0F == 1 ):
            print("PASS:RX FIFO Full is set")
        else:
            print ("FAIL:RX FIFO Full not set") 
        
        IR_RF0L = (0x00000008 & reg_val_32)>>3
        if (IR_RF0L == 1 ):
            print("PASS:RX FIFO Element Lost is set")
        else:
            print("FAIL:RX FIFO Element Lost is not set") 
            
        print("Reading MsgRAM RxFiFo0 - 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
    
            
            
            
def Test_Case_22_rand_overwrite_Focus():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1


    from random import seed

    for s in range(0,1):    
        seed_id = s
        seed(seed_id) 
        print ("seed_id", seed_id)        
        Num_packets = 3#random.randint(4,18)    

        print("Num_packets",Num_packets)

        rxf0c_elements = 2#Num_packets-1
        print ("rxf0c_elements", rxf0c_elements)
        F0WM = 1#Num_packets-2
        f0om = 1 # 0- Blocking 1- Overwrite
        print ("f0om", f0om)
      
      
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
      
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)

        #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = rxf0c_elements, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0,tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
                
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = rxf0c_elements, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0,f0wm=F0WM,f0om=f0om,tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
           
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        
        
        #for n in range(Num_packets):
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
          
        #======================================================#    
        txbuf = CanDeviceLibrary.createTxPacket(can_id=1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)                   
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)                 
        print("Reading MsgRAM RxFiFo0 - 1 time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        #======================================================#  
        
        #======================================================#    
        txbuf = CanDeviceLibrary.createTxPacket(can_id=2, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 1)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 1, txbuf = txbuf)                   
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 1)                 
        print("Reading MsgRAM RxFiFo0 - 2 time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        #======================================================#    
      
        #======================================================#    
        txbuf = CanDeviceLibrary.createTxPacket(can_id=3, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 2)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 2, txbuf = txbuf)                   
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 2)                 
        print("Reading MsgRAM RxFiFo0 - 3 time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        #======================================================#    

       
        #======================================================#    
        txbuf = CanDeviceLibrary.createTxPacket(can_id=4, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 3)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 3, txbuf = txbuf)                   
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 3)                 
        print("Reading MsgRAM RxFiFo0 - 4 time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        #======================================================#    

                             

       
       
     

    
    
        
        print("Reading IR ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("IR. reg_val_32 is", reg_val_32)
        print("\n")

        IR_RF0W = (0x00000002 & reg_val_32)>>1
        if (IR_RF0W == 1 ):
            print("PASS:Water mark is set")
        else:
            print("FAIL:Water mark not set") 
        
        IR_RF0F = (0x00000004 & reg_val_32)>>2
        if (IR_RF0F == 1 ):
            print("PASS:RX FIFO Full is set")
        else:
            print ("FAIL:RX FIFO Full not set") 
        
        IR_RF0L = (0x00000008 & reg_val_32)>>3
        if (IR_RF0L == 1 ):
            print("PASS:RX FIFO Element Lost is set")
        else:
            print("FAIL:RX FIFO Element Lost is not set") 
            
     
          

def Test_case_38_External_loop_back():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)

    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x7FF
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    from random import seed
    
    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id)
        
   
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
        ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x8, 
        ntseg1 = 0x1f, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        #CanDeviceLibrary.verify_rx_tranceiver(m_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf)
        
        
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 8)
        print("\n")
        

        

        print("Reading MsgRAM RxFiFo0")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 8)
        print("\n")
        
     
        
        
        now=datetime.datetime.now()
        print(now)
            
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
     
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
        print("PSR reg_val_32 is :", reg_val_32)
        psr=(reg_val_32 & 0x00000007)
        print("LEC  is :", psr)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TEC=(reg_val_32 & 0x000000FF)
        print("TEC  is :", TEC)
    
        REC=(reg_val_32 & 0x0000FF00)>>8
        print("REC  is :", REC)
        
        
        

def Test_Case_22_rand_overwrite_rand():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1


    from random import seed

    for s in range(0,501):    
        seed_id = s
        seed(seed_id) 
        print ("seed_id", seed_id)        
        Num_packets = random.randint(4,26)    

        print("Num_packets",Num_packets)
        #EFS = Num_packets-1
        #print ("EFS", EFS)
        #EFWM = Num_packets-2
        #print ("EFWM", EFWM)
        rxf0c_elements = Num_packets-1
        print ("rxf0c_elements", rxf0c_elements)
        F0WM = Num_packets-2
        f0om = 1 # 0- Blocking 1- Overwrite
        print ("f0om", f0om)
      
      
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
      
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)

        #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = rxf0c_elements, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0,tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
                
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = rxf0c_elements, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0,f0wm=F0WM,f0om=f0om,tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
           
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        
        
        #for n in range(Num_packets):
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
          
            
        for n in range(Num_packets-1):
            
            txbuf = CanDeviceLibrary.createTxPacket(can_id=1+n, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = n)
            CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = n, txbuf = txbuf)
     
        
        for e in range(Num_packets-1):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = e)

            if (e == F0WM):
                print("Reading IR ")
                reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
                print("IR. reg_val_32 is", reg_val_32)
                print("\n")        
                IR_RF0W = (0x00000002 & reg_val_32)>>1
                if (IR_RF0W == 1 ):
                    print("PASS:Water mark is set")
                else:
                    print("FAIL:Water mark not set")             
          
            if (e == rxf0c_elements):              
                print("Reading IR ")
                reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
                print("IR. reg_val_32 is", reg_val_32)
                print("\n")       
                IR_RF0F = (0x00000004 & reg_val_32)>>2
                if (IR_RF0F == 1 ):
                    print("PASS:RX FIFO Full is set")
                else:
                    print ("FAIL:RX FIFO Full not set") 
            


           
        #CanDeviceLibrary.verify_rx(m_bar = m_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        #CanDeviceLibrary.verify_rx(m_bar = can0_bar, sfec = 0x01, pkt_cnt = 1, txbuf = txbuf , pos = 0)
        
        print("Reading MsgRAM Tx Buffer")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 120)
        print("\n")
        
        print("Reading MsgRAM Tx Event Fifo")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x3A00), dw_count = 50)
        print("\n")
         
        print("Reading MsgRAM RxFiFo0 - 1st time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        

        
        print("Send packets after packets are drained")
        txbuf = CanDeviceLibrary.createTxPacket(can_id=0xF, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)                
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
        print("Send packets after packets are drained")
        txbuf = CanDeviceLibrary.createTxPacket(can_id=0xE, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)                
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)

        Packet_Filled = 0
        Packet_Filled_can_id = 0        
        Packet_Filled = CanDeviceLibrary.ReadMmio(can0_bar, 0x800 + 0x400) #Reading MsgRAM RxFiFo0
        Packet_Filled_can_id= (Packet_Filled & 0x1FFC0000)>>18
        print("Packet_Filled_can_id is ",Packet_Filled_can_id)
        
        
        if (Packet_Filled_can_id == 0xF):
            print("PASS:New packet-1 is received",Packet_Filled_can_id)            
        else:
             print("FAIL: new packet-1 is not received")

        Packet_Filled = 0
        Packet_Filled_can_id=0        
        Packet_Filled = CanDeviceLibrary.ReadMmio(can0_bar, 0x800 + 0x400 + 0x48) #Reading MsgRAM RxFiFo0
        Packet_Filled_can_id= (Packet_Filled & 0x1FFC0000)>>18
        print("Packet_Filled_can_id is ",Packet_Filled_can_id)
             
        if (Packet_Filled_can_id == 0xE):
            print("PASS:New packet-2 is received",Packet_Filled_can_id)            
        else:
             print("FAIL: new packet-2 is not received")
             
        Packet_dropped = CanDeviceLibrary.ReadMmio(can1_bar, ((0x800 + 0x400)+((Num_packets-1)*0x48))) #RXFIFO increments by 0x48
        if (Packet_dropped == 0):
            print("PASS:Packet dropped after fill level")            
        else:
             print("FAIL:Packet not dropped")                     
        
        print("Reading IR ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("IR. reg_val_32 is", reg_val_32)
        print("\n")

        
        IR_RF0F = (0x00000004 & reg_val_32)>>2
        if (IR_RF0F == 1 ):
            print("PASS:RX FIFO Full is set")
        else:
            print ("FAIL:RX FIFO Full not set") 
        
        #TODO: Check whether IR FIFO Lost Element is set or not set in Overwrite mode
        #IR_RF0L = (0x00000008 & reg_val_32)>>3
        #if (IR_RF0L == 1 ):
        #    print("PASS:RX FIFO Element Lost is set")
        #else:
        #    print("FAIL:RX FIFO Element Lost is not set") 
            
        print("Reading MsgRAM RxFiFo0 - 2nd time")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
    
            
def Ack():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    addr_val=0x4300
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec = 0
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    TxBufferOffset = 5 #random.randint(5, 31)

   
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
  
    
    CanDeviceLibrary.can_end_communication(m_bar = m_bar)
    #eidm=0x1FFFFFFF for SFT= 0,1 2 and eidm=0 for SFT= 3
    CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
    lse = 64, flesa = 0x200, eidm = 0, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
    efsa = 0x3A00, efs = 3, efwm = 2, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = 0x50, 
    ntseg1 = 0x2d, nbrp = 1, nsjw = 0, fsjw = 0, ftseg2 = 0x4, ftseg1 = 0xd, fbrp = 0x3, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
    anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
    
   
    CanDeviceLibrary.retransmission_control(m_bar = m_bar, retransmission_disable = 1)
    CanDeviceLibrary.loopback_control(m_bar = m_bar, internal_loopback  = 0 , loopback_enable  = 0)
    CanDeviceLibrary.can_start_communication(m_bar = m_bar)
    
    #TODO: create11bitFilter
    val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7ff)
    CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
    #TODO: Push11bitFilter
    
    
    from random import seed
    for i in range (0,1):
        seed_id = i
        seed(seed_id)
        #TODO check later # addr_list = range(0x4300,0x4781,0x4)
        #addr_list = range(0x3B00+(TxBufferOffset*16),0x3B00+(TxBufferOffset*16)+15,0x4)
        #addr_val = 0x800 + random.choice(addr_list)
        print("SEED_ID is",seed_id)
        
        '''
         ##===============adjacent offsets===============================##
        data = random.randint(1,65535)
        
       
        data_previous = random.randint(1,65535)
        data_next = random.randint(1,65535)
        
        
        data_hex = '0x{0:08X}'.format(data)
        data_hex_previous = '0x{0:08X}'.format(data_previous)
        data_hex_next = '0x{0:08X}'.format(data_next)       
        ##===============================================================##
        '''

        
       

        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
        print("PSR reg_val_32 is :", reg_val_32)
        psr=(reg_val_32 & 0x00000007)
        print("LEC  is :", psr)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TEC=(reg_val_32 & 0x000000FF)
        print("TEC  is :", TEC)
    
        REC=(reg_val_32 & 0x0000FF00)>>8
        print("REC  is :", REC)
        ##==============================================================================================## 
		##=====================================Packets are written to TX buffer before ERR_INJ===============================##
        for i in range (0,5):
            txbuf = CanDeviceLibrary.createTxPacket(can_id=i+1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
            CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf) 

        for i in range (0,5):
            CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = i)
            CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf, pos=0)
        
  
       
        print("Reading MsgRAM Tx Buffer-before ERR_INJ")
        #addr = (0x800 + 0x3B00) + addr_val
        CanDeviceLibrary.ReadRAM(m_bar= m_bar,addr = (0x800 + 0x3B00), dw_count = 100)
        print("\n")
                
        

        print("Reading MsgRAM RxFiFo0--before ERR_INJ")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 100)
        print("\n")
               
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
         
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================## 
        
        
        
 

        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
        print("PSR reg_val_32 is :", reg_val_32)
        psr=(reg_val_32 & 0x00000007)
        print("LEC  is :", psr)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TEC=(reg_val_32 & 0x000000FF)
        print("TEC  is :", TEC)
    
        REC=(reg_val_32 & 0x0000FF00)>>8
        print("REC  is :", REC)
        
                               
def Test_Case_27_CAN0_to_Vector_rand():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    #sfec_values = [1]
    can_id_vector_CAN0 = 5#random.randint(0x1, 0xFE)
    #can_id_vector_CAN1 = random.randint(0xFF, 0x7FF)
    
    print ("can_id_vector_CAN0 is", can_id_vector_CAN0)
    #print ("can_id_vector_CAN1 is", can_id_vector_CAN1)
   # Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0, brs=0 )

    # Randomly choose a value for sfec
    #sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed
    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        #CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
        #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
        #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        
        '''
        for i in range(0,2):
        
            msg=Vector_bus.recv(10)
            if msg:
                print("vector data",msg)

                if (msg.arbitration_id != 0):
                    print ("PASS")
                else:
                    print ("FAIL")
                
            else:
                print("FAIL :No vector data received")
        '''

        print("Reading TEST ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.TEST.offset)
        print("TEST is", reg_val_32)
        print("\n")  

        print("Reading MsgRAM Tx Buffer CAN0")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Tx Buffer CAN1")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
        print("\n")
        
        
        
        
def Test_case_27_Vector_to_CAN0():
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
       # CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
       # CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        print("send packet from Vector...")
        time.sleep(30)
        
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector,channel=0 )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        print("Reading MsgRAM RxFiFo0 CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
 
        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''
        
        
def Multinetwork_Vector_CAN1(pool=True):
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        #CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        '''
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        #CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        #CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        
        #RX filter 
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1FFFF, esync = 0x0, efid2 = 0x1FFFFF)
        CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        print(f"TC1: create11bitFilter() sfec = {sfec} val={val}")
        
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector,channel=0 )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        
        IR_RF1N=0
        
        while(IR_RF1N==0 and pool):
            print("Reading Paity IR_RF1N")
            
            '''
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32) 
            '''
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("can0_bar_IR is", reg_val_32)
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
            print("can1_bar_IR is", reg_val_32)
            
            
            
            reg_val_32 = (reg_val_32&0x00000010) >>4
            
            print("IR_RF1N is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF1N=1
                print("IR_RF1N is set to 1")
            else:
                print("IR_RF1N is not equal to 1")
            
            
                print("\n")  
        

        
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")   


      
        
        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''
        
def Multinetwork_Vector_CAN0(pool=True):
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        #CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        print("#########3before RX filter config#####")
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        #print("IR_RF0N_1 is", reg_val_32)
        print("CAN1_IR is", reg_val_32)
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        #print("IR_RF0N_1 is", reg_val_32)
        print("CAN0_IR is", reg_val_32)        
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        '''
        val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 0x01, efid1 = 0x1FFFF, esync = 0x0, efid2 = 0x1FFFFF)
        CanDeviceLibrary.push29BitFilter(m_bar = m_bar, pos = 0, filt = val)
        '''
        print(f"TC2: create11bitFilter() sfec = {sfec} val={val}")
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector,channel=0 )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        
        IR_RF0N=0
        while(IR_RF0N==0 and pool == True):
            print("Reading Paity IR_RF0N")
            
            '''
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32) 
            '''
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
            #print("IR_RF0N_1 is", reg_val_32)
            print("CAN1_IR is", reg_val_32)
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            #print("IR_RF0N_1 is", reg_val_32)
            print("CAN0_IR is", reg_val_32)
            

            
            reg_val_32 = 0x00000001&reg_val_32
            
            print("IR_RF0N_2 is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF0N=1
                print("IR_RF0N is set to 1")
            else:
                print("IR_RF0N is not equal to 1")
            
            
                print("\n")  
        

        '''
        print("Reading MsgRAM Rx Fifo0_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo0_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")       
        '''

        print("Reading MsgRAM RxFiFo0_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
    
        print("Reading MsgRAM RxFiFo0_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
        
        '''
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")   
        '''
        
        

        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''       
             
def Multinetwork_Vector_Receive_CAN0():
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        #CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        txbuf = CanDeviceLibrary.createTxPacket(can_id=0x5, rtr = 1, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        print("Reading MsgRAM Tx Buffer CAN0")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        




        


def Multinetwork_Vector_Receive_CAN0_CAN1():
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        #CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector,channel=0 )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        
        IR_RF0N=0
        while(IR_RF0N==0):
            print("Reading Paity IR_RF0N")
            
            '''
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32) 
            '''
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32)
            reg_val_32 = reg_val_32
            
            print("IR_RF0N_2 is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF0N=1
                print("IR_RF0N is set to 1")
            else:
                print("IR_RF0N is not equal to 1")
            
            
                print("\n")  
        

        
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")        
        
        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''        
def Test_Case_27_CAN1_to_Vector_rand():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    can_id_vector_CAN0 = random.randint(0x1, 0xFE)
    can_id_vector_CAN1 = random.randint(0xFF, 0x7FF)
    
    print ("can_id_vector_CAN0 is", can_id_vector_CAN0)
    print ("can_id_vector_CAN1 is", can_id_vector_CAN1)
    Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0, brs=0 )

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed
    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        #CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        '''
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        #CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        #CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
        #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
        #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        for i in range(0,2):
        
            msg=Vector_bus.recv(10)
            if msg:
                print("vector data",msg)

                if (msg.arbitration_id != 0):
                    print ("PASS")
                else:
                    print ("FAIL")
                
            else:
                print("FAIL :No vector data received")
        

        

        print("Reading MsgRAM Tx Buffer CAN0")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Tx Buffer CAN1")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
        print("\n")
        

def Test_case_27_Vector_to_CAN1():
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    can_id_vector = random.randint(0x1, 0x7FF)
    print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    can_id_vector = 1 #random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        print ("can_id_vector is", can_id_vector)
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
      #  CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        '''
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
      #  CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
       # CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
       # CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        print("Reading MsgRAM RxFiFo0 CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
 

        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        
        
        
               
        
def Test_Case_27_CAN0_to_Vector_CAN1_to_Vector_rand():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    #sfec_values = [1]
    can_id_vector_CAN0 = 1#random.randint(0x1, 0xFE)
    can_id_vector_CAN1 = 2#random.randint(0xFF, 0x7FF)
    
    print ("can_id_vector_CAN0 is", can_id_vector_CAN0)
    print ("can_id_vector_CAN1 is", can_id_vector_CAN1)
    Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0, brs=0 )
    Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0, brs=0 )

    # Randomly choose a value for sfec
    #sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp_0 = 1
    ntseg1_0 = 63
    ntseg2_0 = 16
    
    #1000kbps
    nbrp_1 = 1
    ntseg1_1 = 31
    ntseg2_1 = 8
    
    #2000kbps
    fbrp = 1
    ftseg1 = 15
    ftseg2 = 4
    
    
    
    CAN0_nbrp = nbrp_0-1
    CAN0_ntseg1 = ntseg1_0-1
    CAN0_ntseg2 = ntseg2_0-1
    
    
    CAN1_nbrp = nbrp_1-1
    CAN1_ntseg1 = ntseg1_1-1
    CAN1_ntseg2 = ntseg2_1-1
    
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed
    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = CAN0_ntseg2, 
        ntseg1 = CAN0_ntseg1, nbrp = CAN0_nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = CAN1_ntseg2, 
        ntseg1 = CAN1_ntseg1, nbrp = CAN1_nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
        #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
        #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        for i in range(0,2):
        
            msg=Vector_bus.recv(10)
            if msg:
                print("vector data",msg)

                if (msg.arbitration_id != 0):
                    print ("PASS")
                else:
                    print ("FAIL")
                
            else:
                print("FAIL :No vector data received")
        

        print("Reading TEST ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.TEST.offset)
        print("TEST is", reg_val_32)
        print("\n")  

        print("Reading MsgRAM Tx Buffer CAN0")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Tx Buffer CAN1")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
        print("\n")
        
def Test_case_27_Vector_to_CAN0_Vector_CAN1():
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    
    ############Packets Randamiztion#####################
    num_packets = random.randint(1, 31)
    print ("num_packets is", num_packets)
    #####################################################


    ############Data and Remote Frame Randamiztion ######
    rand_data_remote_pkt = random.randint(0, 1)
    print ("rand_data_remote_pkt is", rand_data_remote_pkt)
    #####################################################
    
    
    ############11 and 29 bit identifier#################
    identifiers = random.randint(0, 1)
    print ("rand_data_remote_pkt is", rand_data_remote_pkt)
    #####################################################
    
    
    
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    can_id_vector1 = random.randint(0x1, 0xE)
    print ("can_id_vector1 is", can_id_vector1)
  
  

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    can_id_vector2 = random.randint(0xF, 0x7FF)
    print ("can_id_vector2 is", can_id_vector2)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
       
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        
        
        #################### 11 bit identifier##############################################################
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0xE)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0xF, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
       
        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector1,channel=0 )
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector2,channel=1 )
        
        ######################################################################################################
        
        
        
        
        
        ###########################################29 bit filter###############################################
        
        val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = efec, efid1 = 0, esync = 0x0, efid2 = 0x1FFF0000)
        CanDeviceLibrary.push29BitFilter(m_bar = can1_bar, pos = 0, filt = val)
    
        #print("send packet from Vector...")
        #time.sleep(30)
    
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 10, brs = 0, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        CanDeviceLibrary.verify_rx_tranceiver(m_bar = can1_bar, sfec = sfec, pkt_cnt = 1, txbuf = txbuf,pos = 0)

         ######################################################################################################



        
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        
        print("Reading MsgRAM RxFiFo0 CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
 

        #CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)        
 
 
 
def Multinetwork_Vector_CAN1_FIFO0(pool=True):
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        #CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        #CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        '''
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        #CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        #CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        
        #RX filter 
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        print(f"TC1: create11bitFilter() sfec = {sfec} val={val}")
        
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector,channel=0 )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        
        IR_RF1N=0
        
        while(IR_RF1N==0 and pool):
            print("Reading Paity IR_RF1N")
            
            '''
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32) 
            '''
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("can0_bar_IR is", reg_val_32)
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
            print("can1_bar_IR is", reg_val_32)
            
            
            
            reg_val_32 = (reg_val_32&0x00000010) >>4
            
            print("IR_RF1N is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF1N=1
                print("IR_RF1N is set to 1")
            else:
                print("IR_RF1N is not equal to 1")
            
            
                print("\n")  
        

        
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")   


      
        
        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''


def Multinetwork_Vector_CAN1_CAN0_both_filter(pool=True):
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        #CAN 1 as 500Kbps
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        
        #CAN 1 as 1000KBPS
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 0, 
        
        ntseg2 = ftseg2, ntseg1 = ftseg1, nbrp = fbrp, nsjw = 0, 
        ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, fsjw = 0, 
        
        tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        
        #RX filter 
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x5)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 6, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        print(f"TC1: create11bitFilter() sfec = {sfec} val={val}")
        
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector,channel=0 )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        
        print("send packet from Vector...")
        time.sleep(30)
        
        IR_RF1N=0
        
        while(IR_RF1N==0 and pool):
            print("Reading Paity IR_RF1N")
            
            '''
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32) 
            '''
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("can0_bar_IR is", reg_val_32)
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
            print("can1_bar_IR is", reg_val_32)
            
            
            
            reg_val_32 = (reg_val_32&0x00000010) >>4
            
            print("IR_RF1N is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF1N=1
                print("IR_RF1N is set to 1")
            else:
                print("IR_RF1N is not equal to 1")
            
            
                print("\n")  
        

        
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")   


      
        
        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''
        
def Multinetwork_Vector_CAN0(pool=True):
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        #CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        print("#########3before RX filter config#####")
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        #print("IR_RF0N_1 is", reg_val_32)
        print("CAN1_IR is", reg_val_32)
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        #print("IR_RF0N_1 is", reg_val_32)
        print("CAN0_IR is", reg_val_32)        

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        print(f"TC2: create11bitFilter() sfec = {sfec} val={val}")
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector,channel=0 )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        
        IR_RF0N=0
        while(IR_RF0N==0 and pool == True):
            print("Reading Paity IR_RF0N")
            
            '''
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32) 
            '''
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
            #print("IR_RF0N_1 is", reg_val_32)
            print("CAN1_IR is", reg_val_32)
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            #print("IR_RF0N_1 is", reg_val_32)
            print("CAN0_IR is", reg_val_32)
            

            
            reg_val_32 = 0x00000001&reg_val_32
            
            print("IR_RF0N_2 is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF0N=1
                print("IR_RF0N is set to 1")
            else:
                print("IR_RF0N is not equal to 1")
            
            
                print("\n")  
        

        '''
        print("Reading MsgRAM Rx Fifo0_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo0_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")       
        '''

        print("Reading MsgRAM RxFiFo0_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
    
        print("Reading MsgRAM RxFiFo0_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
        
        '''
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")   
        '''
        
        

        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''       

def Multinetwork_Vector_CAN0_CAN_FD(pool=True):
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        #CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        print("#########3before RX filter config#####")
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        #print("IR_RF0N_1 is", reg_val_32)
        print("CAN1_IR is", reg_val_32)
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        #print("IR_RF0N_1 is", reg_val_32)
        print("CAN0_IR is", reg_val_32)        

        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        print(f"TC2: create11bitFilter() sfec = {sfec} val={val}")
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector,channel=0 )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        
        IR_RF0N=0
        while(IR_RF0N==0 and pool == True):
            print("Reading Paity IR_RF0N")
            
            '''
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32) 
            '''
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
            #print("IR_RF0N_1 is", reg_val_32)
            print("CAN1_IR is", reg_val_32)
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            #print("IR_RF0N_1 is", reg_val_32)
            print("CAN0_IR is", reg_val_32)
            

            
            reg_val_32 = 0x00000001&reg_val_32
            
            print("IR_RF0N_2 is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF0N=1
                print("IR_RF0N is set to 1")
            else:
                print("IR_RF0N is not equal to 1")
            
            
                print("\n")  
        

        '''
        print("Reading MsgRAM Rx Fifo0_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo0_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")       
        '''

        print("Reading MsgRAM RxFiFo0_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
    
        print("Reading MsgRAM RxFiFo0_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 50)
        print("\n")
        
        '''
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 80)
        print("\n")   
        '''
        
        

        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''       
        
        
def Multinetwork_Vector_CAN1_CAN0_both_filter_venkat_fd(pool=True):
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1,
        ntseg2 = ntseg2, ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, 
        ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, fsjw = 0, 
        tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        #CAN 1 as 500Kbps
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        
        #CAN 1 as 1000KBPS
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 0, 
        
        ntseg2 = ftseg2, ntseg1 = ftseg1, nbrp = fbrp, nsjw = 0, 
        ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, fsjw = 0, 
        
        tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        
        #RX filter 
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x5)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
        val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = sfec, efid1 = 0x1, esync = 0x0, efid2 = 0x1FFFFFFF)
        CanDeviceLibrary.push29BitFilter(m_bar = can0_bar, pos = 0, filt = val)
       
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 6, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = sfec, efid1 = 0x0000001, esync = 0x0, efid2 = 0x1FFFFFFF)
        CanDeviceLibrary.push29BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        print(f"TC1: create11bitFilter() sfec = {sfec} val={val}")
        
        '''
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x7F, ssync = 0, sfid2 = 0x7FF)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        '''

        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        #CanDeviceLibrary.vector_to_can_send(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0,remote_frame=0, dlc=8,arbitration_id =can_id_vector,channel=0 )




        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        
        print("send packet from Vector...")
        time.sleep(10)
        
        IR_RF1N=0
        
        while(IR_RF1N==0 and pool):
            print("Reading Paity IR_RF1N")
            
            '''
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32) 
            '''
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("can0_bar_IR is", reg_val_32)
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
            print("can1_bar_IR is", reg_val_32)
            
            
            
            reg_val_32 = (reg_val_32&0x00000010)>>4
            
            print("IR_RF1N is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF1N=1
                print("IR_RF1N is set to 1")
            else:
                print("IR_RF1N is not equal to 1")
            
            
                print("\n")  
        

        
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x640), dw_count = 100)
        print("\n")
        
        print("Reading MsgRAM Rx Fifo1_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= m_bar, addr = (0x800 + 0x640), dw_count = 100)
        print("\n")   

        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PSR.offset)
        print("can0_PSR_IR is", reg_val_32)
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
        print("can1_PSR_IR is", reg_val_32)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.ECR.offset)
        print("can0_ECR_IR is", reg_val_32)
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
        print("can1_ECR_IR is", reg_val_32)

      
        
        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''
        
def Multinetwork_Vector_CAN1_CAN0_both_filter_Harshini_fd(pool=True):
    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]
    #can_id_vector = random.randint(0x1, 0x7FF)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #print ("can_id_vector is", can_id_vector)
    '''
    can_id_can0 = random.randint(9,0xA)
    print ("can_id_can0 is", can_id_can0)
    can_id_can1 = random.randint(0xB, 0xF)
    print ("can_id_can1 is", can_id_can1)
    '''
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    #can_id_vector = random.randint(0x1, 0x7FF)
    
    #can_id_can0 = random.randint(0x0A, 0xB)
    #print ("can_id_can0 is", can_id_can0)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 55
    ntseg2 = 24
    
    '''
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    '''
    
    '''
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    '''
    '''
    #2000kbps
    fbrp = 1
    ftseg1 = 15
    ftseg2 = 4
    '''
    #2000kbps
    fbrp = 1
    ftseg1 = 13
    ftseg2 = 6
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed

    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        #print ("can_id_vector is", can_id_vector)
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
        
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1,
        ntseg2 = ntseg2, ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, 
        ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, fsjw = 0, 
        tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1,
        ntseg2 = ntseg2, ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, 
        ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, fsjw = 0, 
        tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
 

        
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        
        #RX filter 
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 1, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = 0, filt = val)
        
        val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 1, efid1 = 0x1, esync = 0x0, efid2 = 0x1FFFFFFF)
        CanDeviceLibrary.push29BitFilter(m_bar = can0_bar, pos = 0, filt = val)
        
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = 2, sfid1 = 1, ssync = 0, sfid2 = 0x7E)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        val = CanDeviceLibrary.create29bitFilter(eft = 0x0, efec = 2, efid1 = 0x0000001, esync = 0x0, efid2 = 0x1FFFFFFF)
        CanDeviceLibrary.push29BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        print(f"TC1: create11bitFilter() sfec = {sfec} val={val}")
        





        '''
        print("Reading MsgRAM RxFiFo0 CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 + 0x400), dw_count = 150)
        print("\n")
        '''
        
        #print("send packet from Vector...")
        #time.sleep(10)
        
        
        IR_RF0N=0
        while(IR_RF0N==0 and pool == True):
            print("Reading Paity IR_RF0N")
            

            reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
            #print("IR_RF0N_1 is", reg_val_32)
            print("CAN1_IR is", reg_val_32)
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            #print("IR_RF0N_1 is", reg_val_32)
            print("CAN0_IR is", reg_val_32)
            

            
            reg_val_32 = 0x00000001&reg_val_32
            
            print("IR_RF0N_2 is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF0N=1
                print("IR_RF0N is set to 1")
            else:
                print("IR_RF0N is not equal to 1")
            
            
                print("\n")  
        
        
        
               
        IR_RF1N=0
        
        while(IR_RF1N==0 and pool):
            print("Reading Paity IR_RF1N")
            
            '''
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("IR_RF0N_1 is", reg_val_32) 
            '''
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
            print("can0_bar_IR is", reg_val_32)
            
            reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
            print("can1_bar_IR is", reg_val_32)
            
            
            
            reg_val_32 = (reg_val_32&0x00000010) >>4
            
            print("IR_RF1N is", reg_val_32)
            if(reg_val_32 == 1):
                IR_RF1N=1
                print("IR_RF1N is set to 1")
            else:
                print("IR_RF1N is not equal to 1")
            
            
                print("\n")  
        
        

        
        print("Reading MsgRAM Rx Fifo 0_CAN0")
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0xA00+0x200), dw_count = 100)
        print("\n")
        
        '''
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0xC00 +  0x1200), dw_count = 100)
        print("\n")   
        '''
        
        print("Reading MsgRAM Rx Fifo1_CAN1")
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar, addr = (0x800 +  0x640), dw_count = 100)
        print("\n")   
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PSR.offset)
        print("can0_PSR_IR is", reg_val_32)
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
        print("can1_PSR_IR is", reg_val_32)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.ECR.offset)
        print("can0_ECR_IR is", reg_val_32)
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
        print("can1_ECR_IR is", reg_val_32)

      
        
        '''
        CanDeviceLibrary.verify_rx_testcase_25(m_bar = m_bar, can1_bar=can1_bar, addr=(0x800 + 0x400), can0_sfid1=1, can0_sfid2=0x7E,can1_sfid1=0x7F, can1_sfid2=0x7FF, sent_can_id=can_id_vector, num_packets=1)
        '''
def Test_Case_27_CAN0_Send_to_Vector_Receive_Classic():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    #sfec_values = [1]
    can_id_vector_CAN0 = 5#random.randint(0x1, 0xFE)
    #can_id_vector_CAN1 = random.randint(0xFF, 0x7FF)
    
    print ("can_id_vector_CAN0 is", can_id_vector_CAN0)
    #print ("can_id_vector_CAN1 is", can_id_vector_CAN1)
   # Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0, brs=0 )

    # Randomly choose a value for sfec
    #sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed
    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        #CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
        #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
        #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN0, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        
        ##==============================================================================================##   
        ##==================Read TXBRP,TXBTO,TC=============================================## 
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("TXBRP reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
            
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
             
            
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("ECR reg_val_32 is :", reg_val_32)
        TC=(reg_val_32 & 0x00000200)>>9
        print("TC  is :", TC)
        print("\n")
        print("\n")
        ##==============================================================================================##  
        
        '''
        for i in range(0,2):
        
            msg=Vector_bus.recv(10)
            if msg:
                print("vector data",msg)

                if (msg.arbitration_id != 0):
                    print ("PASS")
                else:
                    print ("FAIL")
                
            else:
                print("FAIL :No vector data received")
        '''

        print("Reading TEST ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.TEST.offset)
        print("TEST is", reg_val_32)
        print("\n")  

        print("Reading MsgRAM Tx Buffer CAN0")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Tx Buffer CAN1")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
        print("\n")
        

def Test_Case_27_CAN0_Send_to_Vector_Receive_CAN_FD():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    #sfec_values = [1]
    can_id_vector_CAN0 = 5#random.randint(0x1, 0xFE)
    #can_id_vector_CAN1 = random.randint(0xFF, 0x7FF)
    
    print ("can_id_vector_CAN0 is", can_id_vector_CAN0)
    #print ("can_id_vector_CAN1 is", can_id_vector_CAN1)
   # Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0, brs=0 )

    # Randomly choose a value for sfec
    #sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    '''
    #500kbps , 80%
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    '''
    #500kbps , 70% , total =80(Ntseg1+Ntseg2--64+16), 80*0.7=56, 56-1=55.....Ntseg1=55 and Ntseg2=total-ntseg1 (80-56=24), ntseg2=24
    nbrp = 1
    ntseg1 = 55
    ntseg2 = 24
    
    '''
    #1000kbps- (31+1)/(31+1+8)- 80%
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    '''
    
    #1000kbps- 70% 40*0.7= 28-1=27 :1 is for synchroniation
    fbrp = 1
    ftseg1 = 27
    ftseg2 = 12
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed
    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        #CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
        #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
        #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN0, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        
        '''
        for i in range(0,2):
        
            msg=Vector_bus.recv(10)
            if msg:
                print("vector data",msg)

                if (msg.arbitration_id != 0):
                    print ("PASS")
                else:
                    print ("FAIL")
                
            else:
                print("FAIL :No vector data received")
        '''

        print("Reading TEST ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.TEST.offset)
        print("TEST is", reg_val_32)
        print("\n")  

        print("Reading MsgRAM Tx Buffer CAN0")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Tx Buffer CAN1")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
        print("\n")
                
def Test_Case_27_CAN0_Send_to_Vector_Receive_CAN_FD_diff_baud():
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    #tx_data = [0x0437456, 0x03468, 0x02236, 0x0146,0x0845, 0x07576, 0x06367, 0x0534]
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    #tx_data = [0x01, 0x02, 0x03, 0x04,0x05, 0x06, 0x07, 0x08]
    #0x03468<<4 
    #0x04030201
    #0x08070605
    txbuf = []
    m_bar = can0_bar
    sft = 0
    #sfec_values = [1]
    can_id_vector_CAN0 = 5#random.randint(0x1, 0xFE)
    #can_id_vector_CAN1 = random.randint(0xFF, 0x7FF)
    
    print ("can_id_vector_CAN0 is", can_id_vector_CAN0)
    #print ("can_id_vector_CAN1 is", can_id_vector_CAN1)
   # Vector_bus=CanDeviceLibrary.can_vector_receive(fd = 0,can_bitrate=500000, fd_bitrate=0, is_extended=0, brs=0 )

    # Randomly choose a value for sfec
    #sfec = random.choice(sfec_values)
    #min_can_id = 0x001  # Minimum possible value (1 in decimal)
    #max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    #can_id = random.randint(min_can_id, max_can_id)
    can_id = 0x05
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    '''
    #500kbps
    nbrp = 1
    ntseg1 = 63
    ntseg2 = 16
    
    #1000kbps
    fbrp = 1
    ftseg1 = 31
    ftseg2 = 8
    '''
    #500kbps
    nbrp = 1
    ntseg1 = 55
    ntseg2 = 24
    
 #{ Name := "2000kbps/80.00%"; Nbrp := 1; Nsjw := 0; Ntseg1 := 15; Ntseg2 := 4; },: 80% baud rate
    '''
    fbrp = 1
    ftseg1 = 15
    ftseg2 = 4
    '''
    '''
#{ Name := "2000kbps/80.00%"; Nbrp := 1; Nsjw := 0; Ntseg1 := 15; Ntseg2 := 4; },: 70% baud rate
    
    #2000kbps
    fbrp = 1
    ftseg1 = 13
    ftseg2 = 6
    '''
    
#Name := "4000kbps/80.00%"; Nbrp := 1; Nsjw := 0; Ntseg1 := 7; Ntseg2 := 2; 
#Name := "4000kbps/70.00%";7+1+2=10, 10*0.7=7, 7-1=6=ntseg1,10-7=3=ntseg2

   #4000kbps
    fbrp = 1
    ftseg1 = 6
    ftseg2 = 4
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1
    
    from random import seed
    for i in range(0,1):    
        seed_id = i
        seed(seed_id)
        print ("seed_id is", seed_id) 
        CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
        #CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        
        
     
        
        
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 1, brse = 1, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        '''
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = 0, brse = 0, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        '''
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        #CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        #CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar)
        #CanDeviceLibrary.can_start_communication(m_bar = can1_bar)

        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0, ssync = 0, sfid2 = 0x50)
        #CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = 0, filt = val)
        
        #val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 0x60, ssync = 0, sfid2 = 0x80)
        #CanDeviceLibrary.push11BitFilter(m_bar = m_bar, pos = 0, filt = val)
        
        #print("send packet from Vector...")
        #time.sleep(30)
        
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN1, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = 0, fdf = 0, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = can1_bar, pos = 0)
        '''
        txbuf = CanDeviceLibrary.createTxPacket(can_id=can_id_vector_CAN0, rtr = 0, xtd = 1, esi = 0, mm = 0x1, dlc = 8, brs = 1, fdf = 1, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = 0)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = 0, txbuf = txbuf)
        CanDeviceLibrary.pushTxPacketTxbar(m_bar = m_bar, pos = 0)
        
        '''
        for i in range(0,2):
        
            msg=Vector_bus.recv(10)
            if msg:
                print("vector data",msg)

                if (msg.arbitration_id != 0):
                    print ("PASS")
                else:
                    print ("FAIL")
                
            else:
                print("FAIL :No vector data received")
        '''

        print("Reading TEST ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.TEST.offset)
        print("TEST is", reg_val_32)
        print("\n")  

        print("Reading MsgRAM Tx Buffer CAN0")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can0_bar,addr = addr, dw_count = 80)
        print("\n")
        
        print("Reading MsgRAM Tx Buffer CAN1")
        addr = (0x800 + 0x3B00)
        CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 80)
        print("\n")     

    
def thrdfn_can0_send_Vector_26680_receive(runtime_secs=30,baud_rate=0):
    
    start_time = time.time()
    lock = threading.Lock()
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    start_time = time.time()

    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        

    global Thread3_completed
    global txbuf
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    

    brs = 0
    fdf = 0
    

        #1000kbps
    nbrp = 1
    ntseg1 = 27
    ntseg2 = 12
    
    #1000kbps
    fbrp = 1
    ftseg1 = 13
    ftseg2 = 6
    fdoe = 0
    brse = 0
    
    if(baud_rate == 1):
        fdoe = 1
        brse = 1
        brs = 1
        fdf = 1
    
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1    

    while(True):
        time.sleep(3)
        if(Thread2_completed==True):
            break
    lock.acquire()
    for i in range(0,32):
        CanDeviceLibrary.can_setup(m_bar = m_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = fdoe, brse = brse, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        

        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = m_bar) 
        
        can_id_rand = random.randint(min_can_id, max_can_id) 
        xtd = 0   
        canID = can_id_rand
        

        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=canID, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = brs, fdf = fdf, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
        CanDeviceLibrary.pushTxPacketRam(m_bar = m_bar, pos = i, txbuf = txbuf)       

    reg_val_32 = 0xffffffff
    CanDeviceLibrary.WriteMmio(m_bar, can0.TXBAR.offset, reg_val_32)
    print("TXBAR.offset - Number of buffer elements enabled are:", reg_val_32)
    lock.release()
    
    print("CAN0 Sent a Packet to Vector")


    TXBRP=0
    PSR =0
    ECR =0
    PSR1 =0
    err = 0
    
        
    while((TXBRP==0) and ((PSR==0) or (PSR1 ==0)) and (ECR==0)):
        # print("Reading Paity IR_RF1N")
        # time.sleep(3)
        cur_time = time.time()
        if(cur_time> start_time+runtime_secs):
            print("T1 - Completed run time",runtime_secs)
            break
        
        cur_time = time.time()
        if(cur_time> start_time+runtime_secs):
            print("T1 - Completed run time",runtime_secs)
            break
        TXBRP = CanDeviceLibrary.ReadMmio(can0_bar, can0.TXBRP.offset)
        print("can0_TXBRP is", TXBRP)
        
  
        PSR = CanDeviceLibrary.ReadMmio(can0_bar, can0.PSR.offset)
        print("can0_PSR_IR is", PSR)
        PSR= PSR& 0x00000003
        print("can0_PSR_IR is", PSR)
        if ((PSR == 0) or (PSR == 7)):
            PSR1 = 0
            print("PASS")      
        else:
            print("FAIL")
            err=err | 1
        
        PSR = CanDeviceLibrary.ReadMmio(can0_bar, can0.PSR.offset)
        print("can0_PSR_IR is", PSR)
        PSR= PSR& 0x00000040
        print("can0_PSR_IR is", PSR)
        if (PSR == 0):
            print("PASS")
        else:
            print("FAIL")
            err=err | 1

        ECR = CanDeviceLibrary.ReadMmio(can0_bar, can0.ECR.offset)
        print("can0_ECR is", ECR)
        
        if(err == 0):
            break
        
        
    Thread3_completed = True
    print("thread 3 completed................... \n")
    print("\n")

def thrdfn_Vector_26681_send_can1_receive(runtime_secs=30,baud_rate=0):

    start_time = time.time()
    extra_secs= 30
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    lock = threading.Lock()
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    can_id_sent_array =[]
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)
    start_time = time.time()
    global Thread2_completed

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]
    
        #1000kbps
    nbrp = 1
    ntseg1 = 27
    ntseg2 = 12
    
    #1000kbps
    fbrp = 1
    ftseg1 = 13
    ftseg2 = 6
    
    fdoe = 0
    brse = 0
    if(baud_rate == 1):
        fdoe = 1
        brse = 1
        brs = 1
        fdf = 1
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)

    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    while(True):
        time.sleep(3)
        if(Thread1_completed==True):
            break
    lock.acquire()
    for i in range(0,32):
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = fdoe, brse = brse, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can1_bar, pos = i, filt = val) 
    lock.release()
        
    print("CAN1 is ready to receive")
        
        
    IR_RF1N=0
        
    while(IR_RF1N==0):
        # print("Reading Paity IR_RF1N")
        time.sleep(3)
        
        cur_time = time.time()
        if(cur_time> start_time+runtime_secs):
            print("T1 - Completed run time",runtime_secs)
            break

        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("can0_bar_IR is", reg_val_32)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("can1_bar_IR is", reg_val_32)
        
        '''
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.PSR.offset)
        print("can0_PSR_IR is", reg_val_32)
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
        print("can1_PSR_IR is", reg_val_32)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.ECR.offset)
        print("can0_ECR_IR is", reg_val_32)
            
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
        print("can1_ECR_IR is", reg_val_32)
        '''
        print("\n")

        
        
        reg_val_32 = (reg_val_32&0x00000040) >>6
        
        # print("IR_RF1N is", reg_val_32)
        if(reg_val_32 == 1):
            IR_RF1N=1
            print("IR_RF1N is set to 1")
            break
        else:
            print("IR_RF1N is not equal to 1")
        
        
            # print("\n")
    Thread2_completed = True
    print("thread 3 completed................... \n")

def thrdfn_can1_send_Vector_26681_receive(runtime_secs=30,baud_rate=0):

    global Thread4_completed
    start_time = time.time()
    lock = threading.Lock()
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    start_time = time.time()

    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    global txbuf
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [1]
    # return 1
    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0
    

    brs = 0
    fdf = 0
    

        #1000kbps
    nbrp = 1
    ntseg1 = 27
    ntseg2 = 12
    
    #1000kbps
    fbrp = 1
    ftseg1 = 13
    ftseg2 = 6
    fdoe = 0
    brse = 0
    
    if(baud_rate == 1):
        fdoe = 1
        brse = 1
        brs = 1
        fdf = 1
    
    
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1  
        
    while(True):
        time.sleep(3)
        if(Thread3_completed==True):
            break
    lock.acquire()
    for i in range(0,32):
        CanDeviceLibrary.can_setup(m_bar = can1_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = fdoe, brse = brse, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        

        
        CanDeviceLibrary.retransmission_control(m_bar = can1_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can1_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = can1_bar) 
        
        can_id_rand = random.randint(min_can_id, max_can_id) 
        xtd = 0   
        canID = can_id_rand
        

        
        txbuf = CanDeviceLibrary.createTxPacket(can_id=canID, rtr = 0, xtd = 0, esi = 0, mm = 0x1, dlc = 8, brs = brs, fdf = fdf, tsce = 0, efc = 1, txbuf = txbuf, tx_data = tx_data, pos = i)
        CanDeviceLibrary.pushTxPacketRam(m_bar = can1_bar, pos = i, txbuf = txbuf)       

    reg_val_32 = 0xffffffff
    CanDeviceLibrary.WriteMmio(can1_bar, can1.TXBAR.offset, reg_val_32)
    print("TXBAR.offset - Number of buffer elements enabled are:", reg_val_32)
    lock.release()
    
    print("CAN1 Sent a Packet to Vector")

    TXBRP=0
    PSR =0
    ECR =0
    PSR1 =0
    err = 0
    
        
    while((TXBRP==0) and ((PSR==0) or (PSR1 ==0)) and (ECR==0)):
        # print("Reading Paity IR_RF1N")
        # time.sleep(3)
        cur_time = time.time()
        if(cur_time> start_time+runtime_secs):
            print("T1 - Completed run time",runtime_secs)
            break
        
        cur_time = time.time()
        if(cur_time> start_time+runtime_secs):
            print("T1 - Completed run time",runtime_secs)
            break
        TXBRP = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("can1_TXBRP is", TXBRP)
        
  
        PSR = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
        print("can1_PSR_IR is", PSR)
        PSR= PSR& 0x00000003
        print("can1_PSR_IR is", PSR)
        if ((PSR == 0) or (PSR == 7)):
            PSR1 = 0
            print("PASS")      
        else:
            print("FAIL")
            err=err | 1
        
        PSR = CanDeviceLibrary.ReadMmio(can1_bar, can1.PSR.offset)
        print("can1_PSR_IR is", PSR)
        PSR= PSR& 0x00000007
        print("can1_PSR_IR is", PSR)
        if (PSR != 6):
            print("PASS")
        else:
            print("FAIL")
            err=err | 1

        ECR = CanDeviceLibrary.ReadMmio(can1_bar, can1.ECR.offset)
        print("can1_ECR is", ECR)
        
        if(err == 0):
            break
        
    Thread4_completed=True
    print("thread 4 completed................... \n")
    print("\n")

def thrdfn_Vector_26680_send_can0_receive(runtime_secs=30,baud_rate=0):

    start_time = time.time()
    extra_secs= 30
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    lock = threading.Lock()
    num_bytes = 8
    start_num = 0x1A
    tx_data = []
    can_id_sent_array =[]
    min_can_id = 0x001  # Minimum possible value (1 in decimal)
    max_can_id = 0x7FF  # Maximum possible value (2047 in decimal)
    start_time = time.time()
    global Thread1_completed

    # Generate a random CAN ID within the range
    can_id = random.randint(min_can_id, max_can_id)
    for i in range(0,num_bytes):
        tx_data.append(start_num+i)
        
    txbuf = []
    m_bar = can0_bar
    sft = 0
    sfec_values = [2]
    
        #1000kbps
    nbrp = 1
    ntseg1 = 27
    ntseg2 = 12
    
    fbrp = 1
    ftseg1 = 13
    ftseg2 = 6
    
    fdoe = 0
    brse = 0
    
    if(baud_rate == 1):
        fdoe = 1
        brse = 1
        
    nbrp = nbrp-1
    ntseg1 = ntseg1-1
    ntseg2 = ntseg2-1
    
    fbrp = fbrp-1
    ftseg1 = ftseg1-1
    ftseg2 = ftseg2-1

    # Randomly choose a value for sfec
    sfec = random.choice(sfec_values)

    sfid1 = 0
    ssync = 0
    sfid2 = 0
    filt = 0
    val = 0

    lock.acquire()
    for i in range(0,32):
        CanDeviceLibrary.can_setup(m_bar = can0_bar, rxf0c_elements = 64, rxf1c = 0, rxf1c_elements = 64, rxbuff_elements = 64, tbds = 7, flssa = 0x0, lss = 128, 
        lse = 64, flesa = 0x200, eidm = 0x1FFFFFFF, f0sa = 0x400, f1sa = 0x640, rbsa = 0x2800, f0ds = 7, f1ds = 7, rbds = 7, 
        efsa = 0x3A00, efs = 32, efwm = 0, tbsa = 0x3B00, ndtb = 32, tbqs = 0, tbqm = 0, fdoe = fdoe, brse = brse, ntseg2 = ntseg2, 
        ntseg1 = ntseg1, nbrp = nbrp, nsjw = 0, fsjw = 0, ftseg2 = ftseg2, ftseg1 = ftseg1, fbrp = fbrp, tdc = 0, tdcf = 0, tdco = 0, rrfe = 0, rrfs = 0,
        anfe = 2, anfs = 2, tie = 0xFFFFFFFF, cfie = 0xFFFFFFFF, eint0 = 1, eint1 = 0, intrLine = 0)
        
        CanDeviceLibrary.retransmission_control(m_bar = can0_bar, retransmission_disable = 1)
        CanDeviceLibrary.loopback_control(m_bar = can0_bar, internal_loopback  = 0 , loopback_enable  = 0)
        CanDeviceLibrary.can_start_communication(m_bar = can0_bar)
        
        val = CanDeviceLibrary.create11bitFilter(sft = 0, sfec = sfec, sfid1 = 1, ssync = 0, sfid2 = 0x7ff)
        CanDeviceLibrary.push11BitFilter(m_bar = can0_bar, pos = i, filt = val) 
    lock.release()
        
    print("CAN0 is ready to receive")
        
        
    IR_RF0N=0
        
    while(IR_RF0N==0):
        # print("Reading Paity IR_RF1N")
        time.sleep(3)
        
        cur_time = time.time()
        if(cur_time> start_time+runtime_secs):
            print("T1 - Completed run time",runtime_secs)
            break


        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("can1_bar_IR is", reg_val_32)
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can0_bar, can0.IR.offset)
        print("can0_bar_IR is", reg_val_32)

        print("\n")

        
        
        reg_val_32 = (reg_val_32&0x00000040) >>6
        
        # print("IR_RFN is", reg_val_32)
        if(reg_val_32 == 1):
            IR_RF0N=1
            print("IR_RF0N is set to 1")
            break
        else:
            print("IR_RF0N is not equal to 1")
        
        
            # print("\n")
    Thread1_completed=True
    print("thread 1 completed................... \n")


def Test_continuous_b2b_packets_CAN0_to_CAN1_to_CAN0(baud_rate=0):

    import datetime    
    print("Date and Time:")
    now=datetime.datetime.now()
    print(now)
    sfec_values = [1]
    sfec = random.choice(sfec_values)
    global Thread1_completed
    Thread1_completed=False
    global Thread2_completed
    Thread2_completed=False
    global Thread3_completed
    Thread3_completed=False
    
    runtime_secs=120

    
    
    
    
    
    can0_bar = 0x50410000
    can1_bar = 0x50418000
    m_bar = can0_bar
    
    CanDeviceLibrary.clearRAM_control(m_bar = m_bar, clearRAM_enable = 1)
    CanDeviceLibrary.clearRAM_control(m_bar = can1_bar, clearRAM_enable = 1)
    
    
    for i in range(0,1):

        
        CanDeviceLibrary.can_end_communication(m_bar = m_bar)
        CanDeviceLibrary.can_end_communication(m_bar = can1_bar)
        thread1 = threading.Thread(target = thrdfn_Vector_26680_send_can0_receive, args = (runtime_secs,baud_rate))
        thread2 = threading.Thread(target = thrdfn_Vector_26681_send_can1_receive, args = (runtime_secs,baud_rate))
        thread3 = threading.Thread(target = thrdfn_can0_send_Vector_26680_receive, args = (runtime_secs,baud_rate))
        thread4 = threading.Thread(target = thrdfn_can1_send_Vector_26681_receive, args = (runtime_secs,baud_rate))
        
        
        thread1.start() 
        thread2.start()
        thread3.start() 
        thread4.start()
        
        thread1.join() 
        thread2.join() 
        thread3.join() 
        thread4.join()
        
        # CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 32, txbuf = txbuf, pos=0)
        
        # print("Reading MsgRAM Tx Buffer")
        # addr = (0x800 + 0x3B00)
        # CanDeviceLibrary.ReadRAM(m_bar= can1_bar,addr = addr, dw_count = 600)
        # print("\n")
        
        # print("Reading MsgRAM RxFiFo0 CAN0")
        # CanDeviceLibrary.ReadRAM(m_bar= can0_bar, addr = (0x800 + 0x400), dw_count = 600)

        print("\n")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.TXBRP.offset)
        print("TXBRP_AFTER reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        
        
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can0.TXBTO.offset)
        print("TXBTO reg_val_32 is :", reg_val_32)

        print("\n")
        print("\n")
        print("Reading IR ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(can1_bar, can1.IR.offset)
        print("IR can1_bar - reg_val_32 is", reg_val_32)    
           
        print("Reading IR ")
        reg_val_32 = CanDeviceLibrary.ReadMmio(m_bar, can0.IR.offset)
        print("IR can0_bar - reg_val_32 is", reg_val_32)
        print("\n")
        print("*******Baudrate is******** ", baud_rate)
        CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can0_bar, Rx_can_bar = can1_bar, sfec = sfec, pkt_cnt = 32, txbuf = txbuf, pos=0)
        CanDeviceLibrary.verify_rx_tranceiver_canX_to_canY(Tx_can_bar = can1_bar, Rx_can_bar = can0_bar, sfec = sfec, pkt_cnt = 32, txbuf = txbuf, pos=0)
