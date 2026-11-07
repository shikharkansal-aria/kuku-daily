# Kuku TV phone teardown (7 Nov 2026)

Read-only. Device e6217f45, app com.vlv.aravali.reels. Screenshots in outputs/phone/kukutv/.

## Facts
- Notification permission prompt appears first, before any content (01-launch.png). Denied.
- Language picker "Choose show language": Telugu, Hindi, Tamil, Bangla, Kannada, Malayalam, Punjabi, Haryanvi, Gujarati, Bhojpuri (10 options, Telugu preselected) (02-after-notif.png, 03-after-lang.png). No genre or taste picker seen.
- No login wall: home loaded without any account or phone number (08-relaunch.png, 09-home.png).
- A "How's your experience so far?" star rating sheet shows on first home load, before any episode was watched (08-relaunch.png). Dismissed with Back.
- Top tabs: Popular, AI Drama, Originals, K Drama. Bottom nav: Home, Shorts, Premium, My List, Profile (09-home.png).
- Home first screen: 1 hero carousel (6 dots, 1 title visible, auto-playing trailer) plus the header of a Top 10 row; about 1 show fully visible (09-home.png).
- Rows seen by scrolling: hero carousel, Top 10 in India (language filter chips: All, Hindi, Tamil, Telugu, Malayalam, Kannada...), Recommended For You, a 3-column grid of titled shows (She Refused the Don, Parshuram Ka Waaris, God Of Cricket, Mera Handsome Bodyguard, Parcel to Paradise, King in Disguise), Stay Tuned Daily, Browse by Language, New Releases (10-scroll1.png, 11-scroll2.png, 12-scroll3.png).
- Choice load: after 3 scrolls about 8 rows/sections and roughly 25 to 30 distinct tiles passed (partial rows count 2 to 3 visible per carousel; exact tile count not verified).
- Social proof: view counts on tiles (8.9M, 22.8M, 38M, 34.9M) and "New" / "New Episodes" badges (10-scroll1.png, 11-scroll2.png).
- Personalization: a "Recommended For You" row exists on a fresh install with no history (10-scroll1.png); language pick did not visibly change home (Top 10 still "All").
- Existing timed mechanic: a "Stay Tuned Daily" row with "New Episodes" badges on Love ki Century, Parshuram Ka Waaris, Suryaput... (12-scroll3.png). Looks like a returning-episodes shelf; unlock rules not seen.
- Thumbnails and hero art look AI-generated (glossy, uniform faces); an "AI Drama" tab exists (09-home.png, 11-scroll2.png). Hero shows a statutory smoking/alcohol warning overlay (09-home.png).

## Could not check
- Player screen: the screen capture is black on the player (13-show.png, 14-player-again.png, 15-home-top.png). Probably secure-flag protected video or a rendering stall. So I could not see: episode length, how many episodes are free, the paywall wording and episode number, plan prices, trial length, autopay wording, coins or ad-unlock, dialogue language.
- Premium tab (not opened, time and black screen issue).
- Whether picking a language was saved (the first Continue tap raced with the device briefly dropping from adb).
- Exact tile counts per row.

## Paywall (read via UI dump)
Dated 2026-11-07, Kuku TV (com.vlv.aravali.reels), Premium tab, read only (no buy tapped).
Evidence: outputs/phone/kukutv/paywall/04.xml (plans), 03.png (screenshot), 02.xml, 01.xml (home with Premium tab).
Header: "Pick Your Premium Plan", "1M+ users bought premium so far". Plans (price, struck-through list price, period):
- Quarterly Premium: Rs 699 (was 999), 3 months, "Ad-Free - Rs 300 Off", preselected
- Quarterly Premium With Ads: Rs 499 (was 699), 3 months, "Rs 200 Off"
- Annual Premium: Rs 1499 (was 1999), 12 months, "Ad-Free - Rs 500 Off"; footer "Only Rs 233 / month" (as shown)
- Monthly Premium With Ads: Rs 199 (was 399), 1 month, "Rs 200 Off"
- CTA "Pay Rs 699", "Pay via Paytm", Rs 100 OFF chip.
Wording: "Auto-renews - Cancel anytime - Only Rs 233 / month"; "Your plan auto-renews based on the selected plan. You can cancel anytime before renewal, your subscription stays active until it expires." No free trial seen.
Exit sheet seen when pressing back from the plan page: "Close sheet", "Continue", "Go Back" (05.xml). Not tapped.
Home Top shows seen (watch counts): Mera Handsome Bodyguard 38M, King in Disguise 34.9M, Parcel to Paradise 23.6M.

## Could not check
- Free episode count, first locked episode, in-player paywall overlay text, episode duration: the show tap opened a player with a settings sheet and then a different show page; episode selector not reached before the time limit (07 to 10.xml).
- Whether the Rs 233/month figure matches the annual price (1499/12 is about 125); left as displayed.
