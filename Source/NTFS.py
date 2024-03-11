from enum import Flag
import re
import datetime

# function to convert integer to time(UTC)
def convertToTime(val): 
    byteData = val.to_bytes(8, byteorder='little')

    filetime = int.from_bytes(byteData, byteorder='little')

    timestamp = (filetime / 10_000_000) - 11_644_473_600
    timestamp = int(timestamp)
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

class NTFS:
    def __init__(self, name):
        self.name = name
        self.ptr = open(f'\\\\.\\{self.name}:', 'rb')
        with open(f'\\\\.\\{self.name}:', 'rb') as f:
            self.BPB = BPB(self.ptr, self.name + ':')
    
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
            sectorText = sectorData.decode('utf-8')
            data += sectorText
        return data


    def readEntry(self):
        self.ptr.seek(self.BPB.MFT_start_sector * self.BPB.byte_per_sector)
        for i in range(0, self.BPB.number_of_sector, 2):
            # print('num sector: ', i, ' ', self.BPB.number_of_sector)
            data = self.ptr.read(1024) # 1024 bytes

            # check signature
            if (data[0:4] != b'FILE'):
                continue
            # get starting byte of attribute from header
            attrOffset = 20
            attrOffset = int.from_bytes(data[attrOffset:attrOffset + 2], byteorder='little')

            fileSize = 0
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
                
                # add offset to read next attribute
                attrOffset += attrLength
            if (fileSize > 0):
                print('file name: ', fileName)
                print('file size: ', fileSize)
                print('time created: ', createTime)
                print('last modified time: ', modifiedTime)
                print('last accessed time: ', accessedTime)
            if (fileName.lower().endswith('.txt')): 
                print('fileContent:\n', fileContent)
                # print(fileContent.decode('utf-8')) 



# offset = self.BPB.MFT_start_sector * self.BPB.sector_per_cluster * self.BPB.byte_per_sector
        
driveLetter = 'G'
my_NTFS = NTFS(driveLetter)
my_NTFS.get_info()
my_NTFS.readEntry()
# print(convertToTime(130381390209053668))