import itpii
from itpii.datatypes import *
itp = itpii.baseaccess()
#itp.vp = -1 if not hasattr(itp, 'vp') else itp.vp #-1 actually points to thread 3 since there are 4 processor threads aligning from 0 to 3 (4-1)
itp.vp = 0
itp.base = 16 if not hasattr(itp, 'base') else itp.base

# #define CONFIG_ADDRESS 0x0CF8

# #define CONFIG__DATA 0x0CFC



#****************************************************************************

# OpenPciCfg (bus, device, function)

# Arguments:

#    bus - PCI bus number where the configuration cycle should take place.

#    device - device on the PCI bus which should respond to the cycle.

#    function - Function within the device which is being configured.

# Returns:

#   ---removed: 0 - successful

#   ---removed: 1 - error

# Description:

#    This routine will open the PCI configuration space and prepare for

#    reading or writing the specifed bus/device/function.

#    ReadPciCfg and WritePciCfg can be called to do actual read and writes.

#****************************************************************************



def OpenPciCfg(*argvector):
    config_add = Ord4()			#OrdX X: X represents the number of bytes assigned to the unknown
    bus = Ord1()
    PCIdevice = Ord1()
    function = Ord1()
    if len(argvector) == 0x3:
        bus = argvector[0x0]
        PCIdevice = argvector[0x1]
        function = argvector[0x2]
    else:
        itpii.printf("USAGE: OpenPciCfg (<bus>, <device>, <function>)\n")
        return()
    config_add = itp.threads[itp.vp].dport(0xcf8)# Get a starting point for R bits
    config_add &= 0x7f000003# Zero out non-reserved bits
    config_add |= 0x80000000# Set the Config enable bit
    config_add |= (bus & 0xff) * 0x10000# Set the bus number
    config_add |= (PCIdevice & 0x1f) * 0x800# Set the device number
    config_add |= (function & 0x7) * 0x100# Set the function number
    itp.threads[itp.vp].dport(0xcf8,config_add)# Write out the value


#****************************************************************************

# ClosePciCfg ()

# Arguments: None

# Returns:

#    0 - successful

#    1 - error

# Description:

#   This routine will close the PCI config space by writing 0 to 0CF8

#****************************************************************************



def ClosePciCfg(*argvector):
    if len(argvector) != 0x0:
        itpii.printf("USAGE: ClosePciCfg ()\n")
        return()
    itp.threads[itp.vp].dport(0xcf8,0x0)
    return()




#****************************************************************************

# ReadPciCfg (cfgreg, numbytes)

# Arguments:

#    cfgreg - configuration register to read

#    numbytes - Number of bytes to read from offset cfgreg

# Returns:

#    Value read from configuration space

# Description:

#    This routine will read numbytes of _data from the PCI configuration

#    space starting at offset cfgreg.  OpenPciCfg should be called first to

#    prime the system to do config cycles.

#****************************************************************************

def ReadPciCfg(*argvector):
    readaddr = Ord2()
    numbytes = Ord1()
    cfgreg = Ord1()
    config_addr = Ord4()
    # Check for valid arguments
    if len(argvector) != 0x2:
        itpii.printf("USAGE: ReadPciCfg (<register>, <number of bytes>)\n")
        return()
    # assign the arguments to readable variable names
    cfgreg = argvector[0x0]
    numbytes = argvector[0x1]
    readaddr = 0xcfc + (cfgreg & 0x3)
    # Check for valid read length
    if (numbytes < 0x1) or (numbytes > 0x4):
        itpii.printf("ERROR: Read length must be between 1 and 4\n")
        return()
    # Be sure the defined read does not cross a DWORD boundary
    if ((cfgreg % 0x4) + numbytes) > 0x4:
        itpii.printf("ERROR: Reading %d bytes from %x crosses DWORD boundary\n",numbytes,cfgreg)
        return()
    # Put the config register into the CONFIG_ADDRESS port
    config_addr = itp.threads[itp.vp].dport(0xcf8)
    config_addr &= 0xffffff03# zero out the register offset
    config_addr |= (cfgreg & 0xfc)# set the new register value
    itp.threads[itp.vp].dport(0xcf8,config_addr)# output the new value
    # Do the proper read based on the desired length
    if numbytes == 0x1:
        return(itp.threads[itp.vp].port(readaddr))
    else:
        if numbytes == 0x2:
            return(itp.threads[itp.vp].wport(readaddr))
        else:
            if numbytes == 0x4:
                return(itp.threads[itp.vp].dport(readaddr))
            else:
                itpii.printf("ERROR: Unsupported read length %d\n",numbytes)
                return()


