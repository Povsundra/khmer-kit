"""English translations for structured Khmer recipes (paraphrased, not verbatim)."""

from __future__ import annotations

import re

# Common Khmer cooking terms → English (paraphrase glossary)
INGREDIENT_GLOSSARY: dict[str, str] = {
    "សាច់ជ្រូកបីជាន់": "Three-layer pork (belly)",
    "ស្បែកជ្រូកបំពង": "Crispy fried pork skin",
    "ហៃប៊ី": "Dried lily buds",
    "យីហុ": "Wood ear mushrooms",
    "ផ្សិត": "Straw mushrooms",
    "ផ្សិតត្រចៀកកណ្តុរ": "Straw mushrooms",
    "ផ្កាស្ពៃ": "Cauliflower",
    "សាច់មាន់": "Chicken meat",
    "ថ្លើមជ្រូក": "Pork liver",
    "ពោះវៀនជ្រូក": "Pork intestines",
    "ទឹកត្រី": "Fish sauce",
    "អំបិល": "Salt",
    "ស្ករ": "Sugar",
    "ម្សៅស៊ុប": "Soup seasoning powder",
    "ម្រេច": "Black pepper",
    "ខ្ទឹមស": "Garlic",
    "មាន់": "Chicken",
    "ត្រីអណ្តែងទន់": "Soft white fish (e.g. trei andeng)",
    "ផ្លែត្នោតខ្ចី": "Young palm fruit",
    "ខ្ជាយ": "Fingerroot (krachai)",
    "រមៀត": "Turmeric",
    "រំដេង": "Galangal",
    "សំបកក្រូចសើច": "Kaffir lime zest",
    "ខ្ទឹមស-ក្រហម": "Garlic and red shallots",
    "អង្ករលីង": "Roasted rice powder",
    "ប្រហុក": "Fermented fish paste (prahok)",
    "ស្លឹកគ្រៃ": "Lemongrass",
    "ឆ្អឹងជំនីរជ្រូកខ្ចី": "Young pork ribs",
    "ខ្ទឹមបារាំង": "Onion",
    "ម្សៅឆា": "Starch (for thickening)",
    "ទឹកខ្លះ": "A little water",
    "សាច់គោ": "Beef",
    "ថ្លើម": "Liver",
    "បេះដូង": "Heart",
    "ប្រហុកល្អ": "Good quality prahok",
    "ម្ជូរអំពិល": "Tamarind",
    "គល់ស្លឹកគ្រៃ": "Lemongrass seeds",
    "ស្លឹកកន្ទ្រោប": "Holy basil leaves",
    "ស្លឹកក្រូចសើច": "Kaffir lime leaves",
    "ត្រីរស់": "Live fish",
    "ត្រីសណ្ដាយ": "Dried fish",
    "ស្លឹកជីរ": "Basil leaves",
    "ស្លឹកម្ទេស": "Chili leaves",
    "ត្រឡាច": "Lime",
    "ល្ពៅ": "Lemon",
    "ស្បែកជ្រូក": "Pork skin",
    "ឆ្អឹងជំនីជ្រូកខ្ចី": "Young pork ribs",
    "អំពិលទុំ": "Ripe tamarind",
    "ស្លឹកខ្ទឹម": "Lemongrass (sliced)",
    "វ៉ាន់ស៊ុយ": "Green onion (scallion)",
    "ត្រីស្លាត": "Snakehead fish",
    "ស្ពៃក្តោប": "Napa cabbage",
    "យីហុឺ": "Wood ear mushrooms",
    "ត្រីកេសរំពាង": "Kes rompeang fish",
    "សណ្តែកដី": "Peanuts",
    "សំបកផ្លែក្រូចសើច": "Kaffir lime zest",
    "សាច់សុទ្ធ": "Lean pork",
    "មីសួរ": "Glass noodles (mi sor)",
    "ពងទាសាប": "Duck egg",
    "ពពុះសណ្ដែក": "Bean sprouts",
    "ត្រចៀកកណ្តុរ": "Wood ear mushrooms",
    "ខ្លាញ់": "Cooking oil",
    "អង្ករដំណើបស": "Glutinous rice",
    "បង្គា": "Eggplant",
    "ត្រីងៀត": "Dried fish",
    "ស្លឹកចេក": "Banana leaf",
    "ចេកណាំវ៉ា": "Namwa banana",
    "ចេកពងមាន់": "Chicken-egg banana (variety)",
    "ដូងទុំ": "Ripe coconut",
    "ល្ង": "Turmeric (fresh)",
    "ម្សៅកញ្ចប់រូបកុមារ៉ាល់ហោះ": "Flying Boy brand flour mix",
    "ម្សៅខ្សាយ": "Rice flour",
    "ស៊ីអ៊ីវខាប់": "Cooking wine",
    "អង្ករដំណើប": "Glutinous rice",
    "សណ្តែកបាយ": "Soybeans",
    "ស្លឹកឫស្សី": "Pandan leaves",
    "ពងទា": "Duck egg",
    "ពងមាន់": "Chicken egg",
    "កោះ": "Chicken gizzard",
    "ត្រយូងចេក": "Banana blossom",
    "ជីរ": "Herbs (basil/mint)",
    "ទឹកខ្មេះ": "Vinegar",
}

