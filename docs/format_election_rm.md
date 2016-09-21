# Format Specificaziun Elecziuns

Sco formats da datoteca vegnan acceptadas datotecas CSV, XLS u XLSX che vegnan generadas dals programs d'elecziun "Elecziuns (SESAM)" e "Wabsti Elecziuns e votaziuns (VRSG)", u da l'applicaziun web sezza. Sche la tabella duai vegnir fatga a maun, è il format da l'applicaziun web il pli simpel.

## Cuntegn

[SESAM Maiorz](#sesam-maiorz)

[SESAM Proporz](#sesam-proporz)

[Wabsti Maiorz](#wabsti-maiorz)

[Wabsti Proporz](#wabsti-proporz)

[OneGov](#onegov)


## SESAM Maiorz

Il format d'export SESAM cuntegna directamain tut las datas necessarias. I dat ina lingia per candidata u candidat e per vischnanca.

### Colonnas

Las suandantas colonnas vegnan evaluadas e ston almain esser avant maun:

- **Anzahl Sitze** (Dumber dals sezs)
- **Wahlkreis-Nr** (Nr. dal circul electoral)
- **Anzahl Gemeinden** (Dumber da vischnancas)
- **Stimmberechtigte** (Persunas cun dretg da votar)
- **Wahlzettel** (Cedels electorals)
- **Ungültige Wahlzettel** (Cedels electorals nunvalaivels)
- **Leere Wahlzettel** (Cedels electorals vids)
- **Leere Stimmen** (Vuschs vidas)
- **Ungueltige Stimmen** (Vuschs nunvalaivlas)
- **Kandidaten-Nr** (Nr. da la candidata u dal candidat)
- **Gewaehlt** (Elegì)
- **Name** (Num)
- **Vorname** (Prenum)
- **Stimmen** (Vuschs)

### Resultats temporars

L'elecziun vala sco anc betg dumbrada ora, sch'il dumber da vischnancas dumbradas ora ch'è inditgà en `Anzahl Gemeinden` (Dumber da vischnancas) na correspunda betg al dumber total da vischnancas. Las vischnancas che n'èn anc betg dumbradas ora n'èn betg cuntegnidas en las datas.

### Project

[election_sesam_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_sesam_majorz.csv)

## SESAM Proporz

Il format d'export SESAM cuntegna directamain tut las datas necessarias. I dat ina lingia per candidata u candidat e per vischnanca.

### Colonnas

Las suandantas colonnas vegnan evaluadas e ston almain esser avant maun:

- **Anzahl Sitze** (Dumber dals sezs)
- **Wahlkreis-Nr** (Nr. dal circul electoral)
- **Stimmberechtigte** (Persunas cun dretg da votar)
- **Wahlzettel** (Cedels electorals)
- **Ungültige Wahlzettel** (Cedels electorals nunvalaivels)
- **Leere Wahlzettel** (Cedels electorals vids)
- **Leere Stimmen** (Vuschs vidas)
- **Listen-Nr** (Nr. da la glista)
- **Partei-ID** (ID da la partida)
- **Parteibezeichnung** (Num da la partida)
- **HLV-Nr** (Nr. da la colliaziun da glistas principalas)
- **ULV-Nr** (Nr. da la sutcolliaziun da glistas)
- **Anzahl Sitze Liste** (Dumber da sezs da la glista)
- **Kandidatenstimmen unveränderte Wahlzettel** (Vuschs da candidat dals cedels electorals originals, part da las vuschs da la glista)
- **Zusatzstimmen unveränderte Wahlzettel** (Vuschs supplementaras dals cedels electorals originals, part da las vuschs da la glista)
- **Kandidatenstimmen veränderte Wahlzettel** (Vuschs da candidat dals cedels electorals midads, part da las vuschs da la glista)
- **Zusatzstimmen veränderte Wahlzettel** (Vuschs supplementaras dals cedels electorals midads, part da las vuschs da la glista)
- **Kandidaten-Nr** (Nr. da la candidata u dal candidat)
- **Gewählt** (Elegì)
- **Name** (Num)
- **Vorname** (Prenum)
- **Stimmen Total aus Wahlzettel** (Total da vuschs dals cedels electorals)
- **Anzahl Gemeinden** (Dumber da vischnancas)
- **Ungueltige Stimmen** (Vuschs nunvalaivlas)

### Resultats temporars

L'elecziun vala sco anc betg dumbrada ora, sch'il dumber da vischnancas dumbradas ora ch'è inditgà en `Anzahl Gemeinden` (Dumber da vischnancas) na correspunda betg al dumber total da vischnancas. Las vischnancas che n'èn anc betg dumbradas ora n'èn betg cuntegnidas en las datas.

### Project

[election_sesam_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_sesam_proporz.csv)

## Wabsti Maiorz

Il format da datoteca premetta duas singulas tabellas: l'export da datas e la glista da las candidatas e dals candidats elegids.

### Colonnas "Export da datas"

En l'export da datas datti ina lingia per mintga vischnanca, las candidatas ed ils candidats figureschan en colonnas. Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

- **AnzMandate**
- **BFS**
- **StimmBer**
- **StimmAbgegeben**
- **StimmLeer**
- **StimmUngueltig**
- **StimmGueltig**

Sco er per mintga candidata u candidat:

- **KandID_`x`**
- **KandName_`x`**
- **KandVorname_`x`**
- **Stimmen_`x`**

Ultra da quai vegnan las vuschs vidas e nunvalaivlas er registradas sco candidatas e candidats, e quai a maun dals suandants nums da candidat:

- **KandName_`x` = 'Leere Zeilen'** (Empty votes)
- **KandName_`x` = 'Ungültige Stimmen'** (Invalid votes)

### Colonnas "Resultats da las candidatas e dals candidats"

Cunquai ch'il format da datoteca na furnescha naginas infurmaziuns davart las candidatas ed ils candidats elegids, ston quellas vegnir agiuntadas en ina segunda tabella. Mintga lingia cuntegna ina candidata u in candidat elegì cun las suandantas colonnas:

- **ID** : La ID da la candidata u dal candidat (`KandID_x`)
- **Name** : Il num da famiglia da la candidata u dal candidat
- **Vorname** : Il prenum da la candidata u dal candidat

### Resultats temporars

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sche tut l'elecziun è dumbrada ora cumplettamain. Questa infurmaziun sto vegnir furnida directamain sin il formular per l'upload da las datas.

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sch'ina singula vischnanca è dumbrada ora cumplettamain. Perquai na vegn, uscheditg che l'entira elecziun n'è betg terminada, er betg mussà il progress en Wabsti. Sch'i mancan però cumplettamain vischnancas en ils resultats, valan quellas sco anc betg dumbradas ora.

### Projects

[election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_majorz_results.csv)

[election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_majorz_candidates.csv)

## Wabsti Proporz

Il format da datoteca premetta quatter singulas tabellas: l'export da datas dals resultats, l'export da datas da las statisticas, las colliaziuns da glistas e la glista da las candidatas e dals candidats elegids.

### Colonnas "Export da datas dals resultats"

En l'export da datas datti ina lingia per candidata u candidat e per vischnanca. Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

- **Einheit_BFS**
- **Kand_Nachname**
- **Kand_Vorname**
- **Liste_KandID**
- **Liste_ID**
- **Liste_Code**
- **Kand_StimmenTotal**
- **Liste_ParteistimmenTotal**

### Colonnas "Export da datas da la statistica"

La datoteca cun las statisticas tar las singulas vischnancas duess cuntegnair las suandantas colonnas:

- **Einheit_BFS**
- **StimBerTotal**
- **WZEingegangen**
- **WZLeer**
- **WZUngueltig**
- **StmWZVeraendertLeerAmtlLeer**

### Colonnas "Colliaziuns da glistas"

La datoteca cun las colliaziuns da glistas duess cuntegnair las suandantas colonnas:

- **Liste**
- **LV**
- **LUV**

### Colonnas "Resultats da las candidatas e dals candidats"

Cunquai ch'il format da datoteca na furnescha naginas infurmaziuns davart las candidatas ed ils candidats elegids, ston quellas vegnir agiuntadas en ina segunda tabella. Mintga lingia cuntegna ina candidata u in candidat elegì cun las suandantas colonnas:

- **ID** : La ID da la candidata u dal candidat (`Liste_KandID`).
- **Name** : Il num da famiglia da la candidata u dal candidat.
- **Vorname** : Il prenum da la candidata u dal candidat.

### Resultats temporars

Il format che vegn duvrà da l'applicaziun web per l'export sa cumpona d'ina singula datoteca per elecziun. Per mintga vischnanca e candidata u candidat datti ina lingia.

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sch'ina singula vischnanca è dumbrada ora cumplettamain. Perquai na vegn, uscheditg che l'entira elecziun n'è betg terminada, er betg mussà il progress en Wabsti. Sch'i mancan però cumplettamain vischnancas en ils resultats, valan quellas sco anc betg dumbradas ora.

### Projects

[election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_results.csv)

[election_wabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_statistics.csv)

[election_wabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_list_connections.csv)

[election_wabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_candidates.csv)


## OneGov

The format, which will be used by the web application for the export, consists of a single file per election. There is a row for each municipality and candidate.

### Colonnas

Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

- **election_absolute_majority**: Maioritad absoluta da l'elecziun, mo tar elecziuns da maiorz.
- **election_counted_municipalites**: Dumber da las vischnancas ch'èn dumbradas ora. Sche `election_counted_municipalites = election_total_municipalites`, vala l'elecziun sco dumbrada ora cumplettamain.
- **election_total_municipalites**: Dumber total da vischnancas. Sch'i na po betg vegnir dada ina infurmaziun exacta davart il status da l'elecziun (damai che Wahlt è vegnì importà da Wabsti), è questa valur `0`.
- **municipality_bfs_number**: Numer UST da la vischnanca.
- **municipality_elegible_voters**: Dumber da persunas cun dretg da votar da la vischnanca.
- **municipality_received_ballots**: Dumber da cedels da votar consegnads da la vischnanca.
- **municipality_blank_ballots**: Dumber da cedels da votar vids da la vischnanca.
- **municipality_invalid_ballots**: Dumber da cedels da votar nunvalaivels da la vischnanca.
- **municipality_blank_votes**: Dumber da vuschs vidas da la vischnanca.
- **municipality_invalid_votes**: Dumber da vuschs nunvalaivlas da la vischnanca. Nulla en cas d'ina elecziun da proporz.
- **list_name**: Num da la glista da la candidata u dal candidat. Mo tar elecziuns da proporz.
- **list_id**: ID da la glista da la candidata u dal candidat. Mo tar elecziuns da proporz.
- **list_number_of_mandates**: Dumber total da mandats da la glista. Mo tar elecziuns da proporz.
- **list_votes**: Dumber total da vuschs da la glista. Mo tar elecziuns da proporz.
- **list_connection**: ID da la colliaziun da glistas. Mo tar elecziuns da proporz.
- **list_connection_parent**: ID da la colliaziun da glistas surordinada. Mo tar elecziuns da proporz e sch'i sa tracta d'ina sutcolliaziun da glistas.
- **candidate_family_name**: Num da famiglia da la candidata u dal candidat.
- **candidate_first_name**: Prenum da la candidata u dal candidat.
- **candidate_elected**: True, sche la candidata u il candidat è vegnì elegì.
- **candidate_votes**: Dumber da vuschs da candidat en la vischnanca.

### Resultats temporars

L'elecziun vala sco anc betg dumbrada ora, sche `election_counted_municipalites` na correspunda betg a `election_total_municipalites`. En cas da `election_total_municipalites = 0`, na po betg vegnir dada ina infurmaziun exacta davart il status da l'elecziun (damai che Wahlt è vegnì importà da Wabsti).

Las vischnancas che n'èn anc betg dumbradas ora n'èn betg cuntegnidas en las datas.

### Project

[election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_onegov_majorz.csv)

[election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_onegov_proporz.csv)