#****************************************************************************

# WritePciCfg (cfgreg, _data, numbytes)

# Arguments:

#    cfgreg - configuration register to write

#    _data - _data to be written to the configuration register

#    numbytes - Number of bytes to write to offset cfgreg

# Returns:

#    0 - successful

#    non-zero - error

# Description:

#    This routine will write _data which is numbytes in length, to the PCI

#    configuration space starting at offset cfgreg.  OpenPciCfg should be

#    called first to prime the system to do config cycles

#****************************************************************************



def WritePciCfg(*argvector):
    writeaddr = Ord2()
    numbytes = Ord1()
    _data = Ord4()
    cfgreg = Ord1()
    config_addr = Ord4()
    # Check for valid arguments
    if len(argvector) != 0x3:
        itpii.printf("USAGE: WritePciCfg (<cfgreg>, <_data>, <number of bytes>)\n")
        return()
    # Assign the arguments to meaningful variables
    cfgreg = argvector[0x0]
    _data = argvector[0x1]
    numbytes = argvector[0x2]
    writeaddr = 0xcfc + (cfgreg & 0x3)
    if (numbytes < 0x1) or (numbytes > 0x4):
        itpii.printf("ERROR: Write length must be between 1 and 4\n")
        return()
    if ((cfgreg % 0x4) + numbytes) > 0x4:
        itpii.printf("ERROR: Reading %d bytes from %x crosses DWORD boundary\n",numbytes,cfgreg)
        return()
    # Put the config register into the CONFIG_ADDRESS port
    config_addr = itp.threads[itp.vp].dport(0xcf8)
    config_addr &= 0xffffff03
    config_addr |= (cfgreg & 0xfc)
    itp.threads[itp.vp].dport(0xcf8,config_addr)
    # Do the write cycle based on the desired length
    if numbytes == 0x1:
        itp.threads[itp.vp].port(writeaddr,_data)
    else:
        if numbytes == 0x2:
            itp.threads[itp.vp].wport(writeaddr,_data)
        else:
            if numbytes == 0x4:
                itp.threads[itp.vp].dport(writeaddr,_data)
            else:
                itpii.printf("ERROR: Unsupported write length %d\n",numbytes)
                return()
    return()



#****************************************************************************

# ShowPciCfg (bus, device, function)

# Arguments:

#    bus - PCI bus number where the configuration cycle should take place.

#    device - device on the PCI bus which should respond to the cycle.

#    function - Function within the device which is being configured.

# Returns:

#    0 - successful

#    1 - error

# Description:

#    This routine will display the values of all the PCI config registers

#    for a specific bus, device, and function.

#****************************************************************************



