import pytest

from jbst import seq_tools as st
from jbst import vector_build as vb


# Metadata loading
def test_load_metadata():
    assert st.load_metadata() is not None


def test_load_metadata_reduced():
    metadata = st.load_metadata(
        linkers=False,
        loops=False,
        regulators=False,
        fluorescent_tag=False,
        promoters=False,
        polya=False,
        marker=False,
        utr5=False,
        utr3=False,
    )
    assert metadata is not None


# get_sequences_gene
@pytest.mark.parametrize("species", ["human", "mouse", "rat", "both", "both2", "multi"])
def test_get_sequences_gene(species):
    assert st.get_sequences_gene("SMN1", species=species, max_results=100) is not None


# get_sequences_accesion
def test_get_sequences_accesion():
    assert st.get_sequences_accesion(["X81403.1", "KJ890665.1"]) is not None


# generate fasta
def test_generate_and_write_fasta():
    res = st.get_sequences_gene("SMN1", species="both", max_results=100)
    fasta = st.generate_fasta_string(res)
    assert fasta is not None


# alignment
def test_alignment_pipeline():
    res = st.get_sequences_gene("SMN1", species="both", max_results=100)
    fasta = st.generate_fasta_string(res)
    aln = st.MuscleMultipleSequenceAlignment(
        fasta, output=None, gapopen=10, gapextend=0.5
    )
    assert aln is not None
    decoded = st.decode_alignments(aln)
    assert decoded is not None
    assert st.ExtractConsensuse(aln, refseq_sequences=None) is not None


# display alignment
def test_display_alignment():
    res = st.get_sequences_gene("SMN1", species="both", max_results=100)
    fasta = st.generate_fasta_string(res)
    aln = st.MuscleMultipleSequenceAlignment(
        fasta, output=None, gapopen=10, gapextend=0.5
    )
    fig = st.DisplayAlignment(
        aln, color_scheme="Taylor", wrap_length=80, show_grid=True, show_consensus=True
    )
    assert fig is not None


# sequence conversion
def test_sequence_conversion():
    seq = """
    
    #                             atg gcgatgagca gcggcggcag tggtggcggc gtcccggagc
    #        61 aggaggattc cgtgctgttc cggcgcggca caggccagag cgatgattct gacatttggg
    #       121 atgatacagc actgataaaa gcatatgata aagctgtggc ttcatttaag catgctctaa
    #       181 agaatggtga catttgtgaa acttcgggta aaccaaaaac cacacctaaa agaaaacctg
    #       241 ctaagaagaa taaaagccaa aagaagaata ctgcagcttc cttacaacag tggaaagttg
    #       301 gggacaaatg ttctgccatt tggtcagaag acggttgcat ttacccagct accattgctt
    #       361 caattgattt taagagagaa acctgtgttg tggtttacac tggatatgga aatagagagg
    #       421 agcaaaatct gtccgatcta ctttccccaa tctgtgaagt agctaataat atagaacaaa
    #       481 atgctcaaga gaatgaaaat gaaagccaag tttcaacaga tgaaagtgag aactccaggt
    #       541 ctcctggaaa taaatcagat aacatcaagc ccaaatctgc tccatggaac tcttttctcc
    #       601 ctccaccacc ccccatgcca gggccaagac tgggaccagg aaagccaggt ctaaaattca
    #       661 atggcccacc accgccaccg ccaccaccac caccccactt actatcatgc tggctgcctc
    #       721 catttccttc tggaccacca ataattcccc caccacctcc catatgtcca gattctcttg
    #       781 atgatgctga tgctttggga agtatgttaa tttcatggta catgagtggc tatcatactg
    #       841 gctattatat gggtttcaga caaaatcaaa aagaaggaag gtgctcacat tccttaaatt
    #       901 aa    
    
          """
    seq = st.clear_sequence(seq)
    assert seq is not None
    assert st.check_coding(seq) in [True, False]
    assert st.check_upac(seq) in [True, False]
    assert st.reverse(seq) is not None
    assert st.complement(seq) is not None
    rna = st.dna_to_rna(seq, enrichment=False)
    assert rna is not None
    rna2 = st.dna_to_rna(seq, enrichment=True)
    assert rna2 is not None
    assert st.rna_to_dna(rna) is not None


# translation / structure
def test_protein_translation_and_structure():
    metadata = st.load_metadata()
    seq = """
    
    #                             atg gcgatgagca gcggcggcag tggtggcggc gtcccggagc
    #        61 aggaggattc cgtgctgttc cggcgcggca caggccagag cgatgattct gacatttggg
    #       121 atgatacagc actgataaaa gcatatgata aagctgtggc ttcatttaag catgctctaa
    #       181 agaatggtga catttgtgaa acttcgggta aaccaaaaac cacacctaaa agaaaacctg
    #       241 ctaagaagaa taaaagccaa aagaagaata ctgcagcttc cttacaacag tggaaagttg
    #       301 gggacaaatg ttctgccatt tggtcagaag acggttgcat ttacccagct accattgctt
    #       361 caattgattt taagagagaa acctgtgttg tggtttacac tggatatgga aatagagagg
    #       421 agcaaaatct gtccgatcta ctttccccaa tctgtgaagt agctaataat atagaacaaa
    #       481 atgctcaaga gaatgaaaat gaaagccaag tttcaacaga tgaaagtgag aactccaggt
    #       541 ctcctggaaa taaatcagat aacatcaagc ccaaatctgc tccatggaac tcttttctcc
    #       601 ctccaccacc ccccatgcca gggccaagac tgggaccagg aaagccaggt ctaaaattca
    #       661 atggcccacc accgccaccg ccaccaccac caccccactt actatcatgc tggctgcctc
    #       721 catttccttc tggaccacca ataattcccc caccacctcc catatgtcca gattctcttg
    #       781 atgatgctga tgctttggga agtatgttaa tttcatggta catgagtggc tatcatactg
    #       841 gctattatat gggtttcaga caaaatcaaa aagaaggaag gtgctcacat tccttaaatt
    #       901 aa    
    
          """
    seq = st.clear_sequence(seq)
    rna = st.dna_to_rna(seq, enrichment=False)
    assert st.seuqence_to_protein(rna, metadata) is not None
    assert st.seuqence_to_protein(seq, metadata) is not None
    pred, dot = st.predict_structure(rna, show_plot=True)
    assert pred is not None


