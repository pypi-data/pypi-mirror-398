from dataclasses import dataclass, field
from enum import Enum
from xsdata.models.datatype import XmlDate as XmlDate, XmlPeriod as XmlPeriod

__NAMESPACE__: str

class CitationTypeType(Enum):
    BOOK = 'book'
    JOURNAL_ARTICLE = 'journal article'
    ONLINE_JOURNAL_ARTICLE = 'online journal article'
    PATENT = 'patent'
    SUBMISSION = 'submission'
    THESIS = 'thesis'
    UNPUBLISHED_OBSERVATIONS = 'unpublished observations'

class CommentTypeType(Enum):
    ALLERGEN = 'allergen'
    ALTERNATIVE_PRODUCTS = 'alternative products'
    BIOTECHNOLOGY = 'biotechnology'
    BIOPHYSICOCHEMICAL_PROPERTIES = 'biophysicochemical properties'
    CATALYTIC_ACTIVITY = 'catalytic activity'
    CAUTION = 'caution'
    COFACTOR = 'cofactor'
    DEVELOPMENTAL_STAGE = 'developmental stage'
    DISEASE = 'disease'
    DOMAIN = 'domain'
    DISRUPTION_PHENOTYPE = 'disruption phenotype'
    ACTIVITY_REGULATION = 'activity regulation'
    FUNCTION = 'function'
    INDUCTION = 'induction'
    MISCELLANEOUS = 'miscellaneous'
    PATHWAY = 'pathway'
    PHARMACEUTICAL = 'pharmaceutical'
    POLYMORPHISM = 'polymorphism'
    PTM = 'PTM'
    RNA_EDITING = 'RNA editing'
    SIMILARITY = 'similarity'
    SUBCELLULAR_LOCATION = 'subcellular location'
    SEQUENCE_CAUTION = 'sequence caution'
    SUBUNIT = 'subunit'
    TISSUE_SPECIFICITY = 'tissue specificity'
    TOXIC_DOSE = 'toxic dose'
    ONLINE_INFORMATION = 'online information'
    MASS_SPECTROMETRY = 'mass spectrometry'
    INTERACTION = 'interaction'

class ConflictType(Enum):
    FRAMESHIFT = 'frameshift'
    ERRONEOUS_INITIATION = 'erroneous initiation'
    ERRONEOUS_TERMINATION = 'erroneous termination'
    ERRONEOUS_GENE_MODEL_PREDICTION = 'erroneous gene model prediction'
    ERRONEOUS_TRANSLATION = 'erroneous translation'
    MISCELLANEOUS_DISCREPANCY = 'miscellaneous discrepancy'

@dataclass
class ConsortiumType:
    class Meta:
        name = ...
    name: str | None
    def __init__(self, name=...) -> None: ...

@dataclass
class Copyright:
    class Meta:
        name = ...
        namespace = ...
    value: str
    def __init__(self, value=...) -> None: ...

class EntryDataset(Enum):
    SWISS_PROT = 'Swiss-Prot'
    TR_EMBL = 'TrEMBL'

class EventTypeType(Enum):
    ALTERNATIVE_SPLICING = 'alternative splicing'
    ALTERNATIVE_INITIATION = 'alternative initiation'
    ALTERNATIVE_PROMOTER = 'alternative promoter'
    RIBOSOMAL_FRAMESHIFTING = 'ribosomal frameshifting'

@dataclass
class EvidencedStringType:
    class Meta:
        name = ...
    value: str
    evidence: list[int]
    def __init__(self, value=..., evidence=...) -> None: ...

