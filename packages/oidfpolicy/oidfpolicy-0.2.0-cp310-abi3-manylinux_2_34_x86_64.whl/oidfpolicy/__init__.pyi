def merge_policies(tapolicy: str, iapolicy: str) -> str:
    """Merges tapolicy on top of iapolicy and returns the merged policy.

    :param tapolicy: JSON Policy from Trust Anchor in str
    :param iapolicy: JSON Policy from Trust Anchor in str

    :return: str representation of merged policy.
    """

def apply_policy(policy: str, metadata: str) -> str:
    """Applies the given policy on the metadata.

    :param policy: Merged olicy from Root -> IA
    :param metadata: str, the metadata JSON

    :return: str representation of policy applied metadata.
    """
