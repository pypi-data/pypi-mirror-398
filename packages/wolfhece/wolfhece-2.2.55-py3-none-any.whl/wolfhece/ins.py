#Code INS des communes belges
from numpy import sort
from typing import Literal
from .PyTranslate import _

INS_2018="""01000	ROYAUME
04000	RÉGION DE BRUXELLES-CAPITALE
21000	Arrondissement de Bruxelles-Capitale
21001	Anderlecht
21002	Auderghem
21003	Berchem-Sainte-Agathe
21004	Bruxelles
21005	Etterbeek
21006	Evere
21007	Forest
21008	Ganshoren
21009	Ixelles
21010	Jette
21011	Koekelberg
21012	Molenbeek-Saint-Jean
21013	Saint-Gilles
21014	Saint-Josse-ten-Noode
21015	Schaerbeek
21016	Uccle
21017	Watermael-Boitsfort
21018	Woluwe-Saint-Lambert
21019	Woluwe-Saint-Pierre
02000	RÉGION FLAMANDE
10000	Province d'Anvers
11000	Arrondissement d'Anvers
11001	Aartselaar
11002	Anvers
11004	Boechout
11005	Boom
11007	Borsbeek
11008	Brasschaat
11009	Brecht
11013	Edegem
11016	Essen
11018	Hemiksem
11021	Hove
11022	Kalmthout
11023	Kapellen
11024	Kontich
11025	Lint
11057	Malle
11029	Mortsel
11030	Niel
11035	Ranst
11037	Rumst
11038	Schelle
11039	Schilde
11040	Schoten
11044	Stabroek
11050	Wijnegem
11052	Wommelgem
11053	Wuustwezel
11054	Zandhoven
11055	Zoersel
11056	Zwijndrecht
12000	Arrondissement de Malines
12002	Berlaar
12005	Bonheiden
12007	Bornem
12009	Duffel
12014	Heist-op-den-Berg
12021	Lierre
12025	Malines
12026	Nijlen
12029	Putte
12030	Puurs
12034	Sint-Amands
12035	Sint-Katelijne-Waver
12040	Willebroek
13000	Arrondissement de Turnhout
13001	Arendonk
13002	Baerle-Duc
13003	Balen
13004	Beerse
13006	Dessel
13008	Geel
13010	Grobbendonk
13011	Herentals
13012	Herenthout
13013	Herselt
13014	Hoogstraten
13016	Hulshout
13017	Kasterlee
13053	Laakdal
13019	Lille
13021	Meerhout
13023	Merksplas
13025	Mol
13029	Olen
13031	Oud-Turnhout
13035	Ravels
13036	Retie
13037	Rijkevorsel
13040	Turnhout
13044	Vorselaar
13046	Vosselaar
13049	Westerlo
20001	Province du Brabant Flamand
23000	Arrondissement de Hal-Vilvorde
23105	Affligem
23002	Asse
23003	Beersel
23009	Biévène
23016	Dilbeek
23098	Drogenbos
23023	Gammerages
23024	Gooik
23025	Grimbergen
23027	Hal
23032	Herne
23033	Hoeilaart
23038	Kampenhout
23039	Kapelle-op-den-Bos
23099	Kraainem
23104	Lennik
23044	Liedekerke
23100	Linkebeek
23045	Londerzeel
23047	Machelen
23050	Meise
23052	Merchtem
23060	Opwijk
23062	Overijse
23064	Pepingen
23101	Rhode-Saint-Genèse
23097	Roosdaal
23077	Sint-Pieters-Leeuw
23081	Steenokkerzeel
23086	Ternat
23088	Vilvorde
23102	Wemmel
23103	Wezembeek-Oppem
23094	Zaventem
23096	Zemst
24000	Arrondissement de Louvain
24001	Aarschot
24007	Begijnendijk
24008	Bekkevoort
24009	Bertem
24011	Bierbeek
24014	Boortmeerbeek
24016	Boutersem
24020	Diest
24028	Geetbets
24137	Glabbeek
24033	Haacht
24038	Herent
24041	Hoegaarden
24043	Holsbeek
24045	Huldenberg
24048	Keerbergen
24054	Kortenaken
24055	Kortenberg
24059	Landen
24130	Léau
24133	Linter
24062	Louvain
24066	Lubbeek
24134	Montaigu-Zichem
24086	Oud-Heverlee
24094	Rotselaar
24104	Tervuren
24135	Tielt-Winge
24107	Tirlemont
24109	Tremelo
30000	Province de Flandre Occidentale
31000	Arrondissement de Bruges
31003	Beernem
31004	Blankenberge
31005	Bruges
31006	Damme
31012	Jabbeke
31043	Knokke-Heist
31022	Oostkamp
31033	Torhout
31040	Zedelgem
31042	Zuienkerke
34000	Arrondissement de Courtrai
34002	Anzegem
34003	Avelgem
34022	Courtrai
34009	Deerlijk
34043	Espierres-Helchin
34013	Harelbeke
34023	Kuurne
34025	Lendelede
34027	Menin
34040	Waregem
34041	Wevelgem
34042	Zwevegem
32000	Arrondissement de Dixmude
32003	Dixmude
32006	Houthulst
32010	Koekelare
32011	Kortemark
32030	Lo-Reninge
38000	Arrondissement de Furnes
38002	Alveringem
38025	Furnes
38014	Koksijde
38008	La Panne
38016	Nieuport
35000	Arrondissement d'Ostende
35002	Bredene
35029	De Haan
35005	Gistel
35006	Ichtegem
35011	Middelkerke
35013	Ostende
35014	Oudenburg
36000	Arrondissement de Roulers
36006	Hooglede
36007	Ingelmunster
36008	Izegem
36010	Ledegem
36011	Lichtervelde
36012	Moorslede
36015	Roulers
36019	Staden
37000	Arrondissement de Tielt
37020	Ardooie
37002	Dentergem
37007	Meulebeke
37010	Oostrozebeke
37011	Pittem
37012	Ruiselede
37015	Tielt
37017	Wielsbeke
37018	Wingene
33000	Arrondissement d'Ypres
33039	Heuvelland
33040	Langemark-Poelkapelle
33016	Messines
33021	Poperinge
33041	Vleteren
33029	Wervik
33011	Ypres
33037	Zonnebeke
40000	Province de Flandre Orientale
41000	Arrondissement d'Alost
41002	Alost
41011	Denderleeuw
41082	Erpe-Mere
41018	Grammont
41024	Haaltert
41027	Herzele
41034	Lede
41048	Ninove
41063	Sint-Lievens-Houtem
41081	Zottegem
45000	Arrondissement d'Audenarde
45035	Audenarde
45059	Brakel
45062	Horebeke
45060	Kluisbergen
45017	Kruishoutem
45063	Lierde
45064	Maarkedal
45041	Renaix
45061	Wortegem-Petegem
45057	Zingem
45065	Zwalm
43000	Arrondissement d'Eeklo
43002	Assenede
43005	Eeklo
43007	Kaprijke
43010	Maldegem
43014	Sint-Laureins
43018	Zelzate
44000	Arrondissement de Gand
44001	Aalter
44012	De Pinte
44011	Deinze
44013	Destelbergen
44019	Evergem
44021	Gand
44020	Gavere
44029	Knesselare
44034	Lochristi
44036	Lovendegem
44040	Melle
44043	Merelbeke
44045	Moerbeke
44048	Nazareth
44049	Nevele
44052	Oosterzele
44064	Sint-Martens-Latem
44072	Waarschoot
44073	Wachtebeke
44080	Zomergem
44081	Zulte
46000	Arrondissement de Saint-Nicolas
46003	Beveren
46013	Kruibeke
46014	Lokeren
46021	Saint-Nicolas
46020	Sint-Gillis-Waas
46024	Stekene
46025	Tamise
42000	Arrondissement de Termonde
42003	Berlare
42004	Buggenhout
42008	Hamme
42010	Laarne
42011	Lebbeke
42006	Termonde
42023	Waasmunster
42025	Wetteren
42026	Wichelen
42028	Zele
70000	Province du Limbourg
71000	Arrondissement de Hasselt
71002	As
71004	Beringen
71034	Bourg-Léopold
71011	Diepenbeek
71016	Genk
71017	Gingelom
71020	Halen
71069	Ham
71022	Hasselt
71024	Herck-la-Ville
71070	Heusden-Zolder
71037	Lummen
71045	Nieuwerkerken
71047	Opglabbeek
71053	Saint-Trond
71057	Tessenderlo
71066	Zonhoven
71067	Zutendaal
72000	Arrondissement de Maaseik
72003	Bocholt
72004	Bree
72041	Dilsen-Stokkem
72037	Hamont-Achel
72038	Hechtel-Eksel
72039	Houthalen-Helchteren
72018	Kinrooi
72020	Lommel
72021	Maaseik
72040	Meeuwen-Gruitrode
72025	Neerpelt
72029	Overpelt
72030	Peer
73000	Arrondissement de Tongres
73001	Alken
73006	Bilzen
73109	Fourons
73022	Heers
73028	Herstappe
73032	Hoeselt
73040	Kortessem
73042	Lanaken
73009	Looz
73107	Maasmechelen
73066	Riemst
73083	Tongres
73098	Wellen
03000	RÉGION WALLONNE
20002	Province du Brabant Wallon
25000	Arrondissement de Nivelles
25005	Beauvechain
25014	Braine-l'Alleud
25015	Braine-le-Château
25117	Chastre
25018	Chaumont-Gistoux
25023	Court-Saint-Etienne
25031	Genappe
25037	Grez-Doiceau
25118	Hélécine
25043	Incourt
25044	Ittre
25048	Jodoigne
25050	La Hulpe
25119	Lasne
25068	Mont-Saint-Guibert
25072	Nivelles
25120	Orp-Jauche
25121	Ottignies-Louvain-la-Neuve
25084	Perwez
25122	Ramillies
25123	Rebecq
25091	Rixensart
25105	Tubize
25107	Villers-la-Ville
25124	Walhain
25110	Waterloo
25112	Wavre
50000	Province du Hainaut
51000	Arrondissement d'Ath
51004	Ath
51008	Beloeil
51009	Bernissart
51012	Brugelette
51014	Chièvres
51017	Ellezelles
51019	Flobecq
51065	Frasnes-lez-Anvaing
52000	Arrondissement de Charleroi
52074	Aiseau-Presles
52010	Chapelle-lez-Herlaimont
52011	Charleroi
52012	Châtelet
52015	Courcelles
52018	Farciennes
52021	Fleurus
52022	Fontaine-l'Evêque
52025	Gerpinnes
52075	Les Bons Villers
52043	Manage
52048	Montigny-le-Tilleul
52055	Pont-à-Celles
52063	Seneffe
53000	Arrondissement de Mons
53014	Boussu
53082	Colfontaine
53020	Dour
53028	Frameries
53039	Hensies
53083	Honnelles
53044	Jurbise
53046	Lens
53053	Mons
53065	Quaregnon
53084	Quévy
53068	Quiévrain
53070	Saint-Ghislain
54000	Arrondissement de Mouscron
54010	Comines-Warneton
54007	Mouscron
55000	Arrondissement de Soignies
55004	Braine-le-Comte
55050	Ecaussinnes
55010	Enghien
55022	La Louvière
55035	Le Roeulx
55023	Lessines
55039	Silly
55040	Soignies
56000	Arrondissement de Thuin
56001	Anderlues
56005	Beaumont
56011	Binche
56016	Chimay
56022	Erquelinnes
56085	Estinnes
56029	Froidchapelle
56086	Ham-sur-Heure-Nalinnes
56044	Lobbes
56049	Merbes-le-Château
56051	Momignies
56087	Morlanwelz
56088	Sivry-Rance
56078	Thuin
57000	Arrondissement de Tournai
57003	Antoing
57093	Brunehaut
57018	Celles
57027	Estaimpuis
57094	Leuze-en-Hainaut
57095	Mont-de-l'Enclus
57062	Pecq
57064	Péruwelz
57072	Rumes
57081	Tournai
60000	Province de Liège
61000	Arrondissement de Huy
61003	Amay
61079	Anthisnes
61010	Burdinne
61012	Clavier
61080	Engis
61019	Ferrières
61024	Hamoir
61028	Héron
61031	Huy
61039	Marchin
61041	Modave
61043	Nandrin
61048	Ouffet
61081	Tinlot
61063	Verlaine
61068	Villers-le-Bouillet
61072	Wanze
62000	Arrondissement de Liège
62003	Ans
62006	Awans
62009	Aywaille
62011	Bassenge
62015	Beyne-Heusay
62119	Blégny
62022	Chaudfontaine
62026	Comblain-au-Pont
62027	Dalhem
62032	Esneux
62120	Flémalle
62038	Fléron
62118	Grâce-Hollogne
62051	Herstal
62060	Juprelle
62063	Liège
62121	Neupré
62079	Oupeye
62093	Saint-Nicolas
62096	Seraing
62099	Soumagne
62100	Sprimont
62122	Trooz
62108	Visé
63000	Arrondissement de Verviers
63001	Amblève
63003	Aubel
63004	Baelen
63012	Bullange
63087	Burg-Reuland
63013	Butgenbach
63020	Dison
63023	Eupen
63035	Herve
63038	Jalhay
63040	La Calamine
63045	Lierneux
63046	Limbourg
63048	Lontzen
63049	Malmedy
63057	Olne
63058	Pepinster
63088	Plombières
63061	Raeren
63067	Saint-Vith
63072	Spa
63073	Stavelot
63075	Stoumont
63076	Theux
63089	Thimister-Clermont
63086	Trois-Ponts
63079	Verviers
63080	Waimes
63084	Welkenraedt
64000	Arrondissement de Waremme
64008	Berloz
64015	Braives
64021	Crisnée
64023	Donceel
64076	Faimes
64025	Fexhe-le-Haut-Clocher
64029	Geer
64034	Hannut
64047	Lincent
64056	Oreye
64063	Remicourt
64065	Saint-Georges-sur-Meuse
64074	Waremme
64075	Wasseiges
80000	Province du Luxembourg
81000	Arrondissement d'Arlon
81001	Arlon
81003	Attert
81004	Aubange
81013	Martelange
81015	Messancy
82000	Arrondissement de Bastogne
82003	Bastogne
82005	Bertogne
82009	Fauvillers
82037	Gouvy
82014	Houffalize
82038	Sainte-Ode
82036	Vaux-sur-Sûre
82032	Vielsalm
83000	Arrondissement de Marche-en-Famenne
83012	Durbuy
83013	Erezée
83028	Hotton
83031	La Roche-en-Ardenne
83055	Manhay
83034	Marche-en-Famenne
83040	Nassogne
83044	Rendeux
83049	Tenneville
84000	Arrondissement de Neufchâteau
84009	Bertrix
84010	Bouillon
84016	Daverdisse
84029	Herbeumont
84033	Léglise
84035	Libin
84077	Libramont-Chevigny
84043	Neufchâteau
84050	Paliseul
84059	Saint-Hubert
84068	Tellin
84075	Wellin
85000	Arrondissement de Virton
85007	Chiny
85009	Etalle
85011	Florenville
85046	Habay
85024	Meix-devant-Virton
85026	Musson
85047	Rouvroy
85034	Saint-Léger
85039	Tintigny
85045	Virton
90000	Province de Namur
91000	Arrondissement de Dinant
91005	Anhée
91013	Beauraing
91015	Bièvre
91030	Ciney
91034	Dinant
91054	Gedinne
91059	Hamois
91142	Hastière
91064	Havelange
91072	Houyet
91103	Onhaye
91114	Rochefort
91120	Somme-Leuze
91143	Vresse-sur-Semois
91141	Yvoir
92000	Arrondissement de Namur
92003	Andenne
92006	Assesse
92035	Eghezée
92138	Fernelmont
92045	Floreffe
92048	Fosses-la-Ville
92142	Gembloux
92054	Gesves
92140	Jemeppe-sur-Sambre
92141	La Bruyère
92087	Mettet
92094	Namur
92097	Ohey
92101	Profondeville
92137	Sambreville
92114	Sombreffe
93000	Arrondissement de Philippeville
93010	Cerfontaine
93014	Couvin
93018	Doische
93022	Florennes
93056	Philippeville
93090	Viroinval
93088	Walcourt"""

