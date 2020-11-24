from ftplib import FTP_TLS
from cryptography.fernet import Fernet
import sys
import os
import nso_extraction_cutter.encryption.encryption as encryption
import time
import zipfile 



"""
    This class makes crawling the ftp server easier of superview.

    @author Michael de Winter
"""

satellite_size = "200cm"

def __logon():
    """
        Method for logging into the ftp server.

        @return the ftp connection.
    """
    ftps = FTP_TLS('ftp.satellietdataportaal.nl')

    ftps = FTP_TLS('ftp.satellietdataportaal.nl')
    ftps.login(user=encryption.decrypt_message(b'gAAAAABfcu0jGodTmtcPP2zl-VmEa6eIij1aenI2HDVqgdPVwTL_Au7g2bq8CPNEAoHwJJlXiRK34fEbq52LU0peFPqn5UsZ_Q==',os.getcwd()),\
            passwd=encryption.decrypt_message(b'gAAAAABfcu2eMNKRjxyrae6duxPC9YJpvFtdBywHE6klqtvUlZFu6HnKI0_BlCpi7-2_n0L0WGzkKttaXYqiYEy04mow-vOFLBZ-COtnA0El5V4myK-lVaQ=',os.getcwd()))
    ftps.prot_p()

    if satellite_size == "50cm":
        ftps.cwd('/Superview_1_4/SV_RD_11bit_RGBI_50cm')
    
    if satellite_size == "200cm":
        ftps.cwd('/Superview_1_4/SV_RD_11bit_RGBI_200cm')

    return ftps


def __attempt_conn_reset():
  """
    resets the FTP connection in case of a socket disconnect
    @param ftps: a ftp connection

  """
  # 
 
  # allow OS to release port
  time.sleep(2)
  ftps = FTP_TLS('ftp.satellietdataportaal.nl')
  ftps.login(user=encryption.decrypt_message(b'gAAAAABfcu0jGodTmtcPP2zl-VmEa6eIij1aenI2HDVqgdPVwTL_Au7g2bq8CPNEAoHwJJlXiRK34fEbq52LU0peFPqn5UsZ_Q==',scriptpath),\
           passwd=encryption.decrypt_message(b'gAAAAABfcu2eMNKRjxyrae6duxPC9YJpvFtdBywHE6klqtvUlZFu6HnKI0_BlCpi7-2_n0L0WGzkKttaXYqiYEy04mow-vOFLBZ-COtnA0El5V4myK-lVaQ=',scriptpath))
  ftps.prot_p()

  if satellite_size == "50cm":
    ftps.cwd('/Superview_1_4/SV_RD_11bit_RGBI_50cm')

  if satellite_size == "200cm":
    ftps.cwd('/Superview_1_4/SV_RD_11bit_RGBI_200cm')


  return ftps


def __ftp_crawler(aftps,item,placename):
    """
       A recursive method for crawling the ftp server of superview.

       @param aftp: A ftp connection.
       @param placename: a place name to look for. 
    """

    found_objects = []
    try:
        dir_list = aftps.nlst(item)
    except:
        aftps = __attempt_conn_reset()
        dir_list = aftps.nlst(item)
    if len(dir_list) > 1:
       for item in dir_list:     
        __ftp_crawler(aftps,item,placename )
    elif dir_list[0] is not None:
        if placename in dir_list[0]:
            found_objects.append(dir_list[0])
            print(dir_list[0])
            return(dir_list[0])

    return found_objects



def search_ftp(place_name, pixel_size = None):

    if pixel_size != None:
        satellite_size = pixel_size
    
    aftp = __logon()
    return __ftp_crawler(aftp,'',place_name)


def download_ftp_file(filename, Directory):

    aftp = __logon()
    with open(Directory, 'wb') as f:
        aftp.retrbinary('RETR ' + filename, f.write)

    with zipfile.ZipFile(Directory, 'r') as zip_ref:
        zip_ref.extractall(Directory.replace(".zip",""))
    
    os.remove(Directory)

    return 'Done'