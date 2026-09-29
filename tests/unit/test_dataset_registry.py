from scripts.fetch_datasets import DATASETS


def test_dataset_registry_has_pinned_https_sources_and_distinct_directories() -> None:
    assert {"smartbugs-curated", "damn-vulnerable-defi", "defi-vuln-labs", "forge-artifacts"} <= DATASETS.keys()
    assert len({dataset.directory for dataset in DATASETS.values()}) == len(DATASETS)
    for dataset in DATASETS.values():
        assert dataset.url.startswith("https://github.com/")
        assert len(dataset.revision) == 40
