from openpyxl.workbook import Workbook
from rest_framework.exceptions import ValidationError

from ..models import ImportFile
from energy_base.translation import translate as _


class BaseSheetProcessor:
    sheet_index = 0

    def get_cell(self, wb: Workbook, cell: str):
        return wb.worksheets[self.sheet_index][cell] or 0

    def get_row(self, wb: Workbook, from_column: str, to_column: str):
        return [c[0].value or 0 for c in wb.worksheets[self.sheet_index][f"{from_column}:{to_column}"]]

    def get_column(self, wb: Workbook, from_column: str, to_column: str):
        return [c[0].value or 0 for c in wb.worksheets[self.sheet_index][f"{from_column}:{to_column}"]]

    def get_matrix(self, wb: Workbook, from_cell: str, to_cell: str):
        try:
            return [[c.value or 0 for c in r] for r in wb.worksheets[self.sheet_index][f"{from_cell}:{to_cell}"]]
        except:
            raise ValidationError(_('Wrong file was uploaded'), code='file')

    def _validate_matrix(self, wb: Workbook, from_cell: str, to_cell: str):
        errors = []
        data = self.get_matrix(wb, from_cell, to_cell)
        cell_code = from_cell
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                if not isinstance(cell, (float, int)):
                    error_cell = chr(ord(cell_code[0]) + j) + str(int(cell_code[1]) + i)
                    errors.append(f'{error_cell}')

        return errors

    def get_data(self, wb: Workbook) -> list:
        raise NotImplementedError

    def validate(self, wb: Workbook) -> dict | None:
        raise NotImplementedError

    def write_db(self, data: list, file: ImportFile, created_by: str) -> bool:
        raise NotImplementedError
