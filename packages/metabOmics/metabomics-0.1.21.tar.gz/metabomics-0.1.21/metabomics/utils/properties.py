from datetime import datetime
import os

# now = datetime.now()
# now_str = str(now).replace(":", "").replace(".", "").replace(" ", "").replace("-", "")
# print(now_str)


# FLUX_TYPE = 'metabolitics-transformer-with-pfba'
# FLUX_TYPE = 'metabolitics-transformer'
FLUX_TYPE = 'metabolitics-transformer-with-geometric-fba'
# FLUX_TYPE = 'metabolitics-transformer-with-moma'

# PREPROCESS_PIPELINE_TYPE = "reaction"
PREPROCESS_PIPELINE_TYPE = "pathway"

def create_out_dir(flux_type, preprocess_pipeline_type, now_str):
        
    out_dirname = f"out_{flux_type}_{preprocess_pipeline_type}_{now_str}"

    os.mkdir(out_dirname)
    return out_dirname

def get_file_path(out_dirname, file_name):
    # now = datetime.now()
    # now_str = str(now).replace(":", "").replace(".", "").replace(" ", "").replace("-", "")
    # print(now_str)
    file_path = f"{out_dirname}/{file_name}"
    # file_path = f"{out_dirname}/{now_str}_{file_name}"
    print(file_path)
    return file_path
