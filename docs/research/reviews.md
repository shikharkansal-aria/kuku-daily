# Play Store review evidence (Problem 3 hypothesis test)

## Method
- Source: public Google Play reviews, India store, newest first, via `google-play-scraper` (`tools/reviews.py`, no LLM).
- Pulled 2026-11-07. Date ranges are in the table. The CSVs hold date, star, thumbs up, text and theme tags only (no names or images). Files are in `outputs/evidence/`.
- Tagging is keyword matching at word start, case-insensitive. A review can carry several themes. Lists live at the top of `tools/reviews.py`.
  - paywall_price: paisa, mehenga, recharge, subscription, coins, pay, paid, premium, price, costly, money, unlock, refund, charged, autopay, deduct, paywall, plan, lock, free episode, membership
  - too_many_or_wrong_fit: too many shows/stories/series/similar, so many shows/stories, variety, recommendation, irrelevant, cannot find, search, dubbed, not interesting, my taste, choice, category, genre, options
  - repetitive_or_burnout: bore, boring, repetitive, same story/thing/type/plot, all same, copy, timepass, stretch, dragged, too long, unnecessary, ek jaisi, wahi, fir se
  - ads: ads, ad, advert, vigyapan
  - app_bugs: bug, crash, glitch, lag, buffer, not working, error, slow, freeze, stuck, login, otp, chalta nahi
  - positive_story: good/great/best story, interesting, excellent, amazing, awesome, entertaining, addictive, binge, well made, quality, climax, twist, kahani, badhiya (negated by "not"/"no" before)

| App | Package | Lang | N | Dates |
|---|---|---|---|---|
| Kuku TV | com.vlv.aravali.reels | en | 300 | 2026-10-26 to 2026-11-06 |
| Kuku TV | com.vlv.aravali.reels | hi | 200 | 2026-06-21 to 2026-11-03 |
| ReelShort | com.newleaf.app.android.victor | en | 300 | 2026-11-03 to 2026-11-06 |
| DramaBox (contrast) | com.storymatrix.drama | en | 300 | 2026-11-03 to 2026-11-06 |

## Theme share of all pulled reviews (% of N)
| Theme | Kuku en | Kuku hi | ReelShort | DramaBox |
|---|---|---|---|---|
| paywall_price | 20.3 | 12.0 | 33.3 | 22.3 |
| too_many_or_wrong_fit | 0.7 | 0.0 | 0.7 | 1.7 |
| repetitive_or_burnout | 0.3 | 0.0 | 2.3 | 3.0 |
| ads | 6.0 | 1.0 | 22.0 | 32.0 |
| app_bugs | 0.7 | 0.0 | 1.3 | 1.7 |
| positive_story | 9.0 | 0.5 | 10.3 | 6.7 |
| untagged | 69.3 | 87.0 | 45.3 | 49.7 |
| 1-2 star share | 36.3 | 55.5 | 50.3 | 46.0 |

Among 1-2 star reviews only: paywall_price is 51.4% (Kuku en), 18.9% (Kuku hi), 53.6% (ReelShort), 37.0% (DramaBox). Fit is at most 0.9% and burnout at most 5.8% in every app. Per-star counts are in each `*_summary.json`.

## Precision check
Round 1: 40 random tagged reviews, 60 theme tags, 44 correct (73%). Misfires: "rs." matched inside "lovers.", "too many ads" tagged as too-many-shows, "problem" as bugs, "scam" as price, "addict" as burnout, "Not good story" as positive. I tuned once (removed or tightened those keywords, added negation) and re-ran.
Round 2: new random sample of 40 tagged reviews (seed 5), 53 tags, 45 correct: **precision 85%**. Remaining errors: "too many similar storyline" tagged fit not repetition, "too long adds" as burnout, a sarcastic "interesting story" as positive. Recall was not measured; the untagged share above is a rough hint that recall is limited, especially for Hindi in Devanagari script (Kuku hi, 87% untagged), where the keyword lists are thin.

## Representative quotes (Kuku TV unless stated)
- "you should give one drama free trial and then take money" (2026-10-28, 1 star)
- "i started free trail for a month but Autopay with rupees 699 rupees happen please refund my money" (2026-10-27, 1 star)
- "very much high price" (2026-11-03, 1 star)
- "Don't use same episodes with different faces." (2026-10-30, 1 star)
- "paid app. all episodes like same" (2026-11-02, 1 star)
- "too many similar storyline" (DramaBox, 2026-11-04, 3 stars)
- "First episodes were great, nice story line.. But after that it goes so cheese, so predictable.. So boring..." (ReelShort, 2026-11-04, 2 stars)

## What this does and does not show
- Supports (b): price and billing is the largest identifiable complaint theme everywhere, and about half of Kuku and ReelShort 1-2 star reviews. Much of it is billing trust (autopay charges after a Re 1 or Rs 2 trial, refunds, cancelling), not only "too expensive". Those are different fixes.
- Does not support (a): almost no reviewer says there are too many shows or that content does not fit them (0 to 1.7%). Reviewers rarely talk about catalogue size, so absence here is weak evidence, not proof.
- Barely supports (c): repetition or boredom appears in 0.3 to 3.0%, mostly as "same episodes" or "predictable". Binge burnout is not something people write app reviews about.
- Limits: reviewers are not all users, and people who churn quietly never review. Reviews skew to angry 1 star and happy 5 star. Keyword tagging misses sarcasm and spelling variants, and cannot read Devanagari well. Newest-300 windows are short (days for ReelShort and DramaBox), so one bad billing week can inflate paywall share. Kuku en and hi are different pulls and overlap in reviewers is possible. N is small and no significance testing was done. Reviews cannot show drop-off timing; only Kuku's own funnel data can.
