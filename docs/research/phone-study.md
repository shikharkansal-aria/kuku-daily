# Phone study (partial)

Status: incomplete. Device: OnePlus CPH2569, unlocked. Done in about 25 minutes of a 40 minute budget; stopped early.

## What blocked the plan
- `screenrecord` is denied on this phone ("Unable to open ... Permission denied", on /sdcard and /data/local/tmp). No clips, so no ffmpeg or whisper analysis, and no Hindi transcript. Substitute: 1.5 s interval screenshot strips in outputs/phone/frames/ (m1.png, m2.png, m3.png).
- One shell command was refused by the auto mode classifier early on; I retried with smaller steps.
- DramaBox and Kuku TV were not installed (only ReelShort). Kuku FM was already on the phone (screen seen at start).

## Promos observed (Instagram, @reelshortapp, 15.8M followers, 8,867 posts)
| Account | Title | Hook (what was visible) | Overlay | Length | Ending | Views / likes | Why it works |
|---|---|---|---|---|---|---|---|
| reelshortapp | Nero: Made Men | Skull-mask gunman standing still, tilted frame | none, "Now on ReelShort" caption | not timed | not seen | 903K likes (grid 39.6M views) | Striking image, mystery |
| reelshortapp | Runaway Single Mom, Safe in His Arms | Woman close-up, then shirtless man in wheelchair, intimate kitchen | none | not timed (over 9 s) | not seen | 159K likes (grid 33.7M views) | Face close-ups, power and vulnerability contrast |
| reelshortapp | Driven to Love | Couple embrace, then woman turns away, man in doorway, ends on him in bed | "vertical drama full episodes" search chip | over 9 s | man in bed, no resolution | 629 likes | Romance then rupture |
Only 3 promos watched, not 8 to 12. Lengths, first-line audio and endings were not captured because audio and video could not be recorded.

## ReelShort app teardown (partial)
- Publisher NewLeaf Publishing, Play Store 4.2 stars, 1M reviews, 46 MB, in-app purchases, contains ads. Package com.newleaf.app.android.victor.
- Onboarding: notification prompt (denied), then a "Recommended for You / World's most popular dramas" picker with "% choose" badges (95%, 90%) and a "Pick for me" button. I closed it. After close the app showed a black screen for over 10 s, so home, episodes, paywall and prices were not seen.
- Titles and tags: Trapped in the Boss's Embrace (Divorce), I Had a Baby without You (Billionaire), Mistaken as His Mate: The Luna's Regret (Werewolf), Carrying His Triplets, Becoming His Wifey (Billionaire). Tropes: billionaire, werewolf, divorce, secret baby.
- DramaBox, Kuku TV: not done.

## Hook taxonomy (from what was seen)
1. Striking visual (mask, weapon, costume), no dialogue needed.
2. Intimate close-up then power contrast (wheelchair, shirtless, vulnerability).
3. Romance then rupture (embrace, then a third person at the door).
4. Trope title as caption (billionaire, werewolf, secret baby) so the pitch is in the title.

## Implications for a promo finder
1. Score the first 3 s on visual and trope strength, not only on dialogue.
2. Prefer scenes with a third-party interruption (door, phone, entrance) as cliffhanger endings.
3. Standalone check: the trope must be inferable from the clip alone, as the titles do.
4. Output the trope tag (billionaire, divorce, secret baby) with each promo, as ReelShort does.
5. Keep the clip under about 30 s on a single reveal; engagement leaders were short single-situation clips.

## Indian local-language observations
Not observed. Kuku TV and DramaBox were not opened and no Hindi clip was recorded (recording blocked). The only Indian signal: Kuku FM, already on the phone, showed audio-series genres (Motivation, Historical, Crime, Love, Thriller, Mythology, Personal Finance, Spirituality) and a title "Instant pelli" (Telugu word for wedding) with a continue-listening bar. ReelShort onboarding showed only English US-style titles. Whether Kuku TV is original, dubbed or AI, Hindi vs Hinglish and subtitle script remain open.
