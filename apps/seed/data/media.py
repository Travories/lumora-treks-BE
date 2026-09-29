"""
Images in `apps/seed/media/<key>.webp`.

Photos come from Wikimedia Commons at 2400px; `credit` holds the author,
license and source page (also stored on the CMS image) so ownership can be
reviewed and a photo swapped for an owned one. Design assets are the
bespoke, pre-cut artwork the frontend layers (cutouts, collages, masks) —
replace those only together with the frontend design.
"""

IMAGES = {
    # Photos
    "annapurna-circuit": {
        "title": "Thorong La pass",
        "alt": "Prayer flags at Thorong La pass on the Annapurna Circuit",
        "credit": "Vyacheslav Argenberg / Wikimedia Commons / CC BY 4.0 — https://commons.wikimedia.org/wiki/File:Thorong_La_Pass_2,_Himalaya,_Nepal.jpg",
    },
    "annapurna-region": {
        "title": "Annapurna South from Ghandruk",
        "alt": "Annapurna South above a village house in Ghandruk",
        "credit": "Bijaya2043 / Wikimedia Commons / CC BY-SA 3.0 — https://commons.wikimedia.org/wiki/File:Ghandruk_(1).JPG",
    },
    "poon-hill": {
        "title": "Poon Hill viewpoint",
        "alt": "Trekkers at Poon Hill facing Dhaulagiri at sunrise",
        "credit": "Gerd Eichmann / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Poon_Hill-68-Besucher_vor_Dhaulagiri-2013-gje.jpg",
    },
    "poon-hill-sunrise": {
        "title": "Sunrise at Poon Hill",
        "alt": "Photographers watching sunrise light the Himalaya from Poon Hill",
        "credit": "Thapaliyashreeram / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Poon_hill_sunrise.jpg",
    },
    "rara-lake": {
        "title": "Rara Lake",
        "alt": "Rara Lake surrounded by forest and snow-capped peaks",
        "credit": "Prajina Khatiwada / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Rara_lake,_Murma_top.jpg",
    },
    "rara-lake-shore": {
        "title": "Rara Lake shore",
        "alt": "Blue water of Rara Lake beneath snowy mountains",
        "credit": "Pradishpaudel / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Lake_Rara,_Mugu_(2).jpg",
    },
    "pokhara": {
        "title": "Phewa Lake and the Annapurna range",
        "alt": "Phewa Lake in Pokhara with the Annapurna range behind",
        "credit": "Jmhullot / Wikimedia Commons / CC BY 3.0 — https://commons.wikimedia.org/wiki/File:The_Annapurna_range_from_Pokhara.jpg",
    },
    "pokhara-valley": {
        "title": "Pokhara valley",
        "alt": "Phewa Lake and Pokhara seen from a hillside trail",
        "credit": "Abishkar Gautam / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Phewa_Lake_in_Pokhara,_Nepal.jpg",
    },
    "sarangkot": {
        "title": "Sunrise at Sarangkot",
        "alt": "Travellers watching sunrise over Machhapuchhre from Sarangkot",
        "credit": "Gerd Eichmann / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Pokhara-Sarangkot-20-Berge-2015-gje.jpg",
    },
    "bandipur": {
        "title": "Bandipur bazaar",
        "alt": "Traditional Newari houses and temple in Bandipur bazaar",
        "credit": "Rajesh Dhungana / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Bindyabasini_Temple_Bandipur_Tanahu_Nepal_Rajesh_Dhungana_(1).jpg",
    },
    "kathmandu": {
        "title": "Kathmandu Durbar Square",
        "alt": "Maju Dega temple in Kathmandu Durbar Square",
        "credit": "Vyacheslav Argenberg / Wikimedia Commons / CC BY 4.0 — https://commons.wikimedia.org/wiki/File:Kathmandu_Durbar_Square,_Maju_Dega_2,_Nepal.jpg",
    },
    "kathmandu-square": {
        "title": "Morning in Kathmandu Durbar Square",
        "alt": "People walking through Kathmandu Durbar Square",
        "credit": "Gerd Eichmann / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Kathmandu-Durbar_Square-12-Mini-Vishnu-Pratapamalla-Jagannath-2013-gje.jpg",
    },
    "swayambhunath": {
        "title": "Swayambhunath",
        "alt": "Swayambhunath stupa with prayer flags against a blue sky",
        "credit": "Nirmal Dulal / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Swayambhunath_temple_-_an_ancient_religious_architecture_of_Nepal.jpg",
    },
    "boudhanath": {
        "title": "Boudhanath",
        "alt": "Boudhanath stupa with prayer flags in Kathmandu",
        "credit": "Bernard Gagnon / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Boudhanath_stupa,_Kathmandu_01.jpg",
    },
    "patan": {
        "title": "Patan Durbar Square",
        "alt": "Temples and palace courtyard in Patan Durbar Square",
        "credit": "Shadow Ayush / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Patan_Durbar_Square_during_lockdown.jpg",
    },
    "everest-region": {
        "title": "Ama Dablam",
        "alt": "Ama Dablam rising above the Everest region valleys",
        "credit": "Vyacheslav Argenberg / Wikimedia Commons / CC BY 4.0 — https://commons.wikimedia.org/wiki/File:Himalayas,_Ama_Dablam,_Nepal.jpg",
    },
    "dhorpatan-region": {
        "title": "Dhorpatan valley",
        "alt": "Green valley of the Dhorpatan hunting reserve",
        "credit": "Ratish Jung Subedi / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Plateau_of_Dhorpatan,Dhorpatan_Hunting_Reserve.jpg",
    },
    "dhorpatan-meadow": {
        "title": "Dhorpatan meadows",
        "alt": "Sheep grazing on the alpine meadows of Dhorpatan",
        "credit": "Nirojsedhai / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Sheeps_of_Dhorpatan.jpg",
    },
    "gosaikunda": {
        "title": "Gosaikunda",
        "alt": "Sacred Gosaikunda lake among rocky peaks",
        "credit": "Sahilguraya / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:The_Gosaikunda_Lake.jpg",
    },
    "chitwan": {
        "title": "Rhinos in Chitwan",
        "alt": "Greater one-horned rhinoceros and calf in Chitwan National Park",
        "credit": "Aditya Pal / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Greater_one-horned_rhinoceros_at_Chitwan.jpg",
    },
    "mustang": {
        "title": "Mustang cliffs",
        "alt": "Wind-eroded cliffs in the Mustang valley",
        "credit": "Sunuwargr / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:A_Lens_into_the_Forbidden_Kingdom.jpg",
    },
    "langtang": {
        "title": "Langtang valley",
        "alt": "Meadow and pond in the Langtang valley under blue sky",
        "credit": "Stha.nibesh16 / Wikimedia Commons / CC BY-SA 3.0 — https://commons.wikimedia.org/wiki/File:Langtang_Valley.jpg",
    },
    "abc-trail": {
        "title": "Trail to Annapurna Base Camp",
        "alt": "Trail leading towards Annapurna South in the sanctuary",
        "credit": "Bijay Chaurasia / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Mt._Moditse_as_seen_from_Annapurna_Base_Camp-5324.jpg",
    },
    "abc-sunset": {
        "title": "Sunset at Annapurna Base Camp",
        "alt": "Evening light on the peaks above Annapurna Base Camp lodges",
        "credit": "Mithunkunwar9 / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Evening_view_of_Annapurna_Base_Camp.jpg",
    },
    "abc-lodge": {
        "title": "Annapurna Base Camp lodge",
        "alt": "Trekkers at a lodge terrace at Annapurna Base Camp",
        "credit": "Bijaya2043 / Wikimedia Commons / CC BY-SA 3.0 — https://commons.wikimedia.org/wiki/File:Annapurna_Base_Camp_(4).JPG",
    },
    "annapurna-trail": {
        "title": "Annapurna trail",
        "alt": "Snowy Annapurna sanctuary peaks under blue sky",
        "credit": "Rosan Harmens rooszan / Wikimedia Commons / CC0 — https://commons.wikimedia.org/wiki/File:Annapurna_Base_Camp_Trekking_Route,_Ghandruk,_Nepal_(Unsplash).jpg",
    },
    "trail-machhapuchhre": {
        "title": "Trail to Machhapuchhre",
        "alt": "Trekkers walking towards Machhapuchhre in the sanctuary",
        "credit": "Adventure pulse trekkers / Wikimedia Commons / CC BY 4.0 — https://commons.wikimedia.org/wiki/File:Annapurna_Base_Camp_Trek_view.jpg",
    },
    "teahouse": {
        "title": "Tea house in Chhomrong",
        "alt": "A mountain tea house on the Annapurna Base Camp trek",
        "credit": "Bijay Chaurasia / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Tea_House_during_Annapurna_Base_Camp_trek,_Chhomrong_Hill-2991.jpg",
    },
    "ghandruk": {
        "title": "Ghandruk village",
        "alt": "Stone houses of Ghandruk village below Annapurna South",
        "credit": "Kondephy / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Ghandruk_an_Annapurna_South.jpg",
    },
    "trekkers-guide": {
        "title": "Trekking with a local guide",
        "alt": "Trekkers following a guide on a village trail near Ghandruk",
        "credit": "Gerd Eichmann / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Ghandruk-350-Annapurna_Sued-Hiunchuli-2013-gje.jpg",
    },
    "machhapuchhre-sunrise": {
        "title": "Machhapuchhre sunrise",
        "alt": "Sun rays behind Machhapuchhre at dawn",
        "credit": "Bijay Chaurasia / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Machapuchare_Himal-3797.jpg",
    },
    "dal-bhat": {
        "title": "Dal bhat",
        "alt": "A plate of Nepali dal bhat with curries and pickles",
        "credit": "Gaurav Dhwaj Khadka / Wikimedia Commons / CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Masu_Bhat_1.jpg",
    },
    # Design assets
    "hero": {
        "title": "Himalayan panorama",
        "alt": "Snow-capped Himalayan peaks above forested ridges",
        "credit": "Lumora Treks",
    },
    "cta-bg": {
        "title": "Mountain sunset",
        "alt": "Misty forested ridges beneath the mountains",
        "credit": "Lumora Treks",
    },
    "authentic-nepal": {
        "title": "Authentic Nepal",
        "alt": "Stone stupas framed in the authentic experiences cutout",
        "credit": "Lumora Treks",
    },
    "contact-hero": {
        "title": "Contact hero",
        "alt": "Traveller looking out over the Himalaya",
        "credit": "Lumora Treks",
    },
    "packages-hero": {"title": "Packages hero", "alt": "Collage of Nepal travel experiences", "credit": "Lumora Treks"},
    "destinations-hero": {
        "title": "Destinations hero",
        "alt": "Collage of Nepal destinations",
        "credit": "Lumora Treks",
    },
    "avatar-1": {"title": "Author portrait", "alt": "Portrait of a Lumora Treks team member", "credit": "Lumora Treks"},
}
