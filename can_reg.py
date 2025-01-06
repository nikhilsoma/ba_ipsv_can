###Author: ruo.shan.ng@intel.com  --- VICE LPSS SV
## PLEASE DO NOT EDIT ANY of the function. If u want to do so, please inform me. Thank you.
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#Readme First
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++                            
#Before using the script+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#1. Change the lpss_port_id according to product
#2. Set the tool,system_mode,access_mode and sb_accesstype correctly.
#           tool: itp - using itp to run your test
#                 svos - run your script in svos environment 
#   system_mode : pci - pci mode
#                 acpi - acpi mode, will use BAR1 to access config space
#   access_mode : primary - pci config space & mmio register rd/wr using primary access
#                 iosfsb - pci config space & mmio register rd/wr using primary sideband access
#                 tap2iosf - pci config space & mmio register & private register rd/wr using tap2iosf access
#  sb_accesstype: iosfsb - 
#                 tap2iosf - sideband register rd/wr using tap2iosf access
#                 fpga_iosf - fpga sideband register rd/wr using base
#   
###############################################################################################################
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#Example of using the script 
# import lpss_bxt_regs
# i2c0=lpss_bxt_regs.regs(0, 22, 0)  //(bus, dev, func)
# i2c0.readall() //dump all the pci and mmio registers
# i2c0.checkdefault() //check the default value of the registers
#***specify the bus dev func for your contollers accordingly
################################################################################################################
################################################################################################################
import sys
import log_file_framework as var_log_fw

var_log_ALL=4
var_log_INFORMATION=3
var_log_DEBUG=2
var_log_ERROR=1
var_log_CRITICAL=0

#Default Assignment

var_log_level_SET=var_log_ALL
#Faster Execution, Restricted Log Level
#var_log_level_SET=var_log_DEBUG



def log_print(var_log_level=var_log_ALL, var_log_line=''):
    if var_log_level <= var_log_level_SET:
        var_log_fw.write_to_existing_file(var_log_line)

log_print(var_log_INFORMATION,str(sys.argv[0]) + " command line arguments : " + str(sys.argv))

tool = 'itp' ## 'itp' or 'svos'
system_mode = 'pci'  ## 'acpi' or 'pci'
access_mode = 'primary'  ## 'primary' or 'iosfsb' or 'tap2iosf'
sb_accesstype= 'fpga_iosf'  ##iosfsb or tap2iosf or fpga_iosf


if tool=='itp':
    import itpii
    itp = itpii.baseaccess()
    #import pci
    #p2sb=pci.PCI()
    #import my_lib
    #reload (my_lib)
    #elif tool=='svos':
    #import my_lib

if ((system_mode == 'pci') and (access_mode=='primary') and (sb_accesstype=='iosfsb')):
    pci_accesstype = 'pci'
    reg_accesstype = 'mmio'
    sb_accesstype = 'iosfsb'
    print ('system_mode = %s, access_mode = %s, sb_accesstype= %s' % (system_mode, access_mode, sb_accesstype))
elif ((system_mode == 'pci') and (access_mode=='primary') and (sb_accesstype=='fpga_iosf')):
    pci_accesstype = 'pci'
    reg_accesstype = 'mmio'
    sb_accesstype = 'fpga_iosf'
    print ('system_mode = %s, access_mode = %s, sb_accesstype= %s' % (system_mode, access_mode, sb_accesstype))
elif ((system_mode == 'acpi') and (access_mode=='primary')):
    pci_accesstype = 'mbar1'
    reg_accesstype = 'mmio'
    sb_accesstype = 'iosfsb'
    print ('system_mode = %s, access_mode = %s' % (system_mode, access_mode))
elif ((system_mode == 'pci') and (access_mode=='iosfsb')and (sb_accesstype=='iosfsb')):
    pci_accesstype = 'iosfsb'
    reg_accesstype = 'iosfsb'
    sb_accesstype = 'iosfsb'
    print ('system_mode = %s, access_mode = %s, sb_accesstype= %s' % (system_mode, access_mode,sb_accesstype))
elif (access_mode == 'tap2iosf'):
    pci_accesstype = 'tap2iosf'
    reg_accesstype = 'tap2iosf'
    sb_accesstype = 'tap2iosf' 
    from components.socket.soc import bxt_access as access
    print ('access_mode = %s' % ( access_mode))
else:
    print ('system_mode = %s, access_mode = %s' % (system_mode, access_mode))
    print ('ERROR: We dont support this mode. Please make sure system_mode and access_mode are set correctly!!!')
    
import ctypes

#pciebar = 0xe0000000
#pciebar = 0xf8000000
itp.threads[0].dport(0xcf8,0x80000060)
pciebar = int(itp.threads[0].dport(0xcfc) & 0xfffffff8)


port_id = 0xF203
mbar1 = int()
bus = int()
dev = int()



class register():
    name = ''
    offset = 0
    size = 0
    default = 0
    write1val = 0
    write0val = 0
    description = ''

    numfields = 0
    fieldlist = []

    def __init__(self, name, offset, size, default, write1val,description, fields=[]):
        self.name = name
        self.offset = offset
        self.size = size
        self.default = default
        self.write1val = write1val
        self.description = description
        self.numfields = len(fields)
        self.fieldlist = []

        #create the register subfields based on the fields list
        #this instantiates reg_field classes dynamically based on the field names
        if len(fields) > 0:
            for i in range (self.numfields):
                #if user did not provide Field Description
                if len(fields[i]) == 4:
                    exec('self.%s = reg_field(\"%s\", %d, %d, %d, %s)' % (fields[i][0], fields[i][0], fields[i][1], fields[i][2], fields[i][3], 'self'))
                #if they did
                else:
                    exec('self.%s = reg_field(\"%s\", %d, %d, %d, %s, %s)' % (fields[i][0], fields[i][0], fields[i][1], fields[i][2], fields[i][3], 'self', fields[i][4]))
                #add the new field to the fieldlist, so we can access it via array (dont need to know the variable name)
                exec('self.fieldlist.append(self.%s)' % (fields[i][0]))

    def printdesc(self, regtype):
        itpii.printf("%-24s: %-8s    Offset: 0x%02x     Size: %x     %s\n", self.name, regtype, self.offset, self.size, self.description)

    def printfields(self):
        itpii.printf("%-24s.%-20s %s     %s         %s\n", "Reg Name", "Field Name", "Reg Offset", "Bits", "Description")
        itpii.printf("-------------------------------------------------------------------------\n")
        if self.numfields == 0:
            itpii.printf("%s: This register has no fields\n", self.name)
        else:
            for i in range(self.numfields):
                self.fieldlist[i].printdesc()
        itpii.printf("\n")

    def parse(self, value):
        for i in range(self.numfields):
            self.fieldlist[i].parse(value)

    def readandparse(self):
        self.parse(self.read())

class pci_register(register):
    
    def __init__(self, name, dev, func, offset, size, default, write1val, description,fields=[]):
        register.__init__(self, name, offset, size, default, write1val, description, fields)
        self.func = func
        self.dev = dev
        
    def printdesc(self):
        register.printdesc(self, 'PCI Cfg')
        return

    def read (self):
        if pci_accesstype == 'pci':
            return self.read_pci()
        elif pci_accesstype == 'mbar1':
            return self.read_mbar1()
        elif pci_accesstype == 'iosfsb':
            return self.read_pci_iosfsb()
        elif pci_accesstype == 'tap2iosf':
            return self.read_pci_tap2iosf()

    def write (self, value):
        if pci_accesstype == 'pci':
            self.write_pci(value)
        elif pci_accesstype == 'mbar1':
            self.write_mbar1(value)
        elif pci_accesstype == 'iosfsb':
            self.write_pci_iosfsb(value)
        elif pci_accesstype == 'tap2iosf':
            self.write_pci_tap2iosf(value)
        return
        
    def read_pci (self):
        if tool == 'itp':
            return itp.threads[0].mem(str(pciebar | (bus << 20) | (self.dev << 15) | (self.func << 12) | self.offset)+'p', self.size)
        elif tool == 'svos':
            return my_lib.svos_mem_read(hex((pciebar | (bus << 20) | (self.dev << 15) | (self.func << 12) | self.offset)))
    def read_pci_iosfsb (self):
        return my_lib.iosf_read(lpss_port_id, self.offset, fid=(self.func|self.dev<<3), read_opcode=0x4)
    def read_mbar1 (self):
        global mbar1
        mbar1 = iosf_read((lpss_port_id, 0x18, (self.dev<<3 | self.func), 0x6))
        return itp.threads[0].mem(str(mbar1+self.offset)+'p', self.size)
    def read_pci_tap2iosf (self):
        rdVal=access.tap2iosfsb(portid=port_id, offset=self.offset, data=None, size=4, opcode=0x4, wbe=15, bar=0, pci_device=self.dev, pci_function=self.func, fid=((self.dev<<3)|(self.func)), posted=0)
        return rdVal

    def write_pci (self, value):
        if tool == 'itp':
            itp.threads[0].mem(str(pciebar | (bus << 20) | (self.dev << 15) | (self.func << 12) | self.offset)+'p', self.size, value)
        elif tool == 'svos':
            my_lib.svos_mem_write(hex(pciebar | (bus << 20) | (self.dev << 15) | (self.func << 12) | self.offset), value)
        return
    def write_pci_iosfsb (self, value):
        my_lib.iosf_write(lpss_port_id, self.offset, fid=(self.func|self.dev<<3), write_opcode=0x5, value=None)
        return
    def write_mbar1 (self, value):
        itp.threads[0].mem(str(mbar1+self.offset)+'p', self.size, value)
        return
    def write_pci_tap2iosf (self, value):
        access.tap2iosfsb(portid=port_id, offset=self.offset, data=value, size=4, opcode=0x5, wbe=15, bar=0, pci_device=self.dev, pci_function=self.func, fid=((self.dev<<3)|(self.func)), posted=0)
        return

    def checkdefault(self):
        readval = self.read()
        if readval != self.default:
            print ("PCI    0x%03x:    %-16s     0x%08x     0x%08x    MISMATCH" % (self.offset,self.name, self.default,readval))
        else:
            print ("PCI    0x%03x:    %-16s     0x%08x     0x%08x" % (self.offset,self.name, self.default,readval))
        return

    def checkwrite1(self):
        oldval = self.read()
        self.write(0xffffffff)
        newval = self.read()
        self.write(oldval)
        print ("PCI    0x%03x:    %-16s     0x%08x     0x%08x" % (self.offset,self.name, self.write1val,newval))
        if newval != self.write1val:
            print("  MISMATCH!!\n")
        else:
            print("\n")

