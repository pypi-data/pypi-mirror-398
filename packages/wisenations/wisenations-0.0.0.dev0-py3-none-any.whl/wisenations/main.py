import re
from typing import Iterable, Any
from pprint import pprint
from .utils import Sheet
from dataclasses import dataclass

@dataclass
class SheetManager:
    def __init__(self) -> None:
        self.sheets = {}

    def get_sheet(self, id: str) -> Sheet:
        return self.sheets.get(id)
    
    def get_all_sheets(self):
        return self.sheets.items()
   
    def new_sheet(self, id: str) -> None:
        self.sheets.update({id: Sheet()})
    
    def del_sheet(self, id: str) -> None:
        self.sheets.pop(id)
    
if __name__ == "__main__":
    pass