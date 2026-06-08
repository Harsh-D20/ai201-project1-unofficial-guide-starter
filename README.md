# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

I chose the On-Campus Dining domain for the University of Maryland, College Park.
This knowledge is difficult to find because it is scattered across so many websites. Dining hall locations, prices, meal plans, cafes, hours, and special services are spread across 5–10+ separate pages on the UMD Dining website, the Academic Catalog, Reddit, and third-party visitor guides. A student trying to answer even a simple question like "what does a sick meal include?" would have to know to look at a specific subpage of dining.umd.edu. This fragmentation makes it a strong use case for a RAG-based guide that consolidates everything into one searchable interface.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | UMD Dining — Dining Halls Overview | Official dining page | https://dining.umd.edu/hours-locations/dining-halls |
| 2 | UMD Dining — Door Prices | Official dining page | https://dining.umd.edu/home/hours-locations/dining-halls/door-prices |
| 3 | UMD Academic Catalog — Dining Services | Official academic catalog | https://academiccatalog.umd.edu/undergraduate/campus-administration-resources-student-services/student-programs-services/dining-services/ |
| 4 | r/UMD — Charging in Dining Halls | Reddit thread | https://www.reddit.com/r/UMD/comments/1sngnlo/charging_in_dining_halls/ |
| 5 | r/UMD — Meal Plan vs. Buying Food | Reddit thread | https://www.reddit.com/r/UMD/comments/1s1ol7n/whats_cheaper_choosing_a_meal_plan_or_buying/ |
| 6 | UMD Campus Visitor Guide — Where to Eat | Third-party visitor guide | https://campusvisitorguides.com/umd/where-to-eat/ |
| 7 | UMD Dining — Allergy Information | Official dining page | https://dining.umd.edu/nutrition-allergies-and-special-diets/allergy |
| 8 | UMD Dining — Sick Meals | Official dining page | https://dining.umd.edu/students/sick-meals |
| 9 | UMD Dining — Resident Plans | Official dining page | https://dining.umd.edu/students/resident-plans |
| 10 | UMD Dining — Connector Plans | Official dining page | https://dining.umd.edu/students/connector-plans |
| 11 | UMD Dining — Dining Dollars | Official dining page | https://dining.umd.edu/students/dining-dollars-flexible-discounted-and-convenient |

---

## Chunking Strategy

**Chunk size:**
500 characters per chunk.

**Overlap:**
50 characters of overlap between consecutive chunks.

**Why these choices fit your documents:**
The documents are structured as short informational paragraphs — each section of a dining page addresses one distinct topic (a plan type, a price table, a policy). At 500 characters (~60–80 words), a chunk is usually large enough to capture a complete idea without spanning multiple unrelated topics. Smaller chunks would fragment sentences mid-thought; larger chunks would blend distinct topics (e.g., breakfast hours mixed with sick meal policy) that should be retrieved independently.

The 50-character overlap (~10 words) is a safety net for facts that fall near a chunk boundary, such as a price that appears at the end of one paragraph and its explanation at the start of the next. Without overlap, those edge cases would be split across non-adjacent chunks and never co-retrieved. The overlap is kept small because the documents are relatively short and a larger overlap would introduce more duplicate noise per query.

Chunking is recursive: it first tries to split on paragraph breaks (`\n\n`), then line breaks (`\n`), then sentence endings (`. `, `! `, `? `), then words, and finally characters. This preserves semantic boundaries wherever possible rather than cutting blindly at a fixed character count.

**Final chunk count:**
90 chunks across 11 documents.

