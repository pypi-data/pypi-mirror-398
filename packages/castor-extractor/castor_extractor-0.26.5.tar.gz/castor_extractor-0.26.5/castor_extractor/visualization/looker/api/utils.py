from collections.abc import Iterable

from looker_sdk.sdk.api40.models import LookmlModel


def lookml_explore_names(
    lookmls: Iterable[LookmlModel],
) -> set[tuple[str, str]]:
    """
    Explores from the lookml models
    Only valid explores are yielded: with all infos
    """
    model_explores = (
        (model, explore)
        for model in lookmls
        for explore in model.explores or []
    )

    return {
        (model.name, explore.name)
        for model, explore in model_explores
        # accept hidden resources
        if model.name and explore.name
    }