# RNAi
def test_rnai_pipeline():
    seq = """
    
    #                             atg gcgatgagca gcggcggcag tggtggcggc gtcccggagc
    #        61 aggaggattc cgtgctgttc cggcgcggca caggccagag cgatgattct gacatttggg
    #       121 atgatacagc actgataaaa gcatatgata aagctgtggc ttcatttaag catgctctaa
    #       181 agaatggtga catttgtgaa acttcgggta aaccaaaaac cacacctaaa agaaaacctg
    #       241 ctaagaagaa taaaagccaa aagaagaata ctgcagcttc cttacaacag tggaaagttg
    #       301 gggacaaatg ttctgccatt tggtcagaag acggttgcat ttacccagct accattgctt
    #       361 caattgattt taagagagaa acctgtgttg tggtttacac tggatatgga aatagagagg
    #       421 agcaaaatct gtccgatcta ctttccccaa tctgtgaagt agctaataat atagaacaaa
    #       481 atgctcaaga gaatgaaaat gaaagccaag tttcaacaga tgaaagtgag aactccaggt
    #       541 ctcctggaaa taaatcagat aacatcaagc ccaaatctgc tccatggaac tcttttctcc
    #       601 ctccaccacc ccccatgcca gggccaagac tgggaccagg aaagccaggt ctaaaattca
    #       661 atggcccacc accgccaccg ccaccaccac caccccactt actatcatgc tggctgcctc
    #       721 catttccttc tggaccacca ataattcccc caccacctcc catatgtcca gattctcttg
    #       781 atgatgctga tgctttggga agtatgttaa tttcatggta catgagtggc tatcatactg
    #       841 gctattatat gggtttcaga caaaatcaaa aagaaggaag gtgctcacat tccttaaatt
    #       901 aa    
    
          """
    seq = st.clear_sequence(seq)
    metadata = st.load_metadata(
        linkers=False,
        loops=False,
        regulators=False,
        fluorescent_tag=False,
        promoters=False,
        polya=False,
        marker=False,
        utr5=False,
        utr3=False,
    )
    res = st.FindRNAi(
        seq,
        metadata,
        length=23,
        n=200,
        max_repeat_len=3,
        max_off=1,
        species="human",
        output=None,
        database_name="refseq_select_rna",
        evalue=1e-3,
        outfmt=5,
        word_size=7,
        max_hsps=20,
        reward=1,
        penalty=-3,
        gapopen=5,
        gapextend=2,
        dust="no",
        extension="xml",
    )
    assert len(res.index) > 0
    loop_seq = "CTCGAG"
    res2 = st.loop_complementary_adjustment(res, loop_seq, min_length=3)
    assert len(res2.index) > 0
    shrna = st.dna_to_rna(res2["RNAi_sense"][0] + "CTCGAG" + res2["RNAi_seq"][0] + "TT")
    assert shrna is not None
    pred, dot = st.predict_structure(shrna, show_plot=True)
    assert pred is not None


# codon optimization
@pytest.mark.parametrize("species", ["human", "mouse", "rat", "both", "both2", "multi"])
def test_codon_optimization(species):
    seq = """
    
    #                             atg gcgatgagca gcggcggcag tggtggcggc gtcccggagc
    #        61 aggaggattc cgtgctgttc cggcgcggca caggccagag cgatgattct gacatttggg
    #       121 atgatacagc actgataaaa gcatatgata aagctgtggc ttcatttaag catgctctaa
    #       181 agaatggtga catttgtgaa acttcgggta aaccaaaaac cacacctaaa agaaaacctg
    #       241 ctaagaagaa taaaagccaa aagaagaata ctgcagcttc cttacaacag tggaaagttg
    #       301 gggacaaatg ttctgccatt tggtcagaag acggttgcat ttacccagct accattgctt
    #       361 caattgattt taagagagaa acctgtgttg tggtttacac tggatatgga aatagagagg
    #       421 agcaaaatct gtccgatcta ctttccccaa tctgtgaagt agctaataat atagaacaaa
    #       481 atgctcaaga gaatgaaaat gaaagccaag tttcaacaga tgaaagtgag aactccaggt
    #       541 ctcctggaaa taaatcagat aacatcaagc ccaaatctgc tccatggaac tcttttctcc
    #       601 ctccaccacc ccccatgcca gggccaagac tgggaccagg aaagccaggt ctaaaattca
    #       661 atggcccacc accgccaccg ccaccaccac caccccactt actatcatgc tggctgcctc
    #       721 catttccttc tggaccacca ataattcccc caccacctcc catatgtcca gattctcttg
    #       781 atgatgctga tgctttggga agtatgttaa tttcatggta catgagtggc tatcatactg
    #       841 gctattatat gggtttcaga caaaatcaaa aagaaggaag gtgctcacat tccttaaatt
    #       901 aa    
    
          """
    seq = st.clear_sequence(seq)
    metadata = st.load_metadata(linkers=False)
    res = st.codon_otymization(seq, metadata, species=species)
    assert len(res.index) > 0


