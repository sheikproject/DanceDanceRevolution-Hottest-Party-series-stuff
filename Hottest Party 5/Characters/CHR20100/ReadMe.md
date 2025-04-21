This is Emi's 3D model.

## How this .bin works:

Offset	|	Length	|	Description	|
-----	|	-----	|	-----	|
0x00	|	0x06	|	Header	|
0x08	|	0x04	|	Number of files in the .bin	|
0x10	|	0x04	|	Location of the first file (in decimal)	|
0x14	|	0x04	|	Total size of the first file	|
0x18	|	0x04	|	Location of the second file (in decimal)	|
0x1C	|	0x04	|	Total size of the second file	|