class FeatureTypeType(Enum):
    ACTIVE_SITE = 'active site'
    BINDING_SITE = 'binding site'
    CALCIUM_BINDING_REGION = 'calcium-binding region'
    CHAIN = 'chain'
    COILED_COIL_REGION = 'coiled-coil region'
    COMPOSITIONALLY_BIASED_REGION = 'compositionally biased region'
    CROSS_LINK = 'cross-link'
    DISULFIDE_BOND = 'disulfide bond'
    DNA_BINDING_REGION = 'DNA-binding region'
    DOMAIN = 'domain'
    GLYCOSYLATION_SITE = 'glycosylation site'
    HELIX = 'helix'
    INITIATOR_METHIONINE = 'initiator methionine'
    LIPID_MOIETY_BINDING_REGION = 'lipid moiety-binding region'
    METAL_ION_BINDING_SITE = 'metal ion-binding site'
    MODIFIED_RESIDUE = 'modified residue'
    MUTAGENESIS_SITE = 'mutagenesis site'
    NON_CONSECUTIVE_RESIDUES = 'non-consecutive residues'
    NON_TERMINAL_RESIDUE = 'non-terminal residue'
    NUCLEOTIDE_PHOSPHATE_BINDING_REGION = 'nucleotide phosphate-binding region'
    PEPTIDE = 'peptide'
    PROPEPTIDE = 'propeptide'
    REGION_OF_INTEREST = 'region of interest'
    REPEAT = 'repeat'
    NON_STANDARD_AMINO_ACID = 'non-standard amino acid'
    SEQUENCE_CONFLICT = 'sequence conflict'
    SEQUENCE_VARIANT = 'sequence variant'
    SHORT_SEQUENCE_MOTIF = 'short sequence motif'
    SIGNAL_PEPTIDE = 'signal peptide'
    SITE = 'site'
    SPLICE_VARIANT = 'splice variant'
    STRAND = 'strand'
    TOPOLOGICAL_DOMAIN = 'topological domain'
    TRANSIT_PEPTIDE = 'transit peptide'
    TRANSMEMBRANE_REGION = 'transmembrane region'
    TURN = 'turn'
    UNSURE_RESIDUE = 'unsure residue'
    ZINC_FINGER_REGION = 'zinc finger region'
    INTRAMEMBRANE_REGION = 'intramembrane region'

class GeneLocationTypeType(Enum):
    APICOPLAST = 'apicoplast'
    CHLOROPLAST = 'chloroplast'
    ORGANELLAR_CHROMATOPHORE = 'organellar chromatophore'
    CYANELLE = 'cyanelle'
    HYDROGENOSOME = 'hydrogenosome'
    MITOCHONDRION = 'mitochondrion'
    NON_PHOTOSYNTHETIC_PLASTID = 'non-photosynthetic plastid'
    NUCLEOMORPH = 'nucleomorph'
    PLASMID = 'plasmid'
    PLASTID = 'plastid'

class GeneNameTypeType(Enum):
    PRIMARY = 'primary'
    SYNONYM = 'synonym'
    ORDERED_LOCUS = 'ordered locus'
    ORF = 'ORF'

@dataclass
class KeywordType:
    class Meta:
        name = ...
    value: str
    evidence: list[int]
    id: str | None
    def __init__(self, value=..., evidence=..., id=...) -> None: ...

@dataclass
class MoleculeType:
    class Meta:
        name = ...
    value: str
    id: str | None
    def __init__(self, value=..., id=...) -> None: ...

class OrganismNameTypeType(Enum):
    COMMON = 'common'
    FULL = 'full'
    SCIENTIFIC = 'scientific'
    SYNONYM = 'synonym'
    ABBREVIATION = 'abbreviation'

@dataclass
class PersonType:
    class Meta:
        name = ...
    name: str | None
    def __init__(self, name=...) -> None: ...

class PhysiologicalReactionTypeDirection(Enum):
    LEFT_TO_RIGHT = 'left-to-right'
    RIGHT_TO_LEFT = 'right-to-left'

class PositionTypeStatus(Enum):
    CERTAIN = 'certain'
    UNCERTAIN = 'uncertain'
    LESS_THAN = 'less than'
    GREATER_THAN = 'greater than'
    UNKNOWN = 'unknown'

@dataclass
class PropertyType:
    class Meta:
        name = ...
    type_value: str | None
    value: str | None
    def __init__(self, type_value=..., value=...) -> None: ...

class ProteinExistenceTypeType(Enum):
    EVIDENCE_AT_PROTEIN_LEVEL = 'evidence at protein level'
    EVIDENCE_AT_TRANSCRIPT_LEVEL = 'evidence at transcript level'
    INFERRED_FROM_HOMOLOGY = 'inferred from homology'
    PREDICTED = 'predicted'
    UNCERTAIN = 'uncertain'

class SequenceTypeFragment(Enum):
    SINGLE = 'single'
    MULTIPLE = 'multiple'

class SequenceResource(Enum):
    EMBL_CDS = 'EMBL-CDS'
    EMBL = 'EMBL'

class SequenceType2(Enum):
    NOT_DESCRIBED = 'not described'
    DESCRIBED = 'described'
    DISPLAYED = 'displayed'
    EXTERNAL = 'external'

