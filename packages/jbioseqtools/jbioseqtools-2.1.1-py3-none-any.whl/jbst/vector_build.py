import pandas as pd

pd.options.mode.chained_assignment = None
import random
import re
import string

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pkg_resources
import seaborn as sns

pd.options.mode.chained_assignment = None
import warnings

from .seq_tools import *

warnings.filterwarnings("ignore")

random.seed(42)


#       _  ____   _         _____              _
#      | ||  _ \ (_)       / ____|            | |
#      | || |_) | _   ___ | (___   _   _  ___ | |_  ___  _ __ ___
#  _   | ||  _ < | | / _ \ \___ \ | | | |/ __|| __|/ _ \| '_ ` _ \
# | |__| || |_) || || (_) |____) || |_| |\__ \| |_ | __/| | | | | |
#  \____/ |____/ |_| \___/|_____/  \__, ||___/ \__|\___||_| |_| |_|
#                                   __/ |
#                                  |___/


def get_package_directory():
    return pkg_resources.resource_filename(__name__, "")


_cwd = str(get_package_directory())

# debug
# source = str(get_package_directory())


def random_name(length=30):
    # Define a string of characters to choose from
    characters = string.ascii_letters + string.digits

    # Generate a random name by selecting random characters
    name = "".join(random.choice(characters) for _ in range(length))
    return name


def determine_rnai_top_seq(RNAi_data, gc_max=55, gc_min=35, n_max=200):
    RNAi_data = RNAi_data[(RNAi_data["GC%"] > gc_min) & (RNAi_data["GC%"] < gc_max)]

    min_spec = RNAi_data["specificity"].min()

    RNAi_data = RNAi_data[RNAi_data["specificity"] < min_spec + 1]

    RNAi_data = RNAi_data.sort_values(
        by=["specificity", "repeated_motif_pct", "complemenatry_pct", "score"],
        ascending=[True, True, True, False],
    )

    RNAi_data = RNAi_data.reset_index(drop=True)

    RNAi_data = RNAi_data.iloc[:n_max]

    return RNAi_data


