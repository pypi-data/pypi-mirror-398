import amsdal_glue as glue
from amsdal_data.application import AsyncDataApplication
from amsdal_data.application import DataApplication
from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction
from amsdal_data.transactions.errors import AmsdalTransactionError
from amsdal_models.classes.class_manager import ClassManager
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS


@transaction
def rollback_to_timestamp(timestamp: float) -> None:
    """
    Rollback the data to the given timestamp
    Args:
        timestamp (float): The timestamp to rollback the data to.
    Returns:
        None
    """
    class_manager = ClassManager()

    lakehouse_connection = (
        DataApplication()._application.lakehouse_connection_manager.get_connection_pool('Company').get_connection()
    )

    metadatas_to_delete = lakehouse_connection.query(
        query=glue.QueryStatement(
            table=glue.SchemaReference(name='Metadata', version=glue.Version.LATEST),
            where=glue.Conditions(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(field=glue.Field(name='updated_at'), table_name='Metadata'),
                    ),
                    lookup=glue.FieldLookup.GT,
                    right=glue.Value(timestamp),
                ),
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(
                            field=glue.Field(name='prior_version'),
                            table_name='Metadata',
                        ),
                    ),
                    lookup=glue.FieldLookup.ISNULL,
                    right=glue.Value(True),
                ),
            ),
        )
    )

    ids_to_ignore = [m.data['object_id'] for m in metadatas_to_delete]

    metadatas_to_revert = lakehouse_connection.query(
        query=glue.QueryStatement(
            table=glue.SchemaReference(name='Metadata', version=glue.Version.LATEST),
            where=glue.Conditions(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(field=glue.Field(name='updated_at'), table_name='Metadata'),
                    ),
                    lookup=glue.FieldLookup.GT,
                    right=glue.Value(timestamp),
                ),
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(
                            field=glue.Field(name='prior_version'),
                            table_name='Metadata',
                        ),
                    ),
                    lookup=glue.FieldLookup.ISNULL,
                    right=glue.Value(False),
                ),
            ),
        )
    )

    transaction_ids = {m.data['transaction']['ref']['object_id'] for m in metadatas_to_revert}
    transaction_ids.update({m.data['transaction']['ref']['object_id'] for m in metadatas_to_delete})
    ids_to_revert = [
        (m.data['object_id'], m.data['class_schema_reference']['ref']['object_id'])
        for m in metadatas_to_revert
        if m.data['object_id'] not in ids_to_ignore
    ]

    if transaction_ids:
        _conditions = []
        for transaction_id in transaction_ids:
            _parent_field = glue.Field(
                name='transaction',
                child=glue.Field(
                    name='ref',
                    child=glue.Field(name='object_id'),
                ),
            )
            _parent_field.child.parent = _parent_field  # type: ignore[union-attr]
            _parent_field.child.child.parent = _parent_field.child  # type: ignore[union-attr]
            _conditions.append(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(field=_parent_field, table_name='Metadata'),
                        output_type=str,
                    ),
                    lookup=glue.FieldLookup.EQ,
                    right=glue.Value(transaction_id, output_type=str),
                )
            )

        conflict_metadata = lakehouse_connection.query(
            query=glue.QueryStatement(
                table=glue.SchemaReference(name='Metadata', version=glue.Version.LATEST),
                where=glue.Conditions(
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name='updated_at'),
                                table_name='Metadata',
                            ),
                        ),
                        lookup=glue.FieldLookup.LTE,
                        right=glue.Value(timestamp),
                    ),
                    glue.Conditions(*_conditions, connector=glue.FilterConnector.OR),
                ),
            )
        )
        if conflict_metadata:
            msg = 'Cannot rollback to this timestamp because it will conflict with other transactions'
            raise AmsdalTransactionError(msg)

    for m in metadatas_to_delete:
        class_name = m.data['class_schema_reference']['ref']['object_id']
        model_class = class_manager.import_class(class_name)
        obj = (
            model_class.objects.filter(_address__object_id=m.data['object_id'])
            .using(LAKEHOUSE_DB_ALIAS)
            .latest()
            .first()
            .execute()
        )

        if obj and not obj.get_metadata().is_deleted:
            obj.delete()

    for object_id, class_name in ids_to_revert:
        model_class = class_manager.import_class(class_name)

        obj = (
            model_class.objects.filter(_address__object_id=object_id)
            .using(LAKEHOUSE_DB_ALIAS)
            .latest()
            .first()
            .execute()
        )
        old_obj = obj.previous_version()  # type: ignore[union-attr]
        # old_obj = (
        #     model_class.objects.filter(_address__object_id=object_id, _metadata__updated_at__lte=timestamp)
        #     .using(LAKEHOUSE_DB_ALIAS)
        #     .order_by('-_metadata__updated_at')
        #     .first()
        #     .execute()
        # )

        if obj and old_obj:
            for field, value in old_obj.model_dump().items():
                setattr(obj, field, value)

            obj.save()

            if old_obj.get_metadata().is_deleted:
                obj.delete()