DISH_NAME_EN: dict[str, str] = {
    "samlor_chap_chhay": "Samlor Chap Chhay (Mixed Meat and Vegetable Soup)",
    "samlor_kako_phlae_tnoat": "Samlor Kako with Young Palm Fruit",
    "cha_khtuem_barang": "Cha Khtuem Barang (Stir-fried Onion with Pork Ribs)",
    "samlor_kari_kroeung_sach_ko": "Samlor Machu Kroeung Sach Ko (Sour Beef Offal Soup)",
    "samlor_proheur": "Samlor Proheur (Sour Fish Soup)",
    "sngor_chrouk_spay_chrok": "Sngor Pickled Cabbage and Pork Skin Soup",
    "sngor_prohet_trei_slat": "Sngor Fish Ball Soup with Napa Cabbage",
    "kroeung_sach_trei": "Cha Kroeung Sach Trei (Stir-fried Fish with Spice Paste)",
    "cha_mi_sour": "Cha Mi Sour (Stir-fried Glass Noodles)",
    "bay_damnaeub_mukh_bangkea": "Bay Damnaeub Bam Pang (Fried Glutinous Rice Cones)",
    "chek_chien": "Chek Chien (Fried Bananas)",
    "num_ansom_chrouk": "Num Ansom Chrouk (Pork Rice Cake)",
    "omelette": "Omelette (Duck or Chicken Egg)",
    "nhoam_moan_tr_young_cek": "Nhoam Moan Tr Young Cek (Chicken Banana Blossom Salad)",
}

