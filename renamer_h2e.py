import re
import pandas as pd
from nameFinder import *

class renamer_h2e():  
    _num_search = "(?:(?<={1}{0})|(?<={2}{0})|(?<={1})|(?<={2}))\d{{1,2}}" # regexp for S and E
    _num_search2 = "(?:(?<={1}{0})|(?<={2}{0})|(?<={3}{0})|(?<={1})|(?<={2})|(?<={3}))\d{{1,2}}" # regexp for S and E
    in_sep = "[ _.:]"
    in_sep_dup = in_sep + "+"
    out_sep = "."
    video_fmt = ['.mkv','.avi','.mp4']
    
    def __init__(self,xls_path):
        self.heb_xls_path = xls_path[0]
        self.eng_xls_path = xls_path[1]
        df1 = pd.read_excel(self.heb_xls_path, sheet_name = 0)
        df2 = pd.read_excel(self.eng_xls_path, sheet_name = 0) 
        sep_rep = lambda x:re.sub(renamer_h2e.in_sep,renamer_h2e.out_sep,x)
        self.heb2eng_Names = [list(map(sep_rep,list(df1['heb']))), list(map(sep_rep,list(df1['eng'])))]
        self.eng2eng_Names = [list(map(sep_rep,list(df2['eng_from']))), list(map(sep_rep,list(df2['eng_to'])))]
        self.last_series = ""
        self.movie_name = movie_finder()
        self.series_name = series_finder()
        
    def sheb_name2array(self,name): # series - name to array of words
        name = re.sub("(זירה.מדיה.)|(לולו.סרטים.)|(ז.מ.)|(נ.מ.)","",name) # remove starting text
        name = re.search('^.+?(?:(?=.ע\d+פ\d+)|(?=$))',name).group()
        name_array = name.split('.') # create array from name
        to_filter = re.compile('(?!מדובב)^[א-ת0-9\-\']{2,}$') # only hebrew words
        name_array = list(map(lambda x: x.group(),filter(None,map(to_filter.search,name_array))))
        to_filter = re.compile('^([א-ת\-][0-9]){1,2}$') # season and episodes
        name_array = [i for i in name_array if not to_filter.search(i)] # Removing element from a list 
        return name_array
    
    def mheb_name2array(self,name): # movie - name to array of words
        name = re.sub("(זירה.מדיה.)|(לולו.סרטים.)|(ז.מ.)|(נ.מ.)","",name) # remove starting text
        name_array = name.split('.') # create array from name
        to_filter = re.compile('(?!מדובב)^[א-ת0-9\-\']+$') # only hebrew words
        name_array = list(map(lambda x: x.group(),filter(None,map(to_filter.search,name_array))))
        return name_array
    
    # get eng name and return formal eng name and folder name(skip on movie)
    def eng2eng(self,name,isHeb):
        in_sep_dup = renamer_h2e.in_sep_dup
        out_sep = renamer_h2e.out_sep
        if not(isHeb):
            s = re.search(".?(?:s|season).?\d{1,2}.?(?:e|episode).?\d{1,2}.*", name, re.IGNORECASE)
            if s: # is series
                e2e = self.eng2eng_Names
                fname = name[:s.span()[0]] # take only name of series
                idx =  [i for i,iname in enumerate(e2e[0]) if iname.casefold() == fname.casefold()] # find name in table
                if idx: # if name exist in table
                    idx = idx[0]
                    if e2e[1][idx]: # not empty
                        fname = e2e[1][idx]
                        sname = fname + s.group()
                    else:
                        sname = name
                else:
                    e2e[0].append(re.sub(in_sep_dup,out_sep,fname)) # from
                    res = self.series_name.search_eng_name(fname) # find on web
                    if res: # if find on web
                        fname = re.sub(in_sep_dup,out_sep,res[0])
                        sname = fname + s.group()
                        e2e[1].append(re.sub(in_sep_dup,out_sep,fname)) # to
                    else:
                        sname = name
                        e2e[1].append(re.sub(in_sep_dup,out_sep,'')) # to
            else: # is movie
                sname = fname = name
            return bool(s), sname, fname
        
    # update series table names
    def update_table(self):
        # heb 2 eng
        dict = {'heb':self.heb2eng_Names[0],
                'eng':self.heb2eng_Names[1]}
        df = pd.DataFrame(dict)
        df.to_excel(self.heb_xls_path,index=False)
        
        # eng 2 eng
        dict = {'eng_from':self.eng2eng_Names[0],
                'eng_to':self.eng2eng_Names[1]}
        df = pd.DataFrame(dict)
        df = df[df['eng_to']!=''] # remove empty rows
        df.to_excel(self.eng_xls_path,index=False)
        
        print('Excel is Updeted')

    # get heb series file name and return eng name with S and E (from table)
    def heb2eng_series_file(self, iFile):
        hebNames = self.heb2eng_Names[0]
        engNames = self.heb2eng_Names[1]
        num_search = renamer_h2e._num_search
        in_sep = renamer_h2e.in_sep
        idx =  [i for i,iname in enumerate(hebNames) if iname in iFile]
        if idx:
            idx = idx[0]
            fn = [engNames[idx].replace(' ','.')]
            
            ### Season & Episode ###
            num = re.split(hebNames[idx], iFile)[1] # split the name and take after for S and E
            try:
                s = re.search(num_search.format(in_sep,'עונה','ע'), num).group()
            except:
                s = re.findall('\d',num)[0]
            fn.append('S' + s.zfill(2))
            try:
                e = re.search(num_search.format(in_sep,'פרק','פ'), num).group()
            except:
                e = re.findall('\d',num)[1]
            fn.append('E' + e.zfill(2))
        else:
            return False
            
        return fn
    
    # get heb series text name and return eng name in file format
    def heb2eng_series(self, ifn):
        in_sep_dup = renamer_h2e.in_sep_dup
        out_sep = renamer_h2e.out_sep
        name_eng = self.heb2eng_series_file(ifn)
        if not(name_eng) and self.use_web_for_series: # can't find series and Enb Web
            name = self.series_name.search_eng_name(self.sheb_name2array(ifn))
            if name: # find the series in Web
                [name_eng, name_heb] = name
                for iName in name_heb:
                    self.heb2eng_Names[0].append(re.sub(in_sep_dup,out_sep,iName))
                    self.heb2eng_Names[1].append(re.sub(in_sep_dup,out_sep,name_eng.replace("'","")))
                name_eng = self.heb2eng_series_file(ifn)
                return name_eng
            else:
                return False
        else: # series found
            return name_eng

    def heb2eng_movies(self,ifn): # send movie name to search on web
        name_eng = self.movie_name.search_eng_name(self.mheb_name2array(ifn))
        if name_eng:
            return [re.sub(renamer_h2e.in_sep_dup,renamer_h2e.out_sep,name_eng.replace("'",""))]
        else:
            return False

    def hebrew2eng(self,ifn): # get full heb name retun eng name
        in_sep = renamer_h2e.in_sep
        out_sep = renamer_h2e.out_sep
        
        s = re.search(renamer_h2e._num_search2.format(in_sep,'עונה','ע','-'), ifn)
        
        ### Name ###
        if s: # Series (include Season and Episode)
            name_eng = self.heb2eng_series(ifn)
        else: # Movies
            name_eng = self.heb2eng_movies(ifn)
        fn = name_eng
        
        if not(fn):
            return False
        
        year = re.compile("(19|20)\d{2}(?=\D)?")
        q = re.compile("(?<={0})?\d+p(?={0}?)".format(in_sep), re.IGNORECASE) # qulity: 480p/720p/1080p....
        cd1 = re.compile(r"(?<={0})cd\d".format(in_sep),re.IGNORECASE)
        cd2 = re.compile(r"((?<={0}\())\d".format(in_sep))
        frmt = re.compile("(?<={0})?[a-z].*[a-z](?={0}?)".format(in_sep),re.IGNORECASE) # video format (all the rest in eng)
        
        re_array = [year, q, cd1, frmt]
        fn2 = [None] * len(re_array)
        for i in range(len(re_array)):
            i_search = re_array[i]
            res = i_search.search(ifn)
            if res:
                res = res.group()
                fn2[i] = res
                ifn = re.sub(res,"",ifn)
        
        fn2[-1], fn2[-2] = fn2[-2], fn2[-1] # move CD to be last
        if not(fn2[-1]): # check if CD is in ()
            res = cd2.search(ifn)
            if res:
                res = res.group()
                fn2[-1] = "CD" + res
                self.last_series = fn
            elif self.last_series == fn:
                fn2[-1] = "CD1"
                
        fn2 = list(filter(None, fn2)) # remove empty cell
        fn_out = fn + fn2 # concatenate list               
                
        return out_sep.join(fn_out),fn[0],bool(s)
        
                     
                                
def main():
    pass
                
if __name__ == "__main__":
    main()       