# restriction check and repair
def test_restriction_removal():
    seq = """
    
    #                             atg gcgatgagca gcggcggcag tggtggcggc gtcccggagc
    #        61 aggaggattc cgtgctgttc cggcgcggca caggccagag cgatgattct gacatttggg
    #       121 atgatacagc actgataaaa gcatatgata aagctgtggc ttcatttaag catgctctaa
    #       181 agaatggtga catttgtgaa acttcgggta aaccaaaaac cacacctaaa agaaaacctg
    #       241 ctaagaagaa taaaagccaa aagaagaata ctgcagcttc cttacaacag tggaaagttg
    #       301 gggacaaatg ttctgccatt tggtcagaag acggttgcat ttacccagct accattgctt
    #       361 caattgattt taagagagaa acctgtgttg tggtttacac tggatatgga aatagagagg
    #       421 agcaaaatct gtccgatcta ctttccccaa tctgtgaagt agctaataat atagaacaaa
    #       481 atgctcaaga gaatgaaaat gaaagccaag tttcaacaga tgaaagtgag aactccaggt
    #       541 ctcctggaaa taaatcagat aacatcaagc ccaaatctgc tccatggaac tcttttctcc
    #       601 ctccaccacc ccccatgcca gggccaagac tgggaccagg aaagccaggt ctaaaattca
    #       661 atggcccacc accgccaccg ccaccaccac caccccactt actatcatgc tggctgcctc
    #       721 catttccttc tggaccacca ataattcccc caccacctcc catatgtcca gattctcttg
    #       781 atgatgctga tgctttggga agtatgttaa tttcatggta catgagtggc tatcatactg
    #       841 gctattatat gggtttcaga caaaatcaaa aagaaggaag gtgctcacat tccttaaatt
    #       901 aa    
    
          """
    seq = st.clear_sequence(seq)
    metadata = st.load_metadata()
    res1, res2 = st.check_restriction(seq, metadata)
    assert len(res1.index) > 0
    rep1 = st.sequence_restriction_removal(
        seq, metadata, restriction_places=["SfcI", "BbvI"], species="human"
    )
    assert rep1["sequence_na"][1] is not None


# vector building
def test_vector_plot_from_fasta():
    fasta = vb.load_fasta("jbst/tests/fasta_vector_test.fasta")
    assert fasta is not None
    df = vb.decode_fasta_to_dataframe(fasta)
    df = vb.extract_fasta_info(df)
    plot = vb.plot_vector(df)
    assert plot is not None


