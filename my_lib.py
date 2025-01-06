import os
import itpii
import sys
import time
import threading 
itp = itpii.baseaccess()
#pciebar = 0xe0000000
itp.threads[0].dport(0xcf8,0x80000060)
pciebar = int(itp.threads[0].dport(0xcfc) & 0xfffffff8)
# from utils import pci
cnl_fpga_iosfbase=0
#cnl_fpga_iosfbase=0xc4cb0000
#import pci
#p2sb=pci.PCI()
accesstype = 'itp_pci'
bus=0
dev=0
func=0


import log_file_framework as var_log_fw

var_log_ALL=4
var_log_INFORMATION=3
var_log_DEBUG=2
var_log_ERROR=1
var_log_CRITICAL=0
var_log_level_SET=var_log_ALL

def log_print(var_log_level=var_log_ALL, var_log_line=''):
    if var_log_level <= var_log_level_SET:
        var_log_fw.write_to_existing_file(var_log_line)

log_print(var_log_INFORMATION,str(sys.argv[0]) + " command line arguments : " + str(sys.argv))


myliblock = threading.Lock() 

my_lib_retrycnt=20

for b in range (1,0x1f):
    for d in range (0x20):
        ### probably dont have to search all functions.. this will make it go a bit faster
        for f in range (1):
                
            did = itp.threads[0].mem(str(pciebar | b<<20 | d <<15 | f<<12)+'p',4)
                        
            if ((did == 0xc5c58086) or (did == 0x98a08086)):
                bus = b
                dev = d
                func = f

                itp.threads[0].mem(str(pciebar+4 | bus<<20 | dev<<15 | func<<12)+'p', 1, 6)
                cnl_fpga_iosfbase = int(itp.threads[0].mem(str(pciebar+0x10 | b<<20 | d<<15 | f<<12)+'p', 4)) & 0xfffffff0
                
                print 'Found P2SB at B:D:F %d/%d/%d' % (bus,dev,func)
                print 'Found MBAR at 0x%x' % cnl_fpga_iosfbase
                

print 'After P2SB discovery, bus=0x%x, device=0x%x, func=0x%x' % (bus, dev, func)
                                
def svos_mem_read(address):
    return int(os.popen(('m rd %s') % address).read(),16)	

def svos_mem_write(address, value):
    os.system(('m wd %s %x') % (address, value))
    return
    
def mem_read(address, size=4):
    #return int(os.popen(('m rd %s') % address).read(),16)
    return int(itp.threads[0].mem( hex(address) +'p', size))
    
def mem_dump(address, size=4, dump_size=64):
    return str(itp.threads[0].memdump( hex(address) +'p', dump_size, size))

def mem_write(address, value, size=4):
    #os.system(('m wd %s %x') % (address, value))
    # print 'address=0x%x, value=0x%x' % (address,value)
    itp.threads[0].mem( hex(address) +'p', size, value)
    return
    
def svos_iosf_read(port_id, offset, read_opcode=0x6):
    os.system(('m cfgwr32 0 0 0 0xd8 %x') % ( offset & 0xffffff00 ))
    os.system(('m cfgwr32 0 0 0 0xd0 %x') % ( (read_opcode<<24) | (port_id<<16) | ((offset & 0xff)<<8) | 0xf0))
    return int(os.popen('m cfgrd32 0 0 0 0xd4').read(),16)

def svos_iosf_write(port_id, offset, value, write_opcode=0x7):
    os.system(('m cfgwr32 0 0 0 0xd8 %x') % ( offset & 0xffffff00 ))
    os.system(('m cfgwr32 0 0 0 0xd4 %x') % ( value ))
    os.system(('m cfgwr32 0 0 0 0xd0 %x') % ( (write_opcode<<24) | (port_id<<16) | ((offset & 0xff)<<8) | 0xf0))
    return

def iosf_clear(port_id, fid):
    itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func << 12) | 0xd0)+'p', 4, 0x0)
    itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func << 12) | 0xd4)+'p', 4, 0x0)
    itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func << 12) | 0xd8)+'p', 4, 0x0)
    itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func << 12) | 0xdc)+'p', 4, 0x0)
    print 'Init IOSF'
    return    
    
# def iosf_read(port_id, offset, fid, read_opcode):
#     #pciebar = 0xe0000000
#     #print 'bus 0x%x' % bus 
    
#     myliblock.acquire()
#     retrycnt=20
#     val = 0xFFFFFFFF
    
#     bsy_retry=20
#     while True:
#         bsy_retry = bsy_retry -1
#         if(bsy_retry==0):
#             break
#         sts = itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd8)+'p', 2)
#         bsy=sts & 0x1
#         #log_print(var_log_INFORMATION,'sts before = 0x%x'%sts)
#         if(bsy==0):
#             break
#         else:
#             continue
    
