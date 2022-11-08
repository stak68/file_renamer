import csv
import os
import re
from pathlib import Path
import shutil
from renamer_h2e import *

def main():
    # Parameters
    path_scan = r"C:\input" 
    path_save = r"C:\output"
    # path_scan = r"C:\Users\neria\Downloads\pyTest1"
    # path_save = r"C:\Users\neria\Downloads\pyTest2"
    
    # Const 
    xl_series = ['HebEngDict.xlsx', 'EngEngDict.xlsx']
    renamer = renamer_h2e(xl_series)
    renamer.use_web_for_movie = 1
    renamer.use_web_for_series = 1
    
    in_sep = renamer_h2e.in_sep
    in_sep_dup = renamer_h2e.in_sep_dup
    f = open("Failed_File.txt", "w",encoding='utf-8-sig')
    with open('File_List.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["source Path", "source File", "Dest File", "Dest Path"])
        
    # recursive folder scan
    for root,d_names,f_names in os.walk(path_scan): 
        for iFile in f_names:
            split_fn = os.path.splitext(iFile) # split file name , ext
            ifn = re.sub(in_sep_dup,renamer_h2e.out_sep,split_fn[0])
            ext = split_fn[1]
            if not (ext in renamer_h2e. video_fmt): # not a video
                continue
            isHeb = re.search("[א-ת]",ifn) # contains hebrew
            if isHeb:
                fn = renamer.hebrew2eng(ifn)
                if not(fn): # can't find a match
                    print("XXX ERROR: " + ifn + ", not match has been found. XXX\n")
                    f.write(iFile + "\n")
                    continue
                folder_name = fn[1]
                is_series = fn[2]
                fn = fn[0] +  ext
            else: # english name
                [is_series, ifn,folder_name] = renamer.eng2eng(ifn,isHeb)
                fn = ifn +  ext
            fn = re.sub(r'{0}(\d+)(?={0}.*\b\1\b)'.format(in_sep),'',fn) # remove duplicates words
            if is_series:
                iPath_save = os.path.join(path_save,'Series',folder_name)
            else:
                iPath_save = os.path.join(path_save,'Movies')
            Path(iPath_save).mkdir(parents=True, exist_ok=True)
            iName_save = os.path.join(iPath_save,fn)
            print(os.path.join(root,iFile) + " -> " + iName_save)
            with open('File_List.csv', 'a', encoding='utf-8-sig' , newline='') as file:
                writer = csv.writer(file)
                writer.writerow([root, iFile, fn , iPath_save])
            if root[0] == iPath_save[0]:
                try:
                    os.rename(os.path.join(root,iFile), os.path.join(iPath_save,fn))
                except FileExistsError:
                    shutil.move(os.path.join(root,iFile), os.path.join(iPath_save,fn))
            else: 
                shutil.move(os.path.join(root,iFile), os.path.join(iPath_save,fn))
    f.close() 
    renamer.update_table();
    # input('Press Enter...')
    print('*** Done ***')

if __name__ == "__main__":
    main()