def test_vector_expression():
    metadata = vb.load_metadata(
        linkers=False,
        loops=False,
        regulators=False,
        fluorescent_tag=False,
        promoters=False,
        polya=False,
        marker=False,
        utr5=False,
        utr3=False,
    )

    input_dict = {
        "project_name": "test",
        "vector_type": "ssAAV",
        "vector_function": "expression",
        "species": "human",
        "sequences": [
            "ATGGCGATGAGCAGCGGCGGCAGTGGTGGCGGCGTCCCGGAGCAGGAGGATTCCGTGCTGTTCCGGCGCGGCACAGGCCAGAGCGATGATTCTGACATTTGGGATGATACAGCACTGATAAAAGCATATGATAAAGCTGTGGCTTCATTTAAGCATGCTCTAAAGAATGGTGACATTTGTGAAACTTCGGGTAAACCAAAAACCACACCTAAAAGAAAACCTGCTAAGAAGAATAAAAGCCAAAAGAAGAATACTGCAGCTTCCTTACAACAGTGGAAAGTTGGGGACAAATGTTCTGCCATTTGGTCAGAAGACGGTTGCATTTACCCAGCTACCATTGCTTCAATTGATTTTAAGAGAGAAACCTGTGTTGTGGTTTACACTGGATATGGAAATAGAGAGGAGCAAAATCTGTCCGATCTACTTTCCCCAATCTGTGAAGTAGCTAATAATATAGAACAAAATGCTCAAGAGAATGAAAATGAAAGCCAAGTTTCAACAGATGAAAGTGAGAACTCCAGGTCTCCTGGAAATAAATCAGATAACATCAAGCCCAAATCTGCTCCATGGAACTCTTTTCTCCCTCCACCACCCCCCATGCCAGGGCCAAGACTGGGACCAGGAAAGCCAGGTCTAAAATTCAATGGCCCACCACCGCCACCGCCACCACCACCACCCCACTTACTATCATGCTGGCTGCCTCCATTTCCTTCTGGACCACCAATAATTCCCCCACCACCTCCCATATGTCCAGATTCTCTTGATGATGCTGATGCTTTGGGAAGTATGTTAATTTCATGGTACATGAGTGGCTATCATACTGGCTATTATATGTTTCCTGAGGCCTCCCTAAAAGCCGAGCAGATGCCAGCACCATGCTTCCTGTAA",
        ],
        "sequences_names": ["SMN1"],
        "promoter_name": "TBG",
        "promoter_sequence": "GGGCTGGAAGCTACCTTTGACATCATTTCCTCTGCGAATGCATGTATAATTTCTACAGAACCTATTAGAAAGGATCACCCAGCCTCTGCTTTTGTACAACTTTCCCTTAAAAAACTGCCAATTCCACTGCTGTTTGGCCCAATAGTGAGAACTTTTTCCTGCTGCCTCTTGGTGCTTTTGCCTATGGCCCCTATTCTGCCTGCTGAAGACACTCTTGCCAGCATGGACTTAAACCCCTCCAGCTCTGACAATCCTCTTTCTCTTTTGTTTTACATGAAGGGTCTGGCAGCCAAAGCAATCACTCAAAGTTCAAACCTTATCATTTTTTGCTTTGTTCCTCTTGGCCTTGGTTTTGTACATCAGCTTTGAAAATACCATCCCAGGGTTAATGCTGGGGTTAATTTATAACTAAGAGTGCTCTAGTTTTGCAATACAGGACATGCTATAAAAATGGAAAGAT",
        "regulator_name": "WPRE",
        "regulator_sequence": "CGATAATCAACCTCTGGATTACAAAATTTGTGAAAGATTGACTGGTATTCTTAACTATGTTGCTCCTTTTACGCTATGTGGATACGCTGCTTTAATGCCTTTGTATCATGCTATTGCTTCCCGTATGGCTTTCATTTTCTCCTCCTTGTATAAATCCTGGTTGCTGTCTCTTTATGAGGAGTTGTGGCCCGTTGTCAGGCAACGTGGCGTGGTGTGCACTGTGTTTGCTGACGCAACCCCCACTGGTTGGGGCATTGCCACCACCTGTCAGCTCCTTTCCGGGACTTTCGCTTTCCCCCTCCCTATTGCCACGGCGGAACTCATCGCCGCCTGCCTTGCCCGCTGCTGGACAGGGGCTCGGCTGTTGGGCACTGACAATTCCGTGGTGTTGTCGGGGAAGCTGACGTCCTTTCCATGGCTGCTCGCCTGTGTTGCCACCTGGATTCTGCGCGGGACGTCCTTCTGCTACGTCCCTTCGGCCCTCAATCCAGCGGACCTTCCTTCCCGCGGCCTGCTGCCGGCTCTGCGGCCTCTTCCGCGTCTTCGCCTTCGCCCTCAGACGAGTCGGATCTCCCTTTGGGCCGCCTCCCCGCATCGG",
        "polya_name": "SV40_late",
        "polya_sequence": "CAGACATGATAAGATACATTGATGAGTTTGGACAAACCACAACTAGAATGCAGTGAAAAAAATGCTTTATTTGTGAAATTTGTGATGCTATTGCTTTATTTGTAACCATTATAAGCTGCAATAAACAAGTTAACAACAACAATTGCATTCATTTTATGTTTCAGGTTCAGGGGGAGGTGTGGGAGGTTTTTTAAAGCAAGTAAAACCTCTACAAATGTGGTA",
        "linkers_names": [],
        "linkers_sequences": [],
        "fluorescence_name": "",
        "fluorescence_sequence": "",
        "fluorescence_linker_name": "",
        "fluorescence_linker_sequence": "",
        "fluorescence_promoter_name": "",
        "fluorescence_promoter_sequence": "",
        "fluorescence_polya_name": "",
        "fluorescence_polya_sequence": "",
        "selection_marker_name": "Ampicillin",
        "selection_marker_sequence": "ATGAGTATTCAACATTTCCGTGTCGCCCTTATTCCCTTTTTTGCGGCATTTTGCCTTCCTGTTTTTGCTCACCCAGAAACGCTGGTGAAAGTAAAAGATGCTGAAGATCAGTTGGGTGCACGAGTGGGTTACATCGAACTGGATCTCAACAGCGGTAAGATCCTTGAGAGTTTTCGCCCCGAAGAACGTTTTCCAATGATGAGCACTTTTAAAGTTCTGCTATGTGGCGCGGTATTATCCCGTATTGACGCCGGGCAAGAGCAACTCGGTCGCCGCATACACTATTCTCAGAATGACTTGGTTGAGTACTCACCAGTCACAGAAAAGCATCTTACGGATGGCATGACAGTAAGAGAATTATGCAGTGCTGCCATAACCATGAGTGATAACACTGCGGCCAACTTACTTCTGACAACGATCGGAGGACCGAAGGAGCTAACCGCTTTTTTGCACAACATGGGGGATCATGTAACTCGCCTTGATCGTTGGGAACCGGAGCTGAATGAAGCCATACCAAACGACGAGCGTGACACCACGATGCCTGTAGCAATGGCAACAACGTTGCGCAAACTATTAACTGGCGAACTACTTACTCTAGCTTCCCGGCAACAATTAATAGACTGGATGGAGGCGGATAAAGTTGCAGGACCACTTCTGCGCTCGGCCCTTCCGGCTGGCTGGTTTATTGCTGATAAATCTGGAGCCGGTGAGCGTGGAAGCCGCGGTATCATTGCAGCACTGGGGCCAGATGGTAAGCCCTCCCGTATCGTAGTTATCTACACGACGGGGAGTCAGGCAACTATGGATGAACGAAATAGACAGATCGCTGAGATAGGTGCCTCACTGATTAAGCATTGGTAA",
        "restriction_list": [],
        "optimize": True,
        "transcript_GC": 58,
        "poly_len": 7,
    }

    project = vb.vector_create_on_dict(metadata, input_dict, show_plot=False)

    assert project is not None


