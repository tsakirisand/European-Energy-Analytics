import datetime
import io
import pandas as pd
from typing import Dict, Any, Tuple

class DataExporter:
    """Export filtered energy analytics datasets into CSV and Excel formats with metadata."""

    @staticmethod
    def export_to_csv(df: pd.DataFrame, metadata: Dict[str, Any] = None) -> str:
        """Generate CSV string with provenance header comments."""
        output = io.StringIO()
        output.write("# ==================================================\n")
        output.write("# EUROPEAN ENERGY ANALYTICS — DATA EXPORT\n")
        output.write(f"# Exported At: {datetime.datetime.utcnow().isoformat()}\n")
        output.write("# Source: Eurostat Official Dissemination API\n")
        if metadata:
            for k, v in metadata.items():
                output.write(f"# {k}: {v}\n")
        output.write("# ==================================================\n")
        
        df.to_csv(output, index=False)
        return output.getvalue()

    @staticmethod
    def export_to_excel(df: pd.DataFrame, sheet_name: str = "Energy Data", metadata: Dict[str, Any] = None) -> bytes:
        """Generate Excel workbook byte payload with metadata cover sheet."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Metadata sheet
            if metadata:
                meta_rows = [
                    {"Parameter": "Exported At", "Value": datetime.datetime.utcnow().isoformat()},
                    {"Parameter": "Source", "Value": "Eurostat Official Dissemination API"}
                ]
                for k, v in metadata.items():
                    meta_rows.append({"Parameter": k, "Value": str(v)})
                meta_df = pd.DataFrame(meta_rows)
                meta_df.to_excel(writer, sheet_name="Metadata", index=False)

            df.to_excel(writer, sheet_name=sheet_name, index=False)

        return output.getvalue()
