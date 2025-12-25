import os

from metabolights_data_pipeline import MetaboLightsDataPipeline

if __name__ == "__main__":
    METABOLIGHTS_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights"
    )

    METABOLIGHTS_METADATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "metabolights_metadata.json"
    )

    METABOLIGHTS_RAW_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "raw"
    )

    METABOLIGHTS_RAW_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "raw_human_only"
    )

    METABOLIGHTS_PARSED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "00_parsed_human_only"
    )

    METABOLIGHTS_FILTERED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "01_filtered_human_only"
    )

    METABOLIGHTS_MERGED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "02_merged_human_only"
    )

    METABOLIGHTS_MAPPED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "03_mapped_human_only"
    )

    METABOLIGHTS_FILTERED_STUDY_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "04_filtered_study_human_only"
    )

    METABOLIGHTS_RANDOM_FILLED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "05_random_filled_human_only"
    )

    METABOLIGHTS_NORMALIZED_HUMAN_ONLY_DATA_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "06_normalized_human_only"
    )

    METABOLIGHTS_CSV_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "METABOLIGHTS.csv"
    )

    METABOLIGHTS_FILTERED_CSV_PATH = os.path.join(
        "datasets", "disease_datasets", "metabolights", "METABOLIGHTS_filtered.csv"
    )

    ftp_url = "ftp.ebi.ac.uk"

    # Example usage
    pipeline = MetaboLightsDataPipeline(working_dir=os.getcwd())

    # Perform the steps in the pipeline

    # pipeline._download_tsv_files(
    #     ftp_url=ftp_url, destination_folder=METABOLIGHTS_RAW_DATA_PATH
    # )
    # pipeline._extract_metadata(
    #     input_path=METABOLIGHTS_RAW_DATA_PATH,
    #     output_path=METABOLIGHTS_DATA_PATH,
    #     verbose=True,
    # )
    # pipeline._seperate_homosapiens(
    #     metadata_path=METABOLIGHTS_METADATA_PATH,
    #     input_path=METABOLIGHTS_RAW_DATA_PATH,
    #     output_path=METABOLIGHTS_RAW_HUMAN_ONLY_DATA_PATH,
    #     verbose=True,
    # )
    # pipeline._parser(
    #     input_path=METABOLIGHTS_RAW_HUMAN_ONLY_DATA_PATH,
    #     output_path=METABOLIGHTS_PARSED_HUMAN_ONLY_DATA_PATH,
    #     verbose=True,
    # )
    # pipeline._filter_folders(
    #     input_path=METABOLIGHTS_PARSED_HUMAN_ONLY_DATA_PATH,
    #     output_path=METABOLIGHTS_FILTERED_HUMAN_ONLY_DATA_PATH,
    #     metabolite_drop_count=50,
    #     verbose=True,
    # )
    # pipeline._create_study_csv(
    #     input_path=METABOLIGHTS_FILTERED_HUMAN_ONLY_DATA_PATH,
    #     output_path=METABOLIGHTS_MERGED_HUMAN_ONLY_DATA_PATH,
    #     verbose=True,
    # )
    # pipeline._apply_mapping(
    #     mapping_name="new-synonym",
    #     mode="files",
    #     input_path=METABOLIGHTS_MERGED_HUMAN_ONLY_DATA_PATH,
    #     output_path=METABOLIGHTS_MAPPED_HUMAN_ONLY_DATA_PATH,
    # )
    # pipeline._filter_patients(
    #     input_path=METABOLIGHTS_MAPPED_HUMAN_ONLY_DATA_PATH,
    #     output_path=METABOLIGHTS_FILTERED_STUDY_HUMAN_ONLY_DATA_PATH,
    #     metabolite_drop_count=50,
    #     verbose=True,
    # )
    # pipeline._fill_missing(
    #     mode="files",
    #     input_path=METABOLIGHTS_FILTERED_STUDY_HUMAN_ONLY_DATA_PATH,
    #     output_path=METABOLIGHTS_RANDOM_FILLED_HUMAN_ONLY_DATA_PATH,
    #     verbose=True,
    # )
    # pipeline._normalize(
    #     mode="files",
    #     input_path=METABOLIGHTS_RANDOM_FILLED_HUMAN_ONLY_DATA_PATH,
    #     output_path=METABOLIGHTS_NORMALIZED_HUMAN_ONLY_DATA_PATH,
    #     verbose=True,
    # )
    # pipeline._create_metabolights_csv(
    #     input_path=METABOLIGHTS_NORMALIZED_HUMAN_ONLY_DATA_PATH,
    #     output_path=METABOLIGHTS_DATA_PATH,
    #     verbose=True,
    # )
    # pipeline._filter_metabolights_csv(
    #     input_path=METABOLIGHTS_CSV_PATH,
    #     output_path=METABOLIGHTS_FILTERED_CSV_PATH,
    #     metabolite_drop_count=50,
    #     patient_drop_count=50,
    #     verbose=True,
    # )