@transaction
def rollback_transaction(transaction_id: str) -> None:
    """
    Rollback the data to the point in time before the given transaction
    Args:
        transaction_id (str): The transaction ID to rollback the data to.
    Returns:
        None
    """

    lakehouse_connection = (
        DataApplication()._application.lakehouse_connection_manager.get_connection_pool('Company').get_connection()
    )

    _parent_field = glue.Field(
        name='transaction',
        child=glue.Field(
            name='ref',
            child=glue.Field(name='object_id'),
        ),
    )
    _parent_field.child.parent = _parent_field  # type: ignore[union-attr]
    _parent_field.child.child.parent = _parent_field.child  # type: ignore[union-attr]

    metadatas_to_revert = lakehouse_connection.query(
        query=glue.QueryStatement(
            table=glue.SchemaReference(name='Metadata', version=glue.Version.LATEST),
            where=glue.Conditions(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(field=_parent_field, table_name='Metadata'),
                        output_type=str,
                    ),
                    lookup=glue.FieldLookup.EQ,
                    right=glue.Value(transaction_id, output_type=str),
                )
            ),
            order_by=[
                glue.OrderByQuery(
                    field=glue.FieldReference(field=glue.Field(name='updated_at'), table_name='Metadata'),
                    direction=glue.OrderDirection.DESC,
                )
            ],
        )
    )

    if not metadatas_to_revert:
        msg = 'Transaction not found'
        raise AmsdalTransactionError(msg)

    updated_at = metadatas_to_revert[0].data['updated_at']
    rollback_to_timestamp(updated_at)


