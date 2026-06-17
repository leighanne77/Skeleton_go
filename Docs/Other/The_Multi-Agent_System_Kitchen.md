# The Multi-Agent System Kitchen
*A pantry, a standard, and the judgment to handle each ingredient differently as the room changes.*

Just as a great kitchen returns again and again to the same shelf — spices and oils, grains and liquids, fats, vegetables, proteins — and from that fixed pantry produces an endless variety of dishes, a multi-agent system is built from a small, stable set of ingredients that recombine into wildly different results, over and over. The pantry doesn't change much; the cooking does.

And here's the constraint that makes this kitchen interesting: **the food always has to be ready.** A regulated answer, like a dish sent to the pass, cannot be "mostly done" or "probably safe." It goes out correct, on time, every time — or it doesn't go out. What changes from kitchen to kitchen isn't *whether* the food must be perfect; it's the conditions. The ovens run hotter or colder. The room is humid or bone-dry. The altitude changes how things rise. Same ingredients, same standard of "ready" — but you handle everything differently depending on the room you're cooking in. A custard that sets cleanly at sea level curdles on a mountaintop unless you adjust. The recipe is constant; the technique bends to the environment.

That's the whole art of building these systems: a fixed pantry of ingredients, a non-negotiable standard that the food is always ready, and the judgment to handle each ingredient differently as the oven, the humidity, and the room change.

![The kitchen and the food](mas_kitchen_and_food.svg)

## The pantry — ingredients by type and use

**Proteins — the substance of the dish (the reasoning).** The large language model is the protein: the main source of substance, the thing the diner came for. Here the primary protein is Claude. But a good kitchen never lets one palate both cook and judge the same plate, so a second, different protein appears at the pass — a cross-family judge model, chosen precisely *because* it isn't the one that did the cooking. Proteins are also the priciest thing on the shelf and the easiest to overuse; the discipline is to reserve them for where they're actually needed.

**Grains and starches — the reliable base (the orchestrator and the skeleton).** Every plate needs something to sit on. The orchestrator and the graph it runs are the rice, the bread, the base that carries everything else and shows up in nearly every dish. It isn't glamorous, but it's what makes a plate a meal instead of a scatter of parts: it plans, it routes, it gives the other ingredients a place to be.

**Vegetables — structure and fibre (the specialist agents and retrieval-as-a-tool).** The specialists are the vegetables: they give the dish its actual structure, each prepared for its job. And retrieval is a vegetable, not the table — it's an ingredient the cook reaches for when the dish calls for it, not the surface everything is served on. Treating retrieval as one tool among others is what lets the same dish absorb a different vegetable when the menu changes.

**Fats — what carries flavour and binds (memory).** Fat carries flavour across a dish and binds the parts together; memory does the same. Session state holds the thread of a conversation so the dish tastes continuous; working memory is the fond at the bottom of the pan that every agent adds to and reads from. But fat is also where things spoil if you keep them too long — so cross-session memory, the fat you'd render and store for next week, is deliberately left out of this kitchen, because stored fat from a regulated meal is regulated data, and you don't keep it casually.

**Liquids — the medium that moves everything (the data plane).** Stock, water, wine — liquid is what lets heat and flavour move through a dish. The message-passing between agents, the shared channels, the data plane is that liquid: invisible in the final plate, but nothing moves without it.

**Acid — the brightness that cuts and keeps it honest (the guardrails).** A dish without acid is flat and can hide its faults; a squeeze of lemon cuts through and exposes what's really there. The deterministic guardrails are the acid: PII redaction, schema, permitted-use — sharp, cheap, applied first, keeping the dish honest before anything richer goes near it.

**Seasoning and spice — precision over volume (the eval-against-goal).** This is the part that's skill, not quantity. The eval is the seasoning: too little and the dish is bland and unchecked; too much and it's bitter and over-corrected. You taste against what the dish is *supposed* to be — the defined target — not against some generic idea of "good," and you calibrate your own palate so you're not just agreeing with yourself.

**Salt — the non-negotiable in everything (auditability).** Salt goes in at every stage; it's the one thing in nearly every dish, and you season as you go, not at the end. The tamper-evident audit trail is the salt of this kitchen: every decision recorded as it's made, layer by layer, so what reaches the pass can be traced all the way back to the pot it came from. Under-salt and the whole dish is suspect — and you can't fix it afterward.

