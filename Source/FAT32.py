from enum import Flag
import re
import datetime
# class for FAT32 entry status

# function for converting byte to date
def byteToDate(data):
    year = ((data & 0b1111111000000000) >> 9) + 1980
    month = (data & 0b0000000111100000) >> 5
    day = (data & 0b0000000000011111)

    try:
        return datetime.date(year, month, day)
    except:
        return datetime.date(1980, 1, 1)

#function for converting byte to time
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
    
    def offset_from_cluster(self, cluster_idx):
        offset = self.reserved_sectors + (self.fat_size * self.fat_count) + ((cluster_idx - 2) * self.sectors_per_cluster)
        return offset
        
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
        self.file_size = int.from_bytes(data[28:32], byteorder='little')
        self.extension = data[8:11]

    def __str__(self):
        return f'{self.name.decode("utf-8").strip()}'

class RDET:
    def __init__(self, pointer, offset, bytes_per_sector):
        self.entries = []
        self.size = 0
        self.sector = 0
        pointer.seek(offset)
        # print('offset:', offset)
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

class SDET:
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
    def __init__(self, dir = None, entry = None, isRoot = False):
        self.isRoot = isRoot
        self.parent = None
        self.children = []
        self.info = entry
        self.dir = dir
        self.name = ''
    def setName(self, name):
        self.name = name
    def __str__(self):
        return self.name
        
class FAT32:
    def __init__(self, name):
        self.name = name
        with open(f'\\\\.\\{self.name}:', 'rb') as f:
            self.data = f.read(512)
            self.boot_sector = BootSector(self.data, self.name + ':')
        self.ptr = open(f'\\\\.\\{self.name}:', 'rb')
        self.fat = FAT(read_sector(self.ptr, self.boot_sector.reserved_sectors, self.boot_sector.fat_size * self.boot_sector.fat_count, self.boot_sector.bytes_per_sector))
        self.RDET = RDET(self.ptr, self.boot_sector.RDET_start * self.boot_sector.bytes_per_sector, self.boot_sector.bytes_per_sector)
        self.root = Node(dir = self.name + ':', entry = None, isRoot = True)
        self.curNode = self.root
        self.get_dir_tree()
