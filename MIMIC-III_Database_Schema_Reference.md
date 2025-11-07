# MIMIC-III Database Schema Reference
## Complete Table and Column Documentation

**Database Version:** MIMIC-III v1.4  
**Data Period:** 2001-2012  
**Total Tables:** 26  
**Database Type:** Relational (PostgreSQL/BigQuery compatible)

---

## Table of Contents

### Patient Tracking Tables
1. [PATIENTS](#1-patients)
2. [ADMISSIONS](#2-admissions)
3. [ICUSTAYS](#3-icustays)
4. [CALLOUT](#4-callout)
5. [SERVICES](#5-services)
6. [TRANSFERS](#6-transfers)

### ICU Event Tables
7. [CAREGIVERS](#7-caregivers)
8. [CHARTEVENTS](#8-chartevents)
9. [DATETIMEEVENTS](#9-datetimeevents)
10. [INPUTEVENTS_CV](#10-inputevents_cv)
11. [INPUTEVENTS_MV](#11-inputevents_mv)
12. [OUTPUTEVENTS](#12-outputevents)
13. [PROCEDUREEVENTS_MV](#13-procedureevents_mv)
14. [NOTEEVENTS](#14-noteevents)

### Hospital System Tables
15. [LABEVENTS](#15-labevents)
16. [MICROBIOLOGYEVENTS](#16-microbiologyevents)
17. [PRESCRIPTIONS](#17-prescriptions)
18. [CPTEVENTS](#18-cptevents)
19. [DIAGNOSES_ICD](#19-diagnoses_icd)
20. [PROCEDURES_ICD](#20-procedures_icd)
21. [DRGCODES](#21-drgcodes)

### Dictionary Tables
22. [D_CPT](#22-d_cpt)
23. [D_ICD_DIAGNOSES](#23-d_icd_diagnoses)
24. [D_ICD_PROCEDURES](#24-d_icd_procedures)
25. [D_ITEMS](#25-d_items)
26. [D_LABITEMS](#26-d_labitems)

---

## Key Identifier Relationships

```
SUBJECT_ID (Patient) 
    ↓
HADM_ID (Hospital Admission)
    ↓
ICUSTAY_ID (ICU Stay)
```

- One `SUBJECT_ID` can have multiple `HADM_ID` (multiple hospitalizations)
- One `HADM_ID` can have multiple `ICUSTAY_ID` (multiple ICU stays per hospitalization)
- `ROW_ID` is a unique row identifier per table (not used for joins)

---

## 1. PATIENTS

**Purpose:** Defines each unique patient in the database  
**Rows:** 46,520  
**Links to:** All tables with SUBJECT_ID  
**Source:** CareVue and Metavision ICU databases

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | **Primary Key** - Unique patient identifier (one per patient) |
| GENDER | VARCHAR(5) | Patient gender ('M' or 'F') |
| DOB | TIMESTAMP | Date of birth (shifted for de-identification, >89 years set to 300 years before first admission) |
| DOD | TIMESTAMP | Date of death (merged from DOD_HOSP and DOD_SSN) |
| DOD_HOSP | TIMESTAMP | Date of death from hospital records |
| DOD_SSN | TIMESTAMP | Date of death from social security database |
| EXPIRE_FLAG | VARCHAR(5) | Binary flag indicating if patient died (whether DOD is null or not) |

**Key Notes:**
- DOB shifted for patients >89 years old (appears as ~300 years old)
- Median age of shifted patients: 91.4 years
- DOD prioritizes hospital records over SSN records

---

## 2. ADMISSIONS

**Purpose:** Defines each unique hospital admission  
**Rows:** 58,976  
**Links to:** PATIENTS (SUBJECT_ID)  
**Source:** Hospital admission/discharge/transfer (ADT) database

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | **Primary Key** - Unique hospital admission ID (100000-199999) |
| ADMITTIME | TIMESTAMP | Admission date and time |
| DISCHTIME | TIMESTAMP | Discharge date and time |
| DEATHTIME | TIMESTAMP | Time of in-hospital death (if applicable) |
| ADMISSION_TYPE | VARCHAR(50) | Type of admission (ELECTIVE, URGENT, EMERGENCY, etc.) |
| ADMISSION_LOCATION | VARCHAR(50) | Location from which patient was admitted |
| DISCHARGE_LOCATION | VARCHAR(50) | Location to which patient was discharged |
| INSURANCE | VARCHAR(255) | Insurance type (Medicare, Medicaid, Private, etc.) |
| LANGUAGE | VARCHAR(10) | Primary language |
| RELIGION | VARCHAR(50) | Religion |
| MARITAL_STATUS | VARCHAR(50) | Marital status |
| ETHNICITY | VARCHAR(200) | Ethnicity/race |
| EDREGTIME | TIMESTAMP | ED registration time (if applicable) |
| EDOUTTIME | TIMESTAMP | ED discharge time (if applicable) |
| DIAGNOSIS | VARCHAR(255) | Preliminary free-text diagnosis on admission |
| HOSPITAL_EXPIRE_FLAG | SMALLINT | Binary flag: 1 = died in hospital, 0 = survived to discharge |
| HAS_CHARTEVENTS_DATA | SMALLINT | Flag indicating if chartevents data exists |

**Key Notes:**
- HADM_ID range: 1000000-1999999
- Can have duplicate SUBJECT_ID (same patient, multiple admissions)
- DIAGNOSIS is preliminary/free-text; use DIAGNOSES_ICD for coded final diagnoses
- DEATHTIME usually equals DISCHTIME for deceased patients
- Demographics (insurance, language, ethnicity) can change between admissions

---

## 3. ICUSTAYS

**Purpose:** Defines each unique ICU stay  
**Rows:** 61,532  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID)  
**Source:** ICU databases (CareVue and Metavision)

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ICUSTAY_ID | INT | **Primary Key** - Unique ICU stay identifier (200000-299999) |
| DBSOURCE | VARCHAR(20) | ICU database source ('carevue' or 'metavision') |
| FIRST_CAREUNIT | VARCHAR(20) | First care unit for the ICU stay |
| LAST_CAREUNIT | VARCHAR(20) | Last care unit for the ICU stay |
| FIRST_WARDID | SMALLINT | Identifier for first ward |
| LAST_WARDID | SMALLINT | Identifier for last ward |
| INTIME | TIMESTAMP | ICU admission time |
| OUTTIME | TIMESTAMP | ICU discharge time |
| LOS | DOUBLE PRECISION | Length of stay in ICU (days) |

**Key Notes:**
- ICUSTAY_ID range: 200000-299999
- ICU stay is continuous if patient returns within 24 hours
- DBSOURCE indicates monitoring system (affects ITEMID ranges in events tables)

---

## 4. CALLOUT

**Purpose:** ICU discharge planning and execution data  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID)  
**Source:** Hospital administrative system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| SUBMIT_WARDID | INT | Ward where callout was submitted |
| SUBMIT_CAREUNIT | VARCHAR(15) | Care unit where callout was submitted |
| CURR_WARDID | INT | Current ward identifier |
| CURR_CAREUNIT | VARCHAR(15) | Current care unit |
| CALLOUT_WARDID | INT | Destination ward identifier |
| CALLOUT_SERVICE | VARCHAR(10) | Service accepting the patient |
| REQUEST_TELE | SMALLINT | Flag for telemetry request |
| REQUEST_RESP | SMALLINT | Flag for respiratory support request |
| REQUEST_CDIFF | SMALLINT | Flag for C. difficile isolation |
| REQUEST_MRSA | SMALLINT | Flag for MRSA isolation |
| REQUEST_VRE | SMALLINT | Flag for VRE isolation |
| CALLOUT_STATUS | VARCHAR(20) | Status of callout (Active, Inactive, Discharged) |
| CALLOUT_OUTCOME | VARCHAR(20) | Outcome of callout |
| DISCHARGE_WARDID | INT | Actual discharge ward |
| ACKNOWLEDGE_STATUS | VARCHAR(20) | Acknowledgment status |
| CREATETIME | TIMESTAMP | Time callout was created |
| UPDATETIME | TIMESTAMP | Time callout was last updated |
| ACKNOWLEDGETIME | TIMESTAMP | Time callout was acknowledged |
| OUTCOMETIME | TIMESTAMP | Time of callout outcome |
| FIRSTRESERVATIONTIME | TIMESTAMP | Time of first bed reservation |
| CURRENTRESERVATIONTIME | TIMESTAMP | Time of current bed reservation |

**Key Notes:**
- Tracks ICU discharge workflow
- Includes special precautions (MRSA, VRE, etc.)
- Shows delays between readiness and actual discharge

---

## 5. SERVICES

**Purpose:** Tracks clinical service assignments during hospital stay  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID)  
**Source:** Hospital database

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| TRANSFERTIME | TIMESTAMP | Time of service transfer |
| PREV_SERVICE | VARCHAR(20) | Previous service |
| CURR_SERVICE | VARCHAR(20) | Current service |

**Key Notes:**
- Tracks movement between clinical services (medicine, surgery, etc.)
- Multiple rows per admission indicate service transfers
- Services include: CMED, CSURG, DENT, ENT, GU, GYN, MED, NB, NBB, NMED, NSURG, OBS, ORTHO, OMED, OSURG, PSURG, PSYCH, SURG, TRAUM, TSURG, VSURG

---

## 6. TRANSFERS

**Purpose:** Tracks patient movement between locations in hospital  
**Rows:** ~261,897  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), ICUSTAYS (ICUSTAY_ID)  
**Source:** Hospital ADT database

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ICUSTAY_ID | INT | ICU stay identifier (if applicable) |
| DBSOURCE | VARCHAR(20) | Database source |
| EVENTTYPE | VARCHAR(20) | Event type (admit, transfer, discharge) |
| PREV_CAREUNIT | VARCHAR(20) | Previous care unit |
| CURR_CAREUNIT | VARCHAR(20) | Current care unit |
| PREV_WARDID | SMALLINT | Previous ward identifier |
| CURR_WARDID | SMALLINT | Current ward identifier |
| INTIME | TIMESTAMP | Time of transfer in |
| OUTTIME | TIMESTAMP | Time of transfer out |
| LOS | DOUBLE PRECISION | Length of stay in location (days) |

**Key Notes:**
- Multiple entries per patient showing all hospital movements
- Includes ICU admissions and discharges
- Ward IDs de-identified to protect patient privacy
- Care units include: CCU, CSRU, MICU, SICU, TSICU, etc.

---

## 7. CAREGIVERS

**Purpose:** De-identified list of caregivers who recorded data  
**Rows:** 7,567  
**Links to:** Multiple events tables via CGID  
**Source:** ICU databases

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| CGID | INT | **Primary Key** - Caregiver identifier |
| LABEL | VARCHAR(15) | Caregiver label/description |
| DESCRIPTION | VARCHAR(30) | Caregiver type description |

**Key Notes:**
- De-identified caregiver identifiers
- Used to track who recorded observations
- Labels indicate role (e.g., RN for Registered Nurse)

---

## 8. CHARTEVENTS

**Purpose:** All charted observations for patients  
**Rows:** ~330 million  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), ICUSTAYS (ICUSTAY_ID), D_ITEMS (ITEMID), CAREGIVERS (CGID)  
**Source:** ICU databases (CareVue and Metavision)

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ICUSTAY_ID | INT | ICU stay identifier |
| ITEMID | INT | Measurement type identifier (links to D_ITEMS) |
| CHARTTIME | TIMESTAMP | Time observation was made |
| STORETIME | TIMESTAMP | Time observation was recorded in system |
| CGID | BIGINT | Caregiver identifier |
| VALUE | VARCHAR(255) | Observed value |
| VALUENUM | DOUBLE PRECISION | Numeric value (if applicable) |
| VALUEUOM | VARCHAR(50) | Unit of measurement |
| WARNING | INT | Metavision: warning flag |
| ERROR | INT | Metavision: error flag |
| RESULTSTATUS | VARCHAR(50) | CareVue: result status (Manual/Automatic) |
| STOPPED | VARCHAR(50) | CareVue: whether measurement was stopped |

**Key Notes:**
- Largest table (~330M rows)
- Contains vital signs, assessments, scores
- ITEMID ranges: <220000 for CareVue, ≥220000 for Metavision
- LABEVENTS is ground truth when duplicates exist
- Text data from Metavision pick-lists included (v1.4+)

---

## 9. DATETIMEEVENTS

**Purpose:** Date/time observations (line insertions, dialysis times, etc.)  
**Rows:** ~4.5 million  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), ICUSTAYS (ICUSTAY_ID), D_ITEMS (ITEMID), CAREGIVERS (CGID)  
**Source:** ICU databases

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ICUSTAY_ID | INT | ICU stay identifier |
| ITEMID | INT | Event type identifier |
| CHARTTIME | TIMESTAMP | Time observation was charted |
| STORETIME | TIMESTAMP | Time observation was stored |
| CGID | BIGINT | Caregiver identifier |
| VALUE | TIMESTAMP | Date/time value recorded |
| VALUEUOM | VARCHAR(50) | Unit of measurement |
| WARNING | SMALLINT | Metavision warning flag |
| ERROR | SMALLINT | Metavision error flag |
| RESULTSTATUS | VARCHAR(50) | CareVue result status |
| STOPPED | VARCHAR(50) | CareVue stopped status |

**Key Notes:**
- Records events as timestamps (not measurements)
- Examples: dialysis start time, line insertion time

---

## 10. INPUTEVENTS_CV

**Purpose:** Intake data for CareVue patients  
**Rows:** ~17.5 million  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), ICUSTAYS (ICUSTAY_ID), D_ITEMS (ITEMID), CAREGIVERS (CGID)  
**Source:** CareVue ICU database

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ICUSTAY_ID | INT | ICU stay identifier |
| CHARTTIME | TIMESTAMP | Time input was charted |
| ITEMID | INT | Input item identifier (<30000 for CareVue) |
| AMOUNT | DOUBLE PRECISION | Amount administered |
| AMOUNTUOM | VARCHAR(30) | Amount unit of measurement |
| RATE | DOUBLE PRECISION | Rate of administration |
| RATEUOM | VARCHAR(30) | Rate unit of measurement |
| STORETIME | TIMESTAMP | Time observation was stored |
| CGID | BIGINT | Caregiver identifier |
| ORDERID | INT | Order identifier |
| LINKORDERID | INT | Linked order identifier |
| STOPPED | VARCHAR(30) | Status if input was stopped |
| NEWBOTTLE | INT | Flag for new bottle/bag |
| ORIGINALAMOUNT | DOUBLE PRECISION | Original amount in container |
| ORIGINALAMOUNTUOM | VARCHAR(30) | Original amount UOM |
| ORIGINALROUTE | VARCHAR(30) | Original administration route |
| ORIGINALRATE | DOUBLE PRECISION | Original rate |
| ORIGINALRATEUOM | VARCHAR(30) | Original rate UOM |
| ORIGINALSITE | VARCHAR(30) | Original administration site |

**Key Notes:**
- CareVue system only (ITEMID < 30000)
- Includes IV fluids, medications, nutrition
- Boluses show ENDTIME = STARTTIME + 1 minute

---

## 11. INPUTEVENTS_MV

**Purpose:** Intake data for Metavision patients  
**Rows:** ~3.6 million  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), ICUSTAYS (ICUSTAY_ID), D_ITEMS (ITEMID), CAREGIVERS (CGID)  
**Source:** Metavision ICU database

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ICUSTAY_ID | INT | ICU stay identifier |
| STARTTIME | TIMESTAMP | Start time of input event |
| ENDTIME | TIMESTAMP | End time of input event |
| ITEMID | INT | Input item identifier (≥220000 for Metavision) |
| AMOUNT | DOUBLE PRECISION | Amount administered |
| AMOUNTUOM | VARCHAR(30) | Amount unit of measurement |
| RATE | DOUBLE PRECISION | Rate of administration |
| RATEUOM | VARCHAR(30) | Rate unit of measurement |
| STORETIME | TIMESTAMP | Time observation was stored |
| CGID | BIGINT | Caregiver identifier |
| ORDERID | BIGINT | Order identifier |
| LINKORDERID | BIGINT | Linked order identifier |
| ORDERCATEGORYNAME | VARCHAR(100) | Order category |
| SECONDARYORDERCATEGORYNAME | VARCHAR(100) | Secondary order category |
| ORDERCOMPONENTTYPEDESCRIPTION | VARCHAR(200) | Order component type |
| ORDERCATEGORYDESCRIPTION | VARCHAR(50) | Order category description |
| PATIENTWEIGHT | DOUBLE PRECISION | Patient weight at time of order |
| TOTALAMOUNT | DOUBLE PRECISION | Total amount |
| TOTALAMOUNTUOM | VARCHAR(50) | Total amount UOM |
| ISOPENBAG | SMALLINT | Flag for open bag system |
| CONTINUEINNEXTDEPT | SMALLINT | Flag if continued after transfer |
| CANCELREASON | SMALLINT | Reason for cancellation |
| STATUSDESCRIPTION | VARCHAR(30) | Status description |
| COMMENTS_EDITEDBY | VARCHAR(30) | Editor of comments |
| COMMENTS_CANCELEDBY | VARCHAR(30) | Who canceled |
| COMMENTS_DATE | TIMESTAMP | Comment/edit date |
| ORIGINALAMOUNT | DOUBLE PRECISION | Original amount |
| ORIGINALRATE | DOUBLE PRECISION | Original rate |

**Key Notes:**
- Metavision system only (ITEMID ≥ 220000)
- More detailed order information than CareVue
- Boluses: ENDTIME = STARTTIME + 1 minute

---

## 12. OUTPUTEVENTS

**Purpose:** Output data for patients (urine, drains, etc.)  
**Rows:** ~4.3 million  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), ICUSTAYS (ICUSTAY_ID), D_ITEMS (ITEMID), CAREGIVERS (CGID)  
**Source:** ICU databases

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ICUSTAY_ID | INT | ICU stay identifier |
| CHARTTIME | TIMESTAMP | Time output was charted |
| ITEMID | INT | Output item identifier |
| VALUE | DOUBLE PRECISION | Output volume |
| VALUEUOM | VARCHAR(30) | Unit of measurement (usually mL) |
| STORETIME | TIMESTAMP | Time stored in system |
| CGID | BIGINT | Caregiver identifier |
| STOPPED | VARCHAR(30) | Status if collection stopped |
| NEWBOTTLE | CHAR(1) | New collection container flag |
| ISERROR | INT | Error flag |

**Key Notes:**
- No start time - CHARTTIME is when volume was recorded
- VALUE contains output volume
- VALUEUOM typically in mL

---

## 13. PROCEDUREEVENTS_MV

**Purpose:** Patient procedures for Metavision patients  
**Rows:** ~258,066  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), ICUSTAYS (ICUSTAY_ID), D_ITEMS (ITEMID), CAREGIVERS (CGID)  
**Source:** Metavision ICU database

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ICUSTAY_ID | INT | ICU stay identifier |
| STARTTIME | TIMESTAMP | Procedure start time |
| ENDTIME | TIMESTAMP | Procedure end time |
| ITEMID | INT | Procedure identifier |
| VALUE | DOUBLE PRECISION | Procedure value |
| VALUEUOM | VARCHAR(30) | Value unit of measurement |
| LOCATION | VARCHAR(30) | Procedure location |
| LOCATIONCATEGORY | VARCHAR(30) | Location category |
| STORETIME | TIMESTAMP | Time stored |
| CGID | BIGINT | Caregiver identifier |
| ORDERID | BIGINT | Order identifier |
| LINKORDERID | BIGINT | Linked order identifier |
| ORDERCATEGORYNAME | VARCHAR(100) | Order category |
| SECONDARYORDERCATEGORYNAME | VARCHAR(100) | Secondary category |
| ORDERCATEGORYDESCRIPTION | VARCHAR(50) | Category description |
| ISOPENBAG | SMALLINT | Open bag flag |
| CONTINUEINNEXTDEPT | SMALLINT | Continue after transfer flag |
| CANCELREASON | SMALLINT | Cancellation reason |
| STATUSDESCRIPTION | VARCHAR(30) | Status |
| COMMENTS_EDITEDBY | VARCHAR(30) | Editor |
| COMMENTS_CANCELEDBY | VARCHAR(30) | Canceler |
| COMMENTS_DATE | TIMESTAMP | Comment date |

**Key Notes:**
- Metavision only (no CareVue equivalent)
- Tracks procedures performed in ICU
- Examples: ventilation, dialysis, line placements

---

## 14. NOTEEVENTS

**Purpose:** De-identified clinical notes  
**Rows:** 2,083,180  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), CAREGIVERS (CGID)  
**Source:** Hospital database

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| CHARTDATE | TIMESTAMP | Date note was charted |
| CHARTTIME | TIMESTAMP | Time note was charted (if available) |
| STORETIME | TIMESTAMP | Time note was stored |
| CATEGORY | VARCHAR(50) | Note category |
| DESCRIPTION | VARCHAR(255) | Note type description |
| CGID | BIGINT | Caregiver identifier |
| ISERROR | CHAR(1) | Error flag |
| TEXT | TEXT | De-identified note text |

**Key Notes:**
- TEXT often very large with many newlines
- Categories: Discharge summary, Nursing, Physician notes, ECG, Echo, Radiology
- Available for inpatient and outpatient encounters
- CHARTTIME available for most notes except some ECG/Echo reports
- Addendums marked with description 'Addendum' (category still 'Discharge summary')

---

## 15. LABEVENTS

**Purpose:** Laboratory measurements  
**Rows:** ~27 million  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), D_LABITEMS (ITEMID)  
**Source:** Hospital laboratory system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ITEMID | INT | Lab test identifier (links to D_LABITEMS) |
| CHARTTIME | TIMESTAMP | Time specimen was charted |
| VALUE | VARCHAR(200) | Lab result value |
| VALUENUM | DOUBLE PRECISION | Numeric lab result |
| VALUEUOM | VARCHAR(20) | Unit of measurement |
| FLAG | VARCHAR(20) | Abnormal flag (normal, abnormal, delta) |

**Key Notes:**
- Ground truth for lab values (overrides CHARTEVENTS if duplicate)
- ITEMID distinct from D_ITEMS (uses D_LABITEMS)
- Includes inpatient and outpatient labs
- Many mapped to LOINC codes in D_LABITEMS
- FLAG indicates abnormal results

---

## 16. MICROBIOLOGYEVENTS

**Purpose:** Microbiology cultures and sensitivities  
**Rows:** ~631,726  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID)  
**Source:** Hospital microbiology lab

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| CHARTDATE | TIMESTAMP | Date culture was charted |
| CHARTTIME | TIMESTAMP | Time culture was charted |
| SPEC_ITEMID | INT | Specimen identifier |
| SPEC_TYPE_DESC | VARCHAR(100) | Specimen type description |
| ORG_ITEMID | INT | Organism identifier |
| ORG_NAME | VARCHAR(100) | Organism name (NULL for negative cultures) |
| ISOLATE_NUM | SMALLINT | Isolate number |
| AB_ITEMID | INT | Antibiotic identifier |
| AB_NAME | VARCHAR(30) | Antibiotic name |
| DILUTION_TEXT | VARCHAR(10) | Dilution text |
| DILUTION_COMPARISON | VARCHAR(20) | Comparison operator |
| DILUTION_VALUE | DOUBLE PRECISION | Dilution value |
| INTERPRETATION | VARCHAR(5) | Sensitivity result (S, R, I, P) |

**Key Notes:**
- Includes culture results and antibiotic sensitivities
- Negative cultures: ORG_NAME is NULL (added in v1.3+)
- INTERPRETATION: S=Sensitive, R=Resistant, I=Intermediate, P=Pending
- Multiple rows per culture if multiple organisms

---

## 17. PRESCRIPTIONS

**Purpose:** Medications ordered (not necessarily administered)  
**Rows:** ~4.6 million  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), ICUSTAYS (ICUSTAY_ID)  
**Source:** Hospital pharmacy system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| ICUSTAY_ID | INT | ICU stay identifier (if applicable) |
| STARTDATE | TIMESTAMP | Start date of prescription |
| ENDDATE | TIMESTAMP | End date of prescription |
| DRUG_TYPE | VARCHAR(100) | Drug type category |
| DRUG | VARCHAR(100) | Drug name |
| DRUG_NAME_POE | VARCHAR(100) | Drug name from provider order entry |
| DRUG_NAME_GENERIC | VARCHAR(100) | Generic drug name |
| FORMULARY_DRUG_CD | VARCHAR(120) | Formulary drug code |
| GSN | VARCHAR(200) | Generic Sequence Number |
| NDC | VARCHAR(120) | National Drug Code |
| PROD_STRENGTH | VARCHAR(120) | Product strength |
| DOSE_VAL_RX | VARCHAR(120) | Dose value prescribed |
| DOSE_UNIT_RX | VARCHAR(120) | Dose unit |
| FORM_VAL_DISP | VARCHAR(120) | Form value dispensed |
| FORM_UNIT_DISP | VARCHAR(120) | Form unit dispensed |
| ROUTE | VARCHAR(120) | Route of administration |

**Key Notes:**
- Orders, not confirmed administration
- For ICU administration data, use INPUTEVENTS tables
- GSN and NDC codes available for standardization
- ICUSTAY_ID may be NULL for floor medications

---

## 18. CPTEVENTS

**Purpose:** Procedures recorded as CPT codes  
**Rows:** ~573,146  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), D_CPT (CPT_CD)  
**Source:** Hospital billing system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| COSTCENTER | VARCHAR(10) | Hospital cost center |
| CHARTDATE | TIMESTAMP | Date procedure was charted |
| CPT_CD | VARCHAR(10) | CPT code (links to D_CPT) |
| CPT_NUMBER | INT | CPT number |
| CPT_SUFFIX | VARCHAR(5) | CPT suffix |
| TICKET_ID_SEQ | INT | Ticket sequence ID |
| SECTIONHEADER | VARCHAR(50) | Section header |
| SUBSECTIONHEADER | VARCHAR(255) | Subsection header |
| DESCRIPTION | VARCHAR(200) | Procedure description |

**Key Notes:**
- Billing data (CPT = Current Procedural Terminology)
- For detailed procedure data, also check PROCEDURES_ICD
- Cost center indicates department

---

## 19. DIAGNOSES_ICD

**Purpose:** Hospital diagnoses coded in ICD-9  
**Rows:** ~651,047  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), D_ICD_DIAGNOSES (ICD9_CODE)  
**Source:** Hospital billing system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| SEQ_NUM | INT | Priority sequence (1 = primary diagnosis) |
| ICD9_CODE | VARCHAR(10) | ICD-9 diagnosis code (links to D_ICD_DIAGNOSES) |

**Key Notes:**
- Final coded diagnoses (vs preliminary ADMISSIONS.DIAGNOSIS)
- SEQ_NUM=1 indicates primary diagnosis
- Multiple diagnoses per admission
- Use D_ICD_DIAGNOSES for code descriptions

---

## 20. PROCEDURES_ICD

**Purpose:** Hospital procedures coded in ICD-9  
**Rows:** ~240,095  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID), D_ICD_PROCEDURES (ICD9_CODE)  
**Source:** Hospital billing system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| SEQ_NUM | INT | Priority sequence |
| ICD9_CODE | VARCHAR(10) | ICD-9 procedure code (links to D_ICD_PROCEDURES) |

**Key Notes:**
- Coded procedures for billing
- SEQ_NUM indicates priority
- Use D_ICD_PROCEDURES for descriptions
- New in MIMIC-III (wasn't in MIMIC-II)

---

## 21. DRGCODES

**Purpose:** Diagnosis Related Groups for billing  
**Rows:** ~125,557  
**Links to:** PATIENTS (SUBJECT_ID), ADMISSIONS (HADM_ID)  
**Source:** Hospital billing system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| SUBJECT_ID | INT | Patient identifier |
| HADM_ID | INT | Hospital admission identifier |
| DRG_TYPE | VARCHAR(20) | DRG classification system (APR, HCFA, MS) |
| DRG_CODE | VARCHAR(20) | DRG code |
| DESCRIPTION | VARCHAR(255) | DRG description |
| DRG_SEVERITY | SMALLINT | Severity level (APR-DRG only) |
| DRG_MORTALITY | SMALLINT | Mortality risk (APR-DRG only) |

**Key Notes:**
- Used for hospital billing
- Multiple DRG_TYPE values per admission
- DRG_SEVERITY and DRG_MORTALITY only for APR-DRG type
- Same code can have multiple descriptions (use DRG_VERSION to distinguish)

---

## 22. D_CPT

**Purpose:** Dictionary of CPT codes  
**Rows:** ~134  
**Links from:** CPTEVENTS (CPT_CD)  
**Source:** CPT coding system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| CATEGORY | SMALLINT | CPT category |
| SECTIONRANGE | VARCHAR(100) | Section range |
| SECTIONHEADER | VARCHAR(50) | Section header |
| SUBSECTIONRANGE | VARCHAR(100) | Subsection range |
| SUBSECTIONHEADER | VARCHAR(255) | Subsection header |
| CODESUFFIX | VARCHAR(5) | Code suffix |
| MINCODEINSUBSECTION | INT | Minimum code in subsection |
| MAXCODEINSUBSECTION | INT | Maximum code in subsection |

**Key Notes:**
- High-level CPT hierarchy
- Use to categorize CPT procedures
- Does not contain individual code definitions

---

## 23. D_ICD_DIAGNOSES

**Purpose:** Dictionary of ICD-9 diagnosis codes  
**Rows:** ~14,567  
**Links from:** DIAGNOSES_ICD (ICD9_CODE)  
**Source:** ICD-9 coding system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| ICD9_CODE | VARCHAR(10) | **Primary Key** - ICD-9 diagnosis code |
| SHORT_TITLE | VARCHAR(50) | Short description |
| LONG_TITLE | VARCHAR(255) | Long description |

**Key Notes:**
- Standard ICD-9 diagnoses
- Some codes in DIAGNOSES_ICD may not exist here (data quality note)
- Use LEFT JOIN when joining to avoid data loss

---

## 24. D_ICD_PROCEDURES

**Purpose:** Dictionary of ICD-9 procedure codes  
**Rows:** ~3,882  
**Links from:** PROCEDURES_ICD (ICD9_CODE)  
**Source:** ICD-9 coding system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| ICD9_CODE | VARCHAR(10) | **Primary Key** - ICD-9 procedure code |
| SHORT_TITLE | VARCHAR(50) | Short description |
| LONG_TITLE | VARCHAR(255) | Long description |

**Key Notes:**
- Standard ICD-9 procedures
- Similar to D_ICD_DIAGNOSES structure
- Use LEFT JOIN when joining

---

## 25. D_ITEMS

**Purpose:** Dictionary of ITEMIDs (except labs)  
**Rows:** ~12,487  
**Links from:** CHARTEVENTS, DATETIMEEVENTS, INPUTEVENTS, OUTPUTEVENTS, PROCEDUREEVENTS_MV (ITEMID)  
**Source:** ICU databases

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| ITEMID | INT | **Primary Key** - Item identifier |
| LABEL | VARCHAR(200) | Item label/name |
| ABBREVIATION | VARCHAR(100) | Item abbreviation |
| DBSOURCE | VARCHAR(20) | Database source ('carevue' or 'metavision') |
| LINKSTO | VARCHAR(50) | Which event table contains this item |
| CATEGORY | VARCHAR(100) | Item category |
| UNITNAME | VARCHAR(100) | Unit name |
| PARAM_TYPE | VARCHAR(30) | Parameter type (Numeric, Text, Date) |
| CONCEPTID | INT | Concept identifier |

**Key Notes:**
- Central dictionary for most items
- ITEMID ranges: <30000 CareVue inputs, 30001-220000 CareVue outputs, ≥220000 Metavision
- LINKSTO shows which table contains the data
- PARAM_TYPE added in v1.4 for text data support
- Does NOT include laboratory items (see D_LABITEMS)

---

## 26. D_LABITEMS

**Purpose:** Dictionary of laboratory test ITEMIDs  
**Rows:** ~753  
**Links from:** LABEVENTS (ITEMID)  
**Source:** Hospital laboratory system

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ROW_ID | INT | Unique row identifier |
| ITEMID | INT | **Primary Key** - Lab item identifier |
| LABEL | VARCHAR(100) | Lab test name |
| FLUID | VARCHAR(100) | Fluid/specimen type |
| CATEGORY | VARCHAR(100) | Test category |
| LOINC_CODE | VARCHAR(100) | LOINC code (standardized) |

**Key Notes:**
- Separate from D_ITEMS (different ITEMID space)
- LOINC codes enable standardization across systems
- ITEMID values different between MIMIC-II and MIMIC-III
- Use LOINC_CODE for cross-version compatibility

---

## Data Quality Notes

### Age De-identification
- Patients >89 years: DOB shifted to 300 years before first admission
- All dates shifted consistently per patient
- Median age of shifted patients: 91.4 years

### ITEMID Ranges
- **CareVue inputs:** <30000
- **CareVue outputs:** 30001-220000  
- **Metavision all:** ≥220000

### Database Sources
- **CareVue:** Older system (2001-2008)
- **Metavision:** Newer system (2008-2012)
- DBSOURCE field indicates which system

### Common Issues
1. **Duplicate lab values:** LABEVENTS is ground truth (use it over CHARTEVENTS)
2. **Missing dictionary entries:** Some codes in fact tables missing from dimension tables (use LEFT JOIN)
3. **Organ donor accounts:** Short/negative length of stay, may have duplicate DEATHTIMEs
4. **Multiple observations:** ~4,579 chartevents and ~380 labevents per admission (mean)

---

## Key Analysis Starting Points

### Basic Patient Query
```sql
SELECT p.subject_id, p.gender, p.dob, 
       a.hadm_id, a.admittime, a.dischtime,
       i.icustay_id, i.intime, i.outtime
FROM patients p
INNER JOIN admissions a ON p.subject_id = a.subject_id
LEFT JOIN icustays i ON a.hadm_id = i.hadm_id;
```

### Age Calculation (handling >89)
```sql
-- For PostgreSQL
ROUND((CAST(admittime AS DATE) - CAST(dob AS DATE)) / 365.242, 2) AS age

-- For BigQuery
DATETIME_DIFF(admittime, dob, YEAR) AS age

-- Age groups
CASE 
    WHEN age <= 1 THEN 'neonate'
    WHEN age <= 14 THEN 'middle'
    WHEN age > 89 THEN '>89'  -- actually >100 due to shift
    ELSE 'adult'
END AS age_group
```

### Vital Signs Query
```sql
SELECT c.subject_id, c.charttime, 
       d.label, c.value, c.valuenum, c.valueuom
FROM chartevents c
INNER JOIN d_items d ON c.itemid = d.itemid
WHERE d.label IN ('Heart Rate', 'Blood Pressure', 'Respiratory Rate')
AND c.subject_id = 12345;
```

### Lab Results Query
```sql
SELECT l.subject_id, l.charttime,
       d.label, d.fluid, l.value, l.valuenum, l.valueuom, l.flag
FROM labevents l
INNER JOIN d_labitems d ON l.itemid = d.itemid
WHERE l.subject_id = 12345
ORDER BY l.charttime;
```

---

## Additional Resources

- **Official Documentation:** https://mimic.mit.edu/docs/iii/
- **Code Repository:** https://github.com/MIT-LCP/mimic-code
- **BigQuery Access:** `physionet-data.mimiciii_clinical.*`
- **Schema Version:** v1.4 (September 2, 2016)

---

**TL;DR:** MIMIC-III contains 26 relational tables tracking ICU patients (2001-2012). Core structure: PATIENTS (46K) → ADMISSIONS (59K) → ICUSTAYS (61K). Major event tables: CHARTEVENTS (330M rows of vital signs), LABEVENTS (27M lab results), NOTEEVENTS (2M clinical notes). Five dictionary tables (D_*) define codes. Key considerations: >89 age de-identification (shifted to 300 years), two ICU systems (CareVue/Metavision with different ITEMID ranges), LABEVENTS is ground truth for labs. Use LEFT JOINs with dictionaries due to incomplete mappings.
