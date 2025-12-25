# This file was generated automatically. Do not edit it directly.
from typing import (
    List,
    Literal,
    NotRequired,
    Optional,
    TypedDict,
    Union,
    Unpack,
    cast,
)
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)

SearchVariantsRequest = TypedDict(
    "SearchVariantsRequest",
    {
        "variantSetIds": str,
        "include": NotRequired[str],
        "variantId": NotRequired[Union[str, List[str]]],
        "sequenceType": NotRequired[Union[Literal["somatic"], Literal["germline"]]],
        "gene": NotRequired[Union[str, List[str]]],
        "aminoAcidChange": NotRequired[Union[str, List[str]]],
        "drugAssociations": NotRequired[bool],
        "hasJaxKnowledge": NotRequired[bool],
        "class": NotRequired[Union[str, List[str]]],
        "group": NotRequired[Union[str, List[str]]],
        "impact": NotRequired[Union[str, List[str]]],
        "biotype": NotRequired[Union[str, List[str]]],
        "rsid": NotRequired[Union[str, List[str]]],
        "chromosome": NotRequired[Union[str, List[str]]],
        "position": NotRequired[Union[str, List[str]]],
        "nextPageToken": NotRequired[str],
        "pageSize": NotRequired[float],
        "popAlleleFrequency": NotRequired[str],
        "genesPair": NotRequired[str],
        "clinvarSignificance": NotRequired[Union[str, List[str]]],
    },
)


class Clinvar(TypedDict):
    alleleId: str
    disease: str
    review: str
    significance: str
    submission: str
    nearVariant: float


class Cosmic(TypedDict):
    sampleCount: float
    nearVariant: float
    tumorSite: NotRequired[str]
    histology: NotRequired[str]
    cosmicId: NotRequired[str]
    status: NotRequired[str]


EnsemblCanonItem = TypedDict(
    "EnsemblCanonItem",
    {
        "class": NotRequired[str],
        "impact": NotRequired[str],
        "gene": NotRequired[str],
        "geneId": NotRequired[str],
        "transcriptId": NotRequired[str],
        "biotype": NotRequired[str],
        "exonIntronRank": NotRequired[str],
        "nucleotideChange": NotRequired[str],
        "aminoAcidChange": NotRequired[str],
        "hgvsAminoAcidChange": NotRequired[str],
    },
)


class Dbnsfp(TypedDict):
    siftPred: List[Optional[str]]
    mutationTasterPred: List[Optional[str]]
    fathmmPred: List[Optional[str]]


EnsemblItem = TypedDict(
    "EnsemblItem",
    {
        "class": NotRequired[str],
        "impact": NotRequired[str],
        "gene": NotRequired[str],
        "geneId": NotRequired[str],
        "transcriptId": NotRequired[str],
        "biotype": NotRequired[str],
        "exonIntronRank": NotRequired[str],
        "nucleotideChange": NotRequired[str],
        "aminoAcidChange": NotRequired[str],
        "hgvsAminoAcidChange": NotRequired[str],
    },
)


class Vcf(TypedDict):
    quality: float
    filter: str
    variantAllelicFrequency: float
    coverage: str


class Item(TypedDict):
    id: str
    chromosome: str
    reference: str
    alternate: str
    position: float
    minimumAlleleFrequency: float
    maximumAlleleFrequency: float
    gnomadAlleleFrequency: float
    gnomadHomozygous: float
    rsid: str
    zygosity: str
    clinvar: Clinvar
    cosmic: Cosmic
    ensemblCanon: List[EnsemblCanonItem]
    dbnsfp: Dbnsfp
    ensembl: NotRequired[List[EnsemblItem]]
    vcf: NotRequired[Vcf]


class Links(TypedDict):
    self: str
    next: NotRequired[str]


class Invalid(TypedDict):
    variantSetIds: List[str]


class SearchVariantsResponse(TypedDict):
    items: NotRequired[List[Item]]
    links: Links
    sorted: NotRequired[bool]
    count: NotRequired[float]
    invalid: NotRequired[Invalid]


class Set(TypedDict):
    id: str
    fileId: NotRequired[str]
    sequenceId: NotRequired[str]
    name: NotRequired[str]
    setType: NotRequired[str]
    status: NotRequired[str]
    sequenceType: NotRequired[str]


class item(TypedDict):
    id: str
    datasetId: NotRequired[str]
    name: NotRequired[str]
    patientId: NotRequired[str]
    reportFileId: NotRequired[str]
    indexedDate: NotRequired[str]
    testType: NotRequired[str]
    referenceSetId: NotRequired[str]
    sourceFileId: NotRequired[str]
    ingestFileId: NotRequired[str]
    status: NotRequired[str]
    createdDate: NotRequired[str]
    sets: List[Set]


class GetSubjectTestsResponse(TypedDict):
    items: List[item]


class GenomicsServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://genomics-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def search_variants(self, body: SearchVariantsRequest):
        """Search for variants"""
        res = await self.client.request(
            path="/v1/genomics/variants/_search", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[SearchVariantsResponse], res)

    async def get_subject_tests(self, project_id: str, subject_id: str):
        """Get subject tests"""
        res = await self.client.request(
            path=f"/v1/genomics/projects/{quote(project_id)}/subjects/{quote(subject_id)}/tests",
            method="GET",
        )
        return cast(AlphaResponse[GetSubjectTestsResponse], res)