#       data_a = read_chain(cu, 5, boot_sector.sectors_per_cluster, boot_sector.bytes_per_sector, fat, boot_sector.RDET_start)
#       SDET_a = SDET(data_a)
        
    def getVolumeInfo(self):
        print('Volume name: ', self.name + ':')
        print('OEM_Name: ', self.boot_sector.oem_name.decode())
        print('Bytes per sector: ', self.boot_sector.bytes_per_sector)
        print('Sectors per cluster: ', self.boot_sector.sectors_per_cluster)
        print('Reserved sectors: ', self.boot_sector.reserved_sectors)
        print('Number of sectors in volume: ', self.boot_sector.total_sectors)

    def offset_from_cluster(self, cluster_index):
        reserved_sectors = self.boot_sector['Reserved Sectors']
        size_of_fat = self.boot_sector['Sectors Per FAT'] * self.boot_sector['Bytes Per Sector']
        num_fat_copies = self.boot_sector['No. Copies of FAT']
        sectors_per_cluster = self.boot_sector['Sectors Per Cluster']
        offset = reserved_sectors + (size_of_fat * num_fat_copies) + ((cluster_index - 2) * sectors_per_cluster)
        return offset
    
    def vis(self, start_cluster, dir, parRoot = None):
        if (parRoot == None):
            parRoot = self.root
        curEntry = []
        if (parRoot == self.root):
            curEntry = self.RDET.entries
        else:
            tmp = read_chain(self.ptr, start_cluster, self.boot_sector.sectors_per_cluster, self.boot_sector.bytes_per_sector, self.fat, self.boot_sector.RDET_start)
            curEntry = SDET(tmp).entries
        for i in curEntry:
            if (i.starting_cluster == start_cluster):
                continue 
            if (i.name.strip() == b'.' or i.name.strip() == b'..'):
                continue
            if ((not (i.attr & Attribute.DIRECTORY)) and (not (i.attr & Attribute.ARCHIVE))):
                continue
            if ((i.attr & Attribute.HIDDEN)):
                continue
            if ((i.status == Status.DELETED) or (i.status == Status.EMPTY)):
                continue
            curNode = Node(entry = i)
            curNode.parent = parRoot
            parRoot.children.append(curNode)
            tmpDir = dir
            if (i.longFileName != ''):        
                i.longFileName.replace('\x00', '')
                i.longFileName = ''.join(i.longFileName.split('\x00'))
                extension = curNode.info.extension.decode().strip()
                extension.replace('\x00', '')
                extension = ''.join(extension.split('\x00'))
                if (extension != ''):
                    extension = '.' + extension
                extension = extension.lower()         
                curNode.setName(i.longFileName.strip(extension) + extension)
                tmpDir = dir + '\\' + i.longFileName + extension
            else:
                extension = curNode.info.extension.decode().strip()
                extension.replace('\x00', '')
                extension = ''.join(extension.split('\x00'))
                curName = i.name.decode().strip(extension).strip()
                curName.replace('\x00', '')
                curName = ''.join(curName.split('\x00'))
                if (extension != ''):
                    extension = '.' + extension
                curNode.setName(curName + extension)
                tmpDir = dir + '\\' + curName + extension
            curNode.dir = tmpDir
            if (i.attr & Attribute.DIRECTORY):
                self.vis(i.starting_cluster, tmpDir, curNode)
    
    def get_dir_tree(self, start_cluster, curRoot):
        if (not (curRoot.info.attr & Attribute.DIRECTORY)):
            return
        if (curRoot.info.starting_cluster == start_cluster):
            return curRoot
        for i in curRoot.children:
            self.get_dir_tree(start_cluster, i)

    def printFile(self, txtNode):        
        rawData = read_chain(self.ptr, txtNode.info.starting_cluster, self.boot_sector.sectors_per_cluster, self.boot_sector.bytes_per_sector, self.fat, self.boot_sector.RDET_start)
        textSize = txtNode.info.file_size
        fileContent = rawData[:textSize]
        fileName = txtNode.name
        if (fileName.lower().endswith('.txt')): 
            print(fileContent.decode('utf-8', errors = 'replace'))
        elif (fileName.lower().endswith('.docx')):
            print('Please use MS Word to open this file!')
        elif (fileName.lower().endswith('.pdf')):
            print('Please use Adobe Acrobat Reader to open this file!')
        elif (fileName.lower().endswith('.png')):
            print('Please use an image viewer to open this file!')
        elif (fileName.lower().endswith('.jpg')):
            print('Please use an image viewer to open this file!')
        elif (fileName.lower().endswith('.jpeg')):
            print('Please use an image viewer to open this file!')
        elif (fileName.lower().endswith('.gif')):
            print('Please use an image viewer to open this file!')
        elif (fileName.lower().endswith('.mp4')):
            print('Please use a video player to open this file!')
        elif (fileName.lower().endswith('.mp3')):
            print('Please use a music player to open this file!')
        elif (fileName.lower().endswith('.cpp')):
            print('Please use a code editor to open this file!')
        elif (fileName.lower().endswith('.c')):
            print('Please use a code editor to open this file!')
        elif (fileName.lower().endswith('.java')):
            print('Please use a code editor to open this file!')
        else:
            print('Please use an appropriate program to open this file!')
    
    def get_dir_tree(self):
        self.root = Node(dir = self.name + ':', entry = None, isRoot = True)
        self.vis(0, f'\\\\.\\{self.name}:')
        self.curNode = self.root
        
    def draw_dir_tree(self, curNode, depth = 0):
        if (curNode.isRoot):
            print(self.name + ':')
        elif (depth == 0):
            print(curNode.info.name.decode())
        for child in curNode.children:
            print('├─', end = '' )
            for i in range(depth):
                print('──', end = '')
            print(child.name)
            if (child.info.attr & Attribute.DIRECTORY):
                self.draw_dir_tree(curNode = child, depth = depth + 1)

    # From NTFS
    def getDir(self):
        allDir = []
        allDir.append(self.curNode.parent)
        for child in self.curNode.children:
            if (child == self.curNode):
                continue
            allDir.append(child)
        return allDir

    def listDir(self):
        allDir = self.getDir()
        i = 0
        # format column
        print(f'{"Index":<8} | {"Type":<14} | {"Date":<12} | {"Time":<12} | {"Size(B)":<9} | {"Name":<30}')
        print('-' * (8+14+30+15+20+20))
        for child in allDir:
            if (child == None):
                continue
            if (child == self.curNode.parent):
                if (child == self.root):
                    continue
                i = i + 1
                # print(str(i) + '.   directory\t/..')
                print(f'{str(i):<8} | {"directory":<14} | {str(child.info.create_date).strip():<12} | {str(child.info.create_time).strip():<12} | {"":<9} | {"/..":<30}')
                continue
            if (child.info.attr & Attribute.DIRECTORY):
                i = i + 1
                # print(str(i) + '.   directory\t/', end = '')
                # print(child)
                print(f'{str(i):<8} | {"directory":<14} | {str(child.info.create_date).strip():<12} | {str(child.info.create_time).strip():<12} | {"":<9} | {str("/" + child.name.strip()):<30}')
        for child in allDir:
            if (child == self.curNode.parent or child == None):
                continue
            if (child.info.attr & Attribute.ARCHIVE):
                i = i + 1
                # print(str(i) + '.   archive  \t', end = '')
                # print(child)
                print(f'{str(i):<8} | {"archive":<14} | {str(child.info.create_date).strip():<12} | {str(child.info.create_time).strip():<12} | {str(child.info.file_size):<9} | {str(child.name.strip()):<30}')
    
    def moveIntoDir(self):
        print('Folders in', self.curNode, ':')
        allDir = self.getDir()
        i = 0
        tmpMap = {}
        for child in allDir:
            if (child == self.curNode.parent):
                i = i + 1
                print(str(i) + ':\t/..')
                tmpMap[i] = child
                continue
            if (child.info.attr & Attribute.DIRECTORY):
                i = i + 1
                print(str(i) + ':\t/', end = '')
                print(child)
                tmpMap[i] = child
        print('Select folder to open: ', end = '')
        index = int(input())
        if (index <= 0 or index > i):
            print('Invalid index!')
            return
        self.curNode = tmpMap[index]
        print('Current working directory: ', str('/') + self.curNode.name)
    
    def readFile(self): # read txt
        print('Files in', self.curNode, ':')
        tmpMap = {}
        allDir = self.getDir()
        i = 0
        for child in allDir:
            if (child == None):
                continue
            if (child == self.curNode.parent):
                continue
            if (child == self.curNode):
                continue
            if (child.info.attr & Attribute.ARCHIVE):
                i = i + 1
                print(str(i) + ':\t', end = '')
                print(child)
                tmpMap[i] = child
        if (i == 0):
            print('No files in current working directory!')
            return
        print('Select file to print: ', end = '')
        index = int(input())
        if (index <= 0 or index > i):
            print('Invalid index!')
            return
        self.printFile(tmpMap[index])

    def dfs(self, dirList, curNode = None, index = 1):
        if (curNode == None):
            curNode = self.root
        if (index >= len(dirList)):
            return False
        curObjName = dirList[index].lower().strip()
        for obj in curNode.children:
            # print('type: ', type(curObjName), type(obj.name.lower().strip()))
            # if (str(obj.name.lower().strip(r'\x00')) == str(curObjName)):
            if (cmpStr(obj.name.lower().strip(), curObjName.lower().strip())):
                if (obj.info.attr == Attribute.ARCHIVE):
                    if (index == len(dirList) - 1):
                        return obj
                    else:
                        return False
                elif (obj.info.attr == Attribute.DIRECTORY):
                    if (index == len(dirList) - 1):
                        # print('is curnode', curNode.dir, ' ', curNode.name, ' ', curNode.isRoot)
                        self.curNode = obj
                        return True
                    return self.dfs(dirList, obj, index + 1)
        return False
    
    def followDir(self, dir):
        dir = dir.replace('\\', '/')
        dirList = dir.split('/')
        val = self.dfs(dirList)
        return val

    def printFileFromDir(self, dir):
        val = self.followDir(dir)
        if (val == False or val == True):
            print('Invalid directory!')
        else:
            self.printFile(val)
    
    def gotoDir(self, dir):
        dir = dir.replace('\\', '/')
        dirList = dir.split('/')
        if (len(dirList) == 1):
            if (dirList[0] == self.name + ':'):
                self.curNode = self.root
                print('Current working directory: ', self.curNode.dir.strip('\\\\.\\'))
                return
            else:
                print('Invalid directory!')
                return
        val = self.followDir(dir)
        if (val == False):
            print('Invalid directory!')
        else:
            print('Current working directory: ', self.curNode.dir.strip('\\\\.\\'))
    
    def drawTree(self):
        self.draw_dir_tree(curNode = self.curNode)

def cmpStr(str_a, str_b):
    str_a.replace('\x00', '')
    str_a = '' . join(str_a.split('\x00'))
    str_b.replace('\x00', '')
    str_b = '' . join(str_b.split('\x00'))
    if (len(str_a) != len(str_b)):
        return False
    for i in range(0, len(str_a)):
        if (str_a[i] != str_b[i]):
            return False
    return True