def rnai_selection_to_vector(
    project,
    consensuse_dictionary,
    metadata,
    loop_seq,
    species,
    show_plot=True,
    gc_max=55,
    gc_min=35,
    end_3="UU",
    rnai_type="sh",
    length=21,
    n_max=20,
    source=_cwd,
):
    tmp = pd.DataFrame()

    consensuse_dictionary_vec = pd.DataFrame(consensuse_dictionary)
    consensuse_dictionary_vec = (
        consensuse_dictionary_vec[["seq_id", "sequence"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    for n, seq in enumerate(consensuse_dictionary_vec["sequence"]):
        RNAi_df = FindRNAi(
            seq,
            metadata,
            length=length,
            n=1500,
            max_repeat_len=3,
            species=species,
            output=None,
            database_name="refseq_select_rna",
            evalue=1,
            outfmt=5,
            word_size=7,
            max_hsps=20,
            reward=1,
            penalty=-2,
            gapopen=5,
            gapextend=2,
            dust="no",
            extension="xml",
            source=source,
        )

        if len(RNAi_df) > 0:
            RNAi_df = determine_rnai_top_seq(
                RNAi_df, gc_max=gc_max, gc_min=gc_min, n_max=n_max
            )

            RNAi_df["RNAi_name"] = [
                x + f'_{str(consensuse_dictionary_vec["seq_id"][n])}'
                for x in RNAi_df["RNAi_name"]
            ]
            RNAi_df["RNAi_group"] = str(consensuse_dictionary_vec["seq_id"][n])

            for ix in RNAi_df.index:
                if (
                    "Homo sapiens" in RNAi_df["species"][ix]
                    and "Mus musculus" in RNAi_df["species"][ix]
                    and "Rattus norvegicus" not in RNAi_df["species"][ix]
                ):
                    RNAi_df["RNAi_name"][ix] = RNAi_df["RNAi_name"][ix] + "_hs_mm"
                elif (
                    "Homo sapiens" in RNAi_df["species"][ix]
                    and "Mus musculus" in RNAi_df["species"][ix]
                    and "Rattus norvegicus" in RNAi_df["species"][ix]
                ):
                    RNAi_df["RNAi_name"][ix] = RNAi_df["RNAi_name"][ix] + "_hs_mm_rn"
                elif (
                    "Homo sapiens" in RNAi_df["species"][ix]
                    and "Mus musculus" not in RNAi_df["species"][ix]
                    and "Rattus norvegicus" not in RNAi_df["species"][ix]
                ):
                    RNAi_df["RNAi_name"][ix] = RNAi_df["RNAi_name"][ix] + "_hs"
                elif (
                    "Homo sapiens" not in RNAi_df["species"][ix]
                    and "Mus musculus" in RNAi_df["species"][ix]
                    and "Rattus norvegicus" not in RNAi_df["species"][ix]
                ):
                    RNAi_df["RNAi_name"][ix] = RNAi_df["RNAi_name"][ix] + "_mm"
                elif (
                    "Homo sapiens" not in RNAi_df["species"][ix]
                    and "Mus musculus" not in RNAi_df["species"][ix]
                    and "Rattus norvegicus" in RNAi_df["species"][ix]
                ):
                    RNAi_df["RNAi_name"][ix] = RNAi_df["RNAi_name"][ix] + "_rn"
                elif (
                    "Homo sapiens" in RNAi_df["species"][ix]
                    and "Mus musculus" not in RNAi_df["species"][ix]
                    and "Rattus norvegicus" in RNAi_df["species"][ix]
                ):
                    RNAi_df["RNAi_name"][ix] = RNAi_df["RNAi_name"][ix] + "_hs_rn"
                else:
                    RNAi_df["RNAi_name"][ix] = RNAi_df["RNAi_name"][ix]

            tmp = pd.concat([tmp, RNAi_df])

    tmp = tmp.reset_index(drop=True)

    if len(tmp) > 0:
        if rnai_type.lower() == "sh":
            RNAi_data = loop_complementary_adjustment(tmp, loop_seq, min_length=3)

            try:
                if (
                    isinstance(project["transcripts"]["sequences"]["sequence"], str)
                    and len(project["transcripts"]["sequences"]["sequence"]) > 50
                ):
                    RNAi_data = remove_specific_to_sequence(
                        RNAi_data,
                        project["transcripts"]["sequences"]["sequence"],
                        min_length=10,
                    )

                elif (
                    isinstance(project["transcripts"]["sequences"]["sequence"], list)
                    and len(project["transcripts"]["sequences"]["sequence"]) > 0
                    and len(project["transcripts"]["sequences"]["sequence"][0]) > 50
                ):
                    RNAi_data = remove_specific_to_sequence(
                        RNAi_data,
                        project["transcripts"]["sequences"]["sequence"],
                        min_length=10,
                    )

            except:
                pass

            RNAi_data = RNAi_data.sort_values(
                by=["specificity", "repeated_motif_pct", "score", "complemenatry_pct"],
                ascending=[True, True, False, True],
            ).reset_index(drop=True)

            seq = (
                str(RNAi_data["RNAi_sense"][0])
                + str(loop_seq)
                + str(RNAi_data["RNAi_seq"][0])
                + str(end_3)
            )

            if len(RNAi_data.index) > 0:
                figure, dot = predict_structure(
                    dna_to_rna(seq, enrichment=False),
                    anty_sequence="",
                    height=None,
                    width=None,
                    dis_alpha=0.35,
                    seq_force=27,
                    pair_force=8,
                    show_plot=show_plot,
                )

                project["rnai"]["full_data"] = RNAi_data.to_dict(orient="list")
                project["rnai"]["figure"] = figure
                project["rnai"]["dot"] = dot
                project["rnai"]["full_sequence"] = seq
                project["rnai"]["sequence_sense"] = str(RNAi_data["RNAi_sense"][0])
                project["rnai"]["sequence"] = str(RNAi_data["RNAi_seq"][0])
                project["rnai"]["name"] = str(RNAi_data["RNAi_name"][0])

                # return project

            else:
                project["rnai"]["full_data"] = None
                project["rnai"]["figure"] = None
                project["rnai"]["dot"] = None
                project["rnai"]["full_sequence"] = None
                project["rnai"]["sequence_sense"] = None
                project["rnai"]["sequence"] = None
                project["rnai"]["name"] = None
                project["rnai"]["species"] = None

                # return project

        elif rnai_type.lower() == "sirna":
            RNAi_data = tmp.sort_values(
                by=["specificity", "repeated_motif_pct", "score", "complemenatry_pct"],
                ascending=[True, True, False, True],
            ).reset_index(drop=True)

            seq_rnai = str(RNAi_data["RNAi_seq"][0]) + str(end_3)
            seq_sense = str(RNAi_data["RNAi_sense"][0]) + str(end_3)

            if len(RNAi_data.index) > 0:
                figure, dot = predict_structure(
                    dna_to_rna(seq_sense, enrichment=False),
                    anty_sequence=dna_to_rna(seq_rnai, enrichment=False),
                    height=None,
                    width=None,
                    dis_alpha=0.35,
                    seq_force=27,
                    pair_force=8,
                    show_plot=show_plot,
                )

                project["rnai"]["full_data"] = RNAi_data.to_dict(orient="list")
                project["rnai"]["figure"] = figure
                project["rnai"]["dot"] = dot
                project["rnai"]["full_sequence"] = seq_sense + "&" + seq_rnai
                project["rnai"]["sequence_sense"] = seq_sense
                project["rnai"]["sequence"] = seq_rnai
                project["rnai"]["name"] = str(RNAi_data["RNAi_name"][0])

                # return project

            else:
                project["rnai"]["full_data"] = None
                project["rnai"]["figure"] = None
                project["rnai"]["dot"] = None
                project["rnai"]["full_sequence"] = None
                project["rnai"]["sequence_sense"] = None
                project["rnai"]["sequence"] = None
                project["rnai"]["name"] = None
                project["rnai"]["species"] = None

                # return project

    else:
        print("\nRNAi could not be determined in this query!")
        project["rnai"]["full_data"] = None
        project["rnai"]["figure"] = None
        project["rnai"]["dot"] = None
        project["rnai"]["full_sequence"] = None
        project["rnai"]["sequence_sense"] = None
        project["rnai"]["sequence"] = None
        project["rnai"]["name"] = None
        project["rnai"]["species"] = None

    return project


def create_project(project_name: str()):
    try:
        project = {
            "project": str(project_name),
            "transcripts": {},
            "rnai": {},
            "elements": {
                "promoter": {},
                "fluorescence": {},
                "linkers": {},
                "regulators": {},
                "vector": {},
            },
            "vector": {"eval": {}, "elements": {}, "fasta": {}, "graph": {}},
        }

        return project

    except:
        print("\nSomething went wrong. Check the input or contact us!")


# functional functions


def check_stop(project: dict(), codons: pd.DataFrame(), promoter: str()):
    if promoter.lower() == "single":
        try:
            if (
                len(project["transcripts"]["sequences"]["sequence"]) > 0
                and len(project["elements"]["fluorescence"]["sequence"]) > 0
            ):
                repaired = []
                for transcript in range(
                    0, len(project["transcripts"]["sequences"]["sequence"])
                ):
                    test = [
                        project["transcripts"]["sequences"]["sequence"][transcript][
                            y : y + 3
                        ]
                        for y in range(
                            0,
                            len(
                                project["transcripts"]["sequences"]["sequence"][
                                    transcript
                                ]
                            ),
                            3,
                        )
                    ]
                    if test[-1] in list(codons["Triplet"][codons["Amino acid"] == "*"]):
                        repaired.append(
                            project["transcripts"]["sequences"]["sequence"][transcript][
                                0 : len(
                                    project["transcripts"]["sequences"]["sequence"][
                                        transcript
                                    ]
                                )
                                - 3
                            ]
                        )
                    else:
                        repaired.append(
                            project["transcripts"]["sequences"]["sequence"][transcript]
                        )
            elif (
                len(project["transcripts"]["sequences"]["sequence"]) > 1
                and len(project["elements"]["fluorescence"]["sequence"]) == 0
            ):
                repaired = []
                for transcript in range(
                    0, len(project["transcripts"]["sequences"]["sequence"])
                ):
                    test = [
                        project["transcripts"]["sequences"]["sequence"][transcript][
                            y : y + 3
                        ]
                        for y in range(
                            0,
                            len(
                                project["transcripts"]["sequences"]["sequence"][
                                    transcript
                                ]
                            ),
                            3,
                        )
                    ]
                    if transcript < max(
                        range(0, len(project["transcripts"]["sequences"]["sequence"]))
                    ) and test[-1] in list(
                        codons["Triplet"][codons["Amino acid"] == "*"]
                    ):
                        repaired.append(
                            project["transcripts"]["sequences"]["sequence"][transcript][
                                0 : len(
                                    project["transcripts"]["sequences"]["sequence"][
                                        transcript
                                    ]
                                )
                                - 3
                            ]
                        )
                    else:
                        repaired.append(
                            project["transcripts"]["sequences"]["sequence"][transcript]
                        )

            else:
                repaired = project["transcripts"]["sequences"]["sequence"]
        except:
            if len(project["transcripts"]["sequences"]["sequence"]) > 1:
                repaired = []
                for transcript in range(
                    0, len(project["transcripts"]["sequences"]["sequence"])
                ):
                    test = [
                        project["transcripts"]["sequences"]["sequence"][transcript][
                            y : y + 3
                        ]
                        for y in range(
                            0,
                            len(
                                project["transcripts"]["sequences"]["sequence"][
                                    transcript
                                ]
                            ),
                            3,
                        )
                    ]
                    if transcript < max(
                        range(0, len(project["transcripts"]["sequences"]["sequence"]))
                    ) and test[-1] in list(
                        codons["Triplet"][codons["Amino acid"] == "*"]
                    ):
                        repaired.append(
                            project["transcripts"]["sequences"]["sequence"][transcript][
                                0 : len(
                                    project["transcripts"]["sequences"]["sequence"][
                                        transcript
                                    ]
                                )
                                - 3
                            ]
                        )
                    else:
                        repaired.append(
                            project["transcripts"]["sequences"]["sequence"][transcript]
                        )

            else:
                repaired = project["transcripts"]["sequences"]["sequence"]

    elif promoter.lower() == "multi":
        if (
            len(project["transcripts"]["sequences"]["sequence"]) > 1
            and len(project["elements"]["fluorescence"]["sequence"]) > 0
        ):
            repaired = []
            for transcript in range(
                0, len(project["transcripts"]["sequences"]["sequence"])
            ):
                test = [
                    project["transcripts"]["sequences"]["sequence"][transcript][
                        y : y + 3
                    ]
                    for y in range(
                        0,
                        len(
                            project["transcripts"]["sequences"]["sequence"][transcript]
                        ),
                        3,
                    )
                ]
                if transcript < max(
                    range(0, len(project["transcripts"]["sequences"]["sequence"]))
                ) and test[-1] in list(codons["Triplet"][codons["Amino acid"] == "*"]):
                    repaired.append(
                        project["transcripts"]["sequences"]["sequence"][transcript][
                            0 : len(
                                project["transcripts"]["sequences"]["sequence"][
                                    transcript
                                ]
                            )
                            - 3
                        ]
                    )
                else:
                    repaired.append(
                        project["transcripts"]["sequences"]["sequence"][transcript]
                    )

        elif (
            len(project["transcripts"]["sequences"]["sequence"]) > 0
            and len(project["elements"]["fluorescence"]["sequence"]) == 0
        ):
            repaired = []
            for transcript in range(
                0, len(project["transcripts"]["sequences"]["sequence"])
            ):
                test = [
                    project["transcripts"]["sequences"]["sequence"][transcript][
                        y : y + 3
                    ]
                    for y in range(
                        0,
                        len(
                            project["transcripts"]["sequences"]["sequence"][transcript]
                        ),
                        3,
                    )
                ]
                if transcript < max(
                    range(0, len(project["transcripts"]["sequences"]["sequence"]))
                ) and test[-1] in list(codons["Triplet"][codons["Amino acid"] == "*"]):
                    repaired.append(
                        project["transcripts"]["sequences"]["sequence"][transcript][
                            0 : len(
                                project["transcripts"]["sequences"]["sequence"][
                                    transcript
                                ]
                            )
                            - 3
                        ]
                    )
                else:
                    repaired.append(
                        project["transcripts"]["sequences"]["sequence"][transcript]
                    )

        else:
            repaired = project["transcripts"]["sequences"]["sequence"]

    project["transcripts"]["sequences"]["vector_sequence"] = repaired

    print("\nSTOP codons reduced to optimal amount for proper working of vector")

    return project


def sequence_enrichment(
    project, metadata, species, run=True, GC_pct: int = 58, correct_rep: int = 7
):
    try:
        codons = metadata["codons"]

        if species.lower() in ["both", "both2", "multi"]:
            species = "human"

        project["transcripts"]["sequences"]["vector_sequence_GC"] = []
        project["transcripts"]["sequences"]["vector_sequence_frequence"] = []
        project["transcripts"]["sequences"]["optimized_vector_sequence"] = []
        project["transcripts"]["sequences"]["optimized_vector_sequence_GC"] = []
        project["transcripts"]["sequences"]["optimized_vector_sequence_frequence"] = []
        project["transcripts"]["sequences"]["sequence_aa"] = []

        if run == True:
            for tn in range(0, len(project["transcripts"]["sequences"]["sequence"])):
                tmp = codon_otymization(
                    project["transcripts"]["sequences"]["vector_sequence"][tn],
                    metadata,
                    species,
                    GC_pct,
                    correct_rep,
                )
                project["transcripts"]["sequences"]["vector_sequence_GC"].append(
                    tmp["GC%"][0]
                )
                project["transcripts"]["sequences"]["vector_sequence_frequence"].append(
                    tmp["frequence"][0]
                )
                project["transcripts"]["sequences"]["optimized_vector_sequence"].append(
                    tmp["sequence_na"][1]
                )
                project["transcripts"]["sequences"][
                    "optimized_vector_sequence_GC"
                ].append(tmp["GC%"][1])
                project["transcripts"]["sequences"][
                    "optimized_vector_sequence_frequence"
                ].append(tmp["frequence"][1])
                project["transcripts"]["sequences"]["sequence_aa"].append(
                    tmp["sequence_aa"][1]
                )
        else:
            codons = codons[codons["Species"] == species.lower()]
            for tn in range(0, len(project["transcripts"]["sequences"]["sequence"])):
                sequence = project["transcripts"]["sequences"]["sequence"][tn]
                seq_codon = [
                    sequence[y : y + 3].upper() for y in range(0, len(sequence), 3)
                ]
                seq_codon_fr = [
                    codons["Fraction"][codons["Triplet"] == seq.upper()][
                        codons["Fraction"][codons["Triplet"] == seq.upper()].index[0]
                    ]
                    for seq in seq_codon
                ]
                seq_codon_fr = round(sum(seq_codon_fr) / len(seq_codon_fr), 2)

                seq_codon_GC = (
                    ("".join(seq_codon).count("C") + "".join(seq_codon).count("G"))
                    / len("".join(seq_codon))
                    * 100
                )
                seq_aa = []
                for element in seq_codon:
                    tmp = codons["Amino acid"][codons["Triplet"] == element.upper()]
                    tmp = tmp.reset_index()
                    seq_aa.append(tmp["Amino acid"][0])

                project["transcripts"]["sequences"]["vector_sequence_GC"].append(
                    seq_codon_GC
                )
                project["transcripts"]["sequences"]["vector_sequence_frequence"].append(
                    seq_codon_fr
                )
                project["transcripts"]["sequences"]["optimized_vector_sequence"].append(
                    None
                )
                project["transcripts"]["sequences"][
                    "optimized_vector_sequence_GC"
                ].append(None)
                project["transcripts"]["sequences"][
                    "optimized_vector_sequence_frequence"
                ].append(None)
                project["transcripts"]["sequences"]["sequence_aa"].append(
                    "".join(seq_aa)
                )

            print("\nSequence optimization skipped")

        return project

    except:
        print("\nSomething went wrong. Check the input or contact us!")


def sequence_enrichment_denovo(
    project, metadata, species, run=True, GC_pct: int = 58, correct_rep: int = 7
):
    try:
        codons = metadata["codons"]

        if species.lower() in ["both", "both2", "multi"]:
            species = "human"

        if run == True:
            tmp = codon_otymization(
                project["transcripts"]["sequences"]["sequence"],
                metadata,
                species,
                GC_pct,
                correct_rep,
            )
            project["transcripts"]["sequences"]["sequence_GC"] = tmp["GC%"][0]
            project["transcripts"]["sequences"]["sequence_frequence"] = tmp[
                "frequence"
            ][0]
            project["transcripts"]["sequences"]["optimized_sequence"] = tmp[
                "sequence_na"
            ][1]
            project["transcripts"]["sequences"]["optimized_sequence_GC"] = tmp["GC%"][1]
            project["transcripts"]["sequences"]["optimized_sequence_frequence"] = tmp[
                "frequence"
            ][1]
            project["transcripts"]["sequences"]["sequence_aa"] = tmp["sequence_aa"][1]
        else:
            codons = codons[codons["Species"] == species.lower()]
            sequence = project["transcripts"]["sequences"]["sequence"]
            seq_codon = [
                sequence[y : y + 3].upper() for y in range(0, len(sequence), 3)
            ]
            seq_codon_fr = [
                codons["Fraction"][codons["Triplet"] == seq.upper()][
                    codons["Fraction"][codons["Triplet"] == seq.upper()].index[0]
                ]
                for seq in seq_codon
            ]
            seq_codon_fr = round(sum(seq_codon_fr) / len(seq_codon_fr), 2)

            seq_codon_GC = (
                ("".join(seq_codon).count("C") + "".join(seq_codon).count("G"))
                / len("".join(seq_codon))
                * 100
            )
            seq_aa = []
            for element in seq_codon:
                tmp = codons["Amino acid"][codons["Triplet"] == element.upper()]
                tmp = tmp.reset_index()
                seq_aa.append(tmp["Amino acid"][0])

            project["transcripts"]["sequences"]["sequence_GC"] = seq_codon_GC
            project["transcripts"]["sequences"]["sequence_frequence"] = seq_codon_fr
            project["transcripts"]["sequences"]["optimized_sequence"] = None
            project["transcripts"]["sequences"]["optimized_sequence_GC"] = None
            project["transcripts"]["sequences"]["optimized_sequence_frequence"] = None
            project["transcripts"]["sequences"]["sequence_aa"] = "".join(seq_aa)

            print("\nSequence optimization skipped")

        return project

    except:
        print("\nSomething went wrong. Check the input or contact us!")


def sequence_enrichment_alternative(
    project,
    input_dict,
    metadata,
    species,
    run=True,
    GC_pct: int = 58,
    correct_rep: int = 7,
):
    try:
        codons = metadata["codons"]

        if species.lower() in ["both", "both2", "multi"]:
            species = "human"

        project["transcripts"]["alternative"] = {}

        for n, g in enumerate([GC_pct - 5, GC_pct + 5]):
            # transcripts
            if len(input_dict["sequences"]) == len(input_dict["sequences_names"]):
                seq_vec = [
                    "SEQ" + str(l + 1) for l in range(len(input_dict["sequences"]))
                ]
                project["transcripts"]["alternative"][f"var{n}"] = {}
                project["transcripts"]["alternative"][f"var{n}"]["SEQ"] = seq_vec
                project["transcripts"]["alternative"][f"var{n}"]["sequence"] = (
                    input_dict["sequences"]
                )
                project["transcripts"]["alternative"][f"var{n}"]["name"] = input_dict[
                    "sequences_names"
                ]

                project["transcripts"]["alternative"][f"var{n}"]["sequence_GC"] = []
                project["transcripts"]["alternative"][f"var{n}"][
                    "sequence_frequence"
                ] = []
                project["transcripts"]["alternative"][f"var{n}"][
                    "optimized_sequence"
                ] = []
                project["transcripts"]["alternative"][f"var{n}"][
                    "optimized_sequence_GC"
                ] = []
                project["transcripts"]["alternative"][f"var{n}"][
                    "optimized_sequence_frequence"
                ] = []
                project["transcripts"]["alternative"][f"var{n}"]["sequence_aa"] = []

                for tn in range(
                    0, len(project["transcripts"]["alternative"][f"var{n}"]["sequence"])
                ):
                    tmp = codon_otymization(
                        project["transcripts"]["alternative"][f"var{n}"]["sequence"][
                            tn
                        ],
                        metadata,
                        species,
                        g,
                        correct_rep,
                    )
                    project["transcripts"]["alternative"][f"var{n}"][
                        "sequence_GC"
                    ].append(tmp["GC%"][0])
                    project["transcripts"]["alternative"][f"var{n}"][
                        "sequence_frequence"
                    ].append(tmp["frequence"][0])
                    project["transcripts"]["alternative"][f"var{n}"][
                        "optimized_sequence"
                    ].append(tmp["sequence_na"][1])
                    project["transcripts"]["alternative"][f"var{n}"][
                        "optimized_sequence_GC"
                    ].append(tmp["GC%"][1])
                    project["transcripts"]["alternative"][f"var{n}"][
                        "optimized_sequence_frequence"
                    ].append(tmp["frequence"][1])
                    project["transcripts"]["alternative"][f"var{n}"][
                        "sequence_aa"
                    ].append(tmp["sequence_aa"][1])

        return project

    except:
        print("\nSomething went wrong. Check the input or contact us!")


def sequence_enrichment_alternative_denovo(
    project,
    input_dict,
    metadata,
    species,
    run=True,
    GC_pct: int = 58,
    correct_rep: int = 7,
):
    try:
        codons = metadata["codons"]

        if species.lower() in ["both", "both2", "multi"]:
            species = "human"

        project["transcripts"]["alternative"] = {}

        for n, g in enumerate([GC_pct - 5, GC_pct + 5]):
            project["transcripts"]["alternative"][f"var{n}"] = {}
            project["transcripts"]["alternative"][f"var{n}"]["sequence"] = input_dict[
                "sequence"
            ]
            project["transcripts"]["alternative"][f"var{n}"]["name"] = input_dict[
                "sequence_name"
            ]

            tmp = codon_otymization(
                project["transcripts"]["alternative"][f"var{n}"]["sequence"],
                metadata,
                species,
                g,
                correct_rep,
            )
            project["transcripts"]["alternative"][f"var{n}"]["sequence_GC"] = tmp[
                "GC%"
            ][0]
            project["transcripts"]["alternative"][f"var{n}"]["sequence_frequence"] = (
                tmp["frequence"][0]
            )
            project["transcripts"]["alternative"][f"var{n}"]["optimized_sequence"] = (
                tmp["sequence_na"][1]
            )
            project["transcripts"]["alternative"][f"var{n}"][
                "optimized_sequence_GC"
            ] = tmp["GC%"][1]
            project["transcripts"]["alternative"][f"var{n}"][
                "optimized_sequence_frequence"
            ] = tmp["frequence"][1]
            project["transcripts"]["alternative"][f"var{n}"]["sequence_aa"] = tmp[
                "sequence_aa"
            ][1]

        return project

    except:
        print("\nSomething went wrong. Check the input or contact us!")


def find_restriction_vector_alternative(project, metadata, run=True):
    iter_list = project["transcripts"]["alternative"].keys()

    for n, _ in enumerate(iter_list):
        project["transcripts"]["alternative"][f"var{n}"]["full_restriction"] = []
        project["transcripts"]["alternative"][f"var{n}"]["enzymes_df"] = []
        project["transcripts"]["alternative"][f"var{n}"]["not_repaired"] = []

        if run == True:
            for trans in range(
                0, len(project["transcripts"]["alternative"][f"var{n}"]["name"])
            ):
                full, coordinates = check_restriction(
                    str(
                        project["transcripts"]["alternative"][f"var{n}"][
                            "optimized_sequence"
                        ][trans]
                    ),
                    metadata,
                )
                project["transcripts"]["alternative"][f"var{n}"][
                    "full_restriction"
                ].append(full.to_dict())
                project["transcripts"]["alternative"][f"var{n}"]["enzymes_df"].append(
                    coordinates.to_dict()
                )
        else:
            print("\nRestriction places finding skipped")

    return project


def find_restriction_vector_alternative_denovo(project, metadata, run=True):
    iter_list = project["transcripts"]["alternative"].keys()

    for n, _ in enumerate(iter_list):
        if run == True:
            full, coordinates = check_restriction(
                str(
                    project["transcripts"]["alternative"][f"var{n}"][
                        "optimized_sequence"
                    ]
                ),
                metadata,
            )
            project["transcripts"]["alternative"][f"var{n}"][
                "full_restriction"
            ] = full.to_dict()
            project["transcripts"]["alternative"][f"var{n}"][
                "enzymes_df"
            ] = coordinates.to_dict()
        else:
            print("\nRestriction places finding skipped")

    return project


def repair_restriction_vector_alternative(project, metadata, species):
    codons = metadata["codons"]

    iter_list = project["transcripts"]["alternative"].keys()

    for n, _ in enumerate(iter_list):
        if len(project["transcripts"]["alternative"][f"var{n}"]["enzymes"]) != 0:
            for trans in range(
                0, len(project["transcripts"]["alternative"][f"var{n}"]["name"])
            ):
                (
                    final_sequence,
                    not_repaired,
                    enzyme_restriction,
                    restriction_df,
                ) = repair_sequences(
                    project["transcripts"]["alternative"][f"var{n}"][
                        "optimized_sequence"
                    ][trans],
                    metadata,
                    project["transcripts"]["alternative"][f"var{n}"][
                        "full_restriction"
                    ][trans],
                    project["transcripts"]["alternative"][f"var{n}"]["enzymes"][trans],
                    species,
                )

                project["transcripts"]["alternative"][f"var{n}"]["optimized_sequence"][
                    trans
                ] = final_sequence
                project["transcripts"]["alternative"][f"var{n}"]["not_repaired"].append(
                    not_repaired
                )
                project["transcripts"]["alternative"][f"var{n}"]["full_restriction"][
                    trans
                ] = enzyme_restriction.to_dict()
                project["transcripts"]["alternative"][f"var{n}"]["enzymes_df"][
                    trans
                ] = restriction_df.to_dict()

                project["transcripts"]["alternative"][f"var{n}"][
                    "optimized_sequence_GC"
                ][trans] = (
                    (
                        project["transcripts"]["alternative"][f"var{n}"][
                            "optimized_sequence"
                        ][trans].count("C")
                        + project["transcripts"]["alternative"][f"var{n}"][
                            "optimized_sequence"
                        ][trans].count("G")
                    )
                    / len(
                        project["transcripts"]["alternative"][f"var{n}"][
                            "optimized_sequence"
                        ][trans]
                    )
                    * 100
                )

                seq_codon = [
                    project["transcripts"]["alternative"][f"var{n}"][
                        "optimized_sequence"
                    ][trans][y : y + 3]
                    for y in range(
                        0,
                        len(
                            project["transcripts"]["alternative"][f"var{n}"][
                                "optimized_sequence"
                            ][trans]
                        ),
                        3,
                    )
                ]
                seq_codon = [
                    codons["Fraction"][codons["Triplet"] == seq][
                        codons["Fraction"][codons["Triplet"] == seq].index[0]
                    ]
                    for seq in seq_codon
                ]
                seq_codon = round(sum(seq_codon) / len(seq_codon), 2)

                project["transcripts"]["alternative"][f"var{n}"][
                    "optimized_sequence_frequence"
                ][trans] = seq_codon

    return project


def repair_restriction_vector_alternative_denovo(project, metadata, species):
    codons = metadata["codons"]

    iter_list = project["transcripts"]["alternative"].keys()

    for n, _ in enumerate(iter_list):
        if len(project["transcripts"]["alternative"][f"var{n}"]["enzymes"]) != 0:
            (
                final_sequence,
                not_repaired,
                enzyme_restriction,
                restriction_df,
            ) = repair_sequences(
                project["transcripts"]["alternative"][f"var{n}"]["optimized_sequence"],
                metadata,
                project["transcripts"]["alternative"][f"var{n}"]["full_restriction"],
                project["transcripts"]["alternative"][f"var{n}"]["enzymes"],
                species,
            )

            project["transcripts"]["alternative"][f"var{n}"][
                "optimized_sequence"
            ] = final_sequence
            project["transcripts"]["alternative"][f"var{n}"][
                "not_repaired"
            ] = not_repaired
            project["transcripts"]["alternative"][f"var{n}"][
                "full_restriction"
            ] = enzyme_restriction.to_dict()
            project["transcripts"]["alternative"][f"var{n}"][
                "enzymes_df"
            ] = restriction_df.to_dict()

            project["transcripts"]["alternative"][f"var{n}"][
                "optimized_sequence_GC"
            ] = (
                (
                    project["transcripts"]["alternative"][f"var{n}"][
                        "optimized_sequence"
                    ].count("C")
                    + project["transcripts"]["alternative"][f"var{n}"][
                        "optimized_sequence"
                    ].count("G")
                )
                / len(
                    project["transcripts"]["alternative"][f"var{n}"][
                        "optimized_sequence"
                    ]
                )
                * 100
            )

            seq_codon = [
                project["transcripts"]["alternative"][f"var{n}"]["optimized_sequence"][
                    y : y + 3
                ]
                for y in range(
                    0,
                    len(
                        project["transcripts"]["alternative"][f"var{n}"][
                            "optimized_sequence"
                        ]
                    ),
                    3,
                )
            ]
            seq_codon = [
                codons["Fraction"][codons["Triplet"] == seq][
                    codons["Fraction"][codons["Triplet"] == seq].index[0]
                ]
                for seq in seq_codon
            ]
            seq_codon = round(sum(seq_codon) / len(seq_codon), 2)

            project["transcripts"]["alternative"][f"var{n}"][
                "optimized_sequence_frequence"
            ] = seq_codon

    return project


################################################################################3


def select_sequence_variant(project: dict(), sequence_variant=None, **args):
    if project["transcripts"]["sequences"]["vector_sequence_GC"][0] != None:
        for i in range(0, len(project["transcripts"]["sequences"]["name"])):
            if sequence_variant == None:
                print("-------------------------------------------------------------")
                print(
                    "name : "
                    + str(
                        project["transcripts"]["sequences"]["SEQ"][i]
                        + " -> "
                        + project["transcripts"]["sequences"]["name"][i]
                    )
                )
                print("**************************************************************")
                print("Before optimization:")
                print(
                    "* GC % : "
                    + str(project["transcripts"]["sequences"]["vector_sequence_GC"][i])
                )
                print(
                    "* Mean codon frequence : "
                    + str(
                        project["transcripts"]["sequences"][
                            "vector_sequence_frequence"
                        ][i]
                    )
                )
                print("**************************************************************")
                print("After optimization:")
                print(
                    "* GC % : "
                    + str(
                        project["transcripts"]["sequences"][
                            "optimized_vector_sequence_GC"
                        ][i]
                    )
                )
                print(
                    "* Mean codon frequence : "
                    + str(
                        project["transcripts"]["sequences"][
                            "optimized_vector_sequence_frequence"
                        ][i]
                    )
                )
                print("Choose sequence: optimized [o] or not optimized [n]")

                check = True
                while check == True:
                    locals()[str("SEQ_sv" + str(i + 1))] = input(
                        "\n Writte your choose [o/n]: "
                    )
                    if (
                        str("SEQ_sv" + str(i + 1)) in locals()
                        and locals()[str("SEQ_sv" + str(i + 1))] == "o"
                        or str("SEQ_sv" + str(i + 1)) in locals()
                        and locals()[str("SEQ_sv" + str(i + 1))] == "n"
                    ):
                        check = False

            if (
                str("SEQ_sv" + str(i + 1)) in args
                and args[str("SEQ_sv" + str(i + 1))] == "o"
                or sequence_variant == True
            ):
                project["transcripts"]["sequences"]["vector_sequence"][i] = project[
                    "transcripts"
                ]["sequences"]["optimized_vector_sequence"][i]

    return project


def remove_restriction_places(restriction_df: pd.DataFrame(), enzyme_list: list() = []):
    if len(pd.DataFrame(restriction_df)) != 0 or len(enzyme_list) == 0:
        for i in restriction_df.index:
            print("-------------------------------------------------------------")
            print("id : " + str(i))
            print("name : " + restriction_df["name"][i])

        enzyme_list = []
        check = True
        enzyme_n = 1
        while check == True:
            print(
                '\nProvide enzyme id, if no restriction sites are relevant to your experiment or you have already provided all enzyme ids, write "x"'
            )
            enzyme = input("\n Enter enzyme " + str(enzyme_n) + " id: ")
            if (
                len(enzyme) != 0
                and not enzyme.isalpha()
                and int(enzyme) in restriction_df.index
            ):
                enzyme_n += 1
                enzyme_list = enzyme_list + restriction_df["index"][int(enzyme)]
            elif len(enzyme) != 0 and enzyme.upper() == "X":
                check = False

        enzyme_list = np.unique(enzyme_list)
    else:
        print("\nLack of restriction places to choose")

    return np.asarray(enzyme_list)


def find_restriction_vector(project, metadata, run=True):
    project["transcripts"]["sequences"]["full_restriction"] = []
    project["transcripts"]["sequences"]["enzymes_df"] = []
    project["transcripts"]["sequences"]["not_repaired"] = []

    if run == True:
        for trans in range(0, len(project["transcripts"]["sequences"]["name"])):
            full, coordinates = check_restriction(
                str(project["transcripts"]["sequences"]["vector_sequence"][trans]),
                metadata,
            )
            project["transcripts"]["sequences"]["full_restriction"].append(
                full.to_dict()
            )
            project["transcripts"]["sequences"]["enzymes_df"].append(
                coordinates.to_dict()
            )
    else:
        print("\nRestriction places finding skipped")

    return project


def find_restriction_vector_denovo(project, metadata, run=True):
    if run == True:
        full, coordinates = check_restriction(
            str(project["transcripts"]["sequences"]["sequence"]), metadata
        )
        project["transcripts"]["sequences"]["full_restriction"] = full.to_dict()
        project["transcripts"]["sequences"]["enzymes_df"] = coordinates.to_dict()
    else:
        print("\nRestriction places finding skipped")

    return project


def remove_restriction_vector(project: dict(), restriction: pd.DataFrame()):
    project["transcripts"]["sequences"]["enzymes"] = []
    if len(project["transcripts"]["sequences"]["full_restriction"]) != 0:
        for trans in range(0, len(project["transcripts"]["sequences"]["name"])):
            index = pd.DataFrame(
                project["transcripts"]["sequences"]["enzymes_df"][trans]
            )
            print(
                "\nChoose enzymes for "
                + str(project["transcripts"]["sequences"]["SEQ"][trans])
            )
            project["transcripts"]["sequences"]["enzymes"].append(
                remove_restriction_places(index).tolist()
            )

    return project


def add_chosen_restriction(project: dict(), list_of_list: list()):
    project["transcripts"]["sequences"]["enzymes"] = []
    for trans in list_of_list:
        project["transcripts"]["sequences"]["enzymes"].append(trans)

    return project


def repair_restriction_vector(project, metadata, species):
    codons = metadata["codons"]

    if len(project["transcripts"]["sequences"]["enzymes"]) != 0:
        for trans in range(0, len(project["transcripts"]["sequences"]["name"])):
            (
                final_sequence,
                not_repaired,
                enzyme_restriction,
                restriction_df,
            ) = repair_sequences(
                project["transcripts"]["sequences"]["vector_sequence"][trans],
                metadata,
                project["transcripts"]["sequences"]["full_restriction"][trans],
                project["transcripts"]["sequences"]["enzymes"][trans],
                species,
            )
            project["transcripts"]["sequences"]["vector_sequence"][
                trans
            ] = final_sequence
            project["transcripts"]["sequences"]["not_repaired"].append(not_repaired)
            project["transcripts"]["sequences"]["full_restriction"][
                trans
            ] = enzyme_restriction.to_dict()
            project["transcripts"]["sequences"]["enzymes_df"][
                trans
            ] = restriction_df.to_dict()

            project["transcripts"]["sequences"]["optimized_vector_sequence_GC"][
                trans
            ] = (
                (
                    project["transcripts"]["sequences"]["vector_sequence"][trans].count(
                        "C"
                    )
                    + project["transcripts"]["sequences"]["vector_sequence"][
                        trans
                    ].count("G")
                )
                / len(project["transcripts"]["sequences"]["vector_sequence"][trans])
                * 100
            )

            seq_codon = [
                project["transcripts"]["sequences"]["vector_sequence"][trans][y : y + 3]
                for y in range(
                    0,
                    len(project["transcripts"]["sequences"]["vector_sequence"][trans]),
                    3,
                )
            ]
            seq_codon = [
                codons["Fraction"][codons["Triplet"] == seq][
                    codons["Fraction"][codons["Triplet"] == seq].index[0]
                ]
                for seq in seq_codon
            ]
            seq_codon = round(sum(seq_codon) / len(seq_codon), 2)

            project["transcripts"]["sequences"]["optimized_vector_sequence_frequence"][
                trans
            ] = seq_codon

    return project


def repair_restriction_vector_denovo(project, metadata, species):
    codons = metadata["codons"]

    if len(project["transcripts"]["sequences"]["enzymes"]) != 0:
        (
            final_sequence,
            not_repaired,
            enzyme_restriction,
            restriction_df,
        ) = repair_sequences(
            project["transcripts"]["sequences"]["optimized_sequence"],
            metadata,
            project["transcripts"]["sequences"]["full_restriction"],
            project["transcripts"]["sequences"]["enzymes"],
            species,
        )
        project["transcripts"]["sequences"]["optimized_sequence"] = final_sequence
        project["transcripts"]["sequences"]["not_repaired"] = not_repaired
        project["transcripts"]["sequences"][
            "full_restriction"
        ] = enzyme_restriction.to_dict()
        project["transcripts"]["sequences"]["enzymes_df"] = restriction_df.to_dict()

        project["transcripts"]["sequences"]["optimized_sequence_GC"] = (
            (
                project["transcripts"]["sequences"]["optimized_sequence"].count("C")
                + project["transcripts"]["sequences"]["optimized_sequence"].count("G")
            )
            / len(project["transcripts"]["sequences"]["optimized_sequence"])
            * 100
        )

        seq_codon = [
            project["transcripts"]["sequences"]["optimized_sequence"][y : y + 3]
            for y in range(
                0, len(project["transcripts"]["sequences"]["optimized_sequence"]), 3
            )
        ]
        seq_codon = [
            codons["Fraction"][codons["Triplet"] == seq][
                codons["Fraction"][codons["Triplet"] == seq].index[0]
            ]
            for seq in seq_codon
        ]
        seq_codon = round(sum(seq_codon) / len(seq_codon), 2)

        project["transcripts"]["sequences"]["optimized_sequence_frequence"] = seq_codon

    return project


def vector_string(
    project: dict(),
    backbone: pd.DataFrame(),
    vector_type: str(),
    vector_function: str(),
    promoter: str(),
):
    backbone = backbone[backbone["vector_type"] == vector_type]
    backbone = backbone[backbone["function"] == vector_function]
    backbone = backbone[backbone["promoter"] == promoter]

    if vector_type.lower() == "transcription" and vector_function.lower() == "rnai":
        vector1 = str(
            backbone["operators"][backbone["element"] == "p1"][
                backbone["operators"][backbone["element"] == "p1"].index[0]
            ]
        )
        vector1 = vector1 + " + " + "RNAi"
        vector1 = vector1 + str(
            backbone["operators"][backbone["element"] == "p2"][
                backbone["operators"][backbone["element"] == "p2"].index[0]
            ]
        )

        project["vector"]["eval"] = vector1

    else:
        vector1 = str(
            backbone["operators"][backbone["element"] == "p1"][
                backbone["operators"][backbone["element"] == "p1"].index[0]
            ]
        )
        try:
            for i in project["elements"]["transcripts"]:
                vector1 = vector1 + " + " + str(i)
        except:
            None
        vector1 = vector1 + str(
            backbone["operators"][backbone["element"] == "p2"][
                backbone["operators"][backbone["element"] == "p2"].index[0]
            ]
        )

        project["vector"]["eval"] = vector1

    return project


def dataframe_to_fasta(df):
    fasta_lines = []
    for index, row in df.iterrows():
        fasta_lines.append(f">{row['element']}")

        fasta_lines.append(str(row["sequence"]))

    fasta_content = "\n".join(fasta_lines)
    return fasta_content


def eval_vector(project, vectors, vector_type, vector_function, **args):
    vectors = vectors[vectors["vector_type"] == vector_type]
    vectors = vectors[vectors["function"] == vector_function]

    data_elements = {"element": [], "name": [], "sequence": []}

    try:
        for element, n in enumerate(
            range(0, len(project["transcripts"]["sequences"]["name"]))
        ):
            data_elements["element"].append(
                str(project["transcripts"]["sequences"]["SEQ"][n])
            )
            data_elements["name"].append(
                str(project["transcripts"]["sequences"]["name"][n])
            )
            data_elements["sequence"].append(
                str(project["transcripts"]["sequences"]["vector_sequence"][n])
            )
    except:
        None

    try:
        data_elements["sequence"].append(str(project["rnai"]["sequence"]))
        data_elements["element"].append(str("RNAi"))
        data_elements["name"].append(str(project["rnai"]["name"]))

    except:
        None

    elements = project["vector"]["eval"].split()
    tf = [x != "+" for x in elements]
    elemensts = [i for indx, i in enumerate(elements) if tf[indx] == True]

    for element, n in enumerate(project["elements"]):
        if n == "promoter":
            try:
                data_elements["sequence"].append(
                    str(project["elements"][n]["sequence"])
                )
                data_elements["element"].append(str("Promoter"))
                data_elements["name"].append(str(project["elements"][n]["name"]))

            except:
                data_elements["element"].append(str("Promoter"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

        elif n == "promoter_ncrna":
            try:
                data_elements["sequence"].append(
                    str(project["elements"][n]["sequence"])
                )
                data_elements["element"].append(str("Promoter_ncRNA"))
                data_elements["name"].append(str(project["elements"][n]["name"]))

            except:
                data_elements["element"].append(str("Promoter_ncRNA"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

        elif n == "5`UTR":
            try:
                data_elements["sequence"].append(
                    str(project["elements"][n]["sequence"])
                )
                data_elements["element"].append(str("5`UTR"))
                data_elements["name"].append(str(project["elements"][n]["name"]))

            except:
                data_elements["element"].append(str("5`UTR"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

        elif n == "3`UTR":
            try:
                data_elements["sequence"].append(
                    str(project["elements"][n]["sequence"])
                )
                data_elements["element"].append(str("3`UTR"))
                data_elements["name"].append(str(project["elements"][n]["name"]))

            except:
                data_elements["element"].append(str("3`UTR"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

        elif n == "PolyA_tail":
            try:
                data_elements["sequence"].append(
                    str(project["elements"][n]["sequence"])
                )
                data_elements["element"].append(str("PolyA_tail"))
                data_elements["name"].append(str(project["elements"][n]["name"]))

            except:
                data_elements["element"].append(str("PolyA_tail"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

        elif n == "fluorescence":
            try:
                data_elements["sequence"].append(
                    str(project["elements"][n]["sequence"])
                )
                data_elements["element"].append(str("Fluorescent_tag"))
                data_elements["name"].append(str(project["elements"][n]["name"]))

            except:
                data_elements["element"].append(str("Fluorescent_tag"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

            try:
                data_elements["sequence"].append(str(project["elements"][n]["linker"]))
                data_elements["element"].append(str("Fluorescent_tag_linker"))
                data_elements["name"].append(str(project["elements"][n]["linker_name"]))

            except:
                data_elements["element"].append(str("Fluorescent_tag_linker"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

            try:
                data_elements["sequence"].append(
                    str(project["elements"][n]["polya_seq"])
                )
                data_elements["element"].append(str("2nd_polyA_signal"))
                data_elements["name"].append(
                    str(project["elements"][n]["polya_seq_name"])
                )

            except:
                data_elements["element"].append(str("2nd_polyA_signal"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

            try:
                data_elements["sequence"].append(
                    str(project["elements"][n]["promoter_seq"])
                )
                data_elements["element"].append(str("2nd_promoter"))
                data_elements["name"].append(
                    str(project["elements"][n]["promoter_name"])
                )

            except:
                data_elements["element"].append(str("2nd_promoter"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

        elif n == "vector":
            try:
                if "Resistance_R_" in elements:
                    data_elements["sequence"].append(
                        reverse(str(project["elements"][n]["selection_marker"]))
                    )
                    data_elements["element"].append(str("Resistance"))
                    data_elements["name"].append(
                        str(project["elements"][n]["selection_marker_name"])
                    )

                else:
                    data_elements["sequence"].append(
                        str(project["elements"][n]["selection_marker"])
                    )
                    data_elements["element"].append(str("Resistance"))
                    data_elements["name"].append(
                        str(project["elements"][n]["selection_marker_name"])
                    )

            except:
                data_elements["element"].append(str("Resistance"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

        elif n == "regulators":
            try:
                data_elements["sequence"].append(
                    str(project["elements"][n]["enhancer"])
                )
                data_elements["element"].append(str("Enhancer"))
                data_elements["name"].append(
                    str(project["elements"][n]["enhancer_name"])
                )

            except:
                data_elements["element"].append(str("Enhancer"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

            try:
                data_elements["sequence"].append(str(project["elements"][n]["polya"]))
                data_elements["element"].append(str("PolyA_signal"))
                data_elements["name"].append(str(project["elements"][n]["polya_name"]))

            except:
                data_elements["element"].append(str("PolyA_signal"))
                data_elements["name"].append(str(""))
                data_elements["sequence"].append(str(""))

        elif n == "linkers" and len(project["elements"][n]) != 0:
            for r in range(int(len(project["elements"]["linkers"].keys()) / 2)):
                try:
                    data_elements["sequence"].append(
                        str(project["elements"]["linkers"]["linker_" + str(r + 1)])
                    )
                    data_elements["element"].append("Linker_" + str(r + 1))
                    data_elements["name"].append(
                        str(
                            project["elements"]["linkers"][
                                "linker_" + str(r + 1) + "_name"
                            ]
                        )
                    )

                except:
                    data_elements["element"].append("Linker_" + str(r + 1))
                    data_elements["name"].append(str(""))
                    data_elements["sequence"].append(str(""))

    data_elements = pd.DataFrame(data_elements)

    data_frame = {"element": [], "sequence": [], "start": [], "end": [], "length": []}
    fasta = ""
    start = 0
    for el in elemensts:
        el = re.sub("_R_", "", el)
        if el in list(vectors["component"]):
            data_frame["element"].append(str(el))
            data_frame["sequence"].append(
                str(
                    vectors["sequence"][vectors["component"] == el][
                        vectors["sequence"][vectors["component"] == el].index[0]
                    ]
                )
            )
            data_frame["start"].append(start + 1)
            start = start + int(
                len(
                    str(
                        vectors["sequence"][vectors["component"] == el][
                            vectors["sequence"][vectors["component"] == el].index[0]
                        ]
                    )
                )
            )
            data_frame["end"].append(start)
            data_frame["length"].append(
                len(
                    str(
                        vectors["sequence"][vectors["component"] == el][
                            vectors["sequence"][vectors["component"] == el].index[0]
                        ]
                    )
                )
            )
            fasta = fasta + str(
                vectors["sequence"][vectors["component"] == el][
                    vectors["sequence"][vectors["component"] == el].index[0]
                ]
            )
        elif el in list(data_elements["element"]):
            data_frame["element"].append(
                str(el)
                + " : "
                + str(
                    data_elements["name"][data_elements["element"] == el][
                        data_elements["name"][data_elements["element"] == el].index[0]
                    ]
                )
            )
            data_frame["sequence"].append(
                str(
                    data_elements["sequence"][data_elements["element"] == el][
                        data_elements["sequence"][data_elements["element"] == el].index[
                            0
                        ]
                    ]
                )
            )
            data_frame["start"].append(start + 1)
            start = start + int(
                len(
                    str(
                        data_elements["sequence"][data_elements["element"] == el][
                            data_elements["sequence"][
                                data_elements["element"] == el
                            ].index[0]
                        ]
                    )
                )
            )
            data_frame["end"].append(start)
            data_frame["length"].append(
                len(
                    str(
                        data_elements["sequence"][data_elements["element"] == el][
                            data_elements["sequence"][
                                data_elements["element"] == el
                            ].index[0]
                        ]
                    )
                )
            )
            fasta = fasta + str(
                data_elements["sequence"][data_elements["element"] == el][
                    data_elements["sequence"][data_elements["element"] == el].index[0]
                ]
            )

    data_frame = pd.DataFrame(data_frame)
    data_frame = data_frame[data_frame["length"] > 0]

    new_element = []
    for x in data_frame["element"]:
        if "break" in x:
            new_element.append("backbone_element")
        else:
            new_element.append(x)

    data_frame["element"] = new_element
    data_frame = data_frame.reset_index(drop=True)

    project["vector"]["elements"] = data_frame.to_dict()
    project["vector"]["full_vector_length"] = sum(list(data_frame["length"]))

    fragmented_fasta = dataframe_to_fasta(data_frame)
    gene_bank = get_genebank(
        extract_fasta_info(
            decode_fasta_to_dataframe(fragmented_fasta), ommit_pattern="backbone"
        ),
        name=str(vector_type) + "_" + str(vector_function),
        definition=str(project["project"])
        + "_"
        + str(vector_type)
        + "_"
        + str(vector_function)
        + "_"
        + str(sum(list(data_frame["length"])))
        + "nc",
    )

    if "scAAV".lower() in vector_type.lower() or "ssAAv".lower() in vector_type.lower():
        start_index = data_frame.index[data_frame["element"] == "5`ITR"].tolist()[0]
        end_index = data_frame.index[data_frame["element"] == "3`ITR"].tolist()[0]

        # Extract the relevant portion of the DataFrame
        selected_rows = data_frame.iloc[start_index : end_index + 1]

        project["vector"]["vector_insert_length"] = sum(list(selected_rows["length"]))
        project["vector"]["vector_type"] = str(vector_type)
        project["vector"]["vector_function"] = str(vector_function)
        fasta = (
            ">"
            + str(project["project"])
            + "_"
            + str(vector_type)
            + "_"
            + str(vector_function)
            + "_"
            + str(sum(list(data_frame["length"])))
            + "nc\n"
            + fasta
        )
        project["vector"]["full_fasta"] = fasta
        project["vector"]["fasta"] = (
            "# "
            + str(project["project"])
            + "_"
            + str(vector_type)
            + "_"
            + str(vector_function)
            + "_"
            + str(sum(list(data_frame["length"])))
            + "nc\n\n"
            + fragmented_fasta
        )
        project["vector"]["genebank"] = gene_bank

    elif "lentiviral".lower() in vector_type.lower():
        start_index = data_frame.index[data_frame["element"] == "5`LTR"].tolist()[0]
        end_index = data_frame.index[data_frame["element"] == "3`LTR"].tolist()[0]

        # Extract the relevant portion of the DataFrame
        selected_rows = data_frame.iloc[start_index : end_index + 1]

        project["vector"]["vector_insert_length"] = sum(list(selected_rows["length"]))
        project["vector"]["vector_type"] = str("Lentiviral")
        project["vector"]["vector_function"] = str(vector_function)
        fasta = (
            ">"
            + str(project["project"])
            + "_"
            + str("Lentiviral")
            + "_"
            + str(vector_function)
            + "_"
            + str(sum(list(data_frame["length"])))
            + "nc\n"
            + fasta
        )
        project["vector"]["full_fasta"] = fasta
        project["vector"]["fasta"] = (
            "# "
            + str(project["project"])
            + "_"
            + str("Lentiviral")
            + "_"
            + str(vector_function)
            + "_"
            + str(sum(list(data_frame["length"])))
            + "nc\n\n"
            + fragmented_fasta
        )
        project["vector"]["genebank"] = gene_bank

    else:
        project["vector"]["vector_insert_length"] = sum(list(data_frame["length"]))
        project["vector"]["vector_type"] = str("Regular plasmid")
        project["vector"]["vector_function"] = str(vector_function)
        fasta = (
            ">"
            + str(project["project"])
            + "_"
            + str("Regular_plasmid")
            + "_"
            + str(vector_function)
            + "_"
            + str(sum(list(data_frame["length"])))
            + "nc\n"
            + fasta
        )
        project["vector"]["full_fasta"] = fasta
        project["vector"]["fasta"] = (
            "#"
            + str(project["project"])
            + "_"
            + str("Regular_plasmid")
            + "_"
            + str(vector_function)
            + "_"
            + str(sum(list(data_frame["length"])))
            + "nc\n\n"
            + fragmented_fasta
        )
        project["vector"]["genebank"] = gene_bank

    return project


def vector_plot_project(project, metadata, show_plot=True):

    vector_df = pd.DataFrame(project["vector"]["elements"])

    vector_df = vector_df.sort_index(ascending=False)

    explode = []
    for i in vector_df["element"]:
        if i in "backbone_element":
            explode.append(-0.2)
        else:
            explode.append(0)

    labels = []
    for i in vector_df["element"]:
        if i in "backbone_element":
            labels.append("")
        else:
            labels.append(i)

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(aspect="equal"))

    colors = sns.color_palette("gist_ncar", len(vector_df["length"]))

    wedges, texts = ax.pie(
        vector_df["length"], explode=explode, startangle=90, colors=colors
    )

    kw = dict(arrowprops=dict(arrowstyle="-"), zorder=0, va="center")

    n = 0.25
    k = 1

    x_pie = []
    y_pie = []
    x_text = []
    y_text = []
    orient = []
    labels_set = []
    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        if len(labels[i]) > 0:
            k += 1
            if horizontalalignment == "right":
                if k < len(labels) / 2:
                    n += 0.15
                else:
                    n -= 0.15
            else:
                if k < len(labels) / 2:
                    n -= 0.15
                else:
                    n += 0.15

            x_pie.append(x)
            y_pie.append(y)
            x_text.append(x + x * 0.75)
            y_text.append(y + y * n)
            orient.append(horizontalalignment)
            labels_set.append(labels[i])

    df = pd.DataFrame(
        {
            "x_pie": x_pie,
            "y_pie": y_pie,
            "x_text": x_text,
            "y_text": y_text,
            "orient": orient,
            "labels": labels_set,
        }
    )

    df_left = df[df["orient"] == "left"]
    df_right = df[df["orient"] == "right"]

    df["x_text"][df["orient"] == "left"] = max(df_left["x_text"])
    df["x_text"][df["orient"] == "right"] = min(df_right["x_text"])

    df_list = [df_left, df_right]
    for d in df_list:
        if len(d.index) > 1:
            check = True
            while check:
                for i in d.index:
                    if (
                        i > min(d.index)
                        and df["y_text"][i - 1] > df["y_text"][i]
                        and df["orient"][i] == "left"
                    ):
                        tmp = df["y_text"][i - 1]
                        df["y_text"][i - 1] = df["y_text"][i]
                        df["y_text"][i] = tmp
                        break

                    elif (
                        i > min(d.index)
                        and df["y_text"][i - 1] < df["y_text"][i]
                        and df["orient"][i] == "right"
                    ):
                        tmp = df["y_text"][i]
                        df["y_text"][i] = df["y_text"][i - 1]
                        df["y_text"][i - 1] = tmp
                        break

                    elif (
                        i > min(d.index)
                        and (df["y_text"][i] - df["y_text"][i - 1]) < 0.25
                        and df["orient"][i] == "left"
                    ):
                        df["y_text"][i] = df["y_text"][i] + 0.25

                        break
                    elif (
                        i > min(d.index)
                        and (df["y_text"][i - 1] - df["y_text"][i]) < 0.25
                        and df["orient"][i] == "right"
                    ):
                        df["y_text"][i] = df["y_text"][i] - 0.25

                        break

                    elif i == max(d.index):
                        check = False
                        break

    arrow_props = dict(
        facecolor="gray",
        edgecolor="gray",
        arrowstyle="->",
        connectionstyle="arc3,rad=0.05",
    )

    for i in df.index:
        ax.annotate(
            df["labels"][i],
            xy=(df["x_pie"][i], df["y_pie"][i]),
            xytext=(df["x_text"][i], df["y_text"][i]),
            horizontalalignment=df["orient"][i],
            fontsize=20,
            weight="bold",
            arrowprops=arrow_props,
        )

    circle1 = plt.Circle((0, 0), 0.85, color="black")
    circle2 = plt.Circle((0, 0), 0.8, color="white")

    ax.text(
        0.5,
        0.5,
        str(
            str(project["vector"]["vector_type"])
            + "\n"
            + str(project["vector"]["vector_function"])
            + "\n Plasmid size: "
            + str(project["vector"]["full_vector_length"])
            + "nc \n Insert size: "
            + str(project["vector"]["vector_insert_length"])
            + "nc"
        ),
        transform=ax.transAxes,
        va="center",
        ha="center",
        backgroundcolor="white",
        weight="bold",
        fontsize=22,
    )

    capacity = metadata["capacity"]

    cap = str(
        capacity["capacity"][
            capacity["vector_type"] == project["vector"]["vector_type"].lower()
        ][
            capacity["capacity"][
                capacity["vector_type"] == project["vector"]["vector_type"].lower()
            ].index[0]
        ]
    )
    if int(project["vector"]["vector_insert_length"]) < int(
        capacity["capacity"][
            capacity["vector_type"] == project["vector"]["vector_type"].lower()
        ]
    ):
        ax.text(
            0.5,
            -0.7,
            f"The insert sequence of the vector is optimal for this vector type. The optimal insert for this vector is < {cap}nc",
            transform=ax.transAxes,
            va="center",
            ha="center",
            backgroundcolor="white",
            color="green",
            weight="bold",
            fontsize=22,
        )
    else:
        ax.text(
            0.5,
            -0.7,
            f"The insert sequence of the vector is not optimal for this vector type. The optimal insert for this vector should be < {cap}nc",
            transform=ax.transAxes,
            va="center",
            ha="center",
            backgroundcolor="white",
            color="red",
            weight="bold",
            fontsize=22,
        )

    p = plt.gcf()
    p.gca().add_artist(circle1)
    p.gca().add_artist(circle2)

    project["vector"]["graph"] = fig

    if show_plot == True:
        plt.show()
    elif show_plot == False:
        plt.close(fig)

    return project, fig


def create_vector_from_dict_transcription(
    metadata, input_dict, show_plot=True, source=_cwd
):
    try:
        list_to_check_rnai = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "rnai_sequence",
            "rnai_gene_name",
            "loop_sequence",
            "selection_marker_name",
            "selection_marker_sequence",
        ]

        list_to_check_mrna = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "sequences",
            "sequences_names",
            "linkers_names",
            "linkers_sequences",
            "utr5_name",
            "utr5_sequence",
            "utr3_name",
            "utr3_sequence",
            "polya_tail_x",
            "selection_marker_name",
            "selection_marker_sequence",
            "restriction_list",
            "optimize",
        ]

        if set(list_to_check_mrna).issubset(input_dict.keys()):
            must_not_zero = [
                "project_name",
                "vector_type",
                "vector_function",
                "species",
                "sequences",
                "sequences_names",
                "utr5_name",
                "utr5_sequence",
                "utr3_name",
                "utr3_sequence",
                "selection_marker_name",
                "selection_marker_sequence",
            ]

            required = []
            for be in must_not_zero:
                if len(input_dict[str(be)]) == 0:
                    required.append(be)

            length_compare = []
            if len(input_dict["sequences"]) != len(input_dict["sequences_names"]):
                length_compare.append("sequences vs. sequences_names")

            if len(input_dict["linkers_sequences"]) != len(input_dict["linkers_names"]):
                length_compare.append("linkers_sequences vs. linkers_names")

            if len(input_dict["sequences"]) > 1 and len(
                input_dict["sequences"]
            ) - 1 != len(input_dict["linkers_sequences"]):
                length_compare.append("linkers_sequences vs. sequences")

            if (
                len(input_dict["linkers_names"]) > 0
                and len(input_dict["linkers_sequences"]) == 0
            ):
                required.append("linkers_sequences")

            if (
                len(input_dict["linkers_sequences"]) > 0
                and len(input_dict["linkers_names"]) == 0
            ):
                required.append("linkers_names")

            if input_dict["optimize"] not in [True, False]:
                required.append("optimize")

            if not isinstance(input_dict["polya_tail_x"], int):
                required.append("polya_tail_x")

            seq_to_check = [
                "sequences",
                "utr5_sequence",
                "utr3_sequence",
                "selection_marker_sequence",
            ]

            not_coding = []
            not_in_upac = []
            for s in seq_to_check:
                try:
                    input_dict[s]
                    if len(input_dict[s]) > 0:
                        if isinstance(input_dict[s], list) and s == "sequences":
                            tmp = []
                            for c in input_dict[s]:
                                tmp.append(clear_sequence(c))
                                cod = check_coding(clear_sequence(c))
                                if cod == False:
                                    not_coding.append(s)
                                upc = check_upac(clear_sequence(c))
                                if upc == False:
                                    not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif (
                            isinstance(input_dict[s], list) and s == "linkers_sequences"
                        ):
                            tmp = []
                            for c in input_dict[s]:
                                tmp.append(clear_sequence(c))
                                upc = check_upac(clear_sequence(c))
                                if upc == False:
                                    not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif not isinstance(input_dict[s], list) and s == "sequences":
                            tmp = clear_sequence(input_dict[s])
                            cod = check_coding(tmp)
                            if cod == False:
                                not_coding.append(s)
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif (
                            not isinstance(input_dict[s], list)
                            and s == "linkers_sequences"
                        ):
                            tmp = clear_sequence(input_dict[s])
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif (
                            not isinstance(input_dict[s], list)
                            and s == "selection_marker_sequence"
                        ):
                            tmp = clear_sequence(input_dict[s])
                            cod = check_coding(tmp)
                            if cod == False:
                                not_coding.append(s)
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        else:
                            tmp = clear_sequence(input_dict[s])
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                except:
                    not_in_upac.append(s)

            if (
                len(required) == 0
                and len(length_compare) == 0
                and len(not_in_upac) == 0
                and len(not_coding) == 0
            ):
                project = create_project(input_dict["project_name"])
                project["transcripts"] = {}
                project["transcripts"]["sequences"] = {}
                project["elements"] = {}
                project["elements"]["linkers"] = {}
                project["elements"]["vector"] = {}
                project["elements"]["3`UTR"] = {}
                project["elements"]["5`UTR"] = {}
                project["elements"]["PolyA_tail"] = {}

                # transcripts
                if len(input_dict["sequences"]) == len(input_dict["sequences_names"]):
                    seq_vec = [
                        "SEQ" + str(l + 1) for l in range(len(input_dict["sequences"]))
                    ]
                    project["transcripts"]["sequences"]["SEQ"] = seq_vec
                    project["transcripts"]["sequences"]["sequence"] = input_dict[
                        "sequences"
                    ]
                    project["transcripts"]["sequences"]["name"] = input_dict[
                        "sequences_names"
                    ]
                    project["elements"]["transcripts"] = seq_vec

                    # linkers
                    if len(input_dict["sequences"]) > 1 and len(
                        input_dict["sequences"]
                    ) - 1 == len(input_dict["linkers_sequences"]):
                        seq_vec_linker = []
                        for n, i in enumerate(seq_vec):
                            seq_vec_linker = (
                                seq_vec_linker + [i] + ["Linker_" + str(n + 1)]
                            )
                        seq_vec_linker = seq_vec_linker[0:-1]

                        project["elements"]["transcripts"] = seq_vec_linker

                        if len(input_dict["linkers_sequences"]) == len(
                            input_dict["linkers_names"]
                        ):
                            for n, l in enumerate(input_dict["linkers_sequences"]):
                                project["elements"]["linkers"][
                                    "linker_" + str(n + 1)
                                ] = input_dict["linkers_sequences"][n]
                                project["elements"]["linkers"][
                                    "linker_" + str(n + 1) + "_name"
                                ] = input_dict["linkers_names"][n]

                    elif len(project["transcripts"]["sequences"]["sequence"]) <= 1:
                        None

                    else:
                        print("\nWrong number of linkers compareing to linkers names")

                else:
                    print(
                        "\nNumber of provided sequences is different with number of sequences names"
                    )

                # utr3
                project["elements"]["3`UTR"]["name"] = input_dict["utr3_name"]
                project["elements"]["3`UTR"]["sequence"] = input_dict["utr3_sequence"]

                # utr5
                project["elements"]["5`UTR"]["name"] = input_dict["utr5_name"]
                project["elements"]["5`UTR"]["sequence"] = input_dict["utr5_sequence"]

                # polya_tail
                project["elements"]["PolyA_tail"]["name"] = "x " + str(
                    input_dict["polya_tail_x"]
                )
                project["elements"]["PolyA_tail"]["sequence"] = (
                    "A" * input_dict["polya_tail_x"]
                )

                # restriction
                project["elements"]["vector"]["selection_marker"] = input_dict[
                    "selection_marker_sequence"
                ]
                project["elements"]["vector"]["selection_marker_name"] = input_dict[
                    "selection_marker_name"
                ]

                promoter_dec = "single"

                project = check_stop(project, metadata["codons"], promoter_dec)

                run1 = input_dict["optimize"]

                if "transcript_GC" not in input_dict.keys():
                    transcript_GC = 59
                else:
                    transcript_GC = int(input_dict["transcript_GC"])

                if "poly_len" not in input_dict.keys():
                    transcript_rep = 7
                else:
                    transcript_rep = int(input_dict["poly_len"])

                project = sequence_enrichment(
                    project,
                    metadata,
                    input_dict["species"].lower(),
                    run=run1,
                    GC_pct=transcript_GC,
                    correct_rep=transcript_rep,
                )

                if run1:
                    project = sequence_enrichment_alternative(
                        project,
                        input_dict,
                        metadata,
                        input_dict["species"].lower(),
                        run=True,
                        GC_pct=transcript_GC,
                        correct_rep=transcript_rep,
                    )
                    project = select_sequence_variant(project, sequence_variant=True)

                if len(input_dict["restriction_list"]) == 0:
                    input_dict["restriction_list"] = ["SapI", "BsiWI", "AscI"]
                else:
                    input_dict["restriction_list"] = input_dict["restriction_list"] + [
                        "SapI",
                        "BsiWI",
                        "AscI",
                    ]

                if len(input_dict["restriction_list"]) > 0:
                    run2 = True
                else:
                    run2 = False

                project = find_restriction_vector(project, metadata, run=run2)

                if run1:
                    project = find_restriction_vector_alternative(
                        project, metadata, run=run2
                    )

                if run2:
                    list_of_list = []
                    user_defined_enzymes = [
                        e.upper() for e in input_dict["restriction_list"]
                    ]
                    for trans, _ in enumerate(
                        project["transcripts"]["sequences"]["SEQ"]
                    ):
                        if len(user_defined_enzymes) > 0:
                            tmp = pd.DataFrame(
                                project["transcripts"]["sequences"]["enzymes_df"][trans]
                            )
                            tmp["name"] = [t.upper() for t in tmp["name"]]
                            en = list(
                                tmp["index"][tmp["name"].isin(user_defined_enzymes)]
                            )
                            list_tmp = [item for sublist in en for item in sublist]
                            list_of_list.append(list_tmp)
                        else:
                            list_of_list.append([])

                    project = add_chosen_restriction(project, list_of_list)
                    project = repair_restriction_vector(
                        project, metadata, input_dict["species"]
                    )

                    if run1:
                        # alternative
                        user_defined_enzymes = [
                            e.upper() for e in input_dict["restriction_list"]
                        ]
                        for n in project["transcripts"]["alternative"].keys():
                            list_of_list_a = []
                            for s, _ in enumerate(
                                project["transcripts"]["alternative"][n]["name"]
                            ):
                                if len(user_defined_enzymes) > 0:
                                    tmp = pd.DataFrame(
                                        project["transcripts"]["alternative"][n][
                                            "enzymes_df"
                                        ][s]
                                    )
                                    tmp["name"] = [t.upper() for t in tmp["name"]]
                                    en = list(
                                        tmp["index"][
                                            tmp["name"].isin(user_defined_enzymes)
                                        ]
                                    )
                                    list_tmp = [
                                        item for sublist in en for item in sublist
                                    ]
                                    list_of_list_a.append(list_tmp)
                                else:
                                    list_of_list_a.append([])

                            project["transcripts"]["alternative"][n][
                                "enzymes"
                            ] = list_of_list_a

                        project = repair_restriction_vector_alternative(
                            project, metadata, input_dict["species"]
                        )

                        ###################

                project["transcripts"]["sequences"]["sequence_figure"] = []
                project["transcripts"]["sequences"]["sequence_dot"] = []

                for tn in range(
                    0, len(project["transcripts"]["sequences"]["sequence"])
                ):
                    figure, dot = predict_structure(
                        dna_to_rna(
                            project["transcripts"]["sequences"]["sequence"][tn],
                            enrichment=False,
                        ),
                        anty_sequence="",
                        height=None,
                        width=None,
                        dis_alpha=0.1,
                        seq_force=27,
                        pair_force=3,
                        show_plot=show_plot,
                    )

                    project["transcripts"]["sequences"]["sequence_figure"].append(
                        figure
                    )
                    project["transcripts"]["sequences"]["sequence_dot"].append(dot)

                if run1:
                    project["transcripts"]["sequences"][
                        "optimized_sequence_figure"
                    ] = []
                    project["transcripts"]["sequences"]["optimized_sequence_dot"] = []

                    for tn in range(
                        0, len(project["transcripts"]["sequences"]["vector_sequence"])
                    ):
                        figure, dot = predict_structure(
                            dna_to_rna(
                                project["transcripts"]["sequences"]["vector_sequence"][
                                    tn
                                ],
                                enrichment=False,
                            ),
                            anty_sequence="",
                            height=None,
                            width=None,
                            dis_alpha=0.1,
                            seq_force=27,
                            pair_force=3,
                            show_plot=show_plot,
                        )

                        project["transcripts"]["sequences"][
                            "optimized_sequence_figure"
                        ].append(figure)
                        project["transcripts"]["sequences"][
                            "optimized_sequence_dot"
                        ].append(dot)

                project = vector_string(
                    project,
                    metadata["backbone"],
                    input_dict["vector_type"],
                    input_dict["vector_function"],
                    promoter_dec,
                )
                project = eval_vector(
                    project,
                    metadata["vectors"],
                    input_dict["vector_type"],
                    input_dict["vector_function"],
                )

                project, pl = vector_plot_project(
                    project, metadata, show_plot=show_plot
                )

            else:
                project = None
                print(
                    "\nThe project could not be created due to trouble with the lack of dictionary elements!"
                )
                if len(required) > 0:
                    print(
                        f'\nThe elements: {", ".join(required)} are required with non-zero length!'
                    )

                if len(length_compare) > 0:
                    print(
                        f'\nThe elements: {", ".join(length_compare)} are in wrong proportion. Remember that each sequence requires a sequence name, each linker requires linker_name and the number of linkers should be the number of transcripts - 1! If you do not need linkers provide an empty string ([""]) for linker_sequence and linker_name for each pair of transcripts.'
                    )

                if len(not_in_upac) > 0:
                    print(
                        f'\nThe elements: {", ".join(not_in_upac)} include characters not from the UPAC code!'
                    )

                if len(not_coding) > 0:
                    print(
                        f'\nThe elements: {", ".join(length_compare)} are not coding sequences!'
                    )

        elif set(list_to_check_rnai).issubset(input_dict.keys()):
            must_not_zero = [
                "project_name",
                "vector_type",
                "vector_function",
                "species",
                "rnai_gene_name",
                "loop_sequence",
                "selection_marker_name",
                "selection_marker_sequence",
            ]

            required = []
            for be in must_not_zero:
                if len(input_dict[str(be)]) == 0:
                    required.append(be)

            seq_to_check = [
                "rnai_sequence",
                "loop_sequence",
                "selection_marker_sequence",
            ]

            not_coding = []
            not_in_upac = []
            for s in seq_to_check:
                try:
                    input_dict[s]
                    if len(input_dict[s]) > 0:
                        if (
                            not isinstance(input_dict[s], list)
                            and s == "selection_marker_sequence"
                        ):
                            tmp = clear_sequence(input_dict[s])
                            cod = check_coding(tmp)
                            if cod == False:
                                not_coding.append(s)
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        else:
                            tmp = clear_sequence(input_dict[s])
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                except:
                    not_in_upac.append(s)

            if len(required) == 0 and len(not_in_upac) == 0 and len(not_coding) == 0:
                project = create_project(input_dict["project_name"])
                project["rnai"]["sequence"] = {}
                project["rnai"]["name"] = {}
                project["elements"]["loop"] = {}

                promoter_dec = "single"

                # rnai
                if len(input_dict["rnai_sequence"]) > 0:
                    if "overhang_3_prime" not in input_dict.keys():
                        overhang_3_prime = ""
                    else:
                        overhang_3_prime = str(input_dict["overhang_3_prime"])

                    project["rnai"]["sequence"] = (
                        input_dict["rnai_sequence"]
                        + input_dict["loop_sequence"]
                        + complement(reverse(input_dict["rnai_sequence"]))
                        + overhang_3_prime
                    )
                    project["rnai"]["name"] = input_dict["rnai_gene_name"]
                    project["rnai"]["species"] = input_dict["species"].lower()

                    figure, dot = predict_structure(
                        sequence=dna_to_rna(
                            project["rnai"]["sequence"], enrichment=False
                        ),
                        anty_sequence="",
                        height=None,
                        width=None,
                        dis_alpha=0.35,
                        seq_force=27,
                        pair_force=8,
                        show_plot=show_plot,
                    )

                    project["rnai"]["figure"] = figure
                    project["rnai"]["dot"] = dot

                    # restriction
                    project["elements"]["vector"]["selection_marker"] = input_dict[
                        "selection_marker_sequence"
                    ]
                    project["elements"]["vector"]["selection_marker_name"] = input_dict[
                        "selection_marker_name"
                    ]

                    project = vector_string(
                        project,
                        metadata["backbone"],
                        input_dict["vector_type"],
                        input_dict["vector_function"],
                        promoter_dec,
                    )
                    project = eval_vector(
                        project,
                        metadata["vectors"],
                        input_dict["vector_type"],
                        input_dict["vector_function"],
                    )

                    project, pl = vector_plot_project(
                        project, metadata, show_plot=show_plot
                    )

                else:
                    project["elements"]["loop"] = input_dict["loop_sequence"]
                    refseq_sequences = get_sequences_gene(
                        input_dict["rnai_gene_name"], input_dict["species"]
                    )
                    if refseq_sequences != None:
                        fasta_string = generate_fasta_string(refseq_sequences)
                        alignments = MuscleMultipleSequenceAlignment(
                            fasta_string, output="results", gapopen=10, gapextend=0.5
                        )
                        consensuse_dictionary = ExtractConsensuse(
                            alignments, refseq_sequences=refseq_sequences
                        )

                        if len(consensuse_dictionary["sequence"]) == 0 and input_dict[
                            "species"
                        ] in ["both", "both2", "mutli"]:
                            print(
                                "\nThe consensus sequence for both species was unable to be created! We will try obtain consensuse for Homo sapiens!"
                            )
                            refseq_sequences = get_sequences_gene(
                                input_dict["rnai_gene_name"], "human"
                            )
                            fasta_string = generate_fasta_string(refseq_sequences)
                            alignments = MuscleMultipleSequenceAlignment(
                                fasta_string,
                                output="results",
                                gapopen=10,
                                gapextend=0.5,
                            )
                            consensuse_dictionary = ExtractConsensuse(
                                alignments, refseq_sequences=refseq_sequences
                            )
                            if len(consensuse_dictionary["sequence"]) == 0:
                                print(
                                    "\nThe consensus sequence for Homo sapiens was also unable to be created!"
                                )

                        elif len(consensuse_dictionary["sequence"]) == 0 and input_dict[
                            "species"
                        ] not in ["both", "both2", "mutli"]:
                            project = None
                            print(
                                "\nThe consensus sequence was also unable to be created!"
                            )

                        # tutaj-len

                        if "rnai_length" not in input_dict.keys():
                            rnai_length = 23
                        else:
                            rnai_length = int(input_dict["rnai_length"])

                        if "overhang_3_prime" not in input_dict.keys():
                            overhang_3_prime = ""
                        else:
                            overhang_3_prime = str(input_dict["overhang_3_prime"])

                        if (
                            len(consensuse_dictionary["sequence"]) > 0
                            or refseq_sequences != None
                        ):
                            project = rnai_selection_to_vector(
                                project,
                                consensuse_dictionary,
                                metadata,
                                project["elements"]["loop"],
                                input_dict["species"].lower(),
                                end_3=overhang_3_prime,
                                show_plot=show_plot,
                                rnai_type="sh",
                                length=rnai_length,
                                n_max=500,
                                source=source,
                            )
                            if project["rnai"]["sequence"] != None:
                                project["rnai"]["name"] = (
                                    input_dict["rnai_gene_name"]
                                    + "_"
                                    + project["rnai"]["name"]
                                )
                                project["rnai"]["species"] = input_dict[
                                    "species"
                                ].lower()
                            elif project["rnai"]["sequence"] == None and input_dict[
                                "species"
                            ] in ["both", "both2", "mutli"]:
                                print(
                                    "\nThe consensus sequence for both species was unable to be created! We will try obtain consensuse for Homo sapiens!"
                                )
                                refseq_sequences = get_sequences_gene(
                                    input_dict["rnai_gene_name"], "human"
                                )
                                fasta_string = generate_fasta_string(refseq_sequences)
                                alignments = MuscleMultipleSequenceAlignment(
                                    fasta_string,
                                    output="results",
                                    gapopen=10,
                                    gapextend=0.5,
                                )
                                consensuse_dictionary = ExtractConsensuse(
                                    alignments, refseq_sequences=refseq_sequences
                                )
                                if len(consensuse_dictionary["sequence"]) == 0:
                                    print(
                                        "\nThe consensus sequence for Homo sapiens was also unable to be created!"
                                    )
                                    project = None
                                elif len(consensuse_dictionary["sequence"]) > 0:
                                    project = rnai_selection_to_vector(
                                        project,
                                        consensuse_dictionary,
                                        metadata,
                                        project["elements"]["loop"],
                                        input_dict["species"].lower(),
                                        end_3=overhang_3_prime,
                                        show_plot=show_plot,
                                        rnai_type="sh",
                                        length=rnai_length,
                                        n_max=500,
                                        source=source,
                                    )
                                    if project["rnai"]["sequence"] != None:
                                        project["rnai"]["name"] = (
                                            input_dict["rnai_gene_name"]
                                            + "_"
                                            + project["rnai"]["name"]
                                        )
                                        project["rnai"]["species"] = "human"

                                    else:
                                        project = None
                                        print(
                                            "\nThe project could not be created due to trouble with the RNAi selection!"
                                        )
                            else:
                                project = None
                                print(
                                    "\nThe project could not be created due to trouble with the RNAi selection!"
                                )

                            if project != None:
                                # restriction
                                project["elements"]["vector"]["selection_marker"] = (
                                    input_dict["selection_marker_sequence"]
                                )
                                project["elements"]["vector"][
                                    "selection_marker_name"
                                ] = input_dict["selection_marker_name"]

                                project = vector_string(
                                    project,
                                    metadata["backbone"],
                                    input_dict["vector_type"],
                                    input_dict["vector_function"],
                                    promoter_dec,
                                )
                                project = eval_vector(
                                    project,
                                    metadata["vectors"],
                                    input_dict["vector_type"],
                                    input_dict["vector_function"],
                                )

                                project, pl = vector_plot_project(
                                    project, metadata, show_plot=show_plot
                                )

                        else:
                            project = None

                            print(
                                "\nThe project could not be created due to trouble with the consensus sequence obtained. You can try to prepare custom RNAi and paste it into the project next time!"
                            )

                    else:
                        project = None

                        print(
                            "\nThe project could not be created due to trouble with the consensus sequence obtained. You can try to prepare custom RNAi and paste it into the project next time!"
                        )

            else:
                project = None
                print(
                    "\nThe project could not be created due to trouble with the lack of dictionary elements!"
                )
                if len(required) > 0:
                    print(
                        f'\nThe elements: {", ".join(required)} are required with non-zero length!'
                    )

                if len(not_in_upac) > 0:
                    print(
                        f'\nThe elements: {", ".join(not_in_upac)} include characters not from the UPAC code!'
                    )

                if len(not_coding) > 0:
                    print(
                        f'\nThe elements: {", ".join(length_compare)} are not coding sequences!'
                    )

    except:
        project = None

        print(
            "\nThe project could not be created due to trouble with input data issue. Check input data or contact us!"
        )

    return project


def create_vector_from_dict_rnai(metadata, input_dict, show_plot=True, source=_cwd):
    try:
        list_to_check = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "promoter_ncrna_name",
            "promoter_ncrna_sequence",
            "rnai_sequence",
            "rnai_gene_name",
            "loop_sequence",
            "sequences",
            "sequences_names",
            "linkers_names",
            "linkers_sequences",
            "promoter_name",
            "promoter_sequence",
            "regulator_name",
            "regulator_sequence",
            "polya_name",
            "polya_sequence",
            "fluorescence_name",
            "fluorescence_sequence",
            "fluorescence_linker_name",
            "fluorescence_linker_sequence",
            "selection_marker_name",
            "selection_marker_sequence",
            "restriction_list",
            "optimize",
        ]

        boolen_list = [x in input_dict.keys() for x in list_to_check]

        must_not_zero = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "promoter_ncrna_name",
            "promoter_ncrna_sequence",
            "rnai_gene_name",
            "loop_sequence",
            "selection_marker_name",
            "selection_marker_sequence",
        ]

        if False not in boolen_list:
            required = []
            for be in must_not_zero:
                if len(input_dict[str(be)]) == 0:
                    required.append(be)

            length_compare = []
            if len(input_dict["sequences"]) != len(input_dict["sequences_names"]):
                length_compare.append("sequences vs. sequences_names")

            if len(input_dict["linkers_sequences"]) != len(input_dict["linkers_names"]):
                length_compare.append("linkers_sequences vs. linkers_names")

            if len(input_dict["sequences"]) > 1 and len(
                input_dict["sequences"]
            ) - 1 != len(input_dict["linkers_sequences"]):
                length_compare.append("linkers_sequences vs. sequences")

            if (
                len(input_dict["linkers_names"]) > 0
                and len(input_dict["linkers_sequences"]) == 0
            ):
                required.append("linkers_sequences")

            if (
                len(input_dict["linkers_sequences"]) > 0
                and len(input_dict["linkers_names"]) == 0
            ):
                required.append("linkers_names")

            if (
                len(input_dict["fluorescence_name"]) > 0
                and len(input_dict["fluorescence_sequence"]) == 0
            ):
                required.append("fluorescence_sequence")

            if (
                len(input_dict["fluorescence_sequence"]) > 0
                and len(input_dict["fluorescence_name"]) == 0
            ):
                required.append("fluorescence_name")

            if (
                len(input_dict["fluorescence_linker_name"]) > 0
                and len(input_dict["fluorescence_linker_sequence"]) == 0
            ):
                required.append("fluorescence_linker_sequence")

            if (
                len(input_dict["fluorescence_linker_sequence"]) > 0
                and len(input_dict["fluorescence_linker_name"]) == 0
            ):
                required.append("fluorescence_linker_name")

            if (
                len(input_dict["regulator_sequence"]) > 0
                and len(input_dict["regulator_name"]) == 0
            ):
                required.append("regulator_name")

            if (
                len(input_dict["regulator_name"]) > 0
                and len(input_dict["regulator_sequence"]) == 0
            ):
                required.append("regulator_sequence")

            if input_dict["optimize"] not in [True, False]:
                required.append("optimize")

            seq_to_check = [
                "promoter_ncrna_sequence",
                "rnai_sequence",
                "loop_sequence",
                "sequences",
                "linkers_sequences",
                "promoter_sequence",
                "regulator_sequence",
                "polya_sequence",
                "fluorescence_sequence",
                "fluorescence_linker_sequence",
                "selection_marker_sequence",
            ]

            not_coding = []
            not_in_upac = []
            for s in seq_to_check:
                try:
                    input_dict[s]
                    if len(input_dict[s]) > 0:
                        if isinstance(input_dict[s], list) and s == "sequences":
                            tmp = []
                            for c in input_dict[s]:
                                tmp.append(clear_sequence(c))
                                cod = check_coding(clear_sequence(c))
                                if cod == False:
                                    not_coding.append(s)
                                upc = check_upac(clear_sequence(c))
                                if upc == False:
                                    not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif (
                            isinstance(input_dict[s], list) and s == "linkers_sequences"
                        ):
                            tmp = []
                            for c in input_dict[s]:
                                tmp.append(clear_sequence(c))
                                upc = check_upac(clear_sequence(c))
                                if upc == False:
                                    not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif not isinstance(input_dict[s], list) and s == "sequences":
                            tmp = clear_sequence(input_dict[s])
                            cod = check_coding(tmp)
                            if cod == False:
                                not_coding.append(s)
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif (
                            not isinstance(input_dict[s], list)
                            and s == "linkers_sequences"
                        ):
                            tmp = clear_sequence(input_dict[s])
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif (
                            not isinstance(input_dict[s], list)
                            and s == "selection_marker_sequence"
                        ):
                            tmp = clear_sequence(input_dict[s])
                            cod = check_coding(tmp)
                            if cod == False:
                                not_coding.append(s)
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        else:
                            tmp = clear_sequence(input_dict[s])
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                except:
                    not_in_upac.append(s)

        # create project
        if (
            False not in boolen_list
            and len(required) == 0
            and len(length_compare) == 0
            and len(not_in_upac) == 0
            and len(not_coding) == 0
        ):
            project = create_project(input_dict["project_name"])
            project["transcripts"] = {}
            project["rnai"] = {}
            project["transcripts"]["sequences"] = {}
            project["elements"] = {}
            project["elements"]["regulators"] = {}
            project["elements"]["linkers"] = {}
            project["elements"]["promoter"] = {}
            project["elements"]["fluorescence"] = {}
            project["elements"]["promoter_ncrna"] = {}
            project["rnai"]["sequence"] = {}
            project["rnai"]["name"] = {}
            project["elements"]["loop"] = {}
            project["elements"]["vector"] = {}

            # transcripts
            if len(input_dict["sequences"]) == len(input_dict["sequences_names"]):
                seq_vec = [
                    "SEQ" + str(l + 1) for l in range(len(input_dict["sequences"]))
                ]
                project["transcripts"]["sequences"]["SEQ"] = seq_vec
                project["transcripts"]["sequences"]["sequence"] = input_dict[
                    "sequences"
                ]
                project["transcripts"]["sequences"]["name"] = input_dict[
                    "sequences_names"
                ]
                project["elements"]["transcripts"] = seq_vec

                # linkers
                if len(input_dict["sequences"]) > 1 and len(
                    input_dict["sequences"]
                ) - 1 == len(input_dict["linkers_sequences"]):
                    seq_vec_linker = []
                    for n, i in enumerate(seq_vec):
                        seq_vec_linker = seq_vec_linker + [i] + ["Linker_" + str(n + 1)]
                    seq_vec_linker = seq_vec_linker[0:-1]

                    project["elements"]["transcripts"] = seq_vec_linker

                    if len(input_dict["linkers_sequences"]) == len(
                        input_dict["linkers_names"]
                    ):
                        for n, l in enumerate(input_dict["linkers_sequences"]):
                            project["elements"]["linkers"]["linker_" + str(n + 1)] = (
                                input_dict["linkers_sequences"][n]
                            )
                            project["elements"]["linkers"][
                                "linker_" + str(n + 1) + "_name"
                            ] = input_dict["linkers_names"][n]

                elif len(project["transcripts"]["sequences"]["sequence"]) <= 1:
                    pass

                else:
                    print("\nWrong number of linkers compareing to linkers names")

            else:
                print(
                    "\nNumber of provided sequences is different with number of sequences names"
                )

            # regulators

            project["elements"]["regulators"]["enhancer"] = input_dict[
                "regulator_sequence"
            ]
            project["elements"]["regulators"]["enhancer_name"] = input_dict[
                "regulator_name"
            ]
            project["elements"]["regulators"]["polya"] = input_dict["polya_sequence"]
            project["elements"]["regulators"]["polya_name"] = input_dict["polya_name"]

            # main promoter
            project["elements"]["promoter"]["name"] = input_dict["promoter_name"]
            project["elements"]["promoter"]["sequence"] = input_dict[
                "promoter_sequence"
            ]

            # nc promoter
            project["elements"]["promoter_ncrna"]["name"] = input_dict[
                "promoter_ncrna_name"
            ]
            project["elements"]["promoter_ncrna"]["sequence"] = input_dict[
                "promoter_ncrna_sequence"
            ]

            # fluorescence
            if len(project["transcripts"]["sequences"]["sequence"]) != 0:
                project["elements"]["fluorescence"]["linker"] = input_dict[
                    "fluorescence_linker_sequence"
                ]
                project["elements"]["fluorescence"]["linker_name"] = input_dict[
                    "fluorescence_linker_name"
                ]
            else:
                project["elements"]["fluorescence"]["linker"] = ""
                project["elements"]["fluorescence"]["linker_name"] = ""

            project["elements"]["fluorescence"]["name"] = input_dict[
                "fluorescence_name"
            ]
            project["elements"]["fluorescence"]["sequence"] = input_dict[
                "fluorescence_sequence"
            ]

            # restriction
            project["elements"]["vector"]["selection_marker"] = input_dict[
                "selection_marker_sequence"
            ]
            project["elements"]["vector"]["selection_marker_name"] = input_dict[
                "selection_marker_name"
            ]

            # rnai
            if len(input_dict["rnai_sequence"]) > 0:
                if "overhang_3_prime" not in input_dict.keys():
                    overhang_3_prime = ""
                else:
                    overhang_3_prime = str(input_dict["overhang_3_prime"])

                project["rnai"]["sequence"] = (
                    input_dict["rnai_sequence"]
                    + input_dict["loop_sequence"]
                    + complement(reverse(input_dict["rnai_sequence"]))
                    + overhang_3_prime
                )
                project["rnai"]["name"] = input_dict["rnai_gene_name"]
                project["rnai"]["species"] = input_dict["species"].lower()

                figure, dot = predict_structure(
                    sequence=dna_to_rna(project["rnai"]["sequence"], enrichment=False),
                    anty_sequence="",
                    height=None,
                    width=None,
                    dis_alpha=0.35,
                    seq_force=27,
                    pair_force=8,
                    show_plot=show_plot,
                )

                project["rnai"]["figure"] = figure
                project["rnai"]["dot"] = dot

                if (
                    len(project["elements"]["promoter"]["name"]) > 0
                    and len(project["elements"]["promoter"]["sequence"]) > 0
                    and len(project["elements"]["regulators"]["polya"]) > 0
                    and len(project["elements"]["regulators"]["polya_name"]) > 0
                    and len(project["transcripts"]["sequences"]["sequence"]) > 0
                    or len(project["elements"]["fluorescence"]["sequence"]) > 0
                ):
                    promoter_dec = "multi"
                    project = check_stop(project, metadata["codons"], "single")

                else:
                    promoter_dec = "single"

                run1 = input_dict["optimize"]

                if "transcript_GC" not in input_dict.keys():
                    transcript_GC = 59
                else:
                    transcript_GC = int(input_dict["transcript_GC"])

                if "poly_len" not in input_dict.keys():
                    transcript_rep = 7
                else:
                    transcript_rep = int(input_dict["poly_len"])

                if len(project["transcripts"]["sequences"]["sequence"]) > 0:
                    project = sequence_enrichment(
                        project,
                        metadata,
                        input_dict["species"].lower(),
                        run=run1,
                        GC_pct=transcript_GC,
                        correct_rep=transcript_rep,
                    )

                    if run1 == True:
                        project = sequence_enrichment_alternative(
                            project,
                            input_dict,
                            metadata,
                            input_dict["species"].lower(),
                            run=True,
                            GC_pct=transcript_GC,
                            correct_rep=transcript_rep,
                        )
                        project = select_sequence_variant(
                            project, sequence_variant=True
                        )

                    if len(input_dict["restriction_list"]) > 0:
                        run2 = True
                    else:
                        run2 = False

                    project = find_restriction_vector(project, metadata, run=run2)

                    if run1:
                        project = find_restriction_vector_alternative(
                            project, metadata, run=run2
                        )

                    if run2 == True:
                        list_of_list = []
                        user_defined_enzymes = [
                            e.upper() for e in input_dict["restriction_list"]
                        ]
                        for trans, i in enumerate(
                            project["transcripts"]["sequences"]["SEQ"]
                        ):
                            if len(user_defined_enzymes) > 0:
                                tmp = pd.DataFrame(
                                    project["transcripts"]["sequences"]["enzymes_df"][
                                        trans
                                    ]
                                )
                                tmp["name"] = [t.upper() for t in tmp["name"]]
                                en = list(
                                    tmp["index"][tmp["name"].isin(user_defined_enzymes)]
                                )
                                list_tmp = [item for sublist in en for item in sublist]
                                list_of_list.append(list_tmp)
                            else:
                                list_of_list.append([])

                        project = add_chosen_restriction(project, list_of_list)
                        project = repair_restriction_vector(
                            project, metadata, input_dict["species"]
                        )

                        if run1:
                            # alternative
                            user_defined_enzymes = [
                                e.upper() for e in input_dict["restriction_list"]
                            ]
                            for n in project["transcripts"]["alternative"].keys():
                                list_of_list_a = []
                                for s, _ in enumerate(
                                    project["transcripts"]["alternative"][n]["name"]
                                ):
                                    if len(user_defined_enzymes) > 0:
                                        tmp = pd.DataFrame(
                                            project["transcripts"]["alternative"][n][
                                                "enzymes_df"
                                            ][s]
                                        )
                                        tmp["name"] = [t.upper() for t in tmp["name"]]
                                        en = list(
                                            tmp["index"][
                                                tmp["name"].isin(user_defined_enzymes)
                                            ]
                                        )
                                        list_tmp = [
                                            item for sublist in en for item in sublist
                                        ]
                                        list_of_list_a.append(list_tmp)
                                    else:
                                        list_of_list_a.append([])

                                project["transcripts"]["alternative"][n][
                                    "enzymes"
                                ] = list_of_list_a

                            project = repair_restriction_vector_alternative(
                                project, metadata, input_dict["species"]
                            )

                    ###################
                    project["transcripts"]["sequences"]["sequence_figure"] = []
                    project["transcripts"]["sequences"]["sequence_dot"] = []

                    for tn in range(
                        0, len(project["transcripts"]["sequences"]["sequence"])
                    ):
                        figure, dot = predict_structure(
                            dna_to_rna(
                                project["transcripts"]["sequences"]["sequence"][tn],
                                enrichment=False,
                            ),
                            anty_sequence="",
                            height=None,
                            width=None,
                            dis_alpha=0.1,
                            seq_force=27,
                            pair_force=3,
                            show_plot=show_plot,
                        )

                        project["transcripts"]["sequences"]["sequence_figure"].append(
                            figure
                        )
                        project["transcripts"]["sequences"]["sequence_dot"].append(dot)

                    if run1:
                        project["transcripts"]["sequences"][
                            "optimized_sequence_figure"
                        ] = []
                        project["transcripts"]["sequences"][
                            "optimized_sequence_dot"
                        ] = []

                        for tn in range(
                            0,
                            len(project["transcripts"]["sequences"]["vector_sequence"]),
                        ):
                            figure, dot = predict_structure(
                                dna_to_rna(
                                    project["transcripts"]["sequences"][
                                        "vector_sequence"
                                    ][tn],
                                    enrichment=False,
                                ),
                                anty_sequence="",
                                height=None,
                                width=None,
                                dis_alpha=0.1,
                                seq_force=27,
                                pair_force=3,
                                show_plot=show_plot,
                            )

                            project["transcripts"]["sequences"][
                                "optimized_sequence_figure"
                            ].append(figure)
                            project["transcripts"]["sequences"][
                                "optimized_sequence_dot"
                            ].append(dot)

                project = vector_string(
                    project,
                    metadata["backbone"],
                    input_dict["vector_type"],
                    input_dict["vector_function"],
                    promoter_dec,
                )
                project = eval_vector(
                    project,
                    metadata["vectors"],
                    input_dict["vector_type"],
                    input_dict["vector_function"],
                )

                project, pl = vector_plot_project(
                    project, metadata, show_plot=show_plot
                )

            else:
                project["elements"]["loop"] = input_dict["loop_sequence"]
                refseq_sequences = get_sequences_gene(
                    input_dict["rnai_gene_name"], input_dict["species"]
                )
                if refseq_sequences != None:
                    fasta_string = generate_fasta_string(refseq_sequences)
                    alignments = MuscleMultipleSequenceAlignment(
                        fasta_string, output="results", gapopen=10, gapextend=0.5
                    )
                    consensuse_dictionary = ExtractConsensuse(
                        alignments, refseq_sequences=refseq_sequences
                    )
                    if len(consensuse_dictionary["sequence"]) == 0 and input_dict[
                        "species"
                    ] in ["both", "both2", "mutli"]:
                        print(
                            "\nThe consensus sequence for both species was unable to be created! We will try obtain consensuse for Homo sapiens!"
                        )
                        refseq_sequences = get_sequences_gene(
                            input_dict["rnai_gene_name"], "human"
                        )
                        fasta_string = generate_fasta_string(refseq_sequences)
                        alignments = MuscleMultipleSequenceAlignment(
                            fasta_string, output="results", gapopen=10, gapextend=0.5
                        )
                        consensuse_dictionary = ExtractConsensuse(
                            alignments, refseq_sequences=refseq_sequences
                        )
                        if len(consensuse_dictionary["sequence"]) == 0:
                            print(
                                "\nThe consensus sequence for Homo sapiens was also unable to be created!"
                            )
                            project = None

                    elif len(consensuse_dictionary["sequence"]) == 0 and input_dict[
                        "species"
                    ] not in ["both", "both2", "mutli"]:
                        project = None
                        print("\nThe consensus sequence was also unable to be created!")

                    if "rnai_length" not in input_dict.keys():
                        rnai_length = 23
                    else:
                        rnai_length = int(input_dict["rnai_length"])

                    if "overhang_3_prime" not in input_dict.keys():
                        overhang_3_prime = ""
                    else:
                        overhang_3_prime = str(input_dict["overhang_3_prime"])

                    if (
                        len(consensuse_dictionary["sequence"]) > 0
                        or refseq_sequences != None
                    ):
                        project = rnai_selection_to_vector(
                            project,
                            consensuse_dictionary,
                            metadata,
                            project["elements"]["loop"],
                            input_dict["species"].lower(),
                            end_3=overhang_3_prime,
                            show_plot=show_plot,
                            rnai_type="sh",
                            length=rnai_length,
                            n_max=500,
                            source=source,
                        )
                        if project["rnai"]["sequence"] != None:
                            project["rnai"]["name"] = (
                                input_dict["rnai_gene_name"]
                                + "_"
                                + project["rnai"]["name"]
                            )
                            project["rnai"]["species"] = input_dict["species"].lower()

                        elif project["rnai"]["sequence"] == None and input_dict[
                            "species"
                        ] in ["both", "both2", "mutli"]:
                            print(
                                "\nThe consensus sequence for both species was unable to be created! We will try obtain consensuse for Homo sapiens!"
                            )
                            refseq_sequences = get_sequences_gene(
                                input_dict["rnai_gene_name"], "human"
                            )
                            fasta_string = generate_fasta_string(refseq_sequences)
                            alignments = MuscleMultipleSequenceAlignment(
                                fasta_string,
                                output="results",
                                gapopen=10,
                                gapextend=0.5,
                            )
                            consensuse_dictionary = ExtractConsensuse(
                                alignments, refseq_sequences=refseq_sequences
                            )
                            if len(consensuse_dictionary["sequence"]) == 0:
                                print(
                                    "\nThe consensus sequence for Homo sapiens was also unable to be created!"
                                )
                                project = None
                            elif len(consensuse_dictionary["sequence"]) > 0:
                                project = rnai_selection_to_vector(
                                    project,
                                    consensuse_dictionary,
                                    metadata,
                                    project["elements"]["loop"],
                                    input_dict["species"].lower(),
                                    end_3=overhang_3_prime,
                                    show_plot=show_plot,
                                    rnai_type="sh",
                                    length=rnai_length,
                                    n_max=500,
                                    source=source,
                                )
                                if project["rnai"]["sequence"] != None:
                                    project["rnai"]["name"] = (
                                        input_dict["rnai_gene_name"]
                                        + "_"
                                        + project["rnai"]["name"]
                                    )
                                    project["rnai"]["species"] = "human"
                                else:
                                    project = None
                                    print(
                                        "\nThe project could not be created due to trouble with the RNAi selection!"
                                    )

                        else:
                            project = None
                            print(
                                "\nThe project could not be created due to trouble with the RNAi selection!"
                            )

                        if project != None:
                            if (
                                len(project["elements"]["promoter"]["name"]) > 0
                                and len(project["elements"]["promoter"]["sequence"]) > 0
                                and len(project["elements"]["regulators"]["polya"]) > 0
                                and len(project["elements"]["regulators"]["polya_name"])
                                > 0
                                and len(project["transcripts"]["sequences"]["sequence"])
                                > 0
                                or len(project["elements"]["fluorescence"]["sequence"])
                                > 0
                            ):
                                promoter_dec = "multi"
                                project = check_stop(
                                    project, metadata["codons"], "single"
                                )

                            else:
                                promoter_dec = "single"

                            run1 = input_dict["optimize"]

                            if "transcript_GC" not in input_dict.keys():
                                transcript_GC = 59
                            else:
                                transcript_GC = int(input_dict["transcript_GC"])

                            if "poly_len" not in input_dict.keys():
                                transcript_rep = 7
                            else:
                                transcript_rep = int(input_dict["poly_len"])

                            if len(project["transcripts"]["sequences"]["sequence"]) > 0:
                                project = sequence_enrichment(
                                    project,
                                    metadata,
                                    input_dict["species"].lower(),
                                    run=run1,
                                    GC_pct=transcript_GC,
                                    correct_rep=transcript_rep,
                                )

                                if run1 == True:
                                    project = select_sequence_variant(
                                        project, sequence_variant=True
                                    )
                                    project = sequence_enrichment_alternative(
                                        project,
                                        input_dict,
                                        metadata,
                                        input_dict["species"].lower(),
                                        run=True,
                                        GC_pct=transcript_GC,
                                        correct_rep=transcript_rep,
                                    )

                                if len(input_dict["restriction_list"]) > 0:
                                    run2 = True
                                else:
                                    run2 = False

                                project = find_restriction_vector(
                                    project, metadata, run=run2
                                )

                                if run1:
                                    project = find_restriction_vector_alternative(
                                        project, metadata, run=run2
                                    )

                                if run2 == True:
                                    list_of_list = []
                                    user_defined_enzymes = [
                                        e.upper()
                                        for e in input_dict["restriction_list"]
                                    ]
                                    for trans, i in enumerate(
                                        project["transcripts"]["sequences"]["SEQ"]
                                    ):
                                        if len(user_defined_enzymes) > 0:
                                            tmp = pd.DataFrame(
                                                project["transcripts"]["sequences"][
                                                    "enzymes_df"
                                                ][trans]
                                            )
                                            tmp["name"] = [
                                                t.upper() for t in tmp["name"]
                                            ]
                                            en = list(
                                                tmp["index"][
                                                    tmp["name"].isin(
                                                        user_defined_enzymes
                                                    )
                                                ]
                                            )
                                            list_tmp = [
                                                item
                                                for sublist in en
                                                for item in sublist
                                            ]
                                            list_of_list.append(list_tmp)
                                        else:
                                            list_of_list.append([])

                                    project = add_chosen_restriction(
                                        project, list_of_list
                                    )
                                    project = repair_restriction_vector(
                                        project, metadata, input_dict["species"]
                                    )

                                    if run1:
                                        # alternative
                                        user_defined_enzymes = [
                                            e.upper()
                                            for e in input_dict["restriction_list"]
                                        ]
                                        for n in project["transcripts"][
                                            "alternative"
                                        ].keys():
                                            list_of_list_a = []
                                            for s, _ in enumerate(
                                                project["transcripts"]["alternative"][
                                                    n
                                                ]["name"]
                                            ):
                                                if len(user_defined_enzymes) > 0:
                                                    tmp = pd.DataFrame(
                                                        project["transcripts"][
                                                            "alternative"
                                                        ][n]["enzymes_df"][s]
                                                    )
                                                    tmp["name"] = [
                                                        t.upper() for t in tmp["name"]
                                                    ]
                                                    en = list(
                                                        tmp["index"][
                                                            tmp["name"].isin(
                                                                user_defined_enzymes
                                                            )
                                                        ]
                                                    )
                                                    list_tmp = [
                                                        item
                                                        for sublist in en
                                                        for item in sublist
                                                    ]
                                                    list_of_list_a.append(list_tmp)
                                                else:
                                                    list_of_list_a.append([])

                                            project["transcripts"]["alternative"][n][
                                                "enzymes"
                                            ] = list_of_list_a

                                        project = repair_restriction_vector_alternative(
                                            project, metadata, input_dict["species"]
                                        )

                                project["transcripts"]["sequences"][
                                    "sequence_figure"
                                ] = []
                                project["transcripts"]["sequences"]["sequence_dot"] = []

                                for tn in range(
                                    0,
                                    len(
                                        project["transcripts"]["sequences"]["sequence"]
                                    ),
                                ):
                                    figure, dot = predict_structure(
                                        dna_to_rna(
                                            project["transcripts"]["sequences"][
                                                "sequence"
                                            ][tn],
                                            enrichment=False,
                                        ),
                                        anty_sequence="",
                                        height=None,
                                        width=None,
                                        dis_alpha=0.1,
                                        seq_force=27,
                                        pair_force=3,
                                        show_plot=show_plot,
                                    )

                                    project["transcripts"]["sequences"][
                                        "sequence_figure"
                                    ].append(figure)
                                    project["transcripts"]["sequences"][
                                        "sequence_dot"
                                    ].append(dot)

                                if run1:
                                    project["transcripts"]["sequences"][
                                        "optimized_sequence_figure"
                                    ] = []
                                    project["transcripts"]["sequences"][
                                        "optimized_sequence_dot"
                                    ] = []

                                    for tn in range(
                                        0,
                                        len(
                                            project["transcripts"]["sequences"][
                                                "vector_sequence"
                                            ]
                                        ),
                                    ):
                                        figure, dot = predict_structure(
                                            dna_to_rna(
                                                project["transcripts"]["sequences"][
                                                    "vector_sequence"
                                                ][tn],
                                                enrichment=False,
                                            ),
                                            anty_sequence="",
                                            height=None,
                                            width=None,
                                            dis_alpha=0.1,
                                            seq_force=27,
                                            pair_force=3,
                                            show_plot=show_plot,
                                        )

                                        project["transcripts"]["sequences"][
                                            "optimized_sequence_figure"
                                        ].append(figure)
                                        project["transcripts"]["sequences"][
                                            "optimized_sequence_dot"
                                        ].append(dot)

                            project = vector_string(
                                project,
                                metadata["backbone"],
                                input_dict["vector_type"],
                                input_dict["vector_function"],
                                promoter_dec,
                            )
                            project = eval_vector(
                                project,
                                metadata["vectors"],
                                input_dict["vector_type"],
                                input_dict["vector_function"],
                            )

                            project, pl = vector_plot_project(
                                project, metadata, show_plot=show_plot
                            )

                    else:
                        project = None

                        print(
                            "\nThe project could not be created due to trouble with the consensus sequence obtained. You can try to prepare custom RNAi and paste it into the project next time!"
                        )

                else:
                    project = None

                    print(
                        "\nThe project could not be created due to trouble with the consensus sequence obtained. You can try to prepare custom RNAi and paste it into the project next time!"
                    )

        else:
            project = None
            print(
                "\nThe project could not be created due to trouble with the lack of dictionary elements!"
            )
            if len(required) > 0:
                print(
                    f'\nThe elements: {", ".join(required)} are required with non-zero length!'
                )

            if len(length_compare) > 0:
                print(
                    f'\nThe elements: {", ".join(length_compare)} are in wrong proportion. Remember that each sequence requires a sequence name, each linker requires linker_name and the number of linkers should be the number of transcripts - 1! If you do not need linkers provide an empty string ([""]) for linker_sequence and linker_name for each pair of transcripts.'
                )

            if len(not_in_upac) > 0:
                print(
                    f'\nThe elements: {", ".join(not_in_upac)} include characters not from the UPAC code!'
                )

            if len(not_coding) > 0:
                print(
                    f'\nThe elements: {", ".join(length_compare)} are not coding sequences!'
                )

    except:
        project = None

        print(
            "\nThe project could not be created due to trouble with input data issue. Check input data or contact us!"
        )

    return project


def create_vector_from_dict_expression(metadata, input_dict, show_plot=True):
    try:
        list_to_check = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "sequences",
            "sequences_names",
            "promoter_name",
            "promoter_sequence",
            "regulator_name",
            "regulator_sequence",
            "polya_name",
            "polya_sequence",
            "linkers_names",
            "linkers_sequences",
            "fluorescence_name",
            "fluorescence_sequence",
            "fluorescence_linker_name",
            "fluorescence_linker_sequence",
            "fluorescence_promoter_name",
            "fluorescence_promoter_sequence",
            "fluorescence_polya_name",
            "fluorescence_polya_sequence",
            "selection_marker_name",
            "selection_marker_sequence",
            "restriction_list",
            "optimize",
        ]

        boolen_list = [x in input_dict.keys() for x in list_to_check]

        must_not_zero = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "promoter_name",
            "promoter_sequence",
            "polya_name",
            "polya_sequence",
            "selection_marker_name",
            "selection_marker_sequence",
        ]

        if False not in boolen_list:
            required = []
            for be in must_not_zero:
                if len(input_dict[str(be)]) == 0:
                    required.append(be)

            length_compare = []
            if len(input_dict["sequences"]) != len(input_dict["sequences_names"]):
                length_compare.append("sequences vs. sequences_names")

            if len(input_dict["linkers_sequences"]) != len(input_dict["linkers_names"]):
                length_compare.append("linkers_sequences vs. linkers_names")

            if len(input_dict["sequences"]) > 1 and len(
                input_dict["sequences"]
            ) - 1 != len(input_dict["linkers_sequences"]):
                length_compare.append("linkers_sequences vs. sequences")

            if (
                len(input_dict["linkers_names"]) > 0
                and len(input_dict["linkers_sequences"]) == 0
            ):
                required.append("linkers_sequences")

            if (
                len(input_dict["linkers_sequences"]) > 0
                and len(input_dict["linkers_names"]) == 0
            ):
                required.append("linkers_names")

            if (
                len(input_dict["fluorescence_name"]) > 0
                and len(input_dict["fluorescence_sequence"]) == 0
            ):
                required.append("fluorescence_sequence")

            if (
                len(input_dict["fluorescence_sequence"]) > 0
                and len(input_dict["fluorescence_name"]) == 0
            ):
                required.append("fluorescence_name")

            if (
                len(input_dict["fluorescence_linker_name"]) > 0
                and len(input_dict["fluorescence_linker_sequence"]) == 0
            ):
                required.append("fluorescence_linker_sequence")

            if (
                len(input_dict["fluorescence_linker_sequence"]) > 0
                and len(input_dict["fluorescence_linker_name"]) == 0
            ):
                required.append("fluorescence_linker_name")

            if (
                len(input_dict["fluorescence_promoter_name"]) > 0
                and len(input_dict["fluorescence_promoter_sequence"]) == 0
            ):
                required.append("fluorescence_promoter_sequence")

            if (
                len(input_dict["fluorescence_promoter_sequence"]) > 0
                and len(input_dict["fluorescence_promoter_name"]) == 0
            ):
                required.append("fluorescence_promoter_name")

            if (
                len(input_dict["fluorescence_polya_name"]) > 0
                and len(input_dict["fluorescence_polya_sequence"]) == 0
            ):
                required.append("fluorescence_polya_sequence")

            if (
                len(input_dict["fluorescence_polya_sequence"]) > 0
                and len(input_dict["fluorescence_polya_name"]) == 0
            ):
                required.append("fluorescence_polya_name")

            if (
                len(input_dict["regulator_sequence"]) > 0
                and len(input_dict["regulator_name"]) == 0
            ):
                required.append("regulator_name")

            if (
                len(input_dict["regulator_name"]) > 0
                and len(input_dict["regulator_sequence"]) == 0
            ):
                required.append("regulator_sequence")

            if input_dict["optimize"] not in [True, False]:
                required.append("optimize")

            seq_to_check = [
                "sequences",
                "promoter_sequence",
                "regulator_sequence",
                "polya_sequence",
                "linkers_sequences",
                "fluorescence_sequence",
                "fluorescence_linker_sequence",
                "fluorescence_promoter_sequence",
                "fluorescence_polya_sequence",
                "selection_marker_sequence",
            ]

            not_coding = []
            not_in_upac = []
            for s in seq_to_check:
                try:
                    input_dict[s]
                    if len(input_dict[s]) > 0:
                        if isinstance(input_dict[s], list) and s == "sequences":
                            tmp = []
                            for c in input_dict[s]:
                                tmp.append(clear_sequence(c))
                                cod = check_coding(clear_sequence(c))
                                if cod == False:
                                    not_coding.append(s)
                                upc = check_upac(clear_sequence(c))
                                if upc == False:
                                    not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif (
                            isinstance(input_dict[s], list) and s == "linkers_sequences"
                        ):
                            tmp = []
                            for c in input_dict[s]:
                                tmp.append(clear_sequence(c))
                                upc = check_upac(clear_sequence(c))
                                if upc == False:
                                    not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif not isinstance(input_dict[s], list) and s == "sequences":
                            tmp = clear_sequence(input_dict[s])
                            cod = check_coding(tmp)
                            if cod == False:
                                not_coding.append(s)
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif (
                            not isinstance(input_dict[s], list)
                            and s == "linkers_sequences"
                        ):
                            tmp = clear_sequence(input_dict[s])
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        elif (
                            not isinstance(input_dict[s], list)
                            and s == "selection_marker_sequence"
                        ):
                            tmp = clear_sequence(input_dict[s])
                            cod = check_coding(tmp)
                            if cod == False:
                                not_coding.append(s)
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        else:
                            tmp = clear_sequence(input_dict[s])
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                except:
                    not_in_upac.append(s)

        # create project
        if (
            False not in boolen_list
            and len(required) == 0
            and len(length_compare) == 0
            and len(not_in_upac) == 0
            and len(not_coding) == 0
        ):
            project = create_project(input_dict["project_name"])
            project["transcripts"] = {}
            project["transcripts"]["sequences"] = {}
            project["elements"] = {}
            project["elements"]["regulators"] = {}
            project["elements"]["linkers"] = {}
            project["elements"]["promoter"] = {}
            project["elements"]["fluorescence"] = {}
            project["elements"]["vector"] = {}

            # transcripts
            if len(input_dict["sequences"]) == len(input_dict["sequences_names"]):
                seq_vec = [
                    "SEQ" + str(l + 1) for l in range(len(input_dict["sequences"]))
                ]
                project["transcripts"]["sequences"]["SEQ"] = seq_vec
                project["transcripts"]["sequences"]["sequence"] = input_dict[
                    "sequences"
                ]
                project["transcripts"]["sequences"]["name"] = input_dict[
                    "sequences_names"
                ]
                project["elements"]["transcripts"] = seq_vec

                # linkers
                if len(input_dict["sequences"]) > 1 and len(
                    input_dict["sequences"]
                ) - 1 == len(input_dict["linkers_sequences"]):
                    seq_vec_linker = []
                    for n, i in enumerate(seq_vec):
                        seq_vec_linker = seq_vec_linker + [i] + ["Linker_" + str(n + 1)]
                    seq_vec_linker = seq_vec_linker[0:-1]

                    project["elements"]["transcripts"] = seq_vec_linker

                    if len(input_dict["linkers_sequences"]) == len(
                        input_dict["linkers_names"]
                    ):
                        for n, l in enumerate(input_dict["linkers_sequences"]):
                            project["elements"]["linkers"]["linker_" + str(n + 1)] = (
                                input_dict["linkers_sequences"][n]
                            )
                            project["elements"]["linkers"][
                                "linker_" + str(n + 1) + "_name"
                            ] = input_dict["linkers_names"][n]

            # regulators

            project["elements"]["regulators"]["enhancer"] = input_dict[
                "regulator_sequence"
            ]
            project["elements"]["regulators"]["enhancer_name"] = input_dict[
                "regulator_name"
            ]
            project["elements"]["regulators"]["polya"] = input_dict["polya_sequence"]
            project["elements"]["regulators"]["polya_name"] = input_dict["polya_name"]

            # main promoter
            project["elements"]["promoter"]["name"] = input_dict["promoter_name"]
            project["elements"]["promoter"]["sequence"] = input_dict[
                "promoter_sequence"
            ]

            # fluorescence
            project["elements"]["fluorescence"]["name"] = input_dict[
                "fluorescence_name"
            ]
            project["elements"]["fluorescence"]["sequence"] = input_dict[
                "fluorescence_sequence"
            ]

            # restriction
            project["elements"]["vector"]["selection_marker"] = input_dict[
                "selection_marker_sequence"
            ]
            project["elements"]["vector"]["selection_marker_name"] = input_dict[
                "selection_marker_name"
            ]

            if len(project["transcripts"]["sequences"]["sequence"]) != 0:
                project["elements"]["fluorescence"]["linker"] = input_dict[
                    "fluorescence_linker_sequence"
                ]
                project["elements"]["fluorescence"]["linker_name"] = input_dict[
                    "fluorescence_linker_name"
                ]
                project["elements"]["fluorescence"]["polya_seq"] = input_dict[
                    "fluorescence_polya_sequence"
                ]
                project["elements"]["fluorescence"]["polya_seq_name"] = input_dict[
                    "fluorescence_polya_name"
                ]
                project["elements"]["fluorescence"]["promoter_name"] = input_dict[
                    "fluorescence_promoter_name"
                ]
                project["elements"]["fluorescence"]["promoter_seq"] = input_dict[
                    "fluorescence_promoter_sequence"
                ]

            else:
                project["elements"]["fluorescence"]["linker"] = ""
                project["elements"]["fluorescence"]["linker_name"] = ""
                project["elements"]["fluorescence"]["polya_seq"] = ""
                project["elements"]["fluorescence"]["polya_seq_name"] = ""
                project["elements"]["fluorescence"]["promoter_name"] = ""
                project["elements"]["fluorescence"]["promoter_seq"] = ""

            if (
                len(project["elements"]["fluorescence"]["sequence"]) > 0
                and len(project["elements"]["fluorescence"]["polya_seq"]) > 0
                and len(project["elements"]["fluorescence"]["promoter_seq"]) > 0
            ):
                promoter_dec = "multi"
            else:
                promoter_dec = "single"

            if len(project["transcripts"]["sequences"]["sequence"]) > 0:
                project = check_stop(project, metadata["codons"], promoter_dec)

                run1 = input_dict["optimize"]

                if "transcript_GC" not in input_dict.keys():
                    transcript_GC = 59
                else:
                    transcript_GC = int(input_dict["transcript_GC"])

                if "poly_len" not in input_dict.keys():
                    transcript_rep = 7
                else:
                    transcript_rep = int(input_dict["poly_len"])

                project = sequence_enrichment(
                    project,
                    metadata,
                    input_dict["species"].lower(),
                    run=run1,
                    GC_pct=transcript_GC,
                    correct_rep=transcript_rep,
                )

                if run1 == True:
                    project = sequence_enrichment_alternative(
                        project,
                        input_dict,
                        metadata,
                        input_dict["species"].lower(),
                        run=True,
                        GC_pct=transcript_GC,
                        correct_rep=transcript_rep,
                    )
                    project = select_sequence_variant(project, sequence_variant=True)

                if len(input_dict["restriction_list"]) > 0:
                    run2 = True
                else:
                    run2 = False

                project = find_restriction_vector(project, metadata, run=run2)

                if run1:
                    project = find_restriction_vector_alternative(
                        project, metadata, run=run2
                    )

                if run2 == True:
                    list_of_list = []
                    user_defined_enzymes = [
                        e.upper() for e in input_dict["restriction_list"]
                    ]
                    for trans, i in enumerate(
                        project["transcripts"]["sequences"]["SEQ"]
                    ):
                        if len(user_defined_enzymes) > 0:
                            tmp = pd.DataFrame(
                                project["transcripts"]["sequences"]["enzymes_df"][trans]
                            )
                            tmp["name"] = [t.upper() for t in tmp["name"]]
                            en = list(
                                tmp["index"][tmp["name"].isin(user_defined_enzymes)]
                            )
                            list_tmp = [item for sublist in en for item in sublist]
                            list_of_list.append(list_tmp)
                        else:
                            list_of_list.append([])

                    project = add_chosen_restriction(project, list_of_list)
                    project = repair_restriction_vector(
                        project, metadata, input_dict["species"]
                    )

                    if run1:
                        # alternative
                        user_defined_enzymes = [
                            e.upper() for e in input_dict["restriction_list"]
                        ]
                        for n in project["transcripts"]["alternative"].keys():
                            list_of_list_a = []
                            for s, _ in enumerate(
                                project["transcripts"]["alternative"][n]["name"]
                            ):
                                if len(user_defined_enzymes) > 0:
                                    tmp = pd.DataFrame(
                                        project["transcripts"]["alternative"][n][
                                            "enzymes_df"
                                        ][s]
                                    )
                                    tmp["name"] = [t.upper() for t in tmp["name"]]
                                    en = list(
                                        tmp["index"][
                                            tmp["name"].isin(user_defined_enzymes)
                                        ]
                                    )
                                    list_tmp = [
                                        item for sublist in en for item in sublist
                                    ]
                                    list_of_list_a.append(list_tmp)
                                else:
                                    list_of_list_a.append([])

                            project["transcripts"]["alternative"][n][
                                "enzymes"
                            ] = list_of_list_a

                        project = repair_restriction_vector_alternative(
                            project, metadata, input_dict["species"]
                        )

            project["transcripts"]["sequences"]["sequence_figure"] = []
            project["transcripts"]["sequences"]["sequence_dot"] = []

            for tn in range(0, len(project["transcripts"]["sequences"]["sequence"])):
                figure, dot = predict_structure(
                    dna_to_rna(
                        project["transcripts"]["sequences"]["sequence"][tn],
                        enrichment=False,
                    ),
                    anty_sequence="",
                    height=None,
                    width=None,
                    dis_alpha=0.1,
                    seq_force=27,
                    pair_force=3,
                    show_plot=show_plot,
                )

                project["transcripts"]["sequences"]["sequence_figure"].append(figure)
                project["transcripts"]["sequences"]["sequence_dot"].append(dot)

            if run1:
                project["transcripts"]["sequences"]["optimized_sequence_figure"] = []
                project["transcripts"]["sequences"]["optimized_sequence_dot"] = []

                for tn in range(
                    0, len(project["transcripts"]["sequences"]["vector_sequence"])
                ):
                    figure, dot = predict_structure(
                        dna_to_rna(
                            project["transcripts"]["sequences"]["vector_sequence"][tn],
                            enrichment=False,
                        ),
                        anty_sequence="",
                        height=None,
                        width=None,
                        dis_alpha=0.1,
                        seq_force=27,
                        pair_force=3,
                        show_plot=show_plot,
                    )

                    project["transcripts"]["sequences"][
                        "optimized_sequence_figure"
                    ].append(figure)
                    project["transcripts"]["sequences"][
                        "optimized_sequence_dot"
                    ].append(dot)

            project = vector_string(
                project,
                metadata["backbone"],
                input_dict["vector_type"],
                input_dict["vector_function"],
                promoter_dec,
            )
            project = eval_vector(
                project,
                metadata["vectors"],
                input_dict["vector_type"],
                input_dict["vector_function"],
            )

            project, pl = vector_plot_project(project, metadata, show_plot=show_plot)

        else:
            project = None
            print(
                "\nThe project could not be created due to trouble with the lack of dictionary elements!"
            )
            if len(required) > 0:
                print(
                    f'\nThe elements: {", ".join(required)} are required with non-zero length!'
                )

            if len(length_compare) > 0:
                print(
                    f'\nThe elements: {", ".join(length_compare)} are in wrong proportion. Remember that each sequence requires a sequence name, each linker requires linker_name and the number of linkers should be the number of transcripts - 1! If you do not need linkers provide an empty string ([""]) for linker_sequence and linker_name for each pair of transcripts.'
                )

            if len(not_in_upac) > 0:
                print(
                    f'\nThe elements: {", ".join(not_in_upac)} include characters not from the UPAC code!'
                )

            if len(not_coding) > 0:
                print(
                    f'\nThe elements: {", ".join(length_compare)} are not coding sequences!'
                )

    except:
        project = None
        print(
            "\nThe project could not be created due to trouble with input data issue. Check input data or contact us!"
        )

    return project


def vector_create_on_dict(metadata, input_dict: dict, show_plot: bool = True):
    """
    This function change provided by user metadata into three types of vector plasmids:
        -expression (artificial gene expression)
        -RNAi (silencing)
        -invitro transcription (used in mRNA vaccine, mRNA, RNAi, and peptides production)

    in three types of delivery systems:
        -AAVs
        -lentiviruses
        -regular plasmid (for liposomes or other delivery systems)


    Args:
       metadata (dict) - matadata loaded in the load_metadata() function
       input_dict (dict) - dictionary of metadata provided by the user


    Examples:
        -expression vector
        -RNAi vector
        -in-vitro transcription:
            -RNAi
            -mRNA

        Avaiable on https://github.com/jkubis96/JBioSeqTools
        If you have any problem, don't hesitate to contact us!

    Args
        show_plot (bool) - if True the plot will be displayed, if False only the graph will be returned to the project. Default: True


    Returns:
        dict: Dictionary including all vector data (graphs, sequences, fasta) created based on user definition

    """

    try:
        expression = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "sequences",
            "sequences_names",
            "promoter_name",
            "promoter_sequence",
            "regulator_name",
            "regulator_sequence",
            "polya_name",
            "polya_sequence",
            "linkers_names",
            "linkers_sequences",
            "fluorescence_name",
            "fluorescence_sequence",
            "fluorescence_linker_name",
            "fluorescence_linker_sequence",
            "fluorescence_promoter_name",
            "fluorescence_promoter_sequence",
            "fluorescence_polya_name",
            "fluorescence_polya_sequence",
            "selection_marker_name",
            "selection_marker_sequence",
            "restriction_list",
            "optimize",
        ]

        rnai = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "promoter_ncrna_name",
            "promoter_ncrna_sequence",
            "rnai_sequence",
            "rnai_gene_name",
            "loop_sequence",
            "sequences",
            "sequences_names",
            "linkers_names",
            "linkers_sequences",
            "promoter_name",
            "promoter_sequence",
            "regulator_name",
            "regulator_sequence",
            "polya_name",
            "polya_sequence",
            "fluorescence_name",
            "fluorescence_sequence",
            "fluorescence_linker_name",
            "fluorescence_linker_sequence",
            "selection_marker_name",
            "selection_marker_sequence",
            "restriction_list",
            "optimize",
        ]

        transcription_rnai = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "rnai_sequence",
            "rnai_gene_name",
            "loop_sequence",
            "selection_marker_name",
            "selection_marker_sequence",
        ]

        transcription_mrna = [
            "project_name",
            "vector_type",
            "vector_function",
            "species",
            "sequences",
            "sequences_names",
            "linkers_names",
            "linkers_sequences",
            "utr5_name",
            "utr5_sequence",
            "utr3_name",
            "utr3_sequence",
            "polya_tail_x",
            "selection_marker_name",
            "selection_marker_sequence",
            "restriction_list",
            "optimize",
        ]

        if set(rnai).issubset(input_dict.keys()):
            project = create_vector_from_dict_rnai(
                metadata, input_dict, show_plot=show_plot
            )

        elif set(expression).issubset(input_dict.keys()):
            project = create_vector_from_dict_expression(
                metadata, input_dict, show_plot=show_plot
            )

        elif set(transcription_rnai).issubset(input_dict.keys()) or set(
            transcription_mrna
        ).issubset(input_dict.keys()):
            project = create_vector_from_dict_transcription(
                metadata, input_dict, show_plot=show_plot
            )

        else:
            print(
                "\nThe input data does not pass to any function. \n Check the input data or contact us!"
            )
            project = None

    except:
        project = None
        print(
            "\nThe project could not be created due to trouble with input data issue. Check input data or contact us!"
        )

    return project


def plot_vector(
    df_fasta: pd.DataFrame, title=None, title_size=20, show_plot: bool = True
):
    """
    This function displays a plot of the vector plasmid provided in the DataFrame of the FASTA file derived from load_fasta(path) -> decode_fasta_to_dataframe(fasta) -> extract_fasta_info(df_fasta) pipeline.


    Args:
        df_fasta (DataFrame) - dataframe obtained from load_fasta(path) -> decode fasta_to_dataframe(fasta) -> extract_fasta_info(df_fasta) pipeline which prepare decoded FASTA file of vector plasmid.
            *dedicated FASTA structure:

        >name1
        CTGCGCGCTCGCTCGCTCACTGAGGCCGCCCGGGCAAAGCCCGGGCGTCGGGCGACC

        >name2
        TCTAGACAACTTTGTATAGAAAAGTTG

        >name3
        GGGCTGGAAGCTACCTTTGACATCATTTCCTCTGCGAATGCATGTATAATTTCTAC

        Header explanation:
            name1,2,3,... - the name of the sequence element


       title (str | None) - a title that will display in the middle of the plasmid vector. Default: None
       title_size (int | float) - font size of the title. Default: 20
       show_plot (bool) - if True the plot will be displayed, if False only the graph will be returned to the variable. Default: True


    Returns:
        Graph: The vector plot based on the provided DataFrame FASTA data

    """

    try:
        df_fasta = df_fasta.sort_index(ascending=False)

        explode = []
        for i in df_fasta.index:
            if df_fasta["visible"][i] == False:
                explode.append(-0.2)
            else:
                explode.append(0)

        labels = []
        for i in df_fasta.index:
            if df_fasta["visible"][i] == False:
                labels.append("")
            else:
                labels.append(df_fasta["element"][i])

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(aspect="equal"))

        colors = sns.color_palette("gist_ncar", len(df_fasta["length"]))

        wedges, texts = ax.pie(
            df_fasta["length"], explode=explode, startangle=90, colors=colors
        )

        kw = dict(arrowprops=dict(arrowstyle="-"), zorder=0, va="center")

        n = 0.25
        k = 1

        x_pie = []
        y_pie = []
        x_text = []
        y_text = []
        orient = []
        labels_set = []
        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            if len(labels[i]) > 0:
                k += 1
                if horizontalalignment == "right":
                    if k < len(labels) / 2:
                        n += 0.15
                    else:
                        n -= 0.15
                else:
                    if k < len(labels) / 2:
                        n -= 0.15
                    else:
                        n += 0.15

                x_pie.append(x)
                y_pie.append(y)
                x_text.append(x + x * 0.75)
                y_text.append(y + y * n)
                orient.append(horizontalalignment)
                labels_set.append(labels[i])

        df = pd.DataFrame(
            {
                "x_pie": x_pie,
                "y_pie": y_pie,
                "x_text": x_text,
                "y_text": y_text,
                "orient": orient,
                "labels": labels_set,
            }
        )

        df_left = df[df["orient"] == "left"]
        df_right = df[df["orient"] == "right"]

        df["x_text"][df["orient"] == "left"] = max(df_left["x_text"])
        df["x_text"][df["orient"] == "right"] = min(df_right["x_text"])

        df_list = [df_left, df_right]
        for d in df_list:
            if len(d.index) > 1:
                check = True
                while check:
                    for i in d.index:
                        if (
                            i > min(d.index)
                            and df["y_text"][i - 1] > df["y_text"][i]
                            and df["orient"][i] == "left"
                        ):
                            tmp = df["y_text"][i - 1]
                            df["y_text"][i - 1] = df["y_text"][i]
                            df["y_text"][i] = tmp
                            break

                        elif (
                            i > min(d.index)
                            and df["y_text"][i - 1] < df["y_text"][i]
                            and df["orient"][i] == "right"
                        ):
                            tmp = df["y_text"][i]
                            df["y_text"][i] = df["y_text"][i - 1]
                            df["y_text"][i - 1] = tmp
                            break

                        elif (
                            i > min(d.index)
                            and (df["y_text"][i] - df["y_text"][i - 1]) < 0.25
                            and df["orient"][i] == "left"
                        ):
                            df["y_text"][i] = df["y_text"][i] + 0.25

                            break
                        elif (
                            i > min(d.index)
                            and (df["y_text"][i - 1] - df["y_text"][i]) < 0.25
                            and df["orient"][i] == "right"
                        ):
                            df["y_text"][i] = df["y_text"][i] - 0.25

                            break

                        elif i == max(d.index):
                            check = False
                            break

        arrow_props = dict(
            facecolor="gray",
            edgecolor="gray",
            arrowstyle="->",
            connectionstyle="arc3,rad=0.05",
        )

        for i in df.index:
            ax.annotate(
                df["labels"][i],
                xy=(df["x_pie"][i], df["y_pie"][i]),
                xytext=(df["x_text"][i], df["y_text"][i]),
                horizontalalignment=df["orient"][i],
                fontsize=20,
                weight="bold",
                arrowprops=arrow_props,
            )

        circle1 = plt.Circle((0, 0), 0.85, color="black")
        circle2 = plt.Circle((0, 0), 0.8, color="white")

        if title == None:
            title = ""

        ax.text(
            0.5,
            0.5,
            str(title),
            transform=ax.transAxes,
            va="center",
            ha="center",
            backgroundcolor="white",
            weight="bold",
            fontsize=title_size,
        )

        p = plt.gcf()
        p.gca().add_artist(circle1)
        p.gca().add_artist(circle2)

        if show_plot == True:
            plt.show()
        elif show_plot == False:
            plt.close(fig)

        return fig

    except:
        print("\nSomething went wrong - plot_vector. Check the input or contact us!")
        return None


def create_rnai_from_dict(metadata, input_dict, show_plot=True, source=_cwd):
    try:
        list_to_check_rnai = [
            "project_name",
            "species",
            "rnai_type",
            "rnai_length",
            "overhang_3_prime",
            "rnai_sequence",
            "rnai_gene_name",
            "loop_sequence",
        ]

        if set(list_to_check_rnai).issubset(input_dict.keys()):
            must_not_zero = [
                "project_name",
                "species",
                "rnai_gene_name",
                "rnai_type",
                "rnai_length",
            ]

            required = []
            for be in must_not_zero:
                if len(str(input_dict[str(be)])) == 0:
                    required.append(be)

            seq_to_check = ["rnai_sequence", "loop_sequence"]

            not_in_upac = []
            for s in seq_to_check:
                try:
                    input_dict[s]
                    if len(input_dict[s]) > 0:
                        tmp = clear_sequence(input_dict[s])

                        upc = check_upac(tmp)
                        if upc == False:
                            not_in_upac.append(s)

                        input_dict[s] = tmp

                except:
                    not_in_upac.append(s)

            if len(required) == 0 and len(not_in_upac) == 0:
                project = {
                    "project": str(input_dict["project_name"]),
                    "rnai": {},
                    "elements": {},
                }

                # rnai
                if len(input_dict["rnai_sequence"]) > 0:
                    if (
                        input_dict["rnai_type"].lower() == "sh"
                        and len(input_dict["loop_sequence"]) > 0
                    ):
                        project["rnai"]["full_sequence"] = (
                            input_dict["rnai_sequence"]
                            + input_dict["loop_sequence"]
                            + complement(reverse(input_dict["rnai_sequence"]))
                            + input_dict["overhang_3_prime"]
                        )
                        project["rnai"]["sequence"] = input_dict["rnai_sequence"]
                        project["rnai"]["sequence_sense"] = complement(
                            reverse(input_dict["rnai_sequence"])
                        )
                        project["rnai"]["name"] = input_dict["rnai_gene_name"]
                        project["rnai"]["species"] = input_dict["species"].lower()

                        figure, dot = predict_structure(
                            sequence=dna_to_rna(
                                project["rnai"]["full_sequence"], enrichment=False
                            ),
                            anty_sequence="",
                            height=None,
                            width=None,
                            dis_alpha=0.35,
                            seq_force=27,
                            pair_force=8,
                            show_plot=show_plot,
                        )

                    else:
                        sequence = (
                            input_dict["rnai_sequence"].upper()
                            + input_dict["overhang_3_prime"].upper()
                        )
                        anty_sequence = (
                            complement(reverse(input_dict["rnai_sequence"]).upper())
                            + input_dict["overhang_3_prime"].upper()
                        )

                        project["rnai"]["sequence"] = sequence
                        project["rnai"]["sequence_sense"] = anty_sequence
                        project["rnai"]["name"] = input_dict["rnai_gene_name"]
                        project["rnai"]["species"] = input_dict["species"].lower()

                        figure, dot = predict_structure(
                            sequence,
                            anty_sequence=anty_sequence,
                            height=None,
                            width=None,
                            dis_alpha=0.25,
                            seq_force=27,
                            pair_force=8,
                            show_plot=True,
                        )

                    project["rnai"]["figure"] = figure
                    project["rnai"]["dot"] = dot

                else:
                    if (
                        input_dict["rnai_type"].lower() == "sh"
                        and len(input_dict["loop_sequence"]) > 0
                    ):
                        project["elements"]["loop"] = input_dict["loop_sequence"]

                        refseq_sequences = get_sequences_gene(
                            input_dict["rnai_gene_name"], input_dict["species"]
                        )
                        if refseq_sequences != None:
                            fasta_string = generate_fasta_string(refseq_sequences)
                            alignments = MuscleMultipleSequenceAlignment(
                                fasta_string,
                                output="results",
                                gapopen=10,
                                gapextend=0.5,
                            )
                            consensuse_dictionary = ExtractConsensuse(
                                alignments, refseq_sequences=refseq_sequences
                            )

                            if len(
                                consensuse_dictionary["sequence"]
                            ) == 0 and input_dict["species"] in [
                                "both",
                                "both2",
                                "mutli",
                            ]:
                                print(
                                    "\nThe consensus sequence for both species was unable to be created! We will try obtain consensuse for Homo sapiens!"
                                )
                                refseq_sequences = get_sequences_gene(
                                    input_dict["rnai_gene_name"], "human"
                                )
                                fasta_string = generate_fasta_string(refseq_sequences)
                                alignments = MuscleMultipleSequenceAlignment(
                                    fasta_string,
                                    output="results",
                                    gapopen=10,
                                    gapextend=0.5,
                                )
                                consensuse_dictionary = ExtractConsensuse(
                                    alignments, refseq_sequences=refseq_sequences
                                )
                                if len(consensuse_dictionary["sequence"]) == 0:
                                    print(
                                        "\nThe consensus sequence for Homo sapiens was also unable to be created!"
                                    )

                            elif len(
                                consensuse_dictionary["sequence"]
                            ) == 0 and input_dict["species"] not in [
                                "both",
                                "both2",
                                "mutli",
                            ]:
                                project = None
                                print(
                                    "\nThe consensus sequence was also unable to be created!"
                                )

                        if (
                            len(consensuse_dictionary["sequence"]) > 0
                            or refseq_sequences != None
                        ):
                            project = rnai_selection_to_vector(
                                project,
                                consensuse_dictionary,
                                metadata,
                                project["elements"]["loop"],
                                input_dict["species"].lower(),
                                end_3=input_dict["overhang_3_prime"].upper(),
                                show_plot=show_plot,
                                rnai_type=input_dict["rnai_type"].lower(),
                                length=int(input_dict["rnai_length"]),
                                n_max=500,
                                source=source,
                            )
                            if project["rnai"]["sequence"] != None:
                                project["rnai"]["name"] = (
                                    input_dict["rnai_gene_name"]
                                    + "_"
                                    + project["rnai"]["name"]
                                )
                                project["rnai"]["species"] = input_dict[
                                    "species"
                                ].lower()
                            elif project["rnai"]["sequence"] == None and input_dict[
                                "species"
                            ] in ["both", "both2", "mutli"]:
                                print(
                                    "\nThe consensus sequence for both species was unable to be created! We will try obtain consensuse for Homo sapiens!"
                                )
                                refseq_sequences = get_sequences_gene(
                                    input_dict["rnai_gene_name"], "human"
                                )
                                fasta_string = generate_fasta_string(refseq_sequences)
                                alignments = MuscleMultipleSequenceAlignment(
                                    fasta_string,
                                    output="results",
                                    gapopen=10,
                                    gapextend=0.5,
                                )
                                consensuse_dictionary = ExtractConsensuse(
                                    alignments, refseq_sequences=refseq_sequences
                                )
                                if len(consensuse_dictionary["sequence"]) == 0:
                                    print(
                                        "\nThe consensus sequence for Homo sapiens was also unable to be created!"
                                    )
                                    project = None
                                elif len(consensuse_dictionary["sequence"]) > 0:
                                    project = rnai_selection_to_vector(
                                        project,
                                        consensuse_dictionary,
                                        metadata,
                                        project["elements"]["loop"],
                                        input_dict["species"].lower(),
                                        end_3=input_dict["overhang_3_prime"].upper(),
                                        show_plot=show_plot,
                                        rnai_type=input_dict["rnai_type"].lower(),
                                        length=int(input_dict["rnai_length"]),
                                        n_max=500,
                                        source=source,
                                    )
                                    if project["rnai"]["sequence"] != None:
                                        project["rnai"]["name"] = (
                                            input_dict["rnai_gene_name"]
                                            + "_"
                                            + project["rnai"]["name"]
                                        )
                                        project["rnai"]["species"] = "human"

                                    else:
                                        project = None
                                        print(
                                            "\nThe project could not be created due to trouble with the RNAi selection!"
                                        )
                            else:
                                project = None
                                print(
                                    "\nThe project could not be created due to trouble with the RNAi selection!"
                                )

                        else:
                            project = None

                            print(
                                "\nThe project could not be created due to trouble with the consensus sequence obtained. You can try to prepare custom RNAi and paste it into the project next time!"
                            )

                    else:
                        refseq_sequences = get_sequences_gene(
                            input_dict["rnai_gene_name"], input_dict["species"]
                        )
                        if refseq_sequences != None:
                            fasta_string = generate_fasta_string(refseq_sequences)
                            alignments = MuscleMultipleSequenceAlignment(
                                fasta_string,
                                output="results",
                                gapopen=10,
                                gapextend=0.5,
                            )
                            consensuse_dictionary = ExtractConsensuse(
                                alignments, refseq_sequences=refseq_sequences
                            )

                            if len(
                                consensuse_dictionary["sequence"]
                            ) == 0 and input_dict["species"] in [
                                "both",
                                "both2",
                                "mutli",
                            ]:
                                print(
                                    "\nThe consensus sequence for both species was unable to be created! We will try obtain consensuse for Homo sapiens!"
                                )
                                refseq_sequences = get_sequences_gene(
                                    input_dict["rnai_gene_name"], "human"
                                )
                                fasta_string = generate_fasta_string(refseq_sequences)
                                alignments = MuscleMultipleSequenceAlignment(
                                    fasta_string,
                                    output="results",
                                    gapopen=10,
                                    gapextend=0.5,
                                )
                                consensuse_dictionary = ExtractConsensuse(
                                    alignments, refseq_sequences=refseq_sequences
                                )
                                if len(consensuse_dictionary["sequence"]) == 0:
                                    print(
                                        "\nThe consensus sequence for Homo sapiens was also unable to be created!"
                                    )

                            elif len(
                                consensuse_dictionary["sequence"]
                            ) == 0 and input_dict["species"] not in [
                                "both",
                                "both2",
                                "mutli",
                            ]:
                                project = None
                                print(
                                    "\nThe consensus sequence was also unable to be created!"
                                )

                        if (
                            len(consensuse_dictionary["sequence"]) > 0
                            or refseq_sequences != None
                        ):
                            project = rnai_selection_to_vector(
                                project,
                                consensuse_dictionary,
                                metadata,
                                "",
                                input_dict["species"].lower(),
                                end_3=input_dict["overhang_3_prime"].upper(),
                                show_plot=show_plot,
                                rnai_type=input_dict["rnai_type"].lower(),
                                length=int(input_dict["rnai_length"]),
                                n_max=500,
                                source=source,
                            )
                            if project["rnai"]["sequence"] != None:
                                project["rnai"]["name"] = (
                                    input_dict["rnai_gene_name"]
                                    + "_"
                                    + project["rnai"]["name"]
                                )
                                project["rnai"]["species"] = input_dict[
                                    "species"
                                ].lower()
                            elif project["rnai"]["sequence"] == None and input_dict[
                                "species"
                            ] in ["both", "both2", "mutli"]:
                                print(
                                    "\nThe consensus sequence for both species was unable to be created! We will try obtain consensuse for Homo sapiens!"
                                )
                                refseq_sequences = get_sequences_gene(
                                    input_dict["rnai_gene_name"], "human"
                                )
                                fasta_string = generate_fasta_string(refseq_sequences)
                                alignments = MuscleMultipleSequenceAlignment(
                                    fasta_string,
                                    output="results",
                                    gapopen=10,
                                    gapextend=0.5,
                                )
                                consensuse_dictionary = ExtractConsensuse(
                                    alignments, refseq_sequences=refseq_sequences
                                )
                                if len(consensuse_dictionary["sequence"]) == 0:
                                    print(
                                        "\nThe consensus sequence for Homo sapiens was also unable to be created!"
                                    )
                                    project = None
                                elif len(consensuse_dictionary["sequence"]) > 0:
                                    project = rnai_selection_to_vector(
                                        project,
                                        consensuse_dictionary,
                                        metadata,
                                        "",
                                        input_dict["species"].lower(),
                                        end_3=input_dict["overhang_3_prime"].upper(),
                                        show_plot=show_plot,
                                        rnai_type=input_dict["rnai_type"].lower(),
                                        length=int(input_dict["rnai_length"]),
                                        n_max=500,
                                        source=source,
                                    )
                                    if project["rnai"]["sequence"] != None:
                                        project["rnai"]["name"] = (
                                            input_dict["rnai_gene_name"]
                                            + "_"
                                            + project["rnai"]["name"]
                                        )
                                        project["rnai"]["species"] = "human"

                                    else:
                                        project = None
                                        print(
                                            "\nThe project could not be created due to trouble with the RNAi selection!"
                                        )
                            else:
                                project = None
                                print(
                                    "\nThe project could not be created due to trouble with the RNAi selection!"
                                )

                        else:
                            project = None

                            print(
                                "\nThe project could not be created due to trouble with the consensus sequence obtained. You can try to prepare custom RNAi and paste it into the project next time!"
                            )

    except:
        project = None

        print(
            "\nThe project could not be created due to trouble with input data issue. Check input data or contact us!"
        )

    return project


def create_mrna_from_dict(metadata, input_dict, show_plot=True, source=_cwd):
    try:
        list_to_check_mrna = [
            "project_name",
            "species",
            "sequence",
            "sequence_name",
            "restriction_list",
            "optimize",
        ]

        if set(list_to_check_mrna).issubset(input_dict.keys()):
            must_not_zero = ["project_name", "species", "sequence", "sequence_name"]

            required = []
            for be in must_not_zero:
                if len(input_dict[str(be)]) == 0:
                    required.append(be)

            if input_dict["optimize"] not in [True, False]:
                required.append("optimize")

            seq_to_check = ["sequence"]

            not_coding = []
            not_in_upac = []
            for s in seq_to_check:
                try:
                    input_dict[s]
                    if len(input_dict[s]) > 0:
                        if not isinstance(input_dict[s], list) and s == "sequence":
                            tmp = clear_sequence(input_dict[s])
                            cod = check_coding(tmp)
                            if cod == False:
                                not_coding.append(s)
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                        else:
                            tmp = clear_sequence(input_dict[s])
                            upc = check_upac(tmp)
                            if upc == False:
                                not_in_upac.append(s)

                            input_dict[s] = tmp

                except:
                    not_in_upac.append(s)

            if len(required) == 0 and len(not_in_upac) == 0 and len(not_coding) == 0:
                project = {"project_name": input_dict["project_name"]}
                project["transcripts"] = {}
                project["transcripts"]["sequences"] = {}

                project["transcripts"]["sequences"]["sequence"] = input_dict["sequence"]
                project["transcripts"]["sequences"]["name"] = input_dict[
                    "sequence_name"
                ]

            run1 = input_dict["optimize"]

            if "transcript_GC" not in input_dict.keys():
                transcript_GC = 59
            else:
                transcript_GC = int(input_dict["transcript_GC"])

            if "poly_len" not in input_dict.keys():
                transcript_rep = 7
            else:
                transcript_rep = int(input_dict["poly_len"])

            project = sequence_enrichment_denovo(
                project,
                metadata,
                input_dict["species"].lower(),
                run=run1,
                GC_pct=transcript_GC,
                correct_rep=transcript_rep,
            )

            if run1:
                project = sequence_enrichment_alternative_denovo(
                    project,
                    input_dict,
                    metadata,
                    input_dict["species"].lower(),
                    run=True,
                    GC_pct=transcript_GC,
                    correct_rep=transcript_rep,
                )

            if len(input_dict["restriction_list"]) == 0:
                input_dict["restriction_list"] = ["SapI", "BsiWI", "AscI"]
            else:
                input_dict["restriction_list"] = input_dict["restriction_list"] + [
                    "SapI",
                    "BsiWI",
                    "AscI",
                ]

            if len(input_dict["restriction_list"]) > 0:
                run2 = True
            else:
                run2 = False

            project = find_restriction_vector_denovo(project, metadata, run=run2)

            if run1:
                project = find_restriction_vector_alternative_denovo(
                    project, metadata, run=run2
                )

            if run2:
                user_defined_enzymes = [
                    e.upper() for e in input_dict["restriction_list"]
                ]
                if len(user_defined_enzymes) > 0:
                    tmp = pd.DataFrame(
                        project["transcripts"]["sequences"]["enzymes_df"]
                    )
                    tmp["name"] = [t.upper() for t in tmp["name"]]
                    en = list(tmp["index"][tmp["name"].isin(user_defined_enzymes)])
                    project["transcripts"]["sequences"]["enzymes"] = [
                        item for sublist in en for item in sublist
                    ]
                else:
                    project["transcripts"]["sequences"]["enzymes"] = []

                project = repair_restriction_vector_denovo(
                    project, metadata, input_dict["species"]
                )

                if run1:
                    # alternative
                    user_defined_enzymes = [
                        e.upper() for e in input_dict["restriction_list"]
                    ]
                    for n in project["transcripts"]["alternative"].keys():
                        if len(user_defined_enzymes) > 0:
                            tmp = pd.DataFrame(
                                project["transcripts"]["alternative"][n]["enzymes_df"]
                            )
                            tmp["name"] = [t.upper() for t in tmp["name"]]
                            en = list(
                                tmp["index"][tmp["name"].isin(user_defined_enzymes)]
                            )
                            list_tmp = [item for sublist in en for item in sublist]
                            project["transcripts"]["alternative"][n][
                                "enzymes"
                            ] = list_tmp
                        else:
                            project["transcripts"]["alternative"][n]["enzymes"] = []

                    project = repair_restriction_vector_alternative_denovo(
                        project, metadata, input_dict["species"]
                    )

        figure, dot = predict_structure(
            dna_to_rna(
                project["transcripts"]["sequences"]["sequence"], enrichment=False
            ),
            anty_sequence="",
            height=None,
            width=None,
            dis_alpha=0.1,
            seq_force=27,
            pair_force=3,
            show_plot=show_plot,
        )

        project["transcripts"]["sequences"]["sequence_figure"] = figure
        project["transcripts"]["sequences"]["sequence_dot"] = dot

        if run1:
            figure, dot = predict_structure(
                dna_to_rna(
                    project["transcripts"]["sequences"]["optimized_sequence"],
                    enrichment=False,
                ),
                anty_sequence="",
                height=None,
                width=None,
                dis_alpha=0.1,
                seq_force=27,
                pair_force=3,
                show_plot=show_plot,
            )

            project["transcripts"]["sequences"]["optimized_sequence_figure"] = figure
            project["transcripts"]["sequences"]["optimized_sequence_dot"] = dot

        return project

    except:
        project = None

        print(
            "\nThe project could not be created due to trouble with input data issue. Check input data or contact us!"
        )


def create_sequence_from_dict(metadata, input_dict: dict, show_plot: bool = True):
    """
    This function change provided by user metadata into two types of predicted sequences:
        -expression (artificial gene - mRNA)
        -RNAi (silencing - siRNA/shRNA)


    Args:
       metadata (dict) - matadata loaded in the load_metadata() function
       input_dict (dict) - dictionary of metadata provided by the user


    Examples:
        -expression (mRNA)
        -RNAi (siRNA/shRNA)


        Avaiable on https://github.com/jkubis96/JBioSeqTools
        If you have any problem, don't hesitate to contact us!

    Args
        show_plot (bool) - if True the plot will be displayed, if False only the graph will be returned to the project. Default: True


    Returns:
        dict: Dictionary including all vector data (graphs, sequences, fasta) created based on user definition

    """

    try:
        denovo_rnai = [
            "project_name",
            "species",
            "rnai_type",
            "rnai_length",
            "overhang_3_prime",
            "rnai_sequence",
            "rnai_gene_name",
            "loop_sequence",
        ]

        denovo_mrna = [
            "project_name",
            "species",
            "sequence",
            "sequence_name",
            "restriction_list",
            "optimize",
        ]

        if set(denovo_rnai).issubset(input_dict.keys()):
            project = create_rnai_from_dict(metadata, input_dict, show_plot=show_plot)

        elif set(denovo_mrna).issubset(input_dict.keys()):
            project = create_mrna_from_dict(metadata, input_dict, show_plot=show_plot)

        else:
            print(
                "\nThe input data does not pass to any function. \n Check the input data or contact us!"
            )
            project = None

    except:
        project = None
        print(
            "\nThe project could not be created due to trouble with input data issue. Check input data or contact us!"
        )

    return project


#       _  ____   _         _____              _
#      | ||  _ \ (_)       / ____|            | |
#      | || |_) | _   ___ | (___   _   _  ___ | |_  ___  _ __ ___
#  _   | ||  _ < | | / _ \ \___ \ | | | |/ __|| __|/ _ \| '_ ` _ \
# | |__| || |_) || || (_) |____) || |_| |\__ \| |_ | __/| | | | | |
#  \____/ |____/ |_| \___/|_____/  \__, ||___/ \__|\___||_| |_| |_|
#                                   __/ |
#                                  |___/