# Curated (text_kh, text_en) pairs when auto-split does not match recipe flow
CURATED_STEPS: dict[str, list[tuple[str, str]]] = {
    "samlor_kako_phlae_tnoat": [
        (
            "មាន់ឬត្រីលាងទឹកឱ្យស្អាត កាប់ដុំៗទុកសិន",
            "Wash the chicken or fish clean and cut into pieces; set aside.",
        ),
        (
            "ហាន់ស្លឹកគ្រៃឱ្យល្អិត យកទៅបុកជាមួយខ្ជាយរមៀតរំដេង សំបកក្រូចសើច ខ្ទឹមស-ក្រហមឱ្យម៉ដ្ឋទុកសិន អង្ករលីងកិនឱ្យល្អិត",
            "Finely chop lemongrass and pound with fingerroot, turmeric, galangal, kaffir lime zest, and garlic-shallot until smooth; set aside. Grind roasted rice powder finely.",
        ),
        (
            "យកឆ្នាំងដាក់ទឹកកន្លះ យកត្នោតខ្ចីមកចិតឱ្យស្តើងដាក់ក្នុងឆ្នាំង ដាំចំនួនពីរអំពុះ",
            "Put half a pot of water on the heat, peel and thinly slice the young palm fruit into the pot, and bring to a boil twice.",
        ),
        (
            "ជ្រុំប្រហុក បង់សាច់ត្រីឬមាន់ រួចដាក់គ្រឿងដែលបុកចូលនិងអង្ករលីង",
            "Add a block of prahok and the fish or chicken meat, then add the pounded spice paste and roasted rice powder.",
        ),
        (
            "ចាក់ទឹកត្រីអំបិល ស្ករ ម្សៅស៊ុប ភ្លក់មើលឱ្យល្មមតាមចូលចិត្ត",
            "Season with fish sauce, salt, sugar, and soup powder; taste and adjust to preference.",
        ),
    ],
    "cha_khtuem_barang": [
        (
            "ឆ្អឹងជំនីរខ្ចីកាត់ដុំៗ ខ្ទឹមបារាំង កាត់បណ្ដោយធំៗ",
            "Cut the young ribs into pieces; cut the onions into large lengthwise strips.",
        ),
        (
            "ដាំខ្ទះដាក់ខ្លាញ់ឱ្យក្តៅ ដាក់ឆ្អឹងជំនីរជ្រូកខ្ចីឆាចូល ចាក់ទឹកត្រី ដាក់ខ្ទឹមបារាំង អំបិល ស្ករ ម្សៅស៊ុប",
            "Heat a wok with oil, stir-fry the young pork ribs, add fish sauce, then add onion, salt, sugar, and soup powder.",
        ),
        (
            "ចាក់ទឹកខ្លះបន្តិច លាយម្សៅឆាចាក់ចូលបន្តិច ភ្លក្សមើលឱ្យល្មមតាមចូលចិត្ត",
            "Add a little water, mix starch with water and pour in to thicken slightly; taste and adjust to preference.",
        ),
    ],
    "samlor_kari_kroeung_sach_ko": [
        (
            "សាច់គោ ថ្លើម បេះដូង ហាន់ជាបន្ទះស្តើងល្មម ម្ជូរអំពិលឆ្កឹះ គ្រាប់ត្រាំទឹកឱ្យទន់",
            "Slice the beef, liver, and heart into moderate strips; soak tamarind and lemongrass seeds until soft.",
        ),
        (
            "គល់ស្លឹកគ្រៃហាន់ឱ្យល្អិត រំដេង សំបកក្រូចសើច រមៀតហាន់ឱ្យល្អិតទាំងអស់ បុកឱ្យម៉ដ្ឋ",
            "Finely chop lemongrass seeds, galangal, kaffir lime zest, and turmeric; pound until smooth.",
        ),
        (
            "ដាក់សាច់គោ ថ្លើម បេះដូងក្នុងឆ្នាំង ដាក់គ្រឿងបុក ប្រហុកចិញ្ច្រាំ ម្ជូរអំពិល ឬក្រសាំងច្របល់ឱ្យសព្វ ដាក់រម្ងាស់ឱ្យរីងទឹកបន្តិច",
            "Add beef, liver, and heart to the pot with the pounded paste, minced prahok, and tamarind or galangal; simmer briefly.",
        ),
        (
            "ថែមទឹកដាំឱ្យពុះ ស្រង់អំពិលចេញសិន រម្ងាស់ទៅទៀតឱ្យផុយសាច់ បង់បន្លែ រម្ងាស់ឱ្យផុយសាច់ ឆ្អិនបន្លែ",
            "Add more water and bring to a boil; remove tamarind; simmer until meat is tender; add vegetables and cook through.",
        ),
        (
            "ចាក់ទឹកត្រី ដាក់អំបិលភ្លក់ឱ្យល្មម បង់ស្លឹកក្រូចសើច ឬស្លឹកកន្ទ្រោប (ត្រូវរោលភ្លើង)",
            "Add fish sauce and salt to taste; finish with kaffir lime leaves or holy basil off the heat.",
        ),
    ],
    "samlor_proheur": [
        (
            "ត្រីធ្វើឱ្យស្អាតកាប់ជាកង់ៗ ស្លឹកគ្រៃហាន់ឱ្យល្អិត ដាក់ខ្ជាយ រមៀត ខ្ទឹមសបុកឱ្យម៉ដ្ឋ",
            "Clean the fish and cut into rings; finely chop lemongrass and pound with fingerroot, turmeric, and garlic.",
        ),
        (
            "ត្រឡាចចិតស្តើងល្មម ល្ពៅចិតកាស់ដុំៗ ស្លឹកជីរ ស្លឹកម្ទេស បេះលាងឱ្យស្អាតទុកសិន",
            "Peel lime or lemon into thin strips; wash basil and chili leaves; set aside.",
        ),
        (
            "ទើបដាំទឹកឱ្យពុះ ជ្រុំប្រហុកបង់អំបិលបន្តិច រួចដាក់ត្រីបង់ចូលឱ្យឆ្អិន",
            "Bring water to a boil; add prahok and a little salt; add the fish and cook through.",
        ),
        (
            "ដួសខ្លះបេះយកតែសាច់បុកជាមួយគ្រឿង ទើបបង់ល្ពៅ ឬត្រឡាចចូលឱ្យឆ្អិន ចាក់ទឹកត្រី ស្ករ ម្សៅស៊ុប សឹមដាក់គ្រឿងដាំឱ្យពុះ ភ្លក់មើលឱ្យល្មម មុនដាក់ចុះ សឹមបង់ស្លឹកជីរចូល",
            "Scoop some fish, pound the flesh with the spices, return with lemon or lime; season with fish sauce, sugar, and soup powder; simmer; add basil leaves just before serving.",
        ),
    ],
    "sngor_chrouk_spay_chrok": [
        (
            "ស្បែកលាងទឹកឱ្យស្អាត កាត់ប្រវែងមួយថ្នាំងដៃ ឆ្អឹងជំនីជ្រូកលាងឱ្យស្អាត កាប់ដុំៗ យកទៅស្លឱ្យផុយ",
            "Wash the pork skin and cut finger-length; wash and cut the young ribs; simmer the ribs until tender.",
        ),
        (
            "ទើបដាក់ស្បែកជ្រូកចូល ជ្រំអំពិលបន្តិច ដាក់អំបិល ស្ករ ចាក់ទឹកត្រី ម្សៅស៊ុប ភ្លក់មើលឱ្យល្មម",
            "Add the pork skin, ripe tamarind, salt, sugar, fish sauce, and soup powder; taste and adjust.",
        ),
        (
            "ហាន់ស្លឹកខ្ទឹម វ៉ាន់ស៊ុយវែងៗល្មម មុនដាក់ត្រូវបង់ស្លឹកខ្ទឹម វ៉ាន់ស៊ុយចូលសិន",
            "Slice lemongrass and green onion; add both to the soup just before serving.",
        ),
    ],
    "sngor_prohet_trei_slat": [
        (
            "ត្រីស្លាតត្រូវវះជាពីរ រួចយកទៅកោសយកសាច់ យកអំបិលម្រេចម៉ដ្ឋ ម្សៅស៊ុបដាក់ចូលច្របាច់ឱ្យឡើង ដាំទឹកឱ្យពុះ",
            "Split the snakehead fish and scrape out the meat; mix with salt, pepper, and soup powder; bring water to a boil.",
        ),
        (
            "លញ់ជាប្រហិតមូលៗបង់សម្លរទើបចាក់ទឹកត្រី អំបិល ស្ករ ដាក់ហៃប៊ីបង់សម្លរជាមួយឱ្យចេញជាតិ",
            "Shape into round fish balls and add to the soup; season with fish sauce, salt, and sugar; add lily buds for aroma.",
        ),
        (
            "ចិតស្ពៃក្តោបលាងឱ្យស្អាតបង់ចូលចំនួនពីរឬបីអំពុះ ដាក់ម្សៅស៊ុប ម្រេចម៉ដ្ឋ មុនដាក់ចុះត្រូវហាន់ស្លឹកខ្ទឹមបង់ចូល ភ្លក់មើលឱ្យល្មមសឹមដាក់ចុះជាក្រោយ",
            "Shred and wash napa cabbage; boil two or three times; add soup powder and pounded pepper; slice lemongrass and add before serving; taste and adjust.",
        ),
    ],
    "kroeung_sach_trei": [
        (
            "ត្រីស្រកាចេញ ហាន់ជាបន្ទះស្តើងល្មមប៉ុនៗមេដៃ សណ្តែកដីលីងបុក កុំឱ្យម៉ដ្ឋពេកទុកសិន",
            "Descale the fish and slice into thumb-sized strips; roast and crush peanuts, not too finely; set aside.",
        ),
        (
            "ស្លឹកគ្រៃ ខ្ជាយ រមៀត ខ្ទឹមស រំដេង សំបកផ្លែក្រូចសើច បុកឱ្យម៉ដ្ឋ",
            "Pound lemongrass, fingerroot, turmeric, garlic, galangal, and kaffir lime zest until smooth.",
        ),
        (
            "យកខ្ទះដាក់ខ្លាញ់ដាំឱ្យក្តៅ ដាក់ស្លឹកគ្រៃដែលបុកនោះឱ្យឈ្ងុយ ទើបដាក់ត្រីចូល ចាក់ទឹកត្រី អំបិល ស្ករ ម្សៅស៊ុប ឆាឱ្យឆ្អិន ភ្លក់មើលឱ្យល្មមតាមចូលចិត្ត",
            "Heat a wok with oil, fry the pounded paste until fragrant, add the fish, season with fish sauce, salt, sugar, and soup powder; stir-fry until cooked; taste and adjust.",
        ),
    ],
    "cha_mi_sour": [
        (
            "សាច់សុទ្ធហាន់ជាបន្ទះស្តើងចិញ្ច្រាំឱ្យល្អិត មីសួរ ត្រចៀកកណ្តុរ ពពុះសណ្ដែកត្រាំទឹកឱ្យរីកកាត់ឱ្យខ្លី។ ស្រង់ទុកឱ្យស្រសទឹក",
            "Mince the lean pork finely; soak glass noodles, wood ear, and bean sprouts until soft, cut short, and drain well.",
        ),
        (
            "យកខ្លាញ់ដាក់ខ្ទឹមសចិញ្ច្រាំឆាឱ្យឈ្ងុយ ដាក់សាច់ជ្រកឆា ចាក់ទឹកត្រី ស្ករ អំបិល ម្សៅស៊ុប",
            "Heat oil and fry minced garlic until fragrant; stir-fry the pork; add fish sauce, sugar, salt, and soup powder.",
        ),
        (
            "ដាក់ខ្ទឹមបារាំងហាន់បណ្តោយចំណិត ដាក់មីសួរ ត្រចៀកកណ្តុរ ឆាឱ្យឆ្អិន",
            "Add sliced onion, glass noodles, and wood ear; stir-fry until cooked.",
        ),
        (
            "វាយពងទាចាក់ចូលឆាឱ្យសព្វ រោយម្រេចបន្តិច ភ្លក់មើលឱ្យល្មមតាមចូលចិត្ត",
            "Beat the duck egg and pour in; scramble until set; add black pepper; taste and adjust to preference.",
        ),
    ],
    "bay_damnaeub_mukh_bangkea": [
        (
            "អង្ករយកទៅត្រាំជាមួយទឹកអំបិលចំនួន ៣ ម៉ោង ទើបស្រង់ទៅបំពងឱ្យស្រួយយកមកកិន ដាក់អំបិលបន្តិច បង្គាយកទៅបំពងឱ្យស្រួយ ពណ៌ជម្ពូយកទៅបំពងឱ្យស្រួយ រួចបុកឱ្យម៉ដ្ឋបន្តិច",
            "Soak glutinous rice in salted water for 3 hours; drain, fry until crisp, pound lightly with a little salt; fry eggplant and dried fish until crisp and pound lightly.",
        ),
        (
            "ដាក់ម្សៅស៊ុបបន្តិច ចាក់ទឹកត្រីបន្តិច អំបិល ស្ករ ម្សៅស៊ុប ភ្លក់មើលឲ្យល្មម កុំឲ្យប្រៃពេក រួចច្របល់ចូលគ្នាជានិច្ច ទើបយកបាយបំពងមកច្របល់ជាមួយបង្គា និងត្រីងៀត",
            "Season with soup powder, fish sauce, salt, and sugar — not too salty; mix everything together, then combine the fried rice with eggplant and dried fish.",
        ),
        (
            "យកស្លឹកចេកមកធ្វើជាកោណ ។ ចំណែកស្លឹកក្រូចសើចហាន់ជាសរសៃតូចៗ ទើបយកបាយដំណើបដាក់ក្នុងកោណនោះ យកសាច់បង្គាដាក់ពីលើឲ្យពេញ កុំឱ្យយឺតយូរ រួចយកស្លឹកកញ្ចុំដាក់ពីលើ និងស្លឹកក្រូចសើចហាន់ដាក់ពីលើទៀត ជាការស្រេច",
            "Shape a banana leaf into a cone; shred kaffir lime leaves finely; pack glutinous rice into the cone, top with the filling without delay, cover with banana leaf and kaffir shreds; serve.",
        ),
    ],
    "chek_chien": [
        (
            "ចេកត្រូវពុះជាបួនទុកសិន យកម្សៅខ្សាយលាយជាមួយម្សៅរូបកុមារ៉ាល់ហោះដាក់បន្តិច",
            "Halve the bananas lengthwise; mix rice flour with a little Flying Boy flour mix.",
        ),
        (
            "ពងទាយកតែសលាយជាមួយម្សៅឱ្យសព្វ ចាក់ស៊ីអ៊ីវបន្តិច ដាក់អំបិលបន្តិច",
            "Beat egg white into the flour until smooth; add a little cooking wine and salt.",
        ),
        (
            "យកល្ង ដូងពុះយកក្បាលខ្ទិះចាក់លាយម្សៅ រួចយកសាច់ដូងដែលកោសដាក់ចូលខ្លះ",
            "Grate turmeric and coconut head into the batter; add some grated coconut flesh.",
        ),
        (
            "ដាំខ្លាញ់ឱ្យក្តៅទើបយកចេកទៅជ្រលក់នឹងម្សៅ បង់ក្នុងខ្លាញ់ឱ្យឡើងក្រហមស្រួយ ជាការស្រេច",
            "Heat oil; dip bananas in the batter and fry until golden and crisp.",
        ),
    ],
    "num_ansom_chrouk": [
        (
            "អង្ករដំណើបត្រាំទឹកបីឬបួនម៉ោង សណ្តែកបាយលាង រួចយកទៅត្រាំទឹកឱ្យរីកសំបក លាងសម្អាតចេញឱ្យស្អាត",
            "Soak glutinous rice for 3–4 hours; wash soybeans and soak until skins loosen; rinse clean.",
        ),
        (
            "សាច់ជ្រូកហាន់វែងៗ រួចយកទៅប្រឡាក់អំបិល-ម្រេច ហាន់ស្លឹកខ្ទឹមដាក់លាយជាមួយ សណ្តែកបាយទៅដាំបាយសិន",
            "Slice pork into long strips; marinate with salt and pepper; slice lemongrass and mix in; cook soybeans first.",
        ),
        (
            "ជូនកាលយកក្បាលខ្ទិះលាយជាមួយអង្ករ ទើបយកស្លឹកចេកមកជូតពូតឱ្យស្អាត រួចយកអង្ករមកវាសដាក់លើស្លឹកចេក យកសណ្តែកដាក់លើអង្ករ រួចយកសាច់ជ្រូកដាក់កណ្តាលខ្ចប់ជាអន្សម ចងឱ្យជាប់មួយៗ",
            "Mix coconut head with rice; wipe banana leaves clean; spread rice on leaf, add soybeans, place pork in the center, and wrap each ansom tightly.",
        ),
        (
            "យកស្លឹកឫស្សីមកទ្រាប់បាតឆ្នាំង យកអន្សមដាក់ដំរៀបឱ្យពេញល្មម យកស្លឹកឫស្សីគ្របពីលើឱ្យពេញ ទើបចាក់ទឹកឱ្យល្មម រួចលើកចង្ក្រាន",
            "Line the pot with pandan leaves; arrange the ansom; cover with more pandan; add enough water and bring to a boil.",
        ),
        (
            "កាលណាខះទឹកត្រូវចាក់ទឹកថែមទៀត ចំនួន៨ឬ៩ម៉ោង លុះតែឆ្អិន សឹមស្រង់ដាក់ក្រឡបោកតម្រៀបស្រេច",
            "Top up water as needed; steam 8–9 hours until cooked; drain and press in a mold to set.",
        ),
    ],
    "omelette": [
        (
            "យកខ្ទះដាក់ខ្លាញ់ដាំឱ្យក្តៅ គោះពងមាន់ ដាក់លើខ្ទះ រោយអំបិល ស្ករ",
            "Heat a pan with oil; beat the eggs, pour onto the pan, and sprinkle with salt and sugar.",
        ),
        (
            "ម្រេច ត្រឡប់រួចដួសដាក់ចាន ជាការស្រេច",
            "Add black pepper, flip once cooked, then scoop onto a plate to serve.",
        ),
    ],
    "nhoam_moan_tr_young_cek": [
        (
            "មាន់លាងឱ្យស្អាត ស្ងោរឱ្យឆ្អិន ជាមួយកោះថ្លើម",
            "Wash the chicken clean and boil until cooked with the gizzard and liver.",
        ),
        (
            "ត្រយូងចេក ហាន់ស្តើងៗ យកទៅត្រាំទឹកដាក់ទឹកខ្មេះចូល ត្រាំកុំឱ្យខ្មៅ រួចស្រង់ដាក់ កញ្ច្រែងទុកសិន",
            "Slice the banana blossom thinly; soak in water with vinegar so it does not darken; drain and set aside.",
        ),
        (
            "យកមាន់បេះតែសាច់ជាសរសៃល្អិតៗ កោះថ្លើមហាន់ដាក់ លាយជាមួយត្រយូងចេក បេះស្លឹកជីរត្រូវកុំដាក់ឱ្យច្រើនពេក ខ្ទឹមសហាន់ ចៀនឱ្យក្រហមដាក់លាយជាមួយគ្នាទាំងអស់",
            "Shred the chicken meat finely; chop gizzard and liver; mix with banana blossom and a little herb; add fried golden garlic.",
        ),
        (
            "យកទឹកត្រីលាយទឹកខ្មេះ ស្ករ ម្រេចបុក ម្សៅស៊ុប ភ្លក់មើលឱ្យល្មម យកទៅចាក់ចូលលាយឱ្យសព្វ ភ្លក់មើលឱ្យឆ្ងាញ់ជាការស្រេច",
            "Mix fish sauce with vinegar, sugar, pounded pepper, and soup powder; taste; pour over the salad and mix well.",
        ),
    ],
}