def ShowPciCfg(*argvector):
    config_addr = Ord4()
    readaddr = Ord2()
    bus = Ord1()
    PCIdevice = Ord1()
    function = Ord1()
    register = Ord2()
    if len(argvector) == 0x3:
        bus = argvector[0x0]
        PCIdevice = argvector[0x1]
        function = argvector[0x2]
    else:
        itpii.printf("USAGE: ShowPciCfg (<bus>, <device>, <function>)\n")
        return()
    # Open PCI config space and get initial value for config_address
    OpenPciCfg(bus,PCIdevice,function)
    config_addr = itp.threads[itp.vp].dport(0xcf8)
    # Print the header
    itpii.printf("+-----------------------------------------------------+\n") #  %02X used to convert decimal to hexa
    itpii.printf("|Bus: %02X, device: %02X, Function: %02X                    |\n",bus,PCIdevice,function) 
    itpii.printf("|##| x0|x1|x2|x3|x4|x5|x6|x7 | x8|x9|xA|xB|xC|xD|xE|xF|\n")
    itpii.printf("|-----------------------------------------------------|\n")
    # Loop through all 256 configuration registers
    register = 0x0
    while register < 256:
        # Change config address every four reads
        if not (register & 0x3):
            config_addr &= 0xffffff03# zero out the register value
            config_addr |= register# set the new register value
            itp.threads[itp.vp].dport(0xcf8,config_addr)# output the new value
        # Update to a new line in the output every 16 reads
        if not (register & 0xf):
            itpii.printf("|%02X|",register)
        if (register % 0x10) == 0x8:
            itpii.printf(" |")
        # Get the config register value and print it
        readaddr = 0xcfc + (register & 0x3)
        itpii.printf(" %02X",itp.threads[itp.vp].port(readaddr))
        if (register % 0x10) == 0xf:
            itpii.printf("|\n")
        register += 1
    itpii.printf("+-----------------------------------------------------+\n")
    ClosePciCfg()
    return()



#****************************************************************************

# scan_pci

# Arguments:

#    highest_bus : input the highest bus# to scan

# Description:

#    This routine will check for all PCI device locations and report where

#    PCI devices are found.

#****************************************************************************



