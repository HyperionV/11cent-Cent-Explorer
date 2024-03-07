from enum import Flag
import re
import datetime
# class for FAT32 entry status

def byteToDate(data):
    year = ((data & 0b1111111000000000) >> 9) + 1980
    month = (data & 0b0000000111100000) >> 5
    day = (data & 0b0000000000011111)

    try:
        return datetime.date(year, month, day)
    except:
        return datetime.date(1980, 1, 1)

def byteToTime(data):
    h = (data & 0b1111100000000000) >> 11
    m = (data & 0b0000011111100000) >> 5
    s = (data & 0b0000000000011111) * 2
    try:
        return datetime.time(h, m, s)
    except:
        return datetime.time(0, 0, 0)

class Attribute(Flag):
    READ_ONLY = 0x01
    HIDDEN = 0x02
    SYSTEM = 0x04
    VOLUME_ID = 0x08
    DIRECTORY = 0x10
    ARCHIVE = 0x20
    LONG_NAME = 0x0F

class Status(Flag):
    DELETED = 0xE5
    EMPTY = 0x00
    NORMAL = 0xFF

def read_sector(data, start, cnt, bytes_per_sector):
    data.seek(start * bytes_per_sector)
    return data.read(cnt * bytes_per_sector)
    
# Read FAT32 boot sector
class BootSector:
    def __init__(self, data, name):
        self.oem_name = data[3:11]
        self.bytes_per_sector = int.from_bytes(data[11:13], byteorder='little')
        self.sectors_per_cluster = int.from_bytes(data[13:14], byteorder='little')
        self.reserved_sectors = int.from_bytes(data[14:16], byteorder='little')
        self.fat_count = int.from_bytes(data[16:17], byteorder='little')
        self.total_sectors = int.from_bytes(data[32:36], byteorder='little')
        self.fat_size = int.from_bytes(data[36:40], byteorder='little')
        self.root_cluster = int.from_bytes(data[44:48], byteorder='little')
        self.volume_label = name
        self.fat_type = data[54:62]
        self.boot_code = data[62:510]
        self.boot_signature = data[510:512]
        self.RDET_start = self.reserved_sectors + self.fat_count * self.fat_size
        
        
    def __str__(self):
        return f'{self.oem_name.decode("utf-8").strip()}'

class FAT:
    def __init__(self, data):
        self.data = data
        self.size = len(data) / 4
        self.FAT = []
        for i in range(0, len(data), 4):
            self.FAT.append(int.from_bytes(data[i:i+4], byteorder='little'))
            
    def get_cluster_chain(self, start):
        chain = []
        while True:
            chain.append(start)
            if start >= 0x0FFFFFF8:
                break
            start = self.FAT[start]
        return chain
    
class Entry: 
    def __init__(self, data):
        self.name = data[0:11]
        self.longFileName = ''
        self.attr = Attribute(int.from_bytes(data[11:12], byteorder='little'))
        status = int.from_bytes(data[0:1], byteorder='little')
        if status != 0x00 and status != 0xE5:
            status = 0xFF
        
        self.status = Status(status)
            
        self.reserved = int.from_bytes(data[12:20], byteorder='little')
        create_time = data[14:16]
        create_date = data[16:18]

        self.create_time = byteToTime(int.from_bytes(create_time, byteorder='little'))
        self.create_date = byteToDate(int.from_bytes(create_date, byteorder='little'))
             
        last_access_date = data[18:20]
        
        self.last_access_date = byteToDate(int.from_bytes(last_access_date, byteorder='little'))
        
        last_write_time = data[22:24]
        last_write_date = data[24:26]
        
        self.last_write_time = byteToTime(int.from_bytes(last_write_time, byteorder='little'))
        
        year = int.from_bytes(last_write_date, byteorder='little')
        month = int.from_bytes(last_write_date, byteorder='little')
        day = int.from_bytes(last_write_date, byteorder='little')
        
        self.last_write_date = byteToDate(int.from_bytes(last_write_date, byteorder='little'))
        
        self.starting_cluster = int.from_bytes(data[0x14:0x16][::-1] + data[0x1A:0x1C][::-1], byteorder='big')
        self.file_size = int.from_bytes(data[28:32])
        self.extension = data[8:11]

    def __str__(self):
        return f'{self.name.decode("utf-8").strip()}'

