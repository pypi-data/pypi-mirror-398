"""_summary_
This module heps developers to draw table using ascii charachters in console.
usage: 
        import Texttable 
        t = Texttable.Texttable(type='=',page-size=10)
        t.add_columns(['col1','col2','col3'])
        t.add_row(['data1','data2','data3'])
        print(t)
        t.print_with_pagination()
"""
import os

class Alignment:
    """_summary_
        This class is used for text alignment in table
    """
    center = '^'
    left = '<'
    right = '>'

class TextTable:
    """_summary_
        This class heps developers to draw table using ascii charachters in console.
        usage: 
            import Texttable 
            t = Texttable.Texttable(type='=',page-size=10)
            t.add_columns(['col1','col2','col3'])
            t.add_row(['data1','data2','data3'])
            print(t)
            t.print_with_pagination()   
    """
    def __init__(self,ttype='=',page_size=0):
        """_summary_

        Args:
            ttype (str, optional): _description_. Defaults to '='.
            this argument set table type:
              single line table(-)
              double line table(=)
              dashed table(+)
            page_size (int, optional): _description_. Defaults to 0.
            this parameter is set when programer wants to show data in multiple pages.
        """
        self.columns = []
        self.rows = []
        self.columnsw = []
        self.cell_align=[] # < > ^
        self.head_align = []
        self.page_size = page_size
        self.frame={'tl':'+','tm':'+','tr':'+',
                    'ml':'+','mm':'+','mr':'+',
                    'hl':'-','bl':'+','bm':'+',
                    'br':'+','vl':'|'}
        if ttype=='=':
            self.frame={'tl':'╔','tm':'╦','tr':'╗',
                        'ml':'╠','mm':'╬','mr':'╣',
                        'hl':'═','bl':'╚','bm':'╩',
                        'br':'╝','vl':'║'}        
        if ttype=='-':
            self.frame={'tl':'┌','tm':'┬','tr':'┐',
                        'ml':'├','mm':'┼','mr':'┤',
                        'hl':'─','bl':'└','bm':'┴',
                        'br':'┘','vl':'│'}
    def clear_screen(self):
        """_summary_
        this is an internal method to clear screen and used inside print_with_pagination method.
        """
        os.system('cls' if os.name == 'nt' else 'clear')

    def getch(self):
        """_summary_
        This method is a python implementation of getch() in C.
        Returns:
            _type_: _description_
            Byte
        """
        try:
            #First for windows 
            import msvcrt
            ch = msvcrt.getch()
            if ch == b'\xe0' or ch == b'\x00':  # Special keys
                ch2 = msvcrt.getch()
                return ch2#b'SPECIAL-' + ch2
            return ch
        except ImportError:
            import tty, termios,sys
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch == '\x1b':  # Start of escape sequence
                    ch2 = sys.stdin.read(2)  # Read next two bytes
                    return ch2#'ESC' + ch2
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

    def set_columns(self,cols):
        """_summary_
            input cols as a list of strings and set column title using it.
        Args:
            cols (_type_): _description_
            a list of strings that is the column headings.
        """
        colc = len(cols)
        self.columnsw = [0]*colc  # [11,4,9]      
        self.cell_align = [Alignment.left]*colc
        self.head_align = [Alignment.left]*colc
        self.columns = cols
        for i in range(colc):
            cw = len(cols[i])
            if cw > self.columnsw[i]:
                self.columnsw[i] = cw 

    def add_row(self,row):
        """_summary_
        This method add a row's cell data as a list and adds it to the table rows.
        Args:
            row (_type_): _description_
            list of stings
        """
        self.rows.append(row)
        i = 0
        for c in row:
            cw = len(c)
            if cw > self.columnsw[i]:
                self.columnsw[i] = cw
            i = i + 1

    def draw_row_tline(self):
        table_str = self.frame['tl']#"╔"
        for i in range(len(self.columns)-1):
            table_str += f"{self.frame['hl']*self.columnsw[i]}{self.frame['tm']}"
        table_str += f"{self.frame['hl']*self.columnsw[-1]}"    
        table_str += f"{self.frame['tr']}\n"
        return table_str 
    def draw_row_mline(self):
        table_str = self.frame['ml']#"╠"
        for i in range(len(self.columns)-1):
            table_str += f"{self.frame['hl']*self.columnsw[i]}{self.frame['mm']}"
        table_str += f"{self.frame['hl']*self.columnsw[-1]}"
        table_str += f"{self.frame['mr']}\n"
        return table_str 
    def draw_row_bline(self):
        table_str = self.frame['bl']#"╚"
        for i in range(len(self.columns)-1):
            table_str += f"{self.frame['hl']*self.columnsw[i]}{self.frame['bm']}"
        table_str += f"{self.frame['hl']*self.columnsw[-1]}"
        table_str += f"{self.frame['br']}\n"
        return table_str  
  
    def draw_row_content(self,row_content,is_head=False):
        table_str = ""
        i = 0
        for r in row_content:
            r = r[:self.columnsw[i]]
            al = self.head_align[i] if is_head else self.cell_align[i]
            table_str += f"{self.frame['vl']}{r:{al}{self.columnsw[i]}}"
            i = i + 1
        table_str += f"{self.frame['vl']}\n"
        return table_str
    def print_table(self,sr=0,er=0):
        table_str = ""
        #Drawing Table Header
        table_str = self.draw_row_tline()       
        table_str += self.draw_row_content(self.columns,True)
        table_str += self.draw_row_mline()
        #Drawing Table body
        if er == 0:
            er = len(self.rows)
        for i in range(sr,er):
            r = self.rows[i]
            table_str += self.draw_row_content(r)
        #Drawing Table footer
        table_str += self.draw_row_bline()
        #self.getch()
        return table_str
    def print_with_pagination(self,clear_page=True):
        tr = len(self.rows)
        if self.page_size == 0 or self.page_size>=tr:
            print(self.print_table(0,0),end='')
            print(f'Page:{1}/{1}, total rows:{tr}, <-Pre(2)  Next(1)-> end(0)')            
            self.getch()
            return
        er= min(self.page_size,tr)
        sr = 0
        tp = int(tr/self.page_size)
        cp =1
        pre_chars=(b'k',b'K',b'h',b'H',b'2')
        next_chars=(b'm',b'M',b'p',b'P',b'1')
        end_chars=(b'0',b'\r',b'\n',13,10)
        while sr< er:
            if clear_page:
                self.clear_screen()
            print(self.print_table(sr,er),end='')
            print(f'Page:{cp}/{tp}, total rows:{tr}, <-Pre(2)  Next(1)-> end(0)')            
            d = self.getch()
            if d in next_chars:
                cp +=1
                sr += self.page_size
                er = min(sr+self.page_size,tr)
            if d in pre_chars and cp>1:
                cp -=1
                sr -= self.page_size
                er = min(sr+self.page_size,tr)
            if d in end_chars:
                return
    def __str__(self):
        return self.print_table(0,0)