def scan_pci(*argvector):
    lowest_bus = Ord1()
    highest_bus = Ord1()
    bus = Ord1()
    PCIdevice = Ord2()
    function = Ord1()
    ret_val = Ord2()
    vid = Ord2()
    DID = Ord2()
    header_type_reg = Ord1()
    max_function = Ord1()
    base_class_reg = Ord1()
    full_class_reg = Ord2()
    revision_reg = Ord1()
    subbusrange_reg = Ord2()
    notes = String("12345678abcdefg")
    if len(argvector) == 0x1:
        lowest_bus = 0x0
        highest_bus = argvector[0x0]
    else:
        if len(argvector) == 0x2:
            lowest_bus = argvector[0x0]
            highest_bus = argvector[0x1]
        else:
            itpii.printf("\nThis proc scans the pci bus,device,functions for non FFFF device ID's\n")
            itpii.printf("And prints them. A partial list of device class's is decoded.\n\n")
            itpii.printf("Example Usage:\n--------------\n")
            itpii.printf("scan_pci (<highest_bus#>)\n- scans from bus 0 thru bus <highest_bus#>\n")
            itpii.printf("\nOR\n\n")
            itpii.printf("scan_pci (<lowest_bus#>,<highest_bus#>)\n- scans from <lowest_bus#> thru bus <highest_bus#>\n")
            return()
    itpii.printf("\t+---+------+--------+------+------+--------+-----------------+----------+\n")
    itpii.printf("\t|BUS|device|Function|Vendor|device|Stepping|device class:   |SubbusRnge|\n")
    itpii.printf("\t| # |   #  |   #    |  ID  |  ID  | Rev#   |                 |  Hi:Low  |\n")
    itpii.printf("\t|   |      |        |(reg0)|(reg2)|(reg8)  |(reg A,B decoded)|(reg1a,19)|\n")
    itpii.printf("\t+---+------+--------+------+------+--------+-----------------+----------+\n")
    bus = lowest_bus
    while bus <= highest_bus:
        PCIdevice = 0x0
        while PCIdevice <= 0x1f:
            #if the header type register says this isn't a multi-function device, then we don't need to check 
            #			the rest of the functions > 0.
            OpenPciCfg(bus,PCIdevice,0x0)
            header_type_reg = ReadPciCfg(0xe,0x1)
            vid = ReadPciCfg(0x0,0x2)
            if (header_type_reg <= 0x7f) or (vid == 0xffff):
                # if bit7 is 0 -- meaning it is a single function device.
                max_function = 0x0
            else:
                max_function = 0x7
            function = 0x0
            while function <= max_function:
                OpenPciCfg(bus,PCIdevice,function)
                vid = itp.threads[itp.vp].wport(0xcfc)# Read the Vendor ID value
                DID = itp.threads[itp.vp].wport(0xcfc + 0x2)# Read the device ID value
                #print each function we are scanning even if it isn't a valid one: ie ff is read as DID
                itpii.printf("\t| %02X|  %02X  |  %02X    | %04X | %04X |\r",bus,PCIdevice,function,vid,DID)
                #but only keep the non ff DID ones on the screen
                #if it is a non-empty (ff) device, let's get its pci info and print
                if vid != 0xffff:
                    #first get the base class code to see what this thing does
                    base_class_reg = ReadPciCfg(0xb,0x1)
                    full_class_reg = ReadPciCfg(0xa,0x2)
                    revision_reg = ReadPciCfg(0x8,0x1)
                    subbusrange_reg = ReadPciCfg(0x19,0x2)
                    #if (base_class == 06){notes =12345678abcde}
                    notes = "???????????????"
                    if base_class_reg == 0x0:
                        notes = "BuiltBeforeDef "
                    if base_class_reg == 0x1:
                        notes = "Storage:IDE,etc"
                    if base_class_reg == 0x2:
                        notes = "NetworkContrler"
                    if base_class_reg == 0x3:
                        notes = "gfx controller "
                    if base_class_reg == 0x4:
                        notes = "Multi-Media dev"
                    if full_class_reg == 0x400:
                        notes = "MMedia:VideoCtl"
                    if full_class_reg == 0x401:
                        notes = "MMedia:AudioCtl"
                    if base_class_reg == 0x5:
                        notes = "MemoryControler"
                    if base_class_reg == 0x6:
                        notes = "bridge device  "
                    if full_class_reg == 0x600:
                        notes = "Host bridge    "
                    if full_class_reg == 0x601:
                        notes = "ISAorLPC bridge"
                    if full_class_reg == 0x604:
                        notes = "PCI-PCI bridge "
                    if base_class_reg == 0x7:
                        notes = "communications "
                    if full_class_reg == 0x703:
                        notes = "CommunCtl:Modem"
                    if base_class_reg == 0x8:
                        notes = "Generic IO CTL "
                    if base_class_reg == 0x9:
                        notes = "I/O:KB,Mouse,.."
                    if base_class_reg == 0xa:
                        notes = "Docking Station"
                    if base_class_reg == 0xb:
                        notes = "Processor      "
                    if base_class_reg == 0xc:
                        notes = "Serial BusCtl  "
                    if full_class_reg == 0xc03:
                        notes = "USB Controller "
                    if full_class_reg == 0xc00:
                        notes = "1394 Controller"
                    if full_class_reg == 0xc05:
                        notes = "SMbusController"
                    if full_class_reg == 0xff00:
                        notes = "TestCard?svaha?"
                    if full_class_reg == 0x1101:
                        notes = "Perf.Cntr?CHAP?"
                    itpii.printf("\t| %02X|  %02X  |  %02X    | %04X | %04X |  %02X    | %s |   %04X   |\n",bus,PCIdevice,function,vid,DID,revision_reg,notes,subbusrange_reg)
                function += 1
            PCIdevice += 1
        bus += 1
    itpii.printf("\t|___|______|________|______|______|________|_________________|__________|\n")



