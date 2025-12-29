from wallypub.conf.app import WallabagURLParameters

"""
params.py is a utility file for managing the additional params that can be passed into wallabag requests. This should eventually
be refactored into something more dynamic and programmable rather than static files. 
"""


def get_params_from_settings(params: WallabagURLParameters) -> str:
    """
    get_params_from_settings takes in WallabagURLParameters and returns JSON.
    Why it returns JSON is the weight of an earlier decision where these parameters lived
    in discrete JSON files. This was not the ideal refactor, but it was an expedient one. A
    future refactor here is welcome.
    """

    return params.model_dump(mode="json")