class   mmio_register(register):
    def __init__(self, name, bar, offset, size, default, write1val, description='', fields=[]):
        global my_func
        global my_dev
        register.__init__(self, name, offset, size, default, write1val, description, fields)
        self.bar = int(bar)
        self.func = my_func
        self.dev = my_dev
        
    def printdesc(self):
        register.printdesc(self, 'MMIO')    

    def read (self):
        if (reg_accesstype=='mmio'):
            if tool == 'itp':
                #print "addr = 0x%x" %(self.bar+self.offset)
                return itp.threads[0].mem(str(self.bar+self.offset)+'p', self.size)
            elif tool == 'svos':
                return my_lib.svos_mem_read(hex(self.offset+self.bar))
        elif (reg_accesstype=='iosfsb'):
            return self.read_mmio_iosfsb()
        elif (reg_accesstype=='tap2iosf'):
            return self.read_tap2iosf()

    def write (self, value):
        if(reg_accesstype=='mmio'):
            if tool == 'itp':
                if self.size == 8:
                    itp.threads[0].mem(str(self.bar+self.offset)+'p', 4, value & 0xffffffff)
                    itp.threads[0].mem(str(self.bar+self.offset+4)+'p', 4, value >> 32)
                    return
                else:
                    #print "addr = 0x%x value=0x%x" %(self.bar+self.offset,value)
                    itp.threads[0].mem(str(self.bar+self.offset)+'p', self.size, value)
            elif tool == 'svos':
                my_lib.svos_mem_write(hex(self.bar+self.offset), value)
            return
        elif(reg_accesstype=='iosfsb'):
            self.write_mmio_iosfsb(value)
            return
        elif(reg_accesstype=='tap2iosf'):
            self.write_mmio_tap2iosf(value)
            return
            
    def read_mmio_iosfsb (self):
        return my_lib.iosf_read(lpss_port_id, self.offset, fid=((self.dev<<3)|(self.func)), read_opcode=0x0)
        
    def read_tap2iosf (self):
        # print 'my_dev=%x, my_func=%x' % (self.dev, self.func)
        rdVal=access.tap2iosfsb(portid=port_id, offset=self.offset, data=None, size=4, opcode=0, wbe=15, bar=0, pci_device=self.dev, pci_function=self.func, fid=((self.dev<<3)|(self.func)), posted=0)
        return rdVal

    def write_mmio_iosfsb (self, value):
        if self.size == 8:
            my_lib.iosf_write(lpss_port_id, (self.offset), fid=(self.func|self.dev<<3), write_opcode=0x1, value=(value & 0xffffffff))
            my_lib.iosf_write(lpss_port_id, (self.offset+4), fid=(self.func|self.dev<<3), write_opcode=0x1, value=(value>>32))
            return
        my_lib.iosf_write(lpss_port_id, (self.offset), fid=(self.func|self.dev<<3), write_opcode=0x1, value=(value & 0xffffffff))        
        return
    def write_mmio_tap2iosf (self, value):
        my_fid=((self.dev<<3)|(self.func))
        # print 'my+dev=%x    my_func=%x    my_fid=%x'% (self.dev,self.func,my_fid)
        
        # if self.size == 8:
            # tap2iosf.tap2iosf(tapId=tap_id, opCode=0x1, portId=port_id, regOffset=self.offset,  byteEnable=0xf, pciDeviceNumber=dev, pciFunctionNumber=self.func, dataValue = (value & 0xffffffff))
            # tap2iosf.tap2iosf(tapId=tap_id, opCode=0x1, portId=port_id, regOffset=(self.offset+4),  byteEnable=0xf, pciDeviceNumber=dev, pciFunctionNumber=self.func, dataValue = (value>>32))
            # return
        # tap2iosf.tap2iosf(tapId=tap_id, opCode=0x1, portId=port_id, regOffset=self.offset,  byteEnable=0xf, pciDeviceNumber=dev, pciFunctionNumber=self.func, dataValue = value)
        access.tap2iosfsb(portid=port_id, offset=self.offset, data=value, size=4, opcode=0x1, wbe=15, bar=0, pci_device=self.dev, pci_function=self.func, fid=my_fid, posted=0)

        return

    def checkdefault(self):
        readval = self.read()
        
        if readval != self.default:
            log_print(var_log_ERROR, "ERROR | MMIO    0x%03x:    %-16s     0x%08x     0x%08x    MISMATCH" % (self.offset,self.name, self.default,readval))
            return 1
        else:
            log_print(var_log_INFORMATION, "MMIO    0x%03x:    %-16s     0x%08x     0x%08x" % (self.offset,self.name, self.default,readval))
            return 0


    def checkwrite1(self):
        oldval = self.read()
        self.write(0xffffffff)
        newval = self.read()
        self.write(oldval)
        print ("MMIO    0x%03x:    %-16s     0x%08x     0x%08x", self.offset,self.name, self.write1val,newval)
        if newval != self.write1val:
            print("  MISMATCH!!\n")
        else:
            print("\n") 


class  mem_register(register):
    def __init__(self, name, bar, offset, size, default, write1val, description='', fields=[]):
        register.__init__(self, name, offset, size, default, write1val, description, fields)

        
    def printdesc(self):
        register.printdesc(self, 'Mem')    

    def read (self):
        return itp.threads[0].mem((str(self.offset) + 'p'), 4)


    def write (self, value):
        itp.threads[0].mem((str(self.offset) + 'p'), 4, value)
        


    
class reg_field:
    def __init__(self, name, minbit, maxbit, mask, regptr, description=''):
        self.name = name
        self.minbit = minbit
        self.maxbit = maxbit
        self.mask = mask
        self.regptr = regptr
        self.description = description

    def read(self):
        return ((self.regptr.read() & self.mask) >> self.minbit)
    def write(self, value):
        if self.regptr.size == 8:
            self.regptr.write((self.regptr.read()) & ctypes.c_uint64(~self.mask).value  | ((value << self.minbit) & self.mask))
            return
        self.regptr.write((self.regptr.read()) & ctypes.c_uint32(~self.mask).value  | ((value << self.minbit) & self.mask))
        return
    def printdesc(self):
        itpii.printf("%-24s.%-20s Offset 0x%x     Bits %d:%d     %s\n", self.regptr.name, self.name, self.regptr.offset, self.maxbit, self.minbit, self.description)
        return
    def parse(self, value):
        itpii.printf("%-24s0x%x     %s\n", self.regptr.name+'.'+self.name, ((value & self.mask) >> self.minbit), self.description)
        return


            