# Fallback step translations when counts already match parsed Khmer steps
STEP_TRANSLATIONS: dict[str, list[str]] = {
    "samlor_chap_chhay": [
        "Slice the pork into thin strips.",
        "Cut the intestines into short rings.",
        "Slice the liver into thin strips.",
        "Soak the lily buds and wood ear mushrooms in water; slice the wood ear into thin strips.",
        "Cut the straw mushrooms, cauliflower, and peeled crispy pork skin into pieces; cut the chicken into bite-sized pieces.",
        "Heat a pot with oil, fry minced garlic until golden, add pork and chicken and stir-fry until cooked, season with fish sauce, salt, sugar, and soup powder, add all vegetables, pour in enough water to cover and bring to a boil, then finish with black pepper.",
    ],
    "samlor_kako_phlae_tnoat": [
        "Wash the chicken or fish clean and cut into pieces; set aside.",
        "Finely chop lemongrass and pound with fingerroot, turmeric, galangal, kaffir lime zest, and garlic-shallot until smooth; set aside. Grind roasted rice powder finely.",
        "Put half a pot of water on the heat, peel and thinly slice the young palm fruit into the pot, and bring to a boil twice.",
        "Add a block of prahok and the fish or chicken meat, then add the pounded spice paste and roasted rice powder.",
        "Season with fish sauce, salt, sugar, and soup powder; taste and adjust to preference.",
    ],
}


