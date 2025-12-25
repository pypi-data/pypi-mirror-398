from io import BytesIO

from openpyxl import load_workbook

from .base_sheet_processor import BaseSheetProcessor


class XlsProcessor:

    def __init__(self, file: str | bytes):
        self.file = file
        self.wb = load_workbook(BytesIO(self.file))

    def get_data(self, sheet_processor: BaseSheetProcessor):
        return sheet_processor.get_data(self.wb)

    def validate(self, sheet_processor: BaseSheetProcessor):
        return sheet_processor.validate(self.wb)

    def validate_many(self, sheet_processors: list[BaseSheetProcessor]):
        errors = {}
        for sheet_processor in sheet_processors:
            error = self.validate(sheet_processor)
            if error:
                errors.update(error)

        return errors or None
