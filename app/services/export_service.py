# app/services/export_service.py
import pandas as pd
from io import BytesIO
from typing import List, Dict
import json
from datetime import datetime

class ExportService:
    
    @staticmethod
    def export_to_excel(data: List[Dict], filename: str = None) -> BytesIO:
        """Exportar datos a Excel"""
        if not filename:
            filename = f"usuarios_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # Formatear fechas si existen
        date_columns = ['created_date', 'last_logon']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Crear buffer en memoria
        buffer = BytesIO()
        
        # Escribir a Excel con formato
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Usuarios', index=False)
            
            # Obtener el workbook y worksheet para formato
            workbook = writer.book
            worksheet = writer.sheets['Usuarios']
            
            # Ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def export_to_csv(data: List[Dict]) -> str:
        """Exportar datos a CSV"""
        df = pd.DataFrame(data)
        return df.to_csv(index=False)
    
    @staticmethod
    def export_to_json(data: List[Dict]) -> str:
        """Exportar datos a JSON"""
        # Convertir datetime a string para JSON
        for item in data:
            for key, value in item.items():
                if isinstance(value, datetime):
                    item[key] = value.isoformat()
        
        return json.dumps(data, indent=2, ensure_ascii=False)