"""Generate a sample workbook for testing the MR400 Pro tracer."""
import pandas as pd

# Sample legacy requirements (children)
children_data = {
    "Requirement ID": [
        "REQ-001",
        "REQ-002",
        "REQ-003",
        "REQ-004",
        "REQ-005",
        "REQ-006",
        "REQ-007",
        "REQ-008",
    ],
    "Description": [
        "The user shall be able to view ECG waveform in real-time on the monitor display",
        "The monitor shall display SpO2 values with 1% resolution",
        "Alarm limits for heart rate shall be configurable by the clinical user",
        "The system shall support NIBP measurements in both manual and automatic modes",
        "Battery backup shall provide at least 2 hours of operation",
        "The monitor shall be MRI conditional for use in Zone 3",
        "Temperature probe readings shall be displayed in Celsius or Fahrenheit",
        "The user shall be able to pair the monitor with a remote display via wireless connection",
    ],
}

# Sample canonical user needs (parents)
parents_data = {
    "new_doors_id": [
        "CUN-ECG-001",
        "CUN-SPO2-001",
        "CUN-ALM-001",
        "CUN-NIBP-001",
        "CUN-PWR-001",
        "CUN-MRI-001",
        "CUN-TEMP-001",
        "CUN-CONN-001",
    ],
    "Title": [
        "ECG Monitoring",
        "SpO2 Monitoring",
        "Alarm Management",
        "NIBP Measurement",
        "Power Management",
        "MRI Safety",
        "Temperature Monitoring",
        "Wireless Connectivity",
    ],
    "User Requirement": [
        "As a clinical user, the monitor shall display electrocardiogram signals continuously with QRS detection",
        "The monitor shall measure and display oxygen saturation with perfusion index",
        "The user shall configure alarm thresholds and acknowledge alarms per IEC 60601-1-8",
        "The system shall measure non-invasive blood pressure using oscillometric cuff method",
        "The monitor shall operate on AC power or battery with charge indication",
        "The device shall be safe for use in MRI environments up to Zone 3 at 1.5T",
        "The monitor shall measure patient temperature via probe with 0.1°C resolution",
        "The monitor shall support wireless pairing with PIC iX module for remote monitoring",
    ],
}

# Create DataFrames
children_df = pd.DataFrame(children_data)
parents_df = pd.DataFrame(parents_data)

# Write to Excel
output_file = "samples/sample_requirements.xlsx"
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    children_df.to_excel(writer, sheet_name="Combined URs", index=False)
    parents_df.to_excel(writer, sheet_name="Canonical_User_Needs", index=False)

print(f"✅ Created {output_file}")
print(f"   - Children: {len(children_df)} rows")
print(f"   - Parents: {len(parents_df)} rows")

