from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Date,
    DECIMAL,
    ForeignKey,
    Index,
)


metadata = MetaData()


# --------------------------------------------------
# PATIENTS
# --------------------------------------------------

patients = Table(
    "patients",
    metadata,

    Column(
        "patient_id",
        Integer,
        primary_key=True
    ),

    Column(
        "age",
        Integer,
        nullable=False
    ),

    Column(
        "gender",
        String(20),
        nullable=False
    ),

    Column(
        "insurance_type",
        String(30),
        nullable=False
    ),
)


# --------------------------------------------------
# ADMISSIONS
# --------------------------------------------------

admissions = Table(
    "admissions",
    metadata,

    Column(
        "admission_id",
        Integer,
        primary_key=True
    ),

    Column(
        "patient_id",
        Integer,
        ForeignKey("patients.patient_id"),
        nullable=False
    ),

    Column(
        "admission_date",
        Date,
        nullable=False
    ),

    Column(
        "discharge_date",
        Date,
        nullable=False
    ),

    Column(
        "admission_type",
        String(20),
        nullable=False
    ),

    Column(
        "department",
        String(50),
        nullable=False
    ),

    Column(
        "bed_type",
        String(20),
        nullable=False
    ),

    Column(
        "length_of_stay",
        Integer,
        nullable=False
    ),
)


# --------------------------------------------------
# READMISSIONS
# --------------------------------------------------

readmissions = Table(
    "readmissions",
    metadata,

    Column(
        "readmission_id",
        Integer,
        primary_key=True
    ),

    Column(
        "original_admission_id",
        Integer,
        ForeignKey("admissions.admission_id"),
        nullable=False
    ),

    Column(
        "days_since_discharge",
        Integer,
        nullable=False
    ),

    Column(
        "reason_code",
        String(100),
        nullable=False
    ),
)


# --------------------------------------------------
# STAFFING
# --------------------------------------------------

staffing = Table(
    "staffing",
    metadata,

    Column(
        "staffing_id",
        Integer,
        primary_key=True,
        autoincrement=True
    ),

    Column(
        "date",
        Date,
        nullable=False
    ),

    Column(
        "department",
        String(50),
        nullable=False
    ),

    Column(
        "shift",
        String(20),
        nullable=False
    ),

    Column(
        "staff_count",
        Integer,
        nullable=False
    ),

    Column(
        "patient_count",
        Integer,
        nullable=False
    ),
)


# --------------------------------------------------
# COSTS
# --------------------------------------------------

costs = Table(
    "costs",
    metadata,

    Column(
        "admission_id",
        Integer,
        ForeignKey("admissions.admission_id"),
        primary_key=True
    ),

    Column(
        "billed_amount",
        DECIMAL(12, 2),
        nullable=False
    ),

    Column(
        "insurance_covered_amount",
        DECIMAL(12, 2),
        nullable=False
    ),

    Column(
        "out_of_pocket",
        DECIMAL(12, 2),
        nullable=False
    ),
)


# --------------------------------------------------
# INDEXES
# --------------------------------------------------

Index(
    "idx_admissions_patient",
    admissions.c.patient_id
)

Index(
    "idx_admissions_department",
    admissions.c.department
)

Index(
    "idx_admissions_date",
    admissions.c.admission_date
)

Index(
    "idx_readmissions_admission",
    readmissions.c.original_admission_id
)

Index(
    "idx_staffing_date_department",
    staffing.c.date,
    staffing.c.department
)