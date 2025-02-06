from ckan.logic.schema import validator_args


@validator_args
def datatables_view_prioritize(not_empty):
    return {
        "resource_id": [
            not_empty,
        ],
    }
