from enum import Flag
import re
import datetime

# function to convert integer to time(UTC)
def convertToTime(val): 
    byteData = val.to_bytes(8, byteorder='little')

    filetime = int.from_bytes(byteData, byteorder='little')

    timestamp = (filetime / 10_000_000) - 11_644_473_600
    timestamp = int(timestamp)
    timestamp += 60 * 60 * 7
    createTime = datetime.datetime.utcfromtimestamp(timestamp)

    return createTime

class Attribute(Flag):
    STANDARD_INFORMATION = 16
    FILE_NAME = 48
    DATA = 128
        
class BPB:
    def __init__(self, ptr, name):
        self.name = name
        self.ptr = ptr
        self.data = self.ptr.read(100)
        
        self.byte_per_sector = int.from_bytes(self.data[0x0b:0x0d], byteorder='little')
        self.sector_per_cluster = int.from_bytes(self.data[0x0d:0x0e], byteorder='little')
        self.sector_per_track = int.from_bytes(self.data[0x18:0x1a], byteorder='little')
        self.number_of_sector = int.from_bytes(self.data[0x28:0x30], byteorder='little')
        self.MFT_start_sector = self.sector_per_cluster * int.from_bytes(self.data[0x30:0x38], byteorder='little')
        self.MFT_reserve_start_cluster = self.sector_per_cluster * int.from_bytes(self.data[0x38:0x40], byteorder='little')

class FileDir:
    def __init__(self, name, size, createTime, modifiedTime, accessedTime, fileContent, filePermission, isFolder):
        self.name = name
        self.size = size
        self.createTime = createTime
        self.modifiedTime = modifiedTime
        self.accessedTime = accessedTime
        self.fileContent = fileContent
        self.filePermission = filePermission
        self.isFolder = isFolder
        
    def __str__(self):
        return f'name: {self.name}, size: {self.size}, createTime: {self.createTime}, modifiedTime: {self.modifiedTime}, accessedTime: {self.accessedTime}, fileContent: {self.fileContent}, filePermission: {self.filePermission}, isFolder: {self.isFolder}'
    
class Entry:
    def __init__(self, parDirectory, name = None, timeCreated = None, timeAccessed = None, timeModified = None, isFolder = False, fileContent = None):
        self.isFolder = isFolder
        self.name = name
        self.timeCreated = timeCreated
        self.timeAccessed = timeAccessed
        self.timeModified = timeModified
        self.parDir = parDirectory
        self.fileContent = fileContent

class Node:
    def __init__(self, entry = None, parent = None, address = None):
        self.entry = entry
        self.parent = parent
        self.children = []
        self.address = address
    
    def __str__(self):
        return self.entry.name

