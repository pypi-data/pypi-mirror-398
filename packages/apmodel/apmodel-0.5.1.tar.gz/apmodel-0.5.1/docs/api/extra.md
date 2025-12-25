# Extra Models

`apmodel` includes models for vocabularies beyond the core ActivityStreams 2.0 specification.

## Security Vocabulary (`security`)

Models related to data integrity and cryptographic keys.

::: apmodel.extra.security.cryptographickey.CryptographicKey
    options:
      show_root_heading: true

## Data Integrity and Multikey (`cid`)

Models for W3C Data Integrity specifications.

::: apmodel.extra.cid.data_integrity_proof.DataIntegrityProof
    options:
      show_root_heading: true

::: apmodel.extra.cid.multikey.Multikey
    options:
      show_root_heading: true

## Schema.org Extensions (`schema`)

Models from the `schema.org` vocabulary.

::: apmodel.extra.schema.propertyvalue.PropertyValue
    options:
      show_root_heading: true

## Other Extensions

Commonly used extensions from platforms like Mastodon.

::: apmodel.extra.emoji.Emoji
    options:
      show_root_heading: true

::: apmodel.extra.hashtag.Hashtag
    options:
      show_root_heading: true
