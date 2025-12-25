import json
import os
import shutil
from ftplib import FTP

import numpy as np
import pandas as pd
from bcbio import isatab
from sklearn_utils.preprocessing import FeatureRenaming
from sklearn_utils.utils import SkUtilsIO

from preprocessing.metabolitics_pipeline import MetaboliticsPipeline
from utils import load_metabolite_mapping


class MetaboLightsDataPipeline:
    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.line_break = "-" * 40

    ################################ STEP: DOWNLOAD ################################

    @staticmethod
    def _download_tsv_files(
        ftp_url: str, destination_folder: str, verbose: bool = False
    ) -> None:
        """
        Download .tsv files from the MetaboLights FTP server:
        http://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/.

        Args:
            ftp_url (str): The URL of the FTP server to connect to.
            destination_folder (str): The local directory where the downloaded .tsv files will be stored.
            verbose (bool): Turn on/off command line prints.
        """
        if verbose:
            print(f"###################### STEP: DOWNLOAD ######################")

        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Connect to the FTP server
        ftp = FTP(ftp_url)
        ftp.login()

        # Navigate to the desired directory
        ftp.cwd("/pub/databases/metabolights/studies/public/")

        # List the files and directories in the current FTP directory
        file_list = []
        ftp.retrlines("NLST", file_list.append)

        # Download .tsv files from each sub-directory
        for folder in file_list:
            try:
                if verbose:
                    print(f"Downloading files for study {folder} ...")

                folder_path = f"/pub/databases/metabolights/studies/public/{folder}"
                ftp.cwd(folder_path)
                sub_file_list = []
                ftp.retrlines("NLST", sub_file_list.append)

                local_folder_path = os.path.join(destination_folder, folder)

                if not os.path.exists(local_folder_path):
                    os.makedirs(local_folder_path)

                for file_name in sub_file_list:
                    if file_name.endswith(".tsv") or file_name.endswith(".txt"):
                        local_file_path = os.path.join(local_folder_path, file_name)
                        with open(local_file_path, "wb") as local_file:
                            ftp.retrbinary("RETR " + file_name, local_file.write)

            except Exception as e:
                print(f"Error: {str(e)}")
                continue

            ftp.cwd("..")  # Go back to the parent directory after processing a folder

        ftp.quit()

        if verbose:
            print("Download completed.")

    ################################ STEP: METADATA EXTRACTION ################################

    @staticmethod
    def _extract_metadata(
        input_path: str, output_path: str, verbose: bool = False
    ) -> None:
        """
        Extract metadata from ISA-Tab formatted study files and save it as a JSON file.

        Args:
            input_path (str): The path to the directory containing ISA-Tab formatted study files.
            output_path (str): The path to the directory where the extracted metadata JSON file will be saved.
            verbose (bool): Turn on/off command line prints for verbose output.

        """
        if verbose:
            print(
                f"###################### STEP: METADATA EXTRACTION ######################"
            )

        study_metadata = {}

        for subfolder in os.listdir(input_path):
            if verbose:
                print(f"Extracting data from {subfolder}...")

            subfolder_path = os.path.join(input_path, subfolder)

            try:
                # Parse using isatab parser
                rec = isatab.parse(subfolder_path)

            except UnicodeDecodeError as error:
                print(f"UnicodeDecodeError in folder {subfolder}: {str(error)}")
                continue  # Skip this subfolder and continue to the next one
            except KeyError as error:
                print(f"KeyError in folder {subfolder}: {str(error)}")
                continue
            except ValueError as error:
                print(f"ValueError in folder {subfolder}: {str(error)}")
                continue
            except AssertionError as error:
                print(f"AssertionError in folder {subfolder}: {str(error)}")
                continue

            study = rec.studies[0]

            # Extract organism information for the study
            sample_names = study.nodes.keys()
            sample_organism_list = []

            for sample in sample_names:
                try:
                    sample_organism = study.nodes[sample].metadata[
                        "Characteristics[Organism]"
                    ][0][0]
                except KeyError:
                    sample_organism = study.nodes[sample].metadata[
                        "Characteristics[Organism part]"
                    ][0][0]

                sample_organism_list.append(sample_organism)

            unique_organism_list = list(set(sample_organism_list))
            sorted_organism_list = sorted(unique_organism_list)

            # Extract organism part information for the study
            sample_organism_part_list = []

            for sample in sample_names:
                sample_organism_part = study.nodes[sample].metadata[
                    "Characteristics[Organism part]"
                ][0][0]

                sample_organism_part_list.append(sample_organism_part)

            unique_organism_part_list = list(set(sample_organism_part_list))
            sorted_organism_part_list = sorted(unique_organism_part_list)

            # Extract patient/sample information for the study
            samples_dict = {}

            for sample in sample_names:
                sample_dict = {}
                sample_name = study.nodes[sample].metadata["Sample Name"][0]

                # Sample metadata
                sample_metadata = study.nodes[sample].metadata
                meta_data_keys = sample_metadata.keys()

                for key in meta_data_keys:
                    if isinstance(sample_metadata[key][0], str):
                        sample_dict[key] = sample_metadata[key][0]
                    else:
                        sample_dict[key] = sample_metadata[key][0][0]

                samples_dict[sample_name] = sample_dict

            study_dict = {}
            study_dict["Study Title"] = study.metadata["Study Title"]
            study_dict["Study Organism"] = sorted_organism_list
            study_dict["Study Organism Part"] = sorted_organism_part_list
            study_dict["Study Submission Date"] = study.metadata[
                "Study Submission Date"
            ]
            study_dict["Study Public Release Date"] = study.metadata[
                "Study Public Release Date"
            ]
            study_dict["Design Descriptors"] = [
                descriptor for descriptor in study.design_descriptors
            ]
            study_dict["Factors"] = [factor for factor in study.factors]
            study_dict["Samples"] = samples_dict

            study_metadata[study.metadata["Study Identifier"]] = study_dict

        # Convert the dictionary to a JSON string
        json_string = json.dumps(study_metadata, indent=2)

        # Save the JSON string to a file
        metadata_path = os.path.join(output_path, "metabolights_metadata.json")
        with open(metadata_path, "w") as json_file:
            json_file.write(json_string)

        if verbose:
            print(f"JSON data saved to {metadata_path}")

    ################################ STEP: Seperate Only Homo Sapiens Studies ################################

    @staticmethod
    def _seperate_homosapiens(
        metadata_path: str, input_path: str, output_path: str, verbose: bool = False
    ) -> None:
        """
        Separate study folders with "Homo sapiens" as the sole organism into a specified output directory.

        Args:
            metadata_path (str): The path to the JSON metadata file containing study information.
            input_path (str): The path to the directory containing study folders to be separated.
            output_path (str): The path to the output directory where "Homo sapiens" studies will be moved.
            verbose (bool): Turn on/off command line prints for verbose output.
        """
        if verbose:
            print(
                f"###################### STEP: Seperate Only Homo Sapiens Studies ######################"
            )

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        with open(metadata_path, "r") as json_file:
            metadata = json.load(json_file)

        for study_id, study_info in metadata.items():
            study_organisms = study_info.get("Study Organism", [])

            # Check if "Homo sapiens" is in the list of study organisms
            if "Homo sapiens" in study_organisms and len(study_organisms) == 1:
                source_study_path = os.path.join(input_path, study_id)
                destination_study_path = os.path.join(output_path, study_id)

                try:
                    shutil.move(source_study_path, destination_study_path)
                    if verbose:
                        print(f"Study {study_id} moved to {destination_study_path}")
                except FileNotFoundError as error:
                    print(
                        f"FileNotFoundError in folder {source_study_path}: {str(error)}"
                    )
                    continue

        if verbose:
            print("Processing completed.")

    ################################ STEP 0: PARSER ################################

    @staticmethod
    def extract_patient_names(df: pd.DataFrame):
        """
        Extract patient names from a DataFrame containing metabolite concentration data.

        Args:
            df (pd.DataFrame): The DataFrame containing metabolite concentration data.

        Returns:
            list: A list of patient names found in the DataFrame.
        """
        for i, column in enumerate(df.columns):
            if column == "smallmolecule_abundance_std_error_sub":
                return df.columns[i + 1 :]

    def _parser(self, input_path: str, output_path: str, verbose: bool = False) -> None:
        """
        Parse .tsv files from the input directory, extract metabolite data,
        and save parsed csv files in the output directory.

        Args:
            input_path (str): The path to the directory containing .tsv files.
            output_path (str): The path to the output directory for parsed .csv files.
            verbose (bool): Turn on/off command line prints.
        """
        if verbose:
            print(f"###################### STEP: PARSER ######################")

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        for subfolder in os.listdir(input_path):
            subfolder_path = os.path.join(input_path, subfolder)

            unmapped_subfolder_path = os.path.join(output_path, subfolder)

            if not os.path.exists(unmapped_subfolder_path):
                os.makedirs(unmapped_subfolder_path)

            for filename in os.listdir(subfolder_path):
                if filename.endswith(".tsv") and filename[:2] == "m_":
                    try:
                        tsv_path = os.path.join(subfolder_path, filename)
                        if verbose:
                            print(f"Parsing file {tsv_path}")

                        raw_df = pd.read_csv(tsv_path, sep="\t")

                        # Extract unique metabolite names
                        metabolite_names = raw_df["metabolite_identification"]
                        metabolite_names = [
                            metabolite for metabolite in metabolite_names
                        ]
                        # Create columns
                        columns = list(metabolite_names)
                        columns.insert(0, "Factors")
                        study_df = pd.DataFrame(columns=columns)

                        # Get patient names/labels
                        patient_names = self.extract_patient_names(raw_df)
                        study_df["Factors"] = patient_names

                        # Fill metabolite concentration values for each patient
                        for patient_index, patient in enumerate(patient_names):
                            patient_mconc = raw_df[patient]
                            for metabolite_index, metabolite in enumerate(
                                metabolite_names
                            ):
                                study_df.loc[patient_index, metabolite] = patient_mconc[
                                    metabolite_index
                                ]

                        # Create the parsed CSV file in the subfolder of the unmapped directory
                        parsed_filename = os.path.splitext(filename)[0]
                        parsed_csv_path = os.path.join(
                            unmapped_subfolder_path, f"{parsed_filename}.csv"
                        )
                        study_df.to_csv(parsed_csv_path, index=False)
                        if verbose:
                            print(f"Parsed data saved to: {parsed_csv_path}")

                    except TypeError as error:
                        print(f"TypeError in file {filename}: {str(error)}")
                        continue

                    except KeyError as error:
                        print(f"KeyError in file {filename}: {str(error)}")
                        continue

                    except UnicodeDecodeError as error:
                        print(f"UnicodeDecodeError in file {filename}: {str(error)}")
                        continue

    ################################ STEP 1: FILTER BEFORE MERGE ################################

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

    # @staticmethod
    # def check_empty_dataframe(df: pd.DataFrame) -> bool:
    #     """
    #     Check if a DataFrame contains 50% or more missing values (NaNs).

    #     Args:
    #         df (pd.DataFrame): The DataFrame to be checked for missing values.

    #     Returns:
    #         bool: True if the DataFrame contains 50% or more missing values, False otherwise.
    #     """
    #     # Create a boolean mask where True represents missing values
    #     missing_mask = df.isna()

    #     # Count the number of True values (missing values)
    #     missing_count = (
    #         missing_mask.sum().sum()
    #     )  # Sum twice to count all missing values

    #     # Calculate the percentage of missing values
    #     total_cells = df.size
    #     percentage_missing = (missing_count / total_cells) * 100

    #     return percentage_missing >= 50

    def _filter_folders(
        self,
        input_path: str,
        output_path: str,
        metabolite_drop_count: int,
        verbose: bool,
    ) -> None:
        """
        Filter and process CSV files within subfolders in the input directory. This function removes
        rows and columns with uninformative data, averages columns with similar names, drops rows
        where the entire row is empty, and deletes files with fewer than a specified number of metabolites.

        Args:
            input_path (str): The path to the directory containing subfolders with CSV files.
            output_path (str): The path to the output directory for filtered CSV files.
            metabolite_drop_count (int): The minimum number of metabolites required to keep a CSV file.
            verbose (bool): Turn on/off command line prints for detailed processing information.
        """
        if verbose:
            print(
                f"###################### STEP: FILTER BEFORE MERGE ######################"
            )

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        for subfolder in os.listdir(input_path):
            subfolder_path = os.path.join(input_path, subfolder)

            if os.path.isdir(subfolder_path):
                if verbose:
                    print(self.line_break)
                    print(f"Processing study: {subfolder}")
                csv_files = [
                    filename
                    for filename in os.listdir(subfolder_path)
                    if filename.endswith(".csv")
                ]

                # Iterate through csv files in the subfolder
                for filename in csv_files:
                    csv_path = os.path.join(subfolder_path, filename)
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
                        print(f"Deleting file {filename}.")
                        os.remove(csv_path)
                    else:
                        output_csv_path = os.path.join(output_path, subfolder, filename)
                        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
                        df.to_csv(output_csv_path, index=False)

                        if verbose:
                            print(f"Processed data saved to: {output_csv_path}")

                if not os.listdir(subfolder_path):
                    if verbose:
                        print(f"Deleting empty subfolder: {subfolder}")
                    os.rmdir(subfolder_path)

    ################################ STEP 2: STUDY.CSV ################################

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

    def _create_study_csv(
        self, input_path: str, output_path: str, verbose: bool = False
    ) -> None:
        """
        Merge CSV files within study subfolders with specific rules.

        Args:
            input_path (str): The path to the input directory containing subfolders with CSV files.
            output_path (str): The path to the output directory for merged CSV files.
            verbose (bool): Turn on/off command line prints.
        """
        print(
            "################################ STEP: STUDY.CSV ################################"
        )

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        for subfolder in os.listdir(input_path):
            subfolder_path = os.path.join(input_path, subfolder)

            if os.path.isdir(subfolder_path):
                if verbose:
                    print(self.line_break)
                    print(f"Processing study: {subfolder}")
                csv_files = [
                    filename
                    for filename in os.listdir(subfolder_path)
                    if filename.endswith(".csv")
                ]

                # Check if there are more than 2 studies in a folder (POS, NEG, etc.)
                if len(csv_files) >= 2:
                    data_frames = []

                    for filename in csv_files:
                        csv_path = os.path.join(subfolder_path, filename)
                        df = pd.read_csv(csv_path)
                        data_frames.append(df)

                    # Check if there are common column names in both DataFrames
                    common_columns = set(data_frames[0].columns)
                    for df in data_frames[1:]:
                        common_columns &= set(df.columns)

                    if common_columns:
                        # Check if data in the common columns are the same
                        for column in common_columns:
                            if column != "Factors":
                                are_columns_equal = all(
                                    data_frames[0][column].equals(df[column])
                                    for df in data_frames
                                )
                                if are_columns_equal:
                                    data_frames[0] = data_frames[0].drop(column, axis=1)

                        merged_df = self._merge_and_resolve_duplicates(
                            data_frames, "Factors"
                        )

                        if not merged_df.empty:
                            merged_output_path = os.path.join(
                                output_path, f"{subfolder}.csv"
                            )
                            merged_df.to_csv(merged_output_path, index=False)

                            if verbose:
                                print(f"Merged data saved to: {merged_output_path}")

                else:  # Single csv file in directory
                    # Copy the single CSV file and rename it as the subfolder name
                    src_path = os.path.join(subfolder_path, csv_files[0])
                    dst_path = os.path.join(output_path, f"{subfolder}.csv")
                    shutil.copyfile(src_path, dst_path)

                    if verbose:
                        print(f"File copied and renamed to: {dst_path}")

    ################################ STEP 3: MAP WITH NEW-SYNONYM ################################

    @staticmethod
    def _apply_mapping(
        mapping_name: str,
        mode: str,
        input_path: str,
        output_path: str,
        verbose: bool = False,
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
        if verbose:
            print(
                f"###################### STEP: Mapping  with {mapping_name} ######################"
            )
        if mode == "file":
            X_study, y_study = SkUtilsIO(f"{input_path}").from_csv(
                label_column="Factors"
            )

            if verbose:
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

    ################################ STEP 4: FILTER PATIENTS IN STUDY.CSV ################################

    @staticmethod
    def _filter_patients(
        input_path: str,
        output_path: str,
        metabolite_drop_count: int,
        verbose: bool = False,
    ) -> None:
        """
        Travers CSV files in the input_path, drop individuals with less than `metabolite_drop_count` metabolites.

        Args:
            input_path (str): The path to the directory containing CSV files.
            output_path (str): The path to the output directory for CSV files with filters applied.
            metabolite_drop_count (int): The minimum number of metabolites required to keep a patient.
            verbose (bool): Turn on/off command line prints.
        """
        if verbose:
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
                if verbose:
                    print(f"Empty study: {study_path}")
            else:
                # Save to output directory
                output_csv_path = os.path.join(output_path, study)
                os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
                filtered_df.to_csv(output_csv_path, index=False)

                if verbose:
                    print(f"Processed data saved to: {output_csv_path}")

    ################################ STEP 5: FILL MISSING RANDOMLY ################################

    @staticmethod
    def _fill_missing(
        mode: str, input_path: str, output_path: str, verbose: bool = False
    ) -> None:
        """
        Fill missing values with random float values within the range of their respective columns, and output to the output_path.

        Args:
            mode (str): Mode operation for filling. Options: files, folders
            input_path (str): The path to the directory containing subfolders with CSV files.
            output_path (str): The path to the output directory for CSV files with missing values filled.
            verbose (bool): Turn on/off command line prints.
        """
        if verbose:
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

                        if verbose:
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

                if verbose:
                    print(
                        f"CSV file with missing values filled saved to: {output_csv_path}"
                    )

    ################################ STEP 6: NORMALIZE DATA ################################

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

    def _normalize(
        self, mode: str, input_path: str, output_path: str, verbose: bool = False
    ) -> None:
        """
        Traverse subfolders in the input_path, read CSV files, normalize DataFrames with min-max scaling.
        And output to the output_path.

        Args:
            mode (str): Mode operation for normalization. Options: folders, files
            input_path (str): The path to the directory containing subfolders with CSV files.
            output_path (str): The path to the output directory for normalized CSV files.
            verbose (bool): Turn on/off command line prints.
        """
        if verbose:
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

                        if verbose:
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

                if verbose:
                    print(f"Normalized data saved to: {output_csv_path}")

    ################################ STEP 7: Create big METABOLIGHTS.CSV ################################

    @staticmethod
    def _create_metabolights_csv(
        input_path: str, output_path: str, verbose: bool = False
    ) -> None:
        """
        Create a single METABOLIGHTS.csv file by merging CSV files from the input directory.
        The "Factors" column is dropped from each CSV file before merging.

        Args:
            input_path (str): The path to the directory containing CSV files.
            output_path (str): The path to the output CSV file.
            verbose (bool): Turn on/off command line prints.
        """
        if verbose:
            print(
                f"###################### STEP: Create big METABOLIGHTS.CSV ######################"
            )

        data_frames = []

        for filename in os.listdir(input_path):
            if filename.endswith(".csv"):
                if verbose:
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

            metabolights_csv_path = os.path.join(output_path, "METABOLIGHTS.csv")
            merged_df.to_csv(metabolights_csv_path, index=False)

            if verbose:
                print(f"METABOLIGHTS.csv file created at: {metabolights_csv_path}")
        else:
            if verbose:
                print("No CSV files found in the input directory.")

    ################################ STEP 8: Filter METABOLIGHTS.CSV ################################

    @staticmethod
    def _filter_metabolights_csv(
        input_path: str,
        output_path: str,
        metabolite_drop_count: int,
        patient_drop_count: int,
        verbose: bool = False,
    ) -> None:
        """
        Filter METABOLIGHTS.csv file.
        Drop metabolites which is seen less than `metabolite_drop_count` patients.
        Drop patients who have less than `patient_drop_count` metabolites.

        Args:
            input_path (str): The path to the input CSV file.
            output_path (str): The path to the output CSV file.
            metabolite_drop_count (int): The minimum number of metabolites required to keep a patient.
            patient_drop_count (int): The minimum number of patients required to keep a metabolite.
            verbose (bool): Turn on/off command line prints.
        """
        if verbose:
            print(
                f"###################### STEP: Filter METABOLIGHTS.CSV ######################"
            )

        df = pd.read_csv(input_path)

        # Drop patients who have less than `metabolite_drop_count` metabolites
        df = df.loc[df.count(axis=1) >= metabolite_drop_count]

        # Drop metabolites seen in less than `patient_drop_count` patients
        df = df.loc[:, df.count() >= patient_drop_count]

        if not df.empty:
            df.to_csv(output_path, index=False)
            if verbose:
                print(f"Processed data saved to: {output_path}")