**Sample Chunks**
1. [source: dining-halls.txt]  [url: https://dining.umd.edu/hours-locations/dining-halls]
debit cards, Dining Dollars and Terrapin Express. During the semester, times for breakfast, lunch and dinner are:
- Breakfast: Open to 10:30am
- Lunch: 10:30am to 4:00pm
- Dinner:  4:00pm to Close Dining Hall Information:
South Campus: 
Address: 7093 PREINKERT DR, COLLEGE PARK, MD 20742
Phone Number: (301) 314-8044
Breakfast starts at 7 am Monday–Friday and 10 am on weekends, with service running until 9 pm each night.

2. [source: allergy.txt]  [url: https://dining.umd.edu/nutrition-allergies-and-special-diets/allergy]
to carry it with you everywhere and at all times. In the event of an emergency, we have an Epi-Pen at each dining hall. Managers and supervisors are trained in the correct use of the Epi-PEn. However, for your own safety, if you have been prescribed an Epi-Pen, please carry it with you. Questions?

3. [source: dining-dollars-flexible-discounted-and-convenient.txt]  [url: https://dining.umd.edu/students/dining-dollars-flexible-discounted-and-convenient]
iscounted, and Convenient What are Dining Dollars? Dining Dollars are a convenient way to pay for food and snacks at any permanent Maryland Dining location on campus, including dining halls, cafés, markets, and convenience shops. Use your UMD ID card to access and pay with Dining Dollars, and you'll enjoy a discount when you purchase them. Discounts & Tax Savings: - Biggest Discount : You get the best discount when you purchase Dining Dollars as part of an  upgraded Anytime Dining plan .

4. [source: dining-services.txt]  [url: https://academiccatalog.umd.edu/undergraduate/campus-administration-resources-student-services/student-programs-services/dining-services]
kends, with service running until 9 pm each night. - 251 North : Breakfast starts at 8 am every day, with continuous service until 10 pm Monday–Thursday and 7 pm on weekends.

5. [source: dining-dollars-flexible-discounted-and-convenient.txt]  [url: https://dining.umd.edu/students/dining-dollars-flexible-discounted-and-convenient]
- Panera Bread in The Stamp Dining Dollar Bundles | Quantity | Price | Savings |
|--------------------|---------|-----------------------------------------------|
| 125 Dining Dollars | $118.75 | 5% savings + no sales tax (6% off) when used |
| 250 Dining Dollars | $237.50 | 5% savings + no sales tax (6% off) when used |
| 500 Dining Dollars | $475.00 | 5% savings + no sales tax (6% off) when used |

---

## Embedding Model

**Model used:**
`all-MiniLM-L6-v2` (via `sentence-transformers`)

This model was chosen because it is a general-purpose symmetric similarity model — well suited to matching a user's paraphrased question against document text that describes the same concept from the source's perspective. It is compact (22M parameters), runs locally without an API key, and embeds both queries and documents in the same 384-dimensional space, making cosine distance a reliable similarity signal.

**Production tradeoff reflection:**
If cost were not a constraint, the main tradeoffs to weigh would be multilingual support, domain specificity, and context length. UMD has a large international student population, so a multilingual model (e.g., `multilingual-e5-large`) would make the system accessible to students searching in their native language. For domain specificity, a model fine-tuned on question-answering pairs (e.g., `multi-qa-MiniLM-L6-cos-v1`) would improve retrieval for queries phrased as direct questions rather than keyword searches. Finally, if documents were longer — full PDFs rather than scraped web pages — a model with a larger context window would be necessary to avoid losing information at truncation boundaries.

---

## Grounded Generation

**Model:**
`llama-3.3-70b-versatile` via the Groq API, called with `temperature=0` for deterministic, factual responses.

**System prompt grounding instruction:**
The system prompt instructs the model: *"Answer the question using only the information in the provided documents. If the documents don't contain enough information to answer, say 'I don't have enough information on that.'"* The prompt then specifies the citation format explicitly: the model is told to cite the source URL inline after each claim using square brackets, and is given a concrete example so the format is unambiguous. The model is also explicitly told not to add facts from outside the provided documents.

**How source attribution is surfaced in the response:**
Each retrieved chunk is prefixed with its source URL in the context block passed to the model (e.g., `[https://dining.umd.edu/students/sick-meals]`). The system prompt then instructs the model to repeat that URL inline after every claim it derives from that chunk. This produces responses in the format: *"Students can request a sick meal by sending a representative to the dining hall [https://dining.umd.edu/students/sick-meals]."* Because the URL is embedded in the context and the model is instructed to copy it verbatim, hallucinated or fabricated URLs are effectively prevented — the model can only cite what was provided.

---

## Query Interface

The system is served as a Gradio chat interface (`app.py`) running on `localhost:7680`.

**Input:** A freeform text field where the user types a natural-language question about UMD dining. Five example questions from the evaluation plan are pre-loaded as clickable prompts below the input box.

**Output:** A chat bubble containing the model's response rendered as Markdown. Inline citations appear as clickable `[source]` hyperlinks after each claim, linking directly to the source page the information was drawn from.

**Sample interaction transcript:**

> **User:** I have an allergy. Can I go to a dining hall?
>
> **System:** Yes, you can go to a dining hall if you have an allergy. The dining halls have a nutrition staff that is prepared to help you manage your allergy, food intolerance, or dietary restrictions [[source]](https://dining.umd.edu/nutrition-allergies-and-special-diets/allergy). If you have a specific question, you can ask the manager or chef on duty, as they are qualified to discuss specific allergens [[source]](https://dining.umd.edu/nutrition-allergies-and-special-diets/allergy). Additionally, you can check the dining hall menus on the nutrition website to see if they have options that are safe for your allergy [[source]](https://dining.umd.edu/nutrition-allergies-and-special-diets/allergy).

**Example responses with source attribution:**

> **User:** Which dining halls are open early for my 9am class?
>
> **System:** Yahentamitsi and South Campus Dining Hall are open early, with breakfast starting at 7 am Monday–Friday [[source]](https://academiccatalog.umd.edu/undergraduate/campus-administration-resources-student-services/student-programs-services/dining-services). This should give you enough time to grab breakfast before your 9am class.

> **User:** My club ends at 8pm, which dining halls are open?
>
> **System:** According to the provided documents, Yahentamitsi and South Campus Dining Hall are open until 9 pm each night [[source]](https://academiccatalog.umd.edu/undergraduate/campus-administration-resources-student-services/student-programs-services/dining-services). Therefore, if your club ends at 8 pm, Yahentamitsi and South Campus Dining Hall will still be open.

**Out-of-scope refusal example:**

> **User:** What equipment is available at Eppley Gym?
>
> **System:** I don't have enough information on that. The provided documents mention that Sneaker's is a convenience shop located at the Eppley Recreation Center [[source]](https://dining.umd.edu/students/dining-dollars-flexible-discounted-and-convenient), and that Sneakers is also a food option [[source]](https://campusvisitorguides.com/umd/where-to-eat), but they do not provide information about the equipment available at Eppley Gym.

---

## Retrieval Test Results

---

**Query 1: "What is the door price for a student dinner at a UMD dining hall?"**

| Rank | Source | Score |
|------|--------|-------|
| 1 | door-prices.txt | 0.2173 |
| 2 | connector-plans.txt | 0.2230 |
| 3 | dining-services.txt | 0.3151 |
| 4 | dining-services.txt | 0.3306 |
| 5 | dining-halls.txt | 0.3455 |

**Chunk text (top 2):**

> [1] door-prices.txt (score: 0.2173)
> Dining hall door prices for Fall 2025:
> - Breakfast: $9.49 — Open to 10:30am
> - Lunch: $15.99 — 10:30am to 4:00pm
> - Dinner: $19.99 — 4:00pm to Close

> [2] connector-plans.txt (score: 0.2230)
> Dining Hall Door Prices If you're unsure about which plan to select and want to try a dining hall meal first, here are the door prices for Fall 2025: - Breakfast: $9.49 - Lunch: $15.99 - Dinner: $19.99

**Why the top chunks are relevant:**
Rank 1 is the most directly relevant chunk in the entire corpus — it is the complete door price table from the dedicated door-prices page, containing the exact $19.99 dinner figure and its 4:00pm–Close window. Its cosine distance of 0.2173 is the lowest score recorded across all eval queries, reflecting a near-exact semantic match between the query and the document. Rank 2 is also relevant: the connector-plans page independently reproduces the same door price table as a convenience for students considering a plan, so the model has a second source confirming the same fact. Ranks 3–5 are noise — they discuss dining plans, Dining Dollars, and general hall information, none of which contain dinner pricing. Precision for this query is 2/5 = 40%.

---

**Query 2: "What is the difference between a Resident Plan and a Connector Plan at UMD?"**

| Rank | Source | Score |
|------|--------|-------|
| 1 | connector-plans.txt | 0.4983 |
| 2 | resident-plans.txt | 0.5056 |
| 3 | resident-plans.txt | 0.5210 |
| 4 | dining-services.txt | 0.5415 |
| 5 | connector-plans.txt | 0.5561 |

**Chunk text:**

> [1] connector-plans.txt (score: 0.4983)
> Connector Dining Plans & Block Meal Plans: UMD Dining offers flexible dining plans for students who live in a space with their own kitchen! These plans are designed to provide students with access to healthy, delicious meals while connecting them to the UMD community in welcoming spaces.

> [2] resident-plans.txt (score: 0.5056)
> URL_SOURCE: https://dining.umd.edu/students/resident-plans — TITLE: Resident Dining Plans | UMD Dining Services

> [3] resident-plans.txt (score: 0.5210)
> As a resident dining plan member, you have unlimited access to three campus dining halls and can enjoy plenty of great food all semester long. You are welcome in the dining halls for breakfast, lunch, dinner and snacks in between. To allow us to provide this plan, no carryout is permitted.

> [4] dining-services.txt (score: 0.5415)
> Resident Dining Plans For resident students, we offer the Anytime Dining program, which provides unlimited access to the dining halls. Students can choose one of four plans: Base Plan, Base Plus Plan, Preferred Plan, Premium Plan.

> [5] connector-plans.txt (score: 0.5561)
> Five-Day Plans and Connector Block Meal Plans do not fulfill the Resident Dining Plan requirement for students living in traditional on-campus housing. Plan Expiry: All Connector Plans and Dining Dollars expire at the end of Spring Semester.

**Why the top chunks are relevant:**
Ranks 1 and 5 together establish the Connector Plan's identity: rank 1 describes who it is for (students with their own kitchen, i.e. off-campus), and rank 5 explicitly states that Connector Plans do not fulfill the on-campus Resident Dining Plan requirement — the clearest contrast between the two plan types in the corpus. Ranks 2, 3, and 4 cover the Resident Plan side: rank 3 gives the key fact (unlimited access to all three dining halls), and rank 4 provides the tier breakdown. Together, ranks 1–5 give the model enough information to correctly characterize both plans and their primary difference. Notably, the single chunk that most explicitly states the contrast ("for off-campus students without committing to unlimited dining") ranked 23rd and was not retrieved within the top-5 cutoff, yet the answer is still accurate because the individual plan descriptions in ranks 1–5 collectively convey the same information.

---

**Query 3: "What should I do if I am too sick to go to a dining hall?"** *(chunks only)*

| Rank | Source | Score | Chunk preview |
|------|--------|-------|---------------|
| 1 | sick-meals.txt | 0.3719 | URL_SOURCE: https://dining.umd.edu/students/sick-meals TITLE: Sick Meals UMD Dining Services Sick Meals If you are a resident student and are feeling unwell, we understand that it may not be wise for you to come to the dining hall for a meal. To help, we offer a Sick Meal service that allows you to send a representative to collect a meal on your behalf. |
| 2 | sick-meals.txt | 0.4802 | a representative to collect a meal on your behalf. How to Get a Sick Meal: Complete the Online Sick Meal Request Form. Send a Representative : Have a friend come to the dining hall to pick up your meal. Please make sure your representative wears a mask to ensure safety. Your representative should stop at the greeter's station and give your name. We will bring the meal to them. |
| 3 | sick-meals.txt | 0.4818 | nd give your name. We will bring the meal to them. Meal Details: Sick Meals are available at no additional cost for students with a resident dining plan. The service is intended to provide basic nutrition for short-term illness and does not replace long-term medical care. If you are experiencing severe or extended illness (more than three days), we strongly recommend visitingthe Health Center for assistance. |
| 4 | dining-services.txt | 0.5232 | erent tastes and dietary preferences. Dining Halls Dining halls are open to the entire university community, but our first priority is to serve resident students. We are open daily before and after class hours to ensure students can enjoy nutritious meals. The hours of operation for the dining halls are: - Yahentamitsi and South Campus Dining Hall : Breakfast starts at 7 am Monday–Friday and 10 am on weekends, with service running until 9 pm each night. |
| 5 | where-to-eat.txt | 0.5334 | resident students and visitors, faculty and staff Come in and enjoy delicious food from early morning to late evening every day - guests are always welcome! When classes are in session, try one of our three dining halls, packed with delicious options When school’s out, the Stamp is your best bet. Hours vary based on location and academic calendar. For more information, visit dining. umd.edu. For information about Maryland Dining for large groups, email diningplan@umd.edu. Dining Halls |

---

## Evaluation Report

**Q1 — What is the door price for a student dinner at a UMD dining hall?**

- **Expected:** As of Fall 2025, dinner price is $19.99 across all dining halls and dinner is served from 4 PM to close of a dining hall.
- **System response:** The door price for a student dinner at a UMD dining hall is $19.99 [https://dining.umd.edu/home/hours-locations/dining-halls/door-prices]. This price is also confirmed on another page [https://dining.umd.edu/students/connector-plans].
- **Retrieval quality:** Relevant
- **Response accuracy:** Accurate

---

**Q2 — What should a UMD student do if they are too sick to go to a dining hall?**

- **Expected:** Students can request a sick meal from a dining hall by submitting a Sick Meal Request at https://dining.umd.edu/students/sick-meals. The student must then send someone to go pick up the meal, who will pick it up at the greeter's station.
- **System response:** If a UMD student is too sick to go to a dining hall, they can use the Sick Meal service, which allows them to send a representative to collect a meal on their behalf [https://dining.umd.edu/students/sick-meals]. This service is available at no additional cost for students with a resident dining plan [https://dining.umd.edu/students/sick-meals]. However, if the student is experiencing severe or extended illness (more than three days), they are strongly recommended to visit the Health Center for assistance [https://dining.umd.edu/students/sick-meals].
- **Retrieval quality:** Relevant
- **Response accuracy:** Partially accurate — the response correctly describes the sick meal service and representative pickup, but does not mention the greeter's station by name, which is the specific pickup location stated in the expected answer.

---

**Q3 — What is the difference between a Resident Plan and a Connector Plan at UMD?**

- **Expected:** A Resident Plan has unlimited swipes but the student must reside on campus. A Connector Plan has a limited amount of swipes, but allows students to live off campus. The prices for Resident Plans can be found at: https://dining.umd.edu/students/resident-plans, and the prices for Connector Plans can be found at: https://dining.umd.edu/students/connector-plans.
- **System response:** The main difference between a Resident Plan and a Connector Plan at UMD is that Resident Plans provide unlimited access to three campus dining halls [https://dining.umd.edu/students/resident-plans], whereas Connector Plans are designed for students who live in a space with their own kitchen and provide flexible dining options [https://dining.umd.edu/students/connector-plans]. Additionally, Resident Plans are required for students living in traditional on-campus housing, and Connector Plans do not fulfill this requirement [https://dining.umd.edu/students/connector-plans]. Resident Plans also offer different tiers with varying amounts of Dining Dollars and guest passes [https://academiccatalog.umd.edu/undergraduate/campus-administration-resources-student-services/student-programs-services/dining-services], whereas Connector Plans have different options but do not include unlimited dining hall access [https://dining.umd.edu/students/connector-plans].
- **Retrieval quality:** Partially relevant — the most explicit contrast chunk ("for off-campus students without committing to unlimited access") ranked 23rd in cosine distance and was not retrieved within the top-5 cutoff.
- **Response accuracy:** Accurate — the system correctly captured the unlimited vs. block distinction and the on-campus residency requirement, arriving at the right conclusion despite the missing chunk.

---

**Q4 — Is a UMD meal plan cheaper than buying food on your own if I am a commuter student?**

- **Expected:** Consider purchasing a small number of swipes as a back-up in case you are unable to buy or cook food. Additionally, try to plan the average cost of your meal, as the average cost of a meal on a commuter plan is about $10 [Source: https://www.reddit.com/r/UMD/comments/1s1ol7n/whats_cheaper_choosing_a_meal_plan_or_buying/]
- **System response:** According to a Reddit user, the 100 swipe plan works out to $10.5 per meal [https://www.reddit.com/r/UMD/comments/1s1ol7n/whats_cheaper_choosing_a_meal_plan_or_buying]. Another user mentions that cooking at home can be cheaper, with $80 worth of groceries lasting a week for 3 meals per day [https://www.reddit.com/r/UMD/comments/1s1ol7n/whats_cheaper_choosing_a_meal_plan_or_buying]. UMD offers various meal plans, including the Anytime Dining Plan, which provides unlimited access to the dining halls [https://academiccatalog.umd.edu/undergraduate/campus-administration-resources-student-services/student-programs-services/dining-services]. The cost of individual meals is $9.49 for breakfast, $15.99 for lunch, and $19.99 for dinner [https://dining.umd.edu/students/connector-plans]. Considering these prices, it seems that buying food on your own could be cheaper, especially if you can cook at home and buy groceries in bulk [https://www.reddit.com/r/UMD/comments/1s1ol7n/whats_cheaper_choosing_a_meal_plan_or_buying]. However, as a commuter student, having some meal swipes can be convenient for days when you are on campus for long periods [https://www.reddit.com/r/UMD/comments/1s1ol7n/whats_cheaper_choosing_a_meal_plan_or_buying]. Ultimately, the decision depends on your personal preferences, cooking habits, and schedule.
- **Retrieval quality:** Relevant
- **Response accuracy:** Accurate

---

**Q5 — What are Dining Dollars and how do I get them?**

- **Expected:** Dining Dollars are a prepaid balance loaded on your UMD ID card, accepted at all permanent Maryland Dining locations including dining halls, cafes, markets, and convenience shops. You can purchase them in bundles of 125, 250, or 500 at a 5% discount plus sales tax savings. They are also included with upgraded Anytime Dining plans. More info at https://dining.umd.edu/students/dining-dollars-flexible-discounted-and-convenient
- **System response:** Dining Dollars are a convenient way to pay for food and snacks at any permanent Maryland Dining location on campus, including dining halls, cafes, markets, and convenience shops [https://dining.umd.edu/students/dining-dollars-flexible-discounted-and-convenient]. You can get Dining Dollars by purchasing them as part of an upgraded Anytime Dining plan, which provides the best discount [https://dining.umd.edu/students/dining-dollars-flexible-discounted-and-convenient], or by buying Dining Dollar bundles, available in amounts of 125, 250, or 500 Dining Dollars [https://dining.umd.edu/students/dining-dollars-flexible-discounted-and-convenient]. Additionally, some dining plans, such as the Preferred Plan, include a certain amount of Dining Dollars, like 300 Dining Dollars [https://academiccatalog.umd.edu/undergraduate/campus-administration-resources-student-services/student-programs-services/dining-services]. Dining Dollars can also be purchased separately, providing a 5% discount and saving 6% sales tax [https://dining.umd.edu/students/connector-plans].
- **Retrieval quality:** Relevant
- **Response accuracy:** Accurate

---

## Failure Case Analysis

**Question that failed:**
*"What is the difference between a Resident Plan and a Connector Plan at UMD?"*

**What the system returned:**
The system retrieved chunks describing each plan in isolation — the Connector Plan intro, the Resident Plan unlimited-access policy, and the on-campus residency requirement — but did not retrieve the single chunk that most directly contrasts the two plans side by side ("for off-campus students without committing to unlimited access"). That chunk ranked 23rd in cosine distance and fell outside the top-5 cutoff. The generated answer described each plan correctly on its own terms but stated the contrast less crisply than the source document does.

**Root cause (tied to a specific pipeline stage):**
The failure originates in the retrieval stage, specifically the interaction between chunk size and top-k. Because the contrast is stated in one sentence embedded mid-paragraph in the connector plans page, recursive chunking placed it inside a larger 500-character chunk that also contained unrelated pricing detail. That diluted the embedding's similarity signal for a query about *differences* between plans. The chunk ranked highly for queries about Connector Plans specifically, but not for a comparison query — the embedding model matched on individual plan descriptions rather than on the concept of contrast. Top-k was tuned from 3 to 10 to 5 during development; at 5, the key plan-description chunks are retrieved but the most explicit comparison sentence remained out of reach.

**What you would change to fix it:**
Reducing chunk size to 250 characters was tested during development. It isolated the contrast sentence into its own chunk and improved retrieval precision and recall for Q3, but degraded generation quality across other questions — shorter chunks produced less coherent context passages for the LLM — so the change was reverted. The more targeted fix would be query expansion: rephrasing "difference between A and B" as "A vs B", "A compared to B", and "who should choose A over B" before retrieval. This casts a wider semantic net without affecting chunk coherence for any other question.

---

## Spec Reflection

**One way the spec helped you during implementation:**
The Chunking Strategy section of `planning.md` specified the chunk size (500 characters), overlap (50 characters), and separator hierarchy before any code was written. When Claude was asked to implement `chunker.py`, those parameters were passed directly from the spec as context, and the resulting implementation matched the intended design on the first attempt with no ambiguity about what values to use. Without the spec, the implementation step would have required back-and-forth to settle on chunk size — instead, the decision was already made and justified, and the AI tool could focus entirely on the mechanics of recursive splitting and overlap merging.

**One way your implementation diverged from the spec, and why:**
The spec initially set top-k at 3 chunks per query. During evaluation, Q3 (Resident vs. Connector Plan comparison) revealed that 3 chunks was insufficient — two different documents needed to be surfaced simultaneously, and at k=3 the system returned only one plan type's chunks. Top-k was increased to 10 after evaluation showed that synthesis questions needed more chunks, then reduced to 5 after observing that larger context windows introduced noise that degraded generation coherence. The spec was updated at each step to reflect the current value and the reason for the change. This divergence was data-driven throughout: each adjustment was made after testing against the eval questions rather than by intuition.

---

## AI Usage

**Instance 1 — Implementing embedding.py and retrieval.py**

- *What I gave the AI:* The Architecture diagram and Retrieval Approach section from `planning.md`, specifying `all-MiniLM-L6-v2`, ChromaDB as the vector store, and top-k = 3. I asked Claude to implement the embedding step (load chunks, embed, store with source metadata) and a retrieval function returning the top-k chunks.
- *What it produced:* A working `embedding.py` that chunked all `.txt` files and stored them in ChromaDB, and a `retrieval.py` with a `retrieve()` function. The code ran correctly on the first attempt.
- *What I changed or overrode:* The initial implementation used ChromaDB's default distance metric, which is L2 (Euclidean). Scores were exceeding 1.0 and the most relevant chunks were not rising to the top. I caught this by inspecting the raw scores and directed Claude to fix it by adding `metadata={"hnsw:space": "cosine"}` to the `create_collection()` call and rebuilding the index. The fix required understanding that ChromaDB does not default to cosine similarity and that the collection must be deleted and recreated — not just re-added to — for the metric change to take effect.

**Instance 2 — Source URL attribution in generated answers**

- *What I gave the AI:* A request to surface source URLs in the model's citations instead of raw `.txt` filenames. I described the desired output format (inline `[url]` after each claim) and asked Claude to implement it end-to-end across `embedding.py`, `retrieval.py`, and `generate.py`.
- *What it produced:* Claude added a hardcoded `SOURCE_URLS` dictionary in `embedding.py` mapping each filename to its URL, stored the URL in chunk metadata at index time, threaded the URL through `retrieve()`, and updated `build_context()` to label each chunk with its URL so the LLM could cite it inline.
- *What I changed or overrode:* I pointed out that every document file already contains the source URL in its first line (`URL_SOURCE: <url>`), so a hardcoded dictionary was redundant and fragile — it would break silently if a file were renamed or a new document added without a matching dict entry. I directed Claude to replace the dictionary with a `_parse_url()` function that reads the URL directly from the document text at index time. This approach is self-maintaining: any document that follows the `URL_SOURCE:` convention is handled automatically.
