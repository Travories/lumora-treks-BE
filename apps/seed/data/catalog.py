"""Destinations, packages and testimonials."""

DESTINATIONS = [
    {
        "slug": "annapurna-circuit",
        "title": "Annapurna Circuit",
        "image": "pkg-annapurna",
        "subtitle": "A legendary Himalayan journey through changing valleys and high passes.",
        "description": (
            "The Annapurna Circuit moves from subtropical river valleys into dry Himalayan landscapes, passing traditional villages and dramatic mountain walls. It is best known for the high Thorong La crossing and the variety of culture and scenery along the route."
        ),
        "highlights": [
            "Diverse landscapes from low valleys to high Himalaya",
            "Traditional villages and mountain culture",
            "Thorong La pass trekking route",
        ],
        "region": "Annapurna",
        "best_season": "March to May and October to November",
        "layout": "large",
    },
    {
        "slug": "annapurna-region",
        "title": "Annapurna Region",
        "image": "region-annapurna",
        "subtitle": "Teahouse trails, Gurung villages, and the Annapurna Sanctuary.",
        "description": (
            "The Annapurna region combines welcoming mountain villages with some of Nepal's most rewarding Himalayan walking. Travel through rhododendron forest and stone settlements toward wide views of Machhapuchhre, Annapurna South, and the sanctuary."
        ),
        "highlights": [
            "Annapurna Base Camp at 4,130 m",
            "Gurung villages and local teahouses",
            "Forest trails and Himalayan panoramas",
        ],
        "region": "Annapurna",
        "best_season": "March to May and October to November",
        "layout": "large",
    },
    {
        "slug": "poon-hill",
        "title": "Poon Hill",
        "image": "dest-poonhills",
        "subtitle": "A compact Annapurna trek for a remarkable Himalayan sunrise.",
        "description": (
            "Poon Hill is a classic short trek above Ghorepani. Its pre-dawn viewpoint opens across Dhaulagiri, Annapurna South, Hiunchuli, and Machhapuchhre, with village trails and rhododendron forest along the way."
        ),
        "highlights": [
            "Sunrise panorama from Poon Hill",
            "Ghorepani village and teahouses",
            "Rhododendron forest trails",
        ],
        "region": "Annapurna",
        "best_season": "March to May and October to November",
        "layout": "small",
    },
    {
        "slug": "rara-lake",
        "title": "Rara Lake",
        "image": "region-rara-lake",
        "subtitle": "Quiet water, far-west hills, and Nepal's largest alpine lake.",
        "description": (
            "Rara Lake National Park rewards the journey west with deep-blue water, forested slopes, and a calmer rhythm than Nepal's busier trekking corridors. It is ideal for lakeside walks, birdlife, and wide open viewpoints."
        ),
        "highlights": [
            "Nepal's largest alpine lake",
            "Lakeside walks and viewpoints",
            "Birdlife and far-west landscapes",
        ],
        "region": "Western Nepal",
        "best_season": "April to June and September to November",
        "layout": "small",
    },
    {
        "slug": "kathmandu-pokhara",
        "title": "Kathmandu & Pokhara",
        "image": "exp-pokhara",
        "subtitle": "Living heritage in Kathmandu, followed by Pokhara's lakeside calm.",
        "description": (
            "This route connects Kathmandu's historic squares and living temples with Pokhara's relaxed lakefront and mountain views. It is designed for travelers who want a balanced first journey through Nepal without a high-altitude trek."
        ),
        "highlights": [
            "Kathmandu's heritage sites",
            "Phewa Lake and Pokhara viewpoints",
            "Private transfers and local guidance",
        ],
        "region": "Kathmandu Valley",
        "best_season": "February to May and October to December",
        "layout": "small",
    },
    {
        "slug": "bandipur",
        "title": "Bandipur",
        "image": "region-bandipur",
        "subtitle": "A preserved hill town with Newari character and Himalayan views.",
        "description": (
            "Bandipur sits on a ridge between Kathmandu and Pokhara, with pedestrian lanes, traditional Newari houses, and wide views toward the Annapurna range. It is a peaceful stop for culture, short walks, and slower travel."
        ),
        "highlights": ["Historic Newari townscape", "Ridge-top Himalayan views", "Relaxed walking and local cafés"],
        "region": "Gandaki",
        "best_season": "February to May and October to December",
        "layout": "small",
    },
    {
        "slug": "kathmandu",
        "title": "Kathmandu",
        "image": "region-kathmandu",
        "subtitle": "Living heritage, busy bazaars, and a gateway to Nepal.",
        "description": (
            "Kathmandu brings together historic squares, Buddhist stupas, Hindu temples, workshops, and vibrant neighbourhoods. It is the natural starting point for most journeys in Nepal and rewards time beyond the airport transfer."
        ),
        "highlights": [
            "UNESCO heritage sites and living temples",
            "Food, crafts, and local neighbourhoods",
            "Gateway for journeys across Nepal",
        ],
        "region": "Kathmandu Valley",
        "best_season": "February to May and October to December",
        "layout": "small",
    },
    {
        "slug": "swayambhunath",
        "title": "Swayambhunath",
        "image": "region-swayambhunath",
        "subtitle": "An ancient hilltop stupa overlooking the Kathmandu Valley.",
        "description": (
            "Swayambhunath, often called the Monkey Temple, is one of the Kathmandu Valley's most recognisable sacred sites. Its white dome, watchful Buddha eyes, prayer flags, and hilltop views make it a memorable cultural stop."
        ),
        "highlights": [
            "Ancient Buddhist stupa",
            "Panoramic Kathmandu Valley views",
            "Prayer flags, shrines, and local life",
        ],
        "region": "Kathmandu Valley",
        "best_season": "Year-round; clearest views October to March",
        "layout": "small",
    },
    {
        "slug": "everest-region",
        "title": "Everest Region",
        "image": "region-everest",
        "subtitle": "High Himalayan trails beneath the world's tallest mountains.",
        "description": (
            "The Everest region is shaped by Sherpa culture, suspension bridges, alpine valleys, and iconic views of Everest, Lhotse, and Ama Dablam. Routes range from village stays to demanding high-altitude expeditions."
        ),
        "highlights": [
            "Everest and Ama Dablam mountain views",
            "Sherpa villages and monasteries",
            "World-class high-altitude trekking",
        ],
        "region": "Everest",
        "best_season": "March to May and October to November",
        "layout": "large",
    },
    {
        "slug": "dhorpatan-region",
        "title": "Dhorpatan Region",
        "image": "exp-dhorpatan",
        "subtitle": "Remote valleys, alpine meadows, and western Nepal wilderness.",
        "description": (
            "Dhorpatan offers a quieter side of Nepal, with high pasturelands, traditional settlements, and wide-open trails in the western hills. It suits travellers seeking a less-travelled mountain landscape."
        ),
        "highlights": ["Remote western Nepal trails", "Alpine meadows and forest", "Traditional hill communities"],
        "region": "Western Nepal",
        "best_season": "March to May and October to November",
        "layout": "small",
    },
    {
        "slug": "patan",
        "title": "Patan",
        "image": "exp-patan",
        "subtitle": "Newari artistry, courtyards, and one of Nepal's finest durbar squares.",
        "description": (
            "Patan is celebrated for its dense concentration of temples, stonework, metal craft, and traditional Newari courtyards. Its compact historic centre makes it ideal for a thoughtful cultural day in the valley."
        ),
        "highlights": ["Patan Durbar Square", "Newari art and metalwork", "Walkable historic courtyards"],
        "region": "Kathmandu Valley",
        "best_season": "Year-round; October to March is especially clear",
        "layout": "small",
    },
    {
        "slug": "pokhara",
        "title": "Pokhara",
        "image": "exp-pokhara",
        "subtitle": "Lakeside calm with the Annapurna range on the horizon.",
        "description": (
            "Pokhara balances Phewa Lake, easy-going cafés, mountain viewpoints, and access to the Annapurna trails. It works equally well as a restorative stop and as the launch point for adventure in western Nepal."
        ),
        "highlights": [
            "Phewa Lake and lakeside life",
            "Annapurna and Machhapuchhre views",
            "Gateway to trekking and adventure",
        ],
        "region": "Gandaki",
        "best_season": "February to May and October to December",
        "layout": "large",
    },
    {
        "slug": "journey-to-fish-lake",
        "title": "Journey to Fish Lake",
        "image": "seasonal-1",
        "subtitle": "A quieter escape to remote lakeside landscapes.",
        "description": (
            "This destination represents a slower journey through Nepal's remote lake country, where the reward is open water, birdlife, and time away from busy routes. It is a natural match for travellers who value pace and scenery."
        ),
        "highlights": ["Remote lake landscapes", "Quiet walking routes", "Birdlife and wide views"],
        "region": "Western Nepal",
        "best_season": "April to June and September to November",
        "layout": "tall",
    },
    {
        "slug": "gosaikunda-trail",
        "title": "Gosaikunda Trail",
        "image": "seasonal-2",
        "subtitle": "A sacred alpine lake trek north of Kathmandu.",
        "description": (
            "The Gosaikunda Trail climbs through Langtang National Park to a cluster of high, sacred lakes. The route combines forest, ridges, Tamang culture, and an unforgettable alpine destination."
        ),
        "highlights": [
            "Sacred high-altitude lakes",
            "Langtang National Park trails",
            "Tamang villages and ridge views",
        ],
        "region": "Langtang",
        "best_season": "March to May and October to November",
        "layout": "tall",
    },
    {
        "slug": "chitwan-safari",
        "title": "Chitwan Safari",
        "image": "seasonal-3",
        "subtitle": "Jungle walks and river landscapes in Nepal's southern lowlands.",
        "description": (
            "Chitwan National Park offers a different side of Nepal: sal forest, grassland, rivers, and rich wildlife. Guided nature activities focus on responsible viewing, local Tharu culture, and time outdoors."
        ),
        "highlights": [
            "Guided jungle and river activities",
            "Wildlife and birdwatching",
            "Tharu culture and lowland landscapes",
        ],
        "region": "Chitwan",
        "best_season": "October to March",
        "layout": "wide",
    },
    {
        "slug": "mustang-valley",
        "title": "Mustang Valley",
        "image": "seasonal-4",
        "subtitle": "Wind-shaped cliffs, ancient settlements, and trans-Himalayan culture.",
        "description": (
            "Mustang feels distinct from the greener parts of Nepal, with dry valleys, eroded cliffs, walled villages, and Tibetan-influenced culture. The journey is as much about the road and landscape as the destination."
        ),
        "highlights": ["Trans-Himalayan desert scenery", "Ancient walled settlements", "Tibetan-influenced culture"],
        "region": "Mustang",
        "best_season": "May to October",
        "layout": "tall",
    },
    {
        "slug": "langtang-valley",
        "title": "Langtang Valley",
        "image": "seasonal-5",
        "subtitle": "A close-to-Kathmandu Himalayan valley of forest, peaks, and Tamang culture.",
        "description": (
            "Langtang Valley offers an accessible Himalayan trekking experience with oak and rhododendron forest, yak pastures, glacier views, and warm Tamang hospitality. It is ideal for travellers with limited time."
        ),
        "highlights": [
            "Himalayan trekking close to Kathmandu",
            "Tamang villages and culture",
            "Forest, pasture, and glacier views",
        ],
        "region": "Langtang",
        "best_season": "March to May and October to November",
        "layout": "tall",
    },
]