class regs:
    
    def __init__(self, bus_num=3, dev_num=0x1D, func_num=0):
        global bus
        global my_func
        global my_dev
        bus = bus_num
        self.func = my_func=func = func_num
        self.dev = my_dev=dev = dev_num #=0x1D #earlier 0x1F
        uhfi_dev = 0x0A
        

        #bus = 0x03
        #func = 0
        
        self.UHFI_BAR1LOW =          pci_register("BAR1LOW",                     uhfi_dev,   0,   0x18,   4,      0,              0xfffff000, "Base Address Register 1 (PCI Cfg Space)") 
       
        self.uhfi_bar = self.UHFI_BAR1LOW.read() & 0xfffffff0
        print ("UHFI bar = 0x%x" %(self.uhfi_bar))
        
        
        
        self.ID =               pci_register("ID",                          dev,   func,   0x00,   4,      0,              0,          "Identifiers",                                          [["VID", 0,15,0xffff, "\"Vendor ID\""], ["DID", 16,31, 0xffff0000, "\"Device ID\""]])
        self.CMDSTS =           pci_register("CMDSTS",                      dev,   func,   0x04,   4,      0x100000,       0x100506,   "PCI Command and Status",                               [["MSE", 1, 1, 0x2, "\"Memory Space Enable\""], ["BME", 2, 2, 0x4, "\"Bus Master Enable\""], ["SERR", 8, 8, 0x100, "\"SERR# Enable\""], ["INTDIS", 10, 10, 0x400, "\"Interrupt Disable\""], ["INTSTS", 19, 19, 0x80000,"\"Interrupt Status\""], ["CAPLIST", 20,20,0x100000, "\"Capabilities List\""],["SIGTABRT", 27,27, 8000000,"\"Signaled Target Abort\""],["RXTABRT", 28,28, 0x10000000,"\"Received Target Abort\""],["RXMABRT", 29, 29, 0x2000000,"\"Received Master Abort\""],["SIGSYSERR",30,30,0x40000000,"\"Signaled System Error\""]])
        self.RIDCC =            pci_register("RIDCC",                       dev,   func,   0x08,   4,      0x11800000,     0,          "Revision ID and Class Codes",                          [["RID", 0, 7, 0xff,"\"Revision ID\""], ["CC", 8, 31, 0xffffff00, "\"Class Code\""]])
        self.BIST =             pci_register("BIST",                        dev,   func,   0x0C,   4,      0x800000,       0x8000ff,   "CacheLine Size, Latency Timer, Header Type, BIST",     [["CLSZ", 0, 7, 0xff,"\"Cache Line Size\""], ["LT", 8, 15, 0xff00,"\"Latency Timer\""], ["HDRTYPE", 16, 22, 0xef0000,"\"Header Type\""], ["MFDEV", 23, 23, 0x800000,"\"Multi Function Device\""], ["BIST", 24, 31, 0xff000000,"\"Built In Self-Test\""]])
        self.BARLOW =           pci_register("BARLOW",                      dev,   func,   0x10,   4,      0,              0xfffff000, "Base Address Register 0 (MMIO Regs)") 
        self.BARHIGH =          pci_register("BARHIGH",                     dev,   func,   0x14,   4,      0,              0xfffff000, "Base Address Register 1 (PCI Cfg Space)") 
        self.BAR1LOW =          pci_register("BAR1LOW",                     dev,   func,   0x18,   4,      0,              0xfffff000, "Base Address Register 1 (PCI Cfg Space)") 
        self.BAR1HIGH =         pci_register("BAR1HIGH",                    dev,   func,   0x1c,   4,      0,              0xfffff000, "Base Address Register 1 (PCI Cfg Space)")             
        self.SSID =             pci_register("SSID",                        dev,   func,   0x2c,   4,      0,              0xffffffff, "Subsystem Identifiers",                                [["SSVID", 0, 15, 0xffff, "\"Subsystem Vendor ID\""], ["SSID", 16, 31, 0xffff0000,"\"Subsystem ID\""]]) 
        self.ROMBAR =           pci_register("ROMBAR",                      dev,   func,   0x30,   4,      0,              0,          "Expansion ROM Base Address") 
        self.CAP =              pci_register("CAP",                         dev,   func,   0x34,   4,      0x80,           0,         "Capabilities Pointer") 
        self.INTR =             pci_register("INTR",                        dev,   func,   0x3C,   4,      0x100,          0x1ff,      "Interrupt Line and Pin, Min Gnt, Max Latency",         [["INTRLINE", 0, 7, 0xff,"\"Interrupt Line\""], ["INTRPIN", 8, 11, 0xf00,"\"Interrupt Pin\""], ["MINGNT", 16, 23, 0xff0000,"\"Min Gnt\""],["MAXLAT",24,31,0xff000000,"\"Max Lat\""]]) 
        self.PMCAP =            pci_register("PMCAP",                       dev,   func,   0x80,   4,      0x39001,        0,    "PM Capabilities",                                            [["PMCAPID", 0, 7, 0xff,"\"Power Management Capability\""], ["PMVER", 16, 18, 0x70000,"\"Power Management Capabilities Version\""], ["PME",27,31,0xF8000000,"\"PME Support\""]]) 
        self.PMCTRL =           pci_register("PMCTRL",                      dev,   func,   0x84,   4,      0x8,            0x10b,      "PM Control and Status",                                [["PMSTATE", 0, 1, 0x3,"\"Power State\""],["NOSFTRST", 3, 3, 0x8,"\"No Soft Reset\""], ["PMEEN", 8,8,0x100,"\"PME Enable\""],["PMESTS",15,15,0x8000,"\"PME Status\""]]) 
        self.PCIDEVIDLECAPR =   pci_register("PCIDevIDleCapRecord",         dev,   func,   0x90,   4,      0xF0140009,     0xF0140009, "PCI Device Idle Capability Record") 
        self.DEVIDVSR =         pci_register("DevIDVenSpecificReg",         dev,   func,   0x94,   4,      0x1400010,      0, "Device ID Vendor Specific Register")
        self.SWLTRPTR =         pci_register("SWLTRPTR",                    dev,   func,   0x98,   4,      0x00002101,     0, "SWLTRPTR")
        self.DEVIDLEPTR =       pci_register("EVIdlePointerReg",            dev,   func,   0x9C,   4,      0x000024c1,     0, "Device IDLE Pointer Register")  
        self.D0I3MAXDEVPG =     pci_register("D0I3MAXDEVPG",                dev,   func,   0xA0,   4,      0x800,          0x000F1FFF, "D0I3MAXDEVPG")
        self.MANID =            pci_register("MANID",                       dev,   func,   0xF8,   4,      0,              0,          "Manufacturer ID") 
   
        self.bar = self.BARLOW.read() & 0xfffffff0
        
        
        ### Register list for indexed accesses
        self.pci_reglist = [self.ID, self.CMDSTS, self.RIDCC, self.BIST, self.BARLOW, self.BARHIGH, self.BAR1LOW, self.BAR1HIGH, self.SSID, self.ROMBAR, self.CAP, self.INTR, self.PMCAP, self.PMCTRL, self.PCIDEVIDLECAPR, self.DEVIDVSR, self.SWLTRPTR, self.DEVIDLEPTR, self.D0I3MAXDEVPG, self.MANID]
        #open up MEM SPACE AND BUS Master
        if(self.CMDSTS.BME.read() == 0):
            self.CMDSTS.BME.write(1)
            
        if(self.CMDSTS.MSE.read() == 0):
            self.CMDSTS.MSE.write(1)
         
        #figuring out if its hidden port. if it is, increament BAR by 0x400
        '''
        if(self.hidden_port):
            print "Hidden port detected. Increment BAR by 0x400\n"
            self.tempbar = (self.BARLOW.read() & 0xfffffff0) + 0x400
            
        else:    
            self.tempbar = self.BARLOW.read() & 0xfffffff0
        '''
        #print "Done for PCI definition\n"
        print ("CAN bar = 0x%x" %(self.bar))
        
        #CAN registers
        self.MSG_RAM_SIZE = mmio_register("MSG_RAM_SIZE", self.bar, 0x500, 4, 0x0, 0x0, "dunno", [["SIZE_B", 0, 31, 0xffffffff, ""], ])
        self.CTL = mmio_register("CTL", self.bar, 0x504, 4, 0x0, 0x0, "dunno", [["CAN_DIS_MORD", 0, 0, 0x1, ""], ["RSVD0", 1, 31, 0xfffffffe, ""], ])
        self.INT_CTL = mmio_register("INT_CTL", self.bar, 0x508, 4, 0x0, 0x0, "dunno", [["PRIMARY_INT_EN", 0, 0, 0x1, ""], ["PUNIT_INT_EN", 1, 1, 0x2, ""], ["RSVD0", 2, 31, 0xfffffffc, ""], ])
        self.INT_STAT = mmio_register("INT_STAT", self.bar, 0x50c, 4, 0x0, 0x0, "dunno", [["THIS_CAN_CONT_INT", 0, 0, 0x1, ""], ["THIS_CAN_PERR_INT", 1, 1, 0x2, ""], ["OTHER_CAN_CONT_INT", 2, 2, 0x4, ""], ["OTHER_CAN_PERR_INT", 3, 3, 0x8, ""], ["RSVD0", 4, 31, 0xfffffff0, ""], ])
        self.MSGRAM_ADDR_CONFLICT_STAT = mmio_register("MSGRAM_ADDR_CONFLICT_STAT", self.bar, 0x510, 4, 0x0, 0x0, "dunno", [["CAN_ADDR_CONFLICT_OFFSET", 0, 14, 0x7fff, ""], ["RSVD0", 15, 15, 0x8000, ""], ["ADDR_CONFLICT_OCCURED", 16, 16, 0x10000, ""], ["RSVD1", 17, 31, 0xfffe0000, ""], ])
        self.TIMESTAMP_CTL = mmio_register("TIMESTAMP_CTL", self.bar, 0x514, 4, 0x0, 0x0, "dunno", [["LXTSC", 0, 0, 0x1, ""], ["RXTSC", 1, 1, 0x2, ""], ["LXTSV", 2, 2, 0x4, ""], ["RXTSV", 3, 3, 0x8, ""], ["RSVD0", 4, 31, 0xfffffff0, ""], ])
        self.LOCALTIMESTAMP_HIGH = mmio_register("LOCALTIMESTAMP_HIGH", self.bar, 0x518, 4, 0x0, 0x0, "dunno", [["LTH", 0, 31, 0xffffffff, ""], ])
        self.LOCALTIMESTAMP_LOW = mmio_register("LOCALTIMESTAMP_LOW", self.bar, 0x51c, 4, 0x0, 0x0, "dunno", [["LTL", 0, 31, 0xffffffff, ""], ])
        self.MSG_RAM_SIZE = mmio_register("MSG_RAM_SIZE", self.bar, 0x500, 4, 0x0, 0x0, "dunno", [["SIZE_B", 0, 31, 0xffffffff, ""], ])
        self.CTL = mmio_register("CTL", self.bar, 0x504, 4, 0x0, 0x0, "dunno", [["CAN_DIS_MORD", 0, 0, 0x1, ""], ["RSVD0", 1, 31, 0xfffffffe, ""], ])
        self.INT_CTL = mmio_register("INT_CTL", self.bar, 0x508, 4, 0x0, 0x0, "dunno", [["PRIMARY_INT_EN", 0, 0, 0x1, ""], ["PUNIT_INT_EN", 1, 1, 0x2, ""], ["RSVD0", 2, 31, 0xfffffffc, ""], ])
        self.INT_STAT = mmio_register("INT_STAT", self.bar, 0x50c, 4, 0x0, 0x0, "dunno", [["THIS_CAN_CONT_INT", 0, 0, 0x1, ""], ["THIS_CAN_PERR_INT", 1, 1, 0x2, ""], ["OTHER_CAN_CONT_INT", 2, 2, 0x4, ""], ["OTHER_CAN_PERR_INT", 3, 3, 0x8, ""], ["RSVD0", 4, 31, 0xfffffff0, ""], ])
        self.MSGRAM_ADDR_CONFLICT_STAT = mmio_register("MSGRAM_ADDR_CONFLICT_STAT", self.bar, 0x510, 4, 0x0, 0x0, "dunno", [["CAN_ADDR_CONFLICT_OFFSET", 0, 14, 0x7fff, ""], ["RSVD0", 15, 15, 0x8000, ""], ["ADDR_CONFLICT_OCCURED", 16, 16, 0x10000, ""], ["RSVD1", 17, 31, 0xfffe0000, ""], ])
        self.TIMESTAMP_CTL = mmio_register("TIMESTAMP_CTL", self.bar, 0x514, 4, 0x0, 0x0, "dunno", [["LXTSC", 0, 0, 0x1, ""], ["RXTSC", 1, 1, 0x2, ""], ["LXTSV", 2, 2, 0x4, ""], ["RXTSV", 3, 3, 0x8, ""], ["RSVD0", 4, 31, 0xfffffff0, ""], ])
        self.LOCALTIMESTAMP_HIGH = mmio_register("LOCALTIMESTAMP_HIGH", self.bar, 0x518, 4, 0x0, 0x0, "dunno", [["LTH", 0, 31, 0xffffffff, ""], ])
        self.LOCALTIMESTAMP_LOW = mmio_register("LOCALTIMESTAMP_LOW", self.bar, 0x51c, 4, 0x0, 0x0, "dunno", [["LTL", 0, 31, 0xffffffff, ""], ])
        self.PAR_CTL_STAT = mmio_register("PAR_CTL_STAT", self.bar, 0x600, 4, 0x0, 0x0, "dunno", [["PARITY_EN", 0, 0, 0x1, ""], ["PARITY_INIT_IN_PROG", 1, 1, 0x2, ""], ["PERR_OCCURED", 2, 2, 0x4, ""], ["RSVD0", 3, 31, 0xfffffff8, ""], ])
        self.PAR_ERR_OFFSET = mmio_register("PAR_ERR_OFFSET", self.bar, 0x604, 4, 0x0, 0x0, "dunno", [["PAR_ERR_OFFSET", 0, 14, 0x7fff, ""], ["RSVD0", 15, 15, 0x8000, ""], ["PAR_ERR_LOW", 16, 16, 0x10000, ""], ["PAR_ERR_UPP", 17, 17, 0x20000, ""], ["RSVD1", 18, 31, 0xfffc0000, ""], ])
        self.PAR_EINJ_CTL_STAT = mmio_register("PAR_EINJ_CTL_STAT", self.bar, 0x608, 4, 0x0, 0x0, "dunno", [["EINJ_EN", 0, 0, 0x1, ""], ["EINJ_MODE", 1, 1, 0x2, ""], ["EINJ_ONE_TIME_ERR_OCCURED", 2, 2, 0x4, ""], ["RSVD0", 3, 31, 0xfffffff8, ""], ])
        self.PAR_EINJ_OFFSET = mmio_register("PAR_EINJ_OFFSET", self.bar, 0x60c, 4, 0x0, 0x0, "dunno", [["EINJ_OFFSET", 0, 14, 0x7fff, ""], ["RSVD0", 15, 31, 0xffff8000, ""], ])
        self.PAR_EINJ_DATA_MASK = mmio_register("PAR_EINJ_DATA_MASK", self.bar, 0x610, 4, 0x0, 0x0, "dunno", [["EINJ_DATA_MASK", 0, 31, 0xffffffff, ""], ])
        self.PAR_EINJ_PARITY_MASK = mmio_register("PAR_EINJ_PARITY_MASK", self.bar, 0x614, 4, 0x0, 0x0, "dunno", [["EINJ_PARITY_MASK", 0, 1, 0x3, ""], ["RSVD0", 2, 31, 0xfffffffc, ""], ])
        self.PAR_CTL_STAT = mmio_register("PAR_CTL_STAT", self.bar, 0x600, 4, 0x0, 0x0, "dunno", [["PARITY_EN", 0, 0, 0x1, ""], ["PARITY_INIT_IN_PROG", 1, 1, 0x2, ""], ["PERR_OCCURED", 2, 2, 0x4, ""], ["RSVD0", 3, 31, 0xfffffff8, ""], ])
        self.PAR_ERR_OFFSET = mmio_register("PAR_ERR_OFFSET", self.bar, 0x604, 4, 0x0, 0x0, "dunno", [["PAR_ERR_OFFSET", 0, 14, 0x7fff, ""], ["RSVD0", 15, 15, 0x8000, ""], ["PAR_ERR_LOW", 16, 16, 0x10000, ""], ["PAR_ERR_UPP", 17, 17, 0x20000, ""], ["RSVD1", 18, 31, 0xfffc0000, ""], ])
        self.PAR_EINJ_CTL_STAT = mmio_register("PAR_EINJ_CTL_STAT", self.bar, 0x608, 4, 0x0, 0x0, "dunno", [["EINJ_EN", 0, 0, 0x1, ""], ["EINJ_MODE", 1, 1, 0x2, ""], ["EINJ_ONE_TIME_ERR_OCCURED", 2, 2, 0x4, ""], ["RSVD0", 3, 31, 0xfffffff8, ""], ])
        self.PAR_EINJ_OFFSET = mmio_register("PAR_EINJ_OFFSET", self.bar, 0x60c, 4, 0x0, 0x0, "dunno", [["EINJ_OFFSET", 0, 14, 0x7fff, ""], ["RSVD0", 15, 31, 0xffff8000, ""], ])
        self.PAR_EINJ_DATA_MASK = mmio_register("PAR_EINJ_DATA_MASK", self.bar, 0x610, 4, 0x0, 0x0, "dunno", [["EINJ_DATA_MASK", 0, 31, 0xffffffff, ""], ])
        self.PAR_EINJ_PARITY_MASK = mmio_register("PAR_EINJ_PARITY_MASK", self.bar, 0x614, 4, 0x0, 0x0, "dunno", [["EINJ_PARITY_MASK", 0, 1, 0x3, ""], ["RSVD0", 2, 31, 0xfffffffc, ""], ])
        self.CREL = mmio_register("CREL", self.bar, 0x0, 4, 0x0, 0x0, "dunno", [["DAY", 0, 7, 0xff, ""], ["MON", 8, 15, 0xff00, ""], ["YEAR", 16, 19, 0xf0000, ""], ["SUBSTEP", 20, 23, 0xf00000, ""], ["STEP", 24, 27, 0xf000000, ""], ["REL", 28, 31, 0xf0000000, ""], ])
        self.ENDN = mmio_register("ENDN", self.bar, 0x4, 4, 0x0, 0x0, "dunno", [["ETV", 0, 31, 0xffffffff, ""], ])
        self.CUST = mmio_register("CUST", self.bar, 0x8, 4, 0x0, 0x0, "dunno", [["CUST_FIELD", 0, 31, 0xffffffff, ""], ])
        self.DBTP = mmio_register("DBTP", self.bar, 0xc, 4, 0x0, 0x0, "dunno", [["FSJW", 0, 3, 0xf, ""], ["FTSEG2", 4, 7, 0xf0, ""], ["FTSEG1", 8, 12, 0x1f00, ""], ["RSVD2", 13, 15, 0xe000, ""], ["FBRP", 16, 20, 0x1f0000, ""], ["RSVD3", 21, 22, 0x600000, ""], ["TDC", 23, 23, 0x800000, ""], ["RSVD4", 24, 31, 0xff000000, ""], ])
        self.TEST = mmio_register("TEST", self.bar, 0x10, 4, 0x0, 0x0, "dunno", [["TAM", 0, 0, 0x1, ""], ["TAT", 1, 1, 0x2, ""], ["CAM", 2, 2, 0x4, ""], ["CAT", 3, 3, 0x8, ""], ["LBCK", 4, 4, 0x10, ""], ["TX", 5, 6, 0x60, ""], ["RX", 7, 7, 0x80, ""], ["RSVD0", 8, 31, 0xffffff00, ""], ])
        self.RWD = mmio_register("RWD", self.bar, 0x14, 4, 0x0, 0x0, "dunno", [["WDC", 0, 7, 0xff, ""], ["WDV", 8, 15, 0xff00, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.CCCR = mmio_register("CCCR", self.bar, 0x18, 4, 0x0, 0x0, "dunno", [["INIT", 0, 0, 0x1, ""], ["CCE", 1, 1, 0x2, ""], ["ASM", 2, 2, 0x4, ""], ["CSA", 3, 3, 0x8, ""], ["CSR", 4, 4, 0x10, ""], ["MON", 5, 5, 0x20, ""], ["DAR", 6, 6, 0x40, ""], ["TEST", 7, 7, 0x80, ""], ["FDOE", 8, 8, 0x100, ""], ["BRSE", 9, 9, 0x200, ""], ["RSVD1", 10, 11, 0xc00, ""], ["PXHD", 12, 12, 0x1000, ""], ["EFBI", 13, 13, 0x2000, ""], ["TXP", 14, 14, 0x4000, ""], ["NISO", 15, 15, 0x8000, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.NBTP = mmio_register("NBTP", self.bar, 0x1c, 4, 0x0, 0x0, "dunno", [["NTSEG2", 0, 6, 0x7f, ""], ["RSVD0", 7, 7, 0x80, ""], ["NTSEG1", 8, 14, 0x7f00, ""], ["NBRP", 16, 24, 0x1ff0000, ""], ["NSJW", 25, 31, 0xfe000000, ""], ])
        self.TSCC = mmio_register("TSCC", self.bar, 0x20, 4, 0x0, 0x0, "dunno", [["TSS", 0, 1, 0x3, ""], ["RSVD0", 2, 15, 0xfffc, ""], ["TCP", 16, 19, 0xf0000, ""], ["RSVD1", 20, 31, 0xfff00000, ""], ])
        self.TSCV = mmio_register("TSCV", self.bar, 0x24, 4, 0x0, 0x0, "dunno", [["TSC", 0, 15, 0xffff, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.TOCC = mmio_register("TOCC", self.bar, 0x28, 4, 0x0, 0x0, "dunno", [["ETOC", 0, 0, 0x1, ""], ["TOS", 1, 2, 0x6, ""], ["RSVD0", 3, 15, 0xfff8, ""], ["TOP", 16, 31, 0xffff0000, ""], ])
        self.TOCV = mmio_register("TOCV", self.bar, 0x2c, 4, 0x0, 0x0, "dunno", [["TOC", 0, 15, 0xffff, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.ECR = mmio_register("ECR", self.bar, 0x40, 4, 0x0, 0x0, "dunno", [["TEC", 0, 7, 0xff, ""], ["REC", 8, 14, 0x7f00, ""], ["RP", 15, 15, 0x8000, ""], ["CEL", 16, 23, 0xff0000, ""], ["RSVD0", 24, 31, 0xff000000, ""], ])
        self.PSR = mmio_register("PSR", self.bar, 0x44, 4, 0x0, 0x0, "dunno", [["LEC", 0, 2, 0x7, ""], ["ACT", 3, 4, 0x18, ""], ["EP", 5, 5, 0x20, ""], ["EW", 6, 6, 0x40, ""], ["B0", 7, 7, 0x80, ""], ["FLEC", 8, 10, 0x700, ""], ["RESI", 11, 11, 0x800, ""], ["RBRS", 12, 12, 0x1000, ""], ["RFDF", 13, 13, 0x2000, ""], ["PXE", 14, 14, 0x4000, ""], ["RSVD1", 15, 15, 0x8000, ""], ["TDCV", 16, 22, 0x7f0000, ""], ["RSVD0", 23, 31, 0xff800000, ""], ])
        self.TDCR = mmio_register("TDCR", self.bar, 0x48, 4, 0x0, 0x0, "dunno", [["TDCF", 0, 6, 0x7f, ""], ["RSVD1", 7, 7, 0x80, ""], ["TDCO", 8, 14, 0x7f00, ""], ["RSVD0", 15, 31, 0xffff8000, ""], ])
        self.IR = mmio_register("IR", self.bar, 0x50, 4, 0x0, 0x0, "dunno", [["RF0N", 0, 0, 0x1, ""], ["RF0W", 1, 1, 0x2, ""], ["RF0F", 2, 2, 0x4, ""], ["RF0L", 3, 3, 0x8, ""], ["RF1N", 4, 4, 0x10, ""], ["RF1W", 5, 5, 0x20, ""], ["RF1F", 6, 6, 0x40, ""], ["RF1L", 7, 7, 0x80, ""], ["HPM", 8, 8, 0x100, ""], ["TC", 9, 9, 0x200, ""], ["TCF", 10, 10, 0x400, ""], ["TFE", 11, 11, 0x800, ""], ["TEFN", 12, 12, 0x1000, ""], ["TEFW", 13, 13, 0x2000, ""], ["TEFF", 14, 14, 0x4000, ""], ["TEFL", 15, 15, 0x8000, ""], ["TSW", 16, 16, 0x10000, ""], ["MRAF", 17, 17, 0x20000, ""], ["TOO", 18, 18, 0x40000, ""], ["DRX", 19, 19, 0x80000, ""], ["BEC", 20, 20, 0x100000, ""], ["BEU", 21, 21, 0x200000, ""], ["ELO", 22, 22, 0x400000, ""], ["EP", 23, 23, 0x800000, ""], ["EW", 24, 24, 0x1000000, ""], ["BO", 25, 25, 0x2000000, ""], ["WDI", 26, 26, 0x4000000, ""], ["PEA", 27, 27, 0x8000000, ""], ["PED", 28, 28, 0x10000000, ""], ["ARA", 29, 29, 0x20000000, ""], ["RSVD0", 30, 31, 0xc0000000, ""], ])
        self.IE = mmio_register("IE", self.bar, 0x54, 4, 0x0, 0x0, "dunno", [["RF0NE", 0, 0, 0x1, ""], ["RF0WE", 1, 1, 0x2, ""], ["RF0FE", 2, 2, 0x4, ""], ["RF0LE", 3, 3, 0x8, ""], ["RF1NE", 4, 4, 0x10, ""], ["RF1WE", 5, 5, 0x20, ""], ["RF1FE", 6, 6, 0x40, ""], ["RF1LE", 7, 7, 0x80, ""], ["HPME", 8, 8, 0x100, ""], ["TCE", 9, 9, 0x200, ""], ["TCFE", 10, 10, 0x400, ""], ["TFEE", 11, 11, 0x800, ""], ["TEFNE", 12, 12, 0x1000, ""], ["TEFWE", 13, 13, 0x2000, ""], ["TEFFE", 14, 14, 0x4000, ""], ["TEFLE", 15, 15, 0x8000, ""], ["TSWE", 16, 16, 0x10000, ""], ["MRAFE", 17, 17, 0x20000, ""], ["TOOE", 18, 18, 0x40000, ""], ["DRXE", 19, 19, 0x80000, ""], ["BECE", 20, 20, 0x100000, ""], ["BEUE", 21, 21, 0x200000, ""], ["ELOE", 22, 22, 0x400000, ""], ["EPE", 23, 23, 0x800000, ""], ["EWE", 24, 24, 0x1000000, ""], ["BOE", 25, 25, 0x2000000, ""], ["WDIE", 26, 26, 0x4000000, ""], ["PEAE", 27, 27, 0x8000000, ""], ["PEDE", 28, 28, 0x10000000, ""], ["ARAE", 29, 29, 0x20000000, ""], ["RSVD0", 30, 31, 0xc0000000, ""], ])
        self.ILS = mmio_register("ILS", self.bar, 0x58, 4, 0x0, 0x0, "dunno", [["RF0NL", 0, 0, 0x1, ""], ["RF0WL", 1, 1, 0x2, ""], ["RF0FL", 2, 2, 0x4, ""], ["RF0LL", 3, 3, 0x8, ""], ["RF1NL", 4, 4, 0x10, ""], ["RF1WL", 5, 5, 0x20, ""], ["RF1FL", 6, 6, 0x40, ""], ["RF1LL", 7, 7, 0x80, ""], ["HPML", 8, 8, 0x100, ""], ["TCL", 9, 9, 0x200, ""], ["TCFL", 10, 10, 0x400, ""], ["TFEL", 11, 11, 0x800, ""], ["TEFNL", 12, 12, 0x1000, ""], ["TEFWL", 13, 13, 0x2000, ""], ["TEFFL", 14, 14, 0x4000, ""], ["TEFLL", 15, 15, 0x8000, ""], ["TSWL", 16, 16, 0x10000, ""], ["MRAFL", 17, 17, 0x20000, ""], ["TOOL", 18, 18, 0x40000, ""], ["DRXL", 19, 19, 0x80000, ""], ["BECL", 20, 20, 0x100000, ""], ["BEUL", 21, 21, 0x200000, ""], ["ELOL", 22, 22, 0x400000, ""], ["EPL", 23, 23, 0x800000, ""], ["EWL", 24, 24, 0x1000000, ""], ["BOL", 25, 25, 0x2000000, ""], ["WDIL", 26, 26, 0x4000000, ""], ["PEAL", 27, 27, 0x8000000, ""], ["PEDL", 28, 28, 0x10000000, ""], ["ARAL", 29, 29, 0x20000000, ""], ["RSVD0", 30, 31, 0xc0000000, ""], ])
        self.ILE = mmio_register("ILE", self.bar, 0x5c, 4, 0x0, 0x0, "dunno", [["EINT0", 0, 0, 0x1, ""], ["EINT1", 1, 1, 0x2, ""], ["RSVD0", 2, 31, 0xfffffffc, ""], ])
        self.GFC = mmio_register("GFC", self.bar, 0x80, 4, 0x0, 0x0, "dunno", [["RRFE", 0, 0, 0x1, ""], ["RRFS", 1, 1, 0x2, ""], ["ANFE", 2, 3, 0xc, ""], ["ANFS", 4, 5, 0x30, ""], ["RSVD0", 6, 31, 0xffffffc0, ""], ])
        self.SIDFC = mmio_register("SIDFC", self.bar, 0x84, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["FLSSA", 2, 15, 0xfffc, ""], ["LSS", 16, 23, 0xff0000, ""], ["RSVD0", 24, 31, 0xff000000, ""], ])
        self.XIDFC = mmio_register("XIDFC", self.bar, 0x88, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["FLESA", 2, 15, 0xfffc, ""], ["LSE", 16, 22, 0x7f0000, ""], ["RSVD0", 23, 31, 0xff800000, ""], ])
        self.XIDAM = mmio_register("XIDAM", self.bar, 0x90, 4, 0x0, 0x0, "dunno", [["EIDM", 0, 28, 0x1fffffff, ""], ["RSVD0", 29, 31, 0xe0000000, ""], ])
        self.HPMS = mmio_register("HPMS", self.bar, 0x94, 4, 0x0, 0x0, "dunno", [["BIDX", 0, 5, 0x3f, ""], ["MSI", 6, 7, 0xc0, ""], ["FIDX", 8, 14, 0x7f00, ""], ["FLST", 15, 15, 0x8000, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.NDAT1 = mmio_register("NDAT1", self.bar, 0x98, 4, 0x0, 0x0, "dunno", [["ND", 0, 31, 0xffffffff, ""], ])
        self.NDAT2 = mmio_register("NDAT2", self.bar, 0x9c, 4, 0x0, 0x0, "dunno", [["ND", 0, 31, 0xffffffff, ""], ])
        self.RXF0C = mmio_register("RXF0C", self.bar, 0xa0, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["F0SA", 2, 15, 0xfffc, ""], ["F0S", 16, 22, 0x7f0000, ""], ["RSVD0", 23, 23, 0x800000, ""], ["F0WM", 24, 30, 0x7f000000, ""], ["F0OM", 31, 31, 0x80000000, ""], ])
        self.RXF0S = mmio_register("RXF0S", self.bar, 0xa4, 4, 0x0, 0x0, "dunno", [["F0FL", 0, 6, 0x7f, ""], ["RSVD3", 7, 7, 0x80, ""], ["F0GI", 8, 13, 0x3f00, ""], ["RSVD2", 14, 15, 0xc000, ""], ["F0PI", 16, 21, 0x3f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["F0F", 24, 24, 0x1000000, ""], ["RF0L", 25, 25, 0x2000000, ""], ["RSVD0", 26, 31, 0xfc000000, ""], ])
        self.RXF0A = mmio_register("RXF0A", self.bar, 0xa8, 4, 0x0, 0x0, "dunno", [["F0AI", 0, 5, 0x3f, ""], ["RSVD0", 6, 31, 0xffffffc0, ""], ])
        self.RXBC = mmio_register("RXBC", self.bar, 0xac, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["RBSA", 2, 15, 0xfffc, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.RXF1C = mmio_register("RXF1C", self.bar, 0xb0, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["F1SA", 2, 15, 0xfffc, ""], ["F1S", 16, 22, 0x7f0000, ""], ["RSVD0", 23, 23, 0x800000, ""], ["F1WM", 24, 30, 0x7f000000, ""], ["F1OM", 31, 31, 0x80000000, ""], ])
        self.RXF1S = mmio_register("RXF1S", self.bar, 0xb4, 4, 0x0, 0x0, "dunno", [["F1FL", 0, 6, 0x7f, ""], ["RSVD3", 7, 7, 0x80, ""], ["F1GI", 8, 13, 0x3f00, ""], ["RSVD2", 14, 15, 0xc000, ""], ["F1PI", 16, 21, 0x3f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["F1F", 24, 24, 0x1000000, ""], ["RF1L", 25, 25, 0x2000000, ""], ["RSVD0", 26, 31, 0xfc000000, ""], ])
        self.RXF1A = mmio_register("RXF1A", self.bar, 0xb8, 4, 0x0, 0x0, "dunno", [["F1AI", 0, 5, 0x3f, ""], ["RSVD0", 6, 31, 0xffffffc0, ""], ])
        self.RXESC = mmio_register("RXESC", self.bar, 0xbc, 4, 0x0, 0x0, "dunno", [["F0DS", 0, 2, 0x7, ""], ["F1DS", 4, 6, 0x70, ""], ["RSVD1", 7, 7, 0x80, ""], ["RBDS", 8, 10, 0x700, ""], ["RSVD0", 11, 31, 0xfffff800, ""], ])
        self.TXBC = mmio_register("TXBC", self.bar, 0xc0, 4, 0x0, 0x0, "dunno", [["RSVD2", 0, 1, 0x3, ""], ["TBSA", 2, 15, 0xfffc, ""], ["NDTB", 16, 21, 0x3f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["TFQS", 24, 29, 0x3f000000, ""], ["TFQM", 30, 30, 0x40000000, ""], ["RSVD0", 31, 31, 0x80000000, ""], ])
        self.TXFQS = mmio_register("TXFQS", self.bar, 0xc4, 4, 0x0, 0x0, "dunno", [["TFFL", 0, 5, 0x3f, ""], ["RSVD2", 6, 7, 0xc0, ""], ["TFGI", 8, 12, 0x1f00, ""], ["RSVD1", 13, 15, 0xe000, ""], ["TFQPI", 16, 20, 0x1f0000, ""], ["TFQF", 21, 21, 0x200000, ""], ["RSVD0", 22, 31, 0xffc00000, ""], ])
        self.TXESC = mmio_register("TXESC", self.bar, 0xc8, 4, 0x0, 0x0, "dunno", [["TBDS", 0, 2, 0x7, ""], ["RSVD0", 3, 31, 0xfffffff8, ""], ])
        self.TXBRP = mmio_register("TXBRP", self.bar, 0xcc, 4, 0x0, 0x0, "dunno", [["TRP", 0, 31, 0xffffffff, ""], ])
        self.TXBAR = mmio_register("TXBAR", self.bar, 0xd0, 4, 0x0, 0x0, "dunno", [["AR", 0, 31, 0xffffffff, ""], ])
        self.TXBCR = mmio_register("TXBCR", self.bar, 0xd4, 4, 0x0, 0x0, "dunno", [["CR", 0, 31, 0xffffffff, ""], ])
        self.TXBTO = mmio_register("TXBTO", self.bar, 0xd8, 4, 0x0, 0x0, "dunno", [["TO", 0, 31, 0xffffffff, ""], ])
        self.TXBCF = mmio_register("TXBCF", self.bar, 0xdc, 4, 0x0, 0x0, "dunno", [["CF", 0, 31, 0xffffffff, ""], ])
        self.TXBTIE = mmio_register("TXBTIE", self.bar, 0xe0, 4, 0x0, 0x0, "dunno", [["TIE", 0, 31, 0xffffffff, ""], ])
        self.TXBCIE = mmio_register("TXBCIE", self.bar, 0xe4, 4, 0x0, 0x0, "dunno", [["CFIE", 0, 31, 0xffffffff, ""], ])
        self.TXEFC = mmio_register("TXEFC", self.bar, 0xf0, 4, 0x0, 0x0, "dunno", [["RSVD2", 0, 1, 0x3, ""], ["EFSA", 2, 15, 0xfffc, ""], ["EFS", 16, 21, 0x3f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["EFWM", 24, 29, 0x3f000000, ""], ["RSVD0", 30, 31, 0xc0000000, ""], ])
        self.TXEFS = mmio_register("TXEFS", self.bar, 0xf4, 4, 0x0, 0x0, "dunno", [["EFFL", 0, 5, 0x3f, ""], ["RSVD3", 6, 7, 0xc0, ""], ["EFGI", 8, 12, 0x1f00, ""], ["RSVD2", 13, 15, 0xe000, ""], ["EFPI", 16, 20, 0x1f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["EFF", 24, 24, 0x1000000, ""], ["TEFL", 25, 25, 0x2000000, ""], ["RSVD0", 26, 31, 0xfc000000, ""], ])
        self.TXEFA = mmio_register("TXEFA", self.bar, 0xf8, 4, 0x0, 0x0, "dunno", [["EFAI", 0, 4, 0x1f, ""], ["RSVD0", 5, 31, 0xffffffe0, ""], ])
        self.CREL = mmio_register("CREL", self.bar, 0x0, 4, 0x0, 0x0, "dunno", [["DAY", 0, 7, 0xff, ""], ["MON", 8, 15, 0xff00, ""], ["YEAR", 16, 19, 0xf0000, ""], ["SUBSTEP", 20, 23, 0xf00000, ""], ["STEP", 24, 27, 0xf000000, ""], ["REL", 28, 31, 0xf0000000, ""], ])
        self.ENDN = mmio_register("ENDN", self.bar, 0x4, 4, 0x0, 0x0, "dunno", [["ETV", 0, 31, 0xffffffff, ""], ])
        self.CUST = mmio_register("CUST", self.bar, 0x8, 4, 0x0, 0x0, "dunno", [["CUST_FIELD", 0, 31, 0xffffffff, ""], ])
        self.DBTP = mmio_register("DBTP", self.bar, 0xc, 4, 0x0, 0x0, "dunno", [["FSJW", 0, 3, 0xf, ""], ["FTSEG2", 4, 7, 0xf0, ""], ["FTSEG1", 8, 12, 0x1f00, ""], ["RSVD2", 13, 15, 0xe000, ""], ["FBRP", 16, 20, 0x1f0000, ""], ["RSVD3", 21, 22, 0x600000, ""], ["TDC", 23, 23, 0x800000, ""], ["RSVD4", 24, 31, 0xff000000, ""], ])
        self.TEST = mmio_register("TEST", self.bar, 0x10, 4, 0x0, 0x0, "dunno", [["TAM", 0, 0, 0x1, ""], ["TAT", 1, 1, 0x2, ""], ["CAM", 2, 2, 0x4, ""], ["CAT", 3, 3, 0x8, ""], ["LBCK", 4, 4, 0x10, ""], ["TX", 5, 6, 0x60, ""], ["RX", 7, 7, 0x80, ""], ["RSVD0", 8, 31, 0xffffff00, ""], ])
        self.RWD = mmio_register("RWD", self.bar, 0x14, 4, 0x0, 0x0, "dunno", [["WDC", 0, 7, 0xff, ""], ["WDV", 8, 15, 0xff00, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.CCCR = mmio_register("CCCR", self.bar, 0x18, 4, 0x0, 0x0, "dunno", [["INIT", 0, 0, 0x1, ""], ["CCE", 1, 1, 0x2, ""], ["ASM", 2, 2, 0x4, ""], ["CSA", 3, 3, 0x8, ""], ["CSR", 4, 4, 0x10, ""], ["MON", 5, 5, 0x20, ""], ["DAR", 6, 6, 0x40, ""], ["TEST", 7, 7, 0x80, ""], ["FDOE", 8, 8, 0x100, ""], ["BRSE", 9, 9, 0x200, ""], ["RSVD1", 10, 11, 0xc00, ""], ["PXHD", 12, 12, 0x1000, ""], ["EFBI", 13, 13, 0x2000, ""], ["TXP", 14, 14, 0x4000, ""], ["NISO", 15, 15, 0x8000, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.NBTP = mmio_register("NBTP", self.bar, 0x1c, 4, 0x0, 0x0, "dunno", [["NTSEG2", 0, 6, 0x7f, ""], ["RSVD0", 7, 7, 0x80, ""], ["NTSEG1", 8, 14, 0x7f00, ""], ["NBRP", 16, 24, 0x1ff0000, ""], ["NSJW", 25, 31, 0xfe000000, ""], ])
        self.TSCC = mmio_register("TSCC", self.bar, 0x20, 4, 0x0, 0x0, "dunno", [["TSS", 0, 1, 0x3, ""], ["RSVD0", 2, 15, 0xfffc, ""], ["TCP", 16, 19, 0xf0000, ""], ["RSVD1", 20, 31, 0xfff00000, ""], ])
        self.TSCV = mmio_register("TSCV", self.bar, 0x24, 4, 0x0, 0x0, "dunno", [["TSC", 0, 15, 0xffff, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.TOCC = mmio_register("TOCC", self.bar, 0x28, 4, 0x0, 0x0, "dunno", [["ETOC", 0, 0, 0x1, ""], ["TOS", 1, 2, 0x6, ""], ["RSVD0", 3, 15, 0xfff8, ""], ["TOP", 16, 31, 0xffff0000, ""], ])
        self.TOCV = mmio_register("TOCV", self.bar, 0x2c, 4, 0x0, 0x0, "dunno", [["TOC", 0, 15, 0xffff, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.ECR = mmio_register("ECR", self.bar, 0x40, 4, 0x0, 0x0, "dunno", [["TEC", 0, 7, 0xff, ""], ["REC", 8, 14, 0x7f00, ""], ["RP", 15, 15, 0x8000, ""], ["CEL", 16, 23, 0xff0000, ""], ["RSVD0", 24, 31, 0xff000000, ""], ])
        self.PSR = mmio_register("PSR", self.bar, 0x44, 4, 0x0, 0x0, "dunno", [["LEC", 0, 2, 0x7, ""], ["ACT", 3, 4, 0x18, ""], ["EP", 5, 5, 0x20, ""], ["EW", 6, 6, 0x40, ""], ["B0", 7, 7, 0x80, ""], ["FLEC", 8, 10, 0x700, ""], ["RESI", 11, 11, 0x800, ""], ["RBRS", 12, 12, 0x1000, ""], ["RFDF", 13, 13, 0x2000, ""], ["PXE", 14, 14, 0x4000, ""], ["RSVD1", 15, 15, 0x8000, ""], ["TDCV", 16, 22, 0x7f0000, ""], ["RSVD0", 23, 31, 0xff800000, ""], ])
        self.TDCR = mmio_register("TDCR", self.bar, 0x48, 4, 0x0, 0x0, "dunno", [["TDCF", 0, 6, 0x7f, ""], ["RSVD1", 7, 7, 0x80, ""], ["TDCO", 8, 14, 0x7f00, ""], ["RSVD0", 15, 31, 0xffff8000, ""], ])
        self.IR = mmio_register("IR", self.bar, 0x50, 4, 0x0, 0x0, "dunno", [["RF0N", 0, 0, 0x1, ""], ["RF0W", 1, 1, 0x2, ""], ["RF0F", 2, 2, 0x4, ""], ["RF0L", 3, 3, 0x8, ""], ["RF1N", 4, 4, 0x10, ""], ["RF1W", 5, 5, 0x20, ""], ["RF1F", 6, 6, 0x40, ""], ["RF1L", 7, 7, 0x80, ""], ["HPM", 8, 8, 0x100, ""], ["TC", 9, 9, 0x200, ""], ["TCF", 10, 10, 0x400, ""], ["TFE", 11, 11, 0x800, ""], ["TEFN", 12, 12, 0x1000, ""], ["TEFW", 13, 13, 0x2000, ""], ["TEFF", 14, 14, 0x4000, ""], ["TEFL", 15, 15, 0x8000, ""], ["TSW", 16, 16, 0x10000, ""], ["MRAF", 17, 17, 0x20000, ""], ["TOO", 18, 18, 0x40000, ""], ["DRX", 19, 19, 0x80000, ""], ["BEC", 20, 20, 0x100000, ""], ["BEU", 21, 21, 0x200000, ""], ["ELO", 22, 22, 0x400000, ""], ["EP", 23, 23, 0x800000, ""], ["EW", 24, 24, 0x1000000, ""], ["BO", 25, 25, 0x2000000, ""], ["WDI", 26, 26, 0x4000000, ""], ["PEA", 27, 27, 0x8000000, ""], ["PED", 28, 28, 0x10000000, ""], ["ARA", 29, 29, 0x20000000, ""], ["RSVD0", 30, 31, 0xc0000000, ""], ])
        self.IE = mmio_register("IE", self.bar, 0x54, 4, 0x0, 0x0, "dunno", [["RF0NE", 0, 0, 0x1, ""], ["RF0WE", 1, 1, 0x2, ""], ["RF0FE", 2, 2, 0x4, ""], ["RF0LE", 3, 3, 0x8, ""], ["RF1NE", 4, 4, 0x10, ""], ["RF1WE", 5, 5, 0x20, ""], ["RF1FE", 6, 6, 0x40, ""], ["RF1LE", 7, 7, 0x80, ""], ["HPME", 8, 8, 0x100, ""], ["TCE", 9, 9, 0x200, ""], ["TCFE", 10, 10, 0x400, ""], ["TFEE", 11, 11, 0x800, ""], ["TEFNE", 12, 12, 0x1000, ""], ["TEFWE", 13, 13, 0x2000, ""], ["TEFFE", 14, 14, 0x4000, ""], ["TEFLE", 15, 15, 0x8000, ""], ["TSWE", 16, 16, 0x10000, ""], ["MRAFE", 17, 17, 0x20000, ""], ["TOOE", 18, 18, 0x40000, ""], ["DRXE", 19, 19, 0x80000, ""], ["BECE", 20, 20, 0x100000, ""], ["BEUE", 21, 21, 0x200000, ""], ["ELOE", 22, 22, 0x400000, ""], ["EPE", 23, 23, 0x800000, ""], ["EWE", 24, 24, 0x1000000, ""], ["BOE", 25, 25, 0x2000000, ""], ["WDIE", 26, 26, 0x4000000, ""], ["PEAE", 27, 27, 0x8000000, ""], ["PEDE", 28, 28, 0x10000000, ""], ["ARAE", 29, 29, 0x20000000, ""], ["RSVD0", 30, 31, 0xc0000000, ""], ])
        self.ILS = mmio_register("ILS", self.bar, 0x58, 4, 0x0, 0x0, "dunno", [["RF0NL", 0, 0, 0x1, ""], ["RF0WL", 1, 1, 0x2, ""], ["RF0FL", 2, 2, 0x4, ""], ["RF0LL", 3, 3, 0x8, ""], ["RF1NL", 4, 4, 0x10, ""], ["RF1WL", 5, 5, 0x20, ""], ["RF1FL", 6, 6, 0x40, ""], ["RF1LL", 7, 7, 0x80, ""], ["HPML", 8, 8, 0x100, ""], ["TCL", 9, 9, 0x200, ""], ["TCFL", 10, 10, 0x400, ""], ["TFEL", 11, 11, 0x800, ""], ["TEFNL", 12, 12, 0x1000, ""], ["TEFWL", 13, 13, 0x2000, ""], ["TEFFL", 14, 14, 0x4000, ""], ["TEFLL", 15, 15, 0x8000, ""], ["TSWL", 16, 16, 0x10000, ""], ["MRAFL", 17, 17, 0x20000, ""], ["TOOL", 18, 18, 0x40000, ""], ["DRXL", 19, 19, 0x80000, ""], ["BECL", 20, 20, 0x100000, ""], ["BEUL", 21, 21, 0x200000, ""], ["ELOL", 22, 22, 0x400000, ""], ["EPL", 23, 23, 0x800000, ""], ["EWL", 24, 24, 0x1000000, ""], ["BOL", 25, 25, 0x2000000, ""], ["WDIL", 26, 26, 0x4000000, ""], ["PEAL", 27, 27, 0x8000000, ""], ["PEDL", 28, 28, 0x10000000, ""], ["ARAL", 29, 29, 0x20000000, ""], ["RSVD0", 30, 31, 0xc0000000, ""], ])
        self.ILE = mmio_register("ILE", self.bar, 0x5c, 4, 0x0, 0x0, "dunno", [["EINT0", 0, 0, 0x1, ""], ["EINT1", 1, 1, 0x2, ""], ["RSVD0", 2, 31, 0xfffffffc, ""], ])
        self.GFC = mmio_register("GFC", self.bar, 0x80, 4, 0x0, 0x0, "dunno", [["RRFE", 0, 0, 0x1, ""], ["RRFS", 1, 1, 0x2, ""], ["ANFE", 2, 3, 0xc, ""], ["ANFS", 4, 5, 0x30, ""], ["RSVD0", 6, 31, 0xffffffc0, ""], ])
        self.SIDFC = mmio_register("SIDFC", self.bar, 0x84, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["FLSSA", 2, 15, 0xfffc, ""], ["LSS", 16, 23, 0xff0000, ""], ["RSVD0", 24, 31, 0xff000000, ""], ])
        self.XIDFC = mmio_register("XIDFC", self.bar, 0x88, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["FLESA", 2, 15, 0xfffc, ""], ["LSE", 16, 22, 0x7f0000, ""], ["RSVD0", 23, 31, 0xff800000, ""], ])
        self.XIDAM = mmio_register("XIDAM", self.bar, 0x90, 4, 0x0, 0x0, "dunno", [["EIDM", 0, 28, 0x1fffffff, ""], ["RSVD0", 29, 31, 0xe0000000, ""], ])
        self.HPMS = mmio_register("HPMS", self.bar, 0x94, 4, 0x0, 0x0, "dunno", [["BIDX", 0, 5, 0x3f, ""], ["MSI", 6, 7, 0xc0, ""], ["FIDX", 8, 14, 0x7f00, ""], ["FLST", 15, 15, 0x8000, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.NDAT1 = mmio_register("NDAT1", self.bar, 0x98, 4, 0x0, 0x0, "dunno", [["ND", 0, 31, 0xffffffff, ""], ])
        self.NDAT2 = mmio_register("NDAT2", self.bar, 0x9c, 4, 0x0, 0x0, "dunno", [["ND", 0, 31, 0xffffffff, ""], ])
        self.RXF0C = mmio_register("RXF0C", self.bar, 0xa0, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["F0SA", 2, 15, 0xfffc, ""], ["F0S", 16, 22, 0x7f0000, ""], ["RSVD0", 23, 23, 0x800000, ""], ["F0WM", 24, 30, 0x7f000000, ""], ["F0OM", 31, 31, 0x80000000, ""], ])
        self.RXF0S = mmio_register("RXF0S", self.bar, 0xa4, 4, 0x0, 0x0, "dunno", [["F0FL", 0, 6, 0x7f, ""], ["RSVD3", 7, 7, 0x80, ""], ["F0GI", 8, 13, 0x3f00, ""], ["RSVD2", 14, 15, 0xc000, ""], ["F0PI", 16, 21, 0x3f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["F0F", 24, 24, 0x1000000, ""], ["RF0L", 25, 25, 0x2000000, ""], ["RSVD0", 26, 31, 0xfc000000, ""], ])
        self.RXF0A = mmio_register("RXF0A", self.bar, 0xa8, 4, 0x0, 0x0, "dunno", [["F0AI", 0, 5, 0x3f, ""], ["RSVD0", 6, 31, 0xffffffc0, ""], ])
        self.RXBC = mmio_register("RXBC", self.bar, 0xac, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["RBSA", 2, 15, 0xfffc, ""], ["RSVD0", 16, 31, 0xffff0000, ""], ])
        self.RXF1C = mmio_register("RXF1C", self.bar, 0xb0, 4, 0x0, 0x0, "dunno", [["RSVD1", 0, 1, 0x3, ""], ["F1SA", 2, 15, 0xfffc, ""], ["F1S", 16, 22, 0x7f0000, ""], ["RSVD0", 23, 23, 0x800000, ""], ["F1WM", 24, 30, 0x7f000000, ""], ["F1OM", 31, 31, 0x80000000, ""], ])
        self.RXF1S = mmio_register("RXF1S", self.bar, 0xb4, 4, 0x0, 0x0, "dunno", [["F1FL", 0, 6, 0x7f, ""], ["RSVD3", 7, 7, 0x80, ""], ["F1GI", 8, 13, 0x3f00, ""], ["RSVD2", 14, 15, 0xc000, ""], ["F1PI", 16, 21, 0x3f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["F1F", 24, 24, 0x1000000, ""], ["RF1L", 25, 25, 0x2000000, ""], ["RSVD0", 26, 31, 0xfc000000, ""], ])
        self.RXF1A = mmio_register("RXF1A", self.bar, 0xb8, 4, 0x0, 0x0, "dunno", [["F1AI", 0, 5, 0x3f, ""], ["RSVD0", 6, 31, 0xffffffc0, ""], ])
        self.RXESC = mmio_register("RXESC", self.bar, 0xbc, 4, 0x0, 0x0, "dunno", [["F0DS", 0, 2, 0x7, ""], ["F1DS", 4, 6, 0x70, ""], ["RSVD1", 7, 7, 0x80, ""], ["RBDS", 8, 10, 0x700, ""], ["RSVD0", 11, 31, 0xfffff800, ""], ])
        self.TXBC = mmio_register("TXBC", self.bar, 0xc0, 4, 0x0, 0x0, "dunno", [["RSVD2", 0, 1, 0x3, ""], ["TBSA", 2, 15, 0xfffc, ""], ["NDTB", 16, 21, 0x3f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["TFQS", 24, 29, 0x3f000000, ""], ["TFQM", 30, 30, 0x40000000, ""], ["RSVD0", 31, 31, 0x80000000, ""], ])
        self.TXFQS = mmio_register("TXFQS", self.bar, 0xc4, 4, 0x0, 0x0, "dunno", [["TFFL", 0, 5, 0x3f, ""], ["RSVD2", 6, 7, 0xc0, ""], ["TFGI", 8, 12, 0x1f00, ""], ["RSVD1", 13, 15, 0xe000, ""], ["TFQPI", 16, 20, 0x1f0000, ""], ["TFQF", 21, 21, 0x200000, ""], ["RSVD0", 22, 31, 0xffc00000, ""], ])
        self.TXESC = mmio_register("TXESC", self.bar, 0xc8, 4, 0x0, 0x0, "dunno", [["TBDS", 0, 2, 0x7, ""], ["RSVD0", 3, 31, 0xfffffff8, ""], ])
        self.TXBRP = mmio_register("TXBRP", self.bar, 0xcc, 4, 0x0, 0x0, "dunno", [["TRP", 0, 31, 0xffffffff, ""], ])
        self.TXBAR = mmio_register("TXBAR", self.bar, 0xd0, 4, 0x0, 0x0, "dunno", [["AR", 0, 31, 0xffffffff, ""], ])
        self.TXBCR = mmio_register("TXBCR", self.bar, 0xd4, 4, 0x0, 0x0, "dunno", [["CR", 0, 31, 0xffffffff, ""], ])
        self.TXBTO = mmio_register("TXBTO", self.bar, 0xd8, 4, 0x0, 0x0, "dunno", [["TO", 0, 31, 0xffffffff, ""], ])
        self.TXBCF = mmio_register("TXBCF", self.bar, 0xdc, 4, 0x0, 0x0, "dunno", [["CF", 0, 31, 0xffffffff, ""], ])
        self.TXBTIE = mmio_register("TXBTIE", self.bar, 0xe0, 4, 0x0, 0x0, "dunno", [["TIE", 0, 31, 0xffffffff, ""], ])
        self.TXBCIE = mmio_register("TXBCIE", self.bar, 0xe4, 4, 0x0, 0x0, "dunno", [["CFIE", 0, 31, 0xffffffff, ""], ])
        self.TXEFC = mmio_register("TXEFC", self.bar, 0xf0, 4, 0x0, 0x0, "dunno", [["RSVD2", 0, 1, 0x3, ""], ["EFSA", 2, 15, 0xfffc, ""], ["EFS", 16, 21, 0x3f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["EFWM", 24, 29, 0x3f000000, ""], ["RSVD0", 30, 31, 0xc0000000, ""], ])
        self.TXEFS = mmio_register("TXEFS", self.bar, 0xf4, 4, 0x0, 0x0, "dunno", [["EFFL", 0, 5, 0x3f, ""], ["RSVD3", 6, 7, 0xc0, ""], ["EFGI", 8, 12, 0x1f00, ""], ["RSVD2", 13, 15, 0xe000, ""], ["EFPI", 16, 20, 0x1f0000, ""], ["RSVD1", 22, 23, 0xc00000, ""], ["EFF", 24, 24, 0x1000000, ""], ["TEFL", 25, 25, 0x2000000, ""], ["RSVD0", 26, 31, 0xfc000000, ""], ])
        self.TXEFA = mmio_register("TXEFA", self.bar, 0xf8, 4, 0x0, 0x0, "dunno", [["EFAI", 0, 4, 0x1f, ""], ["RSVD0", 5, 31, 0xffffffe0, ""], ])
#        self.TEST = mmio_register("TEST", self.bar, 0x10, 4, 0x0, 0x0, "not supported", [["LBCK", 4, 1, 0x1, "\"Read only value of the size in bytes of the Message RAM of this canss instance&amp;lt;br&amp;gt;                          @@jstokes3, need to set the default value where this RDL is instantiated\""]])
#        self.MSG_RAM_SIZE = mmio_register("MSG_RAM_SIZE", self.bar, 0x500, 4, 0x4600, 0x4600, "not supported", [["SIZE_B", 0, 31, 0xFFFFFFFF, "\"Read only value of the size in bytes of the Message RAM of this canss instance&amp;lt;br&amp;gt;                          @@jstokes3, need to set the default value where this RDL is instantiated\""]])
#        self.CTL = mmio_register("CTL", self.bar, 0x504, 4, 0x0, 0x0, "not supported", [["CAN_DIS_MORD", 0, 0, 0x00000001, "\"Set to 1 to prevent reads to ECR.CEL and PSR.LEC from resetting the CAN error data in the register.\""], ["RSVD0", 1, 31, 0xFFFFFFFE, "\"Reserved\""]])
#        self.INT_CTL = mmio_register("INT_CTL", self.bar, 0x508, 4, 0x0, 0x0, "not supported", [["PRIMARY_INT_EN", 0, 0, 0x00000001, "\"Enables the primary interrupt output int_o.[br]&amp;lt;br&amp;gt;                         Software is expected to set PUNIT_INT_EN or PRIMARY_INT_EN to b1, but not both.\""], ["PUNIT_INT_EN", 1, 1, 0x00000002, "\"Enables the canss PUNIT interrupt output int_punit_o.[br]&amp;lt;br&amp;gt;                         Software is expected to set PUNIT_INT_EN or PRIMARY_INT_EN to b1, but not both.\""], ["RSVD0", 2, 31, 0xFFFFFFFC, "\"Reserved\""]])
#        self.INT_STAT = mmio_register("INT_STAT", self.bar, 0x50C, 4, 0x0, 0x0, "not supported", [["THIS_CAN_CONT_INT", 0, 0, 0x00000001, "\"If asserted then this instance of the M_TTCAN controller has its interrupt asserted.\""], ["THIS_CAN_PERR_INT", 1, 1, 0x00000002, "\"Parity error interrupt for this CAN instance.\""], ["OTHER_CAN_CONT_INT", 2, 2, 0x00000004, "\"If asserted then the other instance of the M_TTCAN controller has its interrupt asserted.\""], ["OTHER_CAN_PERR_INT", 3, 3, 0x00000008, "\"Parity error interrupt for the other CAN instance.\""], ["RSVD0", 4, 31, 0xFFFFFFF0, "\"Reserved\""]])
#        self.MSGRAM_ADDR_CONFLICT_STAT = mmio_register("MSGRAM_ADDR_CONFLICT_STAT", self.bar, 0x510, 4, 0x0, 0x0, "not supported", [["CAN_ADDR_CONFLICT_OFFSET", 0, 14, 0x00007FFF, "\"The M_TTCAN address that the conflict between an AHB access to the MSGRAM simultaneous to an M_TTCAN access to MSGRAM.\""], ["RSVD0", 15, 15, 0x00008000, "\"Reserved\""], ["ADDR_CONFLICT_OCCURED", 16, 16, 0x00010000, "\"A flag to indicate that an address conflict has occurred. This can be used to help the debug of the CAN device driver.[br][br]Note that this does not cause an interrupt.\""], ["RSVD1", 17, 31, 0xFFFE0000, "\"Reserved\""]])
#        self.TIMESTAMP_CTL = mmio_register("TIMESTAMP_CTL", self.bar, 0x514, 4, 0x0, 0x0, "not supported", [["LXTSC", 0, 0, 0x00000001, "\"Capture Local Cross Timestamp\""], ["RXTSC", 1, 1, 0x00000002, "\"Capture Remote Cross Timestamp\""], ["LXTSV", 2, 2, 0x00000004, "\"Local Cross Timestamp Valid\""], ["RXTSV", 3, 3, 0x00000008, "\"Remote Cross Timestamp Valid\""], ["RSVD0", 4, 31, 0xFFFFFFF0, "\"Reserved\""]])
#        self.LOCALTIMESTAMP_HIGH = mmio_register("LOCALTIMESTAMP_HIGH", self.bar, 0x518, 4, 0x0, 0x0, "not supported", [["LTH", 0, 31, 0xFFFFFFFF, "\"Local Timestamp High\""]])
#        self.LOCALTIMESTAMP_LOW = mmio_register("LOCALTIMESTAMP_LOW", self.bar, 0x51C, 4, 0x0, 0x0, "not supported", [["LTL", 0, 31, 0xFFFFFFFF, "\"Local Timestamp Low\""]])
    

        self.mmio_reglist = [self.MSG_RAM_SIZE, self.CTL, self.INT_CTL, self.INT_STAT, self.MSGRAM_ADDR_CONFLICT_STAT, self.TIMESTAMP_CTL, self.LOCALTIMESTAMP_HIGH, self.LOCALTIMESTAMP_LOW, 
                             self.PAR_CTL_STAT, self.PAR_ERR_OFFSET, self.PAR_EINJ_CTL_STAT, self.PAR_EINJ_OFFSET, self.PAR_EINJ_DATA_MASK, self.PAR_EINJ_PARITY_MASK,  
                             self.CREL, self.ENDN, self.CUST, self.DBTP, self.TEST, self.RWD, self.CCCR, self.NBTP, self.TSCC, self.TSCV, self.TOCC, self.TOCV, self.ECR, self.PSR, 
                             self.TDCR, self.IR, self.IE, self.ILS, self.ILE, self.GFC, self.SIDFC, self.XIDFC, self.XIDAM, self.HPMS, self.NDAT1,
                             self.NDAT2, self.RXF0C, self.RXF0S, self.RXF0A, self.RXBC, self.RXF1C, self.RXF1S, self.RXF1A, self.RXESC, 
                             self.TXBC, self.TXFQS, self.TXESC, self.TXBRP, self.TXBAR, self.TXBCR, self.TXBTO, self.TXBCF, self.TXBTIE, self.TXBCIE, self.TXEFC, self.TXEFS, self.TXEFA]
        
    def printfields(self):
        for i in range(len(self.pci_reglist)):
            self.pci_reglist[i].printfields()
        for i in range(len(self.mmio_reglist)):
            self.mmio_reglist[i].printfields()

    def readall(self):
                   
        if (self.dev == 0x1D):
            if (self.func == 0):
                print ('DEV: CAN0')
            #elif (self.func == 1):
            #    print 'DEV: I3C1'
            for i in range(len(self.pci_reglist)):
                log_print(var_log_INFORMATION, '%s (0x%08x) = 0x%08x' % (self.pci_reglist[i].name, self.mmio_reglist[i].bar+self.mmio_reglist[i].offset, self.pci_reglist[i].read()))  
        
            for i in range(len(self.mmio_reglist)):
                log_print(var_log_INFORMATION, '%s (0x%08x) = 0x%08x' % (self.mmio_reglist[i].name, self.mmio_reglist[i].bar+self.mmio_reglist[i].offset, self.mmio_reglist[i].read()))   
            
                
    def checkdefaults(self):
        for i in range(len(self.mmio_reglist)):
            self.mmio_reglist[i].checkdefault()   
    