INS_2019 = """01000	ROYAUME
04000	RÉGION DE BRUXELLES-CAPITALE
21000	Arrondissement de Bruxelles-Capitale
21001	Anderlecht
21002	Auderghem
21003	Berchem-Sainte-Agathe
21004	Bruxelles
21005	Etterbeek
21006	Evere
21007	Forest
21008	Ganshoren
21009	Ixelles
21010	Jette
21011	Koekelberg
21012	Molenbeek-Saint-Jean
21013	Saint-Gilles
21014	Saint-Josse-ten-Noode
21015	Schaerbeek
21016	Uccle
21017	Watermael-Boitsfort
21018	Woluwe-Saint-Lambert
21019	Woluwe-Saint-Pierre
02000	RÉGION FLAMANDE
10000	Province d'Anvers
11000	Arrondissement d'Anvers
11001	Aartselaar
11002	Anvers
11004	Boechout
11005	Boom
11007	Borsbeek
11008	Brasschaat
11009	Brecht
11013	Edegem
11016	Essen
11018	Hemiksem
11021	Hove
11022	Kalmthout
11023	Kapellen
11024	Kontich
11025	Lint
11057	Malle
11029	Mortsel
11030	Niel
11035	Ranst
11037	Rumst
11038	Schelle
11039	Schilde
11040	Schoten
11044	Stabroek
11050	Wijnegem
11052	Wommelgem
11053	Wuustwezel
11054	Zandhoven
11055	Zoersel
11056	Zwijndrecht
12000	Arrondissement de Malines
12002	Berlaar
12005	Bonheiden
12007	Bornem
12009	Duffel
12014	Heist-op-den-Berg
12021	Lierre
12025	Malines
12026	Nijlen
12029	Putte
12041	Puurs-Sint-Amands
12035	Sint-Katelijne-Waver
12040	Willebroek
13000	Arrondissement de Turnhout
13001	Arendonk
13002	Baerle-Duc
13003	Balen
13004	Beerse
13006	Dessel
13008	Geel
13010	Grobbendonk
13011	Herentals
13012	Herenthout
13013	Herselt
13014	Hoogstraten
13016	Hulshout
13017	Kasterlee
13053	Laakdal
13019	Lille
13021	Meerhout
13023	Merksplas
13025	Mol
13029	Olen
13031	Oud-Turnhout
13035	Ravels
13036	Retie
13037	Rijkevorsel
13040	Turnhout
13044	Vorselaar
13046	Vosselaar
13049	Westerlo
20001	Province du Brabant Flamand
23000	Arrondissement de Hal-Vilvorde
23105	Affligem
23002	Asse
23003	Beersel
23009	Biévène
23016	Dilbeek
23098	Drogenbos
23023	Gammerages
23024	Gooik
23025	Grimbergen
23027	Hal
23032	Herne
23033	Hoeilaart
23038	Kampenhout
23039	Kapelle-op-den-Bos
23099	Kraainem
23104	Lennik
23044	Liedekerke
23100	Linkebeek
23045	Londerzeel
23047	Machelen
23050	Meise
23052	Merchtem
23060	Opwijk
23062	Overijse
23064	Pepingen
23101	Rhode-Saint-Genèse
23097	Roosdaal
23077	Sint-Pieters-Leeuw
23081	Steenokkerzeel
23086	Ternat
23088	Vilvorde
23102	Wemmel
23103	Wezembeek-Oppem
23094	Zaventem
23096	Zemst
24000	Arrondissement de Louvain
24001	Aarschot
24007	Begijnendijk
24008	Bekkevoort
24009	Bertem
24011	Bierbeek
24014	Boortmeerbeek
24016	Boutersem
24020	Diest
24028	Geetbets
24137	Glabbeek
24033	Haacht
24038	Herent
24041	Hoegaarden
24043	Holsbeek
24045	Huldenberg
24048	Keerbergen
24054	Kortenaken
24055	Kortenberg
24059	Landen
24130	Léau
24133	Linter
24062	Louvain
24066	Lubbeek
24134	Montaigu-Zichem
24086	Oud-Heverlee
24094	Rotselaar
24104	Tervuren
24135	Tielt-Winge
24107	Tirlemont
24109	Tremelo
30000	Province de Flandre Occidentale
31000	Arrondissement de Bruges
31003	Beernem
31004	Blankenberge
31005	Bruges
31006	Damme
31012	Jabbeke
31043	Knokke-Heist
31022	Oostkamp
31033	Torhout
31040	Zedelgem
31042	Zuienkerke
34000	Arrondissement de Courtrai
34002	Anzegem
34003	Avelgem
34022	Courtrai
34009	Deerlijk
34043	Espierres-Helchin
34013	Harelbeke
34023	Kuurne
34025	Lendelede
34027	Menin
34040	Waregem
34041	Wevelgem
34042	Zwevegem
32000	Arrondissement de Dixmude
32003	Dixmude
32006	Houthulst
32010	Koekelare
32011	Kortemark
32030	Lo-Reninge
38000	Arrondissement de Furnes
38002	Alveringem
38025	Furnes
38014	Koksijde
38008	La Panne
38016	Nieuport
35000	Arrondissement d'Ostende
35002	Bredene
35029	De Haan
35005	Gistel
35006	Ichtegem
35011	Middelkerke
35013	Ostende
35014	Oudenburg
36000	Arrondissement de Roulers
36006	Hooglede
36007	Ingelmunster
36008	Izegem
36010	Ledegem
36011	Lichtervelde
36012	Moorslede
36015	Roulers
36019	Staden
37000	Arrondissement de Tielt
37020	Ardooie
37002	Dentergem
37007	Meulebeke
37010	Oostrozebeke
37011	Pittem
37012	Ruiselede
37015	Tielt
37017	Wielsbeke
37018	Wingene
33000	Arrondissement d'Ypres
33039	Heuvelland
33040	Langemark-Poelkapelle
33016	Messines
33021	Poperinge
33041	Vleteren
33029	Wervik
33011	Ypres
33037	Zonnebeke
40000	Province de Flandre Orientale
41000	Arrondissement d'Alost
41002	Alost
41011	Denderleeuw
41082	Erpe-Mere
41018	Grammont
41024	Haaltert
41027	Herzele
41034	Lede
41048	Ninove
41063	Sint-Lievens-Houtem
41081	Zottegem
45000	Arrondissement d'Audenarde
45035	Audenarde
45059	Brakel
45062	Horebeke
45060	Kluisbergen
45068	Kruisem
45063	Lierde
45064	Maarkedal
45041	Renaix
45061	Wortegem-Petegem
45065	Zwalm
43000	Arrondissement d'Eeklo
43002	Assenede
43005	Eeklo
43007	Kaprijke
43010	Maldegem
43014	Sint-Laureins
43018	Zelzate
44000	Arrondissement de Gand
44084	Aalter
44012	De Pinte
44083	Deinze
44013	Destelbergen
44019	Evergem
44021	Gand
44020	Gavere
44085	Lievegem
44034	Lochristi
44040	Melle
44043	Merelbeke
44045	Moerbeke
44048	Nazareth
44052	Oosterzele
44064	Sint-Martens-Latem
44073	Wachtebeke
44081	Zulte
46000	Arrondissement de Saint-Nicolas
46003	Beveren
46013	Kruibeke
46014	Lokeren
46021	Saint-Nicolas
46020	Sint-Gillis-Waas
46024	Stekene
46025	Tamise
42000	Arrondissement de Termonde
42003	Berlare
42004	Buggenhout
42008	Hamme
42010	Laarne
42011	Lebbeke
42006	Termonde
42023	Waasmunster
42025	Wetteren
42026	Wichelen
42028	Zele
70000	Province du Limbourg
71000	Arrondissement de Hasselt
71002	As
71004	Beringen
71034	Bourg-Léopold
71011	Diepenbeek
71016	Genk
71017	Gingelom
71020	Halen
71069	Ham
71022	Hasselt
71024	Herck-la-Ville
71070	Heusden-Zolder
71037	Lummen
71045	Nieuwerkerken
71053	Saint-Trond
71057	Tessenderlo
71066	Zonhoven
71067	Zutendaal
72000	Arrondissement de Maaseik
72003	Bocholt
72004	Bree
72041	Dilsen-Stokkem
72037	Hamont-Achel
72038	Hechtel-Eksel
72039	Houthalen-Helchteren
72018	Kinrooi
72020	Lommel
72021	Maaseik
72042	Oudsbergen
72030	Peer
72043	Pelt
73000	Arrondissement de Tongres
73001	Alken
73006	Bilzen
73109	Fourons
73022	Heers
73028	Herstappe
73032	Hoeselt
73040	Kortessem
73042	Lanaken
73009	Looz
73107	Maasmechelen
73066	Riemst
73083	Tongres
73098	Wellen
03000	RÉGION WALLONNE
20002	Province du Brabant Wallon
25000	Arrondissement de Nivelles
25005	Beauvechain
25014	Braine-l'Alleud
25015	Braine-le-Château
25117	Chastre
25018	Chaumont-Gistoux
25023	Court-Saint-Etienne
25031	Genappe
25037	Grez-Doiceau
25118	Hélécine
25043	Incourt
25044	Ittre
25048	Jodoigne
25050	La Hulpe
25119	Lasne
25068	Mont-Saint-Guibert
25072	Nivelles
25120	Orp-Jauche
25121	Ottignies-Louvain-la-Neuve
25084	Perwez
25122	Ramillies
25123	Rebecq
25091	Rixensart
25105	Tubize
25107	Villers-la-Ville
25124	Walhain
25110	Waterloo
25112	Wavre
50000	Province du Hainaut
51000	Arrondissement d'Ath
51004	Ath
51008	Beloeil
51009	Bernissart
51012	Brugelette
51014	Chièvres
51017	Ellezelles
51067	Enghien
51019	Flobecq
51065	Frasnes-lez-Anvaing
51069	Lessines
51068	Silly
52000	Arrondissement de Charleroi
52074	Aiseau-Presles
52010	Chapelle-lez-Herlaimont
52011	Charleroi
52012	Châtelet
52015	Courcelles
52018	Farciennes
52021	Fleurus
52022	Fontaine-l'Evêque
52025	Gerpinnes
52075	Les Bons Villers
52048	Montigny-le-Tilleul
52055	Pont-à-Celles
53000	Arrondissement de Mons
53014	Boussu
53082	Colfontaine
53020	Dour
53028	Frameries
53039	Hensies
53083	Honnelles
53044	Jurbise
53046	Lens
53053	Mons
53065	Quaregnon
53084	Quévy
53068	Quiévrain
53070	Saint-Ghislain
55000	Arrondissement de Soignies
55004	Braine-le-Comte
55050	Ecaussinnes
55035	Le Roeulx
55086	Manage
55085	Seneffe
55040	Soignies
56000	Arrondissement de Thuin
56001	Anderlues
56005	Beaumont
56016	Chimay
56022	Erquelinnes
56029	Froidchapelle
56086	Ham-sur-Heure-Nalinnes
56044	Lobbes
56049	Merbes-le-Château
56051	Momignies
56088	Sivry-Rance
56078	Thuin
57000	Arrondissement de Tournai-Mouscron
57003	Antoing
57093	Brunehaut
57018	Celles
57097	Comines-Warneton
57027	Estaimpuis
57094	Leuze-en-Hainaut
57095	Mont-de-l'Enclus
57096	Mouscron
57062	Pecq
57064	Péruwelz
57072	Rumes
57081	Tournai
58000	Arrondissement de La Louvière
58001	La Louvière
58002	Binche
58003	Estinnes
58004	Morlanwelz
60000	Province de Liège
61000	Arrondissement de Huy
61003	Amay
61079	Anthisnes
61010	Burdinne
61012	Clavier
61080	Engis
61019	Ferrières
61024	Hamoir
61028	Héron
61031	Huy
61039	Marchin
61041	Modave
61043	Nandrin
61048	Ouffet
61081	Tinlot
61063	Verlaine
61068	Villers-le-Bouillet
61072	Wanze
62000	Arrondissement de Liège
62003	Ans
62006	Awans
62009	Aywaille
62011	Bassenge
62015	Beyne-Heusay
62119	Blégny
62022	Chaudfontaine
62026	Comblain-au-Pont
62027	Dalhem
62032	Esneux
62120	Flémalle
62038	Fléron
62118	Grâce-Hollogne
62051	Herstal
62060	Juprelle
62063	Liège
62121	Neupré
62079	Oupeye
62093	Saint-Nicolas
62096	Seraing
62099	Soumagne
62100	Sprimont
62122	Trooz
62108	Visé
63000	Arrondissement de Verviers
63001	Amblève
63003	Aubel
63004	Baelen
63012	Bullange
63087	Burg-Reuland
63013	Butgenbach
63020	Dison
63023	Eupen
63035	Herve
63038	Jalhay
63040	La Calamine
63045	Lierneux
63046	Limbourg
63048	Lontzen
63049	Malmedy
63057	Olne
63058	Pepinster
63088	Plombières
63061	Raeren
63067	Saint-Vith
63072	Spa
63073	Stavelot
63075	Stoumont
63076	Theux
63089	Thimister-Clermont
63086	Trois-Ponts
63079	Verviers
63080	Waimes
63084	Welkenraedt
64000	Arrondissement de Waremme
64008	Berloz
64015	Braives
64021	Crisnée
64023	Donceel
64076	Faimes
64025	Fexhe-le-Haut-Clocher
64029	Geer
64034	Hannut
64047	Lincent
64056	Oreye
64063	Remicourt
64065	Saint-Georges-sur-Meuse
64074	Waremme
64075	Wasseiges
80000	Province du Luxembourg
81000	Arrondissement d'Arlon
81001	Arlon
81003	Attert
81004	Aubange
81013	Martelange
81015	Messancy
82000	Arrondissement de Bastogne
82003	Bastogne
82005	Bertogne
82009	Fauvillers
82037	Gouvy
82014	Houffalize
82038	Sainte-Ode
82036	Vaux-sur-Sûre
82032	Vielsalm
83000	Arrondissement de Marche-en-Famenne
83012	Durbuy
83013	Erezée
83028	Hotton
83031	La Roche-en-Ardenne
83055	Manhay
83034	Marche-en-Famenne
83040	Nassogne
83044	Rendeux
83049	Tenneville
84000	Arrondissement de Neufchâteau
84009	Bertrix
84010	Bouillon
84016	Daverdisse
84029	Herbeumont
84033	Léglise
84035	Libin
84077	Libramont-Chevigny
84043	Neufchâteau
84050	Paliseul
84059	Saint-Hubert
84068	Tellin
84075	Wellin
85000	Arrondissement de Virton
85007	Chiny
85009	Etalle
85011	Florenville
85046	Habay
85024	Meix-devant-Virton
85026	Musson
85047	Rouvroy
85034	Saint-Léger
85039	Tintigny
85045	Virton
90000	Province de Namur
91000	Arrondissement de Dinant
91005	Anhée
91013	Beauraing
91015	Bièvre
91030	Ciney
91034	Dinant
91054	Gedinne
91059	Hamois
91142	Hastière
91064	Havelange
91072	Houyet
91103	Onhaye
91114	Rochefort
91120	Somme-Leuze
91143	Vresse-sur-Semois
91141	Yvoir
92000	Arrondissement de Namur
92003	Andenne
92006	Assesse
92035	Eghezée
92138	Fernelmont
92045	Floreffe
92048	Fosses-la-Ville
92142	Gembloux
92054	Gesves
92140	Jemeppe-sur-Sambre
92141	La Bruyère
92087	Mettet
92094	Namur
92097	Ohey
92101	Profondeville
92137	Sambreville
92114	Sombreffe
93000	Arrondissement de Philippeville
93010	Cerfontaine
93014	Couvin
93018	Doische
93022	Florennes
93056	Philippeville
93090	Viroinval
93088	Walcourt
"""

