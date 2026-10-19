## Prise en main

### Choisir ou créer une promotion
Une promotion couvre deux années de formation. Elle est définie par une année de départ et une année de fin (par exemple : 2026-2028) et possède un tarif annuel. Chaque promotion possède sa propre liste de participants.

> **Important :** les données des onglets *Animateurs*, *Destinataires* et *Envoyants* ne dépendent pas des promotions. Les participants, eux, sont rattachés à une promotion particulière.

L'onglet "Promotion XXXX-YYYY" est divisé en trois parties.
Dans la **partie haute** sont affichés la promotion sélectionnée et son tarif annuel.

En dessous : 

- Dans la **partie gauche**, vous pouvez sélectionner une promotion existante puis cliquer sur **Ouvrir** pour l’afficher et la gérer. Si une promotion antérieure est sélectionnée, le bouton **Revenir à la dernière promotion** permet de retrouver la promotion la plus récente.
- Dans la **partie droite**, vous pouvez créer une nouvelle promotion. Elle deviendra alors la promotion sélectionnée. Saisissez son année de départ et son tarif annuel ; l’année de fin est calculée automatiquement.

### Mode modification et mode consultation
Selon le mot de passe qui vous a été fourni, vous disposez de droits de consultation ou de modification. Votre niveau d’accès est indiqué sous votre nom, en bas du volet de gauche.

- Les **droits de consultation** permettent de consulter les informations, de modifier la configuration des étiquettes et des badges, de générer les documents (étiquettes, badges, feuilles d’émargement et de règlement des repas, factures) et d’exporter les données au format Excel.
- Les **droits de modification** permettent également de saisir et de modifier les informations et d’importer des données depuis des fichiers Excel.

### Comprendre les tableaux
Les tableaux des différents onglets possèdent les caractéristiques et fonctionnalités communes suivantes :