#****************************************************************************
# added from kevin farrens script 10/16/01:
# ReadPciCfgBits
# Arguments:
#    reg_offset : pci reg number to read
#    MSB        : highest bit number to read
#    LSB        : lowest bit number to read
# Description:
#    This routine will read the reg_offset(MSB:LSB) and return the result
#
#****************************************************************************
def ReadPciCfgBits(*argvector):
    reg_offset = Ord1()
    MSB = Int1()
    LSB = Int1()
    reg_value = Ord4()
    masked_value = Ord4()
    bit_mask = Ord4()
    bit_mask2 = Ord4()
    count = Int1()
    bytes_to_read = Ord1()
    if len(argvector) != 0x3:
        itpii.printf("This routine will read the reg_offset(MSB:LSB) and return the result)\n")
        itpii.printf("       as a dword, with the bits you wanted aligned to bit0\n")
        itpii.printf("       you have to openpcicfg first! use 0n# to say decimal!\n")
        itpii.printf("Example: ReadPciCfgBits (<0x0, 0n8, 0n4>) will return 0000008 if reg0=25608086\n")
        itpii.printf("USAGE: ReadPciCfgBits (<reg_offset>, <MSB>, <LSB>)\n")
        return()
    reg_offset = argvector[0x0]
    MSB = argvector[0x1]
    LSB = argvector[0x2]
    bit_mask = 0x1
    count = 0
    while count <= LSB:
        if count != 0x0:
            bit_mask = bit_mask + bit_mask
        count += 1
    bit_mask2 = bit_mask
    count = LSB
    while count < MSB:
        bit_mask = bit_mask + bit_mask
        bit_mask2 = bit_mask2 + bit_mask
        count += 1
    bit_mask = bit_mask2
    bytes_to_read = reg_offset % 0x4
    if bytes_to_read == 0x0:
        if MSB <= 0x31:
            bytes_to_read = 0x4
        else:
            itpii.printf("Error: MSB exceeds DWORD boundary!\n")
            return()
    if bytes_to_read == 0x1 or bytes_to_read == 0x2:
        if MSB <= 0x15:
            bytes_to_read = 0x2
        else:
            itpii.printf("Error: MSB exceeds DWORD boundary!\n")
            return()
    if bytes_to_read == 0x3:
        if MSB <= 0x7:
            bytes_to_read = 0x1
        else:
            itpii.printf("Error: MSB exceeds DWORD boundary!\n")
            return()
    reg_value = ReadPciCfg(reg_offset,bytes_to_read)
    masked_value = reg_value & bit_mask
    masked_value >>= LSB
    return(masked_value)


#****************************************************************************
# added from kevin farrens script 10/16/01:
# WritePciCfgBits
# Arguments:
#    reg_offset : pci reg number to write
#    MSB        : highest bit number to write
#    LSB        : lowest bit number to write
#    write_data : lowest bit number to write
# Description:
#    This routine will write "write_data" to the reg_offset(MSB:LSB)bits only
#
#****************************************************************************
def WritePciCfgBits(*argvector):
    reg_offset = Ord1()
    MSB = Int1()
    LSB = Int1()
    reg_value = Ord4()
    old_reg_value = Ord4()
    masked_value = Ord4()
    bit_mask = Ord4()
    bit_mask2 = Ord4()
    count = Int1()
    bytes_to_write = Ord1()
    write_data = Ord4()
    if len(argvector) != 0x4:
        itpii.printf("This routine will write -write_data- to the reg_offset(MSB:LSB)bits only)\n")
        itpii.printf("       \n")
        itpii.printf("       you have to openpcicfg first! use 0n# to say decimal!\n")
        itpii.printf("Example: WritePciCfgBits (<0x44, 0n8, 0n4,0xa>) will write xxxxxxax\n")
        itpii.printf("       to register 44hex. note: above xx means those bits untouched.\n")
        itpii.printf("USAGE: WritePciCfgBits (<reg_offset>, <MSB>, <LSB>,<write_data>)\n")
        return()
    reg_offset = argvector[0x0]
    MSB = argvector[0x1]
    LSB = argvector[0x2]
    write_data = argvector[0x3]
    bit_mask = 0x1
    count = 0
    while count <= LSB:
        if count != 0x0:
            bit_mask = bit_mask + bit_mask
        count += 1
    bit_mask2 = bit_mask
    count = LSB
    while count < MSB:
        bit_mask = bit_mask + bit_mask
        bit_mask2 = bit_mask2 + bit_mask
        count += 1
    bit_mask = ~bit_mask2
    bytes_to_write = reg_offset % 0x4
    if bytes_to_write == 0x0:
        if MSB <= 0x31:
            bytes_to_write = 0x4
        else:
            itpii.printf("Error: MSB exceeds DWORD boundary!\n")
            return()
    if bytes_to_write == 0x1 or bytes_to_write == 0x2:
        if MSB <= 0x15:
            bytes_to_write = 0x2
        else:
            itpii.printf("Error: MSB exceeds DWORD boundary!\n")
            return()
    if bytes_to_write == 0x3:
        if MSB <= 0x7:
            bytes_to_write = 0x1
        else:
            itpii.printf("Error: MSB exceeds DWORD boundary!\n")
            return()
    reg_value = ReadPciCfg(reg_offset,bytes_to_write)
    old_reg_value = reg_value
    write_data <<= LSB
    write_data = write_data & (~bit_mask)
    reg_value = reg_value & bit_mask
    reg_value = reg_value | write_data
    WritePciCfg(reg_offset,reg_value,bytes_to_write)