@dataclass
class SourceDataType:
    class Meta:
        name = ...
    strain: list['SourceDataType.Strain']
    plasmid: list['SourceDataType.Plasmid']
    transposon: list['SourceDataType.Transposon']
    tissue: list['SourceDataType.Tissue']
    @dataclass
    class Strain:
        value: str = field(default='', metadata={'required': True})
        evidence: list[int] = field(default_factory=list, metadata={'type': 'Attribute', 'tokens': True})
    @dataclass
    class Plasmid:
        value: str = field(default='', metadata={'required': True})
        evidence: list[int] = field(default_factory=list, metadata={'type': 'Attribute', 'tokens': True})
    @dataclass
    class Transposon:
        value: str = field(default='', metadata={'required': True})
        evidence: list[int] = field(default_factory=list, metadata={'type': 'Attribute', 'tokens': True})
    @dataclass
    class Tissue:
        value: str = field(default='', metadata={'required': True})
        evidence: list[int] = field(default_factory=list, metadata={'type': 'Attribute', 'tokens': True})
    def __init__(self, strain=..., plasmid=..., transposon=..., tissue=...) -> None: ...

class StatusTypeStatus(Enum):
    KNOWN = 'known'
    UNKNOWN = 'unknown'

@dataclass
class DbReferenceType:
    class Meta:
        name = ...
    molecule: MoleculeType | None
    property: list[PropertyType]
    type_value: str | None
    id: str | None
    evidence: list[int]
    def __init__(self, molecule=..., property=..., type_value=..., id=..., evidence=...) -> None: ...

@dataclass
class EventType:
    class Meta:
        name = ...
    type_value: EventTypeType | None
    def __init__(self, type_value=...) -> None: ...

@dataclass
class GeneNameType:
    class Meta:
        name = ...
    value: str
    evidence: list[int]
    type_value: GeneNameTypeType | None
    def __init__(self, value=..., evidence=..., type_value=...) -> None: ...

@dataclass
class IsoformType:
    class Meta:
        name = ...
    id: list[str]
    name: list['IsoformType.Name']
    sequence: IsoformType.Sequence | None
    text: list[EvidencedStringType]
    @dataclass
    class Name:
        value: str = field(default='', metadata={'required': True})
        evidence: list[int] = field(default_factory=list, metadata={'type': 'Attribute', 'tokens': True})
    @dataclass
    class Sequence:
        type_value: SequenceType2 | None = field(default=None, metadata={'name': 'type', 'type': 'Attribute', 'required': True})
        ref: str | None = field(default=None, metadata={'type': 'Attribute'})
    def __init__(self, id=..., name=..., sequence=..., text=...) -> None: ...

@dataclass
class NameListType:
    class Meta:
        name = ...
    consortium: list[ConsortiumType]
    person: list[PersonType]
    def __init__(self, consortium=..., person=...) -> None: ...

@dataclass
class OrganismNameType:
    class Meta:
        name = ...
    value: str
    type_value: OrganismNameTypeType | None
    def __init__(self, value=..., type_value=...) -> None: ...

@dataclass
class PositionType:
    class Meta:
        name = ...
    position: int | None
    status: PositionTypeStatus
    evidence: list[int]
    def __init__(self, position=..., status=..., evidence=...) -> None: ...

@dataclass
class ProteinExistenceType:
    class Meta:
        name = ...
    type_value: ProteinExistenceTypeType | None
    def __init__(self, type_value=...) -> None: ...

