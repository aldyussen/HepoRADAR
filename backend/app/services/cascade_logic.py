from typing import Any
from app.models.lab import Lab

def compute_reflex_flags(patient_labs: list[Lab]) -> list[dict[str, Any]]:
    """
    Computes reflex flags for a patient based on their labs.
    Rule HCV_RNA_MISSING:
    If anti_hcv is positive, but hcv_rna is missing, return a flag.
    """
    flags = []
    has_anti_hcv_pos = False
    has_hcv_rna = False
    
    for lab in patient_labs:
        analyte = (lab.analyte or "").upper()
        
        # Check ANTI_HCV
        if analyte == "ANTI_HCV" or "ANTI-HCV" in analyte or "HCV AB" in analyte or "HCV_AB" in analyte:
            val_str = str(lab.value).lower() if lab.value is not None else ""
            if val_str in ("1", "1.0", "positive", "pos", "+", "положит", "true") or (lab.value and float(lab.value) > 0):
                has_anti_hcv_pos = True
                
        # Check HCV_RNA
        if analyte == "HCV_RNA" or "HCV RNA" in analyte or "HCV-RNA" in analyte or "РНК" in analyte.upper():
            has_hcv_rna = True
            
    if has_anti_hcv_pos and not has_hcv_rna:
        flags.append({
            "type": "HCV_RNA_MISSING",
            "severity": "action",
            "msg": "Anti-HCV(+) без HCV-RNA — требуется дозаказ ПЦР для подтверждения ХВГ"
        })
        
    return flags