def test_vector_rnai():
    metadata = vb.load_metadata(
        linkers=False,
        loops=False,
        regulators=False,
        fluorescent_tag=False,
        promoters=False,
        polya=False,
        marker=False,
        utr5=False,
        utr3=False,
    )

    input_dict = {
        "project_name": "test_RNAi",
        "vector_type": "ssAAV",
        "vector_function": "rnai",
        "species": "human",
        "promoter_ncrna_name": "U6",
        "promoter_ncrna_sequence": "GAGGGCCTATTTCCCATGATTCCTTCATATTTGCATATACGATACAAGGCTGTTAGAGAGATAATTGGAATTAATTTGACTGTAAACACAAAGATATTAGTACAAAATACGTGACGTAGAAAGTAATAATTTCTTGGGTAGTTTGCAGTTTTAAAATTATGTTTTAAAATGGACTATCATATGCTTACCGTAACTTGAAAGTATTTCGATTTCTTGGCTTTATATATCTTGTGGAAAGGACGAAACACC",
        "rnai_sequence": "",
        "rnai_gene_name": "PAX3",
        "rnai_length": 20,
        "overhang_3_prime": "UU",
        "loop_sequence": "TAGTGAAGCCACAGATGTAC",
        "sequences": [
            "ATGTTAACTAGTGGACTTGTAGTAAGCAACATGTTCTCCTATCATCTCGCAGCCTTGGGACTCATGCCGTCATTCCAGATGGAAGGGCGAGGTCGAGTTAATCAGCTAGGAGGTGTTTTCATTAATGGACGGCCACTGCCCAACCATATACGACTGAAGATTGTCGAGCTAGCGGCCCAGGGCGTCCGTCCGTGCGTCATCAGTAGACAGCTGCGGGTGTCACATGGCTGTGTCAGTAAAATACTCCAACGATATCAAGAAACCGGAAGTATCCGACCTGGGGTTATTGGCGGAAGTAAACCAAGGGTCGCAACTCCGGAAGTTGAGAAAAAGATAGAACAATACAAAAAAGATAATCCGGGAATTTTCAGTTGGGAGATTCGGGATCGGCTGCTGAAGGAGGGGATTTGTGACCGCAGCACCGTGCCAAGTGTGAGCTCCATCAGTCGAGTATTACGGAGCAGGTTCCAGAAATGTGATTCTGATGACAATGACAATGACAATGACAATGAGGACGACGATGGCGATGACGGCAGTAACAGTAGTGTGGCAGACAGGTCTGTTAACTTCTCTGTCAGCGGTCTGCTGTCCGACAATAAAAGCGACAAAAGCGACAACGATTCCGATTGTGAATCAGAGCCGGGGCTATCTGTAAAACGGAAGCAACGCCGCAGTCGAACTACTTTCACCGCGGAGCAGTTGGAGGAACTGGAAAGAGCCTTTGAACGAACTCACTATCCGGATATATATACGCGAGAGGAATTAGCACAAAGAACAAAGCTAACCGAGGCAAGAGTCCAAGTATGGTTTAGTAACCGAAGAGCGAGATGGCGGAAACAGATGGGTAGCAATCAGCTGACAGCCTTGAACAGTATATTACAAGTGCCACAGGGTATGGGAACGCCCTCTTATATGCTGCACGAGCCTGGGTATCCACTCTCACATAATGCAGACAATCTTTGGCATAGATCGTCTATGGCCCAGTCATTACAGTCATTTGGTCAGACAATAAAACCAGAGAATTCCTACGCCGGTCTTATGGAAAACTATTTATCTCATTCATCACAGCTTCATGGTCTTCCTACACATAGTTCATCCGATCCCCTCTCATCCACTTGGTCATCTCCCGTGTCCACTTCCGTTCCTGCGCTAGGATACACGCCATCTAGTGGCCATTACCATCATTACTCTGATGTCACCAAAAGTACTCTTCATTCATATAACGCTCATATTCCTTCAGTCACAAACATGGAGAGATGTTCAGTTGATGACAGTTTGGTTGCTTTACGTATGAAGTCACGTGAGCATTCCGCCGCTCTCAGTTTGATGCAGGTGGCAGACAACAAAATGGCTACCTCATTTTGA"
        ],
        "sequences_names": ["SMN1"],
        "linkers_sequences": [""],
        "linkers_names": [""],
        "promoter_sequence": "GGGCTGGAAGCTACCTTTGACATCATTTCCTCTGCGAATGCATGTATAATTTCTACAGAACCTATTAGAAAGGATCACCCAGCCTCTGCTTTTGTACAACTTTCCCTTAAAAAACTGCCAATTCCACTGCTGTTTGGCCCAATAGTGAGAACTTTTTCCTGCTGCCTCTTGGTGCTTTTGCCTATGGCCCCTATTCTGCCTGCTGAAGACACTCTTGCCAGCATGGACTTAAACCCCTCCAGCTCTGACAATCCTCTTTCTCTTTTGTTTTACATGAAGGGTCTGGCAGCCAAAGCAATCACTCAAAGTTCAAACCTTATCATTTTTTGCTTTGTTCCTCTTGGCCTTGGTTTTGTACATCAGCTTTGAAAATACCATCCCAGGGTTAATGCTGGGGTTAATTTATAACTAAGAGTGCTCTAGTTTTGCAATACAGGACATGCTATAAAAATGGAAAGAT",
        "promoter_name": "TBG",
        "regulator_sequence": "CGATAATCAACCTCTGGATTACAAAATTTGTGAAAGATTGACTGGTATTCTTAACTATGTTGCTCCTTTTACGCTATGTGGATACGCTGCTTTAATGCCTTTGTATCATGCTATTGCTTCCCGTATGGCTTTCATTTTCTCCTCCTTGTATAAATCCTGGTTGCTGTCTCTTTATGAGGAGTTGTGGCCCGTTGTCAGGCAACGTGGCGTGGTGTGCACTGTGTTTGCTGACGCAACCCCCACTGGTTGGGGCATTGCCACCACCTGTCAGCTCCTTTCCGGGACTTTCGCTTTCCCCCTCCCTATTGCCACGGCGGAACTCATCGCCGCCTGCCTTGCCCGCTGCTGGACAGGGGCTCGGCTGTTGGGCACTGACAATTCCGTGGTGTTGTCGGGGAAGCTGACGTCCTTTCCATGGCTGCTCGCCTGTGTTGCCACCTGGATTCTGCGCGGGACGTCCTTCTGCTACGTCCCTTCGGCCCTCAATCCAGCGGACCTTCCTTCCCGCGGCCTGCTGCCGGCTCTGCGGCCTCTTCCGCGTCTTCGCCTTCGCCCTCAGACGAGTCGGATCTCCCTTTGGGCCGCCTCCCCGCATCGG",
        "regulator_name": "WPRE",
        "polya_sequence": "CAGACATGATAAGATACATTGATGAGTTTGGACAAACCACAACTAGAATGCAGTGAAAAAAATGCTTTATTTGTGAAATTTGTGATGCTATTGCTTTATTTGTAACCATTATAAGCTGCAATAAACAAGTTAACAACAACAATTGCATTCATTTTATGTTTCAGGTTCAGGGGGAGGTGTGGGAGGTTTTTTAAAGCAAGTAAAACCTCTACAAATGTGGTA",
        "polya_name": "SV40_late",
        "fluorescence_sequence": "ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAGTTCAGCGTGTCCGGCGAGGGCGAGGGCGATGCCACCTACGGCAAGCTGACCCTGAAGTTCATCTGCACCACCGGCAAGCTGCCCGTGCCCTGGCCCACCCTCGTGACCACCCTGACCTACGGCGTGCAGTGCTTCAGCCGCTACCCCGACCACATGAAGCAGCACGACTTCTTCAAGTCCGCCATGCCCGAAGGCTACGTCCAGGAGCGCACCATCTTCTTCAAGGACGACGGCAACTACAAGACCCGCGCCGAGGTGAAGTTCGAGGGCGACACCCTGGTGAACCGCATCGAGCTGAAGGGCATCGACTTCAAGGAGGACGGCAACATCCTGGGGCACAAGCTGGAGTACAACTACAACAGCCACAACGTCTATATCATGGCCGACAAGCAGAAGAACGGCATCAAGGTGAACTTCAAGATCCGCCACAACATCGAGGACGGCAGCGTGCAGCTCGCCGACCACTACCAGCAGAACACCCCCATCGGCGACGGCCCCGTGCTGCTGCCCGACAACCACTACCTGAGCACCCAGTCCGCCCTGAGCAAAGACCCCAACGAGAAGCGCGATCACATGGTCCTGCTGGAGTTCGTGACCGCCGCCGGGATCACTCTCGGCATGGACGAGCTGTACAAGTAA",
        "fluorescence_name": "EGFP",
        "fluorescence_linker_sequence": "GGAAGCGGAGAGGGCAGGGGAAGTCTTCTAACATGCGGGGACGTGGAGGAAAATCCCGGCCCC",
        "fluorescence_linker_name": "T2A",
        "selection_marker_sequence": "ATGAGTATTCAACATTTCCGTGTCGCCCTTATTCCCTTTTTTGCGGCATTTTGCCTTCCTGTTTTTGCTCACCCAGAAACGCTGGTGAAAGTAAAAGATGCTGAAGATCAGTTGGGTGCACGAGTGGGTTACATCGAACTGGATCTCAACAGCGGTAAGATCCTTGAGAGTTTTCGCCCCGAAGAACGTTTTCCAATGATGAGCACTTTTAAAGTTCTGCTATGTGGCGCGGTATTATCCCGTATTGACGCCGGGCAAGAGCAACTCGGTCGCCGCATACACTATTCTCAGAATGACTTGGTTGAGTACTCACCAGTCACAGAAAAGCATCTTACGGATGGCATGACAGTAAGAGAATTATGCAGTGCTGCCATAACCATGAGTGATAACACTGCGGCCAACTTACTTCTGACAACGATCGGAGGACCGAAGGAGCTAACCGCTTTTTTGCACAACATGGGGGATCATGTAACTCGCCTTGATCGTTGGGAACCGGAGCTGAATGAAGCCATACCAAACGACGAGCGTGACACCACGATGCCTGTAGCAATGGCAACAACGTTGCGCAAACTATTAACTGGCGAACTACTTACTCTAGCTTCCCGGCAACAATTAATAGACTGGATGGAGGCGGATAAAGTTGCAGGACCACTTCTGCGCTCGGCCCTTCCGGCTGGCTGGTTTATTGCTGATAAATCTGGAGCCGGTGAGCGTGGAAGCCGCGGTATCATTGCAGCACTGGGGCCAGATGGTAAGCCCTCCCGTATCGTAGTTATCTACACGACGGGGAGTCAGGCAACTATGGATGAACGAAATAGACAGATCGCTGAGATAGGTGCCTCACTGATTAAGCATTGGTAA",
        "selection_marker_name": "Ampicillin",
        "restriction_list": ["RsaI", "MnlI", "AciI", "AluI", "BmrI"],
        "optimize": True,
        "transcript_GC": 58,
        "poly_len": 7,
    }

    project = vb.vector_create_on_dict(metadata, input_dict, show_plot=False)

    assert project is not None