@async_transaction
async def async_rollback_to_timestamp(timestamp: float) -> None:
    """
    Rollback the data to the given timestamp
    Args:
        timestamp (float): The timestamp to rollback the data to.
    Returns:
        None
    """
    class_manager = ClassManager()

    lakehouse_connection = await (
        AsyncDataApplication()._application.lakehouse_connection_manager.get_connection_pool('Company').get_connection()
    )

    metadatas_to_delete = await lakehouse_connection.query(
        query=glue.QueryStatement(
            table=glue.SchemaReference(name='Metadata', version=glue.Version.LATEST),
            where=glue.Conditions(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(field=glue.Field(name='updated_at'), table_name='Metadata'),
                    ),
                    lookup=glue.FieldLookup.GT,
                    right=glue.Value(timestamp),
                ),
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(
                            field=glue.Field(name='prior_version'),
                            table_name='Metadata',
                        ),
                    ),
                    lookup=glue.FieldLookup.ISNULL,
                    right=glue.Value(True),
                ),
            ),
        )
    )

    ids_to_ignore = [m.data['object_id'] for m in metadatas_to_delete]

    metadatas_to_revert = await lakehouse_connection.query(
        query=glue.QueryStatement(
            table=glue.SchemaReference(name='Metadata', version=glue.Version.LATEST),
            where=glue.Conditions(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(field=glue.Field(name='updated_at'), table_name='Metadata'),
                    ),
                    lookup=glue.FieldLookup.GT,
                    right=glue.Value(timestamp),
                ),
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(
                            field=glue.Field(name='prior_version'), table_name='Metadata'
                        ),
                    ),
                    lookup=glue.FieldLookup.ISNULL,
                    right=glue.Value(False),
                ),
            ),
        )
    )

    transaction_ids = {m.data['transaction']['ref']['object_id'] for m in metadatas_to_revert}
    transaction_ids.update({m.data['transaction']['ref']['object_id'] for m in metadatas_to_delete})
    ids_to_revert = [
        (m.data['object_id'], m.data['class_schema_reference']['ref']['object_id'])
        for m in metadatas_to_revert
        if m.data['object_id'] not in ids_to_ignore
    ]

    if transaction_ids:
        _conditions = []
        for transaction_id in transaction_ids:
            _parent_field = glue.Field(
                name='transaction',
                child=glue.Field(
                    name='ref',
                    child=glue.Field(name='object_id'),
                ),
            )
            _parent_field.child.parent = _parent_field  # type: ignore[union-attr]
            _parent_field.child.child.parent = _parent_field.child  # type: ignore[union-attr]
            _conditions.append(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(field=_parent_field, table_name='Metadata'),
                        output_type=str,
                    ),
                    lookup=glue.FieldLookup.EQ,
                    right=glue.Value(transaction_id, output_type=str),
                )
            )

        conflict_metadata = await lakehouse_connection.query(
            query=glue.QueryStatement(
                table=glue.SchemaReference(name='Metadata', version=glue.Version.LATEST),
                where=glue.Conditions(
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name='updated_at'),
                                table_name='Metadata',
                            ),
                        ),
                        lookup=glue.FieldLookup.LTE,
                        right=glue.Value(timestamp),
                    ),
                    glue.Conditions(*_conditions, connector=glue.FilterConnector.OR),
                ),
            )
        )
        if conflict_metadata:
            msg = 'Cannot rollback to this timestamp because it will conflict with other transactions'
            raise AmsdalTransactionError(msg)

    for m in metadatas_to_delete:
        class_name = m.data['class_schema_reference']['ref']['object_id']
        model_class = class_manager.import_class(class_name)
        obj = await (
            model_class.objects.filter(_address__object_id=m.data['object_id'])
            .using(LAKEHOUSE_DB_ALIAS)
            .latest()
            .first()
            .aexecute()
        )

        if obj and not (await obj.aget_metadata()).is_deleted:
            await obj.adelete()

    for object_id, class_name in ids_to_revert:
        model_class = class_manager.import_class(class_name)

        obj = await (
            model_class.objects.filter(_address__object_id=object_id)
            .using(LAKEHOUSE_DB_ALIAS)
            .latest()
            .first()
            .aexecute()
        )
        old_obj = await obj.aprevious_version()  # type: ignore[union-attr]
        # old_obj = await (
        #     model_class.objects.filter(_address__object_id=object_id, _metadata__updated_at__lte=timestamp)
        #     .using(LAKEHOUSE_DB_ALIAS)
        #     .order_by('-_metadata__updated_at')
        #     .first()
        #     .aexecute()
        # )

        if obj and old_obj:
            for field, value in (await old_obj.amodel_dump()).items():
                setattr(obj, field, value)

            await obj.asave()

            if (await old_obj.aget_metadata()).is_deleted:
                await obj.adelete()


@async_transaction
async def async_rollback_transaction(transaction_id: str) -> None:
    """
    Rollback the data to the point in time before the given transaction
    Args:
        transaction_id (str): The transaction ID to rollback the data to.
    Returns:
        None
    """
    lakehouse_connection = await (
        AsyncDataApplication()._application.lakehouse_connection_manager.get_connection_pool('Company').get_connection()
    )

    _parent_field = glue.Field(
        name='transaction',
        child=glue.Field(
            name='ref',
            child=glue.Field(name='object_id'),
        ),
    )
    _parent_field.child.parent = _parent_field  # type: ignore[union-attr]
    _parent_field.child.child.parent = _parent_field.child  # type: ignore[union-attr]

    metadatas_to_revert = await lakehouse_connection.query(
        query=glue.QueryStatement(
            table=glue.SchemaReference(name='Metadata', version=glue.Version.LATEST),
            where=glue.Conditions(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(field=_parent_field, table_name='Metadata'),
                        output_type=str,
                    ),
                    lookup=glue.FieldLookup.EQ,
                    right=glue.Value(transaction_id, output_type=str),
                )
            ),
            order_by=[
                glue.OrderByQuery(
                    field=glue.FieldReference(field=glue.Field(name='updated_at'), table_name='Metadata'),
                    direction=glue.OrderDirection.DESC,
                )
            ],
        )
    )

    if not metadatas_to_revert:
        msg = 'Transaction not found'
        raise AmsdalTransactionError(msg)

    updated_at = metadatas_to_revert[0].data['updated_at']
    await async_rollback_to_timestamp(updated_at)  # type: ignore[misc]
