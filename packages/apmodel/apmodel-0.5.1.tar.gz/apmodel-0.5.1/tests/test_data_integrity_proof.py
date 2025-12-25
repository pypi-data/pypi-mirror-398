import datetime

from apmodel.extra.cid import DataIntegrityProof


def test_data_integrity_proof_creation():
    # Test creating a DataIntegrityProof instance
    proof = DataIntegrityProof(
        cryptosuite="eddsa-jcs-2022",
        proof_value="zQeVbY4gaN5u643UW5F7",
        proof_purpose="assertionMethod",
        verification_method="did:example:123#key-1",
        created="2023-01-01T00:00:00Z",
    )

    assert proof.cryptosuite == "eddsa-jcs-2022"
    assert proof.proof_value == "zQeVbY4gaN5u643UW5F7"
    assert proof.proof_purpose == "assertionMethod"
    assert proof.verification_method == "did:example:123#key-1"
    assert isinstance(proof.created, datetime.datetime)


def test_data_integrity_proof_default_values():
    # Test creating a DataIntegrityProof instance with default values
    proof = DataIntegrityProof(
        cryptosuite="eddsa-jcs-2022",
        proof_value="zQeVbY4gaN5u643UW5F7",
        proof_purpose="assertionMethod",
        verification_method="did:example:123#key-1",
        created="2023-01-01T00:00:00Z",
    )

    assert proof.type == "DataIntegrityProof"


def test_data_integrity_proof_datetime_conversion():
    # Test datetime conversion from string
    proof = DataIntegrityProof(
        cryptosuite="eddsa-jcs-2022",
        proof_value="zQeVbY4gaN5u643UW5F7",
        proof_purpose="assertionMethod",
        verification_method="did:example:123#key-1",
        created="2023-01-01T12:30:45Z",
    )

    assert isinstance(proof.created, datetime.datetime)
    assert proof.created.year == 2023
    assert proof.created.month == 1
    assert proof.created.day == 1
    assert proof.created.hour == 12
    assert proof.created.minute == 30
    assert proof.created.second == 45


def test_data_integrity_proof_datetime_object():
    dt = datetime.datetime(2023, 1, 1, 12, 30, 45, tzinfo=datetime.timezone.utc)
    proof = DataIntegrityProof(
        cryptosuite="eddsa-jcs-2022",
        proof_value="zQeVbY4gaN5u643UW5F7",
        proof_purpose="assertionMethod",
        verification_method="did:example:123#key-1",
        created=dt,
    )

    assert proof.created == dt


def test_data_integrity_proof_serialization():
    # Test serialization of created field
    proof = DataIntegrityProof(
        cryptosuite="eddsa-jcs-2022",
        proof_value="zQeVbY4gaN5u643UW5F7",
        proof_purpose="assertionMethod",
        verification_method="did:example:123#key-1",
        created="2023-01-01T12:30:45Z",
    )

    # Check that the serialized data contains the expected context
    serialized = proof.model_dump(by_alias=True)
    assert "@context" in serialized
    assert "https://www.w3.org/ns/activitystreams" in serialized["@context"]
    assert "https://w3id.org/security/data-integrity/v1" in serialized["@context"]
    assert serialized["type"] == "DataIntegrityProof"
    assert serialized["cryptosuite"] == "eddsa-jcs-2022"
    assert serialized["proofValue"] == "zQeVbY4gaN5u643UW5F7"
    assert serialized["proofPurpose"] == "assertionMethod"
    assert serialized["verificationMethod"] == "did:example:123#key-1"
    assert serialized["created"] == "2023-01-01T12:30:45Z"
