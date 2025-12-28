from collections import defaultdict
from datetime import date
from dateutil.parser import parse as parse_date
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, TypedDict
from nexo.enums.identity import Gender
from nexo.schemas.document import CSVDocument
from nexo.schemas.error.enums import ErrorCode
from nexo.types.string import OptStr
from ..enums.parameter import ParameterGroup


class PatientInformation(BaseModel):
    id: Annotated[
        str,
        Field(..., description="Patient's ID", max_length=16, pattern=r"^[0-9]{1,16}$"),
    ]
    name: Annotated[str, Field(..., description="Patient's name", max_length=200)]
    checkup_date: Annotated[date, Field(..., description="Checkup date")]
    date_of_birth: Annotated[date, Field(..., description="Patient's Date Of Birth")]
    gender: Annotated[Gender, Field(..., description="Patient's gender")]


class PatientExamination(BaseModel):
    parameter_group: Annotated[
        ParameterGroup, Field(..., description="Parameter group")
    ]
    parameter: Annotated[str, Field(..., description="Parameter", max_length=50)]
    value: Annotated[OptStr, Field(..., description="Value")]
    unit: Annotated[OptStr, Field(..., description="Unit")]


ListOfPatientExaminations = list[PatientExamination]


class PatientExaminationsMixin(BaseModel):
    examinations: Annotated[
        ListOfPatientExaminations, Field(..., description="Examinations", min_length=1)
    ]


class FlatPatientData(PatientExamination, PatientInformation):
    pass


ListOfFlatPatientData = list[FlatPatientData]


class GroupedPatientData(PatientExaminationsMixin, PatientInformation):
    @classmethod
    def from_base(
        cls, base: PatientInformation, examinations: ListOfPatientExaminations
    ) -> "GroupedPatientData":
        return cls(**base.model_dump(), examinations=examinations)


class SeenData(TypedDict):
    name: str
    checkup_date: date
    date_of_birth: date
    gender: Gender


class GroupCSVDocument(CSVDocument):
    @computed_field
    @property
    def flat_patient_data(self) -> ListOfFlatPatientData:
        rows = self.rows
        results: ListOfFlatPatientData = []

        for index, row in enumerate(rows):
            # Validate patient id
            id = row["patient_id"]
            if id is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST, f"Found null patient id in row {index}"
                )
            id = id.strip()

            # Validate patient name
            name = row["name"]
            if name is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST, f"Found null patient name in row {index}"
                )
            name = name.strip()

            # Validate checkup date
            checkup_date = row["mcu_date"]
            if checkup_date is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST, f"Found null Checkup Date in row {index}"
                )
            checkup_date = checkup_date.strip()
            try:
                checkup_date = parse_date(checkup_date, dayfirst=True).date()
            except Exception:
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    f"Invalid date format of Checkup Date in row {index}: '{checkup_date}'",
                )

            # Validate Date Of Birth
            date_of_birth = row["date_of_birth"]
            if date_of_birth is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST, f"Found null Date Of Birth in row {index}"
                )
            date_of_birth = date_of_birth.strip()
            try:
                date_of_birth = parse_date(date_of_birth, dayfirst=True).date()
            except Exception:
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    f"Invalid date format of Date Of Birth in row {index}: '{date_of_birth}'",
                )

            # Validate patient gender
            gender = row["gender"]
            if gender is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST, f"Found null patient gender in row {index}"
                )
            gender = Gender(gender.strip().lower())

            # Validate parameter group
            parameter_group = row["parameter_group"]
            if parameter_group is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST, f"Found null parameter group in row {index}"
                )
            parameter_group = parameter_group.strip().replace(" ", "_").lower()
            if parameter_group == "physical_examination":
                parameter_group = ParameterGroup.PHYSICAL
            else:
                parameter_group = ParameterGroup(parameter_group)

            # Validate parameter
            parameter = row["parameter"]
            if parameter is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST, f"Found null parameter in row {index}"
                )

            data = FlatPatientData(
                id=id,
                name=name,
                checkup_date=checkup_date,
                gender=gender,
                date_of_birth=date_of_birth,
                parameter_group=parameter_group,
                parameter=parameter,
                value=row["value"],
                unit=row["unit"],
            )

            results.append(data)

        # --- Uniqueness validation across rows ---
        seen: dict[str, SeenData] = {}

        for index, row_data in enumerate(results):
            pid = row_data.id

            if pid not in seen:
                seen[pid] = {
                    "name": row_data.name,
                    "checkup_date": row_data.checkup_date,
                    "date_of_birth": row_data.date_of_birth,
                    "gender": row_data.gender,
                }
            else:
                known = seen[pid]

                # Name must match previous occurrences
                if row_data.name != known["name"]:
                    raise ValueError(
                        ErrorCode.BAD_REQUEST,
                        f"Conflicting patient name for ID '{pid}' in row {index}: "
                        f"'{row_data.name}' != '{known['name']}'",
                    )

                # checkup date must match
                if row_data.checkup_date != known["checkup_date"]:
                    raise ValueError(
                        ErrorCode.BAD_REQUEST,
                        f"Conflicting checkup date for ID '{pid}' in row {index}: "
                        f"'{row_data.checkup_date}' != '{known['checkup_date']}'",
                    )

                # Gender must match
                if row_data.gender != known["gender"]:
                    raise ValueError(
                        ErrorCode.BAD_REQUEST,
                        f"Conflicting gender for ID '{pid}' in row {index}: "
                        f"'{row_data.gender}' != '{known['gender']}'",
                    )

        return results

    @computed_field
    @property
    def grouped_patient_data(self) -> dict[str, GroupedPatientData]:
        flat_data = self.flat_patient_data

        grouped: dict[str, PatientInformation] = {}
        examinations: dict[str, ListOfPatientExaminations] = defaultdict(
            ListOfPatientExaminations
        )

        for row in flat_data:
            key = row.id

            if key not in grouped:
                grouped[key] = PatientInformation(
                    id=row.id,
                    name=row.name,
                    checkup_date=row.checkup_date,
                    date_of_birth=row.date_of_birth,
                    gender=row.gender,
                )

            examinations[key].append(
                PatientExamination(
                    parameter_group=row.parameter_group,
                    parameter=row.parameter,
                    value=row.value,
                    unit=row.unit,
                )
            )

        results: dict[str, GroupedPatientData] = {}

        for key, base_data in grouped.items():
            results[key] = GroupedPatientData.from_base(
                base=base_data,
                examinations=examinations[key],
            )

        return results

    @computed_field
    @property
    def patient_count(self) -> int:
        ids = set()
        for index, row in enumerate(self.rows):
            pid = row["patient_id"]
            if pid is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST, f"Found null patient id in row {index}"
                )
            ids.add(pid.strip())

        return len(ids)


OptGroupCSVDocument = GroupCSVDocument | None