INS_2025 = """01000	ROYAUME
04000	RÉGION DE BRUXELLES-CAPITALE
21000	Arrondissement de Bruxelles-Capitale
21001	Anderlecht
21002	Auderghem
21003	Berchem-Sainte-Agathe
21004	Bruxelles
21005	Etterbeek
21006	Evere
21007	Forest
21008	Ganshoren
21009	Ixelles
21010	Jette
21011	Koekelberg
21012	Molenbeek-Saint-Jean
21013	Saint-Gilles
21014	Saint-Josse-ten-Noode
21015	Schaerbeek
21016	Uccle
21017	Watermael-Boitsfort
21018	Woluwe-Saint-Lambert
21019	Woluwe-Saint-Pierre
02000	RÉGION FLAMANDE
10000	Province d'Anvers
11000	Arrondissement d'Anvers
11001	Aartselaar
11002	Anvers
11004	Boechout
11005	Boom
11008	Brasschaat
11009	Brecht
11013	Edegem
11016	Essen
11018	Hemiksem
11021	Hove
11022	Kalmthout
11023	Kapellen
11024	Kontich
11025	Lint
11057	Malle
11029	Mortsel
11030	Niel
11035	Ranst
11037	Rumst
11038	Schelle
11039	Schilde
11040	Schoten
11044	Stabroek
11050	Wijnegem
11052	Wommelgem
11053	Wuustwezel
11054	Zandhoven
11055	Zoersel
12000	Arrondissement de Malines
12002	Berlaar
12005	Bonheiden
12007	Bornem
12009	Duffel
12014	Heist-op-den-Berg
12021	Lierre
12025	Malines
12026	Nijlen
12029	Putte
12041	Puurs-Sint-Amands
12035	Sint-Katelijne-Waver
12040	Willebroek
13000	Arrondissement de Turnhout
13001	Arendonk
13002	Baerle-Duc
13003	Balen
13004	Beerse
13006	Dessel
13008	Geel
13010	Grobbendonk
13011	Herentals
13012	Herenthout
13013	Herselt
13014	Hoogstraten
13016	Hulshout
13017	Kasterlee
13053	Laakdal
13019	Lille
13021	Meerhout
13023	Merksplas
13025	Mol
13029	Olen
13031	Oud-Turnhout
13035	Ravels
13036	Retie
13037	Rijkevorsel
13040	Turnhout
13044	Vorselaar
13046	Vosselaar
13049	Westerlo
20001	Province du Brabant Flamand
23000	Arrondissement de Hal-Vilvorde
23105	Affligem
23002	Asse
23003	Beersel
23009	Biévène
23016	Dilbeek
23098	Drogenbos
23025	Grimbergen
23027	Hal
23033	Hoeilaart
23038	Kampenhout
23039	Kapelle-op-den-Bos
23099	Kraainem
23104	Lennik
23044	Liedekerke
23100	Linkebeek
23045	Londerzeel
23047	Machelen
23050	Meise
23052	Merchtem
23060	Opwijk
23062	Overijse
23106	Pajottegem
23064	Pepingen
23101	Rhode-Saint-Genèse
23097	Roosdaal
23077	Sint-Pieters-Leeuw
23081	Steenokkerzeel
23086	Ternat
23088	Vilvorde
23102	Wemmel
23103	Wezembeek-Oppem
23094	Zaventem
23096	Zemst
24000	Arrondissement de Louvain
24001	Aarschot
24007	Begijnendijk
24008	Bekkevoort
24009	Bertem
24011	Bierbeek
24014	Boortmeerbeek
24016	Boutersem
24020	Diest
24028	Geetbets
24137	Glabbeek
24033	Haacht
24038	Herent
24041	Hoegaarden
24043	Holsbeek
24045	Huldenberg
24048	Keerbergen
24054	Kortenaken
24055	Kortenberg
24059	Landen
24130	Léau
24133	Linter
24062	Louvain
24066	Lubbeek
24134	Montaigu-Zichem
24086	Oud-Heverlee
24094	Rotselaar
24104	Tervuren
24135	Tielt-Winge
24107	Tirlemont
24109	Tremelo
30000	Province de Flandre Occidentale
31000	Arrondissement de Bruges
31003	Beernem
31004	Blankenberge
31005	Bruges
31006	Damme
31012	Jabbeke
31043	Knokke-Heist
31022	Oostkamp
31033	Torhout
31040	Zedelgem
31042	Zuienkerke
34000	Arrondissement de Courtrai
34002	Anzegem
34003	Avelgem
34022	Courtrai
34009	Deerlijk
34043	Espierres-Helchin
34013	Harelbeke
34023	Kuurne
34025	Lendelede
34027	Menin
34040	Waregem
34041	Wevelgem
34042	Zwevegem
32000	Arrondissement de Dixmude
32003	Dixmude
32006	Houthulst
32010	Koekelare
32011	Kortemark
32030	Lo-Reninge
38000	Arrondissement de Furnes
38002	Alveringem
38025	Furnes
38014	Koksijde
38008	La Panne
38016	Nieuport
35000	Arrondissement d'Ostende
35002	Bredene
35029	De Haan
35005	Gistel
35006	Ichtegem
35011	Middelkerke
35013	Ostende
35014	Oudenburg
36000	Arrondissement de Roulers
36006	Hooglede
36007	Ingelmunster
36008	Izegem
36010	Ledegem
36011	Lichtervelde
36012	Moorslede
36015	Roulers
36019	Staden
37000	Arrondissement de Tielt
37020	Ardooie
37002	Dentergem
37010	Oostrozebeke
37011	Pittem
37022	Tielt
37017	Wielsbeke
37021	Wingene
33000	Arrondissement d'Ypres
33039	Heuvelland
33040	Langemark-Poelkapelle
33016	Messines
33021	Poperinge
33041	Vleteren
33029	Wervik
33011	Ypres
33037	Zonnebeke
40000	Province de Flandre Orientale
41000	Arrondissement d'Alost
41002	Alost
41011	Denderleeuw
41082	Erpe-Mere
41018	Grammont
41024	Haaltert
41027	Herzele
41034	Lede
41048	Ninove
41063	Sint-Lievens-Houtem
41081	Zottegem
45000	Arrondissement d'Audenarde
45035	Audenarde
45059	Brakel
45062	Horebeke
45060	Kluisbergen
45068	Kruisem
45063	Lierde
45064	Maarkedal
45041	Renaix
45061	Wortegem-Petegem
45065	Zwalm
43000	Arrondissement d'Eeklo
43002	Assenede
43005	Eeklo
43007	Kaprijke
43010	Maldegem
43014	Sint-Laureins
43018	Zelzate
44000	Arrondissement de Gand
44084	Aalter
44083	Deinze
44013	Destelbergen
44019	Evergem
44021	Gand
44020	Gavere
44085	Lievegem
44087	Lochristi
44088	Merelbeke-Melle
44086	Nazareth-De Pinte
44052	Oosterzele
44064	Sint-Martens-Latem
44081	Zulte
46000	Arrondissement de Saint-Nicolas
46030	Beveren-Kruibeke-Zwijndrecht
46029	Lokeren
46021	Saint-Nicolas
46020	Sint-Gillis-Waas
46024	Stekene
46025	Tamise
42000	Arrondissement de Termonde
42003	Berlare
42004	Buggenhout
42008	Hamme
42010	Laarne
42011	Lebbeke
42006	Termonde
42023	Waasmunster
42025	Wetteren
42026	Wichelen
42028	Zele
70000	Province du Limbourg
71000	Arrondissement de Hasselt
71002	As
71004	Beringen
71034	Bourg-Léopold
71011	Diepenbeek
71016	Genk
71017	Gingelom
71020	Halen
71072	Hasselt
71024	Herck-la-Ville
71070	Heusden-Zolder
71037	Lummen
71045	Nieuwerkerken
71053	Saint-Trond
71071	Tessenderlo-Ham
71066	Zonhoven
71067	Zutendaal
72000	Arrondissement de Maaseik
72003	Bocholt
72004	Bree
72041	Dilsen-Stokkem
72037	Hamont-Achel
72038	Hechtel-Eksel
72039	Houthalen-Helchteren
72018	Kinrooi
72020	Lommel
72021	Maaseik
72042	Oudsbergen
72030	Peer
72043	Pelt
73000	Arrondissement de Tongres
73001	Alken
73110	Bilzen-Hoeselt
73109	Fourons
73022	Heers
73028	Herstappe
73042	Lanaken
73107	Maasmechelen
73066	Riemst
73111	Tongeren-Borgloon
73098	Wellen
03000	RÉGION WALLONNE
20002	Province du Brabant Wallon
25000	Arrondissement de Nivelles
25005	Beauvechain
25014	Braine-l'Alleud
25015	Braine-le-Château
25117	Chastre
25018	Chaumont-Gistoux
25023	Court-Saint-Etienne
25031	Genappe
25037	Grez-Doiceau
25118	Hélécine
25043	Incourt
25044	Ittre
25048	Jodoigne
25050	La Hulpe
25119	Lasne
25068	Mont-Saint-Guibert
25072	Nivelles
25120	Orp-Jauche
25121	Ottignies-Louvain-la-Neuve
25084	Perwez
25122	Ramillies
25123	Rebecq
25091	Rixensart
25105	Tubize
25107	Villers-la-Ville
25124	Walhain
25110	Waterloo
25112	Wavre
50000	Province du Hainaut
51000	Arrondissement d'Ath
51004	Ath
51008	Beloeil
51009	Bernissart
51012	Brugelette
51014	Chièvres
51017	Ellezelles
51067	Enghien
51019	Flobecq
51065	Frasnes-lez-Anvaing
51069	Lessines
51068	Silly
52000	Arrondissement de Charleroi
52074	Aiseau-Presles
52010	Chapelle-lez-Herlaimont
52011	Charleroi
52012	Châtelet
52015	Courcelles
52018	Farciennes
52021	Fleurus
52022	Fontaine-l'Evêque
52025	Gerpinnes
52075	Les Bons Villers
52048	Montigny-le-Tilleul
52055	Pont-à-Celles
53000	Arrondissement de Mons
53014	Boussu
53082	Colfontaine
53020	Dour
53028	Frameries
53039	Hensies
53083	Honnelles
53044	Jurbise
53046	Lens
53053	Mons
53065	Quaregnon
53084	Quévy
53068	Quiévrain
53070	Saint-Ghislain
55000	Arrondissement de Soignies
55004	Braine-le-Comte
55050	Ecaussinnes
55035	Le Roeulx
55086	Manage
55085	Seneffe
55040	Soignies
56000	Arrondissement de Thuin
56001	Anderlues
56005	Beaumont
56016	Chimay
56022	Erquelinnes
56029	Froidchapelle
56086	Ham-sur-Heure-Nalinnes
56044	Lobbes
56049	Merbes-le-Château
56051	Momignies
56088	Sivry-Rance
56078	Thuin
57000	Arrondissement de Tournai-Mouscron
57003	Antoing
57093	Brunehaut
57018	Celles
57097	Comines-Warneton
57027	Estaimpuis
57094	Leuze-en-Hainaut
57095	Mont-de-l'Enclus
57096	Mouscron
57062	Pecq
57064	Péruwelz
57072	Rumes
57081	Tournai
58000	Arrondissement de La Louvière
58001	La Louvière
58002	Binche
58003	Estinnes
58004	Morlanwelz
60000	Province de Liège
61000	Arrondissement de Huy
61003	Amay
61079	Anthisnes
61010	Burdinne
61012	Clavier
61080	Engis
61019	Ferrières
61024	Hamoir
61028	Héron
61031	Huy
61039	Marchin
61041	Modave
61043	Nandrin
61048	Ouffet
61081	Tinlot
61063	Verlaine
61068	Villers-le-Bouillet
61072	Wanze
62000	Arrondissement de Liège
62003	Ans
62006	Awans
62009	Aywaille
62011	Bassenge
62015	Beyne-Heusay
62119	Blégny
62022	Chaudfontaine
62026	Comblain-au-Pont
62027	Dalhem
62032	Esneux
62120	Flémalle
62038	Fléron
62118	Grâce-Hollogne
62051	Herstal
62060	Juprelle
62063	Liège
62121	Neupré
62079	Oupeye
62093	Saint-Nicolas
62096	Seraing
62099	Soumagne
62100	Sprimont
62122	Trooz
62108	Visé
63000	Arrondissement de Verviers
63001	Amblève
63003	Aubel
63004	Baelen
63012	Bullange
63087	Burg-Reuland
63013	Butgenbach
63020	Dison
63023	Eupen
63035	Herve
63038	Jalhay
63040	La Calamine
63045	Lierneux
63046	Limbourg
63048	Lontzen
63049	Malmedy
63057	Olne
63058	Pepinster
63088	Plombières
63061	Raeren
63067	Saint-Vith
63072	Spa
63073	Stavelot
63075	Stoumont
63076	Theux
63089	Thimister-Clermont
63086	Trois-Ponts
63079	Verviers
63080	Waimes
63084	Welkenraedt
64000	Arrondissement de Waremme
64008	Berloz
64015	Braives
64021	Crisnée
64023	Donceel
64076	Faimes
64025	Fexhe-le-Haut-Clocher
64029	Geer
64034	Hannut
64047	Lincent
64056	Oreye
64063	Remicourt
64065	Saint-Georges-sur-Meuse
64074	Waremme
64075	Wasseiges
80000	Province du Luxembourg
81000	Arrondissement d'Arlon
81001	Arlon
81003	Attert
81004	Aubange
81013	Martelange
81015	Messancy
82000	Arrondissement de Bastogne
82039	Bastogne
82009	Fauvillers
82037	Gouvy
82014	Houffalize
82038	Sainte-Ode
82036	Vaux-sur-Sûre
82032	Vielsalm
83000	Arrondissement de Marche-en-Famenne
83012	Durbuy
83013	Erezée
83028	Hotton
83031	La Roche-en-Ardenne
83055	Manhay
83034	Marche-en-Famenne
83040	Nassogne
83044	Rendeux
83049	Tenneville
84000	Arrondissement de Neufchâteau
84009	Bertrix
84010	Bouillon
84016	Daverdisse
84029	Herbeumont
84033	Léglise
84035	Libin
84077	Libramont-Chevigny
84043	Neufchâteau
84050	Paliseul
84059	Saint-Hubert
84068	Tellin
84075	Wellin
85000	Arrondissement de Virton
85007	Chiny
85009	Etalle
85011	Florenville
85046	Habay
85024	Meix-devant-Virton
85026	Musson
85047	Rouvroy
85034	Saint-Léger
85039	Tintigny
85045	Virton
90000	Province de Namur
91000	Arrondissement de Dinant
91005	Anhée
91013	Beauraing
91015	Bièvre
91030	Ciney
91034	Dinant
91054	Gedinne
91059	Hamois
91142	Hastière
91064	Havelange
91072	Houyet
91103	Onhaye
91114	Rochefort
91120	Somme-Leuze
91143	Vresse-sur-Semois
91141	Yvoir
92000	Arrondissement de Namur
92003	Andenne
92006	Assesse
92035	Eghezée
92138	Fernelmont
92045	Floreffe
92048	Fosses-la-Ville
92142	Gembloux
92054	Gesves
92140	Jemeppe-sur-Sambre
92141	La Bruyère
92087	Mettet
92094	Namur
92097	Ohey
92101	Profondeville
92137	Sambreville
92114	Sombreffe
93000	Arrondissement de Philippeville
93010	Cerfontaine
93014	Couvin
93018	Doische
93022	Florennes
93056	Philippeville
93090	Viroinval
93088	Walcourt
"""
class Localities():
    """ Liste des communes de Belgique sur base du code INS et du nom """

    def __init__(self, which:Literal['2018', '2019', '2025', 2018, 2019, 2025] = 2019) -> None:
        #Création de 2 dictionnaires de recherche sur base de la chaîne issue du fichier csv de Statbel
        #https://statbel.fgov.be/sites/default/files/Over_Statbel_FR/Nomenclaturen/REFNIS_2019.csv
        self.inscode2name={}
        self.insname2code={}

        if which in ['2018', 2018]:
            INS = INS_2018
        elif which in ['2019', 2019]:
            INS = INS_2019
        elif which in ['2025', 2025]:
            INS = INS_2025

        for myins in INS.splitlines():
            mycode,myname=myins.split("\t")
            self.inscode2name[int(mycode)]=myname
            self.insname2code[myname.lower()]=int(mycode)

    def get_allcodes(self):
        return list(self.inscode2name.keys())

    def get_allnames(self):
        return list(self.insname2code.keys())

    def get_namefromINS(self,ins:int):
        """Retourne le nom sur base du code """
        if ins not in self.inscode2name:
            return None

        return self.inscode2name[ins]

    def get_INSfromname(self,name:str):
        """Retourne le code sur base du nom """

        if name.lower() not in self.insname2code:
            return None

        return self.insname2code[name.lower()]
