DESCRIPTION_QUERY_TPL = """
    SELECT Description
    FROM EntityDefinition
    WHERE QualifiedApiName = '{table_name}'
"""

SOBJECTS_QUERY_TPL = """
    SELECT
        DeveloperName,
        DurableId,
        ExternalSharingModel,
        InternalSharingModel,
        Label,
        PluralLabel,
        QualifiedApiName
    FROM EntityDefinition
    WHERE DurableId > '{start_durable_id}'
    ORDER BY DurableId
    LIMIT {limit}
"""

SOBJECT_FIELDS_QUERY_TPL = """
    SELECT
        DataType,
        DeveloperName,
        Digits,
        FieldDefinition.BusinessOwnerId,
        FieldDefinition.ComplianceGroup,
        FieldDefinition.DataType,
        FieldDefinition.Description,
        FieldDefinition.IsIndexed,
        FieldDefinition.LastModifiedBy.Username,
        FieldDefinition.LastModifiedDate,
        FieldDefinition.SecurityClassification,
        InlineHelpText,
        IsComponent,
        IsCompound,
        IsNillable,
        IsUnique,
        Label,
        Length,
        Precision,
        QualifiedApiName,
        ReferenceTo,
        RelationshipName,
        Scale
    FROM EntityParticle
    WHERE EntityDefinitionId='{entity_definition_id}'
"""
