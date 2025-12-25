import json
import os
import shutil
from collections import OrderedDict

import numpy as np
import pandas as pd
import requests
from sklearn_utils.preprocessing import FeatureRenaming
from sklearn_utils.utils import SkUtilsIO

from preprocessing.metabolitics_pipeline import MetaboliticsPipeline
from utils import load_metabolite_mapping


class WorkbenchDataPipeline:
    def __init__(self, working_dir, verbose) -> None:
        self.working_dir = working_dir
        self.homo_sapiens_study_ids = []
        self.workbench_mapping = {}
        self.verbose = verbose

    ################################ STEP: DOWNLOAD ################################

    def _set_homo_sapiens_study_ids(self) -> None:
        """
        Send a GET request to the Metabolomics Workbench API and
        retrieve a list of study IDs where the Latin name is "Homo sapiens".
        """
        url = "https://www.metabolomicsworkbench.org/rest/study/study_id/ST/species"
        response = requests.get(url)
        data = response.json()

        # Extract study IDs where Latin name == "Homo sapiens"
        self.homo_sapiens_study_ids = [
            study_data["Study ID"]
            for study_data in data.values()
            if study_data["Latin name"] == "Homo sapiens"
        ]

        if self.verbose:
            print(
                f"{len(self.homo_sapiens_study_ids)} homo sapiens study IDs are retrieved from Metabolomics Workbench API."
            )

    def _get_metabolite_ids(self, destination_path: str) -> None:
        """
        Send a GET request to the Metabolomics Workbench API for each study ID in self.homo_sapiens_study_ids.
        The response for each request parsed and metabolite ids are extracted.

        Args:
            destination_path (str): The path where the JSON mapping will be saved.
        """
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        if len(self.homo_sapiens_study_ids) == 0:
            self._set_homo_sapiens_study_ids()

        base_url = "https://www.metabolomicsworkbench.org/rest/study/study_id/"

        for study_id in self.homo_sapiens_study_ids:
            url = base_url + study_id + "/data"
            try:
                print(f"Requesting study: {study_id}")
                response = requests.get(url, timeout=60)
                data = response.json()
            except requests.exceptions.Timeout:
                print(f"Timeout occurred for study {study_id}, skipping this study.")
                continue

            # If the response is an empty list, skip this iteration
            if not data:
                print(f"Skipped study {study_id}, empty study.")
                continue

            # Check if all keys have a dictionary value
            if all(
                isinstance(value, dict) for value in data.values()
            ):  # Multiple metabolite items in response dictionary

                for value in data.values():
                    if value["metabolite_id"] not in self.workbench_mapping:
                        self.workbench_mapping[value["metabolite_id"]] = []

                    self.workbench_mapping[value["metabolite_id"]].append(
                        value["metabolite_name"]
                    )
            else:  # Single metabolite data block in the response dictionary, weird
                if data["metabolite_id"] not in self.workbench_mapping:
                    self.workbench_mapping[data["metabolite_id"]] = []

                self.workbench_mapping[data["metabolite_id"]].append(
                    data["metabolite_name"]
                )

        # Save the response to a JSON file
        with open(os.path.join(destination_path, "workbench-mapping.json"), "w") as f:
            json.dump(self.workbench_mapping, f, indent=4)

    def _convert_mapping(self, mapping_path: str, output_path: str) -> None:
        """
        Converts the input mapping JSON file, orders the items by keys, and saves it to an output JSON file.

        Args:
            mapping_path (str): The file path to the input mapping JSON file.
            output_path (str): The directory where the ordered mapping JSON file will be saved.
        """
        with open(mapping_path, "r") as fp:
            self.workbench_mapping = json.load(fp)

        for key in self.workbench_mapping:
            self.workbench_mapping[key] = str(
                next(iter(set(self.workbench_mapping[key])))
            )

        # Order items by keys
        self.workbench_mapping = {
            key: value for key, value in sorted(self.workbench_mapping.items())
        }

        with open(os.path.join(output_path, "workbench-mapping.json"), "w") as f:
            json.dump(self.workbench_mapping, f, indent=4)

        print(f"Mapping JSON file has been converted.")

    def _reverse_mapping(self, mapping_path: str, output_path: str) -> None:
        with open(mapping_path, "r") as fp:
            self.workbench_mapping = json.load(fp)

        # Reverse the mapping while preserving key-value order
        reversed_mapping = OrderedDict(
            (v, k) for k, v in self.workbench_mapping.items()
        )

        with open(
            os.path.join(output_path, "workbench-reversed-mapping.json"), "w"
        ) as f:
            json.dump(reversed_mapping, f, indent=2)

        print(f"Reversed mapping JSON file has been saved.")

    def _download_raw_homo_sapiens(self, destination_path: str) -> None:
        """
        Send a GET request to the Metabolomics Workbench API for each study ID in self.homo_sapiens_study_ids.
        The response for each request is saved to a JSON file in the specified destination path.

        Args:
            destination_path (str): The path where the JSON files will be saved.
        """
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        if len(self.homo_sapiens_study_ids) == 0:
            self._set_homo_sapiens_study_ids()

        base_url = "https://www.metabolomicsworkbench.org/rest/study/study_id/"

        for study_id in self.homo_sapiens_study_ids:
            url = base_url + study_id + "/mwtab"
            response = requests.get(url)

            # There may be some problematic JSON files, 2 or more analyses in a single file
            try:
                data = response.json()
            except json.JSONDecodeError as error:  # ERROR 1
                print(f"Error parsing JSON in file {study_id}: {str(error)}")
                continue

            # Save the response to a JSON file
            study_destination_path = os.path.join(destination_path, f"{study_id}.json")

            with open(study_destination_path, "w") as f:
                json.dump(data, f, indent=4)

                if self.verbose:
                    print(
                        f"Downloaded raw data for study and saved to {study_destination_path}"
                    )

    ################################ STEP: DOWNLOAD and PARSE ################################

    def _download_parsed_homo_sapiens(self, destination_path: str) -> None:
        """
        Send a GET request to the Metabolomics Workbench API for each study ID in self.homo_sapiens_study_ids.
        The response for each request is parsed into a DataFrame and saved to a CSV file in the specified destination path.

        Args:
            destination_path (str): The path where the CSV files will be saved.
        """
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        if len(self.homo_sapiens_study_ids) == 0:
            self._set_homo_sapiens_study_ids()

        base_url = "https://www.metabolomicsworkbench.org/rest/study/study_id/"

        for study_id in self.homo_sapiens_study_ids:
            url = base_url + study_id + "/data"
            try:
                print(f"Requesting study: {study_id}")
                response = requests.get(url, timeout=60)
                data = response.json()
            except requests.exceptions.Timeout:
                print(f"Timeout occurred for study {study_id}, skipping this study.")
                continue

            # If the response is an empty list, skip this iteration
            if not data:
                print(f"Skipped study {study_id}, empty study.")
                continue

            # Check if all keys have a dictionary value
            if all(
                isinstance(value, dict) for value in data.values()
            ):  # Multiple metabolite items in response dictionary
                study_id = list(
                    set(
                        [
                            metabolite_data["study_id"]
                            for metabolite_data in data.values()
                        ]
                    )
                )[0]
                analyses_ids = list(
                    set(
                        [
                            metabolite_data["analysis_id"]
                            for metabolite_data in data.values()
                        ]
                    )
                )
                analyses_ids.sort()

                # There is a single analysis in a study for example ST000002
                if len(analyses_ids) == 1 or isinstance(analyses_ids, str):
                    # Find the patient name list with the maximum length
                    patient_names = [
                        metabolite_data["DATA"].keys()
                        for metabolite_data in data.values()
                    ]
                    max_length_patient_names = max(patient_names, key=len)
                    patient_names = [
                        patient_name for patient_name in max_length_patient_names
                    ]

                    # Record metabolites to a dictionary and create a DF
                    df = pd.DataFrame(
                        {
                            metabolite_data["metabolite_name"]: metabolite_data[
                                "DATA"
                            ].values()
                            for metabolite_data in data.values()
                            if len(metabolite_data["DATA"].keys()) == len(patient_names)
                        }
                    )
                    df.insert(0, "Factors", patient_names)

                    study_destination_path = os.path.join(
                        destination_path, f"{study_id}.csv"
                    )
                    df.to_csv(study_destination_path, index=False)

                    print(
                        f"Parsed data for study {study_id} saved to {study_destination_path}"
                    )
                else:  # Multiple analyses in a study, handle that case ST000004
                    for analysis_id in analyses_ids:
                        # Find the patient name list with the maximum length
                        patient_names = [
                            metabolite_data["DATA"].keys()
                            for metabolite_data in data.values()
                            if metabolite_data["analysis_id"] == analysis_id
                        ]
                        max_length_patient_names = max(patient_names, key=len)
                        patient_names = [
                            patient_name for patient_name in max_length_patient_names
                        ]

                        # Record metabolites to a dictionary and create a DF
                        df = pd.DataFrame(
                            {
                                metabolite_data["metabolite_name"]: metabolite_data[
                                    "DATA"
                                ].values()
                                for metabolite_data in data.values()
                                if metabolite_data["analysis_id"] == analysis_id
                                and len(metabolite_data["DATA"].keys())
                                == len(patient_names)
                            }
                        )
                        df.insert(0, "Factors", patient_names)

                        study_destination_path = os.path.join(
                            destination_path, f"{study_id}_{analysis_id}.csv"
                        )
                        df.to_csv(study_destination_path, index=False)

                        print(
                            f"Parsed data for analysis {study_id}_{analysis_id} saved to {study_destination_path}"
                        )
            else:  # Single metabolite data block in the response dictionary, weird
                study_id = data["study_id"]
                analyses_ids = data["analysis_id"]
                patient_names = data["DATA"].keys()

                # Record metabolites to a dictionary and create a DF
                df = pd.DataFrame({data["metabolite_name"]: data["DATA"].values()})
                df.insert(0, "Factors", patient_names)

                study_destination_path = os.path.join(
                    destination_path, f"{study_id}.csv"
                )
                df.to_csv(study_destination_path, index=False)

                print(
                    f"Parsed data for study {study_id} saved to {study_destination_path}"
                )

    ################################ STEP: FILTER BEFORE MERGE ################################

    @staticmethod
    def average_similar_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the average for columns with similar names, and return a DataFrame with averaged columns.

        Args:
            df (DataFrame): The input DataFrame.

        Returns:
            DataFrame: A DataFrame with columns containing averaged values.
        """
        # Create a dictionary to store the columns to be averaged
        columns_to_average = {}

        # Iterate through columns in the DataFrame
        for column in df.columns:
            base_column_name = column.split(".")[
                0
            ]  # Get the base column name (e.g., isoleucine from isoleucine.1)

            # Check if the base column name is already in the dictionary
            if base_column_name in columns_to_average:
                # Add the current column to the list of columns to be averaged
                columns_to_average[base_column_name].append(column)
            else:
                # Create a new list for the base column name and add the current column to it
                columns_to_average[base_column_name] = [column]

        # Iterate through the dictionary and calculate the average for each group of columns
        for base_column_name, columns in columns_to_average.items():
            if base_column_name != "Factors":
                df[base_column_name] = df[columns].mean(axis=1)  # Calculate the average

            if len(columns) > 1:
                drop_cols = columns[1:]
                df.drop(columns=drop_cols, inplace=True)  # Drop the original columns

        return df

    def _filter_studies(
        self,
        input_path: str,
        output_path: str,
        metabolite_drop_count: int,
    ) -> None:
        """
        Filter and process CSV files in the input directory. This function removes
        rows and columns with uninformative data, averages columns with similar names, drops rows
        where the entire row is empty.

        Args:
            input_path (str): The path to the directory containing subfolders with CSV files.
            output_path (str): The path to the output directory for filtered CSV files.
            metabolite_drop_count (int): The minimum number of metabolites required to keep a CSV file.
            verbose (bool): Turn on/off command line prints for detailed processing information.
        """
        if self.verbose:
            print(
                f"###################### STEP: FILTER BEFORE MERGE ######################"
            )

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Iterate through csv files in the folder
        for filename in os.listdir(input_path):
            if filename.endswith(".csv"):
                csv_path = os.path.join(input_path, filename)
                df = pd.read_csv(csv_path)

                # Uncaptured metabolites
                df = df.loc[:, ~df.columns.str.contains("Unnamed")]
                df = df.loc[:, ~df.columns.str.contains("unknown")]
                df = df.loc[:, ~df.columns.str.contains("Unknown")]
                df = df.loc[:, ~df.columns.str.contains("unidentified")]

                # Average columns with similar names
                df = self.average_similar_columns(df)

                # Drop rows where the entire row is empty
                df.dropna(
                    axis=0, how="all", inplace=True, subset=df.columns[1:]
                )  # Exclude the first column

                # Check if the DataFrame has < x metabolites
                if len(df.columns) < metabolite_drop_count:
                    if self.verbose:
                        print(
                            f"Study {filename} has fewer metabolites than {metabolite_drop_count}."
                        )
                    continue
                else:
                    output_csv_path = os.path.join(output_path, filename)
                    df.to_csv(output_csv_path, index=False)

                    if self.verbose:
                        print(f"Processed data saved to: {output_csv_path}")

    ################################ STEP: MERGE ANALYSES ################################

    @staticmethod
    def _merge_and_resolve_duplicates(dataframes, merge_column: str) -> pd.DataFrame:
        """
        Merge multiple DataFrames based on a common column and resolve duplicate columns by
        keeping the maximum value element-wise.

        Args:
            dataframes (list of pd.DataFrame): List of DataFrames to be merged.
            merge_column (str): The name of the common column to merge on.

        Returns:
            pd.DataFrame: The merged DataFrame with resolved duplicate columns.
        """
        # Start with the first DataFrame in the list
        merged_df = dataframes[0]
        # Convert the "Factors" column to a common data type (str)
        merged_df[merge_column] = merged_df[merge_column].astype(str)

        for df in dataframes[1:]:
            df[merge_column] = df[merge_column].astype(str)
            merged_df = pd.merge(
                merged_df, df, on=merge_column, how="outer", suffixes=("", "_y")
            )

            # Resolve duplicate columns by keeping the maximum value element-wise
            for column in merged_df.columns:
                if column != merge_column and column.endswith("_y"):
                    merged_df[column[:-2]] = merged_df[[column, column[:-2]]].max(
                        axis=1
                    )

            # Drop the duplicate columns from the merge
            merged_df = merged_df.drop(
                columns=[
                    column for column in merged_df.columns if column.endswith("_y")
                ]
            )

        # Sort the columns alphabetically, excluding the first column ('Factors')
        columns = list(merged_df.columns)
        columns.remove(merge_column)
        columns.sort()
        columns = [merge_column] + columns
        merged_df = merged_df[columns]

        return merged_df

    def _merge_analyses(self, input_path: str, output_path: str) -> None:
        """
        Iterate files in input_path, merge analyses if they belong to the same study based on Factors column.
        If not a common factors column. concatanate.

        Args:
            input_path (str): The path to the input directory containing CSV files.
            output_path (str): The path to the output directory for merged CSV files.
        """
        if self.verbose:
            print(
                "################################ STEP: MERGE ANALYSES ################################"
            )

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Group files by study_id
        files_by_study_id = {}
        for filename in os.listdir(input_path):
            if filename.endswith(".csv"):
                study_id = filename.split("_")[0].strip(".csv")

                if study_id not in files_by_study_id:
                    files_by_study_id[study_id] = []
                files_by_study_id[study_id].append(os.path.join(input_path, filename))

        # Merge files for each study_id
        for study_id, filepaths in files_by_study_id.items():
            dataframes = [pd.read_csv(filepath) for filepath in filepaths]

            if len(dataframes) > 1:  # Multiple analyses for a study
                # Check if there are common column names in both DataFrames
                common_columns = set(dataframes[0].columns)
                for df in dataframes[1:]:
                    common_columns &= set(df.columns)

                if common_columns:
                    print(f"There are common metabolites in {study_id}")
                    print(f"{common_columns = }")

                    # Check if data in the common columns are the same
                    for column in common_columns:
                        if column != "Factors":
                            are_columns_equal = all(
                                dataframes[0][column].equals(df[column])
                                for df in dataframes
                            )
                            if are_columns_equal:
                                dataframes[0] = dataframes[0].drop(column, axis=1)

                merged_df = self._merge_and_resolve_duplicates(dataframes, "Factors")

                # Save the merged DataFrame to a CSV file
                output_filepath = os.path.join(output_path, f"{study_id}.csv")
                merged_df.to_csv(output_filepath, index=False)

                if self.verbose:
                    print(
                        f"Merged data for study {study_id} saved to {output_filepath}"
                    )
            else:  # Copy the single CSV file to the output directory
                src_path = filepaths[0]
                dst_path = os.path.join(output_path, f"{study_id}.csv")
                shutil.copyfile(src_path, dst_path)

                if self.verbose:
                    print(f"Copied data for study {study_id} to {dst_path}")

    ################################ STEP: MAP WITH NEW-SYNONYM ################################

    def _apply_mapping(
        self,
        mapping_name: str,
        mode: str,
        input_path: str,
        output_path: str,
    ) -> None:
        """
        Apply mapping to an unmapped labeled STUDY.csv file and return a mapped version of it in a .csv format.

        Args:
            mapping_name (str): Mapping JSON file names available in Metabolitics pipeline.
            mode (str): Mode operation for mapping. Options: file, files
            input_path (str): The path to the input directory containing the CSV file to be mapped.
            output_path (str): The path to the output directory where the mapped CSV file will be saved.
            verbose (bool): Turn on/off command line prints.
        """
        if self.verbose:
            print(
                f"###################### STEP: Mapping  with {mapping_name} ######################"
            )
        if mode == "file":
            X_study, y_study = SkUtilsIO(f"{input_path}").from_csv(
                label_column="Factors"
            )

            if self.verbose:
                print(f"Loaded file in path: {input_path}")

            # Choose mapping json
            MetaboliticsPipeline.steps["metabolite-name-mapping"] = FeatureRenaming(
                load_metabolite_mapping(mapping_name)
            )

            transformer_pipe = MetaboliticsPipeline(["metabolite-name-mapping"])
            X_transformed = transformer_pipe.fit_transform(X=X_study, y=y_study)

            X_df = pd.DataFrame(X_transformed)
            y_df = pd.DataFrame({"Factors": y_study})
            mapped_df = pd.concat([y_df, X_df], axis=1)
            mapped_df.to_csv(output_path, index=False)

        elif mode == "files":
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            for study in os.listdir(input_path):
                study_path = os.path.join(input_path, study)
                X_study, y_study = SkUtilsIO(f"{study_path}").from_csv(
                    label_column="Factors"
                )
                print(f"Loaded file in path: {study_path}")

                # Choose mapping json
                MetaboliticsPipeline.steps["metabolite-name-mapping"] = FeatureRenaming(
                    load_metabolite_mapping(mapping_name)
                )

                transformer_pipe = MetaboliticsPipeline(["metabolite-name-mapping"])
                X_transformed = transformer_pipe.fit_transform(X=X_study, y=y_study)

                X_df = pd.DataFrame(X_transformed)
                y_df = pd.DataFrame({"Factors": y_study})
                mapped_df = pd.concat([y_df, X_df], axis=1)
                study_output_path = os.path.join(output_path, study)
                mapped_df.to_csv(study_output_path, index=False)

    ################################ STEP: FILTER PATIENTS IN STUDY.CSV ################################

    def _filter_patients(
        self,
        input_path: str,
        output_path: str,
        metabolite_drop_count: int,
    ) -> None:
        """
        Travers CSV files in the input_path, drop individuals with less than `metabolite_drop_count` metabolites.

        Args:
            input_path (str): The path to the directory containing CSV files.
            output_path (str): The path to the output directory for CSV files with filters applied.
            metabolite_drop_count (int): The minimum number of metabolites required to keep a patient.
            verbose (bool): Turn on/off command line prints.
        """
        if self.verbose:
            print(
                f"###################### STEP: FILTER PATIENTS IN STUDY.CSV ######################"
            )
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        for study in os.listdir(input_path):
            study_path = os.path.join(input_path, study)
            df = pd.read_csv(study_path)

            # Filter rows based on the number of non-missing metabolites
            filtered_df = df[df.count(axis=1) >= metabolite_drop_count]

            # If the DataFrame is empty after filtering, log to console
            if filtered_df.empty:
                if self.verbose:
                    print(f"Empty study: {study_path}")
            else:
                # Save to output directory
                output_csv_path = os.path.join(output_path, study)
                os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
                filtered_df.to_csv(output_csv_path, index=False)

                if self.verbose:
                    print(f"Processed data saved to: {output_csv_path}")

    ################################ STEP: FILL MISSING RANDOMLY ################################

    def _fill_missing(self, mode: str, input_path: str, output_path: str) -> None:
        """
        Fill missing values with random float values within the range of their respective columns, and output to the output_path.

        Args:
            mode (str): Mode operation for filling. Options: files, folders
            input_path (str): The path to the directory containing subfolders with CSV files.
            output_path (str): The path to the output directory for CSV files with missing values filled.
        """
        if self.verbose:
            print(
                f"###################### STEP: FILL MISSING RANDOMLY ######################"
            )
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        if mode == "folders":
            for subfolder in os.listdir(input_path):
                subfolder_path = os.path.join(input_path, subfolder)

                if os.path.isdir(subfolder_path):
                    csv_files = [
                        filename
                        for filename in os.listdir(subfolder_path)
                        if filename.endswith(".csv")
                    ]

                    for filename in csv_files:
                        csv_path = os.path.join(subfolder_path, filename)
                        df = pd.read_csv(csv_path)

                        # Remove completely empty columns (contain only NaN values)
                        df.dropna(axis=1, how="all", inplace=True)

                        # Iterate through columns and fill missing values (including 0.0) with random values within their range
                        for column in df.columns:
                            if column != "Factors":  # Skip the "Factors" column
                                min_value = df[column].min()
                                max_value = df[column].max()
                                missing_mask = (df[column].isna()) | (df[column] == 0.0)
                                num_missing = missing_mask.sum()
                                random_values = np.random.uniform(
                                    min_value, max_value, num_missing
                                )
                                df.loc[missing_mask, column] = random_values

                        output_csv_path = os.path.join(output_path, subfolder, filename)
                        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
                        df.to_csv(output_csv_path, index=False)

                        if self.verbose:
                            print(
                                f"CSV file with missing values filled saved to: {output_csv_path}"
                            )
        elif mode == "files":
            for study in os.listdir(input_path):
                study_path = os.path.join(input_path, study)
                df = pd.read_csv(study_path)

                # Remove completely empty columns (contain only NaN values)
                df.dropna(axis=1, how="all", inplace=True)

                # Iterate through columns and fill missing values (including 0.0) with random values within their range
                for column in df.columns:
                    if column != "Factors":  # Skip the "Factors" column
                        min_value = df[column].min()
                        max_value = df[column].max()
                        missing_mask = (df[column].isna()) | (df[column] == 0.0)
                        num_missing = missing_mask.sum()
                        random_values = np.random.uniform(
                            min_value, max_value, num_missing
                        )
                        df.loc[missing_mask, column] = random_values

                output_csv_path = os.path.join(output_path, study)
                os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
                df.to_csv(output_csv_path, index=False)

                if self.verbose:
                    print(
                        f"CSV file with missing values filled saved to: {output_csv_path}"
                    )

    ################################ STEP: NORMALIZE DATA ################################

    @staticmethod
    def min_max_scaling(series: pd.Series) -> pd.Series:
        """
        Apply min-max scaling to a Pandas Series.

        Args:
            series (pd.Series): The Series to be scaled.

        Returns:
            pd.Series: The scaled Series.
        """
        min_val = series.min()
        max_val = series.max()

        return (series - min_val) / (max_val - min_val)

    def _normalize(self, mode: str, input_path: str, output_path: str) -> None:
        """
        Traverse subfolders in the input_path, read CSV files, normalize DataFrames with min-max scaling.
        And output to the output_path.

        Args:
            mode (str): Mode operation for normalization. Options: folders, files
            input_path (str): The path to the directory containing subfolders with CSV files.
            output_path (str): The path to the output directory for normalized CSV files.
        """
        if self.verbose:
            print(f"###################### STEP: NORMALIZE DATA ######################")

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        if mode == "folders":
            for subfolder in os.listdir(input_path):
                subfolder_path = os.path.join(input_path, subfolder)

                if os.path.isdir(subfolder_path):
                    csv_files = [
                        filename
                        for filename in os.listdir(subfolder_path)
                        if filename.endswith(".csv")
                    ]

                    for filename in csv_files:
                        csv_path = os.path.join(subfolder_path, filename)
                        df = pd.read_csv(csv_path)

                        # Skip the "Factors" column for normalization
                        columns_to_normalize = [
                            col for col in df.columns if col != "Factors"
                        ]

                        # Normalize the selected columns using min-max scaling
                        df[columns_to_normalize] = df[columns_to_normalize].apply(
                            self.min_max_scaling
                        )

                        output_csv_path = os.path.join(output_path, subfolder, filename)
                        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
                        df.to_csv(output_csv_path, index=False)

                        if self.verbose:
                            print(f"Normalized data saved to: {output_csv_path}")

        elif mode == "files":
            for study in os.listdir(input_path):
                study_path = os.path.join(input_path, study)
                df = pd.read_csv(study_path)

                # Skip the "Factors" column for normalization
                columns_to_normalize = [col for col in df.columns if col != "Factors"]

                # Normalize the selected columns using min-max scaling
                df[columns_to_normalize] = df[columns_to_normalize].apply(
                    self.min_max_scaling
                )

                output_csv_path = os.path.join(output_path, study)
                os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
                df.to_csv(output_csv_path, index=False)

                if self.verbose:
                    print(f"Normalized data saved to: {output_csv_path}")

    ################################ STEP 7: Create big WORKBENCH.CSV ################################

    def _create_workbench_csv(self, input_path: str, output_path: str) -> None:
        """
        Create a single WORKBENCH.csv file by merging CSV files from the input directory.
        The "Factors" column is dropped from each CSV file before merging.

        Args:
            input_path (str): The path to the directory containing CSV files.
            output_path (str): The path to the output CSV file.
        """
        if self.verbose:
            print(
                f"###################### STEP: Create big WORKBENCH.CSV ######################"
            )

        data_frames = []

        for filename in os.listdir(input_path):
            if filename.endswith(".csv"):
                if self.verbose:
                    print(f"Reading file: {filename}")
                csv_path = os.path.join(input_path, filename)
                df = pd.read_csv(csv_path)

                # # Drop the "Factors" column if it exists
                if "Factors" in df.columns:
                    df = df.drop(columns=["Factors"])

                data_frames.append(df)

        # Check if there are any DataFrames to merge
        if data_frames:
            merged_df = pd.concat(data_frames, axis=0, ignore_index=True)

            workbench_csv_path = os.path.join(output_path, "WORKBENCH.csv")
            merged_df.to_csv(workbench_csv_path, index=False)

            if self.verbose:
                print(f"WORKBENCH.csv file created at: {workbench_csv_path}")
        else:
            if self.verbose:
                print("No CSV files found in the input directory.")

    ################################ STEP: Filter WORKBENCH.CSV ################################

    def _filter_workbench_csv(
        self,
        input_path: str,
        output_path: str,
        metabolite_drop_count: int,
        patient_drop_count: int,
    ) -> None:
        """
        Filter WORKBENCH.csv file.
        Drop metabolites which is seen less than `metabolite_drop_count` patients.
        Drop patients who have less than `patient_drop_count` metabolites.

        Args:
            input_path (str): The path to the input CSV file.
            output_path (str): The path to the output CSV file.
            metabolite_drop_count (int): The minimum number of metabolites required to keep a patient.
            patient_drop_count (int): The minimum number of patients required to keep a metabolite.
            verbose (bool): Turn on/off command line prints.
        """
        if self.verbose:
            print(
                f"###################### STEP: Filter WORKBENCH.CSV ######################"
            )

        df = pd.read_csv(input_path)

        # Drop patients who have less than `metabolite_drop_count` metabolites
        df = df.loc[df.count(axis=1) >= metabolite_drop_count]

        # Drop metabolites seen in less than `patient_drop_count` patients
        df = df.loc[:, df.count() >= patient_drop_count]

        if not df.empty:
            df.to_csv(output_path, index=False)
            if self.verbose:
                print(f"Processed data saved to: {output_path}")
