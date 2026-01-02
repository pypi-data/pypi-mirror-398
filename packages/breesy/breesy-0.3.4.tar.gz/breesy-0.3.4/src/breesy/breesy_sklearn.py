from sklearn.decomposition import FastICA

from breesy.errors import protect_from_lib_error


@protect_from_lib_error("sklearn")
def _sklearn_fastica(n_components: int, random_state: int | None = None) -> FastICA:
    return FastICA(n_components=n_components, whiten='unit-variance',
                   max_iter=1000, random_state=random_state)


# TODO: add picard ICA (from the picard package)