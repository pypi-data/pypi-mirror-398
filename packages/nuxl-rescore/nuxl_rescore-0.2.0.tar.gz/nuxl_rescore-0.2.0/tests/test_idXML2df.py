import pandas as pd
import requests
from pathlib import Path
from nuxl_rescore import readAndProcessIdXML

def test_read_idxml_github(tmp_path):
    # tmp_path is a pytest fixture providing a temporary folder
    url = "https://github.com/Arslan-Siraj/nuxl-app/raw/main/example-data/idXMLs/Example_perc_0.0100_XLs.idXML"
    
    # Download the file into tmp_path
    local_file = tmp_path / "Example_perc_0.0100_XLs.idXML"
    r = requests.get(url)
    r.raise_for_status() 
    local_file.write_bytes(r.content)

    # Now use your function
    df = readAndProcessIdXML(str(local_file))

    assert isinstance(df, pd.DataFrame)
    assert "Peptide" in df.columns
    assert len(df) > 0