@dataclass
class ProteinType:
    class Meta:
        name = ...
    recommended_name: ProteinType.RecommendedName | None
    alternative_name: list['ProteinType.AlternativeName']
    submitted_name: list['ProteinType.SubmittedName']
    allergen_name: EvidencedStringType | None
    biotech_name: EvidencedStringType | None
    cd_antigen_name: list[EvidencedStringType]
    inn_name: list[EvidencedStringType]
    domain: list['ProteinType.Domain']
    component: list['ProteinType.Component']
    @dataclass
    class Domain:
        recommended_name: ProteinType.Domain.RecommendedName | None = field(default=None, metadata={'name': 'recommendedName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        alternative_name: list['ProteinType.Domain.AlternativeName'] = field(default_factory=list, metadata={'name': 'alternativeName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        submitted_name: list['ProteinType.Domain.SubmittedName'] = field(default_factory=list, metadata={'name': 'submittedName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        allergen_name: EvidencedStringType | None = field(default=None, metadata={'name': 'allergenName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        biotech_name: EvidencedStringType | None = field(default=None, metadata={'name': 'biotechName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        cd_antigen_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'cdAntigenName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        inn_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'innName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        @dataclass
        class RecommendedName:
            full_name: EvidencedStringType | None = field(default=None, metadata={'name': 'fullName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
            short_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'shortName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
            ec_number: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'ecNumber', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        @dataclass
        class AlternativeName:
            full_name: EvidencedStringType | None = field(default=None, metadata={'name': 'fullName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
            short_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'shortName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
            ec_number: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'ecNumber', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        @dataclass
        class SubmittedName:
            full_name: EvidencedStringType | None = field(default=None, metadata={'name': 'fullName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
            ec_number: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'ecNumber', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        def __init__(self, recommended_name=..., alternative_name=..., submitted_name=..., allergen_name=..., biotech_name=..., cd_antigen_name=..., inn_name=...) -> None: ...
    @dataclass
    class Component:
        recommended_name: ProteinType.Component.RecommendedName | None = field(default=None, metadata={'name': 'recommendedName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        alternative_name: list['ProteinType.Component.AlternativeName'] = field(default_factory=list, metadata={'name': 'alternativeName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        submitted_name: list['ProteinType.Component.SubmittedName'] = field(default_factory=list, metadata={'name': 'submittedName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        allergen_name: EvidencedStringType | None = field(default=None, metadata={'name': 'allergenName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        biotech_name: EvidencedStringType | None = field(default=None, metadata={'name': 'biotechName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        cd_antigen_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'cdAntigenName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        inn_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'innName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        @dataclass
        class RecommendedName:
            full_name: EvidencedStringType | None = field(default=None, metadata={'name': 'fullName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
            short_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'shortName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
            ec_number: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'ecNumber', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        @dataclass
        class AlternativeName:
            full_name: EvidencedStringType | None = field(default=None, metadata={'name': 'fullName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
            short_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'shortName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
            ec_number: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'ecNumber', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        @dataclass
        class SubmittedName:
            full_name: EvidencedStringType | None = field(default=None, metadata={'name': 'fullName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
            ec_number: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'ecNumber', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        def __init__(self, recommended_name=..., alternative_name=..., submitted_name=..., allergen_name=..., biotech_name=..., cd_antigen_name=..., inn_name=...) -> None: ...
    @dataclass
    class RecommendedName:
        full_name: EvidencedStringType | None = field(default=None, metadata={'name': 'fullName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
        short_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'shortName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        ec_number: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'ecNumber', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
    @dataclass
    class AlternativeName:
        full_name: EvidencedStringType | None = field(default=None, metadata={'name': 'fullName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        short_name: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'shortName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        ec_number: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'ecNumber', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
    @dataclass
    class SubmittedName:
        full_name: EvidencedStringType | None = field(default=None, metadata={'name': 'fullName', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
        ec_number: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'ecNumber', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
    def __init__(self, recommended_name=..., alternative_name=..., submitted_name=..., allergen_name=..., biotech_name=..., cd_antigen_name=..., inn_name=..., domain=..., component=...) -> None: ...

@dataclass
class SequenceType1:
    class Meta:
        name = ...
    value: str
    length: int | None
    mass: int | None
    checksum: str | None
    modified: XmlDate | None
    version: int | None
    precursor: bool | None
    fragment: SequenceTypeFragment | None
    def __init__(self, value=..., length=..., mass=..., checksum=..., modified=..., version=..., precursor=..., fragment=...) -> None: ...

@dataclass
class StatusType:
    class Meta:
        name = ...
    value: str
    status: StatusTypeStatus
    def __init__(self, value=..., status=...) -> None: ...

@dataclass
class SubcellularLocationType:
    class Meta:
        name = ...
    location: list[EvidencedStringType]
    topology: list[EvidencedStringType]
    orientation: list[EvidencedStringType]
    def __init__(self, location=..., topology=..., orientation=...) -> None: ...

@dataclass
class CitationType:
    class Meta:
        name = ...
    title: str | None
    editor_list: NameListType | None
    author_list: NameListType | None
    locator: str | None
    db_reference: list[DbReferenceType]
    type_value: CitationTypeType | None
    date: XmlDate | XmlPeriod | None
    name: str | None
    volume: str | None
    first: str | None
    last: str | None
    publisher: str | None
    city: str | None
    db: str | None
    number: str | None
    institute: str | None
    country: str | None
    def __init__(self, title=..., editor_list=..., author_list=..., locator=..., db_reference=..., type_value=..., date=..., name=..., volume=..., first=..., last=..., publisher=..., city=..., db=..., number=..., institute=..., country=...) -> None: ...

@dataclass
class CofactorType:
    class Meta:
        name = ...
    name: str | None
    db_reference: DbReferenceType | None
    evidence: list[int]
    def __init__(self, name=..., db_reference=..., evidence=...) -> None: ...

@dataclass
class GeneLocationType:
    class Meta:
        name = ...
    name: list[StatusType]
    type_value: GeneLocationTypeType | None
    evidence: list[int]
    def __init__(self, name=..., type_value=..., evidence=...) -> None: ...

@dataclass
class GeneType:
    class Meta:
        name = ...
    name: list[GeneNameType]
    def __init__(self, name=...) -> None: ...

@dataclass
class ImportedFromType:
    class Meta:
        name = ...
    db_reference: DbReferenceType | None
    def __init__(self, db_reference=...) -> None: ...

@dataclass
class InteractantType:
    class Meta:
        name = ...
    id: str | None
    label: str | None
    db_reference: DbReferenceType | None
    intact_id: str | None
    def __init__(self, id=..., label=..., db_reference=..., intact_id=...) -> None: ...

@dataclass
class LigandPartType:
    class Meta:
        name = ...
    name: str | None
    db_reference: DbReferenceType | None
    label: str | None
    note: str | None
    def __init__(self, name=..., db_reference=..., label=..., note=...) -> None: ...

@dataclass
class LigandType:
    class Meta:
        name = ...
    name: str | None
    db_reference: DbReferenceType | None
    label: str | None
    note: str | None
    def __init__(self, name=..., db_reference=..., label=..., note=...) -> None: ...

@dataclass
class LocationType:
    class Meta:
        name = ...
    begin: PositionType | None
    end: PositionType | None
    position: PositionType | None
    sequence: str | None
    def __init__(self, begin=..., end=..., position=..., sequence=...) -> None: ...

@dataclass
class OrganismType:
    class Meta:
        name = ...
    name: list[OrganismNameType]
    db_reference: list[DbReferenceType]
    lineage: OrganismType.Lineage | None
    evidence: list[int]
    @dataclass
    class Lineage:
        taxon: list[str] = field(default_factory=list, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'min_occurs': 1})
    def __init__(self, name=..., db_reference=..., lineage=..., evidence=...) -> None: ...

@dataclass
class PhysiologicalReactionType:
    class Meta:
        name = ...
    db_reference: DbReferenceType | None
    direction: PhysiologicalReactionTypeDirection | None
    evidence: list[int]
    def __init__(self, db_reference=..., direction=..., evidence=...) -> None: ...

@dataclass
class ReactionType:
    class Meta:
        name = ...
    text: str | None
    db_reference: list[DbReferenceType]
    evidence: list[int]
    def __init__(self, text=..., db_reference=..., evidence=...) -> None: ...

@dataclass
class SourceType:
    class Meta:
        name = ...
    db_reference: DbReferenceType | None
    ref: int | None
    def __init__(self, db_reference=..., ref=...) -> None: ...

@dataclass
class CommentType:
    class Meta:
        name = ...
    molecule: MoleculeType | None
    absorption: CommentType.Absorption | None
    kinetics: CommentType.Kinetics | None
    ph_dependence: CommentType.PhDependence | None
    redox_potential: CommentType.RedoxPotential | None
    temperature_dependence: CommentType.TemperatureDependence | None
    reaction: ReactionType | None
    physiological_reaction: list[PhysiologicalReactionType]
    cofactor: list[CofactorType]
    subcellular_location: list[SubcellularLocationType]
    conflict: CommentType.Conflict | None
    link: list['CommentType.Link']
    event: list[EventType]
    isoform: list[IsoformType]
    interactant: list[InteractantType]
    organisms_differ: bool | None
    experiments: int | None
    disease: CommentType.Disease | None
    location: list[LocationType]
    text: list[EvidencedStringType]
    type_value: CommentTypeType | None
    location_type: str | None
    name: str | None
    mass: float | None
    error: str | None
    method: str | None
    evidence: list[int]
    @dataclass
    class Conflict:
        sequence: CommentType.Conflict.Sequence | None = field(default=None, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        type_value: ConflictType | None = field(default=None, metadata={'name': 'type', 'type': 'Attribute', 'required': True})
        ref: str | None = field(default=None, metadata={'type': 'Attribute'})
        @dataclass
        class Sequence:
            resource: SequenceResource | None = field(default=None, metadata={'type': 'Attribute', 'required': True})
            id: str | None = field(default=None, metadata={'type': 'Attribute', 'required': True})
            version: int | None = field(default=None, metadata={'type': 'Attribute'})
        def __init__(self, sequence=..., type_value=..., ref=...) -> None: ...
    @dataclass
    class Disease:
        name: str | None = field(default=None, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
        acronym: str | None = field(default=None, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
        description: str | None = field(default=None, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
        db_reference: DbReferenceType | None = field(default=None, metadata={'name': 'dbReference', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'required': True})
        id: str | None = field(default=None, metadata={'type': 'Attribute', 'required': True})
    @dataclass
    class Link:
        uri: str | None = field(default=None, metadata={'type': 'Attribute', 'required': True})
    @dataclass
    class Absorption:
        max: EvidencedStringType | None = field(default=None, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        text: list[EvidencedStringType] = field(default_factory=list, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
    @dataclass
    class Kinetics:
        km: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'KM', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        vmax: list[EvidencedStringType] = field(default_factory=list, metadata={'name': 'Vmax', 'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
        text: list[EvidencedStringType] = field(default_factory=list, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot'})
    @dataclass
    class PhDependence:
        text: list[EvidencedStringType] = field(default_factory=list, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'min_occurs': 1})
    @dataclass
    class RedoxPotential:
        text: list[EvidencedStringType] = field(default_factory=list, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'min_occurs': 1})
    @dataclass
    class TemperatureDependence:
        text: list[EvidencedStringType] = field(default_factory=list, metadata={'type': 'Element', 'namespace': 'http://uniprot.org/uniprot', 'min_occurs': 1})
    def __init__(self, molecule=..., absorption=..., kinetics=..., ph_dependence=..., redox_potential=..., temperature_dependence=..., reaction=..., physiological_reaction=..., cofactor=..., subcellular_location=..., conflict=..., link=..., event=..., isoform=..., interactant=..., organisms_differ=..., experiments=..., disease=..., location=..., text=..., type_value=..., location_type=..., name=..., mass=..., error=..., method=..., evidence=...) -> None: ...

@dataclass
class EvidenceType:
    class Meta:
        name = ...
    source: SourceType | None
    imported_from: ImportedFromType | None
    type_value: str | None
    key: int | None
    def __init__(self, source=..., imported_from=..., type_value=..., key=...) -> None: ...

@dataclass
class FeatureType:
    class Meta:
        name = ...
    original: str | None
    variation: list[str]
    location: LocationType | None
    ligand: LigandType | None
    ligand_part: LigandPartType | None
    type_value: FeatureTypeType | None
    id: str | None
    description: str | None
    evidence: list[int]
    ref: str | None
    def __init__(self, original=..., variation=..., location=..., ligand=..., ligand_part=..., type_value=..., id=..., description=..., evidence=..., ref=...) -> None: ...

@dataclass
class ReferenceType:
    class Meta:
        name = ...
    citation: CitationType | None
    scope: list[str]
    source: SourceDataType | None
    evidence: list[int]
    key: str | None
    def __init__(self, citation=..., scope=..., source=..., evidence=..., key=...) -> None: ...

@dataclass
class Entry:
    class Meta:
        name = ...
        namespace = ...
    accession: list[str]
    name: list[str]
    protein: ProteinType | None
    gene: list[GeneType]
    organism: OrganismType | None
    organism_host: list[OrganismType]
    gene_location: list[GeneLocationType]
    reference: list[ReferenceType]
    comment: list[CommentType]
    db_reference: list[DbReferenceType]
    protein_existence: ProteinExistenceType | None
    keyword: list[KeywordType]
    feature: list[FeatureType]
    evidence: list[EvidenceType]
    sequence: SequenceType1 | None
    dataset: EntryDataset | None
    created: XmlDate | None
    modified: XmlDate | None
    version: int | None
    def __init__(self, accession=..., name=..., protein=..., gene=..., organism=..., organism_host=..., gene_location=..., reference=..., comment=..., db_reference=..., protein_existence=..., keyword=..., feature=..., evidence=..., sequence=..., dataset=..., created=..., modified=..., version=...) -> None: ...

@dataclass
class Uniprot:
    class Meta:
        name = ...
        namespace = ...
    entry: list[Entry]
    copyright: Copyright | None
    def __init__(self, entry=..., copyright=...) -> None: ...