#****************************************************************************
# added from kevin farrens script 10/16/01:
# cfg_on
# Arguments:
#    reg_offset : pci reg number to read
#    MSB        : highest bit number to read
#    LSB        : lowest bit number to read
#    value      : value to write
# Description:
#    this script calls the writepcicfgbits script. my guess is that
#    he just wanted a shorter name for writepcicfgbits!
#****************************************************************************
def cfg_on(*argvector):
    reg_offset = Ord1()
    MSB = Ord1()
    LSB = Ord1()
    value = Ord4()
    reg_value = Ord4()
    if len(argvector) != 0x4:
        itpii.printf("This routine will write -write_data- to the reg_offset(MSB:LSB)bits only)\n")
        itpii.printf("       \n")
        itpii.printf("       you have to openpcicfg first! use 0n# to say decimal!\n")
        itpii.printf("Example: cfg_on (<0x44, 0n8, 0n4,0xa>) will write xxxxxxax\n")
        itpii.printf("       to register 44hex. note: above xx means those bits untouched.\n")
        itpii.printf("USAGE: cfg_on (<reg_offset>, <MSB>, <LSB>,<write_data>)\n")
        return()
    reg_offset = argvector[0x0]
    MSB = argvector[0x1]
    LSB = argvector[0x2]
    value = argvector[0x3]
    WritePciCfgBits(reg_offset,MSB,LSB,value)



#****************************************************************************
# added from kevin farrens script 10/16/01:
# cfg_chk
# Arguments:
#    bus,device,function : pci reg number to check
#    reg_offset : pci reg number to check
#    MSB        : highest bit number to check
#    LSB        : lowest bit number to check0x7
#    value      : value to check against
# Description:
#    this script reads the pci reg/bits specified and compares against
#    the expected "value" passsed in
#****************************************************************************
def cfg_chk(*argvector):
    bus = Ord1()
    PCIdevice = Ord1()
    function = Ord1()
    reg_offset = Ord1()
    MSB = Ord1()
    LSB = Ord1()
    value = Ord4()
    reg_value = Ord4()
    if len(argvector) != 0x7:
        itpii.printf("this script reads the pci reg/bits specified and compares against\n")
        itpii.printf("       the expected value passsed in\n")
        itpii.printf("       use 0n# to say decimal! for bit#'s\n")
        itpii.printf("Example: cfg_chk (0,0,0,0x44, 0n8, 0n4,0xa) will read reg 48, bit 8:4 and see if \n")
        itpii.printf("       those bits are 1010 -a- or not\n")
        itpii.printf("USAGE: cfg_chk (<bus>, <dev>, <fun>,<reg_offset>,<MSB>,<LSB>,<value>)\n")
        return()
    bus = argvector[0x0]
    PCIdevice = argvector[0x1]
    function = argvector[0x2]
    reg_offset = argvector[0x3]
    MSB = argvector[0x4]
    LSB = argvector[0x5]
    value = argvector[0x6]
    OpenPciCfg(bus,PCIdevice,function)
    reg_value = ReadPciCfgBits(reg_offset,MSB,LSB)
    if reg_value != value:
        itpii.printf("-----------------------------------------\n")
        itpii.printf("(%02X,%02X,%02X) reg_offset: %02X[%02d:%02d] read %16X not %16X\n",bus,PCIdevice,function,reg_offset,MSB,LSB,reg_value,value)
    # else {
    #        printf("-----------------------------------------\n")
    #        printf("(%02X,%02X,%02X) reg_offset: %02X[%02d:%02d] read %16X correctly!\n", bus, PCIdevice, function, reg_offset, MSB, LSB, reg_value)
    #    }

    
    function
    statement








