from deepdiff import DeepDiff
import yaml


def compare_yaml_with_deepdiff(yaml_str1, yaml_str2):
    dict1 = yaml.safe_load(yaml_str1)
    dict2 = yaml.safe_load(yaml_str2)
    diff = DeepDiff(dict1, dict2, ignore_order=True)
    return diff