class NTFS:
    def __init__(self, name):
        self.name = name
        self.root = None
        self.curNode = None
        self.map = {}
        self.ptr = open(f'\\\\.\\{self.name}:', 'rb')
        with open(f'\\\\.\\{self.name}:', 'rb') as f:
            self.BPB = BPB(self.ptr, self.name + ':')
        self.readEntry()
    
    def get_info(self):
        print('sector_size: ', self.BPB.byte_per_sector)
        print('sector_per_cluster: ', self.BPB.sector_per_cluster)
        print('sector per track: ', self.BPB.sector_per_track)
        print('number_of_sector: ', self.BPB.number_of_sector)

    def clusterToSectorList(self, clusterList):
        sectorList = [] 
        for cluster in clusterList:
            sectorList.append(cluster * self.BPB.sector_per_cluster)
        return sectorList
    
    def readSectorChain(self, sectorList):
        data = ''
        for sectorIndex in sectorList:
            self.ptr.seek(sectorIndex * self.BPB.byte_per_sector)
            sectorData = self.ptr.read(self.BPB.byte_per_sector)
            sectorText = sectorData.decode('utf-8', errors = 'replace')
            data += sectorText
        return data


    def readEntry(self):
        self.ptr.seek(self.BPB.MFT_start_sector * self.BPB.byte_per_sector)
        for i in range(0, self.BPB.number_of_sector, 2):
            data = self.ptr.read(1024) # 1024 bytes

            # check signature
            if (data[0:4] != b'FILE'):
                continue

            fileFlag = int.from_bytes(data[0x16:0x18], byteorder='little')
            if not (fileFlag & 0x01):
                continue
            isFolder = 0
            if (fileFlag & 0x02):
                isFolder = 1
            elif ((fileFlag & 0x04) or (fileFlag & 0x08)):
                continue
            
            # get starting byte of attribute from header
            attrOffset = 20
            attrOffset = int.from_bytes(data[attrOffset:attrOffset + 2], byteorder='little')

            fileSize = 0
            
            flags = None
            while True:
                ## Attribute header
                # get attribute type
                attrType = int.from_bytes(data[attrOffset:attrOffset + 4], byteorder='little')
                # print('attributeType', int(attrType), ' ', Attribute.FILE_NAME.value, ' ', attrType == Attribute.FILE_NAME.value)

                # break if end of attribute
                if (attrType == 0xFFFFFFFF or attrType == 0x0):
                    break
                # get attribute length
                attrLength = int.from_bytes(data[attrOffset + 4:attrOffset + 8], byteorder='little')

                # get attribute type (resident/non-resident)
                attrResident = int.from_bytes(data[attrOffset + 8:attrOffset + 9], byteorder='little')
                isResident = True
                if (attrResident == 1): # non-resident
                    isResident = False
                if (attrResident > 1):
                    break
                # get content's size of the attribute
                attrContentSize = int.from_bytes(data[attrOffset + 16:attrOffset + 20], byteorder='little')
                # get attribute's content's offset 
                attrContentOffset = int.from_bytes(data[attrOffset + 20:attrOffset + 21], byteorder='little')

                ## Attribute content
                # attribute of type $FILE_NAME
                if (attrType == Attribute.FILE_NAME.value):
                    # get file name
                    nameLength = int.from_bytes(data[attrOffset + attrContentOffset + 64:attrOffset + attrContentOffset + 65], byteorder='little')
                    # fileName = int.from_bytes(data[attrOffset + attrContentOffset + 66:attrOffset + attrContentOffset + 66 + nameLength * 2], byteorder='little')
                    fileName = data[attrOffset + attrContentOffset + 66:attrOffset + attrContentOffset + 66 + nameLength * 2]
                    fileName = fileName.decode('utf-16le')
                    if (fileName.startswith('$')):
                        break
                    # get parent directory
                    parDir = int.from_bytes(data[attrOffset + attrContentOffset + 0:attrOffset + attrContentOffset + 6], byteorder='little')
                    parDir = hex(parDir)
                    # whatever this is
                    parDir2 = int.from_bytes(data[attrOffset + attrContentOffset + 6:attrOffset + attrContentOffset + 8], byteorder='little')
                    parDir2 = hex(parDir2)
                    # get file create time
                    createTime = int.from_bytes(data[attrOffset + attrContentOffset + 8:attrOffset + attrContentOffset + 16], byteorder='little')
                    createTime = convertToTime(createTime)
                    # get file last modified time 
                    modifiedTime = int.from_bytes(data[attrOffset + attrContentOffset + 16:attrOffset + attrContentOffset + 24], byteorder='little')
                    modifiedTime = convertToTime(modifiedTime)
                    # get file last accessed time 
                    accessedTime = int.from_bytes(data[attrOffset + attrContentOffset + 32:attrOffset + attrContentOffset + 40], byteorder='little')
                    accessedTime = convertToTime(accessedTime)

                # attribute of type $DATA
                elif (attrType == Attribute.DATA.value):
                    # in case resident attribute
                    if (isResident):
                        fileSize = attrContentSize
                        fileContent = data[attrOffset + attrContentOffset:attrOffset + attrContentOffset + fileSize]
                        fileContent = fileContent.decode('utf-8', errors = 'replace')
                        filePermission = data[attrOffset + attrContentOffset + 0x20:attrOffset + attrContentOffset + 0x2d]
                    # in case non-resident attribute
                    else:
                        dataRunOffset = int.from_bytes(data[attrOffset + 32:attrOffset + 34], byteorder='little')
                        fileSize = int.from_bytes(data[attrOffset + 48:attrOffset + 55], byteorder='little')
                        if fileName.lower().endswith('.txt'):
                            numberOfCluster = int.from_bytes(data[attrOffset + dataRunOffset + 1:attrOffset + dataRunOffset + 2], byteorder='little')
                            startClusterIndex = int.from_bytes(data[attrOffset + dataRunOffset + 2:attrOffset + dataRunOffset + 4], byteorder='little')
                            clusterList = []
                            for cluster in range(startClusterIndex, startClusterIndex + numberOfCluster):
                                clusterList.append(cluster)
                            sectorList = self.clusterToSectorList(clusterList)
                            # read data based on sector list to get file data
                            fileContent = self.readSectorChain(sectorList)
                elif (attrType == Attribute.STANDARD_INFORMATION.value):
                    # get flags
                    flags = int.from_bytes(data[attrOffset + attrContentOffset + 0x20:attrOffset + attrContentOffset + 0x20 + 4], byteorder='little')                   

                # add offset to read next attribute
                attrOffset += attrLength
            
            
            if (isFolder and fileName.strip() != '.'):
                if (flags != None):
                    if (flags & 0x02):
                        continue
                    if (flags & 0x04):
                        continue
            curEntry = None
            if (fileName.startswith('$')):
                continue
            curEntry = Entry(int(parDir, 16), fileName, createTime, accessedTime, modifiedTime, isFolder, fileContent)
            
            # Read .txt file
            # if (fileName.lower().endswith('.txt')): 
            #     print(fileContent.decode('utf-8'))

            self.map[i//2] = Node(entry = curEntry)

        for key, val in self.map.items():
            if (val.entry.parDir in self.map):
                val.parent = self.map[val.entry.parDir]
                self.map[val.entry.parDir].children.append(val)
            if (val.entry.name.strip() == '.'):
                self.root = val
                self.curNode = self.root

    
    def getDirTree(self, curNode = None, depth = 0):
        if (curNode == None):
            print(self.name + ':')
            curNode = self.root
        for child in curNode.children:
            if (child == curNode):
                continue
            for i in range(depth + 1):
                print('--', end = '')
            print(child.entry.name)
            if (child.entry.isFolder):
                self.getDirTree(curNode = child, depth = depth + 1)
    
    def getDir(self):
        allDir = []
        allDir.append(self.curNode.parent)
        for child in self.curNode.children:
            if (child == self.curNode):
                continue
            allDir.append(child)
        return allDir

    def listDir(self):
        print('Objects in', self.curNode, ':')
        allDir = self.getDir()
        for child in allDir:
            if (child == self.curNode.parent):
                print('\t/..')
                continue
            if (child.entry.isFolder):
                print('\t/', end = '')
            print(child)
    
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
            if (child.entry.isFolder):
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
        print('Current working directory: ', str('/') + self.curNode)
        
    def printFile(self, txtNode):
        # Read .txt file
        fileName = txtNode.entry.name
        fileContent = txtNode.entry.fileContent
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
        else
            
            
# offset = self.BPB.MFT_start_sector * self.BPB.sector_per_cluster * self.BPB.byte_per_sector
    
    def readFile(self):
        tmpMap = {}
        allDir = self.getDir()
        print('Files in', self.curNode, ':')
        for child in allDir:
            if not (child.entry.isFolder):
                i = i + 1
                print(str(i) + ':\t/', end = '')
                print(child)
                tmpMap[i] = child
        print('Select file to print: ', end = '')
        index = int(input())
        if (index <= 0 or index > i):
            print('Invalid index!')
            return
        self.printFile(tmpMap[index])
        
driveLetter = 'G'
my_NTFS = NTFS(driveLetter)
my_NTFS.getDirTree()
my_NTFS.listDir()
my_NTFS.moveIntoDir()
# print(convertToTime(130381390209053668))