def test_vector_transcription_rnai():
    metadata = vb.load_metadata(
        linkers=False,
        loops=False,
        regulators=False,
        fluorescent_tag=False,
        promoters=False,
        polya=False,
        marker=False,
        utr5=False,
        utr3=False,
    )

    input_dict = {
        "project_name": "test_invitro_transcription_RNAi",
        "vector_type": "transcription",
        "vector_function": "rnai",
        "species": "human",
        "rnai_sequence": "",
        "rnai_length": 20,
        "overhang_3_prime": "UU",
        "rnai_gene_name": "KIT",
        "loop_sequence": "TAGTGAAGCCACAGATGTAC",
        "selection_marker_sequence": "ATGAGTATTCAACATTTCCGTGTCGCCCTTATTCCCTTTTTTGCGGCATTTTGCCTTCCTGTTTTTGCTCACCCAGAAACGCTGGTGAAAGTAAAAGATGCTGAAGATCAGTTGGGTGCACGAGTGGGTTACATCGAACTGGATCTCAACAGCGGTAAGATCCTTGAGAGTTTTCGCCCCGAAGAACGTTTTCCAATGATGAGCACTTTTAAAGTTCTGCTATGTGGCGCGGTATTATCCCGTATTGACGCCGGGCAAGAGCAACTCGGTCGCCGCATACACTATTCTCAGAATGACTTGGTTGAGTACTCACCAGTCACAGAAAAGCATCTTACGGATGGCATGACAGTAAGAGAATTATGCAGTGCTGCCATAACCATGAGTGATAACACTGCGGCCAACTTACTTCTGACAACGATCGGAGGACCGAAGGAGCTAACCGCTTTTTTGCACAACATGGGGGATCATGTAACTCGCCTTGATCGTTGGGAACCGGAGCTGAATGAAGCCATACCAAACGACGAGCGTGACACCACGATGCCTGTAGCAATGGCAACAACGTTGCGCAAACTATTAACTGGCGAACTACTTACTCTAGCTTCCCGGCAACAATTAATAGACTGGATGGAGGCGGATAAAGTTGCAGGACCACTTCTGCGCTCGGCCCTTCCGGCTGGCTGGTTTATTGCTGATAAATCTGGAGCCGGTGAGCGTGGAAGCCGCGGTATCATTGCAGCACTGGGGCCAGATGGTAAGCCCTCCCGTATCGTAGTTATCTACACGACGGGGAGTCAGGCAACTATGGATGAACGAAATAGACAGATCGCTGAGATAGGTGCCTCACTGATTAAGCATTGGTAA",
        "selection_marker_name": "Ampicillin",
    }

    project = vb.vector_create_on_dict(metadata, input_dict, show_plot=False)

    assert project is not None


