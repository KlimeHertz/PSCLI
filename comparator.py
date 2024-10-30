import difflib
import re
import os
import errno, stat, shutil

class FileComparator:
    def __init__(self):
        self.linesToAddA = list()
        self.linesToAddB = list()
        self.linesToDeleteA = list()
        self.linesToDeleteB = list()
        self.diffrences = list()
        self.tabname = ""
        self.controller = None
        self.whiteSpace = re.compile(r'\s+')
        self.endCodeLine = re.compile(r'.*?[;\n]')
        self.leftDiffs = list()
        self.rightDiffs = list()
        self.rightChange = list()
    
    def compareTexts(self,leftText,rightText,tabname,controller):
        self.controller = controller
        if ".pplc" in tabname:
            tabname = tabname.rstrip(".pplc")        
                
        outLeft , outRight = [],[]
        for left , right in zip(*self.__alignSequences(self.__sentenciseImpro(leftText),self.__sentenciseImpro(rightText))):
            outLeft.append(left)
            outRight.append(right)            
            
        outRightString = '\n'.join(outRight)
        outLeftString = '\n'.join(outLeft)
        
        lines_a = outLeftString.splitlines(keepends=False)
        lines_b = outRightString.splitlines(keepends=False)
        
        max_length = max(len(lines_a), len(lines_b))
        lines_a.extend([''] * (max_length - len(lines_a)))
        lines_b.extend([''] * (max_length - len(lines_b)))
            
        self.controller.addNewTab.emit(tabname,outLeftString,outRightString)

        for i, (left_line, right_line) in enumerate(zip(lines_a, lines_b)):
            if left_line.strip() and not right_line.strip():
                self.leftDiffs.append(i)
                self.controller.highlightLine.emit("remove",i,tabname,True)
            elif not left_line.strip() and right_line.strip():
                self.rightDiffs.append(i)
                self.controller.highlightLine.emit("add",i,tabname,False)
            elif left_line.strip() and right_line.strip() and left_line != right_line:
                self.rightChange.append(i)
                self.controller.highlightLine.emit("change",i,tabname,False)
                self.controller.highlightLine.emit("change",i,tabname,True)
        
    
    def __alignSequences(self,left,right,fill=''):
        out_a, out_b = [], []
        seqmatcher = difflib.SequenceMatcher(a=left, b=right, autojunk=False)
        for tag, a0, a1, b0, b1 in seqmatcher.get_opcodes():
            delta = (a1 - a0) - (b1 - b0)
            out_a += left[a0:a1] + [fill] * max(-delta, 0)
            out_b += right[b0:b1] + [fill] * max(delta, 0)
        assert len(out_a) == len(out_b)
        return out_a, out_b
            
    
    def mergeTexts(self,leftText,rightText,tabname,projectpath):
        lines_a = leftText.splitlines(keepends=False)
        lines_b = rightText.splitlines(keepends=False)
        
        max_length = max(len(lines_a), len(lines_b))
        lines_a.extend([''] * (max_length - len(lines_a)))
        lines_b.extend([''] * (max_length - len(lines_b)))
        
        mergedTextList = list()
        try:
            with open(os.path.join(projectpath,tabname+'.pplc'),"w") as file:  
                for i, (left_line, right_line) in enumerate(zip(lines_a, lines_b)):
                    if left_line.strip() and not right_line.strip():
                        mergedTextList.append(left_line)
                        file.write(left_line+'\n')
                    elif left_line.strip() and right_line.strip() and left_line != right_line:
                        mergedTextList.append(left_line)
                        file.write(left_line+'\n')
                    else:
                        mergedTextList.append(right_line)
                        file.write(right_line+'\n')
        except:
            print(f"le chemin {projectpath} existe déja et sera suprimé.")
            #delete merge path                    
            #shutil.rmtree(projectpath, ignore_errors=False, onerror=handleRemoveReadonly)
            #self.mergeTexts(leftText=leftText,rightText=rightText,tabname=tabname,projectpath=projectpath)
        
        mergedText = ''.join(mergedTextList)            
        
        return mergedText
    
    def __insertJumpLine(self, string, index):
        return string[:index] + '\n' + string[index:]
    
    def __sentenciseImpro(self,code_text):
        sentences = []
        current_sentence = ''
        in_single_quote = False
        in_double_quote = False
        in_single_line_comment = False
        in_multi_line_comment = False

        # List of keywords that signify the end of a sentence
        ending_keywords = ['Then', 'Evaluate', 'For', 'While','Else']

        lines = code_text.splitlines(keepends=True)

        for line in lines:
            i = 0
            n = len(line)
            while i < n:
                char = line[i]
                next_char = line[i+1] if i+1 < n else ''

                if in_single_line_comment:
                    current_sentence += char
                    if char == '\n':
                        in_single_line_comment = False

                elif in_multi_line_comment:
                    current_sentence += char
                    if char == '*' and next_char == '/':
                        current_sentence += next_char
                        in_multi_line_comment = False
                        i += 1  # Skip the next character

                elif in_single_quote:
                    current_sentence += char
                    if char == '\\':
                        # Skip escaped character inside single quotes
                        i += 1
                        if i < n:
                            current_sentence += line[i]
                    elif char == "'":
                        in_single_quote = False

                elif in_double_quote:
                    current_sentence += char
                    if char == '\\':
                        # Skip escaped character inside double quotes
                        i += 1
                        if i < n:
                            current_sentence += line[i]
                    elif char == '"':
                        in_double_quote = False

                else:
                    if char == '/' and next_char == '/':
                        current_sentence += char + next_char
                        in_single_line_comment = True
                        i += 1  # Skip the next character
                    elif char == '/' and next_char == '*':
                        current_sentence += char + next_char
                        in_multi_line_comment = True
                        i += 1  # Skip the next character
                    elif char == "'":
                        in_single_quote = True
                        current_sentence += char
                    elif char == '"':
                        in_double_quote = True
                        current_sentence += char
                    elif char == ';':
                        current_sentence += char
                        sentences.append(current_sentence.strip())
                        current_sentence = ''
                    else:
                        current_sentence += char

                i += 1

            # At the end of the line, check for ending keywords
            if not (in_single_quote or in_double_quote or in_single_line_comment or in_multi_line_comment):
                # Remove any trailing comments for keyword checking
                code_part = line
                comment_pos = line.find('//')
                if comment_pos != -1:
                    code_part = line[:comment_pos]
                code_part = code_part.rstrip()

                # Check if the line ends with any of the ending keywords
                if any(code_part.endswith(keyword) for keyword in ending_keywords):
                    sentences.append(current_sentence.strip())
                    current_sentence = ''

        # Add any remaining code as the last sentence
        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        return sentences

#handler for windows deletion if read only dir 
def handleRemoveReadonly(func, path, exc):
  excvalue = exc[1]
  if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
      func(path)
  else:
      raise
  