def translate_ingredient(raw_kh: str) -> str:
    cleaned = raw_kh.rstrip("។").strip()
    if cleaned in INGREDIENT_GLOSSARY:
        return INGREDIENT_GLOSSARY[cleaned]
    for kh, en in INGREDIENT_GLOSSARY.items():
        if kh in cleaned:
            return INGREDIENT_GLOSSARY[kh]
    return cleaned


def translate_steps(slug: str, steps_kh: list[str]) -> list[str]:
    if slug in STEP_TRANSLATIONS:
        curated = STEP_TRANSLATIONS[slug]
        if len(curated) == len(steps_kh):
            return curated
    return [translate_ingredient(s) for s in steps_kh]


def apply_curated_steps(recipe: dict, slug: str) -> dict | None:
    pairs = CURATED_STEPS.get(slug)
    if not pairs:
        return None
    recipe["steps"] = [
        {
            "step": i,
            "text_kh": kh,
            "text_en": en,
            "technique_note": "",
            "requires_safety_review": False,
            "contextualized_text_en": "",
        }
        for i, (kh, en) in enumerate(pairs, start=1)
    ]
    return recipe


def apply_translation(recipe: dict, *, slug: str) -> dict:
    recipe["dish_name_en"] = DISH_NAME_EN.get(slug, recipe.get("dish_name_en") or recipe["dish_name_kh"])
    for item in recipe["ingredients"]:
        item["standardized_en"] = translate_ingredient(item["raw_kh"])

    curated = apply_curated_steps(recipe, slug)
    if curated is not None:
        return curated

    texts_en = translate_steps(slug, [s["text_kh"] for s in recipe["steps"]])
    for step, text_en in zip(recipe["steps"], texts_en, strict=True):
        step["text_en"] = text_en
    return recipe