# What a package includes, by kind of trip.
TREK_INCLUDED = [
    "Licensed local guide",
    "Teahouse accommodation",
    "Daily breakfast",
    "Required permits",
    "Ground transfers",
]
TOUR_INCLUDED = [
    "Licensed local guide",
    "Hotel accommodation",
    "Daily breakfast",
    "Entrance fees for listed sites",
    "Private ground transfers",
]
EXCLUDED = ["International flights", "Travel insurance", "Personal expenses", "Meals not listed"]

PACKAGES = [
    {
        "slug": "annapurna-base-camp-trek",
        "title": "Annapurna Base Camp Trek",
        "category": "Trekking",
        "destination": "annapurna-region",
        "image": "dest-annapurna",
        "gallery": ["pkg-annapurna", "dest-annapurna", "region-annapurna", "package-card3"],
        "summary": "A classic teahouse trek through Gurung villages, forest trails, and the Annapurna Sanctuary.",
        "description": (
            "Follow the Modi Khola valley from the foothills into the Annapurna Sanctuary. This seven-day route balances a steady ascent with warm teahouse stays, rhododendron forest, Machhapuchhre views, and a dawn at Annapurna Base Camp (4,130 m)."
        ),
        "duration": "7 Days",
        "duration_days": 7,
        "price": 650,
        "difficulty": "moderate",
        "people_count": 12,
        "is_popular": True,
        "highlights": [
            "Sunrise at Annapurna Base Camp",
            "Gurung villages and teahouse hospitality",
            "Machhapuchhre and Annapurna Sanctuary views",
        ],
        "itinerary": [
            (
                "Day 1",
                "Pokhara to Ghandruk",
                "Drive from Pokhara to the trailhead and walk into Ghandruk, a stone village with wide views of Annapurna South.",
            ),
            (
                "Day 2",
                "Ghandruk to Chhomrong",
                "Descend to the Kimrong Khola, then climb to Chhomrong, the gateway village to the sanctuary.",
            ),
            (
                "Day 3",
                "Chhomrong to Bamboo",
                "Follow stone steps and a shaded forest trail through Sinuwa, Kuldighar, and Bamboo.",
            ),
            (
                "Day 4",
                "Bamboo to Deurali",
                "Climb through bamboo and rhododendron forest to the open valley below Machhapuchhre Base Camp.",
            ),
            (
                "Day 5",
                "Deurali to Annapurna Base Camp",
                "Walk beneath the steep sanctuary walls to Annapurna Base Camp for an evening among the peaks.",
            ),
            (
                "Day 6",
                "Annapurna Base Camp to Bamboo",
                "Enjoy a clear mountain morning, then retrace the valley downhill to Bamboo.",
            ),
            ("Day 7", "Bamboo to Pokhara", "Descend to the roadhead and return to Pokhara after the trek."),
        ],
        "included": TREK_INCLUDED,
        "excluded": EXCLUDED,
    },
    {
        "slug": "poon-hill-sunrise-trek",
        "title": "Poon Hill Sunrise Trek",
        "category": "Trekking",
        "destination": "poon-hill",
        "image": "dest-poonhills",
        "gallery": ["dest-poonhills", "pkg-annapurna", "region-annapurna"],
        "summary": "A short, rewarding Annapurna trek built around the sunrise panorama from Poon Hill.",
        "description": (
            "This compact four-day trek passes through Magar and Gurung villages, rhododendron forest, and traditional teahouses before an early climb to Poon Hill. The viewpoint looks across Dhaulagiri, Annapurna South, Hiunchuli, and Machhapuchhre."
        ),
        "duration": "4 Days",
        "duration_days": 4,
        "price": 380,
        "difficulty": "easy",
        "people_count": 12,
        "is_popular": True,
        "highlights": [
            "Sunrise from Poon Hill",
            "Ghorepani's mountain teahouses",
            "Rhododendron forest and village trails",
        ],
        "itinerary": [
            ("Day 1", "Pokhara to Ulleri", "Drive to Nayapul and walk past terraced fields to Ulleri."),
            (
                "Day 2",
                "Ulleri to Ghorepani",
                "Climb through forest to Ghorepani, a lively stop on the Annapurna trails.",
            ),
            (
                "Day 3",
                "Poon Hill sunrise and Tadapani",
                "Make the pre-dawn walk to Poon Hill, then continue through forest to Tadapani.",
            ),
            ("Day 4", "Tadapani to Pokhara", "Descend through Ghandruk and return by road to Pokhara."),
        ],
        "included": TREK_INCLUDED,
        "excluded": EXCLUDED,
    },
    {
        "slug": "journey-to-fish-lake",
        "title": "Journey to Fish Lake",
        "category": "Hiking",
        "destination": "rara-lake",
        "image": "package-card1",
        "gallery": ["package-card1", "region-rara-lake", "seasonal-1"],
        "summary": "A relaxed highland escape to Rara Lake, Nepal's largest alpine lake.",
        "description": (
            "Travel from Nepalgunj into the far-west hills for quiet trails, lakeside viewpoints, and time around the deep-blue waters of Rara Lake. This is a slower journey for travelers who want scenery, birdlife, and space away from busy trekking routes."
        ),
        "duration": "5 Days",
        "duration_days": 5,
        "price": 720,
        "difficulty": "easy",
        "people_count": 10,
        "is_popular": True,
        "highlights": ["Rara Lake shoreline walks", "Far-west Nepal landscapes", "Birdwatching and quiet viewpoints"],
        "itinerary": [
            ("Day 1", "Nepalgunj to Talcha", "Fly to Talcha and transfer toward Rara National Park."),
            ("Day 2", "Explore Rara Lake", "Walk the shoreline and settle into the lake landscape."),
            (
                "Day 3",
                "Lakeside viewpoints",
                "Hike to a viewpoint for broad views across Rara and the surrounding hills.",
            ),
            ("Day 4", "Village trail", "Take an easy guided walk through nearby settlement and forest."),
            ("Day 5", "Return via Talcha", "Transfer to Talcha for the return journey."),
        ],
        "included": TREK_INCLUDED,
        "excluded": EXCLUDED,
    },
    {
        "slug": "pokhara-kathmandu-tours",
        "title": "Pokhara & Kathmandu Tours",
        "category": "Sightseeing",
        "destination": "kathmandu-pokhara",
        "image": "package-card2",
        "gallery": ["package-card2", "cultural-1", "exp-pokhara", "pkg-pokhara", "cultural-2", "region-kathmandu"],
        "summary": "A culture-and-landscape journey linking Kathmandu's heritage with Pokhara's lakeside calm.",
        "description": (
            "Spend time in Kathmandu's historic squares and living temples, then continue to Pokhara for Phewa Lake, mountain views, and a gentler pace. It is designed for first-time Nepal visitors who want cultural depth without a high-altitude trek."
        ),
        "duration": "5 Days",
        "duration_days": 5,
        "price": 560,
        "difficulty": "easy",
        "people_count": 14,
        "is_popular": True,
        "highlights": [
            "Kathmandu heritage sites",
            "Phewa Lake and Pokhara viewpoints",
            "Private transfers and local guide support",
        ],
        "itinerary": [
            ("Day 1", "Arrive in Kathmandu", "Airport welcome and an evening orientation."),
            ("Day 2", "Kathmandu heritage day", "Explore key historic squares and temples with a local guide."),
            ("Day 3", "Drive to Pokhara", "Travel west through river valleys to Pokhara."),
            ("Day 4", "Pokhara lakeside and viewpoints", "Visit Phewa Lake and a sunrise viewpoint."),
            ("Day 5", "Return to Kathmandu", "Travel back to Kathmandu for onward departure."),
        ],
        "included": TOUR_INCLUDED,
        "excluded": EXCLUDED,
    },
    {
        "slug": "abc-base-camp-trek",
        "title": "ABC Base Camp Trek",
        "category": "Trekking",
        "destination": "annapurna-region",
        "image": "package-card3",
        "gallery": ["package-card3", "pkg-annapurna", "dest-annapurna", "region-annapurna"],
        "summary": "An Annapurna Sanctuary trek with extra time for acclimatization and village life.",
        "description": (
            "A fuller Annapurna Base Camp itinerary for travelers who want measured walking days and time to enjoy the changing landscape from foothill villages to the high sanctuary. The route uses trusted local teahouses and a licensed mountain guide."
        ),
        "duration": "9 Days",
        "duration_days": 9,
        "price": 780,
        "difficulty": "moderate",
        "people_count": 10,
        "is_popular": True,
        "highlights": [
            "Measured acclimatization schedule",
            "Annapurna Sanctuary sunrise",
            "Licensed guide and local teahouses",
        ],
        "itinerary": [
            ("Day 1", "Pokhara to Ghandruk", "Transfer to the trail and walk to Ghandruk."),
            ("Day 2", "Ghandruk to Chhomrong", "Climb to the sanctuary gateway village."),
            ("Day 3", "Chhomrong to Bamboo", "Forest trail and teahouse stay."),
            ("Day 4", "Bamboo to Deurali", "Continue through the Modi Khola valley."),
            ("Day 5", "Deurali to Machhapuchhre Base Camp", "Enter the upper sanctuary beneath Machhapuchhre."),
            ("Day 6", "Machhapuchhre Base Camp to Annapurna Base Camp", "Short high-altitude walk to the base camp."),
            ("Day 7", "Annapurna Base Camp to Bamboo", "Return downhill through the sanctuary."),
            ("Day 8", "Bamboo to Jhinu Danda", "Walk to Jhinu Danda, known for its natural hot springs."),
            ("Day 9", "Jhinu Danda to Pokhara", "Finish the trek and return to Pokhara."),
        ],
        "included": TREK_INCLUDED,
        "excluded": EXCLUDED,
    },
]

TESTIMONIALS = [
    {
        "author_name": "Sarah Whitman",
        "author_role": "Everest Base Camp Trekker",
        "quote": (
            "Traveling with Lumora Treks was the best decision we made this year — every trail, "
            "every sunrise, and every local story felt like it was made just for us."
        ),
        "rating": 5,
        "package": None,
        "is_featured": True,
    },
    {
        "author_name": "Maya Sharma",
        "author_role": "Verified traveller",
        "quote": "A smooth, thoughtful Nepal journey with excellent local guidance.",
        "rating": 5,
        "package": "annapurna-base-camp-trek",
        "is_featured": False,
    },
    {
        "author_name": "Daniel Carter",
        "author_role": "Adventure traveller",
        "quote": "Beautiful routes, clear planning, and memorable experiences from start to finish.",
        "rating": 5,
        "package": "pokhara-kathmandu-tours",
        "is_featured": False,
    },
]