class RDET:
    def __init__(self, pointer, offset, bytes_per_sector):
        self.entries = []
        self.size = 0
        self.sector = 0
        pointer.seek(offset)
        print('offset:', offset)
        self.read_entries(pointer, bytes_per_sector)

    def read_entries(self, pointer, bytes_per_sector=512):
        nameBuffer = ''
        self.sector = 0
        while True:
            data = pointer.read(bytes_per_sector)
            self.sector += 1
            for i in range(0, len(data), 32):
                entry = Entry(data[i:i+32])
                if entry.status == Status.EMPTY:
                    self.size = len(self.entries)
                    return
                if entry.status == Status.DELETED:
                    continue
                if entry.attr == Attribute.LONG_NAME:
                    string = data[i+1:i+11] + data[i+14:i+26] + data[i+28:i+32]
                    for i in range(0, len(string), 2):
                        if string[i:i+2] == b'\xff\xff':
                            string = string[:i]
                    nameBuffer = string.decode('utf-16-le') + nameBuffer
                    continue
                if nameBuffer:
                    entry.longFileName = nameBuffer
                    nameBuffer = ''
                self.entries.append(entry)
            

    def find_entry(self, name):
        for entry in self.entries:
            # print(entry.name.decode('utf-8').strip().lower())
            if entry.name.decode('utf-8').strip().lower() == name.lower():
                return entry
            if entry.longFileName.lower() == name.lower():
                return entry
        return None           
                
    def __str__(self) -> str:
        return f'{self.name}'
    
def read_chain(pointer, starting_cluster, sectors_per_cluster, bytes_per_sector, fat, RDET_start):
    data = b''
    for cluster in fat.get_cluster_chain(starting_cluster):
        data += read_sector(pointer, RDET_start + (cluster - 2) * sectors_per_cluster, sectors_per_cluster, bytes_per_sector)
    return data

class CDET:
    def __init__(self, data):
        self.entries = []
        self.read_entries(data)
        
    def read_entries(self, data):
        nameBuffer = ''
        self.sector = 0
        for i in range(0, len(data), 32):
            entry = Entry(data[i:i+32])
            if entry.status == Status.EMPTY:
                self.size = len(self.entries)
                return
            if entry.status == Status.DELETED:
                continue
            if entry.attr == Attribute.LONG_NAME:
                string = data[i+1:i+11] + data[i+14:i+26] + data[i+28:i+32]
                for i in range(0, len(string), 2):
                    if string[i:i+2] == b'\xff\xff':
                        string = string[:i]
                nameBuffer = string.decode('utf-16-le') + nameBuffer
                continue
            if nameBuffer:
                entry.longFileName = nameBuffer
                nameBuffer = ''
            self.entries.append(entry)

    def find_entry(self, name):
        for entry in self.entries:
            # print(entry.name.decode('utf-8').strip().lower())
            if entry.name.decode('utf-8').strip().lower() == name.lower():
                return entry
            if entry.longFileName.lower() == name.lower():
                return entry
        return None           
                
    def __str__(self) -> str:
        return f'{self.name}' 

class Node:
    def __init__(self, entry = None, isRoot = False):
        self.isRoot = isRoot
        self.parent = None
        self.children = []
        self.info = entry

class FAT32:
    def __init__(self, name):
        self.name = name
        with open(f'\\\\.\\{self.name}:', 'rb') as f:
            self.data = f.read(512)
            self.boot_sector = BootSector(data, self.name + ':')
        self.ptr = open(f'\\\\.\\{self.name}:', 'rb')
        self.RDET = RDET(self.ptr, self.boot_sector.RDET_start * self.boot_sector.bytes_per_sector, self.boot_sector.bytes_per_sector)
        self.root = Node(entry = None, isRoot = True)
