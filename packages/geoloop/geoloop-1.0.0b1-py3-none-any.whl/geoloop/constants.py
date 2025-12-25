from pathlib import Path

repo_path = Path(__file__).parent.parent.parent

# Test directories
test_dir = repo_path / "test"
tests_input_path = test_dir / "input"
test_output_path = test_dir / "output"

# Resources directory
resources_path = repo_path / "resources"

# Lithology resources directory
lithology_properties_xlsx = (
    resources_path / "lithology_properties" / "lithology_properties.xlsx"
)

# Dictionary of units for various parameters in the model.
units_dict = {
    "Q_b": "W",
    "flowrate": "kg/s",
    "T_fi": "\u00b0C",
    "T_fo": "\u00b0C",
    "T_bave": "\u00b0C",
    "dploop": "bar",
    "qloop": "W",
    "z": "m",
    "T_b": "\u00b0C",
    "T_f": "\u00b0C",
    "qzb": "W/m",
    "k_g": "W/mK",
    "k_p": "W/mK",
    "m_flow": "kg/s",
    "Tin": "\u00b0C",
    "H": "m",
    "epsilon": "m",
    "alfa": "m\u00b2/s",
    "Tgrad": "\u00b0C/100m",
    "Q": "W",
    "qsign": "-",
    "nPipes": "-",
    "zseg": "-",
    "k_s_scale": "-",
    "Re_in": "-",
    "Re_out": "-",
    "h_f_max": "-",
    "h_f_min": "-",
    "k_s": "W/mK",
    "k_s_res": "W/mK",
    "fluid_percent": "%",
    "insu_z": "m",
    "insu_dr": "%",
    "k_g_res": "W/mK",
}

# Dictionary of formatted names for various parameters in the model.
format_dict = {
    "Q_b": "$Q_{b}$",
    "flowrate": "$flowrate$",
    "T_fi": "$T_{fi}$",
    "T_fo": "$T_{fo}$",
    "T_bave": "$T_{bave}$",
    "dploop": "$dploop$",
    "qloop": "$qloop$",
    "z": "$z$",
    "T_b": "$T_{b}$",
    "T_f": "$T_{f}$",
    "qzb": "$qzb$",
    "k_g": "$k_{g}$",
    "k_p": "$k_{p}$",
    "m_flow": "$m_{flow}$",
    "Tin": "$Tin$",
    "H": "$H$",
    "epsilon": r"$\epsilon$",
    "alfa": r"$\alpha$",
    "Tgrad": "$T_{grad}$",
    "Q": "$Q$",
    "qsign": "$q_{sign}$",
    "nPipes": "$n_{Pipes}$",
    "zseg": "$z_{seg}$",
    "k_s_scale": "$k_{s}scale$",
    "Re_in": "$Re_{in}$",
    "Re_out": "$Re_{out}$",
    "h_f_max": "$h_{f}max$",
    "h_f_min": "$h_{f}min$",
    "k_s": "$k_{s}$",
    "k_s_res": "$k_{s-res}$",
    "fluid_percent": "$fluid_{percent}$",
    "insu_z": "$insu_{z}$",
    "insu_dr": "$insu_{dr}$",
    "k_g_res": "$k_{g-res}$",
}

# Dictionary with colors for lithology plotting
lithology_colors = {
    "sand": "#FFFF00",
    "clay": "#008000",
    "shells": "#800080",
    "chalk": "#FFFFFF",
    "marl": "#A52A2A",
    "claystone": "#1F1F1F",
}

# Dictionary for mapping lithology names from Dutch to English
lithology_names_english = {
    "zand": "Sand",
    "klei": "Clay",
    "schelpen": "Shells",
    "krijt": "Chalk",
    "mergel": "Marl",
    "kleisteen": "Claystone",
}