def test_vector_transcription_mrna():
    metadata = vb.load_metadata(
        linkers=False,
        loops=False,
        regulators=False,
        fluorescent_tag=False,
        promoters=False,
        polya=False,
        marker=False,
        utr5=False,
        utr3=False,
    )

    input_dict = {
        "project_name": "regular",
        "vector_type": "transcription",
        "vector_function": "mrna",
        "species": "human",
        "sequences": [
            "ATGGCGATGAGCAGCGGCGGCAGTGGTGGCGGCGTCCCGGAGCAGGAGGATTCCGTGCTGTTCCGGCGCGGCACAGGCCAGAGCGATGATTCTGACATTTGGGATGATACAGCACTGATAAAAGCATATGATAAAGCTGTGGCTTCATTTAAGCATGCTCTAAAGAATGGTGACATTTGTGAAACTTCGGGTAAACCAAAAACCACACCTAAAAGAAAACCTGCTAAGAAGAATAAAAGCCAAAAGAAGAATACTGCAGCTTCCTTACAACAGTGGAAAGTTGGGGACAAATGTTCTGCCATTTGGTCAGAAGACGGTTGCATTTACCCAGCTACCATTGCTTCAATTGATTTTAAGAGAGAAACCTGTGTTGTGGTTTACACTGGATATGGAAATAGAGAGGAGCAAAATCTGTCCGATCTACTTTCCCCAATCTGTGAAGTAGCTAATAATATAGAACAAAATGCTCAAGAGAATGAAAATGAAAGCCAAGTTTCAACAGATGAAAGTGAGAACTCCAGGTCTCCTGGAAATAAATCAGATAACATCAAGCCCAAATCTGCTCCATGGAACTCTTTTCTCCCTCCACCACCCCCCATGCCAGGGCCAAGACTGGGACCAGGAAAGCCAGGTCTAAAATTCAATGGCCCACCACCGCCACCGCCACCACCACCACCCCACTTACTATCATGCTGGCTGCCTCCATTTCCTTCTGGACCACCAATAATTCCCCCACCACCTCCCATATGTCCAGATTCTCTTGATGATGCTGATGCTTTGGGAAGTATGTTAATTTCATGGTACATGAGTGGCTATCATACTGGCTATTATATGTTTCCTGAGGCCTCCCTAAAAGCCGAGCAGATGCCAGCACCATGCTTCCTGTAA"
        ],
        "sequences_names": ["SMN1"],
        "linkers_names": ["T2A"],
        "linkers_sequences": [
            "GGAAGCGGAGAGGGCAGGGGAAGTCTTCTAACATGCGGGGACGTGGAGGAAAATCCCGGCCCC"
        ],
        "utr5_name": "TBG",
        "utr5_sequence": "GGGCTGGAAGCTACCTTTGACATCATTTCCTCTGCGAATGCATGTATAATTTCTACAGAACCTATTAGAAAGGATCACCCAGCCTCTGCTTTTGTACAACTTTCCCTTAAAAAACTGCCAATTCCACTGCTGTTTGGCCCAATAGTGAGAACTTTTTCCTGCTGCCTCTTGGTGCTTTTGCCTATGGCCCCTATTCTGCCTGCTGAAGACACTCTTGCCAGCATGGACTTAAACCCCTCCAGCTCTGACAATCCTCTTTCTCTTTTGTTTTACATGAAGGGTCTGGCAGCCAAAGCAATCACTCAAAGTTCAAACCTTATCATTTTTTGCTTTGTTCCTCTTGGCCTTGGTTTTGTACATCAGCTTTGAAAATACCATCCCAGGGTTAATGCTGGGGTTAATTTATAACTAAGAGTGCTCTAGTTTTGCAATACAGGACATGCTATAAAAATGGAAAGAT",
        "utr3_name": "SV40_late",
        "utr3_sequence": "CAGACATGATAAGATACATTGATGAGTTTGGACAAACCACAACTAGAATGCAGTGAAAAAAATGCTTTATTTGTGAAATTTGTGATGCTATTGCTTTATTTGTAACCATTATAAGCTGCAATAAACAAGTTAACAACAACAATTGCATTCATTTTATGTTTCAGGTTCAGGGGGAGGTGTGGGAGGTTTTTTAAAGCAAGTAAAACCTCTACAAATGTGGTA",
        "polya_tail_x": 10,
        "selection_marker_name": "Ampicillin",
        "selection_marker_sequence": "ATGAGTATTCAACATTTCCGTGTCGCCCTTATTCCCTTTTTTGCGGCATTTTGCCTTCCTGTTTTTGCTCACCCAGAAACGCTGGTGAAAGTAAAAGATGCTGAAGATCAGTTGGGTGCACGAGTGGGTTACATCGAACTGGATCTCAACAGCGGTAAGATCCTTGAGAGTTTTCGCCCCGAAGAACGTTTTCCAATGATGAGCACTTTTAAAGTTCTGCTATGTGGCGCGGTATTATCCCGTATTGACGCCGGGCAAGAGCAACTCGGTCGCCGCATACACTATTCTCAGAATGACTTGGTTGAGTACTCACCAGTCACAGAAAAGCATCTTACGGATGGCATGACAGTAAGAGAATTATGCAGTGCTGCCATAACCATGAGTGATAACACTGCGGCCAACTTACTTCTGACAACGATCGGAGGACCGAAGGAGCTAACCGCTTTTTTGCACAACATGGGGGATCATGTAACTCGCCTTGATCGTTGGGAACCGGAGCTGAATGAAGCCATACCAAACGACGAGCGTGACACCACGATGCCTGTAGCAATGGCAACAACGTTGCGCAAACTATTAACTGGCGAACTACTTACTCTAGCTTCCCGGCAACAATTAATAGACTGGATGGAGGCGGATAAAGTTGCAGGACCACTTCTGCGCTCGGCCCTTCCGGCTGGCTGGTTTATTGCTGATAAATCTGGAGCCGGTGAGCGTGGAAGCCGCGGTATCATTGCAGCACTGGGGCCAGATGGTAAGCCCTCCCGTATCGTAGTTATCTACACGACGGGGAGTCAGGCAACTATGGATGAACGAAATAGACAGATCGCTGAGATAGGTGCCTCACTGATTAAGCATTGGTAA",
        "restriction_list": [],
        "optimize": True,
        "transcript_GC": 58,
        "poly_len": 7,
    }

    project = vb.vector_create_on_dict(metadata, input_dict, show_plot=False)

    assert project is not None


