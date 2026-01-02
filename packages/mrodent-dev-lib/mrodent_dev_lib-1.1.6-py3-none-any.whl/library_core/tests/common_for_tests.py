import re 
    
class AnyStringWithRegex(str):
    def __init__(self, case_insensitive=True):
        self.case_insensitive = case_insensitive
    def __eq__(self, other):
        if self.case_insensitive:
            return len(re.findall(self.lower(), other.lower(), re.DOTALL)) != 0
        return len(re.findall(self, other, re.DOTALL)) != 0
    
def is_match(pattern, string, flags=re.IGNORECASE | re.DOTALL): # or "is_full_match", as desired
    return re.fullmatch(pattern, string, flags)!=None