#     while True:
#         retrycnt= retrycnt-1
#         if(retrycnt==0):
#             break
#         itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func << 12) | 0xd4)+'p', 4, 0x0)
#         itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func << 12) | 0xdc)+'p', 4, 0x0)
#         itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func<< 12) | 0xda)+'p', 2, (0xf<<12)|fid)
#         itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func<< 12) | 0xd0)+'p', 4, (port_id<<24|offset))
#         itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func<< 12) | 0xd8)+'p', 2, (read_opcode<<8|1))
#         bsy_retry=20

#         while True:
#             bsy_retry = bsy_retry -1
#             if(bsy_retry==0):
#                 break
#             sts = itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd8)+'p', 2)
#             bsy=sts & 0x1
#             #log_print(var_log_INFORMATION,'sts after = 0x%x'%sts)
#             if(bsy==0):
#                 val = itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd4)+'p', 4)
#                 #print 'bsy_retry=%d' %bsy_retry
#                 break
#             else:
#                 continue
#         if(val == 0xFFFFFFFF): 
#             continue
#         else:
#             break
#     myliblock.release()    
#     return val

def update_retrycnt(cnt=20):
    global my_lib_retrycnt
    my_lib_retrycnt=cnt
    print 'cnt=%d' % my_lib_retrycnt

def iosf_read(port_id, offset, fid, read_opcode):
    #pciebar = 0xe0000000
    #print 'pciebar 0x%x, port_id=0x%x, fid=0x%x, offset=0x%x ' % (pciebar, port_id,fid,offset)
    #print "read from address 0x%x" %(pciebar | (bus << 20) | (dev<< 15) | (func << 12))
    myliblock.acquire()
    retrycnt=my_lib_retrycnt #20
    val = 0xFFFFFFFF
    
        
    while True:
        retrycnt= retrycnt-1
        if(retrycnt==0):
            break
        itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func << 12) | 0xd4)+'p', 4, 0x0)
        itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func << 12) | 0xdc)+'p', 4, 0x0)
        itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func<< 12) | 0xda)+'p', 2, (0xf<<12)|fid)
        itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func<< 12) | 0xd0)+'p', 4, (port_id<<24|offset))
        itp.threads[0].mem(str(pciebar | (bus << 20) | (dev<< 15) | (func<< 12) | 0xd8)+'p', 2, (read_opcode<<8|1))
        val = itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd4)+'p', 4)
        #sbistat = itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd8)+'p', 2)
        #p2sbc = itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xE0)+'p', 4)
        #print ' SBISTAT= 0x%x P2SB Control=0x%x'%(sbistat, p2sbc)
        if(val == 0xFFFFFFFF):
            
            continue
        else:
            break

    myliblock.release()    
    return val

def iosf_write(port_id, offset, fid, write_opcode, value, posted=0):
    #print 'bus 0x%x' % bus
    # bsy_retry=20
    # while True:
    #     bsy_retry = bsy_retry -1
    #     if(bsy_retry==0):
    #         break
    #     sts = itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd8)+'p', 2)
    #     bsy=sts & 0x1
    #     if(bsy==0):
    #         break
    #     else:
    #         continue
    myliblock.acquire()
    itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd0)+'p', 4, (port_id<<24|offset))
    itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xda)+'p', 2, (0xf<<12)|fid)
    itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd4)+'p', 4, value)
    itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd8)+'p', 2, (write_opcode<<8|posted<<7|1))
    myliblock.release()
    #time.sleep(0.1)
    # bsy_retry=20
    # while True:
    #     bsy_retry = bsy_retry -1
    #     if(bsy_retry==0):
    #         break
    #     sts = itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd8)+'p', 2)
    #     bsy=sts & 0x1
    #     if(bsy==0):
    #         break
    #     else:
    #         continue
    #print 'fid = 0x%x' % ((0xf<<12)|fid)
    #print 'output = 0x%x' % (write_opcode<<8|posted<<7|1)
    return 
    
def fpga_iosf_read(offset,portid):
    if(cnl_fpga_iosfbase == 0):
        print "ERROR: Did not find P2SB in FPGA\n"
        return 1
    return itp.threads[0].mem(str(cnl_fpga_iosfbase+(portid<<16)+offset) + 'p', 4)
    
def fpga_iosf_write(offset,portid,value):
    if(cnl_fpga_iosfbase == 0):
        print "ERROR: Did not find P2SB in FPGA\n"
        return 1
    itp.threads[0].mem(str(cnl_fpga_iosfbase+(portid<<16)+offset) + 'p', 4, value)
    return



def iosf_read_sbistat_reg():
    return itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xd8)+'p', 4)

def iosf_read_ures_reg():
    return itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xf0)+'p', 4)

def iosf_read_urec_reg():
    return itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xf4)+'p', 4)

def iosf_write_urec_reg(value):
    itp.threads[0].mem(str(pciebar | (bus << 20) | (dev << 15) | (func << 12) | 0xf4)+'p', 2, value)