def test_vector_denovo_mrna():
    metadata = vb.load_metadata(
        linkers=False,
        loops=False,
        regulators=False,
        fluorescent_tag=False,
        promoters=False,
        polya=False,
        marker=False,
        utr5=False,
        utr3=False,
    )

    input_dict = {
        "project_name": "test_mRNA",
        "species": "human",
        "sequence": "ATGTTAACTAGTGGACTTGTAGTAAGCAACATGTTCTCCTATCATCTCGCAGCCTTGGGACTCATGCCGTCATTCCAGATGGAAGGGCGAGGTCGAGTTAATCAGCTAGGAGGTGTTTTCATTAATGGACGGCCACTGCCCAACCATATACGACTGAAGATTGTCGAGCTAGCGGCCCAGGGCGTCCGTCCGTGCGTCATCAGTAGACAGCTGCGGGTGTCACATGGCTGTGTCAGTAAAATACTCCAACGATATCAAGAAACCGGAAGTATCCGACCTGGGGTTATTGGCGGAAGTAAACCAAGGGTCGCAACTCCGGAAGTTGAGAAAAAGATAGAACAATACAAAAAAGATAATCCGGGAATTTTCAGTTGGGAGATTCGGGATCGGCTGCTGAAGGAGGGGATTTGTGACCGCAGCACCGTGCCAAGTGTGAGCTCCATCAGTCGAGTATTACGGAGCAGGTTCCAGAAATGTGATTCTGATGACAATGACAATGACAATGACAATGAGGACGACGATGGCGATGACGGCAGTAACAGTAGTGTGGCAGACAGGTCTGTTAACTTCTCTGTCAGCGGTCTGCTGTCCGACAATAAAAGCGACAAAAGCGACAACGATTCCGATTGTGAATCAGAGCCGGGGCTATCTGTAAAACGGAAGCAACGCCGCAGTCGAACTACTTTCACCGCGGAGCAGTTGGAGGAACTGGAAAGAGCCTTTGAACGAACTCACTATCCGGATATATATACGCGAGAGGAATTAGCACAAAGAACAAAGCTAACCGAGGCAAGAGTCCAAGTATGGTTTAGTAACCGAAGAGCGAGATGGCGGAAACAGATGGGTAGCAATCAGCTGACAGCCTTGAACAGTATATTACAAGTGCCACAGGGTATGGGAACGCCCTCTTATATGCTGCACGAGCCTGGGTATCCACTCTCACATAATGCAGACAATCTTTGGCATAGATCGTCTATGGCCCAGTCATTACAGTCATTTGGTCAGACAATAAAACCAGAGAATTCCTACGCCGGTCTTATGGAAAACTATTTATCTCATTCATCACAGCTTCATGGTCTTCCTACACATAGTTCATCCGATCCCCTCTCATCCACTTGGTCATCTCCCGTGTCCACTTCCGTTCCTGCGCTAGGATACACGCCATCTAGTGGCCATTACCATCATTACTCTGATGTCACCAAAAGTACTCTTCATTCATATAACGCTCATATTCCTTCAGTCACAAACATGGAGAGATGTTCAGTTGATGACAGTTTGGTTGCTTTACGTATGAAGTCACGTGAGCATTCCGCCGCTCTCAGTTTGATGCAGGTGGCAGACAACAAAATGGCTACCTCATTTTGA",
        "sequence_name": "SMN1",
        "restriction_list": ["RsaI", "MnlI", "AciI", "AluI", "BmrI"],
        "optimize": True,
        "transcript_GC": 58,
        "poly_len": 7,
    }

    project = vb.create_sequence_from_dict(metadata, input_dict, show_plot=False)

    assert project is not None


def test_vector_denovo_rnai():
    metadata = vb.load_metadata(
        linkers=False,
        loops=False,
        regulators=False,
        fluorescent_tag=False,
        promoters=False,
        polya=False,
        marker=False,
        utr5=False,
        utr3=False,
    )

    input_dict = {
        "project_name": "test_shRNA",
        "species": "human",
        "rnai_type": "sh",
        "rnai_sequence": "",
        "rnai_length": 20,
        "overhang_3_prime": "UU",
        "rnai_gene_name": "KIT",
        "loop_sequence": "TAGTGAAGCCACAGATGTAC",
    }

    project = vb.create_sequence_from_dict(metadata, input_dict, show_plot=False)

    assert project is not None
