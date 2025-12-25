import os

from workbench_data_pipeline import WorkbenchDataPipeline

if __name__ == "__main__":

    WORKBENCH_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolomics_workbench"
    )

    WORKBENCH_CSV_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolomics_workbench", "WORKBENCH.csv"
    )

    WORKBENCH_FILTERED_CSV_PATH = os.path.join(
        "datasets",
        "disease_datasets",
        "metabolomics_workbench",
        "WORKBENCH_filtered.csv",
    )

    WORKBENCH_RAW_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolomics_workbench", "raw_human_only"
    )

    WORKBENCH_PARSED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolomics_workbench", "00_parsed_human_only"
    )

    WORKBENCH_FILTERED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets",
        "disease_datasets",
        "metabolomics_workbench",
        "01_filtered_human_only",
    )

    WORKBENCH_MERGED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolomics_workbench", "02_merged_human_only"
    )

    WORKBENCH_MAPPED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolomics_workbench", "03_mapped_human_only"
    )

    WORKBENCH_FILTERED_STUDY_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets",
        "disease_datasets",
        "metabolomics_workbench",
        "04_filtered_study_human_only",
    )

    WORKBENCH_RANDOM_FILLED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets",
        "disease_datasets",
        "metabolomics_workbench",
        "05_random_filled_human_only",
    )

    WORKBENCH_NORMALIZED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets",
        "disease_datasets",
        "metabolomics_workbench",
        "06_normalized_human_only",
    )

    pipeline = WorkbenchDataPipeline(working_dir=os.getcwd(), verbose=True)

    # RAW FILES
    # pipeline._download_raw_homo_sapiens(
    #     destination_path=WORKBENCH_RAW_HUMAN_ONLY_DATA_PATH
    # )

    # NAME MAPPING
    # pipeline._get_metabolite_ids(destination_path=WORKBENCH_DATA_PATH)
    # pipeline._convert_mapping(
    #     mapping_path=os.path.join(WORKBENCH_DATA_PATH, "workbench-mapping.json"),
    #     output_path=WORKBENCH_DATA_PATH,
    # )
    pipeline._reverse_mapping(
        mapping_path=os.path.join(WORKBENCH_DATA_PATH, "workbench-mapping.json"),
        output_path=WORKBENCH_DATA_PATH,
    )

    # MAIN PIPELINE
    # pipeline._download_parsed_homo_sapiens(
    #     destination_path=WORKBENCH_PARSED_HUMAN_ONLY_DATA_PATH
    # )
    # pipeline._filter_studies(
    #     input_path=WORKBENCH_PARSED_HUMAN_ONLY_DATA_PATH,
    #     output_path=WORKBENCH_FILTERED_HUMAN_ONLY_DATA_PATH,
    #     metabolite_drop_count=50,
    # )
    # pipeline._merge_analyses(
    #     input_path=WORKBENCH_FILTERED_HUMAN_ONLY_DATA_PATH,
    #     output_path=WORKBENCH_MERGED_HUMAN_ONLY_DATA_PATH,
    # )
    # pipeline._apply_mapping(
    #     mapping_name="new-synonym",
    #     mode="files",
    #     input_path=WORKBENCH_MERGED_HUMAN_ONLY_DATA_PATH,
    #     output_path=WORKBENCH_MAPPED_HUMAN_ONLY_DATA_PATH,
    # )
    # pipeline._filter_patients(
    #     input_path=WORKBENCH_MAPPED_HUMAN_ONLY_DATA_PATH,
    #     output_path=WORKBENCH_FILTERED_STUDY_HUMAN_ONLY_DATA_PATH,
    #     metabolite_drop_count=50,
    # )
    # pipeline._fill_missing(
    #     mode="files",
    #     input_path=WORKBENCH_FILTERED_STUDY_HUMAN_ONLY_DATA_PATH,
    #     output_path=WORKBENCH_RANDOM_FILLED_HUMAN_ONLY_DATA_PATH,
    # )
    # pipeline._normalize(
    #     mode="files",
    #     input_path=WORKBENCH_RANDOM_FILLED_HUMAN_ONLY_DATA_PATH,
    #     output_path=WORKBENCH_NORMALIZED_HUMAN_ONLY_DATA_PATH,
    # )
    # pipeline._create_workbench_csv(
    #     input_path=WORKBENCH_NORMALIZED_HUMAN_ONLY_DATA_PATH,
    #     output_path=WORKBENCH_DATA_PATH,
    # )
    # pipeline._filter_workbench_csv(
    #     input_path=WORKBENCH_CSV_PATH,
    #     output_path=WORKBENCH_FILTERED_CSV_PATH,
    #     metabolite_drop_count=50,
    #     patient_drop_count=50,
    # )
