PREFER = 'Prefer'
PREFERENCE_RESPOND_ASYNC = 'respond-async'


def preference(with_wait: int | None = None) -> str:
    if with_wait:
        return f'{PREFERENCE_RESPOND_ASYNC}, wait={with_wait}'
    else:
        return PREFERENCE_RESPOND_ASYNC
