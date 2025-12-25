import json

from oidfpolicy import apply_policy, merge_policies


class TestMergePolicies:
    def test_merging_policies(self, tapolicy0, iapolicy0, policymerge0):
        merged = merge_policies(tapolicy0, iapolicy0)
        data = json.loads(merged)
        assert data == policymerge0

    def test_merging_policies_with_other_types(
        self, tapolicy1, iapolicy1, policymerge1
    ):
        merged = merge_policies(tapolicy1, iapolicy1)
        data = json.loads(merged)
        assert data == policymerge1


class TestApplyPolicy:
    def test_apply_policy(self, merged_policy0, metadata0, applied_metadata0):
        applied = json.loads(apply_policy(merged_policy0, metadata0))
        assert applied["openid_relying_party"] == applied_metadata0
