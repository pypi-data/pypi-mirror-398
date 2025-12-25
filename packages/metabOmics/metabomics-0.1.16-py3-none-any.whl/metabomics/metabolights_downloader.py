""" Python script to download related .tsv files from
    MetaboLights FTP server: http://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/
"""
import os
from ftplib import FTP

METABOLIGHTS_RAW_DATA_PATH = os.path.join(
    "datasets", "disease_datasets", "metabolights", "raw"
)


def download_tsv_files(ftp_url, destination_folder):
    # Create the destination folder if it doesn't exist
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
        print("Download completed.")


if __name__ == "__main__":
    # Example usage:
    ftp_url = "ftp.ebi.ac.uk"
    download_tsv_files(ftp_url, METABOLIGHTS_RAW_DATA_PATH)
