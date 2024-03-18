from NTFS import NTFS
from FAT32 import FAT32
import os
import psutil

def check_filesystem_type(drive_letter):
    partitions = psutil.disk_partitions(all=True)
    for partition in partitions:
        if partition.device.startswith(drive_letter):
            filesystem_type = partition.fstype
            return filesystem_type
    return None

def isFAT32(diskType):
    return diskType.strip() == 'FAT32'

def getUserQuery():
    print('Input command: ', end = '')
    query = input()
    if (query.isdecimal()):
        return int(query)
    else:
        return False

def invalidQuery():
    print('Invalid query!')

def helpQuery(query, disk, diskType):
    isF32 = isFAT32(diskType)
    if (query == 1):
        print('List of all commands:')
        print('1. List all command type')
        print('2. Print file content from working directory')
        print('3. Print file content from directory')
        print('4. Change to directory')
        print('5. Print volume information')
        print('6. List all files and folders in current working directory')
        print('7. Print the tree of working directory')
        print('8. Exit program')
        print('Type the number that corresponds to the command!')
    elif (query == 2):
        print('Input directory: ', end = '')
        dir = input()
        disk.printFileFromDir(dir)
    elif (query == 3):
        disk.readFile()
    elif (query == 4):
        print('Input directory: ', end = '')
        dir = input()
        disk.gotoDir(dir)
    elif (query == 5):
        disk.getVolumeInfo()
    elif (query == 6):
        disk.listDir()
    elif (query == 7):
        disk.drawTree()
    elif (query == 8):
        return False
        

if __name__ == "__main__":
    volume = [chr(x) for x in range(65, 91) if os.path.exists(chr(x) + ":")]
    print("Available volumes:")
    for i in range(len(volume)):
        print(f"{i + 1}/", volume[i] + ':')
    print("Choose volume: ", end = "")
    vol = int(input())
    if (vol <= 0 or vol > len(volume)):
        print("Invalid volume!")
        exit()
    vol = vol - 1
    driveLetter = volume[vol]
    print('driveLetter: ', driveLetter)
    fileSystem = check_filesystem_type(driveLetter)
    disk = None
    if (fileSystem.strip() == 'FAT32'):
        disk = FAT32(driveLetter)
        print(driveLetter, 'uses FAT32 file system.')
    elif (fileSystem.strip() == 'NTFS'):
        disk = NTFS(driveLetter)
        print(driveLetter, 'uses NTFS file system.')
    else:
        print("Unsupported file system!")
        exit()
    helpQuery(1, disk, fileSystem)
    while True:
        print('\n')
        query = getUserQuery()
        if (query == False):
            print('Invalid command!')
            helpQuery(1, disk, fileSystem)
            continue
        elif (query <= 0 or query > 8):
            print('Invalid command!')
            helpQuery(1, disk, fileSystem)
            continue
        val = helpQuery(query, disk, fileSystem)
        if (val == False):
            print('Program exitted! Thanks for using!')
            break