**Heat and technique — not an ingredient, the handling (the deployment archetypes).** Then there's the part that isn't on the shelf at all: the heat, the timing, the technique. The same pantry becomes a different meal depending on whether you're cooking in a Rolls-Royce kitchen built for decades, a Formula-One kitchen optimised for speed on the customer's own equipment, or a field kitchen that has to run anywhere with no power. The ingredients don't change. How you handle them does.

**Mise en place — the thing you do before you cook (the spec and golden set).** Before a single pan is lit, the good cook writes down what "done" means and lays everything out in its place. The spec and the golden set are the mise en place: define what a correct dish is, set out the tests it must pass, and only then start cooking. Skip it and you're seasoning blind.

![The cooks at work — the brigade](mas_cooks_at_work.svg)

## The story — the kitchen that cooks for the auditor

Picture a kitchen that doesn't cook for a dining room. It cooks for an inspector — one who can push through the doors at any hour, lift the lid off any pot, and ask to see exactly where every ingredient came from and who touched it. This is the energy-and-utilities kitchen: the diner is a NERC CIP compliance analyst at a utility, and behind her stands the regulator, and the food she needs is an answer she can stand behind when someone official says *"show me."*

So we built the kitchen backwards from the inspection.

**First, we decided what "ready" means here.** Not "tastes good" — *defensible*. A plate leaves this kitchen only if every claim on it can be traced to the standard it came from, with the citation pinned to the page. That decision — written down before a single burner was lit — is the mise en place: the spec and the golden set that say what a correct dish *is* in this kitchen, so nobody is seasoning by feel.

**We chose to treat retrieval as a vegetable, not the table.** The grid throws different work at this analyst week to week — today it's CIP evidence, tomorrow a FERC filing, next a state-PUC rate case — so the dish had to absorb a different ingredient without rebuilding the kitchen. Make retrieval one tool the cook reaches for, and the same skeleton serves all of it.

**We put a second cook at the pass.** In most kitchens the cook who made the plate decides whether it's good enough; in this one, that's a conflict of interest the inspector would catch in a second. So the verifier is a *different* palate from the one that cooked — an independent taster whose only job is to check the plate against what it was supposed to be. If it isn't right, it doesn't go out the door; it goes back to the line, and if it still can't be made right, it goes to a human, not to the diner. In a kitchen cooking for an auditor, a plate you can't vouch for is a liability, not a meal.

**We salt at every station.** Every decision — what was retrieved, what was checked, what passed, what was held back — is written into a record as it happens, and each entry seals the one before it, so that if anyone alters a page, the break shows. When the inspector lifts the lid, the seasoning is already there, all the way down; we don't reconstruct the meal from memory.

**We cook only with what this diner is allowed to be served.** The pantry is scoped to her entitlements — she can't be handed an answer built from documents she was never cleared to see — so the dish is safe not just in what it says, but in what it was ever allowed to be made from.

**We loaded the right dietary rules for the room.** NERC CIP, FERC, IEC 62443, the state-PUC rules — these are the restrictions this diner cooks under, set out on the board before service and defaulted to the strictest that applies, so the kitchen never improvises a rule it should have known.

**And we sourced every ingredient from suppliers we trust, and built the kitchen to run when the power flickers.** This is, after all, a kitchen inside the energy world — the lights are not guaranteed. So nothing essential depends on a live delivery truck or an outside hand: it runs offline, on clean-provenance ingredients, on a single bench if it has to. A kitchen that feeds the grid can't fall over when the grid does.

None of these were exotic ingredients. They were the same pantry every governed agent is built from — the protein, the base, the acid, the salt, the seasoning, the mise en place. What made it the *energy* kitchen was the handling: a room where the inspector can arrive unannounced, the power isn't promised, and the standard of "ready" is not "delicious" but "defensible." Hold those three conditions in mind and the skeleton almost designs itself — which is the quiet point of cooking from a fixed pantry. You don't invent new ingredients for every meal. You learn the room, and you handle what you have like someone who's expecting the inspector.

![The right dish to the right diner, even in a blackout](mas_right_dish_blackout.svg)
