HR stands for Human Readable
I don't know if it's really appropriate ...

Both files from the pathways of Saccharomyces Cerevisiae found on KEGG:
 - Glycolysis
 - Pentose Phosphate

Reversible reactions are inputed two times, ex:
A <-> B
reaction(A, gene, B)
reaction(B, gene, A)

When more that one gene is involved in one reaction, same behavior ! ex:
A (G1, G2)-> B
reaction(A, G1, B)
reaction(A, G2, B)
/!\ BUT if you are in the [default] reaction mode you only have:
A (rn:id)-> B
reaction(A, rn:id, B)

When more that one substract (or more that one product) are involved you get:
reaction(complex(A, B), rn:id, complex(C, D))