- Chaque colonne possède un en-tête. Cliquez dessus pour modifier l’ordre de **tri** du tableau.
- Lorsque des données sont incorrectes (manquantes ou format incorrect), les cellules correspondantes apparaissent en **rouge**.
- Chaque ligne du tableau possède une case à cocher dans la première colonne. Elle permet de sélectionner une ou plusieurs lignes. La case à cocher de l’en-tête permet de sélectionner ou désélectionner toutes les lignes.
- Lorsque vous disposez des droits de modification, trois boutons apparaissent sous le tableau, à **gauche** :
  - **Ajouter** : ajoute une ligne blanche à la fin du tableau pour saisir une nouvelle personne ;
  - **Importer** : importe des données depuis un fichier Excel (voir [Importer des données depuis Excel](#importer-des-donnees-depuis-excel)).
  - **Supprimer** : supprime les lignes sélectionnées.
- À **droite**, deux boutons permettent :
  - d’ajuster la largeur des colonnes à leur contenu ;
  - de recharger les données enregistrées. Cette action peut être utile si plusieurs utilisateurs modifient les données en même temps.

## Gérer les données

### Participants
L’onglet *Participants* permet de gérer les participants de la promotion sélectionnée. En plus des fonctions communes aux tableaux :

- Un filtre situé au-dessus du tableau permet de n’afficher que les participants envoyés par une personne donnée.
- Dans la dernière colonne, sélectionnez l’envoyant de chaque participant. Si celui-ci n’est pas dans la liste, ajoutez-le dans l’onglet [Envoyants](#envoyants).

> **Remarque :** si le libellé de l’envoyant apparaît en rouge, il ne correspond à aucun envoyant de la liste. Corrigez-le en ajoutant l’envoyant manquant ou en sélectionnant la bonne valeur. Sinon, les [factures](#factures-des-envoyants) ne pourront pas être générées pour ce participant.

### Animateurs
L’onglet *Animateurs* permet de gérer les animateurs de groupes de reprise. Ils peuvent recevoir des étiquettes de dossiers.

### Destinataires
L’onglet *Destinataires* permet de gérer des destinataires de courriers supplémentaires. Une étiquette de courrier est générée pour chacun d’eux.

### Envoyants
L’onglet *Envoyants* permet de gérer les personnes ou organisations (paroisses, mouvements, etc.) qui ont appelé les participants à rejoindre l’École du diocèse. Les envoyants sont également les destinataires des factures.

Les personnes et organisations de cette liste sont proposées comme envoyants dans la dernière colonne du tableau des [participants](#participants). Le nombre de participants associés à chaque envoyant est affiché dans le tableau ; cliquez sur ce nombre pour filtrer les participants correspondants.

### Ajouter, modifier et supprimer des lignes
Lorsque vous disposez des droits de modification, vous pouvez ajouter ou supprimer des lignes dans les tableaux. Modifiez directement les cellules pour mettre à jour les données.

### Importer des données depuis Excel
Lorsque vous disposez des droits de modification, vous pouvez importer des données Excel dans les tableaux. Le fichier doit respecter les règles suivantes :

- Le classeur doit contenir une feuille portant le nom de l’onglet à importer : *Participants*, *Animateurs*, *Destinataires* ou *Envoyants*.
- Les lignes vides situées au-dessus du tableau sont ignorées.
- Le tableau doit comporter une ligne d’en-tête. Les noms de colonnes reconnus dépendent de la configuration d’importation de l’application.

> **Remarque :** les données importées s’ajoutent aux données existantes ; elles ne les remplacent pas.

> Les fichiers Excel de l’ancien logiciel de gestion de l’École du diocèse peuvent également être utilisés pour importer des données.

## Générer les documents

### Feuilles d’émargement
Pour la promotion sélectionnée, cliquez sur l’année souhaitée (première ou deuxième année) dans la ligne **Émargement** du volet de gauche. La feuille est générée au format PDF et téléchargée.

### Feuilles de règlement des repas
Pour la promotion sélectionnée, cliquez sur l’année souhaitée dans la ligne **Repas** du volet de gauche. La feuille de règlement est générée au format PDF et téléchargée.

### Factures des envoyants
Pour la promotion sélectionnée, cliquez sur l’année souhaitée dans la ligne **Factures** du volet de gauche. Une facture est générée pour chaque envoyant associé à des participants. Le tarif annuel de la promotion est appliqué à chaque participant. Le PDF est téléchargé. La génération est bloquée si un participant renseigné n’a pas d’envoyant valide.

### Badges des participants
Cliquez sur **Badges** dans le volet de gauche pour générer et télécharger les badges des participants de la promotion sélectionnée au format PDF.

> Le format des badges est configurable dans l’onglet *Configuration* (voir [Configurer le logiciel](#configurer-le-logiciel)).

### Étiquettes de courriers
Cliquez sur **Étiquettes courriers** dans le volet de gauche pour générer et télécharger un PDF d’étiquettes pour les participants de la promotion sélectionnée et les destinataires enregistrés dans l’onglet *Destinataires*.

> Le format des étiquettes de courrier est configurable dans l’onglet *Configuration* (voir [Configurer le logiciel](#configurer-le-logiciel)).

### Étiquettes de dossiers
Cliquez sur **Étiquettes dossiers** dans le volet de gauche. Renseignez les informations de l’intervention pour laquelle générer les étiquettes :

- Nom de l’intervenant ;
- date de l’intervention ;
- titre de l’intervention.

Un PDF d’étiquettes est généré pour les participants de la promotion sélectionnée et les animateurs enregistrés dans l’application. Des étiquettes supplémentaires « INTERVENANT » et « ARCHIVE » sont également ajoutées. Le fichier est téléchargé.

> Le format des étiquettes de dossier est configurable dans l’onglet *Configuration* (voir [Configurer le logiciel](#configurer-le-logiciel)).


## Exporter les données

### Export Excel de la promotion
Cliquez sur **Export Excel** dans le volet de gauche pour télécharger un classeur contenant les données de la promotion sélectionnée et les listes générales :

- *Participants* : les participants de la promotion sélectionnée ;
- *Animateurs* : les animateurs tels qu'ils sont dans le système à ce jour ;
- *Destinataires* : les destinataires tels qu'ils sont dans le système à ce jour ;
- *Envoyants* : les envoyants tels qu'ils sont dans le système à ce jour ;

> **Remarque :** ce classeur peut servir de sauvegarde locale. Son format permet également de réimporter les données dans les onglets correspondants (voir [Importer des données depuis Excel](#importer-des-donnees-depuis-excel)).

## Configurer le logiciel

### Format des étiquettes et des badges
Dans l’onglet *Configuration*, vous pouvez ajuster le format des étiquettes et des badges en fonction du papier utilisé. Pour chaque format, définissez :

- les marges haute, basse, gauche et droite ;
- le nombre de colonnes et de lignes.

Le logiciel calcule et affiche les dimensions des étiquettes en temps réel.

> **Remarque :** même avec les droits de consultation, vous pouvez modifier la configuration des formats. Les changements sont conservés dans le système.

### Informations générales et coordonnées bancaires
Avec les droits de modification, vous pouvez renseigner dans l’onglet *Configuration* les informations générales et les coordonnées bancaires qui figureront sur les factures. Les champs obligatoires et les formats sont vérifiés avant l’enregistrement.