#       data_a = read_chain(cu, 5, boot_sector.sectors_per_cluster, boot_sector.bytes_per_sector, fat, boot_sector.RDET_start)
#       cdet_a = CDET(data_a)
        
    def vis(self, start_cluster, dir, parRoot = None):
        if (parRoot == None):
            parRoot = self.root
        # curEntry = read_chain(self.ptr, start_cluster, boot_sector.sectors_per_cluster, boot_sector.bytes_per_sector, fat, boot_sector.RDET_start)
        # curCDET = CDET(curEntry)
        curEntry = []
        if (parRoot == self.root):
            curEntry = self.RDET.entries
        else:
            tmp = read_chain(self.ptr, start_cluster, boot_sector.sectors_per_cluster, boot_sector.bytes_per_sector, fat, boot_sector.RDET_start)
            curEntry = CDET(tmp).entries
        for i in curEntry:
            if (i.starting_cluster == start_cluster):
                continue 
            if (i.name.strip() == b'.' or i.name.strip() == b'..'):
                continue
            if ((not (i.attr & Attribute.DIRECTORY)) and (not (i.attr & Attribute.ARCHIVE))):
                continue
            if ((i.attr & Attribute.HIDDEN)):
                continue
            print('?', i.attr, ' ', i.status)
            if ((i.status == Status.DELETED) or (i.status == Status.EMPTY)):
                continue
            curNode = Node(entry = i)
            curNode.parent = parRoot
            parRoot.children.append(curNode)
            tmpDir = dir
            if (i.longFileName != ''):
                tmpDir = dir + '\\' + i.longFileName
            else:
                curName = i.name.decode().strip()
                tmpDir = dir + '\\' + curName
            if (i.attr & Attribute.DIRECTORY):
                self.vis(i.starting_cluster, tmpDir, curNode)
    
    def get_dir_tree(self, start_cluster, curRoot): # get node that has known start cluster 
        if (not (curRoot.info.attr & Attribute.DIRECTORY)):
            return
        if (curRoot.info.starting_cluster == start_cluster):
            return curRoot
        for i in curRoot.children:
            self.get_dir_tree(start_cluster, i)

    # def read_txt_file(self, txtNode):
    #     data = read_chain

# test boot sector
driveLetter = 'F'
boot_sector = None
with open(f'\\\\.\\{driveLetter}:', 'rb') as f:
    data = f.read(512)
    boot_sector = BootSector(data, 'F:')
    print('volume label: ', boot_sector.volume_label)
    print('bytes per sector: ', boot_sector.bytes_per_sector)
    print('sec/cluster: ', boot_sector.sectors_per_cluster)
    print(boot_sector.reserved_sectors)
    print(boot_sector.fat_count)
    print(boot_sector.total_sectors)
    print(boot_sector.fat_size)
    print(boot_sector.root_cluster)
    print(boot_sector.total_sectors * boot_sector.bytes_per_sector / (1024 * 1024))
    
print('rdet_start:', boot_sector.RDET_start)

cu = open(f'\\\\.\\{driveLetter}:', 'rb')


lmao = RDET(cu, boot_sector.RDET_start * boot_sector.bytes_per_sector, boot_sector.bytes_per_sector)
data_start = boot_sector.RDET_start + lmao.sector
print('start\n')
for i in lmao.entries:
    print('Name:', i.name)
    print('Long Name:', i.longFileName)
    print('Attr:', i.attr)
    print('Status:', i.status)
    print('Reserved:', i.reserved)
    print('Create Time:', i.create_time)
    print('Create Date:', i.create_date)
    print('Last Access Date:', i.last_access_date)
    print('Last Write Time:', i.last_write_time)
    print('Last Write Date:', i.last_write_date)
    print('Starting Cluster:', i.starting_cluster)
    if (i.attr == Attribute.DIRECTORY):
        print('File Size:', i.file_size)
        print('Extension:', i.extension)
    print('---------------------------------')
    
fat = FAT(read_sector(cu, boot_sector.reserved_sectors, boot_sector.fat_size * boot_sector.fat_count, boot_sector.bytes_per_sector)) 
    
data_a = read_chain(cu, 5, boot_sector.sectors_per_cluster, boot_sector.bytes_per_sector, fat, boot_sector.RDET_start)
cdet_a = CDET(data_a)
print('-' * 100)
# print('data_a:', data_a)
print('-' * 100)


for i in cdet_a.entries:
    print('Name:', i.name)
    print('Long Name:', i.longFileName)
    print('Attr:', i.attr)
    print('Status:', i.status)
    print('Reserved:', i.reserved)
    print('Create Time:', i.create_time)
    print('Create Date:', i.create_date)
    print('Last Access Date:', i.last_access_date)
    print('Last Write Time:', i.last_write_time)
    print('Last Write Date:', i.last_write_date)
    print('Starting Cluster:', i.starting_cluster)
    print('File Size:', i.file_size)
    print('Extension:', i.extension)
    print('---------------------------------')

print('FAT32\n')
f32 = FAT32('F')
f32.vis(0, '\\\\.\\F:')