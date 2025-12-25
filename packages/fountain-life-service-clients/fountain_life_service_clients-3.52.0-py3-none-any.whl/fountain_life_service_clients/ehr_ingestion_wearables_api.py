# This file was generated automatically. Do not edit it directly.
from typing import List, Literal, NotRequired, TypedDict, Unpack, cast

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class GetAnchorParams(TypedDict):
    type: str
    projectId: str


class GetAnchorResponse(TypedDict):
    anchor: NotRequired[str]


class Source(TypedDict):
    name: str


class SourceRevision(TypedDict):
    """
    The source of the device or app that recorded the data.
    """

    source: Source


class Metadata(TypedDict):
    HKTimeZone: NotRequired[str]


class Sample(TypedDict):
    uuid: str
    startDate: str
    endDate: str
    sourceRevision: NotRequired[SourceRevision]
    metadata: NotRequired[Metadata]


class DeletedSample(TypedDict):
    uuid: str


class PutRecordsRequest(TypedDict):
    type: str
    projectId: str
    newAnchor: str
    tz: NotRequired[str]
    samples: List[Sample]
    deletedSamples: List[DeletedSample]


class PutRecordsResponse(TypedDict):
    runId: NotRequired[str]


class DeleteRecordsParams(TypedDict):
    type: NotRequired[
        Literal[
            "HKQuantityTypeIdentifierBodyMass",
            "HKQuantityTypeIdentifierHeight",
            "HKQuantityTypeIdentifierBodyMassIndex",
            "HKQuantityTypeIdentifierBodyFatPercentage",
            "HKWorkoutTypeIdentifier",
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKQuantityTypeIdentifierActiveEnergyBurned",
            "HKCategoryTypeIdentifierMenstrualFlow",
            "HKQuantityTypeIdentifierBloodGlucose",
            "HKQuantityTypeIdentifierOxygenSaturation",
            "HKQuantityTypeIdentifierAppleWalkingSteadiness",
            "HKQuantityTypeIdentifierWalkingHeartRateAverage",
            "HKQuantityTypeIdentifierRestingHeartRate",
            "HKCategoryTypeIdentifierHighHeartRateEvent",
            "HKCategoryTypeIdentifierLowHeartRateEvent",
            "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
            "HKQuantityTypeIdentifierSixMinuteWalkTestDistance",
            "HKClinicalTypeIdentifierLabResultRecord",
            "HKClinicalTypeIdentifierAllergyRecord",
            "HKClinicalTypeIdentifierMedicationRecord",
            "HKClinicalTypeIdentifierConditionRecord",
            "HKClinicalTypeIdentifierImmunizationRecord",
            "HKClinicalTypeIdentifierProcedureRecord",
        ]
    ]
    projectId: str


class BackfillRecordsRequest(TypedDict):
    hkType: Literal[
        "HKQuantityTypeIdentifierBodyMass",
        "HKQuantityTypeIdentifierHeight",
        "HKQuantityTypeIdentifierBodyMassIndex",
        "HKQuantityTypeIdentifierBodyFatPercentage",
        "HKWorkoutTypeIdentifier",
        "HKCategoryTypeIdentifierSleepAnalysis",
        "HKQuantityTypeIdentifierActiveEnergyBurned",
        "HKCategoryTypeIdentifierMenstrualFlow",
        "HKQuantityTypeIdentifierBloodGlucose",
        "HKQuantityTypeIdentifierOxygenSaturation",
        "HKQuantityTypeIdentifierAppleWalkingSteadiness",
        "HKQuantityTypeIdentifierWalkingHeartRateAverage",
        "HKQuantityTypeIdentifierRestingHeartRate",
        "HKCategoryTypeIdentifierHighHeartRateEvent",
        "HKCategoryTypeIdentifierLowHeartRateEvent",
        "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
        "HKQuantityTypeIdentifierSixMinuteWalkTestDistance",
        "HKClinicalTypeIdentifierLabResultRecord",
        "HKClinicalTypeIdentifierAllergyRecord",
        "HKClinicalTypeIdentifierMedicationRecord",
        "HKClinicalTypeIdentifierConditionRecord",
        "HKClinicalTypeIdentifierImmunizationRecord",
        "HKClinicalTypeIdentifierProcedureRecord",
    ]
    projectId: str
    patientId: NotRequired[str]


class BackfillRecordsResponse(TypedDict):
    runId: str


class EhrIngestionWearablesApiClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {
            "target": "lambda://ehr-ingestion-wearables-api:deployed",
            **(cfg or {}),
        }
        super().__init__(**kwargs)

    async def get_anchor(self, params: GetAnchorParams):
        """Get the member's most recently processed anchor for a given healthkit sample type."""
        res = await self.client.request(
            path="/v1/ehr-ingestion-wearables/v1/healthkit/anchor",
            method="GET",
            params=cast(dict, params),
        )
        return cast(AlphaResponse[GetAnchorResponse], res)

    async def put_records(self, body: PutRecordsRequest):
        """Put records of a given healthkit sample type. Supports idempotent creation and deletion."""
        res = await self.client.request(
            path="/v1/ehr-ingestion-wearables/v1/healthkit/records",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[PutRecordsResponse], res)

    async def delete_records(self, params: DeleteRecordsParams):
        """Delete all records for a member's given healthkit sample type."""
        await self.client.request(
            path="/v1/ehr-ingestion-wearables/v1/healthkit/records",
            method="DELETE",
            params=cast(dict, params),
        )

    async def backfill_records(self, body: BackfillRecordsRequest):
        """Backfill all records for a given healthkit sample type."""
        res = await self.client.request(
            path="/private/v1/healthkit/records/backfill",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[BackfillRecordsResponse], res)
